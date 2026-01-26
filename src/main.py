import time
import threading
from datetime import datetime
import cv2

from src.utils.config import *
from src.camera.camera_manager import CameraManager
from src.ai.detector import DiseaseDetector
from src.services.firebase_service import FirebaseService
from src.services.ngrok_service import NgrokService
from src.web.stream_server import create_stream_app


def main():
    print("🚀 Starting Tree AI system...")

    # 1️⃣ Camera (OPEN ONCE)
    camera = CameraManager(WIDTH, HEIGHT)

    # 2️⃣ YOLO
    detector = DiseaseDetector(MODEL_PATH, conf=CONF, interval=DETECT_INTERVAL)

    # 3️⃣ Firebase
    fb = FirebaseService(
        FIREBASE_KEY_PATH,
        FIREBASE_DB_URL,
        storage_bucket=FIREBASE_STORAGE_BUCKET if FIREBASE_STORAGE_BUCKET else None
    )

    # 4️⃣ Flask stream server (same process)
    app = create_stream_app(camera)
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=8000, debug=False, use_reloader=False),
        daemon=True
    ).start()

    time.sleep(2)

    # 5️⃣ Ngrok
    ngrok = NgrokService(port=8000)
    stream_url = ngrok.get_public_url()
    if stream_url:
        fb.push_stream_url(stream_url + "/video")

    print("✅ System running")

    last_sent = {}

    try:
        while True:
            frame = camera.get_frame()
            if frame is None:
                time.sleep(0.05)
                continue

            results = detector.detect_if_needed(frame)
            if results and results.boxes:
                top = max(results.boxes, key=lambda b: float(b.conf[0]))
                label = results.names[int(top.cls[0])]
                conf = float(top.conf[0])

                now = time.time()
                if now - last_sent.get(label, 0) >= SEND_COOLDOWN:
                    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
                    path = f"{SNAPSHOT_DIR}/{ts}_{label.replace(' ', '_')}.jpg"
                    cv2.imwrite(path, frame)
                    fb.push_detection(label, conf, path)
                    last_sent[label] = now
                    print(f"🌱 Detected: {label} ({conf:.2f})")

            time.sleep(0.05)

    except KeyboardInterrupt:
        print("🛑 Stopping...")

    finally:
        camera.stop()


if __name__ == "__main__":
    main()
