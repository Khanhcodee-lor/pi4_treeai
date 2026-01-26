import requests
import time

class NgrokService:
    def __init__(self, port=8000):
        self.port = port

    def get_public_url(self, retry=10, delay=1):
        """
        Lấy URL public từ ngrok local API
        """
        for _ in range(retry):
            try:
                res = requests.get("http://127.0.0.1:4040/api/tunnels")
                data = res.json()
                for tunnel in data["tunnels"]:
                    if tunnel["proto"] == "https":
                        return tunnel["public_url"]
            except Exception:
                pass
            time.sleep(delay)
        return None
