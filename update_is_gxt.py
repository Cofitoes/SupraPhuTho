import pandas as pd
import json
import sys

sys.stdout.reconfigure(encoding='utf-8')

def main():
    # Load Excel
    df = pd.read_excel('DSCuaHangFinal.xlsx')
    
    # Create mapping: Store_ID -> isGXT (boolean)
    # Trip_Type has 'GXT' or 'Giao Thang'
    mapping = {}
    for idx, row in df.iterrows():
        store_id = str(row['Store_ID']).strip()
        trip_type = str(row['Trip_Type']).strip()
        mapping[store_id] = (trip_type == 'GXT')
    
    # Read store_data.js
    with open('store_data.js', 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Parse JSON from store_data.js
    prefix = 'const STORE_LIST_DATA = '
    start_idx = content.find(prefix)
    if start_idx == -1:
        print("Could not find STORE_LIST_DATA declaration in store_data.js")
        return
        
    start_idx += len(prefix)
    end_idx = content.rfind(';')
    if end_idx == -1:
        end_idx = len(content)
        
    json_str = content[start_idx:end_idx].strip()
    try:
        stores = json.loads(json_str)
    except Exception as e:
        print(f"Error parsing JSON from store_data.js: {e}")
        return
        
    # Update isGXT
    updated_count = 0
    not_found_in_excel = 0
    
    for store in stores:
        sid = str(store.get('id', '')).strip()
        if sid in mapping:
            store['isGXT'] = mapping[sid]
            updated_count += 1
        else:
            not_found_in_excel += 1
            
    # Write back to store_data.js
    new_json_str = json.dumps(stores, indent=4, ensure_ascii=False)
    new_content = content[:start_idx] + new_json_str + ';\n'
    
    with open('store_data.js', 'w', encoding='utf-8') as f:
        f.write(new_content)
        
    print(f"Successfully updated store_data.js!")
    print(f"Updated {updated_count} stores based on DSCuaHangFinal.xlsx")
    print(f"{not_found_in_excel} stores in store_data.js were not found in the Excel file.")

if __name__ == "__main__":
    main()
