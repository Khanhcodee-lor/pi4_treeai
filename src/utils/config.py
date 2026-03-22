import os


DEVICE_ID = os.getenv("DEVICE_ID", "tomato_001")

# Firebase
FIREBASE_DB_URL = os.getenv(
    "FIREBASE_DB_URL",
    "https://pi4-iot-1b7bb-default-rtdb.asia-southeast1.firebasedatabase.app"
)
COMMAND_POLL_INTERVAL = float(os.getenv("COMMAND_POLL_INTERVAL", "1.0"))

# Detection server (remote HTTP API)
SERVER_URL = os.getenv("SERVER_URL", "http://192.168.1.100:5000")
CONF = float(os.getenv("CONF", "0.5"))

# Camera settings
WIDTH = int(os.getenv("WIDTH", "416"))
HEIGHT = int(os.getenv("HEIGHT", "416"))
CAMERA_BACKEND = os.getenv("CAMERA_BACKEND", "auto")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

# Image preprocessing
BLUR_KERNEL = int(os.getenv("BLUR_KERNEL", "5"))

# Snapshot save (local storage)
SAVE_SNAPSHOTS = os.getenv("SAVE_SNAPSHOTS", "true").lower() in ("1", "true", "yes")
SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "detections/snapshots")

VERBOSE = os.getenv("VERBOSE", "true").lower() in ("1", "true", "yes")
