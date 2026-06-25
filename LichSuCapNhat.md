# Lịch Sử Cập Nhật Hệ Thống Supra Phú Thọ

Tài liệu này lưu trữ các thay đổi và cập nhật quan trọng của hệ thống tính toán và ghép tuyến (Cập nhật mới nhất: 25/06/2026).

## 1. Cập nhật ngày 25/06/2026: Nâng Cấp Xuất Excel Theo Form Mẫu & Dọn Dẹp Tiến Trình
- **Nâng cấp Xuất Excel Theo Form Mẫu (`index.html`, `demo.html`):**
  - Chuyển đổi trình lắng nghe sự kiện của nút **Xuất Excel** (`btn-export-planner`) sang chế độ bất đồng bộ (`async`).
  - Sử dụng API `fetch` để tự động tải mẫu gốc `Form Xuất Báo Cáo.xlsb` từ máy chủ cục bộ và dữ liệu booking thô tương ứng với ngày được chọn từ thư mục `Data_Booking`.
  - Xóa toàn bộ các hàng dữ liệu cũ trong sheet `Total` (từ dòng 2 trở đi) để tránh trùng lặp dữ liệu cũ.
  - Sắp xếp và phân tuyến chuyến xe (ưu tiên xe lớn trước, xe nhỏ sau), sắp xếp các siêu thị trong tuyến theo thứ tự bốc xếp (LIFO / khoảng cách xa gần).
  - Điền tự động 32 cột dữ liệu phân tuyến chi tiết theo biểu mẫu:
    - **Mã giờ (Mã chuyến):** Định dạng `DDMMYY` + số thứ tự chuyến (ví dụ: `18062601`).
    - **Tài xế & Biển số xe & SĐT:** Điền đầy đủ thông tin hoặc dùng cấu hình mặc định.
    - **Trọng tải xe & Số điểm giao:** Chỉ hiển thị ở dòng đầu tiên của mỗi tuyến.
    - **Trọng lượng & Thể tích cộng gộp:** Chỉ hiển thị ở dòng đầu tiên của cửa hàng đó, các dòng sau để trống để phù hợp với logic Excel gốc.
    - **Số thứ tự rơi (Chẵn):** Thứ tự giao hàng lũy kế của các điểm giao trên các tuyến.
    - **Đếm dòng (Count):** Gán bằng `1` ở dòng đầu của cửa hàng và `0` ở các dòng sau.
  - Lưu và xuất file dưới định dạng `.xlsb` có bảo toàn macro (`bookVBA: true`).
- **Dọn dẹp tiến trình ẩn và file khóa hệ thống:**
  - Phát hiện và tắt bỏ 16 tiến trình PowerShell/CMD/VBScript chạy trùng lặp gây xung đột khóa tiến trình.
  - Giải phóng file khóa tồn đọng `update_in_progress.lock` để khôi phục hoạt động cho script chạy tự động.
  - Khởi động lại máy chủ cục bộ `local_server.py` và thực hiện đồng bộ thành công dữ liệu với GitHub.

## 2. Cập nhật Thuật toán Ghép Chuyến (trips_logic_v5.js)
- **Cơ chế cũ:** Mọi cửa hàng (Delivery Point) đều bị giới hạn bởi trần xe 1.9 Tấn (1900kg, 14 khối). Nếu một cửa hàng có lượng hàng lớn hơn sức chứa của xe 1.9 Tấn, thuật toán cũ có thể cắt lẻ, bỏ qua hoặc ép vào xe không phù hợp.
- **Cơ chế mới (Ngoại lệ 5 Tấn):** 
  - Hệ thống tự động phát hiện các cửa hàng có lượng hàng vượt quá 1 xe 1.9 Tấn (`weight > 1900` hoặc `volume > 14`).
  - Lập tức nâng trần sức chứa (Truck Limit) của luồng chia đó lên thành **xe 5 Tấn** (`4900kg`, `26 khối`).
  - Cho phép hệ thống **ghép thêm các cửa hàng lân cận** vào chung chuyến 5 Tấn này cho đến khi lấp đầy tải trọng/thể tích của xe 5 Tấn.
- **Sửa lỗi Infinite Loop:** Đã kiểm tra và tối ưu hóa vòng lặp `while` ghép chuyến, đảm bảo thuật toán kết thúc nhanh và không gây đứng trình duyệt.

## 3. Tối ưu Giao diện & Hiệu năng (demo.html)
- **Tối ưu CSS Multi-column:** Sửa lỗi giật lag UI khi hiển thị danh sách dài bằng cách chuyển sang sử dụng CSS Grid (`grid-template-columns`), giúp trình duyệt render mượt mà hơn.
- **Search Debounce:** Áp dụng kỹ thuật `debounce` (độ trễ 300ms) cho thanh tìm kiếm. Giảm thiểu số lần gọi hàm lọc dữ liệu liên tục khi người dùng gõ nhanh, khắc phục triệt để tình trạng treo màn hình.

## 4. Khắc phục Lỗi Xuất Báo Cáo Excel
- **Lỗi cũ:** Cột số `SO` và `DO/GHN` bị thiếu dòng. Khi một siêu thị có nhiều mã SO hoặc DO khác nhau, hệ thống chỉ lấy số lượng theo chiều dài mảng lớn hơn một cách thiếu chính xác, dẫn đến việc mất mát các mã SO/DO ở phần đuôi.
- **Cách khắc phục:** Cập nhật logic `Math.max(1, soList.length, doList.length)` để đảm bảo số hàng (rows) xuất ra trong Excel luôn vừa đủ để chứa toàn bộ mã SO và mã đơn GHN của siêu thị đó.

## 5. Xử lý Lỗi Đồng Bộ GitHub (Git Sync)
- **Lỗi phát sinh:** Khi ấn "Đồng bộ Github", màn hình báo lỗi đỏ `Không thể tạo commit mới (git commit failed)`.
- **Nguyên nhân:** Xung đột trạng thái giữa máy tính (Local) và máy chủ (Remote) do quá trình tự động cập nhật bị ngắt quãng trước đó, dẫn đến trạng thái non-fast-forward. Hệ thống `run_pipeline.ps1` cố push nhưng bị từ chối.
- **Khắc phục:** Đã xử lý kỹ thuật (fetch và reset local branch) để đồng nhất dữ liệu. Script cập nhật tự động `Dong_Bo_Github.bat` và `run_pipeline.ps1` hiện đã hoạt động trơn tru.

## 6. Hướng dẫn sử dụng tính năng "Tự Động Chạy Tối Ưu"
Thay vì phải có một nút riêng biệt để chạy thuật toán:
- Hệ thống đã được thiết kế để tự động kích hoạt thuật toán chia tuyến mỗi khi thay đổi ngày.
- **Cách làm mới kết quả:** Nhấn `F5` (Tải lại trang) để nạp code mới nhất -> Chuyển sang ngày khác -> Chọn lại ngày cần tính toán. Code logic chia chuyến mới sẽ lập tức chạy ngầm và hiển thị ra màn hình.

