import os


def _get_bool(name, default):
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in ("1", "true", "yes", "on")


DEVICE_ID = os.getenv("DEVICE_ID", "tomato_001")
DEVICE_ROOT = os.getenv("DEVICE_ROOT", "plants")

MODEL_PATH = os.getenv("MODEL_PATH", "models/best.pt")
CONF = float(os.getenv("CONF", "0.5"))

# Camera
WIDTH = int(os.getenv("WIDTH", "416"))
HEIGHT = int(os.getenv("HEIGHT", "416"))
CAMERA_BACKEND = os.getenv("CAMERA_BACKEND", "auto")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

# Detector throttling for optional live mode helpers
DETECT_INTERVAL = float(os.getenv("DETECT_INTERVAL", "0.8"))

# Firebase capture polling interval
COMMAND_POLL_INTERVAL = float(os.getenv("COMMAND_POLL_INTERVAL", "1.0"))

# Local snapshot directory
SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "detections/snapshots")

# Firebase config
FIREBASE_KEY_PATH = os.getenv("FIREBASE_KEY_PATH", "firebase_key.json")
FIREBASE_DB_URL = os.getenv(
    "FIREBASE_DB_URL",
    "https://pi4-iot-1b7bb-default-rtdb.asia-southeast1.firebasedatabase.app/",
)
FIREBASE_STORAGE_BUCKET = os.getenv("FIREBASE_STORAGE_BUCKET", "pi4-iot-1b7bb.firebasestorage.app")
FIREBASE_UPLOAD_TO_STORAGE = _get_bool("FIREBASE_UPLOAD_TO_STORAGE", True)

# Firebase RTDB paths
_DEVICE_PREFIX = f"{DEVICE_ROOT}/{DEVICE_ID}" if DEVICE_ROOT else DEVICE_ID
CAPTURE_COMMAND_PATH = os.getenv("CAPTURE_COMMAND_PATH", f"{_DEVICE_PREFIX}/commands/capture")
CAPTURE_RESULT_LATEST_PATH = os.getenv("CAPTURE_RESULT_LATEST_PATH", f"{_DEVICE_PREFIX}/detections/latest")
CAPTURE_RESULT_HISTORY_PATH = os.getenv("CAPTURE_RESULT_HISTORY_PATH", f"{_DEVICE_PREFIX}/detections/history")

# Logging / debug
VERBOSE = _get_bool("VERBOSE", True)
