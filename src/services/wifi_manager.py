import shutil
import subprocess


class WiFiManager:
    """Wrap nmcli commands for scanning and connecting Wi-Fi on Raspberry Pi."""

    def __init__(self, interface="wlan0"):
        self.interface = interface
        if shutil.which("nmcli") is None:
            raise RuntimeError("nmcli not found. Install NetworkManager before using Wi-Fi provisioning.")

    def _run(self, args, timeout=20):
        proc = subprocess.run(args, capture_output=True, text=True, timeout=timeout)
        stdout = (proc.stdout or "").strip()
        stderr = (proc.stderr or "").strip()
        return proc.returncode, stdout, stderr

    def scan_networks(self, max_items=30):
        cmd = [
            "nmcli",
            "-t",
            "--separator",
            "|",
            "-f",
            "SSID,SIGNAL,SECURITY",
            "dev",
            "wifi",
            "list",
            "ifname",
            self.interface,
            "--rescan",
            "yes",
        ]
        code, out, err = self._run(cmd, timeout=25)
        if code != 0:
            return {"ok": False, "error": err or out or "Unable to scan Wi-Fi"}

        networks = []
        seen_ssid = set()
        for row in out.splitlines():
            parts = row.split("|", 2)
            if len(parts) != 3:
                continue

            ssid = parts[0].strip()
            signal_raw = parts[1].strip()
            security = parts[2].strip() or "OPEN"

            if not ssid or ssid in seen_ssid:
                continue

            seen_ssid.add(ssid)
            try:
                signal = int(signal_raw)
            except ValueError:
                signal = 0

            networks.append(
                {
                    "ssid": ssid,
                    "signal": signal,
                    "security": security,
                }
            )

        networks.sort(key=lambda item: item["signal"], reverse=True)
        return {"ok": True, "networks": networks[:max_items]}

    def connect(self, ssid, password=None):
        if not ssid:
            return {"ok": False, "error": "SSID is required"}

        cmd = ["nmcli", "dev", "wifi", "connect", ssid, "ifname", self.interface]
        if password:
            cmd.extend(["password", password])

        code, out, err = self._run(cmd, timeout=40)
        if code != 0:
            return {"ok": False, "error": err or out or "Unable to connect Wi-Fi"}

        status = self.status()
        return {
            "ok": True,
            "message": out or "Connected",
            "status": status,
        }

    def status(self):
        status = {
            "interface": self.interface,
            "state": "unknown",
            "connection": None,
            "ip": None,
        }

        cmd_status = ["nmcli", "-t", "--separator", "|", "-f", "DEVICE,STATE,CONNECTION", "device", "status"]
        code, out, err = self._run(cmd_status, timeout=10)
        if code != 0:
            status["error"] = err or out or "Unable to read interface status"
            return status

        for row in out.splitlines():
            parts = row.split("|", 2)
            if len(parts) != 3:
                continue
            device, state, connection = parts
            if device == self.interface:
                status["state"] = state
                status["connection"] = connection if connection and connection != "--" else None
                break

        cmd_ip = ["nmcli", "-t", "-f", "IP4.ADDRESS", "dev", "show", self.interface]
        code, out, _ = self._run(cmd_ip, timeout=10)
        if code == 0:
            for row in out.splitlines():
                if row.startswith("IP4.ADDRESS"):
                    _, value = row.split(":", 1)
                    status["ip"] = value.split("/", 1)[0].strip()
                    break

        return status