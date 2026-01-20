#!/bin/bash
# Start SSH tunnel to ProDesk MQTT broker
# Run this before starting the backend

# Load configuration from .env
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ENV_FILE="$SCRIPT_DIR/../.env"

if [ -f "$ENV_FILE" ]; then
    export $(grep -v '^#' "$ENV_FILE" | grep -E '^(PRODESK_HOST|PRODESK_USER|PRODESK_MQTT_PORT|MQTT_PORT)=' | xargs)
fi

# Default values if not in .env
PRODESK_HOST="${PRODESK_HOST:-192.168.1.113}"
PRODESK_USER="${PRODESK_USER:-simon}"
PRODESK_MQTT_PORT="${PRODESK_MQTT_PORT:-1883}"
LOCAL_PORT="${MQTT_PORT:-11883}"

# Check if tunnel already exists
if pgrep -f "ssh.*${LOCAL_PORT}:localhost:${PRODESK_MQTT_PORT}.*${PRODESK_HOST}" > /dev/null; then
    echo "✅ MQTT tunnel already running on localhost:${LOCAL_PORT}"
    exit 0
fi

# Kill any stale tunnels on the same port
pkill -f "ssh.*-L ${LOCAL_PORT}:" 2>/dev/null

# Start new tunnel
echo "🔗 Starting SSH tunnel: localhost:${LOCAL_PORT} -> ${PRODESK_HOST}:${PRODESK_MQTT_PORT}"
ssh -o ConnectTimeout=10 -f -N -L ${LOCAL_PORT}:localhost:${PRODESK_MQTT_PORT} ${PRODESK_USER}@${PRODESK_HOST}

if [ $? -eq 0 ]; then
    echo "✅ MQTT tunnel established successfully"
else
    echo "❌ Failed to establish MQTT tunnel"
    exit 1
fi
