from docx import Document

docx_path = r'g:\My Drive\Training AI\Supra Phú Thọ\Logic_Chia_Tuyen.docx'
out_path = r'g:\My Drive\Training AI\Supra Phú Thọ\docx_content.txt'
doc = Document(docx_path)

with open(out_path, 'w', encoding='utf-8') as f:
    for i, p in enumerate(doc.paragraphs):
        f.write(f"[{i}] {p.text}\n")
