import os

from src.services.bluetooth_provisioning import BluetoothProvisioningServer


def main():
    bt_channel = int(os.getenv("BT_CHANNEL", "4"))
    wifi_interface = os.getenv("WIFI_INTERFACE", "wlan0")
    bt_device_name = os.getenv("BT_DEVICE_NAME", "khanhpi")
    bt_auto_setup = os.getenv("BT_AUTO_SETUP", "true").lower() in ("1", "true", "yes")

    server = BluetoothProvisioningServer(
        channel=bt_channel,
        interface=wifi_interface,
        device_name=bt_device_name,
        auto_configure_adapter=bt_auto_setup,
    )
    server.start()


if __name__ == "__main__":
    main()