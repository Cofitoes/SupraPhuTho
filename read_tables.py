from docx import Document

docx_path = r'g:\My Drive\Training AI\Supra Phú Thọ\BangGia\Pham_Gia_88\Phạm Gia 88\FINAL_GHN_PHAMGIA88_Phụ_Lục_01_HDDV_Thuê_Tải_Liên_Vùng_B2B.docx'
out_path = r'g:\My Drive\Training AI\Supra Phú Thọ\tables.txt'
doc = Document(docx_path)

with open(out_path, 'w', encoding='utf-8') as f:
    for t_idx, table in enumerate(doc.tables):
        f.write(f"--- Table {t_idx} ---\n")
        for r_idx, row in enumerate(table.rows):
            row_data = [cell.text.replace('\n', ' ').strip() for cell in row.cells]
            f.write(f"[{r_idx}] " + " | ".join(row_data) + "\n")
        f.write("\n")
