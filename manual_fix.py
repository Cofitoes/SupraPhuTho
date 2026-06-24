def manual_fix(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
    except UnicodeDecodeError:
        with open(filepath, 'r', encoding='windows-1252') as f:
            content = f.read()

    lines = content.split('\n')
    out = []
    i = 0
    while i < len(lines):
        line = lines[i]
        
        if "<!-- 1." in line and "ConCung" in line:
            out.append('                                <!-- 1. Chọn Ngày -->')
            i += 1
            continue
            
        if "incident-concung-code" in line or "ConCung</label>" in line or "Đơn ConCung" in line or "?n ConCung" in line:
            i += 1
            continue
            
        if "window.GlobalConcungMap =" in line:
            i += 7
            continue
            
        if "concung_data.js" in line:
            i += 1
            continue
            
        if "if (typeof concungData !== 'undefined')" in line and i+1 < len(lines) and "const b = p.buff" in lines[i+1]:
            i += 9
            continue
            
        if "} else if (searchName && typeof concungData !== 'undefined') {" in line:
            out.append(line[:line.find("}") + 1])
            i += 6
            continue
            
        if "} else if (b && typeof concungData !== 'undefined') {" in line:
            out.append(line[:line.find("}") + 1])
            i += 6
            continue
            
        if "concungCodeVal =" in line or "concungCode:" in line or "item.concungCode" in line or "<th>Mã Đơn ConCung</th>" in line or "<th>MA `n ConCung</th>" in line:
            i += 1
            continue
            
        if "if (typeof concungData !== 'undefined')" in line and i+1 < len(lines) and "allData = allData.concat" in lines[i+1]:
            i += 3
            continue

        line = line.replace("<title>Logistics Hub | Quản lý vận hành</title>", "<title>Supra Phú Thọ | Quản Lý Vận Tải Thông Minh</title>")
        line = line.replace("<title>Logistics Hub | Qun lA? v-n hAnh</title>", "<title>Supra Phú Thọ | Quản Lý Vận Tải Thông Minh</title>")
        line = line.replace("Logistics Hub Manager", "GHN Manager")
        line = line.replace("Logistics Hub Staff", "GHN Staff")
        line = line.replace("logistics_local_users", "supra_local_users")
        line = line.replace("logistics_incidents", "supra_incidents")
        line = line.replace("logisticsupdate://", "supraupdate://")

        out.append(line)
        i += 1

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write('\n'.join(out))

manual_fix('index.html')
manual_fix('demo.html')
