from flask import Flask, Response
import cv2

def create_stream_app(camera_manager):
    app = Flask(__name__)

    def gen():
        while True:
            frame = camera_manager.get_frame()
            if frame is None:
                continue
            _, jpeg = cv2.imencode(".jpg", frame)
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" +
                jpeg.tobytes() + b"\r\n"
            )

    @app.route("/video")
    def video():
        return Response(
            gen(),
            mimetype="multipart/x-mixed-replace; boundary=frame"
        )

    return app
