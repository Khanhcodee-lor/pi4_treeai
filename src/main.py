import os
import time
from datetime import datetime

import cv2

from src.ai.detector import DiseaseDetector
from src.camera.camera_manager import CameraManager
from src.services.firebase_service import FirebaseService
from src.services.stream_service import build_disease_list, draw_boxes, extract_detections
from src.utils.config import *


def ensure_snapshot_dir():
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def sanitize_name(value):
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in str(value))


def wait_for_frame(camera, timeout=3):
    deadline = time.time() + timeout
    while time.time() < deadline:
        frame = camera.get_frame()
        if frame is not None:
            return frame
        time.sleep(0.05)
    return None


def main():
    print("Starting Tree AI system...")
    ensure_snapshot_dir()

    camera = CameraManager(WIDTH, HEIGHT)
    detector = DiseaseDetector(MODEL_PATH, conf=CONF, interval=DETECT_INTERVAL)
    fb = FirebaseService(
        FIREBASE_KEY_PATH,
        FIREBASE_DB_URL,
        storage_bucket=FIREBASE_STORAGE_BUCKET if FIREBASE_STORAGE_BUCKET else None,
        command_path=CAPTURE_COMMAND_PATH,
        result_latest_path=CAPTURE_RESULT_LATEST_PATH,
        result_history_path=CAPTURE_RESULT_HISTORY_PATH,
    )

    print("System ready. Waiting for Firebase capture commands...")

    try:
        while True:
            command = fb.get_capture_command()
            if not command:
                time.sleep(COMMAND_POLL_INTERVAL)
                continue

            request_id = command["request_id"]
            print(f"Capture requested: {request_id}")

            try:
                fb.update_capture_status("processing", request_id=request_id)

                frame = wait_for_frame(camera)
                if frame is None:
                    raise RuntimeError("Camera frame unavailable")

                results = detector.detect(frame)
                detections = extract_detections(results)
                diseases = build_disease_list(detections)
                annotated_frame = draw_boxes(frame.copy(), results)

                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                disease_tag = sanitize_name(diseases[0] if diseases else "healthy")
                safe_request_id = sanitize_name(request_id)
                snapshot_path = f"{SNAPSHOT_DIR}/{timestamp}_{safe_request_id}_{disease_tag}.jpg"

                if not cv2.imwrite(snapshot_path, annotated_frame):
                    raise RuntimeError(f"Failed to write snapshot to {snapshot_path}")

                payload = fb.push_capture_result(
                    request_id=request_id,
                    detections=detections,
                    diseases=diseases,
                    snapshot_local_path=snapshot_path,
                    upload_to_storage=command.get("upload_to_storage", FIREBASE_UPLOAD_TO_STORAGE),
                )
                fb.complete_capture_command(request_id, result=payload)
                print(f"Capture processed: {request_id}, diseases={diseases}")
            except Exception as e:
                print("Capture processing error:", e)
                fb.fail_capture_command(request_id, e)

    except KeyboardInterrupt:
        print("Stopping...")
    finally:
        camera.stop()


if __name__ == "__main__":
    main()
