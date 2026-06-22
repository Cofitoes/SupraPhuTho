import pandas as pd

file_path = r'g:\My Drive\Training AI\Supra Phú Thọ\Danh sách Winmart (1).xlsx'
out_path = r'g:\My Drive\Training AI\Supra Phú Thọ\inspect_out.txt'

df = pd.read_excel(file_path)
col_I = df.columns[8]

with open(out_path, 'w', encoding='utf-8') as f:
    f.write(f"Column I name: {col_I}\n")
    unique_vals = df[col_I].dropna().unique()
    f.write(f"Unique values: {unique_vals[:20]}\n")
    
    gxt_stores = df[df[col_I].astype(str).str.contains('GXT', case=False, na=False)]['Tên cửa hàng'].head(10).tolist()
    f.write(f"Sample GXT stores: {gxt_stores}\n")
