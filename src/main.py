import os
import time
from datetime import datetime

import cv2
import numpy as np

from src.ai.detector import RemoteDetector
from src.camera.camera_manager import CameraManager
from src.services.firebase_command import FirebaseCommandListener
from src.services.sensor_publisher import SensorPublisher
from src.services.wifi_manager import WiFiManager
from src.services.oled_status import OledStatusDisplay
from src.utils.config import *


def ensure_snapshot_dir():
    """Create snapshot directory if needed"""
    os.makedirs(SNAPSHOT_DIR, exist_ok=True)


def sharpen_image(frame, kernel_size=5):
    """Apply a gentle unsharp mask to avoid harsh, artificial edges."""
    amount = max(0.0, SHARPEN_AMOUNT)
    if amount <= 0:
        return frame

    blurred = cv2.GaussianBlur(frame, (0, 0), 1.0)
    return cv2.addWeighted(frame, 1.0 + amount, blurred, -amount, 0)


def apply_gray_world_white_balance(frame):
    """Reduce color cast by normalizing channel means (Gray-World AWB)."""
    img = frame.astype(np.float32)
    mean_b = float(np.mean(img[:, :, 0]))
    mean_g = float(np.mean(img[:, :, 1]))
    mean_r = float(np.mean(img[:, :, 2]))
    mean_gray = (mean_b + mean_g + mean_r) / 3.0

    eps = 1e-6
    img[:, :, 0] *= mean_gray / (mean_b + eps)
    img[:, :, 1] *= mean_gray / (mean_g + eps)
    img[:, :, 2] *= mean_gray / (mean_r + eps)
    return np.clip(img, 0, 255).astype(np.uint8)


def adjust_gamma(frame, gamma=1.0):
    """Gamma correction to recover details in low-light frames."""
    gamma = max(0.1, float(gamma))
    if abs(gamma - 1.0) < 1e-3:
        return frame

    inv_gamma = 1.0 / gamma
    table = np.array([((i / 255.0) ** inv_gamma) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(frame, table)


def adjust_saturation(frame, gain=1.0):
    """Slightly boost saturation so leaf color is easier to distinguish."""
    if abs(gain - 1.0) < 1e-3:
        return frame

    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV).astype(np.float32)
    hsv[:, :, 1] *= float(gain)
    hsv[:, :, 1] = np.clip(hsv[:, :, 1], 0, 255)
    return cv2.cvtColor(hsv.astype(np.uint8), cv2.COLOR_HSV2BGR)


def preprocess_frame(frame):
    """Preprocess frame for stable quality before sending to server."""
    # Resize to target dimensions
    frame = cv2.resize(frame, (WIDTH, HEIGHT))

    if ENABLE_COLOR_CORRECTION:
        if AUTO_WHITE_BALANCE:
            frame = apply_gray_world_white_balance(frame)
        frame = adjust_gamma(frame, GAMMA)
        frame = adjust_saturation(frame, SATURATION_GAIN)

    if ENABLE_SHARPEN:
        frame = sharpen_image(frame)
    
    return frame


def draw_detections(frame, detections):
    """Draw detection boxes on frame"""
    if not isinstance(detections, list) or not detections:
        return frame
    
    annotated = frame.copy()
    for det in detections:
        if not isinstance(det, dict) or "box" not in det:
            continue
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
        
        cv2.imwrite(filename, frame, [cv2.IMWRITE_JPEG_QUALITY, JPEG_QUALITY])
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
    sensor_publisher = SensorPublisher(
        db_url=FIREBASE_DB_URL,
        device_id=DEVICE_ID,
        path_template=SENSOR_PATH_TEMPLATE,
        enabled=SENSOR_PUBLISH_ENABLED,
        publish_interval=SENSOR_PUBLISH_INTERVAL,
        sensor_source=SENSOR_SOURCE,
        uart_serial_port=UART_SERIAL_PORT,
        uart_baudrate=UART_BAUDRATE,
        uart_serial_timeout=UART_SERIAL_TIMEOUT,
        uart_stale_after=UART_STALE_AFTER,
        uart_error_streak_threshold=UART_ERROR_STREAK_THRESHOLD,
        ble_device_name=BLE_DEVICE_NAME,
        ble_address=BLE_ADDRESS,
        ble_service_uuid=BLE_SERVICE_UUID,
        ble_notify_char_uuid=BLE_NOTIFY_CHAR_UUID,
        ble_scan_timeout=BLE_SCAN_TIMEOUT,
        ble_connect_timeout=BLE_CONNECT_TIMEOUT,
        ble_reconnect_delay=BLE_RECONNECT_DELAY,
        ble_stale_after=BLE_STALE_AFTER,
        ble_error_streak_threshold=BLE_ERROR_STREAK_THRESHOLD,
        soil_gpio=SOIL_SENSOR_GPIO,
        soil_active_low=SOIL_SENSOR_ACTIVE_LOW,
        soil_pull=SOIL_SENSOR_PULL,
        soil_sample_count=SOIL_SENSOR_SAMPLE_COUNT,
        soil_sample_delay=SOIL_SENSOR_SAMPLE_DELAY,
        dht_gpio=DHT_SENSOR_GPIO,
        dht_sensor_type=DHT_SENSOR_TYPE,
    )

    wifi_manager = None
    wifi_ssid = None
    wifi_ip = None
    last_wifi_check = 0.0

    if OLED_ENABLED:
        try:
            wifi_manager = WiFiManager(interface=WIFI_INTERFACE)
        except Exception as exc:
            print(f"OLED warning: Wi-Fi status unavailable: {exc}")

    oled = OledStatusDisplay(
        enabled=OLED_ENABLED,
        width=OLED_WIDTH,
        height=OLED_HEIGHT,
        i2c_address=OLED_I2C_ADDRESS,
        rotate=OLED_ROTATE,
        update_interval=OLED_UPDATE_INTERVAL,
    )
    
    print(f"📷 Camera: {WIDTH}x{HEIGHT} @ {CAMERA_BACKEND}")
    print(f"🌐 Server: {SERVER_URL}")
    print(f"⏱️  Poll interval: {COMMAND_POLL_INTERVAL}s")
    print("=" * 60)
    print("Waiting for Firebase commands...\n")
    
    try:
        capture_count = 0
        start_time = time.time()
        
        while True:
            sensor_publisher.publish_if_due()

            if oled is not None and OLED_ENABLED:
                now = time.time()
                if wifi_manager is not None and now - last_wifi_check >= OLED_WIFI_REFRESH_INTERVAL:
                    status = wifi_manager.status()
                    wifi_ssid = status.get("connection")
                    wifi_ip = status.get("ip")
                    last_wifi_check = now

                status = sensor_publisher.get_status_snapshot()
                oled.update_if_due(
                    wifi_ssid=wifi_ssid,
                    wifi_ip=wifi_ip,
                    ble_connected=status.get("ble_connected"),
                    firebase_ok=status.get("last_publish_ok"),
                )

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
                    if not isinstance(detections, list):
                        detections = []
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
        sensor_publisher.stop()
        camera.stop()


if __name__ == "__main__":
    main()
