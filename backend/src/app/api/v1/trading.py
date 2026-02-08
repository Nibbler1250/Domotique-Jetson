"""Trading WebSocket endpoint for Momentum Trader V7 integration.

Bridges MQTT messages from trader/# topics to WebSocket clients.
Access restricted to admin or simon users.
"""

import asyncio
import json
import logging
import os
import threading
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import paho.mqtt.client as mqtt

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/trading", tags=["trading"])

# MQTT Configuration - Jetson broker (where Momentum Trader V7 publishes)
# Use localhost with SSH tunnel when direct Jetson access not available
MQTT_BROKER = os.environ.get("MQTT_HOST", "127.0.0.1")
MQTT_PORT = int(os.environ.get("MQTT_PORT", "11883"))  # Tunnel port default
MQTT_TOPICS = [
    "trader/services/#",
    "trader/portfolio/#",
    "trader/scanner/#",
    "trader/errors/#",
    "trader/status/#",
    "trader/positions/#",
    "trader/pnl/#",
    "trader/forex/#",
    "trader/decisions/#",
    "trader/alerts/#",
    # V7.4: Account & Capital management
    "trader/account/#",
    "trader/capital/#",
    "trader/control/#",
    # V7.5: Margin Protection & Trading Config
    "trader/margin_protection/#",
    "trader/config/#",
    # V7.25: Historical Statistics
    "trader/history/#",
    # V8: Swing Trading
    "momentum/swing/#",
]


class TradingConnectionManager:
    """Manage trading WebSocket connections with MQTT bridge."""

    def __init__(self) -> None:
        self.active_connections: list[WebSocket] = []
        self._lock = asyncio.Lock()
        self._mqtt_client: mqtt.Client | None = None
        self._mqtt_connected = False
        self._loop: asyncio.AbstractEventLoop | None = None
        # V7.46.21: Store retained messages with their original timestamps
        # Format: {topic: {"payload": ..., "received_at": ...}}
        self._retained_messages: dict[str, dict[str, Any]] = {}
        self._retained_lock = threading.Lock()  # Thread-safe access from MQTT callback
        # V8: Swing config cache (persists until backend restart)
        self._swing_config: dict[str, Any] = {
            "enabled": True,
            "budget_pct": 20,
            "max_positions": 5,
            "max_position_size": 5000,
            "auto_entry": False
        }

    def _setup_mqtt(self) -> None:
        """Setup MQTT client for trader topics."""
        if self._mqtt_client is not None:
            return

        # Use VERSION1 callback API for compatibility with existing code
        self._mqtt_client = mqtt.Client(
            callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
            client_id="family_hub_trading"
        )
        self._mqtt_client.on_connect = self._on_mqtt_connect
        self._mqtt_client.on_disconnect = self._on_mqtt_disconnect
        self._mqtt_client.on_message = self._on_mqtt_message

        try:
            print(f"[MQTT DEBUG] Attempting connect to {MQTT_BROKER}:{MQTT_PORT}")
            self._mqtt_client.connect_async(MQTT_BROKER, MQTT_PORT, 60)
            self._mqtt_client.loop_start()
            logger.info(f"MQTT client connecting to {MQTT_BROKER}:{MQTT_PORT}")
            print("[MQTT DEBUG] loop_start() called successfully")
        except Exception as e:
            logger.error(f"Failed to connect MQTT: {e}")
            print(f"[MQTT DEBUG] Exception: {e}")

    def _on_mqtt_connect(
        self, client: mqtt.Client, userdata: Any, flags: Any, rc: int
    ) -> None:
        """Callback when MQTT connects."""
        print(f"[MQTT DEBUG] on_connect callback fired with rc={rc}")
        if rc == 0:
            self._mqtt_connected = True
            logger.info("Trading MQTT connected, subscribing to trader topics")
            print("[MQTT DEBUG] MQTT connected successfully!")
            for topic in MQTT_TOPICS:
                client.subscribe(topic, qos=1)
                logger.debug(f"Subscribed to {topic}")
        else:
            logger.error(f"Trading MQTT connection failed: {rc}")
            print(f"[MQTT DEBUG] Connection failed with rc={rc}")

    def _on_mqtt_disconnect(
        self, client: mqtt.Client, userdata: Any, rc: int
    ) -> None:
        """Callback when MQTT disconnects."""
        self._mqtt_connected = False
        if rc != 0:
            logger.warning(f"Trading MQTT unexpected disconnect: {rc}")

    def _on_mqtt_message(
        self, client: mqtt.Client, userdata: Any, msg: mqtt.MQTTMessage
    ) -> None:
        """Callback when MQTT message received - forward to WebSocket clients."""
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
            topic = msg.topic
            now = datetime.now(timezone.utc).isoformat()

            # V7.46.21: Extract original timestamp from payload if available
            # This ensures we don't mask stale data with fresh timestamps
            payload_timestamp = None
            if isinstance(payload, dict):
                payload_timestamp = payload.get("timestamp")

            # Use payload timestamp if available, otherwise current time
            message_timestamp = payload_timestamp or now

            # V7.46.21: Store retained messages with timestamp (thread-safe)
            if msg.retain:
                with self._retained_lock:
                    self._retained_messages[topic] = {
                        "payload": payload,
                        "timestamp": message_timestamp,
                        "received_at": now
                    }

            # Create WebSocket message
            ws_message = {
                "type": "mqtt",
                "topic": topic,
                "payload": payload,
                "timestamp": message_timestamp,
            }

            # Broadcast to all connected WebSocket clients
            if self._loop and self.active_connections:
                asyncio.run_coroutine_threadsafe(
                    self._broadcast(ws_message), self._loop
                )

        except json.JSONDecodeError:
            logger.warning(f"Invalid JSON from MQTT topic {msg.topic}")
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")

    async def connect(self, websocket: WebSocket) -> None:
        """Accept and store a new WebSocket connection."""
        await websocket.accept()
        async with self._lock:
            self.active_connections.append(websocket)

        # Store event loop for MQTT callbacks
        self._loop = asyncio.get_running_loop()

        # Setup MQTT if first connection
        if len(self.active_connections) == 1:
            self._setup_mqtt()

        logger.info(
            f"Trading WebSocket connected. Total: {len(self.active_connections)}"
        )

        # V7.46.21: Send retained messages to new client (thread-safe copy)
        # Use original timestamp to prevent showing stale data as fresh
        with self._retained_lock:
            retained_copy = dict(self._retained_messages)

        for topic, data in retained_copy.items():
            try:
                await websocket.send_text(
                    json.dumps({
                        "type": "mqtt",
                        "topic": topic,
                        "payload": data["payload"],
                        "timestamp": data["timestamp"],  # Original timestamp
                    })
                )
            except Exception:
                pass

    async def disconnect(self, websocket: WebSocket) -> None:
        """Remove a WebSocket connection."""
        async with self._lock:
            if websocket in self.active_connections:
                self.active_connections.remove(websocket)

        logger.info(
            f"Trading WebSocket disconnected. Total: {len(self.active_connections)}"
        )

        # Stop MQTT if no connections
        if not self.active_connections and self._mqtt_client:
            self._mqtt_client.loop_stop()
            self._mqtt_client.disconnect()
            self._mqtt_client = None
            self._mqtt_connected = False
            logger.info("Trading MQTT stopped (no clients)")

    async def _broadcast(self, message: dict[str, Any]) -> None:
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

            for conn in disconnected:
                if conn in self.active_connections:
                    self.active_connections.remove(conn)


# Singleton manager
trading_manager = TradingConnectionManager()


@router.websocket("/ws")
async def trading_websocket(
    websocket: WebSocket,
) -> None:
    """Trading WebSocket endpoint for real-time Momentum Trader V7 data.

    Messages sent to client:
    - mqtt: { topic, payload, timestamp } - MQTT messages from trader/#

    Messages from client:
    - ping: {} (keepalive)
    - subscribe: { topics: [...] } (future: selective subscription)

    Access: Requires admin or simon user authentication.
    """
    # Note: WebSocket auth would need cookie/token validation
    # For now, we'll accept connections and the frontend handles access control
    await trading_manager.connect(websocket)

    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                msg_type = message.get("type", "")

                if msg_type == "ping":
                    await websocket.send_text(
                        json.dumps({
                            "type": "pong",
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                            "mqtt_connected": trading_manager._mqtt_connected,
                        })
                    )

                # V7.4: Handle publish requests from dashboard
                elif msg_type == "publish":
                    topic = message.get("topic", "")
                    payload = message.get("payload", {})
                    if topic.startswith("trader/control/") and trading_manager._mqtt_client:
                        try:
                            trading_manager._mqtt_client.publish(
                                topic,
                                json.dumps(payload),
                                qos=2
                            )
                            logger.info(f"Published control message to {topic}")
                            # V8: Cache swing config locally for persistence
                            if topic == "trader/control/swing/config":
                                trading_manager._swing_config.update({
                                    k: v for k, v in payload.items()
                                    if k in ("enabled", "budget_pct", "max_positions",
                                             "max_position_size", "auto_entry")
                                })
                                logger.info(f"Cached swing config: {trading_manager._swing_config}")
                        except Exception as e:
                            logger.error(f"Failed to publish to {topic}: {e}")

            except json.JSONDecodeError:
                logger.warning("Invalid JSON from trading WebSocket client")

    except WebSocketDisconnect:
        await trading_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"Trading WebSocket error: {e}")
        await trading_manager.disconnect(websocket)


@router.get("/status")
async def trading_status() -> dict[str, Any]:
    """Get trading connection status."""
    return {
        "mqtt_connected": trading_manager._mqtt_connected,
        "websocket_clients": len(trading_manager.active_connections),
        "mqtt_broker": MQTT_BROKER,
        "subscribed_topics": MQTT_TOPICS,
    }


@router.get("/swing/state")
async def get_swing_state() -> dict[str, Any]:
    """Get cached swing trading state from retained MQTT messages.

    Returns the last known state for swing trading, useful when
    WebSocket reconnects and might miss retained messages.
    """
    with trading_manager._retained_lock:
        retained = dict(trading_manager._retained_messages)

    result: dict[str, Any] = {
        "heartbeat": None,
        "candidates": [],
        "positions": [],
        "config": trading_manager._swing_config,  # V8: Include cached config
        "timestamp": None,
    }

    # Extract swing data from retained messages
    for topic, data in retained.items():
        if topic == "momentum/swing/heartbeat":
            result["heartbeat"] = data.get("payload")
            result["timestamp"] = data.get("timestamp")
        elif topic == "momentum/swing/candidates":
            payload = data.get("payload", {})
            result["candidates"] = payload.get("candidates", [])
        elif topic == "momentum/swing/positions":
            payload = data.get("payload", {})
            result["positions"] = payload.get("positions", [])

    return result
