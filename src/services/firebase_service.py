import firebase_admin
from firebase_admin import credentials, db
from datetime import datetime

class FirebaseService:
    def __init__(self, key_path, db_url):
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            "databaseURL": db_url
        })

    def push_detection(self, label, conf):
        ref = db.reference("detections/latest")
        ref.set({
            "class": label,
            "confidence": float(conf),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
