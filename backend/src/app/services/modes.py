"""Modes service for predefined automation sequences."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.modes import mode_executions, modes
from app.services.hubitat import get_hubitat_service

logger = logging.getLogger(__name__)


# Default modes - created on startup if not existing
DEFAULT_MODES = [
    {
        "name": "mode_nuit",
        "label": "Mode Nuit",
        "description": "Éteint les lumières, baisse le chauffage, verrouille la porte",
        "icon": "moon",
        "color": "indigo",
        "actions": [
            {"type": "device", "command": "off", "device_type": "light"},
            {"type": "temperature", "command": "setHeatingSetpoint", "value": 19.5},
            {"type": "device", "command": "lock", "device_type": "lock"},
        ],
        "display_order": 1,
    },
    {
        "name": "mode_matin",
        "label": "Mode Matin",
        "description": "Allume les lumières principales, monte le chauffage",
        "icon": "sun",
        "color": "amber",
        "actions": [
            {"type": "device", "command": "on", "device_type": "light", "rooms": ["Salon", "Cuisine"]},
            {"type": "temperature", "command": "setHeatingSetpoint", "value": 21.5},
        ],
        "display_order": 2,
    },
    {
        "name": "mode_souper",
        "label": "Mode Souper",
        "description": "Lumières tamisées, ambiance détente",
        "icon": "utensils",
        "color": "orange",
        "actions": [
            {"type": "device", "command": "setLevel", "value": 40, "device_type": "dimmer", "rooms": ["Salon"]},
            {"type": "device", "command": "on", "device_type": "light", "rooms": ["Cuisine"]},
        ],
        "display_order": 3,
    },
    {
        "name": "mode_absence",
        "label": "Mode Absence",
        "description": "Tout éteint, chauffage économie, porte verrouillée",
        "icon": "door-closed",
        "color": "gray",
        "actions": [
            {"type": "device", "command": "off", "device_type": "light"},
            {"type": "temperature", "command": "setHeatingSetpoint", "value": 18.0},
            {"type": "device", "command": "lock", "device_type": "lock"},
        ],
        "display_order": 4,
    },
]


async def get_mode_by_id(conn: AsyncConnection, mode_id: int) -> dict[str, Any] | None:
    """Get a mode by ID."""
    result = await conn.execute(select(modes).where(modes.c.id == mode_id))
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("actions"):
        data["actions"] = json.loads(data["actions"])
    return data


async def get_mode_by_name(conn: AsyncConnection, name: str) -> dict[str, Any] | None:
    """Get a mode by name."""
    result = await conn.execute(select(modes).where(modes.c.name == name))
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("actions"):
        data["actions"] = json.loads(data["actions"])
    return data


async def get_all_modes(conn: AsyncConnection, enabled_only: bool = False) -> list[dict[str, Any]]:
    """Get all modes."""
    query = select(modes)
    if enabled_only:
        query = query.where(modes.c.is_enabled == True)  # noqa: E712
    query = query.order_by(modes.c.display_order.nulls_last(), modes.c.label)

    result = await conn.execute(query)
    mode_list = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("actions"):
            data["actions"] = json.loads(data["actions"])
        mode_list.append(data)
    return mode_list


async def get_active_mode(conn: AsyncConnection) -> dict[str, Any] | None:
    """Get the currently active mode (if any)."""
    result = await conn.execute(
        select(modes).where(modes.c.is_active == True)  # noqa: E712
    )
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("actions"):
        data["actions"] = json.loads(data["actions"])
    return data


async def create_mode(
    conn: AsyncConnection,
    name: str,
    label: str,
    actions: list[dict[str, Any]],
    description: str | None = None,
    icon: str | None = None,
    color: str | None = None,
) -> dict[str, Any]:
    """Create a new mode."""
    values = {
        "name": name,
        "label": label,
        "description": description,
        "icon": icon,
        "color": color,
        "actions": json.dumps(actions),
    }
    result = await conn.execute(insert(modes).values(**values).returning(modes))
    await conn.commit()
    row = result.fetchone()
    data = dict(row._mapping) if row else {}
    if data.get("actions"):
        data["actions"] = json.loads(data["actions"])
    return data


async def update_mode(
    conn: AsyncConnection,
    mode_id: int,
    label: str | None = None,
    description: str | None = None,
    actions: list[dict[str, Any]] | None = None,
    icon: str | None = None,
    color: str | None = None,
    is_enabled: bool | None = None,
    display_order: int | None = None,
) -> dict[str, Any] | None:
    """Update a mode."""
    update_data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}
    if label is not None:
        update_data["label"] = label
    if description is not None:
        update_data["description"] = description
    if actions is not None:
        update_data["actions"] = json.dumps(actions)
    if icon is not None:
        update_data["icon"] = icon
    if color is not None:
        update_data["color"] = color
    if is_enabled is not None:
        update_data["is_enabled"] = is_enabled
    if display_order is not None:
        update_data["display_order"] = display_order

    result = await conn.execute(
        update(modes).where(modes.c.id == mode_id).values(**update_data).returning(modes)
    )
    await conn.commit()
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("actions"):
        data["actions"] = json.loads(data["actions"])
    return data


async def delete_mode(conn: AsyncConnection, mode_id: int) -> bool:
    """Delete a mode."""
    result = await conn.execute(delete(modes).where(modes.c.id == mode_id))
    await conn.commit()
    return result.rowcount > 0


async def activate_mode(
    conn: AsyncConnection,
    mode_id: int,
    user_id: int | None = None,
    triggered_by: str = "user",
    use_mistral_brain: bool = False,
) -> dict[str, Any]:
    """Activate a mode - execute all its actions.

    Args:
        conn: Database connection
        mode_id: ID of the mode to activate
        user_id: ID of the user triggering the mode (optional)
        triggered_by: Source of the trigger (user, schedule, automation)
        use_mistral_brain: If True, try to execute via Mistral Brain first

    Returns execution result with success/failure details.
    """
    mode = await get_mode_by_id(conn, mode_id)
    if not mode:
        raise ValueError(f"Mode {mode_id} not found")

    if not mode.get("is_enabled"):
        raise ValueError(f"Mode {mode['label']} is disabled")

    actions = mode.get("actions", [])
    hubitat = get_hubitat_service()

    # Deactivate all other modes first
    await conn.execute(update(modes).values(is_active=False))

    # Try Mistral Brain first if requested
    brain_executed = False
    if use_mistral_brain:
        try:
            from app.services.mistral_brain import get_mistral_brain_service

            brain = get_mistral_brain_service()
            await brain.execute_automation(mode["name"])
            brain_executed = True
            logger.info(f"Mode {mode['name']} executed via Mistral Brain")
        except Exception as e:
            logger.warning(f"Mistral Brain execution failed, falling back: {e}")

    # Execute actions directly if Brain didn't handle it
    succeeded = 0
    failed = 0
    errors = []

    if not brain_executed:
        for action in actions:
            try:
                await _execute_action(hubitat, action, conn)
                succeeded += 1
            except Exception as e:
                failed += 1
                errors.append({
                    "action": action,
                    "error": str(e),
                })
                logger.error(f"Mode action failed: {action} - {e}")
    else:
        # If Brain executed, count all as succeeded
        succeeded = len(actions)

    # Mark mode as active
    await conn.execute(
        update(modes)
        .where(modes.c.id == mode_id)
        .values(is_active=True, last_activated=datetime.now(timezone.utc))
    )

    # Log execution
    execution_log = {
        "mode_id": mode_id,
        "mode_name": mode["name"],
        "triggered_by": triggered_by,
        "user_id": user_id,
        "success": failed == 0,
        "actions_total": len(actions),
        "actions_succeeded": succeeded,
        "actions_failed": failed,
        "error_details": json.dumps(errors) if errors else None,
    }
    await conn.execute(insert(mode_executions).values(**execution_log))
    await conn.commit()

    return {
        "mode_id": mode_id,
        "mode_name": mode["name"],
        "mode_label": mode["label"],
        "success": failed == 0,
        "actions_total": len(actions),
        "actions_succeeded": succeeded,
        "actions_failed": failed,
        "errors": errors if errors else None,
    }


async def deactivate_all_modes(conn: AsyncConnection) -> None:
    """Deactivate all modes (no mode active)."""
    await conn.execute(update(modes).values(is_active=False))
    await conn.commit()


async def _execute_action(hubitat, action: dict[str, Any], conn: AsyncConnection) -> None:
    """Execute a single mode action."""
    action_type = action.get("type")
    command = action.get("command")
    value = action.get("value")

    if action_type == "device":
        # Direct device command
        device_id = action.get("device_id")
        if device_id:
            if value is not None:
                await hubitat.send_command(device_id, command, str(value))
            else:
                await hubitat.send_command(device_id, command)
        else:
            # Execute on all devices of type in specified rooms
            device_type = action.get("device_type")
            rooms = action.get("rooms")
            await _execute_on_device_type(hubitat, command, value, device_type, rooms, conn)

    elif action_type == "temperature":
        # Temperature command to all thermostats
        from app.services import devices as device_service

        thermostats = await device_service.get_thermostats(conn)
        for thermostat in thermostats:
            if value is not None:
                await hubitat.send_command(thermostat["hubitat_id"], command, str(value))
            else:
                await hubitat.send_command(thermostat["hubitat_id"], command)

    elif action_type == "delay":
        # Wait for specified seconds
        delay = action.get("seconds", 1)
        await asyncio.sleep(delay)


async def _execute_on_device_type(
    hubitat,
    command: str,
    value: Any,
    device_type: str | None,
    rooms: list[str] | None,
    conn: AsyncConnection,
) -> None:
    """Execute command on all devices of a type, optionally filtered by room."""
    from app.services import devices as device_service

    all_devices = await device_service.get_devices(conn)

    for device in all_devices:
        # Filter by type
        if device_type:
            dev_type = (device.get("type") or "").lower()
            caps = device.get("capabilities") or []
            caps_lower = [c.lower() for c in caps]

            if device_type == "light":
                if not ("switch" in dev_type or "dimmer" in dev_type or "light" in dev_type):
                    if not any("switch" in c or "level" in c for c in caps_lower):
                        continue
            elif device_type == "dimmer":
                if "dimmer" not in dev_type and "switchlevel" not in caps_lower:
                    continue
            elif device_type == "lock":
                if "lock" not in dev_type and "lock" not in caps_lower:
                    continue
            else:
                if device_type not in dev_type:
                    continue

        # Filter by room
        if rooms and device.get("room") not in rooms:
            continue

        # Execute command
        try:
            if value is not None:
                await hubitat.send_command(device["hubitat_id"], command, str(value))
            else:
                await hubitat.send_command(device["hubitat_id"], command)
        except Exception as e:
            logger.warning(f"Failed to execute {command} on {device['name']}: {e}")


async def get_mode_executions(
    conn: AsyncConnection, mode_id: int | None = None, limit: int = 50
) -> list[dict[str, Any]]:
    """Get mode execution history."""
    query = select(mode_executions).order_by(mode_executions.c.executed_at.desc()).limit(limit)
    if mode_id:
        query = query.where(mode_executions.c.mode_id == mode_id)

    result = await conn.execute(query)
    executions = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("error_details"):
            data["error_details"] = json.loads(data["error_details"])
        executions.append(data)
    return executions


async def create_default_modes(conn: AsyncConnection) -> None:
    """Create default modes if they don't exist."""
    for mode_data in DEFAULT_MODES:
        existing = await get_mode_by_name(conn, mode_data["name"])
        if not existing:
            await create_mode(
                conn,
                name=mode_data["name"],
                label=mode_data["label"],
                actions=mode_data["actions"],
                description=mode_data.get("description"),
                icon=mode_data.get("icon"),
                color=mode_data.get("color"),
            )
            # Update display_order separately
            mode = await get_mode_by_name(conn, mode_data["name"])
            if mode and mode_data.get("display_order"):
                await update_mode(conn, mode["id"], display_order=mode_data["display_order"])
            logger.info(f"Created default mode: {mode_data['label']}")
