import pandas as pd
import json

def main():
    df = pd.read_excel('DSCuaHangFinal.xlsx')
    df = df.fillna('')
    
    stores = []
    for _, row in df.iterrows():
        store_id = str(row.get('Store_ID', '')).strip()
        name = str(row.get('Store_Name', '')).strip()
        address = str(row.get('Address', '')).strip()
        district = str(row.get('District', '')).strip()
        province = str(row.get('Province', '')).strip()
        
        trip_type = str(row.get('Trip_Type', '')).strip()
        is_gxt = trip_type.upper() == 'GXT'
        
        lat = row.get('Lat', '')
        lng = row.get('Lng', '')
        
        if not store_id and not name:
            continue
            
        store_obj = {
            "id": store_id,
            "name": name,
            "address": address,
            "district": district,
            "province": province,
            "isGXT": is_gxt
        }
        
        if lat and lng:
            try:
                store_obj["coords"] = {"lat": float(lat), "lng": float(lng)}
            except:
                pass
                
        stores.append(store_obj)
        
    js_content = f"const STORE_LIST_DATA = {json.dumps(stores, ensure_ascii=False, indent=4)};\n"
    
    with open('store_data.js', 'w', encoding='utf-8') as f:
        f.write(js_content)
        
    print(f"Created store_data.js with {len(stores)} stores.")

if __name__ == "__main__":
    main()
