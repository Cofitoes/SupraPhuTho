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

    # Helper matching checkIsGXTStore
    def is_gxt(p):
        pid = p.get('id', '').strip().lower()
        name = p.get('name', '').strip().lower()
        for s in stores:
            sid = s.get('id', '').strip().lower()
            sname = s.get('name', '').strip().lower()
            if (pid and sid == pid) or (sname == name or sname in name or name in sname):
                return s.get('isGXT') == True or s.get('trip_type') == 'GXT'
        return any(gn in name or name in gn for gn in gxt_names)

    stores_db = {}
    for s in stores:
        sid = s.get('id', '').strip().lower()
        sname = s.get('name', '').strip().lower()
        sdist = s.get('district', '')
        if sid: stores_db[sid] = sdist
        if sname: stores_db[sname] = sdist

    def getDistrictForPoint(p):
        name = p.get('name', '').strip().lower()
        pid = p.get('id', '').strip().lower()
        if pid in stores_db: return stores_db[pid]
        if name in stores_db: return stores_db[name]
        return ''

    routeGroups = [
        {"name": "Tuyến 1: Thanh Thủy - Thanh Sơn", "districts": ["H. Thanh Thủy", "H. Thanh Sơn"]},
        {"name": "Tuyến 2: Yên Lập - Cẩm Khê", "districts": ["H. Yên Lập", "H. Cẩm Khê"]},
        {"name": "Tuyến 3: Tam Nông - Lâm Thao", "districts": ["H. Tam Nông", "H. Lâm Thao"]},
        {"name": "Tuyến 4: Đoan Hùng - Phù Ninh", "districts": ["H. Đoan Hùng", "H. Phù Ninh"]},
        {"name": "Tuyến 5: Hạ Hòa - Thanh Ba", "districts": ["H. Hạ Hoà", "H. Hạ Hòa", "H. Thanh Ba"]}
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

    # 4. Target Date 2026-06-29
    pts_d = [p for p in points if p.get('date') == '2026-06-29']
    direct_pts = [p for p in pts_d if not is_gxt(p)]

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

    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("=== ROUTE GROUP COUNTS WITH EXACT GXT FILTER ===\n")
        log.write(f"Total direct points = {len(direct_pts)}\n")
        for g in groups:
            w = g['totalWeight']
            v = sum(p.get('volume', 0) for p in g['points'])
            log.write(f"  {g['name']}: {len(g['points'])} stores, Weight = {w}kg, Volume = {v:.2f}m3\n")

        # Now simulate merge check for Yên Lập - Cẩm Khê (Group with 4 stores!)
        gA = next((g for g in groups if "Yên Lập - Cẩm Khê" in g['name']), None)
        if gA:
            log.write(f"\nAnalyzing Group A: {gA['name']} ({len(gA['points'])} stores)\n")
            distA = getGroupDistance(gA['points'])
            costA = getTripCostDetails('1.9T', distA, gA['totalWeight'])
            log.write(f"  Original dist A: {distA} km, Cost: {costA:,} VND\n\n")

            for gB in groups:
                if gA['name'] == gB['name']: continue
                combined = gB['points'] + gA['points']
                c_w = gA['totalWeight'] + gB['totalWeight']
                c_v = sum(p.get('volume', 0) for p in combined)
                
                truck = ''
                if c_w <= 2090 and c_v <= 14:
                    truck = '1.9T'
                elif c_w <= 5500 and c_v <= 26:
                    truck = '5T'
                
                log.write(f"Checking Partner: {gB['name']}\n")
                log.write(f"  Combined Weight: {c_w:.2f}kg, Combined Vol: {c_v:.2f}m3\n")
                if not truck:
                    log.write("  -> REJECTED: Exceeds 5T capacity limit.\n\n")
                    continue
                    
                distCombined = getGroupDistance(combined)
                costCombined = getTripCostDetails(truck, distCombined, c_w)
                
                distB = getGroupDistance(gB['points'])
                volB = sum(p.get('volume', 0) for p in gB['points'])
                origTruckB = '1.9T'
                if gB['totalWeight'] > 2090 or volB > 14: origTruckB = '5T'
                costB = getTripCostDetails(origTruckB, distB, gB['totalWeight'])
                
                costIncrease = costCombined - costB
                log.write(f"  Combined Dist: {distCombined} km, Combined Cost ({truck}): {costCombined:,} VND\n")
                log.write(f"  Original Dist B: {distB} km, Original Cost B ({origTruckB}): {costB:,} VND\n")
                log.write(f"  Cost Increase (Combined - B): {costIncrease:,} VND\n")
                if costIncrease <= 1300000:
                    log.write("  -> VALID FOR MERGE! (<= 1,300,000 VND)\n\n")
                else:
                    log.write("  -> REJECTED: Cost increase exceeds 1,300,000 VND limit.\n\n")

except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"ERROR: {e}\n")
