import json

with open('booking_data.js', 'r', encoding='utf-8') as f:
    content = f.read()
    json_str = content.split('=', 1)[1].strip()
    if json_str.endswith(';'): json_str = json_str[:-1]
    data = json.loads(json_str)
    
with open('out.txt', 'w', encoding='utf-8') as fw:
    for p in data:
        if 'WM VC+' in p['name']:
            fw.write(f"{p['name']} | {p['address']} | {p['province']}\n")
