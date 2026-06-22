import pandas as pd
import numpy as np

existing_path = r'g:\My Drive\Training AI\Supra Phú Thọ\DS_Winmart_Extracted.xlsx'
new_path = r'g:\My Drive\Training AI\Supra Phú Thọ\Danh sách Winmart (1).xlsx'

print("Loading existing stores...")
df_existing = pd.read_excel(existing_path)
existing_names = set(df_existing['Tên cửa hàng'].astype(str).str.strip().str.lower())
print(f"Existing stores: {len(existing_names)}")

print("Loading new file...")
df_new = pd.read_excel(new_path)

new_stores = []

def extract_from_cols(name_col, addr_col, prov_col, lat_col=None, lon_col=None):
    if name_col not in df_new.columns:
        return
    for _, row in df_new.iterrows():
        name = str(row[name_col]).strip()
        if pd.isna(row[name_col]) or name == '' or name.lower() == 'nan':
            continue
        
        if name.lower() not in existing_names:
            addr = row[addr_col] if addr_col in df_new.columns and not pd.isna(row[addr_col]) else ''
            prov = row[prov_col] if prov_col in df_new.columns and not pd.isna(row[prov_col]) else ''
            lat = row[lat_col] if lat_col in df_new.columns and not pd.isna(row[lat_col]) else ''
            lon = row[lon_col] if lon_col in df_new.columns and not pd.isna(row[lon_col]) else ''
            
            coord = ''
            if lat != '' and lon != '':
                coord = f"{lat}, {lon}"
            
            new_stores.append({
                'Tên cửa hàng': name,
                'Mã cửa hàng (Mã SAP)': '',
                'Mã cửa hàng (Mã CH)': '',
                'Địa chỉ': addr,
                'Quận/Huyện/Xã': '',
                'Thành Phố/Tỉnh': prov,
                'Vị trí Lat/Long': coord
            })
            existing_names.add(name.lower())

# Extract from Group 1
extract_from_cols('Tên cửa hàng', 'địa chỉ', 'Tỉnh giao', 'Lat', 'Long')

# Extract from Group 2
extract_from_cols('Customer Name', 'Địa Chỉ', 'Tỉnh')

# Extract from Group 3
extract_from_cols('Customer Name.1', 'Địa chỉ', 'tỉnh')

print(f"Found {len(new_stores)} new stores.")

if len(new_stores) > 0:
    df_new_stores = pd.DataFrame(new_stores)
    # Align columns
    for col in df_existing.columns:
        if col not in df_new_stores.columns:
            df_new_stores[col] = ''
    df_new_stores = df_new_stores[df_existing.columns]
    
    df_combined = pd.concat([df_existing, df_new_stores], ignore_index=True)
    df_combined.to_excel(existing_path, index=False)
    print("Appended new stores and saved to existing file.")
else:
    print("No new stores to add.")

