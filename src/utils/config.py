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

# Sensor publish (LM393 DO + DHT11/DHT22)
SENSOR_PUBLISH_ENABLED = os.getenv("SENSOR_PUBLISH_ENABLED", "true").lower() in (
    "1",
    "true",
    "yes",
)
SENSOR_PUBLISH_INTERVAL = float(os.getenv("SENSOR_PUBLISH_INTERVAL", "15"))
SENSOR_PATH_TEMPLATE = os.getenv("SENSOR_PATH_TEMPLATE", "plant/{device_id}/sensor")
SENSOR_SOURCE = os.getenv("SENSOR_SOURCE", "uart")

UART_SERIAL_PORT = os.getenv(
    "UART_SERIAL_PORT",
    os.getenv("ZIGBEE_SERIAL_PORT", "/dev/serial0"),
)
UART_BAUDRATE = int(
    os.getenv("UART_BAUDRATE", os.getenv("ZIGBEE_BAUDRATE", "115200"))
)
UART_SERIAL_TIMEOUT = float(
    os.getenv("UART_SERIAL_TIMEOUT", os.getenv("ZIGBEE_SERIAL_TIMEOUT", "0.05"))
)
UART_STALE_AFTER = float(
    os.getenv("UART_STALE_AFTER", os.getenv("ZIGBEE_STALE_AFTER", "30"))
)
UART_ERROR_STREAK_THRESHOLD = int(
    os.getenv(
        "UART_ERROR_STREAK_THRESHOLD",
        os.getenv("ZIGBEE_ERROR_STREAK_THRESHOLD", "2"),
    )
)

SOIL_SENSOR_GPIO = int(os.getenv("SOIL_SENSOR_GPIO", "17"))
SOIL_SENSOR_ACTIVE_LOW = os.getenv("SOIL_SENSOR_ACTIVE_LOW", "true").lower() in (
    "1",
    "true",
    "yes",
)
SOIL_SENSOR_PULL = os.getenv("SOIL_SENSOR_PULL", "up")
SOIL_SENSOR_SAMPLE_COUNT = int(os.getenv("SOIL_SENSOR_SAMPLE_COUNT", "15"))
SOIL_SENSOR_SAMPLE_DELAY = float(os.getenv("SOIL_SENSOR_SAMPLE_DELAY", "0.02"))

DHT_SENSOR_TYPE = os.getenv("DHT_SENSOR_TYPE", "DHT11")
DHT_SENSOR_GPIO = int(os.getenv("DHT_SENSOR_GPIO", "4"))
