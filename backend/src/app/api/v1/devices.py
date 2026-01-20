"""Device API endpoints."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.response import api_response
from app.db.database import get_connection
from app.schemas.devices import DeviceCreate, DeviceResponse, DeviceUpdate, DeviceWithState
from app.services import devices as device_service
from app.services.mqtt import get_mqtt_service

router = APIRouter(prefix="/devices", tags=["devices"])

mqtt_service = get_mqtt_service()


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


@router.get("", response_model=dict[str, Any])
async def list_devices(
    room: str | None = None,
    favorites: bool = False,
    include_hidden: bool = False,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """List all devices with optional filtering."""
    devices_list = await device_service.get_devices(
        conn, room=room, favorites_only=favorites, include_hidden=include_hidden
    )

    # Enrich with current state from MQTT
    enriched = []
    for device in devices_list:
        # Get state by device label or name (MQTT topic uses label/name)
        device_key = device.get("label") or device.get("name")
        state = mqtt_service.get_device_state(device_key) or {}
        enriched.append({**device, "state": state})

    return api_response(enriched)


@router.get("/rooms", response_model=dict[str, Any])
async def list_rooms(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """List all unique room names."""
    rooms = await device_service.get_rooms(conn)
    return api_response(rooms)


@router.get("/{device_id}", response_model=dict[str, Any])
async def get_device(device_id: int, conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Get a device by ID with current state."""
    device = await device_service.get_device_by_id(conn, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    # Get current state
    device_key = device.get("label") or device.get("name")
    state = mqtt_service.get_device_state(device_key) or {}

    return api_response({**device, "state": state})


@router.post("", response_model=dict[str, Any], status_code=status.HTTP_201_CREATED)
async def create_device(
    device: DeviceCreate, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Create a new device."""
    existing = await device_service.get_device_by_hubitat_id(conn, device.hubitat_id)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Device with hubitat_id {device.hubitat_id} already exists",
        )
    created = await device_service.create_device(conn, device)
    return api_response(created)


@router.patch("/{device_id}", response_model=dict[str, Any])
async def update_device(
    device_id: int, device_update: DeviceUpdate, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Update a device."""
    updated = await device_service.update_device(conn, device_id, device_update)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return api_response(updated)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_device(device_id: int, conn: AsyncConnection = Depends(get_conn)) -> None:
    """Delete a device."""
    deleted = await device_service.delete_device(conn, device_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")


@router.post("/sync", response_model=dict[str, Any])
async def sync_devices(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Sync devices from Hubitat Maker API.

    This endpoint fetches all devices from Hubitat and upserts them into the database.
    """
    # Import here to avoid circular imports
    from app.services.hubitat import get_hubitat_service

    hubitat = get_hubitat_service()
    hubitat_devices = await hubitat.get_all_devices()

    synced = []
    for hd in hubitat_devices:
        device_data = DeviceCreate(
            hubitat_id=hd["id"],
            name=hd.get("name", f"Device {hd['id']}"),
            label=hd.get("label"),
            type=hd.get("type", "Unknown"),
            capabilities=hd.get("capabilities", []),
        )
        result = await device_service.upsert_device(conn, device_data)
        synced.append(result)

    return api_response({"synced": len(synced), "devices": synced})


@router.post("/refresh-states", response_model=dict[str, Any])
async def refresh_device_states(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Refresh current states of all devices from Hubitat.

    This endpoint fetches current attributes (temperature, setpoint, switch state, etc)
    for all devices and updates them in the database.
    """
    from app.services.hubitat import get_hubitat_service

    hubitat = get_hubitat_service()

    # Get all devices from DB
    all_devices = await device_service.get_devices(conn, include_hidden=True)

    updated_count = 0
    errors = []

    for device in all_devices:
        try:
            # Fetch current state from Hubitat
            hubitat_device = await hubitat.get_device(device["hubitat_id"])

            # Update state in database
            if "attributes" in hubitat_device:
                await device_service.update_device_state(
                    conn,
                    device["id"],
                    hubitat_device["attributes"]
                )
                updated_count += 1
        except Exception as e:
            errors.append({"device_id": device["id"], "error": str(e)})

    # Commit all changes
    await conn.commit()

    return api_response({
        "updated": updated_count,
        "total": len(all_devices),
        "errors": errors
    })


@router.post("/{device_id}/command", response_model=dict[str, Any])
async def send_device_command(
    device_id: int,
    command: str,
    value: str | None = None,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Send a command to a device via Hubitat Maker API.

    Args:
        device_id: Internal device ID
        command: Command to send (on, off, setLevel, lock, unlock, etc.)
        value: Optional value for the command
    """
    from app.services.hubitat import get_hubitat_service

    # Get device to find hubitat_id
    device = await device_service.get_device_by_id(conn, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    hubitat = get_hubitat_service()
    try:
        result = await hubitat.send_command(device["hubitat_id"], command, value)
        return api_response(result)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to send command to Hubitat: {str(e)}",
        )


@router.post("/{device_id}/on", response_model=dict[str, Any])
async def turn_device_on(
    device_id: int, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Turn on a device."""
    result = await send_device_command(device_id, "on", None, conn)
    # Optimistic update: set switch_state to 'on' immediately
    print(f"[DEBUG] Updating device {device_id} switch_state to 'on'")
    await device_service.update_device_state(conn, device_id, [{"name": "switch", "currentValue": "on"}])
    await conn.commit()
    print(f"[DEBUG] Committed switch_state='on' for device {device_id}")
    return result


@router.post("/{device_id}/off", response_model=dict[str, Any])
async def turn_device_off(
    device_id: int, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Turn off a device."""
    result = await send_device_command(device_id, "off", None, conn)
    # Optimistic update: set switch_state to 'off' immediately
    print(f"[DEBUG] Updating device {device_id} switch_state to 'off'")
    await device_service.update_device_state(conn, device_id, [{"name": "switch", "currentValue": "off"}])
    await conn.commit()
    print(f"[DEBUG] Committed switch_state='off' for device {device_id}")
    return result


@router.post("/{device_id}/level/{level}", response_model=dict[str, Any])
async def set_device_level(
    device_id: int, level: int, conn: AsyncConnection = Depends(get_conn)
) -> dict[str, Any]:
    """Set device level (0-100)."""
    level = max(0, min(100, level))
    result = await send_device_command(device_id, "setLevel", str(level), conn)
    # Optimistic update: set level and switch state immediately
    switch_state = "on" if level > 0 else "off"
    await device_service.update_device_state(conn, device_id, [
        {"name": "level", "currentValue": level},
        {"name": "switch", "currentValue": switch_state}
    ])
    await conn.commit()
    return result
