import docx
import os

doc_path = r"g:\My Drive\Training AI\Supra Phú Thọ\Logic Chia Tuyen New.docx"
log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"

try:
    if os.path.exists(doc_path):
        doc = docx.Document(doc_path)
        
        # 1. Update Step 1 paragraph
        # "Bước 1: Lọc bỏ GXT: Quét danh sách các bưu cục trong booking ngày làm việc. Nếu bưu cục thuộc diện GXT (chuyển tiếp), chuyển thẳng sang luồng vận chuyển GXT Phú Thọ riêng. Hệ thống sẽ tự động tính toán tổng lượng hàng, trọng tải và thể tích của nhóm siêu thị này để đề xuất loại xe (1.9T, 5T, 8T) phù hợp nhất, đảm bảo tối ưu chi phí."
        target_p1 = "Bước 1: Lọc bỏ GXT:"
        new_p1 = "Bước 1: Lọc bỏ GXT (Luồng Xe Trung Chuyển): Quét danh sách các bưu cục trong booking ngày làm việc. Nếu bưu cục thuộc diện GXT (chuyển tiếp), chuyển thẳng sang luồng vận chuyển xe trung chuyển GXT Phú Thọ riêng. Hệ thống sẽ tự động tính toán tổng lượng hàng, trọng tải và thể tích của nhóm siêu thị này để đề xuất loại xe trung chuyển (1.9T, 5T, 8T) phù hợp nhất, đảm bảo tối ưu chi phí."
        
        # 2. Update Step 2 paragraph
        # "Bước 2: Gom Huyện/Xã: Lọc các đơn hàng còn lại theo địa bàn và gán về 5 nhóm tuyến cố định nêu trên dựa trên trường thông tin Huyện/Xã."
        target_p2 = "Bước 2: Gom Huyện/Xã:"
        new_p2 = "Bước 2: Gom Huyện/Xã (Luồng Xe Giao Thẳng): Lọc các đơn hàng còn lại theo địa bàn và gán về 5 nhóm tuyến cố định nêu trên dựa trên trường thông tin Huyện/Xã."
        
        # 3. Update Step 3 paragraph
        # "Bước 3: Đóng chuyến & Nâng tải: Xếp hàng hóa vào xe 1.9T trước. Nếu tổng trọng lượng <= 2090 kg và thể tích <= 14 CBM, chốt chạy xe 1.9T. Nếu vượt quá định mức xe 1.9T, tự động nâng tải trọng xe lên xe 5T. Nếu vượt quá trần xe 5T (5500 kg hoặc 26 CBM), tiến hành chốt chuyến xe 5T đầu tiên và chuyển phần hàng còn thừa sang chuyến xe thứ 2 (bắt đầu lại từ định mức 1.9T).Số lượng xe 5T sử dụng trong 1 ngày tối đa 2 xe, còn lại sử dụng xe 1.9T"
        target_p3 = "Bước 3: Đóng chuyến & Nâng tải:"
        new_p3 = "Bước 3: Đóng chuyến & Nâng tải: Xếp hàng hóa của xe giao thẳng vào xe 1.9T trước. Nếu tổng trọng lượng <= 2090 kg và thể tích <= 14 CBM, chốt chạy xe giao thẳng 1.9T. Nếu vượt quá định mức xe 1.9T, tự động nâng tải trọng xe lên xe giao thẳng 5T. Nếu vượt quá trần xe 5T (5500 kg hoặc 26 CBM), tiến hành chốt chuyến xe giao thẳng 5T đầu tiên và chuyển phần hàng còn thừa sang chuyến xe giao thẳng thứ 2 (bắt đầu lại từ định mức 1.9T). Số lượng xe giao thẳng 5T sử dụng trong 1 ngày tối đa 2 xe, còn lại sử dụng xe giao thẳng 1.9T."

        updated_count = 0
        for para in doc.paragraphs:
            if para.text.startswith(target_p1):
                para.text = new_p1
                updated_count += 1
            elif para.text.startswith(target_p2):
                para.text = new_p2
                updated_count += 1
            elif para.text.startswith(target_p3):
                para.text = new_p3
                updated_count += 1

        doc.save(doc_path)
        with open(log_path, 'w', encoding='utf-8') as log:
            log.write(f"Successfully updated DOCX file logic description. Updated paragraphs count: {updated_count}\n")
    else:
        with open(log_path, 'w', encoding='utf-8') as log:
            log.write("DOCX file for logic description not found!\n")
            
except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"ERROR updating docx: {e}\n")

# Delete docx_content.txt
temp_txt = r"g:\My Drive\Training AI\Supra Phú Thọ\docx_content.txt"
if os.path.exists(temp_txt):
    os.remove(temp_txt)

# Self delete
if os.path.exists(__file__):
    os.remove(__file__)
