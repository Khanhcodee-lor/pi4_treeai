#!/bin/bash
set -e

PROJECT_DIR="/home/khanhpi/project/pi4_treeai"
SERVICE_NAME="pi4-tree-ai.service"
SERVICE_SRC="$PROJECT_DIR/deploy/$SERVICE_NAME"
SERVICE_DST="/etc/systemd/system/$SERVICE_NAME"

if [[ ! -f "$SERVICE_SRC" ]]; then
  echo "Service file not found: $SERVICE_SRC"
  exit 1
fi

echo "Installing $SERVICE_NAME ..."
sudo cp "$SERVICE_SRC" "$SERVICE_DST"
sudo chmod 644 "$SERVICE_DST"

echo "Reloading systemd ..."
sudo systemctl daemon-reload

echo "Enabling Tree AI service at boot ..."
sudo systemctl enable "$SERVICE_NAME"
sudo systemctl restart "$SERVICE_NAME"

echo "---"
echo "Service status:"
sudo systemctl --no-pager --full status "$SERVICE_NAME" | sed -n '1,20p'
echo "---"
echo "Done. Pi4 will auto-start Tree AI on power-on."
