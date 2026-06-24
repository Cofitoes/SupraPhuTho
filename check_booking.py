import json
import sys
sys.stdout.reconfigure(encoding='utf-8')
with open('booking_data.js', 'r', encoding='utf-8') as f:
    text = f.read().replace('const BOOKING_DELIVERY_POINTS = ', '').strip()
    if text.endswith(';'): text = text[:-1]
    booking_data = json.loads(text)

with open('store_data.js', 'r', encoding='utf-8') as f:
    text = f.read().replace('const STORE_LIST_DATA = ', '').strip()
    if text.endswith(';'): text = text[:-1]
    store_data = json.loads(text)

store_dict = {s['id']: s for s in store_data}
store_name_dict = {s['name']: s for s in store_data}

seen = set()
for b in booking_data:
    b_id = b['id']
    if b_id not in store_dict:
        store = store_name_dict.get(b['name'])
        if store and str(store['id']) != str(b_id):
            key = f"{b_id}-{store['id']}"
            if key not in seen:
                print(f"Booking ID: {b_id}, Store ID: {store['id']}, Name: {b['name']}")
                seen.add(key)
