"""Hubitat Maker API service for device control."""

import logging
from typing import Any

import httpx

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class HubitatService:
    """Service for interacting with Hubitat Maker API."""

    def __init__(self) -> None:
        self._base_url = settings.hubitat_base_url
        self._token = settings.hubitat_token

    def _build_url(self, endpoint: str) -> str:
        """Build full URL with access token."""
        separator = "&" if "?" in endpoint else "?"
        return f"{self._base_url}/{endpoint}{separator}access_token={self._token}"

    async def get_all_devices(self) -> list[dict[str, Any]]:
        """Get all devices from Hubitat."""
        url = self._build_url("devices/all")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch devices from Hubitat: {e}")
                raise

    async def get_device(self, device_id: int) -> dict[str, Any]:
        """Get a specific device from Hubitat."""
        url = self._build_url(f"devices/{device_id}")
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                return response.json()
            except httpx.HTTPError as e:
                logger.error(f"Failed to fetch device {device_id} from Hubitat: {e}")
                raise

    async def send_command(
        self, device_id: int, command: str, value: str | None = None
    ) -> dict[str, Any]:
        """Send a command to a Hubitat device.

        Args:
            device_id: Hubitat device ID
            command: Command to send (on, off, setLevel, etc.)
            value: Optional value for the command (e.g., level for setLevel)
        """
        if value is not None:
            url = self._build_url(f"devices/{device_id}/{command}/{value}")
        else:
            url = self._build_url(f"devices/{device_id}/{command}")

        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(url, timeout=30.0)
                response.raise_for_status()
                return {"success": True, "device_id": device_id, "command": command, "value": value}
            except httpx.HTTPError as e:
                logger.error(f"Failed to send command to device {device_id}: {e}")
                raise

    async def turn_on(self, device_id: int) -> dict[str, Any]:
        """Turn on a device."""
        return await self.send_command(device_id, "on")

    async def turn_off(self, device_id: int) -> dict[str, Any]:
        """Turn off a device."""
        return await self.send_command(device_id, "off")

    async def set_level(self, device_id: int, level: int) -> dict[str, Any]:
        """Set device level (0-100)."""
        level = max(0, min(100, level))  # Clamp to 0-100
        return await self.send_command(device_id, "setLevel", str(level))

    async def set_color_temperature(self, device_id: int, temp: int) -> dict[str, Any]:
        """Set color temperature (2700-6500K typical)."""
        return await self.send_command(device_id, "setColorTemperature", str(temp))

    async def lock(self, device_id: int) -> dict[str, Any]:
        """Lock a lock device."""
        return await self.send_command(device_id, "lock")

    async def unlock(self, device_id: int) -> dict[str, Any]:
        """Unlock a lock device."""
        return await self.send_command(device_id, "unlock")

    async def set_thermostat_heating_setpoint(
        self, device_id: int, temperature: float
    ) -> dict[str, Any]:
        """Set thermostat heating setpoint."""
        return await self.send_command(device_id, "setHeatingSetpoint", str(temperature))

    async def set_thermostat_cooling_setpoint(
        self, device_id: int, temperature: float
    ) -> dict[str, Any]:
        """Set thermostat cooling setpoint."""
        return await self.send_command(device_id, "setCoolingSetpoint", str(temperature))


# Singleton instance
_hubitat_service: HubitatService | None = None


def get_hubitat_service() -> HubitatService:
    """Get or create the Hubitat service singleton."""
    global _hubitat_service
    if _hubitat_service is None:
        _hubitat_service = HubitatService()
    return _hubitat_service
