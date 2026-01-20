"""Integration status API endpoints."""

import asyncio
from datetime import datetime, timezone
from typing import Any

import httpx
from fastapi import APIRouter, Depends, HTTPException, status

from app.api.v1.auth import get_current_user
from app.core.config import get_settings
from app.core.response import api_response
from app.services.mqtt import get_mqtt_service

router = APIRouter(prefix="/integrations", tags=["integrations"])

settings = get_settings()


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
    """Require admin role."""
    if current_user["role"] != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user


async def check_hubitat_status() -> dict[str, Any]:
    """Check Hubitat hub connectivity."""
    hubitat_url = settings.hubitat_base_url
    hubitat_token = settings.hubitat_token

    if not settings.hubitat_host or not hubitat_token:
        return {
            "name": "Hubitat",
            "status": "not_configured",
            "message": "Hubitat URL or token not configured",
            "url": None,
        }

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            # Try to get hub info
            response = await client.get(
                f"{hubitat_url}/hub/advanced/freeOSMemory",
                params={"access_token": hubitat_token},
            )
            if response.status_code == 200:
                return {
                    "name": "Hubitat",
                    "status": "connected",
                    "message": "Hub responding",
                    "url": hubitat_url,
                }
            else:
                return {
                    "name": "Hubitat",
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "url": hubitat_url,
                }
    except httpx.TimeoutException:
        return {
            "name": "Hubitat",
            "status": "timeout",
            "message": "Connection timeout",
            "url": hubitat_url,
        }
    except Exception as e:
        return {
            "name": "Hubitat",
            "status": "error",
            "message": str(e),
            "url": hubitat_url,
        }


async def check_mqtt_status() -> dict[str, Any]:
    """Check MQTT broker connectivity."""
    mqtt_service = get_mqtt_service()

    if mqtt_service.is_connected:
        return {
            "name": "MQTT",
            "status": "connected",
            "message": "Connected to broker",
            "broker": settings.mqtt_host,
            "port": settings.mqtt_port,
        }
    else:
        return {
            "name": "MQTT",
            "status": "disconnected",
            "message": "Not connected to broker",
            "broker": settings.mqtt_host,
            "port": settings.mqtt_port,
        }


async def check_mistral_brain_status() -> dict[str, Any]:
    """Check Mistral Brain service connectivity."""
    brain_url = getattr(settings, "mistral_brain_url", None)

    if not brain_url:
        # Try default Jetson URL
        brain_url = "http://192.168.1.118:5000"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{brain_url}/api/status")
            if response.status_code == 200:
                data = response.json()
                return {
                    "name": "Mistral Brain",
                    "status": "connected",
                    "message": "Brain service responding",
                    "url": brain_url,
                    "automations_count": data.get("automations_count", 0),
                }
            else:
                return {
                    "name": "Mistral Brain",
                    "status": "error",
                    "message": f"HTTP {response.status_code}",
                    "url": brain_url,
                }
    except httpx.TimeoutException:
        return {
            "name": "Mistral Brain",
            "status": "timeout",
            "message": "Connection timeout",
            "url": brain_url,
        }
    except Exception:
        return {
            "name": "Mistral Brain",
            "status": "unavailable",
            "message": "Service not reachable",
            "url": brain_url,
        }


@router.get("", response_model=dict[str, Any])
async def get_integrations_status(
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    """Get status of all integrations.

    Returns status for:
    - Hubitat hub
    - MQTT broker
    - Mistral Brain service
    """
    # Run all checks concurrently
    hubitat, mqtt, brain = await asyncio.gather(
        check_hubitat_status(),
        check_mqtt_status(),
        check_mistral_brain_status(),
    )

    integrations = [hubitat, mqtt, brain]

    # Calculate overall health
    connected_count = sum(1 for i in integrations if i["status"] == "connected")
    total_count = len(integrations)

    return api_response({
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "overall_status": "healthy" if connected_count == total_count else "degraded",
        "connected": connected_count,
        "total": total_count,
        "integrations": integrations,
    })


@router.get("/hubitat", response_model=dict[str, Any])
async def get_hubitat_status(
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    """Get detailed Hubitat status."""
    status_info = await check_hubitat_status()

    if status_info["status"] == "connected":
        # Get more details
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(
                    f"{settings.hubitat_base_url}/devices",
                    params={"access_token": settings.hubitat_token},
                )
                if response.status_code == 200:
                    devices = response.json()
                    status_info["devices_count"] = len(devices)
        except Exception:
            pass

    return api_response(status_info)


@router.get("/mqtt", response_model=dict[str, Any])
async def get_mqtt_status(
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    """Get detailed MQTT status."""
    return api_response(await check_mqtt_status())


@router.get("/brain", response_model=dict[str, Any])
async def get_brain_status(
    current_user: dict = Depends(require_admin),
) -> dict[str, Any]:
    """Get detailed Mistral Brain status."""
    return api_response(await check_mistral_brain_status())
