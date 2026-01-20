"""Configuration export/import API endpoints."""

import json
from datetime import datetime, timezone
from typing import Any

import yaml
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncConnection

from app.api.v1.auth import get_current_user
from app.core.response import api_response
from app.db.database import get_connection
from app.services import automations as automation_service
from app.services import devices as device_service
from app.services import modes as mode_service
from app.services import profiles as profile_service

router = APIRouter(prefix="/config", tags=["config"])


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


@router.get("/export", response_class=Response)
async def export_config(
    current_user: dict = Depends(require_admin),
    conn: AsyncConnection = Depends(get_conn),
) -> Response:
    """Export full configuration as YAML file.

    Includes:
    - Modes and their actions
    - Automations (from database)
    - Device favorites and display settings
    - User profiles (themes, preferences)
    """
    config: dict[str, Any] = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "exported_by": current_user["username"],
    }

    # Export modes
    modes = await mode_service.get_modes(conn)
    config["modes"] = [
        {
            "name": mode["name"],
            "label": mode["label"],
            "description": mode.get("description"),
            "icon": mode.get("icon"),
            "color": mode.get("color"),
            "actions": json.loads(mode["actions"]) if isinstance(mode["actions"], str) else mode["actions"],
            "is_enabled": mode["is_enabled"],
            "display_order": mode.get("display_order"),
        }
        for mode in modes
    ]

    # Export automations
    automations = await automation_service.get_automations(conn)
    config["automations"] = [
        {
            "brain_name": a["brain_name"],
            "label": a["label"],
            "description": a.get("description"),
            "trigger_type": a.get("trigger_type"),
            "is_enabled": a["is_enabled"],
        }
        for a in automations
    ]

    # Export device preferences (favorites, hidden, etc.)
    devices = await device_service.get_devices(conn, include_hidden=True)
    config["devices"] = [
        {
            "hubitat_id": d["hubitat_id"],
            "name": d["name"],
            "label": d.get("label"),
            "room": d.get("room"),
            "is_favorite": d.get("is_favorite", False),
            "is_hidden": d.get("is_hidden", False),
            "display_order": d.get("display_order"),
        }
        for d in devices
    ]

    # Convert to YAML
    yaml_content = yaml.dump(config, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # Return as downloadable file
    filename = f"family-hub-config-{datetime.now().strftime('%Y%m%d-%H%M%S')}.yaml"
    return Response(
        content=yaml_content,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.post("/import", response_model=dict[str, Any])
async def import_config(
    file: UploadFile = File(...),
    current_user: dict = Depends(require_admin),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Import configuration from YAML file.

    Updates existing entries, creates new ones.
    Does NOT delete entries not in the import file.
    """
    # Validate file type
    if not file.filename or not file.filename.endswith((".yaml", ".yml")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be a YAML file (.yaml or .yml)",
        )

    # Parse YAML
    try:
        content = await file.read()
        config = yaml.safe_load(content.decode("utf-8"))
    except yaml.YAMLError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid YAML: {e!s}",
        )
    except UnicodeDecodeError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be UTF-8 encoded",
        )

    # Validate structure
    if not isinstance(config, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid config structure",
        )

    stats = {
        "modes_imported": 0,
        "modes_updated": 0,
        "automations_imported": 0,
        "devices_updated": 0,
    }

    # Import modes
    if "modes" in config and isinstance(config["modes"], list):
        for mode_data in config["modes"]:
            name = mode_data.get("name")
            if not name:
                continue

            # Check if mode exists
            existing = await mode_service.get_mode_by_name(conn, name)
            if existing:
                # Update
                await mode_service.update_mode(
                    conn,
                    existing["id"],
                    label=mode_data.get("label"),
                    description=mode_data.get("description"),
                    icon=mode_data.get("icon"),
                    color=mode_data.get("color"),
                    actions=mode_data.get("actions"),
                    is_enabled=mode_data.get("is_enabled"),
                    display_order=mode_data.get("display_order"),
                )
                stats["modes_updated"] += 1
            else:
                # Create
                await mode_service.create_mode(
                    conn,
                    name=name,
                    label=mode_data.get("label", name),
                    description=mode_data.get("description"),
                    icon=mode_data.get("icon"),
                    color=mode_data.get("color"),
                    actions=mode_data.get("actions", []),
                )
                stats["modes_imported"] += 1

    # Import automations (just sync from database, don't create new)
    if "automations" in config and isinstance(config["automations"], list):
        for auto_data in config["automations"]:
            brain_name = auto_data.get("brain_name")
            if not brain_name:
                continue

            # Check if automation exists
            existing = await automation_service.get_automation_by_name(conn, brain_name)
            if existing:
                # Update enabled status
                await automation_service.update_automation(
                    conn,
                    existing["id"],
                    is_enabled=auto_data.get("is_enabled", True),
                )
                stats["automations_imported"] += 1

    # Import device preferences
    if "devices" in config and isinstance(config["devices"], list):
        for device_data in config["devices"]:
            hubitat_id = device_data.get("hubitat_id")
            if not hubitat_id:
                continue

            # Find device by hubitat_id
            existing = await device_service.get_device_by_hubitat_id(conn, hubitat_id)
            if existing:
                # Update preferences
                await device_service.update_device(
                    conn,
                    existing["id"],
                    label=device_data.get("label"),
                    room=device_data.get("room"),
                    is_favorite=device_data.get("is_favorite"),
                    is_hidden=device_data.get("is_hidden"),
                    display_order=device_data.get("display_order"),
                )
                stats["devices_updated"] += 1

    return api_response({
        "success": True,
        "message": "Configuration imported successfully",
        "stats": stats,
    })


@router.get("/export/json", response_model=dict[str, Any])
async def export_config_json(
    current_user: dict = Depends(require_admin),
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Export configuration as JSON (for API consumption)."""
    config: dict[str, Any] = {
        "version": "1.0",
        "exported_at": datetime.now(timezone.utc).isoformat(),
    }

    # Export modes
    modes = await mode_service.get_modes(conn)
    config["modes"] = [
        {
            "name": mode["name"],
            "label": mode["label"],
            "actions_count": len(json.loads(mode["actions"]) if isinstance(mode["actions"], str) else mode["actions"]),
            "is_enabled": mode["is_enabled"],
        }
        for mode in modes
    ]

    # Export automations count
    automations = await automation_service.get_automations(conn)
    config["automations_count"] = len(automations)
    config["automations_enabled"] = sum(1 for a in automations if a["is_enabled"])

    # Export devices count
    devices = await device_service.get_devices(conn)
    config["devices_count"] = len(devices)
    config["devices_favorite"] = sum(1 for d in devices if d.get("is_favorite"))

    return api_response(config)
