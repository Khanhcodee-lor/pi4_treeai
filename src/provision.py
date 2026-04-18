import os

from src.services.ble_provisioning import BLEProvisioningServer
from src.services.bluetooth_provisioning import BluetoothProvisioningServer


def main():
    bt_transport = os.getenv("BT_TRANSPORT", "ble").strip().lower()
    bt_channel = int(os.getenv("BT_CHANNEL", "4"))
    wifi_interface = os.getenv("WIFI_INTERFACE", "wlan0")
    bt_device_name = os.getenv("BT_DEVICE_NAME", "khanhpi")
    bt_auto_setup = os.getenv("BT_AUTO_SETUP", "true").lower() in ("1", "true", "yes")
    bt_scan_limit = int(os.getenv("BT_SCAN_LIMIT", "12"))

    if bt_transport == "rfcomm":
        server = BluetoothProvisioningServer(
            channel=bt_channel,
            interface=wifi_interface,
            device_name=bt_device_name,
            auto_configure_adapter=bt_auto_setup,
            scan_limit=bt_scan_limit,
        )
    elif bt_transport == "ble":
        server = BLEProvisioningServer(
            interface=wifi_interface,
            device_name=bt_device_name,
            auto_configure_adapter=bt_auto_setup,
            scan_limit=bt_scan_limit,
        )
    else:
        raise RuntimeError(f"Unsupported BT_TRANSPORT: {bt_transport}")

    server.start()


if __name__ == "__main__":
    main()
