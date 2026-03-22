import os
import time
from datetime import datetime

import cv2
import numpy as np

from src.ai.detector import RemoteDetector
from src.camera.camera_manager import CameraManager
from src.services.firebase_command import FirebaseCommandListener
from src.utils.config import *


def ensure_snapshot_dir():
    """Create snapshot directory if needed"""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def sharpen_image(frame, kernel_size=5):
    """Sharpen image using kernel"""
    kernel = np.array([[-1, -1, -1],
                       [-1,  9, -1],
                       [-1, -1, -1]])
    
    # Apply sharpening
    sharpened = cv2.filter2D(frame, -1, kernel)
    
    # Blend with original (reduce over-sharpening)
    alpha = 0.7
    result = cv2.addWeighted(frame, 1 - alpha, sharpened, alpha, 0)
    return result


def preprocess_frame(frame):
    """Preprocess frame: resize, sharpen"""
    # Resize to target dimensions
    frame = cv2.resize(frame, (WIDTH, HEIGHT))
    
    # Sharpen
    frame = sharpen_image(frame, BLUR_KERNEL)
    
    return frame


def draw_detections(frame, detections):
    """Draw detection boxes on frame"""
    if not detections:
        return frame
    
    annotated = frame.copy()
    for det in detections:
        x1 = det["box"]["x1"]
        y1 = det["box"]["y1"]
        x2 = det["box"]["x2"]
        y2 = det["box"]["y2"]
        label = f"{det['label']} {det['confidence']:.2f}"
        
        # Draw box
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
        
        # Draw label
        cv2.putText(annotated, label, (x1, y1 - 5),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
    
    return annotated


def save_snapshot(frame, detections=None):
    """Save snapshot locally"""
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S%f")[:-3]
        
        # Annotate if detections exist
        if detections:
            frame = draw_detections(frame, detections)
            count = len(detections)
            filename = f"{SNAPSHOT_DIR}/{timestamp}_{count}det.jpg"
        else:
            filename = f"{SNAPSHOT_DIR}/{timestamp}_nodet.jpg"
        
        cv2.imwrite(filename, frame)
        return filename
    except Exception as e:
        print(f"    Snapshot save error: {e}")
        return None


def main():
    print("=" * 60)
    print("Pi Camera Capture Agent (Firebase Command Mode)")
    print("=" * 60)
    
    if SAVE_SNAPSHOTS:
        ensure_snapshot_dir()
        print(f"📁 Snapshots: {SNAPSHOT_DIR}")
    
    camera = CameraManager(WIDTH, HEIGHT, backend=CAMERA_BACKEND, camera_index=CAMERA_INDEX)
    detector = RemoteDetector(server_url=SERVER_URL, conf=CONF)
    fb = FirebaseCommandListener(db_url=FIREBASE_DB_URL, device_id=DEVICE_ID)
    
    print(f"📷 Camera: {WIDTH}x{HEIGHT} @ {CAMERA_BACKEND}")
    print(f"🌐 Server: {SERVER_URL}")
    print(f"⏱️  Poll interval: {COMMAND_POLL_INTERVAL}s")
    print("=" * 60)
    print("Waiting for Firebase commands...\n")
    
    try:
        capture_count = 0
        start_time = time.time()
        
        while True:
            # Poll Firebase for command
            command = fb.get_command()
            
            if command:
                capture_count += 1
                request_id = command.get("request_id", f"capture_{capture_count}")
                timestamp = datetime.now().strftime("%H:%M:%S")
                
                print(f"[{capture_count:04d}] {timestamp} | CMD: {request_id}")
                
                # Update status
                fb.update_status("processing", request_id)
                
                # Get fresh frame
                for _ in range(10):  # Try 10 times with 100ms delay
                    frame = camera.get_frame()
                    if frame is not None:
                        break
                    time.sleep(0.1)

                captured_at_epoch = time.time()
                captured_at_iso = datetime.now().isoformat(timespec="seconds")
                
                if frame is None:
                    print("        ✗ Camera error")
                    fb.update_status("error", request_id)
                    fb.acknowledge_command(request_id=request_id, captured_at=None)
                    time.sleep(COMMAND_POLL_INTERVAL)
                    continue
                
                # Preprocess
                processed = preprocess_frame(frame)
                
                # Send to server
                print(f"        → ", end="", flush=True)
                result = detector.send_frame(processed)
                
                detections = []
                if result:
                    detections = result.get("detections", [])
                    count = result.get("count", 0)
                    print(f"✓ {count} detection(s)", end="")
                    
                    if count > 0 and VERBOSE:
                        print()
                        for det in detections:
                            label = det["label"]
                            conf = det["confidence"]
                            print(f"             └─ {label}: {conf:.2f}")
                    else:
                        print()
                else:
                    print("✗ Server error")
                
                # Save local snapshot
                if SAVE_SNAPSHOTS:
                    snapshot = save_snapshot(processed, detections if detections else None)
                    if snapshot and VERBOSE:
                        print(f"             📸 {os.path.basename(snapshot)}")
                
                # Update Firebase completion
                fb.update_status(
                    "completed",
                    request_id,
                    extra={
                        "captured_at": captured_at_iso,
                        "captured_at_unix": captured_at_epoch,
                        "detection_count": len(detections),
                    },
                )
                fb.acknowledge_command(request_id=request_id, captured_at=captured_at_iso)
                print(f"        ✓ Done\n")
            
            # Wait before next poll
            time.sleep(COMMAND_POLL_INTERVAL)
            
    except KeyboardInterrupt:
        elapsed = time.time() - start_time
        print()
        print("=" * 60)
        print(f"Stopped. Captures: {capture_count} | Time: {elapsed:.1f}s")
        print("=" * 60)
    finally:
        camera.stop()


if __name__ == "__main__":
    main()
