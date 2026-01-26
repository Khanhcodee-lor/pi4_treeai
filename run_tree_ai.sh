#!/bin/bash
set -e

PROJECT_DIR="/home/khanhpi/project/tree_ai"
VENV="$PROJECT_DIR/venv"

echo "Starting Tree AI..."

cd "$PROJECT_DIR"

# Activate virtual environment
source "$VENV/bin/activate"

# Run main app (foreground for systemd)
exec python -m src.main

