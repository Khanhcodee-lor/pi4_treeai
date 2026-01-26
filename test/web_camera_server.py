from flask import Flask, Response
from picamera2 import Picamera2
import cv2
import time

app = Flask(__name__)

# Init camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"format": "BGR888", "size": (640, 480)}
)
picam2.configure(config)
picam2.start()
time.sleep(1)

def gen_frames():
    while True:
        frame = picam2.capture_array()

        ret, buffer = cv2.imencode(
            ".jpg", frame,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )
        if not ret:
            continue

        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               buffer.tobytes() + b"\r\n")

@app.route("/")
def index():
    return """
    <html>
      <head><title>Pi Camera Live</title></head>
      <body>
        <h3>Raspberry Pi Camera</h3>
        <img src="/video">
      </body>
    </html>
    """

@app.route("/video")
def video():
    return Response(
        gen_frames(),
        mimetype="multipart/x-mixed-replace; boundary=frame"
    )

if __name__ == "__main__":
    print("Camera server running at http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, threaded=True)
