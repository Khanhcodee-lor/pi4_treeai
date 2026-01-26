# src/utils/config.py
# Chỉnh các giá trị phù hợp với hệ thống bạn

MODEL_PATH = "models/best.pt"
CONF = 0.5

# camera/stream resolution
WIDTH = 416
HEIGHT = 416

# detect interval (s) để không detect mỗi frame
DETECT_INTERVAL = 0.8

# tránh spam firebase: tối thiểu giây giữa 2 lần gửi cùng label
SEND_COOLDOWN = 30

# nơi lưu snapshot local
SNAPSHOT_DIR = "detections/snapshots"

# Firebase config: chỉnh path và URL của bạn
FIREBASE_KEY_PATH = "/home/khanhpi/project/tree_ai/firebase_key.json"  # đặt file JSON ở đây
FIREBASE_DB_URL = "https://pi4-iot-1b7bb-default-rtdb.asia-southeast1.firebasedatabase.app/"

# nếu muốn upload snapshot lên Firebase Storage, đặt tên bucket (optional)
FIREBASE_STORAGE_BUCKET = "pi4-iot-1b7bb.firebasestorage.app"

# logging / debug
VERBOSE = True
