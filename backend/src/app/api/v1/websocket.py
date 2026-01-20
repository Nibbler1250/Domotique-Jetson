"""WebSocket endpoint for real-time device state updates."""

import asyncio
import json
import logging
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.services.mqtt import get_mqtt_service

logger = logging.getLogger(__name__)
router = APIRouter(tags=["websocket"])


class ConnectionManager:
    """Manage WebSocket connections."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)
        logger.info(f"WebSocket connected. Total: {len(self.active_connections)}")

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)
        logger.info(f"WebSocket disconnected. Total: {len(self.active_connections)}")

    async def broadcast(self, message: dict[str, Any]) -> None:
        """Broadcast message to all connected clients."""
        if not self.active_connections:
            return

        data = json.dumps(message)
        async with self._lock:
            disconnected = []
            for connection in self.active_connections:
                try:
                    await connection.send_text(data)
                except Exception:
                    disconnected.append(connection)

            # Clean up disconnected
            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)


# Singleton connection manager
manager = ConnectionManager()


def create_ws_message(msg_type: str, payload: Any) -> dict[str, Any]:
    """Create a WebSocket message in standard format."""
    return {
        "type": msg_type,
        "payload": payload,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def on_device_state_change(device_id: str, attribute: str, value: Any) -> None:
    """Callback for MQTT state changes - broadcasts to WebSocket clients."""
    message = create_ws_message(
        "device_state",
        {
            "device_id": device_id,
            "attribute": attribute,
            "value": value,
        },
    )
    # Schedule broadcast in event loop
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(manager.broadcast(message))
    except RuntimeError:
        # No running loop - skip
        pass


# Register MQTT callback
mqtt_service = get_mqtt_service()
mqtt_service.add_callback(on_device_state_change)


@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket) -> None:
    """WebSocket endpoint for real-time updates.

    Messages sent to client:
    - device_state: { device_id, attribute, value }
    - initial_state: { devices: { device_id: { attr: value } } }
    - pong: {} (response to ping)

    Messages from client:
    - ping: {} (keepalive)
    - subscribe: { device_ids: [...] } (future: selective subscription)
    """
    await manager.connect(websocket)

    try:
        # Send initial state
        initial_state = mqtt_service.device_states
        await websocket.send_text(
            json.dumps(create_ws_message("initial_state", {"devices": initial_state}))
        )

        # Listen for client messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type", "")

                if msg_type == "ping":
                    await websocket.send_text(json.dumps(create_ws_message("pong", {})))

            except json.JSONDecodeError:
                logger.warning("Invalid JSON received from WebSocket client")

    except WebSocketDisconnect:
        await manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await manager.disconnect(websocket)
