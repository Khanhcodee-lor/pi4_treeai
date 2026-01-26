import threading
import time
from picamera2 import Picamera2
import cv2

class CameraManager:
    def __init__(self, width=640, height=480):
        self.picam2 = Picamera2()
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

    def _update(self):
        while self.running:
            frame = self.picam2.capture_array()
            with self.lock:
                self.frame = frame
            time.sleep(0.01)

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()

    def stop(self):
        self.running = False
        time.sleep(0.2)
        self.picam2.stop()
