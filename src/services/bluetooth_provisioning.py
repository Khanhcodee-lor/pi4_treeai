import json
import socket
import time

from src.services.wifi_manager import WiFiManager


class BluetoothProvisioningServer:
    """Bluetooth RFCOMM server for Wi-Fi provisioning from mobile apps."""

    def __init__(self, channel=4, interface="wlan0", backlog=1):
        self.channel = int(channel)
        self.backlog = backlog
        self.wifi = WiFiManager(interface=interface)
        self.server = None
        self.running = False

    def _send_json(self, conn, payload):
        body = json.dumps(payload, ensure_ascii=True) + "\n"
        conn.sendall(body.encode("utf-8"))

    def _handle_action(self, action, payload):
        if action == "ping":
            return {"ok": True, "action": action, "ts": time.time()}

        if action == "scan_wifi":
            result = self.wifi.scan_networks()
            result["action"] = action
            return result

        if action == "wifi_status":
            return {
                "ok": True,
                "action": action,
                "status": self.wifi.status(),
            }

        if action == "connect_wifi":
            ssid = (payload.get("ssid") or "").strip()
            password = payload.get("password")
            result = self.wifi.connect(ssid=ssid, password=password)
            result["action"] = action
            result["ssid"] = ssid
            return result

        return {
            "ok": False,
            "action": action,
            "error": "Unsupported action",
            "supported": ["ping", "scan_wifi", "wifi_status", "connect_wifi"],
        }

    def _handle_client(self, conn, addr):
        print(f"Bluetooth client connected: {addr}")
        self._send_json(conn, {"ok": True, "event": "welcome", "message": "Pi4 provisioning ready"})

        buffer = ""
        while self.running:
            data = conn.recv(4096)
            if not data:
                break

            buffer += data.decode("utf-8", errors="ignore")

            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                line = line.strip()
                if not line:
                    continue

                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    self._send_json(
                        conn,
                        {"ok": False, "error": "Invalid JSON", "hint": "Send one JSON object per line"},
                    )
                    continue

                action = payload.get("action")
                if not action:
                    self._send_json(conn, {"ok": False, "error": "Missing action"})
                    continue

                try:
                    response = self._handle_action(action, payload)
                except Exception as exc:
                    response = {
                        "ok": False,
                        "action": action,
                        "error": str(exc),
                    }

                self._send_json(conn, response)

        print(f"Bluetooth client disconnected: {addr}")

    def start(self):
        self.server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.server.bind(("", self.channel))
        self.server.listen(self.backlog)
        self.running = True

        print("=" * 60)
        print("Pi4 Bluetooth Wi-Fi Provisioning Server")
        print("=" * 60)
        print(f"RFCOMM channel: {self.channel}")
        print(f"Wi-Fi interface: {self.wifi.interface}")
        print("Waiting for Bluetooth client...\n")

        try:
            while self.running:
                conn, addr = self.server.accept()
                try:
                    self._handle_client(conn, addr)
                finally:
                    conn.close()
        except KeyboardInterrupt:
            print("\nStopping provisioning server...")
        finally:
            self.stop()

    def stop(self):
        self.running = False
        if self.server is not None:
            try:
                self.server.close()
            except OSError:
                pass