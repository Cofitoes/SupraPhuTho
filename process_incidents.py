import os
import json
import sys
from datetime import datetime

# Reconfigure stdout to use utf-8 to prevent UnicodeEncodeError in Windows consoles
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# ========================================================
# CAU HINH THU MUC VA TEP KET XUAT
# ========================================================
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
INCIDENTS_DIRS = [
    os.path.join(WORKSPACE_DIR, "Su_Co"),
    os.path.join(WORKSPACE_DIR, "Sá»± Cá»‘")
]
OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "incidents_data.js")
# ========================================================

def main():
    # Dam bao thu muc ton tai
    main_dir = INCIDENTS_DIRS[0]
    if not os.path.exists(main_dir):
        os.makedirs(main_dir)
        print(f"Da tao thu muc: {main_dir}")

    incidents_list = []
    processed_ids = set()

    # Quet ca hai thu muc
    for folder in INCIDENTS_DIRS:
        if not os.path.exists(folder):
            continue
            
        print(f"Dang quet thu muc su co: {folder}")
        for filename in os.listdir(folder):
            if not filename.lower().endswith('.json'):
                continue
                
            file_path = os.path.join(folder, filename)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                # Kiem tra cac truong bat buoc
                if isinstance(data, dict) and "id" in data and "date" in data:
                    inc_id = data["id"]
                    if inc_id not in processed_ids:
                        incidents_list.append(data)
                        processed_ids.add(inc_id)
                        print(f" -> Nap thanh cong su co: {inc_id} ({data.get('type', 'Chua phan loai')}) tu file {filename}")
                    else:
                        print(f" -> Bo qua phieu trung lap: {inc_id} tu file {filename}")
            except Exception as e:
                print(f"[WARNING] Khong the doc file {filename}: {e}")

    # Sap xep theo thoi gian giam dan
    incidents_list.sort(key=lambda x: (x.get("date", ""), x.get("id", "")), reverse=True)

    # Ghi ra file js
    js_content = f"const INCIDENTS_DATA = {json.dumps(incidents_list, indent=4, ensure_ascii=False)};\n"
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(js_content)
        
    print(f"\n========================================================")
    print(f"DA HOAN TAT TON HOP DU LIEU SU CO!")
    print(f"Da cap nhat thanh cong tep: {OUTPUT_FILE} voi {len(incidents_list)} su co duoc dong bo.")
    print(f"========================================================")

if __name__ == "__main__":
    main()

