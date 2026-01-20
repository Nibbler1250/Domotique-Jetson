"""Temperature API endpoints for climate control."""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.response import api_response
from app.db.database import get_connection
from app.services import devices as device_service
from app.services.hubitat import get_hubitat_service
from app.services.mqtt import get_mqtt_service

router = APIRouter(prefix="/temperature", tags=["temperature"])

mqtt_service = get_mqtt_service()


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


class TemperatureReading(BaseModel):
    """Temperature reading for a room or device."""

    device_id: int
    device_name: str
    room: str | None
    temperature: float | None = None
    humidity: float | None = None
    is_thermostat: bool = False
    heating_setpoint: float | None = None
    cooling_setpoint: float | None = None
    thermostat_mode: str | None = None
    operating_state: str | None = None


class SetTemperatureRequest(BaseModel):
    """Request to set thermostat temperature."""

    setpoint: float = Field(..., ge=15.0, le=30.0, description="Target temperature in Celsius")
    mode: str | None = Field(None, description="Thermostat mode: heat, cool, auto, off")


class TemperatureShortcut(BaseModel):
    """A temperature shortcut action."""

    name: str
    label: str
    delta: float = Field(..., description="Temperature change in Celsius")
    duration_minutes: int | None = Field(None, description="Duration before reverting (null = permanent)")


@router.get("", response_model=dict[str, Any])
async def get_temperature_overview(
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get temperature overview with all sensors and thermostats.

    Returns current temperature readings, thermostat setpoints, and
    device states organized by room.
    """
    temp_devices = await device_service.get_temperature_devices(conn)

    readings: list[dict[str, Any]] = []
    by_room: dict[str, list[dict[str, Any]]] = {}

    for device in temp_devices:
        # Determine if thermostat
        is_thermostat = (
            "thermostat" in (device.get("type") or "").lower()
            or any("thermostat" in cap.lower() for cap in (device.get("capabilities") or []))
        )

        reading = {
            "device_id": device["id"],
            "device_name": device.get("label") or device["name"],
            "room": device.get("room"),
            "temperature": device.get("temperature"),
            "humidity": device.get("humidity"),
            "is_thermostat": is_thermostat,
            "heating_setpoint": device.get("heating_setpoint"),
            "cooling_setpoint": device.get("cooling_setpoint"),
            "thermostat_mode": device.get("thermostat_mode"),
            "operating_state": device.get("operating_state"),
        }

        readings.append(reading)

        # Group by room
        room = device.get("room") or "Unassigned"
        if room not in by_room:
            by_room[room] = []
        by_room[room].append(reading)

    return api_response({
        "readings": readings,
        "by_room": by_room,
        "thermostats": [r for r in readings if r["is_thermostat"]],
        "sensors": [r for r in readings if not r["is_thermostat"]],
    })


@router.get("/rooms", response_model=dict[str, Any])
async def get_temperature_by_room(
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get temperature readings grouped by room.

    Returns the average/primary temperature per room.
    """
    temp_devices = await device_service.get_temperature_devices(conn)

    room_temps: dict[str, dict[str, Any]] = {}

    for device in temp_devices:
        room = device.get("room") or "Unassigned"
        temp = device.get("temperature")

        if temp is None:
            continue

        if room not in room_temps:
            room_temps[room] = {
                "room": room,
                "temperature": temp,
                "humidity": device.get("humidity"),
                "devices": [],
            }
        else:
            # Average temperatures if multiple sensors
            existing = room_temps[room]["temperature"]
            if existing is not None:
                room_temps[room]["temperature"] = (existing + temp) / 2

        room_temps[room]["devices"].append({
            "device_id": device["id"],
            "device_name": device.get("label") or device["name"],
            "temperature": temp,
        })

    return api_response(list(room_temps.values()))


@router.get("/thermostats", response_model=dict[str, Any])
async def get_thermostats(
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Get all thermostats with their current state and setpoints."""
    thermostats = await device_service.get_thermostats(conn)

    result = []
    for device in thermostats:
        device_key = device.get("label") or device.get("name")
        state = mqtt_service.get_device_state(device_key) or {}

        result.append({
            "device_id": device["id"],
            "hubitat_id": device["hubitat_id"],
            "device_name": device.get("label") or device["name"],
            "room": device.get("room"),
            "temperature": state.get("temperature"),
            "heating_setpoint": state.get("heatingSetpoint"),
            "cooling_setpoint": state.get("coolingSetpoint"),
            "thermostat_mode": state.get("thermostatMode"),
            "operating_state": state.get("thermostatOperatingState"),
            "humidity": state.get("humidity"),
        })

    return api_response(result)


@router.post("/{device_id}/setpoint", response_model=dict[str, Any])
async def set_thermostat_temperature(
    device_id: int,
    request: SetTemperatureRequest,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Set thermostat temperature.

    Args:
        device_id: Internal device ID
        request: Temperature setpoint and optional mode
    """
    device = await device_service.get_device_by_id(conn, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    hubitat = get_hubitat_service()

    try:
        # Set heating setpoint
        await hubitat.send_command(device["hubitat_id"], "setHeatingSetpoint", str(request.setpoint))

        # Optionally set mode
        if request.mode:
            await hubitat.send_command(device["hubitat_id"], "setThermostatMode", request.mode)

        return api_response({
            "success": True,
            "device_id": device_id,
            "setpoint": request.setpoint,
            "mode": request.mode,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to set temperature: {str(e)}",
        )


@router.post("/{device_id}/adjust", response_model=dict[str, Any])
async def adjust_temperature(
    device_id: int,
    delta: float,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Adjust thermostat temperature by a delta value.

    Args:
        device_id: Internal device ID
        delta: Temperature change in Celsius (positive = warmer, negative = cooler)
    """
    device = await device_service.get_device_by_id(conn, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    # Get current setpoint from MQTT state
    device_key = device.get("label") or device.get("name")
    state = mqtt_service.get_device_state(device_key) or {}
    current_setpoint = state.get("heatingSetpoint")

    if current_setpoint is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot determine current setpoint",
        )

    new_setpoint = max(15.0, min(30.0, float(current_setpoint) + delta))

    hubitat = get_hubitat_service()

    try:
        await hubitat.send_command(device["hubitat_id"], "setHeatingSetpoint", str(new_setpoint))

        return api_response({
            "success": True,
            "device_id": device_id,
            "previous_setpoint": current_setpoint,
            "new_setpoint": new_setpoint,
            "delta": delta,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to adjust temperature: {str(e)}",
        )


# Shortcuts configuration (could be moved to config/database later)
TEMPERATURE_SHORTCUTS = [
    TemperatureShortcut(
        name="j_ai_frette",
        label="J'ai frette",
        delta=1.5,
        duration_minutes=120,
    ),
    TemperatureShortcut(
        name="j_ai_chaud",
        label="J'ai chaud",
        delta=-1.5,
        duration_minutes=120,
    ),
    TemperatureShortcut(
        name="mode_economie",
        label="Mode économie",
        delta=-2.0,
        duration_minutes=None,  # Permanent
    ),
    TemperatureShortcut(
        name="mode_confort",
        label="Mode confort",
        delta=1.0,
        duration_minutes=None,
    ),
]


@router.get("/shortcuts", response_model=dict[str, Any])
async def get_shortcuts() -> dict[str, Any]:
    """Get available temperature shortcuts."""
    return api_response([s.model_dump() for s in TEMPERATURE_SHORTCUTS])


@router.post("/{device_id}/shortcut/{shortcut_name}", response_model=dict[str, Any])
async def apply_shortcut(
    device_id: int,
    shortcut_name: str,
    conn: AsyncConnection = Depends(get_conn),
) -> dict[str, Any]:
    """Apply a temperature shortcut to a thermostat.

    Args:
        device_id: Internal device ID
        shortcut_name: Name of the shortcut to apply
    """
    # Find shortcut
    shortcut = next((s for s in TEMPERATURE_SHORTCUTS if s.name == shortcut_name), None)
    if not shortcut:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Shortcut '{shortcut_name}' not found",
        )

    # Apply the delta
    device = await device_service.get_device_by_id(conn, device_id)
    if not device:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")

    device_key = device.get("label") or device.get("name")
    state = mqtt_service.get_device_state(device_key) or {}
    current_setpoint = state.get("heatingSetpoint")

    if current_setpoint is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot determine current setpoint",
        )

    new_setpoint = max(15.0, min(30.0, float(current_setpoint) + shortcut.delta))

    hubitat = get_hubitat_service()

    try:
        await hubitat.send_command(device["hubitat_id"], "setHeatingSetpoint", str(new_setpoint))

        return api_response({
            "success": True,
            "device_id": device_id,
            "shortcut": shortcut.label,
            "previous_setpoint": current_setpoint,
            "new_setpoint": new_setpoint,
            "duration_minutes": shortcut.duration_minutes,
        })
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Failed to apply shortcut: {str(e)}",
        )
