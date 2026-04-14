#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

PROJECT_DIR="${PROJECT_DIR:-/home/khanhpi/project/pi4_treeai}"
VENV_DIR="${VENV_DIR:-$PROJECT_DIR/myenv}"
PYTHON_BIN="${PYTHON_BIN:-python3}"
PRIMARY_SERVICE="${PRIMARY_SERVICE:-pi4-tree-ai.service}"
OPTIONAL_SERVICES="${OPTIONAL_SERVICES:-pi4-bt-provision.service}"

log() {
  echo "[deploy] $*"
}

require_command() {
  if ! command -v "$1" >/dev/null 2>&1; then
    echo "Missing required command: $1" >&2
    exit 1
  fi
}

sync_repository() {
  mkdir -p "$PROJECT_DIR"

  rsync -a --delete \
    --exclude ".git/" \
    --exclude ".github/" \
    --exclude "myenv/" \
    --exclude "venv/" \
    --exclude ".env" \
    --exclude "firebase_key.json" \
    --exclude "detections/" \
    --exclude "snapshots/" \
    "$REPO_ROOT/" "$PROJECT_DIR/"

  chmod +x "$PROJECT_DIR/run_tree_ai.sh"
  chmod +x "$PROJECT_DIR/run_bt_provision.sh"
  chmod +x "$PROJECT_DIR/setup_bt_autostart.sh"

  if [[ -f "$PROJECT_DIR/setup_tree_ai_autostart.sh" ]]; then
    chmod +x "$PROJECT_DIR/setup_tree_ai_autostart.sh"
  fi
}

install_python_dependencies() {
  if [[ ! -d "$VENV_DIR" ]]; then
    log "Creating virtual environment at $VENV_DIR"
    "$PYTHON_BIN" -m venv "$VENV_DIR"
  fi

  # shellcheck disable=SC1090
  source "$VENV_DIR/bin/activate"

  log "Installing Python dependencies"
  python -m pip install --upgrade pip
  python -m pip install -r "$PROJECT_DIR/requirements.txt"
}

refresh_installed_units() {
  local updated=0
  local unit_src
  local unit_name
  local unit_dst

  for unit_src in "$PROJECT_DIR"/deploy/*.service; do
    [[ -f "$unit_src" ]] || continue

    unit_name="$(basename "$unit_src")"
    unit_dst="/etc/systemd/system/$unit_name"

    if [[ -f "$unit_dst" ]]; then
      log "Refreshing installed unit $unit_name"
      sudo install -m 644 "$unit_src" "$unit_dst"
      updated=1
    fi
  done

  if [[ "$updated" -eq 1 ]]; then
    sudo systemctl daemon-reload
  fi
}

restart_if_managed() {
  local service_name="$1"

  if sudo systemctl is-enabled "$service_name" >/dev/null 2>&1 || \
     sudo systemctl is-active "$service_name" >/dev/null 2>&1; then
    log "Restarting $service_name"
    sudo systemctl restart "$service_name"
    sudo systemctl --no-pager --full status "$service_name" | sed -n '1,12p'
  else
    log "Skipping $service_name because it is not enabled on this Pi"
  fi
}

main() {
  require_command rsync
  require_command sudo
  require_command "$PYTHON_BIN"

  log "Syncing repository to $PROJECT_DIR"
  sync_repository

  install_python_dependencies
  refresh_installed_units

  restart_if_managed "$PRIMARY_SERVICE"

  for service_name in $OPTIONAL_SERVICES; do
    restart_if_managed "$service_name"
  done

  log "Deployment completed"
}

main "$@"
