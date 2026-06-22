# TÀI LIỆU LOGIC CHIA TUYẾN VẬN TẢI (CẬP NHẬT TỪ CODEBASE)

Tài liệu này tổng hợp bộ quy tắc (logic) đang được cài đặt trong hệ thống (dựa trên source code `trips_logic2.js` của dự án Supra Phú Thọ) để tự động chia tuyến, ghép chuyến, và đề xuất xe tải.

---

## 1. THÔNG SỐ CHUNG & GIỚI HẠN THIẾT LẬP

**Các điểm trung chuyển (Hubs)**
* **Hub chính xuất phát:** KCN Minh Quang (Tọa độ: 20.9193754, 106.115945)
* **KTC Hưng Yên:** (Tọa độ: 20.8370687, 106.0433685)
* **KTC Hà Nội 02:** (Tọa độ: 21.0310096, 105.9237737)

**Phân loại xe vận chuyển & Tải trọng tối đa (Logic cập nhật từ sau 08/06/2026)**
* **Xe 1.9 Tấn:** Tải trọng tối đa 1,900 kg | Thể tích tối đa 14 CBM.
* **Xe 5 Tấn:** Tải trọng tối đa 4,900 kg (cũ 5,500 kg) | Thể tích tối đa 26 CBM.
* **Xe 8 Tấn:** Tải trọng tối đa 6,800 kg (cũ 8,140 kg) | Thể tích tối đa 55 CBM.

*(Nguyên tắc quy đổi: 1 CBM tương đương 1,000 kg. Khi thuật toán xếp xe, khối lượng và thể tích được tính toán song song, không được vượt mốc nào).*

---

## 2. HƯỚNG DẪN LOGIC PHÂN TUYẾN & GOM HÀNG

Quy trình tối ưu hóa và ghép chuyến được thực hiện tuần tự theo 3 bước:

### BƯỚC 1: Ưu tiên giao thẳng Nhóm 1 (Tuyến gần / Nội Vùng)
**Nhóm 1 bao gồm:** Hà Nội, Bắc Ninh, Hưng Yên, Hải Dương.

* **Phân cụm tuyệt đối:** Ban đầu, đơn hàng được gom nghiêm ngặt theo từng tỉnh.
* **Thuật toán Farthest-First (Điểm xa nhất làm mỏ neo):** 
  * Tìm điểm giao xa Hub chính (KCN Minh Quang) nhất để làm điểm neo.
  * Quét các điểm giao chưa được xếp xe trong **cùng tỉnh**, chọn tối đa 2 điểm gần điểm neo nhất để ghép chung 1 xe 1.9T (Tối đa 3 điểm giao/xe).
  * Điều kiện: Tổng khối lượng <= 1,900kg và tổng thể tích <= 14 CBM.
* **Tối ưu thứ tự giao hàng (TSP):** Sắp xếp thứ tự các điểm dừng sao cho tổng quãng đường ngắn nhất.
* **Xử lý hàng lẻ (Leftovers):** Các điểm rớt lại không ghép đủ chuyến trong cùng một tỉnh sẽ được phép **ghép chéo (cross-province)** giữa 4 tỉnh này để tối ưu xe 1.9T. Hạn chế tối đa việc cho 1 xe đi 1 điểm nếu không đầy tải.
* **Cân bằng chuyến (Áp dụng từ 27/05/2026):** Thuật toán Move/Swap nội bộ để cân bằng lộ trình các chuyến, cố gắng duy trì quãng đường mỗi chuyến dưới 120km.

### BƯỚC 2: Phân tuyến đi tỉnh (Gộp Nhóm A, B, C, D)
**Phân loại nhóm tỉnh:**
* **Nhóm A:** Quảng Ninh, Hải Phòng, Thái Bình (Sử dụng xe 5T hoặc 8T).
* **Nhóm B:** Hà Nam & Nam Định (Gộp chung), Ninh Bình, Thanh Hóa (Sử dụng xe 5T hoặc 8T).
* **Nhóm C:** Vĩnh Phúc, Phú Thọ, Hòa Bình (Sử dụng xe 5T hoặc 8T).
* **Nhóm D:** Nghệ An, Hà Tĩnh, Quảng Bình, Đà Nẵng, Khánh Hòa, các tỉnh miền Trung & Tây Nguyên khác (Chỉ sử dụng xe 8T, **cho phép vượt quá 10% tải** để ưu tiên không phải đi trung chuyển).

**Logic xếp xe:**
* **Giai đoạn 1 (Giao thẳng 1 tỉnh):** Nếu tổng hàng của 1 tỉnh đủ >= 80% tải trọng/thể tích của xe 8T hoặc 5T, tỉnh đó sẽ được xếp đi thẳng 1 xe. Tất cả các điểm giao trong tỉnh được gộp thành 1 "Điểm đại diện".
* **Giai đoạn 2 (Ghép tỉnh cùng nhóm):** Những tỉnh còn lẻ hàng sẽ được thử ghép với các tỉnh khác **trong cùng một Nhóm** (A ghép A, B ghép B...). Nếu tổ hợp đạt >= 80% sức chứa, chuyến xe sẽ được chốt.
* **Giai đoạn 3 (Ngoại lệ ghép chéo nhóm):** Ưu tiên ghép chéo giữa Nhóm B và Nhóm D (Ví dụ: Hà Tĩnh ghép với Hà Nam - Nam Định) để tận dụng chuyến xe 8T chạy chung hướng mà không bị điều về KTC.

### BƯỚC 3: Trung chuyển hàng lẻ về các KTC (Kho Trung Chuyển)
Áp dụng cho các booking không thuộc Nhóm 1 chưa được xếp xe, hoặc các tỉnh rớt lại không ghép đủ chuyến đi thẳng ở Bước 2.

* **Phân luồng điều hướng:**
  * **Về KTC Hà Nội 02:** Hà Giang, Tuyên Quang, Lai Châu, Lào Cai, Yên Bái, Hòa Bình.
  * **Về KTC Hưng Yên:** Các tỉnh còn lại (Thanh Hóa, Nghệ An, Vĩnh Phúc, Hải Phòng...).
* **Gom xe trung chuyển:** 
  * Gom toàn bộ hàng lẻ của từng Hub và điều phối xe tải lớn (Ưu tiên xe 8T, sau đó là xe 5T) chở thẳng đến KTC.
  * Nếu tải trọng cho phép, có thể **ghép KTC Hưng Yên và KTC Hà Nội 02 vào chung 1 xe** để tiết kiệm chi phí.
  * Sau khi chia xong xe lớn, những đơn hàng sót lại siêu nhỏ sẽ được gom cho xe 1.9T chạy chặng trung chuyển.
