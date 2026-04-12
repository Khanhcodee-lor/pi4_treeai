#!/bin/bash

PROJECT_DIR="/home/khanhpi/project/pi4_treeai"
VENV="$PROJECT_DIR/myenv"

echo "Starting Pi4 Bluetooth Wi-Fi Provisioning..."

cd "$PROJECT_DIR"
source "$VENV/bin/activate"

export BT_CHANNEL="${BT_CHANNEL:-4}"
export WIFI_INTERFACE="${WIFI_INTERFACE:-wlan0}"
export BT_DEVICE_NAME="${BT_DEVICE_NAME:-khanhpi}"
export BT_AUTO_SETUP="${BT_AUTO_SETUP:-true}"

echo "Bluetooth name: $BT_DEVICE_NAME"
echo "Bluetooth RFCOMM channel: $BT_CHANNEL"
echo "Wi-Fi interface: $WIFI_INTERFACE"
echo "---"

exec python -m src.provision