import pandas as pd
import json

file_path = r"G:\My Drive\Training AI\Supra Phú Thọ\Danh_sach_Winmart.xlsx"

try:
    xl = pd.ExcelFile(file_path)
    # Find the sheet that looks like data
    sheet_name = xl.sheet_names[0]
    for s in xl.sheet_names:
        if 'data' in s.lower() or 'danh' in s.lower():
            sheet_name = s
            break
            
    df = pd.read_excel(file_path, sheet_name=sheet_name)
    gxt_stores = []
    
    # Try to find a column that indicates GXT.
    # The doc says "cột I", which is column index 8.
    # Let's also find the store name column.
    name_col = None
    for c in df.columns:
        if 'tên siêu thị' in str(c).lower() or 'tên' in str(c).lower() or 'name' in str(c).lower():
            name_col = c
            break
    if not name_col:
        name_col = df.columns[2]
        
    gxt_col = None
    if len(df.columns) > 8:
        gxt_col = df.columns[8]
    
    if gxt_col:
        for idx, row in df.iterrows():
            val = str(row[gxt_col]).strip().upper()
            if val == 'GXT':
                s_name = str(row[name_col]).strip()
                if s_name and s_name != 'nan':
                    gxt_stores.append(s_name)
                    
    with open("gxt_stores.js", "w", encoding="utf-8") as f:
        f.write(f"const GXT_STORE_LIST = {json.dumps(gxt_stores, ensure_ascii=False, indent=2)};\n")
        
    print(f"Extracted {len(gxt_stores)} stores.")
except Exception as e:
    print("Error")
