"""Device service for CRUD operations."""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import delete, insert, select, update
from sqlalchemy.ext.asyncio import AsyncConnection

from app.models.devices import devices
from app.schemas.devices import DeviceCreate, DeviceUpdate


async def get_device_by_id(conn: AsyncConnection, device_id: int) -> dict[str, Any] | None:
    """Get a device by ID."""
    result = await conn.execute(select(devices).where(devices.c.id == device_id))
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    # Parse capabilities JSON
    if data.get("capabilities") and isinstance(data["capabilities"], str):
        data["capabilities"] = json.loads(data["capabilities"])
    return data


async def get_device_by_hubitat_id(conn: AsyncConnection, hubitat_id: int) -> dict[str, Any] | None:
    """Get a device by Hubitat ID."""
    result = await conn.execute(select(devices).where(devices.c.hubitat_id == hubitat_id))
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("capabilities") and isinstance(data["capabilities"], str):
        data["capabilities"] = json.loads(data["capabilities"])
    return data


async def get_devices(
    conn: AsyncConnection,
    room: str | None = None,
    favorites_only: bool = False,
    include_hidden: bool = False,
) -> list[dict[str, Any]]:
    """Get all devices with optional filtering."""
    query = select(devices)

    if room:
        query = query.where(devices.c.room == room)
    if favorites_only:
        query = query.where(devices.c.is_favorite == True)  # noqa: E712
    if not include_hidden:
        query = query.where(devices.c.is_hidden == False)  # noqa: E712

    query = query.order_by(devices.c.display_order.nulls_last(), devices.c.name)

    result = await conn.execute(query)
    device_list = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("capabilities"):
            data["capabilities"] = json.loads(data["capabilities"])
        device_list.append(data)
    return device_list


async def create_device(conn: AsyncConnection, device: DeviceCreate) -> dict[str, Any]:
    """Create a new device."""
    values = {
        "hubitat_id": device.hubitat_id,
        "name": device.name,
        "label": device.label,
        "type": device.type,
        "room": device.room,
        "is_favorite": device.is_favorite,
        "is_hidden": device.is_hidden,
        "display_order": device.display_order,
        "icon": device.icon,
        "capabilities": json.dumps(device.capabilities) if device.capabilities else None,
    }
    result = await conn.execute(insert(devices).values(**values).returning(devices))
    await conn.commit()
    row = result.fetchone()
    data = dict(row._mapping) if row else {}
    if data.get("capabilities") and isinstance(data["capabilities"], str):
        data["capabilities"] = json.loads(data["capabilities"])
    return data


async def update_device(
    conn: AsyncConnection, device_id: int, device_update: DeviceUpdate
) -> dict[str, Any] | None:
    """Update a device."""
    update_data = device_update.model_dump(exclude_unset=True)
    if not update_data:
        return await get_device_by_id(conn, device_id)

    update_data["updated_at"] = datetime.now(timezone.utc)
    result = await conn.execute(
        update(devices).where(devices.c.id == device_id).values(**update_data).returning(devices)
    )
    await conn.commit()
    row = result.fetchone()
    if not row:
        return None
    data = dict(row._mapping)
    if data.get("capabilities") and isinstance(data["capabilities"], str):
        data["capabilities"] = json.loads(data["capabilities"])
    return data


async def delete_device(conn: AsyncConnection, device_id: int) -> bool:
    """Delete a device."""
    result = await conn.execute(delete(devices).where(devices.c.id == device_id))
    await conn.commit()
    return result.rowcount > 0


async def upsert_device(conn: AsyncConnection, device: DeviceCreate) -> dict[str, Any]:
    """Create or update a device by hubitat_id."""
    existing = await get_device_by_hubitat_id(conn, device.hubitat_id)
    if existing:
        # Update existing
        update_data = {
            "name": device.name,
            "label": device.label,
            "type": device.type,
            "capabilities": json.dumps(device.capabilities) if device.capabilities else None,
            "updated_at": datetime.now(timezone.utc),
        }
        result = await conn.execute(
            update(devices)
            .where(devices.c.hubitat_id == device.hubitat_id)
            .values(**update_data)
            .returning(devices)
        )
        await conn.commit()
        row = result.fetchone()
        data = dict(row._mapping) if row else {}
    else:
        data = await create_device(conn, device)

    if data.get("capabilities") and isinstance(data["capabilities"], str):
        data["capabilities"] = json.loads(data["capabilities"])
    return data


async def get_rooms(conn: AsyncConnection) -> list[str]:
    """Get list of unique room names."""
    result = await conn.execute(
        select(devices.c.room)
        .where(devices.c.room.is_not(None))
        .distinct()
        .order_by(devices.c.room)
    )
    return [row[0] for row in result.fetchall()]


async def get_temperature_devices(conn: AsyncConnection) -> list[dict[str, Any]]:
    """Get all devices with temperature capabilities (sensors and thermostats)."""
    result = await conn.execute(
        select(devices).where(
            (devices.c.type.ilike("%thermostat%"))
            | (devices.c.type.ilike("%temperature%"))
            | (devices.c.type.ilike("%sensor%"))
            | (devices.c.capabilities.ilike("%temperature%"))
            | (devices.c.capabilities.ilike("%thermostat%"))
        )
    )
    device_list = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("capabilities"):
            data["capabilities"] = json.loads(data["capabilities"])
        device_list.append(data)
    return device_list


async def get_thermostats(conn: AsyncConnection) -> list[dict[str, Any]]:
    """Get only thermostat devices."""
    result = await conn.execute(
        select(devices).where(
            (devices.c.type.ilike("%thermostat%"))
            | (devices.c.capabilities.ilike("%thermostat%"))
        )
    )
    device_list = []
    for row in result.fetchall():
        data = dict(row._mapping)
        if data.get("capabilities"):
            data["capabilities"] = json.loads(data["capabilities"])
        device_list.append(data)
    return device_list


async def update_device_state(
    conn: AsyncConnection,
    device_id: int,
    attributes: list[dict[str, Any]]
) -> dict[str, Any] | None:
    """Update device state attributes (temperature, setpoint, mode, etc).

    Args:
        attributes: List of attribute objects from Hubitat with format:
            [{"name": "temperature", "currentValue": 22.2}, ...]
    """
    # Build update dict with only non-None values
    update_data: dict[str, Any] = {"updated_at": datetime.now(timezone.utc)}

    # Convert attributes list to dict for easier lookup
    attrs_dict = {attr["name"]: attr.get("currentValue") for attr in attributes}

    # Extract common attributes
    if "temperature" in attrs_dict:
        update_data["temperature"] = attrs_dict["temperature"]
    if "heatingSetpoint" in attrs_dict:
        update_data["heating_setpoint"] = attrs_dict["heatingSetpoint"]
    if "coolingSetpoint" in attrs_dict:
        update_data["cooling_setpoint"] = attrs_dict["coolingSetpoint"]
    if "thermostatMode" in attrs_dict:
        update_data["thermostat_mode"] = attrs_dict["thermostatMode"]
    if "thermostatOperatingState" in attrs_dict:
        update_data["operating_state"] = attrs_dict["thermostatOperatingState"]
    if "switch" in attrs_dict:
        update_data["switch_state"] = attrs_dict["switch"]
    if "level" in attrs_dict:
        update_data["level"] = attrs_dict["level"]
    if "battery" in attrs_dict:
        update_data["battery"] = attrs_dict["battery"]
    if "humidity" in attrs_dict:
        update_data["humidity"] = attrs_dict["humidity"]

    # Update the device
    await conn.execute(
        update(devices)
        .where(devices.c.id == device_id)
        .values(**update_data)
    )

    # Return updated device
    return await get_device_by_id(conn, device_id)
