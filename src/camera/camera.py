from picamera2 import Picamera2
import time
import threading

class PiCameraService:
    def __init__(self, width, height):
        self.picam2 = Picamera2()
        config = self.picam2.create_preview_configuration(
            main={"format": "BGR888", "size": (width, height)}
        )
        self.picam2.configure(config)
        self.picam2.start()
        time.sleep(1)

        self.frame = None
        self.lock = threading.Lock()

        threading.Thread(target=self._update, daemon=True).start()

    def _update(self):
        while True:
            frame = self.picam2.capture_array()
            with self.lock:
                self.frame = frame

    def get_frame(self):
        with self.lock:
            return None if self.frame is None else self.frame.copy()
