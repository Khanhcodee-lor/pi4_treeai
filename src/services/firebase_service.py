import os
from datetime import datetime

import firebase_admin
from firebase_admin import credentials, db, storage


class FirebaseService:
    def __init__(
        self,
        key_path,
        db_url,
        storage_bucket=None,
        command_path="commands/capture",
        result_latest_path="detections/latest",
        result_history_path="detections/history",
    ):
        self.enabled = False
        self.bucket = None
        self.command_path = command_path
        self.result_latest_path = result_latest_path
        self.result_history_path = result_history_path

        if not os.path.exists(key_path):
            print("Firebase key not found at:", key_path)
            return

        cred = credentials.Certificate(key_path)
        options = {"databaseURL": db_url}
        if storage_bucket:
            options["storageBucket"] = storage_bucket

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(cred, options)

        self.enabled = True
        self.bucket = storage.bucket() if storage_bucket else None
        print("Firebase initialized. DB:", db_url, "Storage bucket:", storage_bucket)

    def _now(self):
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def _safe_key(self, value):
        return str(value).translate(
            str.maketrans(
                {
                    ".": "_",
                    "#": "_",
                    "$": "_",
                    "[": "_",
                    "]": "_",
                    "/": "_",
                }
            )
        )

    def get_capture_command(self):
        if not self.enabled:
            return None

        try:
            command = db.reference(self.command_path).get()
        except Exception as e:
            print("Firebase command read error:", e)
            return None

        if not isinstance(command, dict):
            return None

        should_capture = bool(command.get("capture"))
        status = command.get("status", "pending")
        if not should_capture or status not in ("pending", "", None):
            return None

        request_id = command.get("request_id") or datetime.now().strftime("%Y%m%d_%H%M%S")
        command["request_id"] = str(request_id)
        return command

    def update_capture_status(self, status, request_id=None, extra=None):
        if not self.enabled:
            return

        payload = {
            "status": status,
            "updated_at": self._now(),
        }
        if request_id is not None:
            payload["request_id"] = str(request_id)
        if extra:
            payload.update(extra)

        try:
            db.reference(self.command_path).update(payload)
        except Exception as e:
            print("Firebase command update error:", e)

    def upload_image(self, snapshot_local_path, folder="detections"):
        if not self.bucket or not snapshot_local_path or not os.path.exists(snapshot_local_path):
            return snapshot_local_path

        try:
            blob_name = os.path.basename(snapshot_local_path)
            blob = self.bucket.blob(f"{folder}/{blob_name}")
            blob.upload_from_filename(snapshot_local_path)
            blob.make_public()
            return blob.public_url
        except Exception as e:
            print("Firebase Storage upload error:", e)
            return snapshot_local_path

    def push_capture_result(
        self,
        request_id,
        detections,
        diseases,
        snapshot_local_path=None,
        upload_to_storage=False,
    ):
        if not self.enabled:
            return None

        snapshot_ref = snapshot_local_path
        if upload_to_storage:
            snapshot_ref = self.upload_image(snapshot_local_path, folder="captures")

        top_detection = max(detections, key=lambda item: item["confidence"], default=None)
        data = {
            "request_id": str(request_id),
            "time": self._now(),
            "status": "done",
            "class": top_detection["label"] if top_detection else None,
            "confidence": top_detection["confidence"] if top_detection else 0.0,
            "snapshot": snapshot_ref,
            "diseases": diseases,
            "detections": detections,
            "detection_count": len(detections),
        }

        try:
            db.reference(self.result_latest_path).set(data)
            db.reference(self.result_history_path).child(self._safe_key(request_id)).set(data)
        except Exception as e:
            print("Firebase DB push error:", e)

        return data

    def push_detection(self, label, confidence, snapshot_local_path=None, upload_to_storage=False):
        detections = [
            {
                "label": label,
                "confidence": float(confidence),
                "box": None,
            }
        ]
        return self.push_capture_result(
            request_id=datetime.now().strftime("%Y%m%d_%H%M%S"),
            detections=detections,
            diseases=[label],
            snapshot_local_path=snapshot_local_path,
            upload_to_storage=upload_to_storage,
        )

    def complete_capture_command(self, request_id, result=None):
        extra = {
            "capture": False,
            "processed_at": self._now(),
        }
        if result is not None:
            extra["result"] = result
        self.update_capture_status("done", request_id=request_id, extra=extra)

    def fail_capture_command(self, request_id, error):
        self.update_capture_status(
            "failed",
            request_id=request_id,
            extra={
                "capture": False,
                "error": str(error),
                "processed_at": self._now(),
            },
        )
