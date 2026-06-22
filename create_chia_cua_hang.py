import pandas as pd

master_path = r'g:\My Drive\Training AI\Supra Phú Thọ\DS_Winmart_Extracted.xlsx'
source_path = r'g:\My Drive\Training AI\Supra Phú Thọ\Danh sách Winmart (1).xlsx'
out_path = r'g:\My Drive\Training AI\Supra Phú Thọ\ChiaCuaHang.xlsx'

print("Loading data...")
df_master = pd.read_excel(master_path)
df_source = pd.read_excel(source_path)

col_name = 'Tên cửa hàng'
col_I = df_source.columns[8]  # Loại kho giao (OM đánh giá)

print("Building GXT mapping...")
gxt_set = set()

# Process source file to find all GXT stores
for _, row in df_source.iterrows():
    name = str(row[col_name]).strip()
    val = str(row[col_I]).strip().upper()
    if pd.notna(row[col_name]) and name != '' and name.lower() != 'nan':
        if val == 'GXT':
            gxt_set.add(name.lower())

print(f"Found {len(gxt_set)} stores marked as GXT.")

print("Creating ChiaCuaHang dataset...")
result = []
for name in df_master['Tên cửa hàng']:
    clean_name = str(name).strip()
    if clean_name.lower() in gxt_set:
        bo_phan = "GXT"
    else:
        bo_phan = "Giao thẳng"
    
    result.append({
        'Tên cửa hàng': clean_name,
        'Bộ phận': bo_phan
    })

df_out = pd.DataFrame(result)
# Remove duplicates if any
df_out = df_out.drop_duplicates(subset=['Tên cửa hàng'])

df_out.to_excel(out_path, index=False)
print(f"Successfully saved {len(df_out)} stores to {out_path}")
