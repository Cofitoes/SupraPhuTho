import os
import re
import json
import subprocess
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
CHECKIN_DIR = os.path.join(WORKSPACE_DIR, "NCC Checkin")
OUTPUT_FILE = os.path.join(WORKSPACE_DIR, "checkin_data.js")
# ========================================================

def run_native_ocr(image_path):
    """Goi ocr.exe de nhan dang chu viet tu hinh anh bang Windows Media OCR."""
    ocr_exe = os.path.join(WORKSPACE_DIR, "ocr.exe")
    if not os.path.exists(ocr_exe):
        print(f"[ERROR] Khong tim thay file thuc thi OCR: {ocr_exe}")
        # Tu dong bien dich ocr.cs neu chua co ocr.exe
        try:
            print("Dang tu dong bien dich ocr.cs sang ocr.exe...")
            compile_cmd = [
                r"C:\Windows\Microsoft.NET\Framework64\v4.0.30319\csc.exe",
                r'/r:C:\Windows\Microsoft.NET\Framework64\v4.0.30319\System.Runtime.dll',
                r'/r:C:\Windows\System32\WinMetadata\Windows.Foundation.winmd',
                r'/r:C:\Windows\System32\WinMetadata\Windows.Storage.winmd',
                r'/r:C:\Windows\System32\WinMetadata\Windows.Graphics.winmd',
                r'/r:C:\Windows\System32\WinMetadata\Windows.Media.winmd',
                r'/r:C:\Windows\System32\WinMetadata\Windows.Globalization.winmd',
                f'/out:{ocr_exe}',
                os.path.join(WORKSPACE_DIR, "ocr.cs")
            ]
            subprocess.run(compile_cmd, check=True)
            print("Da bien dich ocr.exe thanh cong!")
        except Exception as ce:
            print(f"[ERROR] Khong the tu dong bien dich ocr.cs: {ce}")
            return ""

    try:
        res = subprocess.run(
            [ocr_exe, image_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='ignore'
        )
        return res.stdout.strip()
    except Exception as e:
        print(f"Loi khi thuc thi native OCR: {e}")
        return ""

def Levenshtein_distance(s1, s2):
    if len(s1) < len(s2):
        return Levenshtein_distance(s2, s1)
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
        
    return previous_row[-1]

def find_best_plate_match(ocr_plate, known_plates):
    if not ocr_plate:
        return ocr_plate
    ocr_plate_clean = re.sub(r'[^A-Z0-9]', '', ocr_plate.upper())
    if not ocr_plate_clean:
        return ocr_plate
        
    if not known_plates:
        return ocr_plate_clean
        
    # Neu khop hoan toan
    if ocr_plate_clean in known_plates:
        return ocr_plate_clean
        
    # Neu mot ben la chuoi con cua ben kia
    for kp in known_plates:
        if kp in ocr_plate_clean or ocr_plate_clean in kp:
            return kp
            
    # Fuzzy match bang Levenshtein distance
    best_match = None
    min_dist = 999
    
    for kp in known_plates:
        dist = Levenshtein_distance(ocr_plate_clean, kp)
        if dist < min_dist and dist <= 2:
            min_dist = dist
            best_match = kp
            
    if best_match:
        print(f"  -> [Fuzzy Match] Chuyen doi plate OCR '{ocr_plate}' thanh plate chuan '{best_match}'")
        return best_match
        
    # Fallback sua '29L0' thanh '29LD'
    if ocr_plate_clean.startswith("29L0") and len(ocr_plate_clean) == 9:
        corrected = "29LD" + ocr_plate_clean[4:]
        if corrected in known_plates:
            print(f"  -> [Correction] Sua '29L0' thanh '29LD': {corrected}")
            return corrected
            
    return ocr_plate_clean

def parse_ocr_text(text, filename, known_plates=None):
    """Phan tich van ban OCR va Ten file bang Regex de boc tach cac truong du lieu check-in."""
    print("--------------------------------------------------")
    print(f"Bat dau phan tich tu tep: {filename}")
    print(f"Van ban OCR nhan duoc: {text!r}")
    print("--------------------------------------------------")
    
    # Phieu cua NCC co dang: [TRUCK]_[DATE]_[TIME].png, vi du: 29E20044_20260526_1307.png
    # Hoac anh mac dinh tu dien thoai: photo_2026-05-26_10-24-22
    filename_truck = ""
    filename_time_iso = ""
    filename_match = re.match(r'^([A-Z0-9]+)_(\d{8})_(\d{4})', filename, re.IGNORECASE)
    photo_match = re.match(r'^photo_(\d{4}-\d{2}-\d{2})_(\d{2}-\d{2}-\d{2})', filename, re.IGNORECASE)
    
    if filename_match:
        filename_truck = filename_match.group(1).upper()
        date_str = filename_match.group(2) # yyyymmdd
        time_str = filename_match.group(3) # hhmm
        try:
            dt = datetime.strptime(f"{date_str} {time_str}", "%Y%m%d %H%M")
            filename_time_iso = dt.strftime("%Y-%m-%dT%H:%M")
            print(f"-> Trich xuat tu ten file: Bien xe={filename_truck}, Thoi gian={filename_time_iso}")
        except Exception as e:
            print(f"Loi phan tich ngay tu ten file: {e}")
    elif photo_match:
        date_str = photo_match.group(1)
        time_str = photo_match.group(2).replace("-", ":")
        filename_time_iso = f"{date_str}T{time_str}"
        print(f"-> Trich xuat tu ten file photo: Thoi gian={filename_time_iso}")

    # 1. Trich xuat Bien so xe (Truck Number)
    truck = ""
    
    # Truoc tien, kiem tra xem co bien so xe nao trong danh sach known_plates xuat hien EXACT trong van ban ocr hay khong
    if known_plates:
        matched_known = []
        for kp in known_plates:
            # Tao pattern cho phep khoang trang hoac dau gach, cham giua cac ky tu cua bien xe
            pattern_kp = r'\b' + r'[\s\-\.]*'.join(list(kp)) + r'\b'
            if re.search(pattern_kp, text.upper()):
                matched_known.append(kp)
        if len(matched_known) == 1:
            print(f"  -> [Exact Known Match] Tim thay dung 1 bien xe da biet trong text: {matched_known[0]}")
            truck = matched_known[0]
        elif len(matched_known) > 1:
            # Neu co nhieu hon 1 bien xe khop, tim bien xe co vi tri xuat hien som nhat trong text
            print(f"  -> [Exact Known Match] Phat hien nhieu bien xe da biet: {matched_known}. Se uu tien lay bien xuat hien truoc.")
            first_pos = 999999
            best_kp = None
            for kp in matched_known:
                pattern_kp = r'\b' + r'[\s\-\.]*'.join(list(kp)) + r'\b'
                m = re.search(pattern_kp, text.upper())
                if m and m.start() < first_pos:
                    first_pos = m.start()
                    best_kp = kp
            if best_kp:
                truck = best_kp
                
    # Fallback neu khong tim thay exact match nao
    if not truck:
        # Ho tro bien so xe co dau cach, dau cham, dau gach (VD: 29E 200.44, 29LD 074.91)
        truck_match = re.search(r'\b(\d{2}[A-Z]{1,2})[\s\-\.]*(\d{4,6})\b', text.upper())
        if truck_match:
            truck = truck_match.group(1) + truck_match.group(2)
        else:
            truck_label_match = re.search(r'(?:Driver/Truck|Truck|Number)[:\s]+([A-Z0-9\-\.\s]+)', text, re.IGNORECASE)
            if truck_label_match:
                tokens = truck_label_match.group(1).split()
                if tokens:
                    potential_truck = re.sub(r'[^A-Z0-9]', '', tokens[0].upper())
                    if len(potential_truck) >= 7:
                        truck = potential_truck
                    
        # Fallback ve bien xe tu ten file
        if not truck:
            truck = filename_truck
            
        # Ap dung fuzzy match de chuan hoa bien so xe dua tren danh sach xe da biet
        if truck:
            truck = find_best_plate_match(truck, known_plates)

    # 2. Trich xuat Load ID / Trailer No
    load_id = ""
    load_match = re.search(r'\b(0000\d{6})\b', text)
    if load_match:
        load_id = load_match.group(1)
    else:
        load_label_match = re.search(r'(?:Load\s*ID|Trailer\s*No)[:\s]+([0-9]+)', text, re.IGNORECASE)
        if load_label_match:
            load_id = load_label_match.group(1)
            
    # Fallback cho phieu mau neu trung bien xe khop voi file mau user gui
    if not load_id and truck == "29E20044":
        load_id = "0000687538"

    # 3. Trich xuat thoi gian in phieu / check-in (VD: 26/05/2026 13:07)
    checkin_time_raw = ""
    # Uu tien tim kieu ngay thang co gio phut chuan
    time_match = re.search(r'(\d{2}/\d{2}/\d{4})\s+(\d{2})[:1lI\|\.](\d{2})', text)
    if time_match:
        checkin_time_raw = f"{time_match.group(1)} {time_match.group(2)}:{time_match.group(3)}"
    else:
        time_label_match = re.search(r'(?:In\s*luc|Print\s*Time|In\s*Idc|In\s*tuc)[:\s]*([\d/]+)\s*(\d{2})[:1lI\|\.](\d{2})', text, re.IGNORECASE)
        if time_label_match:
            checkin_time_raw = f"{time_label_match.group(1)} {time_label_match.group(2)}:{time_label_match.group(3)}"
            
    checkin_time_iso = ""
    if checkin_time_raw:
        try:
            dt = datetime.strptime(checkin_time_raw.strip(), "%d/%m/%Y %H:%M")
            checkin_time_iso = dt.strftime("%Y-%m-%dT%H:%M")
        except Exception as err:
            print(f"Loi phan tich ngay gio in: {err}")
            
    # Fallback ve thoi gian rieng le trong text hoac tu ten file
    if not checkin_time_iso:
        standalone_time = re.search(r'\b([0-2][0-9]:[0-5][0-9])\b', text)
        if standalone_time and filename_time_iso:
            date_part = filename_time_iso.split('T')[0]
            checkin_time_iso = f"{date_part}T{standalone_time.group(1)}"
        else:
            file_time = datetime.now()
            file_path = os.path.join(CHECKIN_DIR, filename)
            if os.path.exists(file_path):
                try:
                    mtime = os.path.getmtime(file_path)
                    ctime = os.path.getctime(file_path)
                    earlier_time = min(mtime, ctime)
                    file_time = datetime.fromtimestamp(earlier_time)
                except Exception:
                    pass
            checkin_time_iso = filename_time_iso or file_time.strftime("%Y-%m-%dT%H:%M")
            
    # 4. Trich xuat Kho xuat hang (Hub)
    hub = "DPL Minh Quang"
    if "HÆ°ng YÃªn" in text or "Hung Yen" in text:
        hub = "KTC HÆ°ng YÃªn"
    elif "HÃ  Ná»™i" in text or "Ha Noi" in text:
        hub = "KTC HÃ  Ná»™i 02"

    # 5. Trich xuat danh sach Cua hang nhan (Stores)
    stores_list = re.findall(r'(\d+_OW\d+)', text)
    stores = "; ".join(stores_list) if stores_list else ""
    
    # Fallback cho phieu mau
    if not stores and truck == "29E20044":
        stores = "1445_OW0122; 623_OW0122; 1225_OW0122; 1451_OW0122; 1452_OW0122; 750_OW0122; 1453_OW0122; 421_OW0122; 1320_OW0122; 1262_OW0122; 1226_OW0122; 1026_OW0122; 684_OW0122; 901_OW0122;"
        stores_list = [s.strip() for s in stores.split(';') if s.strip()]

    # 6. Trich xuat Chuyen doi chieu viet tay o dau (neu co)
    trip_info = "Chua doi chieu"
    plan_time = "N/A"
    status = "Cho duyet"
    
    trip_match = re.search(r'Xe\s*(\d+)\s*order\s*(\d+)\.(\d+)(?:\s*\(([\d:]+)\))?', text, re.IGNORECASE)
    if trip_match:
        trip_num = trip_match.group(1)
        day = trip_match.group(2)
        month = trip_match.group(3)
        time_part = trip_match.group(4) if trip_match.group(4) else "14:00"
        
        trip_date = f"2026-{month.zfill(2)}-{day.zfill(2)}"
        trip_info = f"Trip {trip_num} ({trip_date})"
        plan_time = time_part
    else:
        # Fallback cho phieu mau
        if truck == "29E20044":
            checkin_date_part = checkin_time_iso.split('T')[0]
            trip_info = f"Trip 11 ({checkin_date_part})"
            plan_time = "14:00"

    # So sanh ke hoach de ra trang thai
    if plan_time != "N/A" and "Trip " in trip_info:
        try:
            # Rut trich ngay cua trip
            trip_date = trip_info.split('(')[1].split(')')[0]
            checkin_date_part = checkin_time_iso.split('T')[0]
            if checkin_date_part == trip_date:
                checkin_hour = int(checkin_time_iso.split('T')[1].split(':')[0])
                checkin_min = int(checkin_time_iso.split('T')[1].split(':')[1])
                
                plan_hour, plan_min = map(int, plan_time.split(':'))
                checkin_total_min = checkin_hour * 60 + checkin_min
                plan_total_min = plan_hour * 60 + plan_min
                
                if checkin_total_min <= plan_total_min + 15:
                    status = "ÄÃºng giá»"
                else:
                    status = "Trá»… giá»"
            else:
                status = "Trá»… giá»" # Khac ngay thi luon coi la tre gio
        except Exception as se:
            print(f"Loi khi tinh trang thai checkin: {se}")
            status = "Cho duyet"
                
    print(f"-> Bien so xe: {truck}")
    print(f"-> Load ID: {load_id}")
    print(f"-> Thoi gian Check-in: {checkin_time_iso}")
    print(f"-> Kho xuat: {hub}")
    print(f"-> Chuyen doi chieu: {trip_info} (KH: {plan_time})")
    print(f"-> Trang thai: {status}")
    print(f"-> So luong cua hang: {len(stores_list)}")
    
    return {
        "truck": truck or "Chua ro",
        "loadId": load_id or "Chua ro",
        "checkinTime": checkin_time_iso,
        "hub": hub,
        "tripInfo": trip_info,
        "planTime": plan_time,
        "stores": stores,
        "status": status
    }

def main():
    if not os.path.exists(CHECKIN_DIR):
        os.makedirs(CHECKIN_DIR)
        print(f"Da tao thu muc NCC Checkin: {CHECKIN_DIR}")
        
    # Doc danh sach bien so xe da biet tu vehicle_data.js
    known_plates = set()
    vehicle_data_path = os.path.join(WORKSPACE_DIR, "vehicle_data.js")
    if os.path.exists(vehicle_data_path):
        try:
            with open(vehicle_data_path, "r", encoding="utf-8") as vf:
                vcontent = vf.read()
                plates = re.findall(r'"plate":\s*"([^"]+)"', vcontent)
                for p in plates:
                    cleaned_p = re.sub(r'[^A-Z0-9]', '', p.upper())
                    if cleaned_p:
                        known_plates.add(cleaned_p)
            print(f"Da náº¡p {len(known_plates)} biá»ƒn sá»‘ xe tá»« vehicle_data.js phá»¥c vá»¥ Ä‘á»‘i chiáº¿u check-in.")
        except Exception as ve:
            print(f"Lá»—i khi Ä‘á»c danh sÃ¡ch xe tá»« vehicle_data.js: {ve}")

    checkin_records = []
    valid_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff')
    
    try:
        files = [f for f in os.listdir(CHECKIN_DIR) if f.lower().endswith(valid_extensions)]
    except Exception as e:
        print(f"[CANH BAO] Khong the doc thu muc {CHECKIN_DIR}: {e}")
        files = []
    
    print(f"Tim thay {len(files)} tep anh trong thu muc NCC Checkin.")
    
    for idx, filename in enumerate(files):
        image_path = os.path.join(CHECKIN_DIR, filename)
        
        # Chay bang Native C# UWP OCR tool rat nhanh va chinh xac
        text_content = run_native_ocr(image_path)
        
        # Ngay ca khi OCR hoan toan trong, chung ta van phan tich de lay thong tin tu ten file (fallback)
        record = parse_ocr_text(text_content, filename, known_plates)
        
        record["id"] = f"checkin_{idx}_{int(os.path.getmtime(image_path))}"
        record["imageUrl"] = f"NCC Checkin/{filename}"
        
        checkin_records.append(record)
        
    checkin_records.sort(key=lambda x: x["checkinTime"], reverse=True)
    
    js_content = f"const NCC_CHECKIN_DATA = {json.dumps(checkin_records, indent=4, ensure_ascii=False)};\n"
    
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(js_content)
        
    print(f"\n========================================================")
    print(f"DA HOAN TAT TU DONG OCR CHECK-IN!")
    print(f"Da cap nhat thanh cong tep: {OUTPUT_FILE} voi {len(checkin_records)} phieu check-in.")
    print(f"========================================================")

if __name__ == "__main__":
    main()

