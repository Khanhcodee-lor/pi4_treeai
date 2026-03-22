#!/bin/bash

PROJECT_DIR="/home/khanhpi/project/pi4_treeai"
VENV="$PROJECT_DIR/myenv"

echo "Starting Pi Camera Agent..."

cd "$PROJECT_DIR"

# Activate venv
source "$VENV/bin/activate"

# Set defaults (override with env vars)
export SERVER_URL="${SERVER_URL:-http://192.168.1.100:5000}"
export CAPTURE_INTERVAL="${CAPTURE_INTERVAL:-1.0}"
export WIDTH="${WIDTH:-416}"
export HEIGHT="${HEIGHT:-416}"
export VERBOSE="${VERBOSE:-true}"

echo "Server: $SERVER_URL"
echo "Frame size: ${WIDTH}x${HEIGHT}"
echo "---"

# Run
exec python -m src.main

