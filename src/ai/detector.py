import time

from ultralytics import YOLO


class DiseaseDetector:
    def __init__(self, model_path, conf=0.5, interval=0.8):
        print("Loading YOLO model:", model_path)
        self.model = YOLO(model_path)
        self.conf = conf
        self.interval = interval
        self._last_run = 0
        self._last_result = None

    def detect(self, frame):
        try:
            self._last_result = self.model(frame, conf=self.conf, verbose=False)[0]
        except Exception as e:
            print("Detector error:", e)
            self._last_result = None
        self._last_run = time.time()
        return self._last_result

    def detect_if_needed(self, frame):
        now = time.time()
        if now - self._last_run >= self.interval:
            self.detect(frame)
        return self._last_result

    def get_last(self):
        return self._last_result
