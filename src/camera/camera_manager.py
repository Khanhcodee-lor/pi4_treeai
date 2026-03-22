import threading
import time

import cv2

try:
    from picamera2 import Picamera2
except ImportError:
    Picamera2 = None


class OpenCVCamera:
    def __init__(self, width=640, height=480, camera_index=0):
        self.cap = cv2.VideoCapture(camera_index)
        if not self.cap.isOpened():
            raise RuntimeError(f"Cannot open webcam at index {camera_index}")

        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    def create_video_configuration(self, main):
        return main

    def configure(self, config):
        return config

    def start(self):
        return None

    def capture_array(self):
        ok, frame = self.cap.read()
        if not ok or frame is None:
            raise RuntimeError("Failed to read frame from webcam")
        return frame

    def stop(self):
        self.cap.release()


class CameraManager:
    def __init__(self, width=640, height=480, camera_factory=None, backend="auto", camera_index=0):
        self.picam2 = self._build_camera(
            width=width,
            height=height,
            camera_factory=camera_factory,
            backend=backend,
            camera_index=camera_index,
        )

        config = self.picam2.create_video_configuration(
            main={"size": (width, height), "format": "BGR888"}
        )
        self.picam2.configure(config)
        self.picam2.start()

        self.frame = None
        self.lock = threading.Lock()
        self.running = True

        self.thread = threading.Thread(target=self._update, daemon=True)
        self.thread.start()

    def _build_camera(self, width, height, camera_factory, backend, camera_index):
        if camera_factory is not None:
            return camera_factory()

        backend = (backend or "auto").lower()

        if backend == "picamera2":
            if Picamera2 is None:
                raise ImportError("picamera2 is not installed")
            return Picamera2()

        if backend == "opencv":
            return OpenCVCamera(width=width, height=height, camera_index=camera_index)

        if backend == "auto":
            if Picamera2 is not None:
                try:
                    return Picamera2()
                except Exception as exc:
                    print("Pi camera unavailable, falling back to webcam:", exc)
            return OpenCVCamera(width=width, height=height, camera_index=camera_index)

        raise ValueError(f"Unsupported camera backend: {backend}")

    def _update(self):
        while self.running:
            try:
                frame = self.picam2.capture_array()
            except Exception as exc:
                print("Camera capture error:", exc)
                time.sleep(0.1)
                continue

            with self.lock:
                self.frame = frame
            time.sleep(0.01)

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        self.running = False
        if self.thread.is_alive():
            self.thread.join(timeout=0.5)
        self.picam2.stop()
