import shutil
import subprocess


def _split_nmcli_terse(line, expected_parts):
    """Split nmcli -t output by unescaped ':' and unescape values."""
    parts = []
    current = []
    escaped = False

    for ch in line:
        if escaped:
            current.append(ch)
            escaped = False
            continue

        if ch == "\\":
            escaped = True
            continue

        if ch == ":" and len(parts) < expected_parts - 1:
            parts.append("".join(current))
            current = []
            continue

        current.append(ch)

    parts.append("".join(current))
    if len(parts) < expected_parts:
        parts.extend([""] * (expected_parts - len(parts)))
    return [item.strip() for item in parts[:expected_parts]]


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
        try:
            cmd = [
                "nmcli",
                "-t",
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
                # Fallback for older/different nmcli variants.
                fallback_cmd = [
                    "nmcli",
                    "-t",
                    "-f",
                    "SSID,SIGNAL,SECURITY",
                    "dev",
                    "wifi",
                    "list",
                ]
                code, out, err = self._run(fallback_cmd, timeout=25)

            if code != 0:
                return {"ok": False, "error": err or out or "Unable to scan Wi-Fi"}

            networks = []
            seen_ssid = set()
            for row in out.splitlines():
                ssid, signal_raw, security_raw = _split_nmcli_terse(row, 3)

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
                        "security": security_raw or "OPEN",
                    }
                )

            networks.sort(key=lambda item: item["signal"], reverse=True)
            return {"ok": True, "networks": networks[:max_items]}
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def connect(self, ssid, password=None):
        if not ssid:
            return {"ok": False, "error": "SSID is required"}

        try:
            # Best effort cleanup when a stale profile with same SSID exists.
            self._run(["nmcli", "connection", "delete", ssid], timeout=5)

            cmd = ["nmcli", "dev", "wifi", "connect", ssid, "ifname", self.interface]
            if password:
                cmd.extend(["password", password])

            code, out, err = self._run(cmd, timeout=40)
            if code != 0:
                # Fallback for nmcli variants rejecting ifname argument order/mode.
                fallback_cmd = ["nmcli", "dev", "wifi", "connect", ssid]
                if password:
                    fallback_cmd.extend(["password", password])
                code, out, err = self._run(fallback_cmd, timeout=40)

            if code != 0:
                return {"ok": False, "error": err or out or "Unable to connect Wi-Fi"}

            status = self.status()
            return {
                "ok": True,
                "message": out or "Connected",
                "status": status,
            }
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

    def status(self):
        status = {
            "interface": self.interface,
            "state": "unknown",
            "connection": None,
            "ip": None,
        }

        try:
            cmd_status = ["nmcli", "-t", "-f", "DEVICE,STATE,CONNECTION", "device", "status"]
            code, out, err = self._run(cmd_status, timeout=10)
            if code != 0:
                status["error"] = err or out or "Unable to read interface status"
                return status

            target_interface = self.interface
            found = False

            for row in out.splitlines():
                device, state, connection = _split_nmcli_terse(row, 3)
                if not device:
                    continue

                if device == self.interface:
                    target_interface = device
                    status["state"] = state
                    status["connection"] = connection if connection and connection != "--" else None
                    found = True
                    break

            if not found:
                # Fallback to first wlan* interface if configured one isn't listed.
                for row in out.splitlines():
                    device, state, connection = _split_nmcli_terse(row, 3)
                    if not device.startswith("wlan"):
                        continue

                    target_interface = device
                    status["interface"] = device
                    status["state"] = state
                    status["connection"] = connection if connection and connection != "--" else None
                    found = True
                    break

            if not found:
                status["error"] = "No wlan interface found"
                return status

            cmd_ip = ["nmcli", "-t", "-f", "IP4.ADDRESS", "dev", "show", target_interface]
            code, out, _ = self._run(cmd_ip, timeout=10)
            if code == 0:
                for row in out.splitlines():
                    if not row.startswith("IP4.ADDRESS"):
                        continue

                    _, value = row.split(":", 1)
                    status["ip"] = value.split("/", 1)[0].strip()
                    break

            return status
        except Exception as exc:
            status["error"] = str(exc)
            return status
