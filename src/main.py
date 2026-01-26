from src.camera.camera import PiCameraService
from src.ai.detector import DiseaseDetector
from src.web.flask_app import create_app
from src.utils.config import *

camera = PiCameraService(WIDTH, HEIGHT)
detector = DiseaseDetector(MODEL_PATH, CONF, DETECT_INTERVAL)

app = create_app(camera, detector, None)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, threaded=True)
