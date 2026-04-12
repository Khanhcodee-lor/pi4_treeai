import os

from src.services.bluetooth_provisioning import BluetoothProvisioningServer


def main():
    bt_channel = int(os.getenv("BT_CHANNEL", "4"))
    wifi_interface = os.getenv("WIFI_INTERFACE", "wlan0")

    server = BluetoothProvisioningServer(channel=bt_channel, interface=wifi_interface)
    server.start()


if __name__ == "__main__":
    main()