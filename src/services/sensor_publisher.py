import json
import time
from datetime import datetime

import firebase_admin
from firebase_admin import db

try:
    import serial
except ImportError:
    serial = None

try:
    import RPi.GPIO as GPIO
except ImportError:
    GPIO = None

try:
    import Adafruit_DHT
except ImportError:
    Adafruit_DHT = None

try:
    import adafruit_dht
    import board
except ImportError:
    adafruit_dht = None
    board = None


class SensorPublisher:
    """Publish sensor data to Firebase from local GPIO or UART frames."""

    def __init__(
        self,
        db_url,
        device_id,
        path_template="plant/{device_id}/sensor",
        enabled=True,
        publish_interval=15.0,
        sensor_source="local",
        uart_serial_port="/dev/serial0",
        uart_baudrate=115200,
        uart_serial_timeout=0.05,
        uart_stale_after=30.0,
        uart_error_streak_threshold=2,
        zigbee_serial_port=None,
        zigbee_baudrate=None,
        zigbee_serial_timeout=None,
        zigbee_stale_after=None,
        zigbee_error_streak_threshold=None,
        soil_gpio=17,
        soil_active_low=True,
        soil_pull="up",
        soil_sample_count=15,
        soil_sample_delay=0.02,
        dht_gpio=4,
        dht_sensor_type="DHT11",
        dht_read_retries=5,
        dht_min_read_interval=2.0,
        dht_error_streak_threshold=2,
    ):
        self.db_url = (db_url or "").rstrip("/")
        self.device_id = device_id
        self.path = (
            (path_template or "plant/{device_id}/sensor")
            .format(device_id=device_id)
            .strip("/")
        )
        self.enabled = bool(enabled)
        self.publish_interval = max(1.0, float(publish_interval))

        self.sensor_source = (sensor_source or "local").strip().lower()
        if self.sensor_source in ("zigbee_uart", "zigbee"):
            self.sensor_source = "uart"
        if self.sensor_source not in ("local", "uart"):
            print(f"Sensor warning: unknown source '{self.sensor_source}', fallback to local")
            self.sensor_source = "local"

        self.uart_serial_port = zigbee_serial_port or uart_serial_port or "/dev/serial0"
        self.uart_baudrate = int(
            zigbee_baudrate if zigbee_baudrate is not None else uart_baudrate
        )
        self.uart_serial_timeout = max(
            0.01,
            float(
                zigbee_serial_timeout
                if zigbee_serial_timeout is not None
                else uart_serial_timeout
            ),
        )
        self.uart_stale_after = max(
            1.0,
            float(zigbee_stale_after if zigbee_stale_after is not None else uart_stale_after),
        )
        self.uart_error_streak_threshold = max(
            1,
            int(
                zigbee_error_streak_threshold
                if zigbee_error_streak_threshold is not None
                else uart_error_streak_threshold
            ),
        )

        self.soil_gpio = int(soil_gpio)
        self.soil_active_low = bool(soil_active_low)
        self.soil_pull = (soil_pull or "up").strip().lower()
        self.soil_sample_count = max(1, int(soil_sample_count))
        self.soil_sample_delay = max(0.0, float(soil_sample_delay))

        self.dht_gpio = int(dht_gpio)
        self.dht_sensor_type = (dht_sensor_type or "DHT11").strip().upper()
        self.dht_read_retries = max(1, int(dht_read_retries))
        self.dht_min_read_interval = max(2.0, float(dht_min_read_interval))
        self.dht_error_streak_threshold = max(1, int(dht_error_streak_threshold))

        self._last_publish = 0.0
        self._ref = None

        self._serial = None
        self._last_remote_received_at = 0.0
        self._uart_fail_streak = 0
        self._last_remote_soil = {}
        self._last_remote_air = {}
        self._last_remote_meta = {}

        self._gpio_ready = False
        self._dht_backend = None
        self._dht_device = None
        self._dht_sensor = None
        self._last_dht_read_at = 0.0
        self._last_good_humidity = None
        self._last_good_temperature_c = None
        self._dht_fail_streak = 0
        self._last_soil_raw = None

        if not self.enabled:
            print("Sensor publisher disabled by configuration")
            return

        self._setup_firebase()
        self._setup_sensor_backends()

        print(f"Sensor publisher enabled: every {self.publish_interval:.0f}s")
        print(f"  Path: {self.path}")
        print(f"  Source: {self.sensor_source}")

        if self.sensor_source == "uart":
            print(
                f"  UART: port={self.uart_serial_port}, "
                f"baud={self.uart_baudrate}, timeout={self.uart_serial_timeout:.2f}s"
            )
            print(
                f"  UART policy: stale_after={self.uart_stale_after:.1f}s, "
                f"error_after={self.uart_error_streak_threshold} consecutive fails"
            )
        else:
            print(f"  Soil DO: GPIO{self.soil_gpio} (active_low={self.soil_active_low})")
            print(
                f"  Soil read policy: pull={self.soil_pull}, "
                f"samples={self.soil_sample_count}, delay={self.soil_sample_delay:.3f}s"
            )
            print(
                f"  DHT: {self.dht_sensor_type} on GPIO{self.dht_gpio} "
                f"(backend={self._dht_backend or 'disabled'})"
            )
            print(
                f"  DHT read policy: retries={self.dht_read_retries}, "
                f"min_interval={self.dht_min_read_interval:.1f}s, "
                f"error_after={self.dht_error_streak_threshold} consecutive fails"
            )

    def _setup_firebase(self):
        try:
            try:
                firebase_admin.get_app()
            except ValueError:
                firebase_admin.initialize_app(options={"databaseURL": self.db_url})

            self._ref = db.reference(self.path)
        except Exception as exc:
            print(f"Sensor publisher disabled (Firebase init error): {exc}")
            self.enabled = False

    def _setup_sensor_backends(self):
        if not self.enabled:
            return

        if self.sensor_source == "uart":
            self._setup_uart_backend()
            return

        self._setup_local_sensor_backends()

    def _setup_uart_backend(self):
        if serial is None:
            print("Sensor warning: pyserial not installed, uart source unavailable")
            return

        try:
            self._serial = serial.Serial(
                port=self.uart_serial_port,
                baudrate=self.uart_baudrate,
                timeout=self.uart_serial_timeout,
            )
            try:
                self._serial.reset_input_buffer()
            except Exception:
                pass
        except Exception as exc:
            self._serial = None
            print(f"Sensor warning: failed to open uart serial {self.uart_serial_port}: {exc}")

    def _setup_local_sensor_backends(self):
        if GPIO is None:
            print("Sensor warning: RPi.GPIO not available, soil DO reading disabled")
        else:
            try:
                pull_map = {
                    "up": GPIO.PUD_UP,
                    "down": GPIO.PUD_DOWN,
                    "off": GPIO.PUD_OFF,
                    "none": GPIO.PUD_OFF,
                }
                pull_cfg = pull_map.get(self.soil_pull)
                if pull_cfg is None:
                    print(
                        f"Sensor warning: unsupported soil pull '{self.soil_pull}', "
                        "fallback to 'up'"
                    )
                    pull_cfg = GPIO.PUD_UP

                GPIO.setmode(GPIO.BCM)
                GPIO.setup(self.soil_gpio, GPIO.IN, pull_up_down=pull_cfg)
                self._gpio_ready = True
            except Exception as exc:
                print(f"Sensor warning: failed to init soil GPIO{self.soil_gpio}: {exc}")

        if adafruit_dht is not None and board is not None:
            self._dht_device = self._build_circuitpython_dht_device()
            if self._dht_device is not None:
                self._dht_backend = "circuitpython"

        if self._dht_backend is None and Adafruit_DHT is not None:
            self._dht_sensor = self._resolve_dht_type(self.dht_sensor_type)
            if self._dht_sensor is None:
                print(
                    f"Sensor warning: unsupported DHT type '{self.dht_sensor_type}', "
                    "expected DHT11 or DHT22"
                )
            else:
                self._dht_backend = "adafruit_legacy"

        if self._dht_backend is None:
            print("Sensor warning: no supported DHT backend available, DHT reading disabled")

    def _build_circuitpython_dht_device(self):
        board_pin = getattr(board, f"D{self.dht_gpio}", None)
        if board_pin is None:
            print(f"Sensor warning: board pin D{self.dht_gpio} not available for DHT")
            return None

        try:
            if self.dht_sensor_type == "DHT11":
                return adafruit_dht.DHT11(board_pin, use_pulseio=False)
            if self.dht_sensor_type in ("DHT22", "AM2302"):
                return adafruit_dht.DHT22(board_pin, use_pulseio=False)

            print(
                f"Sensor warning: unsupported DHT type '{self.dht_sensor_type}' "
                "for circuitpython backend"
            )
            return None
        except Exception as exc:
            print(f"Sensor warning: failed to init circuitpython DHT backend: {exc}")
            return None

    def _resolve_dht_type(self, sensor_type):
        mapping = {
            "DHT11": getattr(Adafruit_DHT, "DHT11", None),
            "DHT22": getattr(Adafruit_DHT, "DHT22", None),
            "AM2302": getattr(Adafruit_DHT, "AM2302", None),
        }
        return mapping.get(sensor_type)

    def publish_if_due(self):
        if not self.enabled:
            return

        now = time.time()
        if now - self._last_publish < self.publish_interval:
            return

        self._last_publish = now
        self.publish_once()

    def publish_once(self):
        if not self.enabled or self._ref is None:
            return

        now = time.time()
        now_iso = datetime.now().isoformat(timespec="seconds")

        if self.sensor_source == "uart":
            payload = self._build_remote_payload(now=now, now_iso=now_iso)
        else:
            payload = self._build_local_payload(now=now, now_iso=now_iso)

        try:
            self._ref.update(payload)
        except Exception as exc:
            print(f"Sensor publisher write error: {exc}")

    def _build_remote_payload(self, now, now_iso):
        errors = []

        frame, read_error = self._read_latest_uart_frame()
        if frame is not None:
            soil_part, air_part, meta_part = self._normalize_remote_payload(frame)
            if soil_part:
                self._last_remote_soil.update(soil_part)
            if air_part:
                self._last_remote_air.update(air_part)
            if meta_part:
                self._last_remote_meta.update(meta_part)

            self._last_remote_received_at = now
            self._uart_fail_streak = 0
        else:
            self._uart_fail_streak += 1
            if read_error is None:
                read_error = "uart_no_new_frame"

        age = None
        if self._last_remote_received_at > 0:
            age = round(now - self._last_remote_received_at, 2)
            if age > self.uart_stale_after:
                errors.append(f"uart_stale({age}s)")
        else:
            errors.append("uart_never_received")

        if self._uart_fail_streak >= self.uart_error_streak_threshold and read_error:
            errors.append(
                f"uart_read_failed(streak={self._uart_fail_streak}): {read_error}"
            )

        soil = dict(self._last_remote_soil)
        air = dict(self._last_remote_air)
        meta = dict(self._last_remote_meta)

        if not soil and not air:
            errors.append("uart_payload_empty")

        ok = len(errors) == 0
        return {
            "timestamp": now,
            "updated_at": now_iso,
            "source": "uart",
            "soil": soil,
            "air": air,
            "meta": meta,
            "link": {
                "port": self.uart_serial_port,
                "baudrate": self.uart_baudrate,
                "last_rx_age_s": age,
                "read_fail_streak": self._uart_fail_streak,
            },
            "ok": ok,
            "errors": errors,
        }

    def _read_latest_uart_frame(self):
        if self._serial is None:
            self._setup_uart_backend()
            if self._serial is None:
                return None, "uart_serial_unavailable"

        latest = None
        parse_error = None

        for _ in range(30):
            try:
                raw = self._serial.readline()
            except Exception as exc:
                self._close_uart_serial()
                return None, f"uart_serial_read_failed: {exc}"

            if not raw:
                break

            text = raw.decode("utf-8", errors="ignore").strip()
            if not text:
                continue

            try:
                parsed = json.loads(text)
            except Exception as exc:
                parse_error = f"uart_json_parse_failed: {exc}"
                continue

            if not isinstance(parsed, dict):
                parse_error = "uart_json_not_object"
                continue

            latest = parsed

        return latest, parse_error

    def _normalize_remote_payload(self, payload):
        if not isinstance(payload, dict):
            return {}, {}, {}

        soil = {}
        air = {}
        meta = {}

        if isinstance(payload.get("soil"), dict):
            soil.update(payload["soil"])
        if isinstance(payload.get("air"), dict):
            air.update(payload["air"])
        if isinstance(payload.get("dht"), dict) and not air:
            air.update(payload["dht"])

        for key in (
            "do_raw",
            "is_wet",
            "is_dry",
            "moisture_raw",
            "moisture_percent",
            "adc",
            "adc_raw",
            "sample_ones",
            "sample_zeros",
            "sample_count",
        ):
            if key in payload and key not in soil:
                soil[key] = payload[key]

        for key in (
            "temperature_c",
            "temperature_f",
            "humidity",
            "heat_index_c",
            "heat_index_f",
        ):
            if key in payload and key not in air:
                air[key] = payload[key]

        for key in (
            "node_id",
            "device_id",
            "rssi",
            "lqi",
            "battery",
            "battery_v",
            "fw",
            "seq",
            "remote_ts",
            "updated_at",
            "timestamp",
        ):
            if key in payload:
                meta[key] = payload[key]

        if isinstance(payload.get("errors"), list):
            meta["remote_errors"] = payload.get("errors")

        return soil, air, meta

    def _build_local_payload(self, now, now_iso):
        errors = []

        soil_raw = self._last_soil_raw
        soil_ones = None
        soil_zeros = None
        if self._gpio_ready:
            try:
                soil_raw, soil_ones, soil_zeros = self._read_soil_digital()
            except Exception as exc:
                errors.append(f"soil_gpio_read_failed: {exc}")
        else:
            errors.append("soil_gpio_unavailable")

        if soil_raw in (0, 1):
            self._last_soil_raw = soil_raw

        is_wet = None
        is_dry = None
        if soil_raw in (0, 1):
            wet_raw = 0 if self.soil_active_low else 1
            is_wet = soil_raw == wet_raw
            is_dry = not is_wet

        humidity = self._last_good_humidity
        temperature_c = self._last_good_temperature_c
        if self._dht_backend is not None:
            humidity_raw, temp_raw, dht_error = self._read_dht_with_retry()
            if humidity_raw is not None and temp_raw is not None:
                humidity = round(float(humidity_raw), 2)
                temperature_c = round(float(temp_raw), 2)
                self._last_good_humidity = humidity
                self._last_good_temperature_c = temperature_c
                self._dht_fail_streak = 0
            else:
                self._dht_fail_streak += 1
                if self._dht_fail_streak >= self.dht_error_streak_threshold:
                    reason = dht_error or "empty result"
                    errors.append(
                        f"dht_read_failed(streak={self._dht_fail_streak}): {reason}"
                    )
        else:
            errors.append("dht_unavailable")

        return {
            "timestamp": now,
            "updated_at": now_iso,
            "source": "local",
            "soil": {
                "gpio": self.soil_gpio,
                "do_raw": soil_raw,
                "is_wet": is_wet,
                "is_dry": is_dry,
                "sample_ones": soil_ones,
                "sample_zeros": soil_zeros,
                "sample_count": self.soil_sample_count,
            },
            "air": {
                "sensor": self.dht_sensor_type,
                "gpio": self.dht_gpio,
                "temperature_c": temperature_c,
                "humidity": humidity,
                "read_fail_streak": self._dht_fail_streak,
            },
            "ok": len(errors) == 0,
            "errors": errors,
        }

    def _read_soil_digital(self):
        ones = 0
        zeros = 0

        for i in range(self.soil_sample_count):
            v = int(GPIO.input(self.soil_gpio))
            if v == 1:
                ones += 1
            else:
                zeros += 1

            if i < self.soil_sample_count - 1 and self.soil_sample_delay > 0:
                time.sleep(self.soil_sample_delay)

        if ones == zeros:
            if self._last_soil_raw in (0, 1):
                return self._last_soil_raw, ones, zeros
            return 0, ones, zeros

        raw = 1 if ones > zeros else 0
        return raw, ones, zeros

    def _read_dht_with_retry(self):
        last_error = None

        for _ in range(self.dht_read_retries):
            now = time.time()
            wait_time = self.dht_min_read_interval - (now - self._last_dht_read_at)
            if wait_time > 0:
                time.sleep(wait_time)

            self._last_dht_read_at = time.time()

            try:
                humidity, temperature = self._read_dht_once()
                if humidity is not None and temperature is not None:
                    return humidity, temperature, None
                last_error = "empty result"
            except Exception as exc:
                last_error = str(exc)

        return None, None, last_error

    def _read_dht_once(self):
        if self._dht_backend == "circuitpython":
            return (self._dht_device.humidity, self._dht_device.temperature)

        if self._dht_backend == "adafruit_legacy":
            return Adafruit_DHT.read_retry(
                self._dht_sensor,
                self.dht_gpio,
                retries=2,
                delay_seconds=0.3,
            )

        return (None, None)

    def _close_uart_serial(self):
        if self._serial is None:
            return
        try:
            self._serial.close()
        except Exception:
            pass
        self._serial = None

    def stop(self):
        self._close_uart_serial()

        if self._dht_backend == "circuitpython" and self._dht_device is not None:
            try:
                self._dht_device.exit()
            except Exception:
                pass

        if self._gpio_ready and GPIO is not None:
            try:
                GPIO.cleanup(self.soil_gpio)
            except Exception:
                pass
