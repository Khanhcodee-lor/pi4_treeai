from flask import Flask, Response
import cv2
from src.services.stream_service import draw_boxes

def create_app(camera, detector, config):
    app = Flask(__name__)

    def gen_frames():
        while True:
            frame = camera.get_frame()
            if frame is None:
                continue

            results = detector.detect_if_needed(frame)
            frame = draw_boxes(frame, results)

            ret, buffer = cv2.imencode(".jpg", frame)
            if not ret:
                continue

            yield (b"--frame\r\n"
                   b"Content-Type: image/jpeg\r\n\r\n" +
                   buffer.tobytes() + b"\r\n")

    @app.route("/video")
    def video():
        return Response(gen_frames(),
                        mimetype="multipart/x-mixed-replace; boundary=frame")

    @app.route("/")
    def index():
        return "<h3>Tomato Disease Detection</h3><img src='/video'>"

    return app
