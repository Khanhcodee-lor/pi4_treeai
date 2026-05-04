import time
from pathlib import Path

try:
    import board
    import busio
    from PIL import Image, ImageDraw, ImageFont
    import adafruit_ssd1306
    OLED_AVAILABLE = True
except ImportError:
    OLED_AVAILABLE = False


class OledStatusDisplay:
    """Minimal OLED status renderer for current Wi-Fi and ESP32 BLE state."""

    def __init__(
        self,
        enabled=True,
        width=128,
        height=64,
        i2c_address=0x3C,
        rotate=0,
        update_interval=2.0,
    ):
        self.enabled = bool(enabled) and OLED_AVAILABLE
        self.width = int(width)
        self.height = int(height)
        self.i2c_address = int(i2c_address)
        self.rotate = int(rotate)
        self.update_interval = max(0.5, float(update_interval))

        self._display = None
        self._font = None
        self._last_update_at = 0.0

        if not self.enabled:
            if bool(enabled) and not OLED_AVAILABLE:
                print("OLED warning: dependencies not installed")
            return

        try:
            self._init_display()
        except Exception as exc:
            print(f"OLED warning: init failed: {exc}")
            self.enabled = False

    def _init_display(self):
        i2c = busio.I2C(board.SCL, board.SDA)
        self._display = adafruit_ssd1306.SSD1306_I2C(
            self.width,
            self.height,
            i2c,
            addr=self.i2c_address,
        )
        try:
            self._display.contrast(255)
        except Exception:
            pass
        self._display.fill(0)
        self._display.show()
        self._font = self._load_font()
        self._show_boot_splash()

    def _load_font(self):
        font_candidates = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        ]

        for font_path in font_candidates:
            if Path(font_path).exists():
                try:
                    return ImageFont.truetype(font_path, 9)
                except Exception:
                    pass

        return ImageFont.load_default()

    def _show_boot_splash(self):
        image = Image.new("1", (self.width, self.height))
        draw = ImageDraw.Draw(image)

        draw.text((0, 0), "OLED OK", font=self._font, fill=255)
        draw.text((0, 18), "Pi4 Gateway", font=self._font, fill=255)
        draw.text((0, 36), "Starting...", font=self._font, fill=255)

        self._display.image(image)
        self._display.show()

    def update_if_due(self, wifi_ssid, wifi_ip, ble_connected):
        if not self.enabled:
            return

        now = time.time()
        if now - self._last_update_at < self.update_interval:
            return

        self._last_update_at = now
        self.update(wifi_ssid, wifi_ip, ble_connected)

    def update(self, wifi_ssid, wifi_ip, ble_connected):
        if not self.enabled:
            return

        image = Image.new("1", (self.width, self.height))
        draw = ImageDraw.Draw(image)

        lines = [
            f"WiFi:{self._trim(wifi_ssid, 11)}",
            f"IP:{self._trim(wifi_ip, 15)}",
            f"BLE:{self._bool_text(ble_connected, 'ESP32 ON', 'ESP32 OFF')}",
        ]

        line_height = 18
        y = 0
        for line in lines:
            draw.text((0, y), line, font=self._font, fill=255)
            y += line_height

        if self.rotate in (90, 180, 270):
            image = image.rotate(self.rotate)

        self._display.image(image)
        self._display.show()

    def _bool_text(self, value, true_text, false_text):
        if value is None:
            return "-"
        return true_text if value else false_text

    def _trim(self, value, max_len=16):
        text = (value or "-").strip()
        if len(text) <= max_len:
            return text
        return text[: max_len - 1] + "~"
