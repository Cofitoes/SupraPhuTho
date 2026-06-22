# CÔNG TẮC TIẾP QUẢN DỰ ÁN (AI CONTEXT SWITCH)

**Mục đích:** File này dùng để khôi phục "trí nhớ" cho AI khi bạn chuyển sang máy tính khác làm việc hoặc reset máy.
**Lệnh gọi AI trên máy tính mới:** *"Bạn hãy đọc file `Cong_Tac_Tiep_Quan.md` trong thư mục Supra Phú Thọ để tiếp tục"*

---

## 1. Môi trường làm việc (Workspace)
- **Thư mục dự án chính xác:** `g:\My Drive\Training AI\Supra Phú Thọ`
- **Lưu ý cho AI:** Cần chú ý kỹ thư mục làm việc, không được nhầm lẫn với project `LogisticsHub` (vì 2 thư mục có chung nhiều file giống nhau như `trips_logic2.js`).

## 2. Các quy ước cốt lõi (Bắt buộc AI phải tuân theo)
- **Nguồn Logic Chia Tuyến (QUAN TRỌNG NHẤT):**
  - Toàn bộ luật chia tuyến, gom hàng, phân loại xe hiện đã được xuất ra định dạng Word.
  - AI **bắt buộc** chỉ được tham chiếu và đọc logic từ file: `Logic_Chia_Tuyen.docx` (nằm trong thư mục Supra Phú Thọ). 
  - Người dùng sẽ cập nhật trực tiếp trên file Word đó, AI tuyệt đối không tự biên diễn hoặc lấy logic từ các file js cũ nếu có sự khác biệt.
- **Nguồn Chia Cửa Hàng (GXT vs Giao Thẳng):**
  - Các script và thuật toán **chỉ sử dụng file `ChiaCuaHang.xlsx`** làm căn cứ để xác định một cửa hàng thuộc cụm "GXT" hay "Giao thẳng", không sử dụng lại file tổng `Danh sách Winmart (1).xlsx`.

## 3. Tiến độ đã hoàn thành (Tính đến cuối ngày 20/06/2026)
- **Chuẩn hóa dữ liệu Winmart:** 
  - Đã xử lý, dọn dẹp lỗi tọa độ cho 4920 cửa hàng đầu tiên.
  - Đã tích hợp thêm 1672 cửa hàng mới từ file `Danh sách Winmart (1).xlsx`.
  - **Dữ liệu chuẩn cuối cùng** hiện có 6,592 cửa hàng và nằm ở file `DS_Winmart_Extracted.xlsx`.
- **Phân luồng định tuyến cửa hàng:** 
  - Đã trích xuất xong trạng thái từ cột I của file mới. 
  - Tạo ra file **`ChiaCuaHang.xlsx`** bao gồm 2 cột (Tên cửa hàng, Bộ phận) để làm căn cứ chia tuyến (Gồm 152 siêu thị GXT và phần còn lại là Giao thẳng).
- **Tài liệu:** 
  - File `Logic_Chia_Tuyen.docx` đã được cập nhật xong Phần 2: Thêm nguyên tắc gom nhóm về kho GXT Phú Thọ hoặc điều từ Hub chính.

---
*AI khi đọc được dòng này đã khôi phục thành công toàn bộ ngữ cảnh trước đó. Sẵn sàng nhận lệnh mới từ người dùng!*
