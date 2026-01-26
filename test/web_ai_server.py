from flask import Flask, Response
from picamera2 import Picamera2
from ultralytics import YOLO
import cv2
import time

# ---------------- CONFIG ----------------
MODEL_PATH = "models/best.pt"
CONF = 0.5
WIDTH = 640
HEIGHT = 480
# ----------------------------------------

app = Flask(__name__)

# Load YOLO model
model = YOLO(MODEL_PATH)

# Init camera
picam2 = Picamera2()
config = picam2.create_preview_configuration(
    main={"format": "BGR888", "size": (WIDTH, HEIGHT)}
)
picam2.configure(config)
picam2.start()
time.sleep(1)

def gen_frames():
    while True:
        frame = picam2.capture_array()

        # Detect
        results = model(frame, conf=CONF, verbose=False)[0]

        for box in results.boxes:
            x1, y1, x2, y2 = map(int, box.xyxy[0])
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            label = f"{results.names[cls_id]} {conf:.2f}"

            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(
                frame,
                label,
                (x1, y1 - 8),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                2
            )

        # Encode JPEG
        ret, buffer = cv2.imencode(".jpg", frame)
        if not ret:
            continue

        frame_bytes = buffer.tobytes()
        yield (b"--frame\r\n"
               b"Content-Type: image/jpeg\r\n\r\n" +
               frame_bytes + b"\r\n")

@app.route("/")
def index():
    return """
    <html>
        <head>
            <title>Tomato Disease Detection</title>
        </head>
        <body>
            <h2>🍅 Tomato Leaf Disease Detection</h2>
            <img src="/video">
        </body>
    </html>
    """

@app.route("/video")
def video():
    return Response(gen_frames(),
                    mimetype="multipart/x-mixed-replace; boundary=frame")

if __name__ == "__main__":
    print("🚀 Web AI đang chạy tại http://0.0.0.0:8000")
    app.run(host="0.0.0.0", port=8000, threaded=True)
