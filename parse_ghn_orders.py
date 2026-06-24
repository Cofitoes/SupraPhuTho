import pandas as pd
import json
import os
import glob
from datetime import datetime
import re

DATA_DIR = "g:\\My Drive\\Training AI\\Supra Phú Thọ\\Data_Booking"
MAIN_FILE = "g:\\My Drive\\Training AI\\Supra Phú Thọ\\T06.2026 GHN-Supra.xlsx"

store_ghn_so_data = {}

def extract_date_from_filename(filename):
    match = re.search(r'202606(\d{2})', filename)
    if match: return f"2026-06-{match.group(1).zfill(2)}"
    match = re.search(r'(\d{1,2})\.(\d{1,2})\.(\d{4})', filename)
    if match: return f"{match.group(3)}-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
    match = re.search(r'(\d{1,2})\.(\d{1,2})', filename)
    if match: return f"2026-{match.group(2).zfill(2)}-{match.group(1).zfill(2)}"
    return None

def process_dataframe(df, default_date_str):
    header_row_idx = -1
    for idx, row in df.head(15).iterrows():
        row_vals = [str(x).lower() for x in row.values]
        if any('mã đơn ghn' in v or 'số do' in v or 'số so' in v for v in row_vals):
            header_row_idx = idx
            break
            
    if header_row_idx == -1:
        return
        
    df.columns = df.iloc[header_row_idx]
    df = df.iloc[header_row_idx+1:]
    df.columns = [str(c).strip().lower() for c in df.columns]
    
    col_ghn = next((c for c in df.columns if 'mã đơn ghn' in c or 'số do' in c), None)
    col_so = next((c for c in df.columns if 'số so' in c), None)
    col_store = next((c for c in df.columns if 'tên siêu thị' in c or 'store name' in c), None)
    col_date = next((c for c in df.columns if 'ngày xuất' in c or 'ngày' in c), None)
    
    if not col_ghn or not col_so or not col_store:
        return
        
    for _, row in df.iterrows():
        store_name = str(row[col_store]).strip()
        if store_name == 'nan' or not store_name: continue
        
        ghn = str(row[col_ghn]).strip()
        so = str(row[col_so]).strip()
        if ghn == 'nan': ghn = ''
        if so == 'nan': so = ''
        if not ghn and not so: continue
        
        date_str = default_date_str
        if col_date and pd.notna(row[col_date]):
            val = row[col_date]
            if isinstance(val, datetime):
                date_str = val.strftime("%Y-%m-%d")
            else:
                try:
                    date_str = pd.to_datetime(val).strftime("%Y-%m-%d")
                except:
                    pass
                    
        if not date_str: continue
            
        if date_str not in store_ghn_so_data:
            store_ghn_so_data[date_str] = {}
        if store_name not in store_ghn_so_data[date_str]:
            store_ghn_so_data[date_str][store_name] = {'so': [], 'ghn': []}
            
        if so and so not in store_ghn_so_data[date_str][store_name]['so']:
            store_ghn_so_data[date_str][store_name]['so'].append(so)
        if ghn and ghn not in store_ghn_so_data[date_str][store_name]['ghn']:
            store_ghn_so_data[date_str][store_name]['ghn'].append(ghn)

# Process MAIN_FILE
if os.path.exists(MAIN_FILE):
    try:
        xl = pd.ExcelFile(MAIN_FILE)
        for sheet_name in xl.sheet_names:
            try:
                date_obj = datetime.strptime(sheet_name.strip(), "%d.%m.%Y")
                date_str = date_obj.strftime("%Y-%m-%d")
            except ValueError:
                continue
            df = pd.read_excel(MAIN_FILE, sheet_name=sheet_name, header=None)
            process_dataframe(df, date_str)
    except Exception as e:
        print(f"Error processing {MAIN_FILE}: {e}")

# Process Data_Booking files
for file in glob.glob(os.path.join(DATA_DIR, "*.xls*")):
    if "~$" in file: continue
    filename = os.path.basename(file)
    default_date = extract_date_from_filename(filename)
    
    try:
        engine = "pyxlsb" if file.lower().endswith(".xlsb") else "openpyxl"
        if file.lower().endswith(".xlsb"):
            import pyxlsb
            wb = pyxlsb.open_workbook(file)
            for sheet_idx in range(len(wb.sheets)):
                df = pd.read_excel(file, engine="pyxlsb", sheet_name=sheet_idx, header=None)
                process_dataframe(df, default_date)
        else:
            xl = pd.ExcelFile(file, engine="openpyxl")
            for sheet_name in xl.sheet_names:
                df = pd.read_excel(file, sheet_name=sheet_name, engine="openpyxl", header=None)
                process_dataframe(df, default_date)
    except Exception as e:
        print(f"Error processing {filename}: {e}")

js_content = f"const STORE_GHN_SO_DATA = {json.dumps(store_ghn_so_data, ensure_ascii=False, indent=2)};\n"
output_path = "g:\\My Drive\\Training AI\\Supra Phú Thọ\\data_ghn_so.js"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(js_content)
print(f"Written data_ghn_so.js successfully.")
