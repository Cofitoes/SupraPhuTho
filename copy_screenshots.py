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
        sdist = s.get('district', '')
        if sid: stores_db[sid] = sdist
        if sname: stores_db[sname] = sdist

    # Read gxt stores
    gxt_path = r"g:\My Drive\Training AI\Supra Phú Thọ\gxt_stores.js"
    with open(gxt_path, 'r', encoding='utf-8') as f:
        gxt_content = f.read()
    gxt_names = [n.strip().lower() for n in re.findall(r'"([^"]+)"', gxt_content) if n.strip()]

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

    # 3. Helpers
    def calculateDistance(c1, c2):
        if not c1 or not c2: return 0
        from math import sin, cos, atan2, sqrt, pi
        R = 6371
        dLat = (c2['lat'] - c1['lat']) * pi / 180
        dLng = (c2['lng'] - c1['lng']) * pi / 180
        a = sin(dLat/2)**2 + cos(c1['lat'] * pi / 180) * cos(c2['lat'] * pi / 180) * sin(dLng/2)**2
        return R * 2 * atan2(sqrt(a), sqrt(1-a))

    hubDC = {'coords': {'lat': 21.3879985, 'lng': 105.1803274}}

    def getDistrictForPoint(p):
        name = p.get('name', '').strip().lower()
        pid = p.get('id', '').strip().lower()
        if pid in stores_db: return stores_db[pid]
        if name in stores_db: return stores_db[name]
        return ''

    routeGroups = [
        {"name": "Tuyến 1", "districts": ["H. Thanh Thủy", "H. Thanh Sơn"]},
        {"name": "Tuyến 2", "districts": ["H. Yên Lập", "H. Cẩm Khê"]},
        {"name": "Tuyến 3", "districts": ["H. Tam Nông", "H. Lâm Thao"]},
        {"name": "Tuyến 4", "districts": ["H. Đoan Hùng", "H. Phù Ninh"]},
        {"name": "Tuyến 5", "districts": ["H. Hạ Hoà", "H. Hạ Hòa", "H. Thanh Ba"]}
    ]

    def solveTSP(hub, pts):
        unvisited = list(pts)
        curr = hub
        seq = []
        while unvisited:
            best_idx = 0
            best_d = 9999999
            for idx, p in enumerate(unvisited):
                d = calculateDistance(curr['coords'], p['coords'])
                if d < best_d:
                    best_d = d
                    best_idx = idx
            curr = unvisited.pop(best_idx)
            seq.append(curr)
        return seq

    def getGroupDistance(pts):
        if not pts: return 0
        seq = solveTSP(hubDC, pts)
        dist = 0
        last = hubDC
        for p in seq:
            dist += calculateDistance(last['coords'], p['coords'])
            last = p
        dist += calculateDistance(last['coords'], hubDC['coords'])
        return round(dist * 1.4, 2)

    def getTripCostDetails(truckType, dist, weight):
        if truckType == '1.9T':
            base = 1700000
            extra = 0
            if dist > 120:
                extra = (dist - 120) * 11000
            return base + extra
        else:
            if dist <= 50:
                return 1100000
            elif dist <= 100:
                return 2400000
            elif dist <= 150:
                return 3000000
            else:
                return 3000000 + (dist - 150) * 20000

    all_dates = sorted(list(set(p.get('date') for p in points if p.get('date'))))

    report = []
    for d in all_dates:
        pts_d = [p for p in points if p.get('date') == d]
        
        def is_gxt(p):
            name = p.get('name', '').strip().lower()
            return p.get('isGXT') == True or any(gn in name for gn in gxt_names)

        direct_pts = [p for p in pts_d if not is_gxt(p)]
        if not direct_pts:
            continue

        groups = []
        for rg in routeGroups:
            g_pts = []
            for p in direct_pts:
                p_dist = getDistrictForPoint(p)
                if not p_dist: continue
                match_rg = False
                for dist in rg['districts']:
                    n_dist = re.sub(r'^(h\.|tp\.)\s*', '', dist.lower()).strip()
                    n_pdist = re.sub(r'^(h\.|tp\.)\s*', '', p_dist.lower()).strip()
                    if n_dist == n_pdist:
                        match_rg = True
                        break
                if match_rg:
                    g_pts.append(p)
            
            if g_pts:
                groups.append({
                    'name': rg['name'],
                    'points': g_pts,
                    'totalWeight': sum(p.get('weight', 0) for p in g_pts)
                })

        if not groups:
            continue

        # SIMULATE ORIGINAL PACKING (No Merges)
        orig_trips = []
        for g in groups:
            pts = list(g['points'])
            while pts:
                chunk = []
                cw, cv = 0, 0
                truck = '1.9T'
                i = 0
                while i < len(pts):
                    p = pts[i]
                    p_w = p.get('weight', 0)
                    p_v = p.get('volume', 0)
                    if cw + p_w <= 2090 and cv + p_v <= 14:
                        chunk.append(pts.pop(i))
                        cw += p_w
                        cv += p_v
                    elif cw + p_w <= 5500 and cv + p_v <= 26:
                        truck = '5T'
                        chunk.append(pts.pop(i))
                        cw += p_w
                        cv += p_v
                    else:
                        i += 1
                if not chunk:
                    p = pts.pop(0)
                    chunk.append(p)
                    cw += p.get('weight', 0)
                    cv += p.get('volume', 0)
                    truck = '5T'
                orig_trips.append({'points': chunk, 'truck': truck, 'weight': cw, 'volume': cv, 'group_name': g['name']})

        orig_cost = 0
        for ot in orig_trips:
            dist = getGroupDistance(ot['points'])
            orig_cost += getTripCostDetails(ot['truck'], dist, ot['weight'])

        # SIMULATE NEW MERGING PACKING
        merged_groups = []
        for g in groups:
            merged_groups.append({
                'name': g['name'],
                'points': list(g['points']),
                'totalWeight': g['totalWeight']
            })
            
        isSmall = lambda g: len(g['points']) <= 2 and g['totalWeight'] <= 1200 and sum(p.get('volume', 0) for p in g['points']) <= 3.5
        
        mergedAny = True
        while mergedAny:
            mergedAny = False
            merged_groups.sort(key=lambda x: x['totalWeight'])
            for i, gA in enumerate(merged_groups):
                if not isSmall(gA): continue
                bestPartnerIdx = -1
                bestCostIncrease = 99999999
                
                for j, gB in enumerate(merged_groups):
                    if i == j: continue
                    combined = gB['points'] + gA['points']
                    c_w = gA['totalWeight'] + gB['totalWeight']
                    c_v = sum(p.get('volume', 0) for p in combined)
                    
                    truck = ''
                    if c_w <= 2090 and c_v <= 14:
                        truck = '1.9T'
                    elif c_w <= 5500 and c_v <= 26:
                        truck = '5T'
                        
                    if not truck: continue
                    
                    distCombined = getGroupDistance(combined)
                    costCombined = getTripCostDetails(truck, distCombined, c_w)
                    
                    distB = getGroupDistance(gB['points'])
                    volB = sum(p.get('volume', 0) for p in gB['points'])
                    origTruckB = '1.9T'
                    if gB['totalWeight'] > 2090 or volB > 14: origTruckB = '5T'
                    costB = getTripCostDetails(origTruckB, distB, gB['totalWeight'])
                    
                    costIncrease = costCombined - costB
                    if costIncrease <= 1300000 and costIncrease < bestCostIncrease:
                        bestCostIncrease = costIncrease
                        bestPartnerIdx = j
                
                if bestPartnerIdx != -1:
                    gB = merged_groups[bestPartnerIdx]
                    gB['points'] = gB['points'] + gA['points']
                    gB['totalWeight'] += gA['totalWeight']
                    gB['name'] = gB['name'] + " + " + gA['name']
                    merged_groups.pop(i)
                    mergedAny = True
                    break

        new_trips = []
        for g in merged_groups:
            pts = list(g['points'])
            while pts:
                chunk = []
                cw, cv = 0, 0
                truck = '1.9T'
                i = 0
                while i < len(pts):
                    p = pts[i]
                    p_w = p.get('weight', 0)
                    p_v = p.get('volume', 0)
                    if cw + p_w <= 2090 and cv + p_v <= 14:
                        chunk.append(pts.pop(i))
                        cw += p_w
                        cv += p_v
                    elif cw + p_w <= 5500 and cv + p_v <= 26:
                        truck = '5T'
                        chunk.append(pts.pop(i))
                        cw += p_w
                        cv += p_v
                    else:
                        i += 1
                if not chunk:
                    p = pts.pop(0)
                    chunk.append(p)
                    cw += p.get('weight', 0)
                    cv += p.get('volume', 0)
                    truck = '5T'
                new_trips.append({'points': chunk, 'truck': truck, 'weight': cw, 'volume': cv, 'group_name': g['name']})

        new_cost = 0
        for nt in new_trips:
            dist = getGroupDistance(nt['points'])
            new_cost += getTripCostDetails(nt['truck'], dist, nt['weight'])

        if len(orig_trips) != len(new_trips) or orig_cost != new_cost:
            report.append({
                'date': d,
                'old_trips': len(orig_trips),
                'old_trucks': [ot['truck'] for ot in orig_trips],
                'new_trips': len(new_trips),
                'new_trucks': [nt['truck'] for nt in new_trips],
                'new_names': [nt['group_name'] for nt in new_trips],
                'savings': orig_cost - new_cost
            })

    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("=== ROUTE COMBINING IMPACT REPORT ===\n")
        log.write(f"Total dates with changed routes: {len(report)}\n\n")
        for r in report:
            log.write(f"Date: {r['date']}\n")
            log.write(f"  Old Trips: {r['old_trips']} ({r['old_trucks']})\n")
            log.write(f"  New Trips: {r['new_trips']} ({r['new_trucks']})\n")
            log.write(f"  Merged Routes: {r['new_names']}\n")
            log.write(f"  Savings: {r['savings']:,} VND\n\n")

except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"ERROR: {e}\n")
