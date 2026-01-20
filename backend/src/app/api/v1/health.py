"""System health API endpoints."""

import asyncio
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection

from app.core.config import get_settings
from app.core.response import api_response
from app.db.database import get_connection
from app.services.mqtt import get_mqtt_service

router = APIRouter(prefix="/health", tags=["health"])

settings = get_settings()


async def get_conn():
    """Dependency to get database connection."""
    async with get_connection() as conn:
        yield conn


@router.get("/system", response_model=dict[str, Any])
async def get_system_health(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Get comprehensive system health status.

    Returns status of all system components:
    - Database connectivity
    - MQTT broker connection
    - Hubitat API availability
    - Mistral Brain status
    - Node-RED status
    """
    health = {
        "status": "healthy",
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "components": {},
    }

    # Check database
    try:
        await conn.execute(text("SELECT 1"))
        health["components"]["database"] = {
            "status": "healthy",
            "type": "SQLite",
        }
    except Exception as e:
        health["components"]["database"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health["status"] = "degraded"

    # Check MQTT
    mqtt_service = get_mqtt_service()
    health["components"]["mqtt"] = {
        "status": "healthy" if mqtt_service.is_connected else "disconnected",
        "broker": f"{settings.mqtt_host}:{settings.mqtt_port}",
        "devices_tracked": len(mqtt_service.device_states),
    }
    if not mqtt_service.is_connected:
        health["status"] = "degraded"

    # Check Hubitat
    try:
        from app.services.hubitat import get_hubitat_service

        hubitat = get_hubitat_service()
        # Quick connectivity check
        await asyncio.wait_for(hubitat.get_all_devices(), timeout=5.0)
        health["components"]["hubitat"] = {
            "status": "healthy",
            "url": hubitat.base_url,
        }
    except asyncio.TimeoutError:
        health["components"]["hubitat"] = {
            "status": "timeout",
            "error": "Connection timeout",
        }
        health["status"] = "degraded"
    except Exception as e:
        health["components"]["hubitat"] = {
            "status": "unhealthy",
            "error": str(e),
        }
        health["status"] = "degraded"

    # Check Mistral Brain (optional)
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://192.168.1.118:1880/automation/list")
            if response.status_code == 200:
                health["components"]["mistral_brain"] = {
                    "status": "healthy",
                    "url": "http://192.168.1.118:1880",
                }
            else:
                health["components"]["mistral_brain"] = {
                    "status": "degraded",
                    "error": f"HTTP {response.status_code}",
                }
    except Exception as e:
        health["components"]["mistral_brain"] = {
            "status": "unavailable",
            "error": str(e),
        }
        # Mistral Brain is optional, don't degrade overall status

    # Check Node-RED
    try:
        import httpx

        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get("http://192.168.1.118:1880")
            health["components"]["nodered"] = {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "url": "http://192.168.1.118:1880",
            }
    except Exception as e:
        health["components"]["nodered"] = {
            "status": "unavailable",
            "error": str(e),
        }

    return api_response(health)


@router.get("/devices", response_model=dict[str, Any])
async def get_devices_health(conn: AsyncConnection = Depends(get_conn)) -> dict[str, Any]:
    """Get device health overview.

    Returns counts and status of devices from MQTT state.
    """
    from app.services import devices as device_service

    mqtt_service = get_mqtt_service()
    device_states = mqtt_service.device_states

    # Get device count from database
    all_devices = await device_service.get_devices(conn)

    online = 0
    offline = 0
    low_battery = []

    for device in all_devices:
        device_key = device.get("label") or device.get("name")
        state = device_states.get(device_key, {})

        if state:
            online += 1
            # Check battery
            battery = state.get("battery")
            if battery is not None and int(battery) < 20:
                low_battery.append({
                    "name": device.get("name"),
                    "battery": battery,
                })
        else:
            offline += 1

    return api_response({
        "total_devices": len(all_devices),
        "online": online,
        "offline": offline,
        "low_battery_count": len(low_battery),
        "low_battery_devices": low_battery,
    })


@router.get("/services", response_model=dict[str, Any])
async def get_services_status() -> dict[str, Any]:
    """Get status of external services.

    Quick ping check to all external services.
    """
    import httpx

    services = [
        {"name": "Hubitat", "url": "http://192.168.1.66", "timeout": 3},
        {"name": "Node-RED", "url": "http://192.168.1.118:1880", "timeout": 3},
        {"name": "Node-RED UI", "url": "http://192.168.1.118:1880/ui", "timeout": 3},
    ]

    results = []

    async with httpx.AsyncClient() as client:
        for service in services:
            try:
                start = datetime.now()
                response = await client.get(
                    service["url"],
                    timeout=service["timeout"],
                    follow_redirects=True,
                )
                latency = (datetime.now() - start).total_seconds() * 1000

                results.append({
                    "name": service["name"],
                    "url": service["url"],
                    "status": "online" if response.status_code < 400 else "error",
                    "latency_ms": round(latency, 1),
                    "http_status": response.status_code,
                })
            except httpx.TimeoutException:
                results.append({
                    "name": service["name"],
                    "url": service["url"],
                    "status": "timeout",
                    "latency_ms": None,
                })
            except Exception as e:
                results.append({
                    "name": service["name"],
                    "url": service["url"],
                    "status": "offline",
                    "error": str(e),
                })

    return api_response(results)
