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
WIDTH = int(os.getenv("WIDTH", "640"))
HEIGHT = int(os.getenv("HEIGHT", "480"))
CAMERA_BACKEND = os.getenv("CAMERA_BACKEND", "auto")
CAMERA_INDEX = int(os.getenv("CAMERA_INDEX", "0"))

# Image preprocessing
ENABLE_SHARPEN = os.getenv("ENABLE_SHARPEN", "false").lower() in ("1", "true", "yes")
SHARPEN_AMOUNT = float(os.getenv("SHARPEN_AMOUNT", "0.2"))
JPEG_QUALITY = int(os.getenv("JPEG_QUALITY", "95"))
ENABLE_COLOR_CORRECTION = os.getenv("ENABLE_COLOR_CORRECTION", "true").lower() in ("1", "true", "yes")
AUTO_WHITE_BALANCE = os.getenv("AUTO_WHITE_BALANCE", "true").lower() in ("1", "true", "yes")
GAMMA = float(os.getenv("GAMMA", "1.15"))
SATURATION_GAIN = float(os.getenv("SATURATION_GAIN", "1.05"))

# Snapshot save (local storage)
SAVE_SNAPSHOTS = os.getenv("SAVE_SNAPSHOTS", "true").lower() in ("1", "true", "yes")
SNAPSHOT_DIR = os.getenv("SNAPSHOT_DIR", "detections/snapshots")

VERBOSE = os.getenv("VERBOSE", "true").lower() in ("1", "true", "yes")
