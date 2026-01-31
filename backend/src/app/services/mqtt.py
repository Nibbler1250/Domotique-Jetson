"""MQTT service for Hubitat device state subscriptions."""

import asyncio
import logging
from collections.abc import Callable
from typing import Any

import aiomqtt

from app.core.config import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()


class MQTTService:
    """MQTT client service for subscribing to Hubitat device states."""

    def __init__(self) -> None:
        self._client: aiomqtt.Client | None = None
        self._running = False
        self._callbacks: list[Callable[[str, str, Any], None]] = []
        self._device_states: dict[str, dict[str, Any]] = {}
        self._reconnect_interval = 5

    @property
    def is_connected(self) -> bool:
        """Check if MQTT client is connected."""
        return self._client is not None and self._running

    @property
    def device_states(self) -> dict[str, dict[str, Any]]:
        """Get current device states."""
        return self._device_states.copy()

    def add_callback(self, callback: Callable[[str, str, Any], None]) -> None:
        """Add a callback for state changes.

        Callback signature: (device_id: str, attribute: str, value: Any) -> None
        """
        self._callbacks.append(callback)

    def remove_callback(self, callback: Callable[[str, str, Any], None]) -> None:
        """Remove a callback."""
        if callback in self._callbacks:
            self._callbacks.remove(callback)

    def _parse_topic(self, topic: str) -> tuple[str, str] | None:
        """Parse MQTT topic to extract hubitat_id and attribute.

        Topic format: hubitat/genius-hub-000d/{slugified-label}-{hubitat_id}/{attribute}
        Example: hubitat/genius-hub-000d/plancher-cuisine-13/temperature
        Returns: ("13", "temperature") - using hubitat_id as device key
        """
        parts = topic.split("/")
        if len(parts) < 4:
            return None

        # Device slug is parts[2] (e.g., "plancher-cuisine-13")
        # Extract hubitat_id from the end (last number after hyphen)
        device_slug = parts[2]
        attribute = parts[3]

        # Extract hubitat_id: find the last hyphen and get the number after it
        last_hyphen = device_slug.rfind("-")
        if last_hyphen != -1:
            potential_id = device_slug[last_hyphen + 1:]
            if potential_id.isdigit():
                hubitat_id = potential_id
            else:
                # No numeric ID found, use full slug as fallback
                hubitat_id = device_slug
        else:
            hubitat_id = device_slug

        return hubitat_id, attribute

    def _parse_value(self, payload: str) -> Any:
        """Parse payload value."""
        # Try to convert to appropriate type
        if payload.lower() in ("true", "on", "active"):
            return True
        if payload.lower() in ("false", "off", "inactive"):
            return False
        try:
            return int(payload)
        except ValueError:
            pass
        try:
            return float(payload)
        except ValueError:
            pass
        return payload

    async def _handle_message(self, message: aiomqtt.Message) -> None:
        """Handle incoming MQTT message."""
        topic = str(message.topic)
        payload = message.payload.decode("utf-8") if message.payload else ""

        parsed = self._parse_topic(topic)
        if not parsed:
            return

        device_id, attribute = parsed
        value = self._parse_value(payload)

        # Update state cache
        if device_id not in self._device_states:
            self._device_states[device_id] = {}
        self._device_states[device_id][attribute] = value

        logger.debug(f"MQTT: {device_id}/{attribute} = {value}")

        # Notify callbacks
        for callback in self._callbacks:
            try:
                callback(device_id, attribute, value)
            except Exception as e:
                logger.error(f"Error in MQTT callback: {e}")

    async def start(self) -> None:
        """Start MQTT client and subscribe to topics."""
        if self._running:
            return

        self._running = True
        topic = f"{settings.mqtt_topic_prefix}/#"

        while self._running:
            try:
                async with aiomqtt.Client(
                    hostname=settings.mqtt_host,
                    port=settings.mqtt_port,
                ) as client:
                    self._client = client
                    logger.info(f"MQTT connected to {settings.mqtt_host}:{settings.mqtt_port}")

                    await client.subscribe(topic)
                    logger.info(f"MQTT subscribed to {topic}")

                    async for message in client.messages:
                        await self._handle_message(message)

            except aiomqtt.MqttError as e:
                logger.warning(f"MQTT connection error: {e}")
                self._client = None
                if self._running:
                    logger.info(f"Reconnecting in {self._reconnect_interval}s...")
                    await asyncio.sleep(self._reconnect_interval)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"MQTT unexpected error: {e}")
                self._client = None
                if self._running:
                    await asyncio.sleep(self._reconnect_interval)

        self._client = None
        logger.info("MQTT client stopped")

    async def stop(self) -> None:
        """Stop MQTT client."""
        self._running = False
        if self._client:
            # Client will be closed by the context manager
            pass

    def get_device_state(self, device_id: str) -> dict[str, Any] | None:
        """Get current state for a specific device."""
        return self._device_states.get(device_id)


# Singleton instance
_mqtt_service: MQTTService | None = None


def get_mqtt_service() -> MQTTService:
    """Get or create the MQTT service singleton."""
    global _mqtt_service
    if _mqtt_service is None:
        _mqtt_service = MQTTService()
    return _mqtt_service
