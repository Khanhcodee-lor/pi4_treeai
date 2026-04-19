#!/bin/bash

PROJECT_DIR="/home/khanhpi/project/pi4_treeai"
VENV="$PROJECT_DIR/myenv"

echo "Starting Pi Camera Agent..."

cd "$PROJECT_DIR"

# Activate venv
source "$VENV/bin/activate"

# Default Firebase ADC for systemd/headless runs
if [[ -z "${GOOGLE_APPLICATION_CREDENTIALS:-}" && -f "$PROJECT_DIR/firebase_key.json" ]]; then
	export GOOGLE_APPLICATION_CREDENTIALS="$PROJECT_DIR/firebase_key.json"
fi

# Set defaults (override with env vars)
export SERVER_URL="${SERVER_URL:-http://192.168.1.100:5000}"
export COMMAND_POLL_INTERVAL="${COMMAND_POLL_INTERVAL:-1.0}"
export WIDTH="${WIDTH:-640}"
export HEIGHT="${HEIGHT:-480}"
export CAMERA_BACKEND="${CAMERA_BACKEND:-opencv}"
export CAMERA_INDEX="${CAMERA_INDEX:-0}"
export ENABLE_SHARPEN="${ENABLE_SHARPEN:-false}"
export JPEG_QUALITY="${JPEG_QUALITY:-95}"
export ENABLE_COLOR_CORRECTION="${ENABLE_COLOR_CORRECTION:-true}"
export AUTO_WHITE_BALANCE="${AUTO_WHITE_BALANCE:-true}"
export GAMMA="${GAMMA:-1.15}"
export SATURATION_GAIN="${SATURATION_GAIN:-1.05}"
export VERBOSE="${VERBOSE:-true}"
export SENSOR_PUBLISH_ENABLED="${SENSOR_PUBLISH_ENABLED:-true}"
export SENSOR_PUBLISH_INTERVAL="${SENSOR_PUBLISH_INTERVAL:-15}"
if [[ -z "${SENSOR_PATH_TEMPLATE:-}" ]]; then
	export SENSOR_PATH_TEMPLATE="plant/{device_id}/sensor"
fi
export SENSOR_SOURCE="${SENSOR_SOURCE:-uart}"
export UART_SERIAL_PORT="${UART_SERIAL_PORT:-${ZIGBEE_SERIAL_PORT:-/dev/serial0}}"
export UART_BAUDRATE="${UART_BAUDRATE:-${ZIGBEE_BAUDRATE:-115200}}"
export UART_SERIAL_TIMEOUT="${UART_SERIAL_TIMEOUT:-${ZIGBEE_SERIAL_TIMEOUT:-0.05}}"
export UART_STALE_AFTER="${UART_STALE_AFTER:-${ZIGBEE_STALE_AFTER:-30}}"
export UART_ERROR_STREAK_THRESHOLD="${UART_ERROR_STREAK_THRESHOLD:-${ZIGBEE_ERROR_STREAK_THRESHOLD:-2}}"
export SOIL_SENSOR_GPIO="${SOIL_SENSOR_GPIO:-17}"
export SOIL_SENSOR_ACTIVE_LOW="${SOIL_SENSOR_ACTIVE_LOW:-true}"
export SOIL_SENSOR_PULL="${SOIL_SENSOR_PULL:-up}"
export SOIL_SENSOR_SAMPLE_COUNT="${SOIL_SENSOR_SAMPLE_COUNT:-15}"
export SOIL_SENSOR_SAMPLE_DELAY="${SOIL_SENSOR_SAMPLE_DELAY:-0.02}"
export DHT_SENSOR_TYPE="${DHT_SENSOR_TYPE:-DHT11}"
export DHT_SENSOR_GPIO="${DHT_SENSOR_GPIO:-4}"

echo "Server: $SERVER_URL"
echo "Frame size: ${WIDTH}x${HEIGHT}"
echo "Camera backend: $CAMERA_BACKEND"
echo "Camera index: $CAMERA_INDEX"
echo "Sensor source: $SENSOR_SOURCE"
echo "UART serial: ${UART_SERIAL_PORT}@${UART_BAUDRATE}"
echo "Sensor path template: $SENSOR_PATH_TEMPLATE"
if [[ -n "${GOOGLE_APPLICATION_CREDENTIALS:-}" ]]; then
	echo "Firebase credentials: $GOOGLE_APPLICATION_CREDENTIALS"
else
	echo "Firebase credentials: not set"
fi
echo "---"

# Run
exec python -m src.main

