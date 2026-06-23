import pandas as pd
import json
import os
from datetime import datetime
import glob

# Try to find the file
file_path = "g:\\My Drive\\Training AI\\Supra Phú Thọ\\T06.2026 GHN-Supra.xlsx"
if not os.path.exists(file_path):
    print(f"File not found: {file_path}")
    exit(1)

store_ghn_so_data = {}

try:
    xl = pd.ExcelFile(file_path)
    for sheet_name in xl.sheet_names:
        # sheet_name is like "11.06.2026", convert to "2026-06-11"
        try:
            date_obj = datetime.strptime(sheet_name.strip(), "%d.%m.%Y")
            date_str = date_obj.strftime("%Y-%m-%d")
        except ValueError:
            # Skip sheets that aren't dates
            continue
        
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=None)
        
        header_row_idx = -1
        for idx, row in df.head(15).iterrows():
            row_vals = [str(x).lower() for x in row.values]
            if any('mã đơn ghn' in v or 'số so' in v or 'tên siêu thị' in v for v in row_vals):
                header_row_idx = idx
                break
                
        if header_row_idx == -1:
            continue
            
        df = pd.read_excel(file_path, sheet_name=sheet_name, header=header_row_idx)
            
        # Standardize column names
        df.columns = [str(c).strip() for c in df.columns]
        
        # Find exact column names case-insensitively
        col_ghn = next((c for c in df.columns if 'mã đơn ghn' in str(c).lower()), None)
        col_so = next((c for c in df.columns if 'số so' in str(c).lower()), None)
        col_store = next((c for c in df.columns if 'tên siêu thị' in str(c).lower()), None)
        
        if not col_ghn or not col_so or not col_store:
            # Skip safely
            continue
            
        if date_str not in store_ghn_so_data:
            store_ghn_so_data[date_str] = {}
            
        for _, row in df.iterrows():
            store_name = str(row[col_store]).strip()
            if store_name == 'nan' or not store_name:
                continue
                
            ghn = str(row[col_ghn]).strip()
            so = str(row[col_so]).strip()
            
            if ghn == 'nan': ghn = ''
            if so == 'nan': so = ''
            
            if store_name not in store_ghn_so_data[date_str]:
                store_ghn_so_data[date_str][store_name] = {'so': [], 'ghn': []}
                
            if so and so not in store_ghn_so_data[date_str][store_name]['so']:
                store_ghn_so_data[date_str][store_name]['so'].append(so)
                
            if ghn and ghn not in store_ghn_so_data[date_str][store_name]['ghn']:
                store_ghn_so_data[date_str][store_name]['ghn'].append(ghn)
                
except Exception as e:
    print(f"Error parsing excel: {e}")
    exit(1)

js_content = f"const STORE_GHN_SO_DATA = {json.dumps(store_ghn_so_data, ensure_ascii=False, indent=2)};\n"
output_path = "g:\\My Drive\\Training AI\\Supra Phú Thọ\\data_ghn_so.js"

with open(output_path, "w", encoding="utf-8") as f:
    f.write(js_content)
