import json
import socket
import subprocess
import time

from src.services.wifi_manager import WiFiManager


class ProvisioningCommandProcessor:
    """Handle Wi-Fi provisioning actions shared by RFCOMM and BLE servers."""

    SUPPORTED_ACTIONS = [
        "ping",
        "scan_wifi",
        "wifi_status",
        "connect_wifi",
        "device_status",
    ]

    def __init__(self, interface="wlan0", scan_limit=12):
        self.wifi = WiFiManager(interface=interface)
        self.scan_limit = int(scan_limit)

    def _run_command(self, args, timeout=10):
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        return proc.returncode, stdout, stderr

    def _read_host_ips(self):
        code, out, _ = self._run_command(["hostname", "-I"], timeout=5)
        if code != 0 or not out:
            return []
        return [item for item in out.split() if item]

    def _read_ssh_service_status(self):
        candidates = ("ssh", "sshd")
        result = {
            "service": None,
            "active": False,
            "enabled": False,
            "listening": False,
            "error": None,
        }

        for service_name in candidates:
            code, out, err = self._run_command(
                ["systemctl", "show", service_name, "--property", "LoadState", "--value"],
                timeout=5,
            )
            load_state = (out or "").strip()
            if code == 0 and load_state and load_state != "not-found":
                result["service"] = service_name
                break

        if result["service"] is None:
            result["error"] = "ssh service not found"
        else:
            service_name = result["service"]
            code, out, err = self._run_command(["systemctl", "is-active", service_name], timeout=5)
            result["active"] = code == 0 and out == "active"
            if code != 0 and not out:
                result["error"] = err or "Unable to read ssh active state"

            code, out, err = self._run_command(["systemctl", "is-enabled", service_name], timeout=5)
            result["enabled"] = code == 0 and out == "enabled"
            if code != 0 and not out and result["error"] is None:
                result["error"] = err or "Unable to read ssh enabled state"

        code, out, err = self._run_command(["ss", "-tln"], timeout=5)
        if code == 0:
            result["listening"] = any(":22" in line for line in out.splitlines())
        elif result["error"] is None:
            result["error"] = err or "Unable to inspect listening sockets"

        return result

    def _device_status(self):
        return {
            "ok": True,
            "hostname": socket.gethostname(),
            "wifi": self.wifi.status(),
            "ips": self._read_host_ips(),
            "ssh": self._read_ssh_service_status(),
        }

    def handle_action(self, action, payload):
        if action == "ping":
            return {"ok": True, "action": action, "ts": time.time()}

        if action == "scan_wifi":
            requested_limit = payload.get("limit", self.scan_limit)
            try:
                max_items = max(1, min(int(requested_limit), 30))
            except (TypeError, ValueError):
                max_items = self.scan_limit
            result = self.wifi.scan_networks(max_items=max_items)
            result["action"] = action
            result["limit"] = max_items
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

        if action == "device_status":
            result = self._device_status()
            result["action"] = action
            return result

        return {
            "ok": False,
            "action": action,
            "error": "Unsupported action",
            "supported": self.SUPPORTED_ACTIONS,
        }


class BluetoothProvisioningServer:
    """Bluetooth RFCOMM server for Wi-Fi provisioning from mobile apps."""

    def __init__(
        self,
        channel=4,
        interface="wlan0",
        backlog=1,
        device_name="khanhpi",
        auto_configure_adapter=True,
        scan_limit=12,
    ):
        self.channel = int(channel)
        self.backlog = backlog
        self.processor = ProvisioningCommandProcessor(interface=interface, scan_limit=scan_limit)
        self.device_name = (device_name or "khanhpi").strip() or "khanhpi"
        self.auto_configure_adapter = bool(auto_configure_adapter)
        self.server = None
        self.running = False

    @property
    def wifi(self):
        return self.processor.wifi

    def _configure_adapter(self):
        """Ensure Bluetooth adapter is powered, renamed, and connectable."""
        commands = [
            "power on",
            f"system-alias {self.device_name}",
            "discoverable on",
            "discoverable-timeout 0",
            "pairable on",
            "pairable-timeout 0",
            "agent on",
            "default-agent",
            "show",
            "quit",
        ]

        cmd = ["bluetoothctl"]
        try:
            proc = subprocess.run(
                cmd,
                input="\n".join(commands) + "\n",
                capture_output=True,
                text=True,
                timeout=15,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        if proc.returncode != 0:
            err = (proc.stderr or "").strip()
            out = (proc.stdout or "").strip()
            return {"ok": False, "error": err or out or "bluetoothctl failed"}

        return {"ok": True}

    def _send_json(self, conn, payload):
        body = json.dumps(payload, ensure_ascii=True) + "\n"
        conn.sendall(body.encode("utf-8"))

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
                    response = self.processor.handle_action(action, payload)
                except Exception as exc:
                    response = {
                        "ok": False,
                        "action": action,
                        "error": str(exc),
                    }

                self._send_json(conn, response)

        print(f"Bluetooth client disconnected: {addr}")

    def start(self):
        if self.auto_configure_adapter:
            config = self._configure_adapter()
            if config.get("ok"):
                print(f"Bluetooth alias set to: {self.device_name}")
            else:
                print(f"Bluetooth setup warning: {config.get('error')}")

        self.server = socket.socket(socket.AF_BLUETOOTH, socket.SOCK_STREAM, socket.BTPROTO_RFCOMM)
        self.server.bind(("", self.channel))
        self.server.listen(self.backlog)
        self.running = True

        print("=" * 60)
        print("Pi4 Bluetooth Wi-Fi Provisioning Server (RFCOMM)")
        print("=" * 60)
        print(f"Bluetooth name: {self.device_name}")
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
