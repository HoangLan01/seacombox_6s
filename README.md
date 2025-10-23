# SeaComBox 6S — Hệ thống giám sát tàu cá

Dự án triển khai thiết bị giám sát tàu cá trên biển sử dụng Raspberry Pi Pico (RP2040) và lập trình bằng CircuitPython. Thiết bị thu thập vị trí, trạng thái, và truyền dữ liệu về máy chủ phục vụ quản lý, an toàn và tuân thủ quy định.

Tác giả: OSB Holding JSC (`__author__ = 'osb holding jsc'`)

## Mục tiêu
- Thu thập vị trí GPS, tốc độ, hướng di chuyển, thời gian thực.
- Gửi dữ liệu lên máy chủ qua GSM/LTE/LoRa/VSAT (tùy cấu hình).
- Lưu trữ cục bộ khi mất kết nối và đồng bộ lại khi có mạng.
- Vận hành ổn định, tiêu thụ điện thấp, chịu môi trường biển khắc nghiệt.

## Kiến trúc tổng quan
- Vi điều khiển: Raspberry Pi Pico (RP2040) chạy CircuitPython.
- Cảm biến/Module: GPS GNSS, mô-đun truyền thông (GSM/LTE/LoRa), cảm biến nguồn (VIN, pin), cảm biến môi trường (tuỳ chọn).
- Phần mềm: `code.py` điều phối vòng lặp chính; thư viện đặt trong `lib/`.
- Máy chủ: API nhận dữ liệu (REST/MQTT), lưu trữ và hiển thị.

## Phần cứng tham khảo
- Raspberry Pi Pico hoặc Pico W (nếu cần Wi‑Fi).
- Mô-đun GNSS (ví dụ: u-blox NEO-M8N) giao tiếp UART/I2C.
- Mô-đun truyền thông: SIM800/Quectel EC25 (UART/USB) hoặc LoRa SX127x.
- Nguồn: DC 12–24V (tàu), mạch hạ áp sang 5V, pin dự phòng.
- Vỏ chống nước IP67, ăng-ten GPS/cellular ngoài, cầu chì/bảo vệ quá áp.

## Yêu cầu phần mềm
- CircuitPython (phiên bản phù hợp RP2040).
- Thư viện CircuitPython của Adafruit cho GPS, UART, I2C, mạng.
- Trình soạn thảo/IDE và driver USB (Windows/macOS/Linux).

## Cài đặt nhanh
1. Cài CircuitPython cho Pico:
   - Nhấn giữ BOOTSEL, cắm USB để Pico vào chế độ USB Mass Storage.
   - Tải tệp UF2 CircuitPython cho RP2040 từ trang Adafruit.
   - Chép UF2 vào ổ `RPI-RP2`; thiết bị sẽ xuất hiện ổ `CIRCUITPY`.
2. Chuẩn bị mã nguồn:
   - Tạo thư mục `lib/` trên `CIRCUITPY` và thêm các thư viện cần thiết.
   - Sao chép `code.py` vào gốc ổ `CIRCUITPY`.
3. Cấu hình (tuỳ chọn):
   - Tạo `settings.toml` với các khoá như `SERVER_URL`, `APN`, `DEVICE_ID`.
   - Kiểm tra chân UART/I2C trùng với đấu nối phần cứng.

## Vận hành
- Thiết bị sẽ tự chạy `code.py` khi cấp nguồn.
- Đèn báo trạng thái: 
  - Xanh: GPS khoá vị trí.
  - Vàng: Đang truyền/đồng bộ.
  - Đỏ: Lỗi kết nối hoặc cảm biến.
- Dữ liệu được đẩy theo chu kỳ (ví dụ 30–60 giây) hoặc sự kiện (rời/cập bến).

## Cấu trúc firmware đề xuất
- `code.py`: vòng lặp chính, đọc GPS, gom gói dữ liệu, gửi về server, xử lý lỗi.
- `lib/`: thư viện CircuitPython (UART, HTTP/MQTT, GNSS parser, retry/backoff).
- `settings.toml`: thông số triển khai, chu kỳ gửi, ngưỡng pin, server.
- `log.txt`: (tuỳ chọn) ghi nhật ký để chẩn đoán.

## Giao thức trao đổi dữ liệu
- HTTP(S) REST: `POST /telemetry` với JSON `{device_id, ts, lat, lon, speed, heading, status}`.
- MQTT: chủ đề `vessel/{device_id}/telemetry` với payload JSON như trên.
- Hỗ trợ nén/gom lô (batch) khi kết nối yếu.

## Thiết kế độ tin cậy
- Bộ đệm cục bộ khi mất mạng; đồng bộ lại theo FIFO.
- Watchdog và tự khởi động lại khi lỗi treo.
- Kiểm soát nguồn, tiết kiệm năng lượng, chu kỳ ngủ/thức.
- Kiểm tra tính hợp lệ GPS (HDOP, số vệ tinh, tuổi dữ liệu).

## Kiểm thử
- Mô phỏng GPS bằng dữ liệu NMEA ghi sẵn.
- Thử nghiệm mất kết nối mạng, đánh giá khả năng phục hồi.
- Kiểm tra tiêu thụ điện và nhiệt độ trong môi trường thực tế.

## Lộ trình phát triển
- Thêm hỗ trợ nhiều mô-đun truyền thông, tự động chuyển mạng.
- Mã hoá/chuẩn hoá payload, ký số chống giả mạo.
- OTA cập nhật firmware (nếu phần cứng cho phép).
- Bảng điều khiển trực quan và cảnh báo thời gian thực.

## Ghi chú pháp lý
- Tuân thủ quy định giám sát tàu cá của cơ quan quản lý.
- Bảo vệ dữ liệu cá nhân và quyền riêng tư thuyền viên.

## Liên hệ
- Doanh nghiệp: OSB Holding JSC
- Hỗ trợ kỹ thuật: vui lòng liên hệ bộ phận R&D.

## Ví dụ payload JSON

- REST đơn lẻ (`POST /telemetry`):
```
{
  "device_id": "PICO-SEA-0001",
  "ts": "2025-01-15T08:42:31Z",
  "lat": 16.0678,
  "lon": 108.2140,
  "speed": 8.2,
  "heading": 132.0,
  "hdop": 0.9,
  "sats": 12,
  "status": "ok",
  "battery": 3.95,
  "seq": 12345,
  "firmware": "seacombox-6s@0.1.0"
}
```
- REST gom lô (batch):
```
{
  "device_id": "PICO-SEA-0001",
  "batch": [
    { "ts": "2025-01-15T08:42:31Z", "lat": 16.0678, "lon": 108.2140, "speed": 8.2, "heading": 132.0, "hdop": 0.9, "sats": 12, "status": "ok", "battery": 3.95, "seq": 12345 },
    { "ts": "2025-01-15T08:43:31Z", "lat": 16.0681, "lon": 108.2149, "speed": 8.5, "heading": 130.0, "hdop": 1.1, "sats": 11, "status": "ok", "battery": 3.94, "seq": 12346 }
  ]
}
```
- MQTT: chủ đề `vessel/PICO-SEA-0001/telemetry`, payload giống REST đơn lẻ.
- Header REST mẫu:
```
POST https://api.example.com/telemetry
Authorization: Bearer <SERVER_TOKEN>
Content-Type: application/json
```

## settings.toml mẫu
```
# Thiết lập máy chủ
SERVER_URL = "https://api.example.com/telemetry"
SERVER_TOKEN = "replace-with-your-token"

# Lựa chọn giao thức
USE_MQTT = false
MQTT_BROKER = "mqtt.example.com"
MQTT_PORT = 8883
MQTT_USERNAME = "user"
MQTT_PASSWORD = "pass"
MQTT_TOPIC = "vessel/{device_id}/telemetry"
MQTT_TLS = true

# Thông tin thiết bị
DEVICE_ID = "PICO-SEA-0001"
SEND_INTERVAL_S = 60
BATCH_MAX = 20
RETRY_BACKOFF_S = 30

# GPS (UART/I2C tuỳ module)
GPS_UART_TX = "GP4"
GPS_UART_RX = "GP5"
GPS_BAUDRATE = 9600
GPS_MIN_HDOP = 2.0
GPS_MIN_SATS = 4

# Modem (GSM/LTE)
MODEM_UART_TX = "GP8"
MODEM_UART_RX = "GP9"
MODEM_BAUDRATE = 115200
APN = "internet"
APN_USER = ""
APN_PASS = ""

# Nguồn & nhật ký
LOW_BATTERY_V = 3.6
ENABLE_LOG = true

# Geofence polygon (chuỗi "lat,lon;lat,lon;...")
# Ví dụ: khu vực quanh toạ độ Đà Nẵng
GEOFENCE_POLYGON = "16.0600,108.2000;16.0600,108.2300;16.0750,108.2300;16.0750,108.2000"

# Tuỳ chọn kiểm thử nhanh
TEST_LAT = "16.0678"
TEST_LON = "108.2140"
```
Gợi ý: Đọc cấu hình bằng `os.getenv()` (nếu firmware hỗ trợ `settings.toml`), hoặc dùng chuỗi `GEOFENCE_POLYGON` dạng "lat,lon;lat,lon;..." để parse.

### Kiểm tra vùng biên (ray casting)
- Mã nguồn trong `code.py` cung cấp hàm `point_in_polygon()` và `is_outside_geofence()`.
- Đặt `GEOFENCE_POLYGON` trong `settings.toml`, tuỳ chọn `TEST_LAT`, `TEST_LON` để chạy kiểm thử nhanh (in ra kết quả khi chạy `code.py`).
- Thuật toán ray casting xử lý cả trường hợp điểm nằm trên cạnh (coi là bên trong).
---
Tài liệu này mô tả định hướng và cách triển khai mẫu. Tuỳ biến theo phần cứng và yêu cầu thực tế của từng tàu/đội tàu.