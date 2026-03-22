import base64
import cv2
import requests
import numpy as np


class RemoteDetector:
    """Simple HTTP client to send frames to detection server"""
    
    def __init__(self, server_url, conf=0.5):
        """
        Args:
            server_url: Detection server endpoint (e.g., http://192.168.1.100:5000/detect)
            conf: Confidence threshold
        """
        base_url = server_url.rstrip("/")
        if base_url.endswith("/detect"):
            self.base_url = base_url[: -len("/detect")]
            self.detect_url = base_url
        else:
            self.base_url = base_url
            self.detect_url = f"{base_url}/detect"

        self.conf = conf
        print(f"Detector: {self.detect_url}")
        self._test_connection()
    
    def _test_connection(self):
        """Test server connectivity"""
        try:
            resp = requests.get(f"{self.base_url}/health", timeout=2)
            if resp.status_code == 200:
                print("✓ Server OK")
            else:
                print(f"⚠ Server status {resp.status_code}")
        except Exception as e:
            print(f"✗ Server unreachable: {e}")
    
    def _frame_to_base64(self, frame):
        """Convert frame to base64"""
        _, buffer = cv2.imencode(".jpg", frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        return base64.b64encode(buffer).decode("utf-8")
    
    def send_frame(self, frame):
        """
        Send frame to server for detection
        
        Returns:
            dict: {detections: [...], count: N} or None on error
        """
        try:
            frame_b64 = self._frame_to_base64(frame)
            payload = {"image": frame_b64, "conf": self.conf}
            
            resp = requests.post(self.detect_url, json=payload, timeout=5)
            resp.raise_for_status()
            
            return resp.json()
        
        except Exception as e:
            print(f"Frame send error: {e}")
            return None
