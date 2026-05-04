import json
import subprocess
import types
from urllib.parse import parse_qsl

from src.services.bluetooth_provisioning import ProvisioningCommandProcessor

try:
    import dbus
    import dbus.exceptions
    import dbus.mainloop.glib
    import dbus.service
    from gi.repository import GLib
    DBUS_AVAILABLE = True
except ImportError:
    DBUS_AVAILABLE = False
    GLib = None

    class _DummyDBusException(Exception):
        pass

    class _DummyServiceObject:
        def __init__(self, *args, **kwargs):
            return None

    def _dummy_decorator(*args, **kwargs):
        def wrapper(func):
            return func

        return wrapper

    dbus = types.SimpleNamespace(
        Byte=lambda value: value,
        String=str,
        Array=lambda values, signature=None: list(values),
        ObjectPath=str,
        exceptions=types.SimpleNamespace(DBusException=_DummyDBusException),
        service=types.SimpleNamespace(
            Object=_DummyServiceObject,
            method=_dummy_decorator,
            signal=_dummy_decorator,
        ),
        mainloop=types.SimpleNamespace(
            glib=types.SimpleNamespace(DBusGMainLoop=lambda *args, **kwargs: None)
        ),
    )


BLUEZ_SERVICE_NAME = "org.bluez"
DBUS_OM_IFACE = "org.freedesktop.DBus.ObjectManager"
DBUS_PROP_IFACE = "org.freedesktop.DBus.Properties"
GATT_MANAGER_IFACE = "org.bluez.GattManager1"
GATT_SERVICE_IFACE = "org.bluez.GattService1"
GATT_CHRC_IFACE = "org.bluez.GattCharacteristic1"
LE_ADVERTISING_MANAGER_IFACE = "org.bluez.LEAdvertisingManager1"
LE_ADVERTISEMENT_IFACE = "org.bluez.LEAdvertisement1"

PROVISIONING_SERVICE_UUID = "0f5c0001-95c7-43f1-b1d5-28f9f0dca001"
COMMAND_CHARACTERISTIC_UUID = "0f5c0002-95c7-43f1-b1d5-28f9f0dca001"
RESULT_CHARACTERISTIC_UUID = "0f5c0003-95c7-43f1-b1d5-28f9f0dca001"
STATUS_CHARACTERISTIC_UUID = "0f5c0004-95c7-43f1-b1d5-28f9f0dca001"
MAX_GATT_VALUE_BYTES = 512
MAX_RESULT_VALUE_BYTES = 480
MAX_COMMAND_BUFFER_BYTES = 4096


class InvalidArgsException(dbus.exceptions.DBusException if dbus else Exception):
    _dbus_error_name = "org.freedesktop.DBus.Error.InvalidArgs"


class NotSupportedException(dbus.exceptions.DBusException if dbus else Exception):
    _dbus_error_name = "org.bluez.Error.NotSupported"


class FailedException(dbus.exceptions.DBusException if dbus else Exception):
    _dbus_error_name = "org.bluez.Error.Failed"


class Application(dbus.service.Object):
    def __init__(self, bus):
        self.path = "/org/treeai/provision"
        self.services = []
        super().__init__(bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_service(self, service):
        self.services.append(service)

    @dbus.service.method(DBUS_OM_IFACE, out_signature="a{oa{sa{sv}}}")
    def GetManagedObjects(self):
        managed_objects = {}

        for service in self.services:
            managed_objects[service.get_path()] = service.get_properties()
            for characteristic in service.characteristics:
                managed_objects[characteristic.get_path()] = characteristic.get_properties()

        return managed_objects


class Service(dbus.service.Object):
    PATH_BASE = "/org/treeai/provision/service"

    def __init__(self, bus, index, uuid, primary=True):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.uuid = uuid
        self.primary = primary
        self.characteristics = []
        super().__init__(bus, self.path)

    def get_properties(self):
        return {
            GATT_SERVICE_IFACE: {
                "UUID": self.uuid,
                "Primary": self.primary,
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def add_characteristic(self, characteristic):
        self.characteristics.append(characteristic)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_SERVICE_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_SERVICE_IFACE]


class Characteristic(dbus.service.Object):
    def __init__(self, bus, index, uuid, flags, service):
        self.path = service.path + "/char" + str(index)
        self.bus = bus
        self.uuid = uuid
        self.flags = flags
        self.service = service
        super().__init__(bus, self.path)

    def get_properties(self):
        return {
            GATT_CHRC_IFACE: {
                "Service": self.service.get_path(),
                "UUID": self.uuid,
                "Flags": dbus.Array(self.flags, signature="s"),
            }
        }

    def get_path(self):
        return dbus.ObjectPath(self.path)

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != GATT_CHRC_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[GATT_CHRC_IFACE]

    @dbus.service.method(GATT_CHRC_IFACE, in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE, in_signature="aya{sv}")
    def WriteValue(self, value, options):
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        raise NotSupportedException()

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        raise NotSupportedException()

    @dbus.service.signal(DBUS_PROP_IFACE, signature="sa{sv}as")
    def PropertiesChanged(self, interface, changed, invalidated):
        return None


class Advertisement(dbus.service.Object):
    PATH_BASE = "/org/treeai/provision/advertisement"

    def __init__(self, bus, index, local_name, service_uuids):
        self.path = self.PATH_BASE + str(index)
        self.bus = bus
        self.local_name = local_name
        self.service_uuids = service_uuids
        super().__init__(bus, self.path)

    def get_path(self):
        return dbus.ObjectPath(self.path)

    def get_properties(self):
        return {
            LE_ADVERTISEMENT_IFACE: {
                "Type": "peripheral",
                "ServiceUUIDs": dbus.Array(self.service_uuids, signature="s"),
                "LocalName": dbus.String(self.local_name),
                "Includes": dbus.Array(["tx-power"], signature="s"),
            }
        }

    @dbus.service.method(DBUS_PROP_IFACE, in_signature="s", out_signature="a{sv}")
    def GetAll(self, interface):
        if interface != LE_ADVERTISEMENT_IFACE:
            raise InvalidArgsException()
        return self.get_properties()[LE_ADVERTISEMENT_IFACE]

    @dbus.service.method(LE_ADVERTISEMENT_IFACE, in_signature="", out_signature="")
    def Release(self):
        return None


class ResultCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        self.value = self._encode_json(
            {
                "ok": True,
                "event": "ready",
                "message": "BLE provisioning ready",
            }
        )
        super().__init__(bus, index, RESULT_CHARACTERISTIC_UUID, ["read"], service)

    def _json_bytes(self, payload):
        body = json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
        return body.encode("utf-8")

    def _encode_bytes(self, raw):
        return [dbus.Byte(byte) for byte in raw]

    def _encode_json(self, payload):
        return self._encode_bytes(self._json_bytes(payload))

    def _fit_payload_for_ble(self, payload):
        raw = self._json_bytes(payload)
        if len(raw) <= MAX_RESULT_VALUE_BYTES:
            return payload

        if isinstance(payload, dict) and isinstance(payload.get("networks"), list):
            total_networks = len(payload["networks"])
            for count in range(total_networks, -1, -1):
                candidate = dict(payload)
                candidate["networks"] = payload["networks"][:count]
                candidate["total_networks"] = total_networks
                candidate["truncated"] = count < total_networks
                if candidate["truncated"]:
                    candidate["message"] = "Scan result truncated to fit BLE payload limit"

                if len(self._json_bytes(candidate)) <= MAX_RESULT_VALUE_BYTES:
                    return candidate

        return {
            "ok": False,
            "error": "Response too large for BLE payload limit",
            "max_bytes": MAX_RESULT_VALUE_BYTES,
        }

    def _read_with_offset(self, options):
        offset = 0
        if options:
            try:
                offset = int(options.get("offset", 0))
            except (TypeError, ValueError):
                raise InvalidArgsException()

        if offset < 0 or offset > len(self.value):
            raise InvalidArgsException()

        return self.value[offset:]

    def set_payload(self, payload):
        fitted_payload = self._fit_payload_for_ble(payload)
        self.value = self._encode_json(fitted_payload)

    @dbus.service.method(GATT_CHRC_IFACE, in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        return self._read_with_offset(options)


class StatusCharacteristic(Characteristic):
    def __init__(self, bus, index, service):
        self.notifying = False
        self.sequence = 0
        self.value = self._encode_text("0")
        super().__init__(bus, index, STATUS_CHARACTERISTIC_UUID, ["read", "notify"], service)

    def _encode_text(self, text):
        return [dbus.Byte(byte) for byte in text.encode("utf-8")]

    def bump(self):
        self.sequence += 1
        self.value = self._encode_text(str(self.sequence))
        if self.notifying:
            self.PropertiesChanged(
                GATT_CHRC_IFACE,
                {"Value": dbus.Array(self.value, signature="y")},
                [],
            )

    @dbus.service.method(GATT_CHRC_IFACE, in_signature="a{sv}", out_signature="ay")
    def ReadValue(self, options):
        offset = 0
        if options:
            try:
                offset = int(options.get("offset", 0))
            except (TypeError, ValueError):
                raise InvalidArgsException()

        if offset < 0 or offset > len(self.value):
            raise InvalidArgsException()

        return self.value[offset:]

    @dbus.service.method(GATT_CHRC_IFACE)
    def StartNotify(self):
        self.notifying = True

    @dbus.service.method(GATT_CHRC_IFACE)
    def StopNotify(self):
        self.notifying = False


class CommandCharacteristic(Characteristic):
    def __init__(self, bus, index, service, server):
        self.server = server
        super().__init__(
            bus,
            index,
            COMMAND_CHARACTERISTIC_UUID,
            ["write", "write-without-response"],
            service,
        )

    @dbus.service.method(GATT_CHRC_IFACE, in_signature="aya{sv}")
    def WriteValue(self, value, options):
        raw_fragment = bytes(value).decode("utf-8", errors="ignore")
        self.server.process_command_fragment(raw_fragment, options)


class ProvisioningGattService(Service):
    def __init__(self, bus, index, server):
        super().__init__(bus, index, PROVISIONING_SERVICE_UUID, primary=True)
        self.result_characteristic = ResultCharacteristic(bus, 0, self)
        self.status_characteristic = StatusCharacteristic(bus, 1, self)
        self.command_characteristic = CommandCharacteristic(bus, 2, self, server)
        self.add_characteristic(self.result_characteristic)
        self.add_characteristic(self.status_characteristic)
        self.add_characteristic(self.command_characteristic)


class BLEProvisioningServer:
    """BLE GATT server for Wi-Fi provisioning from mobile apps."""

    def __init__(
        self,
        interface="wlan0",
        device_name="khanhpi",
        auto_configure_adapter=True,
        scan_limit=12,
    ):
        if not DBUS_AVAILABLE or GLib is None:
            raise RuntimeError(
                "BLE provisioning requires dbus-python and PyGObject. "
                "On Raspberry Pi OS install python3-dbus and python3-gi."
            )

        self.device_name = (device_name or "khanhpi").strip() or "khanhpi"
        self.auto_configure_adapter = bool(auto_configure_adapter)
        self.processor = ProvisioningCommandProcessor(interface=interface, scan_limit=scan_limit)
        self.bus = None
        self.mainloop = None
        self.app = None
        self.service = None
        self.advertisement = None
        self.adapter_path = None
        self._startup_complete = False
        self._startup_error = None
        self._startup_timeout_id = None
        self._command_buffers = {}

    @property
    def wifi(self):
        return self.processor.wifi

    def _configure_adapter(self):
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

        try:
            proc = subprocess.run(
                ["bluetoothctl"],
                input="\n".join(commands) + "\n",
                capture_output=True,
                text=True,
                timeout=15,
            )
        except Exception as exc:
            return {"ok": False, "error": str(exc)}

        if proc.returncode != 0:
            return {"ok": False, "error": (proc.stderr or proc.stdout or "bluetoothctl failed").strip()}

        return {"ok": True}

    def _find_adapter(self):
        remote_om = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME, "/"),
            DBUS_OM_IFACE,
        )
        objects = remote_om.GetManagedObjects()

        for path, interfaces in objects.items():
            if GATT_MANAGER_IFACE in interfaces and LE_ADVERTISING_MANAGER_IFACE in interfaces:
                return path

        raise RuntimeError("BLE adapter with GATT/Advertising manager not found")

    def _set_startup_error(self, message):
        if self._startup_error is None:
            self._startup_error = RuntimeError(message)

        if self.mainloop is not None and self.mainloop.is_running():
            self.mainloop.quit()

    def _register_app(self):
        service_manager = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
            GATT_MANAGER_IFACE,
        )
        service_manager.RegisterApplication(
            self.app.get_path(),
            {},
            reply_handler=self._on_app_registered,
            error_handler=self._on_app_registration_failed,
        )

    def _on_app_registered(self):
        self._register_advertisement()

    def _on_app_registration_failed(self, error):
        self._set_startup_error(f"RegisterApplication failed: {error}")

    def _register_advertisement(self):
        ad_manager = dbus.Interface(
            self.bus.get_object(BLUEZ_SERVICE_NAME, self.adapter_path),
            LE_ADVERTISING_MANAGER_IFACE,
        )
        ad_manager.RegisterAdvertisement(
            self.advertisement.get_path(),
            {},
            reply_handler=self._on_advertisement_registered,
            error_handler=self._on_advertisement_registration_failed,
        )

    def _on_advertisement_registered(self):
        self._startup_complete = True

        if self._startup_timeout_id is not None:
            GLib.source_remove(self._startup_timeout_id)
            self._startup_timeout_id = None

        print("=" * 60)
        print("Pi4 BLE Wi-Fi Provisioning Server")
        print("=" * 60)
        print(f"Bluetooth name: {self.device_name}")
        print(f"Wi-Fi interface: {self.wifi.interface}")
        print(f"Service UUID: {PROVISIONING_SERVICE_UUID}")
        print(f"Command Char UUID: {COMMAND_CHARACTERISTIC_UUID}")
        print(f"Result Char UUID: {RESULT_CHARACTERISTIC_UUID}")
        print(f"Status Char UUID: {STATUS_CHARACTERISTIC_UUID}")
        print("App flow: subscribe status, write command, read result.\n")

    def _on_advertisement_registration_failed(self, error):
        self._set_startup_error(f"RegisterAdvertisement failed: {error}")

    def _on_startup_timeout(self):
        if not self._startup_complete:
            self._set_startup_error(
                "Timed out while registering BLE GATT app/advertisement with BlueZ"
            )

        return False

    def _client_key(self, options):
        if not options:
            return "_default"

        device = options.get("device")
        if device:
            return str(device)

        link = options.get("link")
        if link:
            return str(link)

        return "_default"

    def _extract_complete_commands(self, buffer):
        commands = []
        pending = buffer.replace("\r", "")

        while "\n" in pending:
            line, pending = pending.split("\n", 1)
            line = line.strip()
            if line:
                commands.append(line)

        tail = pending.strip()
        if not tail:
            return commands, ""

        if tail.startswith("{"):
            try:
                json.loads(tail)
            except json.JSONDecodeError:
                return commands, pending

            commands.append(tail)
            return commands, ""

        if "{" in tail or "}" in tail:
            return commands, pending

        commands.append(tail)
        return commands, ""

    def _parse_compact_command(self, raw):
        action, has_query_separator, query = raw.partition("?")
        action = action.strip()
        if not action:
            raise ValueError("Missing action")

        payload = {"action": action}
        if has_query_separator and query:
            for key, value in parse_qsl(query, keep_blank_values=True):
                if key == "limit":
                    try:
                        payload[key] = int(value)
                    except ValueError:
                        payload[key] = value
                else:
                    payload[key] = value

        return payload

    def _parse_request(self, raw):
        command = (raw or "").strip()
        if not command:
            raise ValueError("Empty command")

        if command.startswith("{"):
            return json.loads(command)

        return self._parse_compact_command(command)

    def _publish_payload(self, payload):
        self.service.result_characteristic.set_payload(payload)
        self.service.status_characteristic.bump()

    def process_command_fragment(self, fragment, options):
        client_key = self._client_key(options)
        current_buffer = self._command_buffers.get(client_key, "")
        merged_buffer = current_buffer + (fragment or "")

        if len(merged_buffer.encode("utf-8")) > MAX_COMMAND_BUFFER_BYTES:
            self._command_buffers.pop(client_key, None)
            self._publish_payload(
                {
                    "ok": False,
                    "error": "Command payload too large",
                    "max_bytes": MAX_COMMAND_BUFFER_BYTES,
                }
            )
            return

        commands, remainder = self._extract_complete_commands(merged_buffer)
        self._command_buffers[client_key] = remainder

        for command in commands:
            self.process_command(command)

    def process_command(self, raw):
        try:
            request = self._parse_request(raw)
        except json.JSONDecodeError:
            payload = {
                "ok": False,
                "error": "Invalid JSON",
                "hint": "Write one JSON object (optionally chunked) or compact action like scan_wifi",
            }
        except ValueError as exc:
            payload = {"ok": False, "error": str(exc)}
        else:
            action = request.get("action")
            if not action:
                payload = {"ok": False, "error": "Missing action"}
            else:
                try:
                    payload = self.processor.handle_action(action, request)
                except Exception as exc:
                    payload = {"ok": False, "action": action, "error": str(exc)}

        self._publish_payload(payload)

    def start(self):
        if self.auto_configure_adapter:
            config = self._configure_adapter()
            if config.get("ok"):
                print(f"Bluetooth alias set to: {self.device_name}")
            else:
                print(f"Bluetooth setup warning: {config.get('error')}")

        dbus.mainloop.glib.DBusGMainLoop(set_as_default=True)
        self.bus = dbus.SystemBus()
        self.adapter_path = self._find_adapter()

        self.app = Application(self.bus)
        self.service = ProvisioningGattService(self.bus, 0, self)
        self.app.add_service(self.service)
        self.advertisement = Advertisement(
            self.bus,
            0,
            local_name=self.device_name,
            service_uuids=[PROVISIONING_SERVICE_UUID],
        )

        self.mainloop = GLib.MainLoop()
        self._startup_complete = False
        self._startup_error = None
        self._startup_timeout_id = GLib.timeout_add_seconds(35, self._on_startup_timeout)
        self._register_app()

        try:
            self.mainloop.run()
        except KeyboardInterrupt:
            print("\nStopping BLE provisioning server...")
        finally:
            if self._startup_timeout_id is not None:
                GLib.source_remove(self._startup_timeout_id)
                self._startup_timeout_id = None
            self.stop()

        if self._startup_error is not None:
            raise self._startup_error

    def stop(self):
        if self.mainloop is not None and self.mainloop.is_running():
            self.mainloop.quit()
