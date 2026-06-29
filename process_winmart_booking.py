import os
import glob
import pandas as pd
import json
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "Data_Booking")
BOOKING_JS_PATH = os.path.join(BASE_DIR, "booking_data.js")
SUMMARY_JS_PATH = os.path.join(BASE_DIR, "summary_data.js")

def extract_date_from_filename(filename):
    # Pattern 1: YYYYMMDD (e.g., 20260623)
    match = re.search(r'(\d{4})(\d{2})(\d{2})', filename)
    if match:
        return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"
    # Pattern 2: DD.MM.YYYY or DD-MM-YYYY (e.g., 22.6.2026 or 22-06-2026)
    match = re.search(r'(\d{1,2})[\.\-](\d{1,2})[\.\-](\d{4})', filename)
    if match:
        return f"{match.group(3)}-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
    # Pattern 3: DD.MM or DD-MM (e.g., 27.6 or 19.06) - assume current year 2026
    match = re.search(r'(\d{1,2})[\.\-](\d{1,2})', filename)
    if match:
        return f"2026-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
    return None

def main():
    booking_points = []
    summary_data = {}

    all_files = glob.glob(os.path.join(DATA_DIR, "*.xls*"))
    date_groups = {}
    
    for file in all_files:
        if "~$" in file: continue
        filename = os.path.basename(file)
        date_str = extract_date_from_filename(filename)
        
        # If date is not found in filename, try reading it
        if not date_str:
            try:
                if file.lower().endswith(".xlsb"):
                    df = pd.read_excel(file, engine="pyxlsb", nrows=10)
                else:
                    df = pd.read_excel(file, engine="openpyxl", nrows=10)
                
                # Check for "Ngày xuất"
                for col in df.columns:
                    if 'Ngày xuất' in str(col):
                        first_date = df[col].dropna().iloc[0]
                        if pd.notnull(first_date):
                            date_str = pd.to_datetime(first_date).strftime('%Y-%m-%d')
                            break
            except Exception:
                pass
                
        if not date_str:
            print(f"Skipping {filename}: Cannot determine date")
            continue
            
        if date_str not in date_groups:
            date_groups[date_str] = []
        date_groups[date_str].append(file)

    # Deduplicate: select one file per date
    selected_files = []
    for date_str, group in date_groups.items():
        if len(group) == 1:
            selected_files.append((group[0], date_str))
        else:
            # Multiple files for the same date! Prioritize Booking Supra over others
            best_file = None
            for file in group:
                filename = os.path.basename(file)
                if filename.startswith("Booking Supra"):
                    best_file = file
                    break
            if not best_file:
                for file in group:
                    filename = os.path.basename(file)
                    if "GHN" in filename:
                        best_file = file
                        break
            if not best_file:
                best_file = group[0]
                
            ignored = [os.path.basename(f) for f in group if f != best_file]
            print(f"For date {date_str}, processed {os.path.basename(best_file)} and ignored duplicates: {ignored}")
            selected_files.append((best_file, date_str))

    for file, date_str in selected_files:
        filename = os.path.basename(file)
        
        # Determine engine
        engine = "pyxlsb" if file.lower().endswith(".xlsb") else "openpyxl"
        
        try:
            df = None
            
            if file.lower().endswith(".xlsb"):
                # For .xlsb files, try all sheets to find the one with detail data
                # pyxlsb has Unicode NFD encoding issues with sheet names, so we read by index
                import pyxlsb
                wb = pyxlsb.open_workbook(file)
                num_sheets = len(wb.sheets)
                
                best_df = None
                best_rows = 0
                
                for sheet_idx in range(num_sheets):
                    try:
                        candidate = pd.read_excel(file, engine="pyxlsb", sheet_name=sheet_idx)
                        # Detect header row
                        header_idx = None
                        for idx, row in candidate.head(10).iterrows():
                            row_str = str(row.values)
                            if 'STT' in row_str or 'Tỉnh' in row_str or 'Ngày xuất' in row_str or 'siêu thị' in row_str.lower():
                                header_idx = idx
                                break
                        if header_idx is not None and header_idx > 0:
                            candidate = pd.read_excel(file, engine="pyxlsb", sheet_name=sheet_idx, header=header_idx)
                        
                        candidate.columns = [str(c).strip() for c in candidate.columns]
                        
                        # Check if this sheet has the detail columns we need
                        has_store = any('siêu thị' in str(c).lower() or 'Tên siêu thị' in str(c) for c in candidate.columns)
                        if has_store and len(candidate) > best_rows:
                            best_df = candidate
                            best_rows = len(candidate)
                    except Exception:
                        continue
                
                if best_df is not None:
                    df = best_df
                else:
                    # Fallback: read default sheet
                    df = pd.read_excel(file, engine="pyxlsb")
                    header_idx = None
                    for idx, row in df.head(10).iterrows():
                        row_str = str(row.values)
                        if 'STT' in row_str or 'Tỉnh' in row_str or 'Ngày xuất' in row_str:
                            header_idx = idx
                            break
                    if header_idx is not None and header_idx > 0:
                        df = pd.read_excel(file, engine="pyxlsb", header=header_idx)
            else:
                # For .xlsx/.xls files
                df = pd.read_excel(file, engine="openpyxl")
                header_idx = None
                for idx, row in df.head(10).iterrows():
                    row_str = str(row.values)
                    if 'STT' in row_str or 'Tỉnh' in row_str or 'Ngày xuất' in row_str:
                        header_idx = idx
                        break
                if header_idx is not None and header_idx > 0:
                    df = pd.read_excel(file, engine="openpyxl", header=header_idx)
                
            # Date is already determined as date_str
            if not date_str:
                continue
                
            # Rename columns to handle slight variations like spaces
            df.columns = [str(c).strip() for c in df.columns]
            
            # Group by Store (Mã siêu thị or Tên siêu thị)
            # Group fields: Tên siêu thị, Tỉnh, Quận, Đơn vị vận tải
            if 'Tên siêu thị' not in df.columns:
                continue
                
            for _, row in df.iterrows():
                store_name = row.get('Tên siêu thị', '')
                if pd.isna(store_name) or not str(store_name).strip():
                    continue
                    
                province = row.get('Tỉnh', '')
                district = row.get('Quận', '')
                def safe_float(val):
                    if pd.isna(val): return 0.0
                    try:
                        return float(str(val).strip())
                    except ValueError:
                        return 0.0

                volume = safe_float(row.get('Volume'))
                if volume == 0:
                    volume = safe_float(row.get('Volume up (m3)'))
                
                weight = safe_float(row.get('Weight'))
                if weight == 0:
                    weight = safe_float(row.get('Weight (kg)'))
                    
                qty = safe_float(row.get('Qty'))
                
                carrier = str(row.get('Đơn vị vận tải', 'GHN')).strip()
                if pd.isna(carrier) or carrier == 'nan':
                    carrier = 'GHN'
                    
                so_do_count = 1 if pd.notna(row.get('Số SO')) or pd.notna(row.get('Số DO')) else 0

                # Check if we already have this store for this date
                existing = next((p for p in booking_points if p['date'] == date_str and p['name'] == store_name), None)
                if existing:
                    existing['volume'] += volume
                    existing['weight'] += weight
                    existing['total_qty'] += qty
                    existing['so_count'] += so_do_count
                else:
                    booking_points.append({
                        "id": str(row.get('Mã siêu thị', store_name)).strip(),
                        "date": date_str,
                        "name": store_name,
                        "address": f"{district}, {province}".strip(", "),
                        "province": province,
                        "volume": volume,
                        "weight": weight,
                        "total_qty": qty,
                        "so_count": so_do_count,
                        "carrier": carrier
                    })
                    
        except Exception as e:
            print(f"Error processing {filename}: {e}")

    # Write booking_data.js
    with open(BOOKING_JS_PATH, "w", encoding="utf-8") as f:
        f.write(f"const BOOKING_DELIVERY_POINTS = {json.dumps(booking_points, ensure_ascii=False, indent=2)};\n")
    print(f"Written {len(booking_points)} points to {BOOKING_JS_PATH}")
    
    # Generate summary_data.js
    for p in booking_points:
        d = p['date']
        if d not in summary_data:
            summary_data[d] = {
                "date": d,
                "storeCount": 0,
                "totalVolume": 0,
                "totalWeight": 0
            }
        summary_data[d]["storeCount"] += 1
        summary_data[d]["totalVolume"] += p["volume"]
        summary_data[d]["totalWeight"] += p["weight"]
        
    summary_list = list(summary_data.values())
    summary_list.sort(key=lambda x: x['date'])
    with open(SUMMARY_JS_PATH, "w", encoding="utf-8") as f:
        f.write(f"const BOOKING_SUMMARY = {json.dumps(summary_list, ensure_ascii=False, indent=2)};\n")
    print(f"Written summary for {len(summary_list)} dates to {SUMMARY_JS_PATH}")

if __name__ == '__main__':
    main()
