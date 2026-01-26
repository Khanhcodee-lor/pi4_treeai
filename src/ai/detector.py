# src/ai/detector.py
from ultralytics import YOLO
import time

class DiseaseDetector:
    def __init__(self, model_path, conf=0.5, interval=0.8):
        print("Loading YOLO model:", model_path)
        self.model = YOLO(model_path)
        self.conf = conf
        self.interval = interval
        self._last_run = 0
        self._last_result = None

    def detect_if_needed(self, frame):
        now = time.time()
        if now - self._last_run >= self.interval:
            # run detection (returns a Results object; we take the first )
            try:
                results = self.model(frame, conf=self.conf, verbose=False)[0]
                self._last_result = results
            except Exception as e:
                print("Detector error:", e)
                self._last_result = None
            self._last_run = now
        return self._last_result

    def get_last(self):
        return self._last_result
