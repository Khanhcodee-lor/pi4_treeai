import asyncio
import json
import threading
import time

try:
    from bleak import BleakClient, BleakScanner
except ImportError:
    BleakClient = None
    BleakScanner = None


class BleJsonReceiver:
    """BLE client that receives JSON payloads via notifications."""

    def __init__(
        self,
        device_name=None,
        address=None,
        service_uuid=None,
        notify_char_uuid=None,
        scan_timeout=6.0,
        connect_timeout=10.0,
        reconnect_delay=3.0,
        max_buffer_bytes=4096,
    ):
        self.device_name = (device_name or "").strip() or None
        self._device_name_lc = self.device_name.lower() if self.device_name else None
        self.address = (address or "").strip() or None
        self.service_uuid = (service_uuid or "").strip().lower() or None
        self.notify_char_uuid = (notify_char_uuid or "").strip().lower() or None
        self.scan_timeout = max(1.0, float(scan_timeout))
        self.connect_timeout = max(1.0, float(connect_timeout))
        self.reconnect_delay = max(1.0, float(reconnect_delay))
        self.max_buffer_bytes = max(256, int(max_buffer_bytes))

        self._buffer = ""
        self._lock = threading.Lock()
        self._thread = None
        self._loop = None
        self._stop_event = threading.Event()

        self._latest_payload = None
        self._last_received_at = 0.0
        self._last_error = None
        self._connected = False

    def start(self):
        if BleakClient is None or BleakScanner is None:
            self._set_error("bleak_not_installed")
            return False
        if not self.notify_char_uuid:
            self._set_error("ble_notify_char_uuid_missing")
            return False

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        return True

    def stop(self):
        self._stop_event.set()
        if self._loop is not None:
            try:
                self._loop.call_soon_threadsafe(lambda: None)
            except Exception:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5)
            self._thread = None

    def get_latest(self):
        with self._lock:
            return (
                self._latest_payload,
                self._last_received_at,
                self._last_error,
                self._connected,
            )

    def _run(self):
        self._loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self._loop)
        try:
            self._loop.run_until_complete(self._run_async())
        finally:
            try:
                self._loop.close()
            except Exception:
                pass
            self._loop = None

    async def _run_async(self):
        while not self._stop_event.is_set():
            device = None
            try:
                device = await self._find_device()
            except Exception as exc:
                self._set_error(f"ble_scan_failed: {exc}")

            if device is None:
                await asyncio.sleep(self.reconnect_delay)
                continue

            try:
                await self._connect_and_listen(device)
            except Exception as exc:
                self._set_error(f"ble_connect_failed: {exc}")

            self._set_connected(False)
            await asyncio.sleep(self.reconnect_delay)

    async def _find_device(self):
        if self.address:
            return self.address

        devices = await BleakScanner.discover(timeout=self.scan_timeout)
        if not devices:
            self._set_error("ble_device_not_found")
            return None

        if self._device_name_lc:
            for dev in devices:
                name = (dev.name or "").strip()
                if name and name.lower() == self._device_name_lc:
                    return dev

        if self.service_uuid:
            for dev in devices:
                uuids = self._extract_device_uuids(dev)
                if self.service_uuid in uuids:
                    return dev

        self._set_error("ble_device_not_found")
        return None

    def _extract_device_uuids(self, dev):
        uuids = []

        metadata = getattr(dev, "metadata", None)
        if isinstance(metadata, dict):
            uuids = metadata.get("uuids") or metadata.get("service_uuids") or []

        if not uuids:
            details = getattr(dev, "details", None)
            if isinstance(details, dict):
                uuids = details.get("uuids") or details.get("service_uuids") or []

        return [item.lower() for item in uuids if isinstance(item, str)]

    async def _connect_and_listen(self, device):
        async with BleakClient(device, timeout=self.connect_timeout) as client:
            self._set_connected(True)

            try:
                await client.start_notify(self.notify_char_uuid, self._handle_notify)
            except Exception as exc:
                self._set_error(f"ble_notify_start_failed: {exc}")
                return

            while not self._stop_event.is_set():
                if not client.is_connected:
                    break
                await asyncio.sleep(0.5)

            try:
                if client.is_connected:
                    await client.stop_notify(self.notify_char_uuid)
            except Exception:
                pass

    def _handle_notify(self, _sender, data):
        try:
            chunk = bytes(data).decode("utf-8", errors="ignore")
        except Exception:
            return

        if not chunk:
            return

        with self._lock:
            self._buffer += chunk
            if len(self._buffer) > self.max_buffer_bytes:
                self._buffer = ""
                self._last_error = "ble_buffer_overflow"
                return

            if "\n" in self._buffer:
                lines = self._buffer.split("\n")
                self._buffer = lines[-1]
                for line in lines[:-1]:
                    self._try_parse(line)
                return

            trimmed = self._buffer.strip()
            if trimmed.startswith("{") and trimmed.endswith("}"):
                self._try_parse(trimmed)
                self._buffer = ""

    def _try_parse(self, text):
        raw = (text or "").strip()
        if not raw:
            return

        try:
            payload = json.loads(raw)
        except Exception as exc:
            self._last_error = f"ble_json_parse_failed: {exc}"
            return

        if not isinstance(payload, dict):
            self._last_error = "ble_json_not_object"
            return

        self._latest_payload = payload
        self._last_received_at = time.time()
        self._last_error = None

    def _set_error(self, message):
        with self._lock:
            self._last_error = message

    def _set_connected(self, connected):
        with self._lock:
            self._connected = bool(connected)
