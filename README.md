# 🌱 Smart Garden IoT System

## 📌 Giới thiệu
**Smart Garden IoT System** là dự án khu vườn thông minh sử dụng **Raspberry Pi làm gateway trung tâm**, kết hợp với các **node ESP32** để giám sát môi trường, tưới tiêu tự động và **nhận diện sâu bệnh bằng camera**.  
Hệ thống cho phép thu thập dữ liệu nhiệt độ, độ ẩm, độ ẩm đất và gửi dữ liệu lên **Firebase** để theo dõi từ xa.

---

## 🎯 Mục tiêu dự án
- Xây dựng hệ thống IoT theo mô hình **Gateway – Node**
- Ứng dụng **Embedded Software + IoT + AI** vào nông nghiệp
- Giám sát môi trường và tưới tiêu tự động
- Nhận diện sâu bệnh nhằm hỗ trợ chăm sóc cây trồng

---

## 🏗️ Kiến trúc hệ thống

ESP32 Nodes (Sensors + Pump)
|
| MQTT / HTTP
v
Raspberry Pi (Gateway + AI Processing)
|
| Firebase
v
App Mobile


- **ESP32**: Thu thập dữ liệu cảm biến, điều khiển bơm tưới
- **Raspberry Pi**: Gateway trung tâm, xử lý AI, giao tiếp Firebase
- **Firebase**: Lưu trữ và hiển thị dữ liệu realtime

---

## 🔧 Chức năng chính

### 🌡️ Giám sát môi trường
- Đọc nhiệt độ và độ ẩm không khí
- Đọc độ ẩm đất
- Gửi dữ liệu realtime lên Firebase

### 🚿 Tưới tiêu tự động
- Điều khiển bơm nước thông qua relay
- Tưới theo ngưỡng độ ẩm đất
- Có thể mở rộng điều khiển thủ công từ xa

### 📷 Nhận diện sâu bệnh
- Sử dụng camera gắn trên Raspberry Pi
- Nhận diện sâu bệnh bằng mô hình AI (`best.pt`)
- Hỗ trợ cảnh báo sớm

---

## 🛠️ Công nghệ sử dụng

### Phần cứng
- Raspberry Pi 4
- ESP32
- Camera Raspberry Pi
- Relay, bơm nước
- Cảm biến nhiệt độ, độ ẩm, độ ẩm đất

### Phần mềm
- **Ngôn ngữ:** C/C++, Python
- **Giao thức:** MQTT, HTTP
- **Cloud:** Firebase
- **AI:** PyTorch / YOLO
- **Công cụ:** PlatformIO, Arduino IDE, Git/GitHub

---

## 🚀 Cách triển khai

1. Nạp firmware cho ESP32 bằng PlatformIO  
2. Kết nối ESP32 với Raspberry Pi qua MQTT
3. Cài đặt môi trường Python trên Raspberry Pi  
4. Chạy service gateway và AI detection  
5. Kết nối Firebase để giám sát dữ liệu  

---

## 📶 Bluetooth Wi-Fi Provisioning (Pi4)

Pi4 hỗ trợ nhận cấu hình Wi-Fi từ app Flutter qua Bluetooth. Mặc định repo hiện chạy theo **BLE GATT**; nếu cần tương thích cũ vẫn có thể chuyển về **Bluetooth Classic RFCOMM** bằng `BT_TRANSPORT=rfcomm`.

1. Bật Bluetooth ở chế độ discoverable/pairable:

```bash
sudo bluetoothctl <<EOF
power on
discoverable on
pairable on
agent on
default-agent
EOF
```

2. Chạy provisioning server:

```bash
./run_bt_provision.sh
```

### Chế độ BLE GATT mặc định

App Flutter kết nối tới thiết bị BLE có tên `khanhpi` rồi dùng 1 service custom:

- Service UUID: `0f5c0001-95c7-43f1-b1d5-28f9f0dca001`
- Command characteristic UUID: `0f5c0002-95c7-43f1-b1d5-28f9f0dca001`
- Result characteristic UUID: `0f5c0003-95c7-43f1-b1d5-28f9f0dca001`
- Status characteristic UUID: `0f5c0004-95c7-43f1-b1d5-28f9f0dca001`

Flow phía app:

1. Subscribe `status characteristic`
2. Ghi command vào `command characteristic`:
	- Nên ưu tiên `write with response`.
	- Nếu dùng `write without response`, payload mỗi packet phải nhỏ (thường <= 20 bytes khi MTU mặc định).
	- Với JSON dài, có thể chia nhỏ thành nhiều packet và kết thúc bằng `\n`.
3. Khi `status characteristic` notify số mới, app đọc `result characteristic`
4. Parse JSON response và hiển thị danh sách Wi-Fi hoặc trạng thái connect

Ví dụ command để lấy danh sách Wi-Fi:

```json
{"action":"scan_wifi","limit":12}
```

Ví dụ compact command (gọn, phù hợp packet nhỏ):

```text
scan_wifi?limit=12
```

Ví dụ command để Pi kết nối Wi-Fi:

```json
{"action":"connect_wifi","ssid":"TenWifi","password":"MatKhau"}
```

Lưu ý kết quả `scan_wifi` qua BLE có thể được cắt gọn để vừa payload GATT an toàn; khi đó response có các field như `truncated`, `total_networks`, `message`.

### Chế độ tương thích RFCOMM

Nếu app của bạn vẫn đang dùng Bluetooth socket, đặt:

```bash
export BT_TRANSPORT=rfcomm
```

Khi đó app Flutter kết nối Bluetooth socket (RFCOMM channel mặc định `4`) và gửi mỗi lệnh dạng 1 JSON trên 1 dòng (`\n` ở cuối).

### Các action hỗ trợ

- `{"action":"ping"}`
- `{"action":"scan_wifi"}`
- `{"action":"wifi_status"}`
- `{"action":"connect_wifi","ssid":"TenWifi","password":"MatKhau"}`
- `{"action":"device_status"}`

Ví dụ phản hồi thành công khi connect:

```json
{
	"ok": true,
	"action": "connect_wifi",
	"ssid": "TenWifi",
	"message": "Device 'wlan0' successfully activated...",
	"status": {
		"interface": "wlan0",
		"state": "connected",
		"connection": "TenWifi",
		"ip": "192.168.1.50"
	}
}
```

Ví dụ phản hồi khi kiểm tra trạng thái thiết bị:

```json
{
	"ok": true,
	"action": "device_status",
	"hostname": "khanhpi",
	"ips": ["192.168.1.50"],
	"wifi": {
		"interface": "wlan0",
		"state": "connected",
		"connection": "TenWifi",
		"ip": "192.168.1.50"
	},
	"ssh": {
		"service": "ssh",
		"active": true,
		"enabled": true,
		"listening": true,
		"error": null
	}
}
```

Biến môi trường:

- `BT_CHANNEL` (mặc định `4`)
- `BT_TRANSPORT` (`ble` hoặc `rfcomm`, mặc định `ble`)
- `WIFI_INTERFACE` (mặc định `wlan0`)
- `BT_DEVICE_NAME` (mặc định `khanhpi`)
- `BT_AUTO_SETUP` (mặc định `true`)
- `BT_SCAN_LIMIT` (mặc định `12`)

### Tự chạy khi Pi4 vừa cấp nguồn

Để Pi4 tự bật Bluetooth provisioning mỗi lần cắm nguồn:

```bash
chmod +x setup_bt_autostart.sh
./setup_bt_autostart.sh
```

Service sẽ:

- Bật `bluetooth.service`
- Tự chạy `run_bt_provision.sh` khi boot
- Đặt Bluetooth alias là `khanhpi`, bật discoverable + pairable

Kiểm tra lại:

```bash
sudo systemctl status pi4-bt-provision.service
```

---

## 📈 Hướng phát triển
- Xây dựng dashboard web/mobile
- Mở rộng nhiều node ESP32
- Thêm hệ thống cảnh báo (email / notification)
- Tối ưu mô hình AI nhận diện sâu bệnh

---

## 👤 Tác giả
- **Khánh Nguyễn**
- Sinh viên Điện tử – Viễn thông
- Định hướng: Embedded Software / IoT Developer

