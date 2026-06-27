import re
import json
import os

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"

try:
    # 1. Read store data
    store_path = r"g:\My Drive\Training AI\Supra Phú Thọ\store_data.js"
    with open(store_path, 'r', encoding='utf-8') as f:
        store_content = f.read()
    
    store_json_match = re.search(r'STORE_LIST_DATA\s*=\s*(\[[\s\S]*?\]);', store_content)
    stores = json.loads(store_json_match.group(1))
    
    stores_db = {}
    for s in stores:
        sid = s.get('id', '').strip().lower()
        sname = s.get('name', '').strip().lower()
        if sid: stores_db[sid] = s
        if sname: stores_db[sname] = s

    # 2. Read booking data
    booking_path = r"g:\My Drive\Training AI\Supra Phú Thọ\booking_data.js"
    with open(booking_path, 'r', encoding='utf-8') as f:
        booking_content = f.read()

    match = re.search(r'BOOKING_DELIVERY_POINTS\s*=\s*(\[[\s\S]*?\]);', booking_content)
    js_array = match.group(1)
    js_array_clean = re.sub(r'//.*', '', js_array)
    js_array_clean = re.sub(r',\s*\]', ']', js_array_clean)
    js_array_clean = re.sub(r',\s*\}', '}', js_array_clean)
    js_array_clean = re.sub(r'(\w+)\s*:', r'"\1":', js_array_clean)
    js_array_clean = js_array_clean.replace("'", '"')
    points = json.loads(js_array_clean)

    pts_29 = [p for p in points if p.get('date') == '2026-06-29']

    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"=== ANALYSIS OF 2026-06-29 POINTS (Total in booking: {len(pts_29)}) ===\n")
        
        has_coords = 0
        gxt_count = 0
        direct_count = 0
        
        for p in pts_29:
            pid = p.get('id', '').strip().lower()
            name = p.get('name', '').strip().lower()
            
            # Resolve store
            store = None
            if pid in stores_db: store = stores_db[pid]
            elif name in stores_db: store = stores_db[name]
            
            # Resolve coordinates
            coords = None
            if store and store.get('coords') and store['coords'].get('lat') and store['coords'].get('lng'):
                coords = store['coords']
            elif p.get('coords') and p['coords'].get('lat') and p['coords'].get('lng'):
                coords = p['coords']
                
            if coords:
                has_coords += 1
                # Check if GXT
                is_gxt = False
                if store:
                    is_gxt = store.get('isGXT') == True or store.get('trip_type') == 'GXT'
                else:
                    is_gxt = p.get('isGXT') == True
                
                if is_gxt:
                    gxt_count += 1
                else:
                    direct_count += 1
                    
        log.write(f"Points with valid coordinates: {has_coords}\n")
        log.write(f"  GXT points: {gxt_count}\n")
        log.write(f"  Direct points: {direct_count}\n")

except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"ERROR: {e}\n")
