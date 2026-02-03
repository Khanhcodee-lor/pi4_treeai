import os
from datetime import datetime
import firebase_admin
from firebase_admin import credentials, db, storage

class FirebaseService:
    def __init__(self, key_path, db_url, storage_bucket=None):
        self.enabled = False
        if not os.path.exists(key_path):
            print("Firebase key not found at:", key_path)
            return
        cred = credentials.Certificate(key_path)
        firebase_admin.initialize_app(cred, {
            'databaseURL': db_url,
            'storageBucket': storage_bucket if storage_bucket else None
        })
        self.enabled = True
        self.bucket = storage.bucket() if storage_bucket else None
        print("Firebase initialized. DB:", db_url, "Storage bucket:", storage_bucket)

    def push_detection(self, label, confidence, snapshot_local_path=None, upload_to_storage=False):
        if not self.enabled:
            return
        data = {
            "class": label,
            "confidence": float(confidence),
            "time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "snapshot": snapshot_local_path
        }

        if upload_to_storage and self.bucket and snapshot_local_path and os.path.exists(snapshot_local_path):
            try:
                blob_name = os.path.basename(snapshot_local_path)
                blob = self.bucket.blob(f"detections/{blob_name}")
                blob.upload_from_filename(snapshot_local_path)
                blob.make_public()
                data["snapshot"] = blob.public_url
            except Exception as e:
                print("Firebase Storage upload error:", e)

        try:
            db.reference("detections/latest").set(data)
            db.reference("detections/history").push(data)
        except Exception as e:
            print("Firebase DB push error:", e)

    def push_stream_url(self, url):
        if not self.enabled:
            return
        try:
            db.reference("stream/video_url").set(url)
            print("Pushed ngrok URL to Firebase:", url)
        except Exception as e:
            print("Push stream url error:", e)
