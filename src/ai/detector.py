from ultralytics import YOLO
import time

class DiseaseDetector:
    def __init__(self, model_path, conf, interval):
        self.model = YOLO(model_path)
        self.conf = conf
        self.interval = interval
        self.last_run = 0
        self.last_result = None

    def detect_if_needed(self, frame):
        now = time.time()
        if now - self.last_run >= self.interval:
            self.last_result = self.model(frame, conf=self.conf, verbose=False)[0]
            self.last_run = now
        return self.last_result
