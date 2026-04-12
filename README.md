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

Pi4 hỗ trợ nhận cấu hình Wi-Fi từ app Flutter qua Bluetooth RFCOMM:

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

3. App Flutter kết nối Bluetooth socket (RFCOMM channel mặc định `4`) và gửi mỗi lệnh dạng 1 JSON trên 1 dòng (`\n` ở cuối).

### Các action hỗ trợ

- `{"action":"ping"}`
- `{"action":"scan_wifi"}`
- `{"action":"wifi_status"}`
- `{"action":"connect_wifi","ssid":"TenWifi","password":"MatKhau"}`

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

Biến môi trường:

- `BT_CHANNEL` (mặc định `4`)
- `WIFI_INTERFACE` (mặc định `wlan0`)
- `BT_DEVICE_NAME` (mặc định `khanhpi`)
- `BT_AUTO_SETUP` (mặc định `true`)

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

