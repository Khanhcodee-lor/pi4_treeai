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

