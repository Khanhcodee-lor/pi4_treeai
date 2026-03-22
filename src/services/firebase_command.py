import firebase_admin
from firebase_admin import db
import json
import time
import sys


class FirebaseCommandListener:
    """Listen for capture commands from Firebase RTDB"""
    
    def __init__(self, db_url, device_id):
        """
        Args:
            db_url: Firebase RTDB URL (e.g., https://xxx.firebasedatabase.app/)
            device_id: Device ID
        """
        self.db_url = db_url.rstrip("/")
        self.device_id = device_id
        self.command_path = f"plants/{device_id}/commands/capture"
        
        # Initialize Firebase
        try:
            # Check if already initialized
            try:
                firebase_admin.get_app()
            except ValueError:
                # Not initialized yet
                options = {
                    'databaseURL': self.db_url
                }
                firebase_admin.initialize_app(options=options)
            
            self.db = db
            self._last_command_id = None
            self._last_status = None
            
            print(f"🔥 Firebase: {self.db_url}")
            print(f"   Path: {self.command_path}")
            self._test_connection()
        
        except Exception as e:
            print(f"\n❌ Firebase initialization failed:")
            print(f"   Error: {e}")
            print(f"\n   Setup guide:")
            print(f"   1. Download service account key from Firebase Console")
            print(f"   2. Save as 'firebase_key.json' in project root")
            print(f"   3. Run: export GOOGLE_APPLICATION_CREDENTIALS=\"$(pwd)/firebase_key.json\"")
            print(f"   4. Or use: gcloud auth application-default login\n")
            sys.exit(1)
    
    def _test_connection(self):
        """Test Firebase connection"""
        try:
            ref = self.db.reference(self.command_path)
            ref.get()
            print("   ✓ Connected OK\n")
        except Exception as e:
            print(f"   ⚠️  Connection error: {e}")
            print(f"   Will retry on poll...\n")
    
    def get_command(self, timeout=1.0):
        """
        Poll Firebase for capture command
        
        Command formats:
        {
            "status": 1,
            "request_id": "cmd_123",
            "timestamp": 1234567890,
            "captured_at": "2026-03-22T23:10:05"
        }
        
        Returns:
            dict: Command if found, None otherwise
        """
        try:
            ref = self.db.reference(self.command_path)
            data = ref.get()
            
            if data is None:
                return None
            
            # If data is string (treated as single command)
            if isinstance(data, str):
                try:
                    data = json.loads(data)
                except:
                    pass
            
            if not isinstance(data, dict):
                return None

            # Status trigger mode: fire on edge 0 -> 1.
            status = data.get("status")
            if status is not None:
                status_int = int(status)
                should_fire = status_int == 1 and self._last_status != 1
                self._last_status = status_int

                if should_fire:
                    request_id = data.get("request_id") or f"status_{int(time.time())}"
                    return {
                        "request_id": request_id,
                        "timestamp": data.get("timestamp", time.time())
                    }
                return None
            
            # Check if this is a new command (not processed yet)
            request_id = data.get("request_id")
            if request_id and request_id != self._last_command_id:
                self._last_command_id = request_id
                return {
                    "request_id": request_id,
                    "timestamp": data.get("timestamp", time.time())
                }
            
            return None
        
        except Exception as e:
            print(f"Firebase get_command error: {e}")
            return None

    def acknowledge_command(self, request_id=None, captured_at=None):
        """Reset capture command node to status 0 with the agreed schema."""
        try:
            ref = self.db.reference(self.command_path)
            payload = {
                "status": 0,
                "request_id": request_id,
                "timestamp": time.time(),
                "captured_at": captured_at,
            }
            ref.set(payload)
            self._last_status = 0
        except Exception as e:
            print(f"Firebase acknowledge_command error: {e}")
    
    def update_status(self, status, request_id=None, extra=None):
        """Update capture status with optional extra metadata."""
        try:
            result_path = f"plants/{self.device_id}/detections/latest"
            ref = self.db.reference(result_path)
            
            payload = {
                "status": status,
                "request_id": request_id,
                "timestamp": time.time()
            }

            if isinstance(extra, dict):
                payload.update(extra)
            
            ref.update(payload)
        except Exception as e:
            print(f"Firebase update_status error: {e}")
