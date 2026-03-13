# src/utils/config.py

MODEL_PATH = "models/best.pt"
CONF = 0.5

# Camera resolution
WIDTH = 416
HEIGHT = 416

# Detector throttling for optional live mode helpers
DETECT_INTERVAL = 0.8

# Firebase capture polling interval
COMMAND_POLL_INTERVAL = 1.0

# Local snapshot directory
SNAPSHOT_DIR = "detections/snapshots"

# Firebase config
FIREBASE_KEY_PATH = "/home/khanhpi/project/tree_ai/firebase_key.json"
FIREBASE_DB_URL = "https://pi4-iot-1b7bb-default-rtdb.asia-southeast1.firebasedatabase.app/"
FIREBASE_STORAGE_BUCKET = "pi4-iot-1b7bb.firebasestorage.app"
FIREBASE_UPLOAD_TO_STORAGE = True

# Firebase RTDB paths
CAPTURE_COMMAND_PATH = "commands/capture"
CAPTURE_RESULT_LATEST_PATH = "detections/latest"
CAPTURE_RESULT_HISTORY_PATH = "detections/history"

# Logging / debug
VERBOSE = True
