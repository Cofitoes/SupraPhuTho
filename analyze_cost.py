"""
Cost Optimization Analysis Script
Analyzes all historical booking data and simulates different routing strategies
to find the lowest cost approach for direct deliveries.
"""
import json, math, re, os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def parse_js_array(filepath, var_name):
    with open(filepath, 'r', encoding='utf-8') as f:
        raw = f.read()
    pattern = re.compile(r'(?:const|var|let)\s+' + var_name + r'\s*=\s*')
    m = pattern.search(raw)
    if not m:
        return []
    start = m.end()
    depth = 0
    i = start
    while i < len(raw):
        if raw[i] in '[{':
            depth += 1
        elif raw[i] in ']}':
            depth -= 1
            if depth == 0:
                i += 1
                break
        i += 1
    return json.loads(raw[start:i])

BOOKING_POINTS = parse_js_array(os.path.join(BASE_DIR, 'booking_data.js'), 'BOOKING_DELIVERY_POINTS')
STORE_LIST = parse_js_array(os.path.join(BASE_DIR, 'store_data.js'), 'STORE_LIST_DATA')
GXT_STORE_LIST = parse_js_array(os.path.join(BASE_DIR, 'gxt_stores.js'), 'GXT_STORE_LIST')

TRUCK_LIMITS = {
    '1.9T': {'maxW': 1900, 'maxWA': 2090, 'maxV': 14},
    '5T':   {'maxW': 5000, 'maxWA': 5500, 'maxV': 26},
    '8T':   {'maxW': 6800, 'maxWA': 7480, 'maxV': 55},
}
HUB_DC = {'lat': 21.3879985, 'lng': 105.1803274}
HUB_GXT = {'lat': 21.3264875, 'lng': 105.3246094}

def trip_cost(truck, dist_km, weight_kg, trip_type='GT'):
    cfg = {
        '1.9T': {'minKm': 120, 'base': 1700000, 'extra': 11000},
        '5T':   {'rates': [1100000, 2400000, 3000000], 'extra': 20000},
        '8T':   {'rates': [1500000, 3000000, 4200000], 'extra': 22000},
    }
    c = cfg[truck]
    base = extra = loading = 0
    if truck == '1.9T':
        base = c['base']
        if dist_km > c['minKm']:
            extra = c['extra'] * (dist_km - c['minKm'])
    else:
        r = c['rates']
        if dist_km <= 50: base = r[0]
        elif dist_km <= 100: base = r[1]
        elif dist_km <= 150: base = r[2]
        else: base = r[2]; extra = c['extra'] * (dist_km - 150)
    if trip_type == 'TC':
        loading = (weight_kg or 0) * 200
    return round(base + extra + loading)

def haversine(a, b):
    R = 6371
    dLat = math.radians(b['lat'] - a['lat'])
    dLng = math.radians(b['lng'] - a['lng'])
    sl = math.sin(dLat / 2)
    sn = math.sin(dLng / 2)
    h = sl*sl + math.cos(math.radians(a['lat'])) * math.cos(math.radians(b['lat'])) * sn*sn
    return R * 2 * math.atan2(math.sqrt(h), math.sqrt(1 - h))

def tsp_nn(hub, points):
    unvisited = list(points)
    current = hub
    total_dist = 0
    while unvisited:
        min_d, ni = float('inf'), 0
        for i, p in enumerate(unvisited):
            d = haversine(current, p['coords'])
            if d < min_d:
                min_d = d; ni = i
        total_dist += min_d
        current = unvisited[ni]['coords']
        unvisited.pop(ni)
    if points:
        total_dist += haversine(current, hub)
    return round(total_dist, 2)

_store_cache = {}
def _build_store_cache():
    for s in STORE_LIST:
        if s.get('id'): _store_cache[s['id']] = s
        if s.get('name'): _store_cache[s['name']] = s
_build_store_cache()

def is_gxt(p):
    if p.get('isGXT') is True: return True
    if p.get('isGXT') is False: return False
    store = _store_cache.get(p.get('id')) or _store_cache.get(p.get('name'))
    if store and 'isGXT' in store:
        return store['isGXT']
    pn = p.get('name', '').strip().lower()
    for gn in GXT_STORE_LIST:
        gn_l = gn.strip().lower()
        if gn_l == pn or gn_l in pn or pn in gn_l:
            return True
    return False

def get_district(p):
    store = _store_cache.get(p.get('id')) or _store_cache.get(p.get('name'))
    if store and store.get('district'):
        return store['district']
    addr = p.get('address', '')
    parts = [x.strip() for x in addr.split(',') if x.strip()]
    return parts[0] if parts else ''

ROUTE_GROUPS = [
    ("Thanh Thuy - Thanh Son", ["thanh thủy", "thanh sơn"]),
    ("Yen Lap - Cam Khe", ["yên lập", "cẩm khê"]),
    ("Tam Nong - Lam Thao", ["tam nông", "lâm thao"]),
    ("Doan Hung - Phu Ninh", ["đoan hùng", "phù ninh"]),
    ("Ha Hoa - Thanh Ba", ["hạ hoà", "hạ hòa", "thanh ba"]),
]

def match_route(district):
    nd = re.sub(r'^(h\.|tp\.|tx\.)\s*', '', district.lower()).strip()
    for name, districts in ROUTE_GROUPS:
        for d in districts:
            if d == nd:
                return name
    return 'Khac'

def pack_trips(points, truck_type):
    lim = TRUCK_LIMITS[truck_type]
    remaining = list(points)
    trips = []
    while remaining:
        chunk = []
        cw = cv = 0
        i = 0
        while i < len(remaining):
            p = remaining[i]
            pw = p.get('weight', 0) or 0
            pv = p.get('volume', 0) or 0
            if cw + pw <= lim['maxWA'] and cv + pv <= lim['maxV']:
                chunk.append(p)
                cw += pw; cv += pv
                remaining.pop(i)
            else:
                i += 1
        if not chunk and remaining:
            p = remaining.pop(0)
            chunk.append(p)
            cw = p.get('weight', 0) or 0
            cv = p.get('volume', 0) or 0
        dist = tsp_nn(HUB_DC, chunk)
        cost = trip_cost(truck_type, dist, cw)
        fill = cw / lim['maxWA'] if lim['maxWA'] else 0
        trips.append({'truck': truck_type, 'w': cw, 'v': cv, 'dist': dist, 'cost': cost, 'n': len(chunk), 'fill': fill, 'points': chunk})
    return trips

# ========== STRATEGIES ==========

def group_by_route(pts):
    groups = {}
    for p in pts:
        g = match_route(get_district(p))
        groups.setdefault(g, []).append(p)
    return groups

def S1_current(pts):
    """Current: 1.9T grouped by route"""
    all_t = []
    for gpts in group_by_route(pts).values():
        all_t.extend(pack_trips(gpts, '1.9T'))
    return all_t

def S2_19t_nogroup(pts):
    """All 1.9T, no grouping"""
    return pack_trips(pts, '1.9T')

def S3_5t_grouped(pts):
    """All 5T, grouped by route"""
    all_t = []
    for gpts in group_by_route(pts).values():
        all_t.extend(pack_trips(gpts, '5T'))
    return all_t

def S4_mixed_weight(pts):
    """5T for heavy routes (>3T), 1.9T for light"""
    all_t = []
    for gpts in group_by_route(pts).values():
        tw = sum(p.get('weight', 0) or 0 for p in gpts)
        all_t.extend(pack_trips(gpts, '5T' if tw > 3000 else '1.9T'))
    return all_t

def S5_smart_mixed(pts):
    """Compare 1.9T vs 5T cost per route, pick cheaper"""
    all_t = []
    for gpts in group_by_route(pts).values():
        t19 = pack_trips(gpts, '1.9T')
        t5 = pack_trips(gpts, '5T')
        c19 = sum(t['cost'] for t in t19)
        c5 = sum(t['cost'] for t in t5)
        all_t.extend(t5 if c5 < c19 else t19)
    return all_t

def S6_5t_nogroup(pts):
    """All 5T, no grouping"""
    return pack_trips(pts, '5T')

def S7_geo_cluster_5t(pts):
    """Geographic clustering with 5T"""
    remaining = list(pts)
    trips = []
    lim = TRUCK_LIMITS['5T']
    while remaining:
        # Start from furthest point
        max_d, si = -1, 0
        for i, p in enumerate(remaining):
            d = haversine(HUB_DC, p['coords'])
            if d > max_d: max_d = d; si = i
        chunk = [remaining.pop(si)]
        cw = chunk[0].get('weight', 0) or 0
        cv = chunk[0].get('volume', 0) or 0
        while remaining:
            last = chunk[-1]
            ni, nd = -1, float('inf')
            for i, p in enumerate(remaining):
                pw = p.get('weight', 0) or 0
                pv = p.get('volume', 0) or 0
                if cw + pw <= lim['maxWA'] and cv + pv <= lim['maxV']:
                    d = haversine(last['coords'], p['coords'])
                    if d < nd: nd = d; ni = i
            if ni == -1 or nd > 25: break
            p = remaining.pop(ni)
            chunk.append(p)
            cw += p.get('weight', 0) or 0
            cv += p.get('volume', 0) or 0
        dist = tsp_nn(HUB_DC, chunk)
        trips.append({'truck': '5T', 'w': cw, 'v': cv, 'dist': dist, 'cost': trip_cost('5T', dist, cw), 'n': len(chunk), 'fill': cw / lim['maxWA']})
    return trips

def S8_hybrid_merge(pts):
    """Smart per route + re-pack leftovers together"""
    all_t = []
    leftovers = []
    for gpts in group_by_route(pts).values():
        t19 = pack_trips(gpts, '1.9T')
        t5 = pack_trips(gpts, '5T')
        c19 = sum(t['cost'] for t in t19)
        c5 = sum(t['cost'] for t in t5)
        chosen = t5 if c5 < c19 else t19
        for t in chosen:
            if t['n'] < 5 and t['fill'] < 0.6:
                leftovers.extend(t.get('points', []))
            else:
                all_t.append(t)
    if leftovers:
        all_t.extend(pack_trips(leftovers, '1.9T'))
    return all_t

def S9_8t_grouped(pts):
    """All 8T, grouped by route"""
    all_t = []
    for gpts in group_by_route(pts).values():
        all_t.extend(pack_trips(gpts, '8T'))
    return all_t

# ========== MAIN ==========

date_groups = {}
for p in BOOKING_POINTS:
    c = p.get('coords')
    if not c or not c.get('lat') or not c.get('lng'):
        continue
    date_groups.setdefault(p['date'], []).append(p)

dates = sorted(date_groups.keys())

strats = [
    ("S1: Hien tai (1.9T, nhom tuyen)", S1_current),
    ("S2: Tat ca 1.9T, khong nhom", S2_19t_nogroup),
    ("S3: Tat ca 5T, nhom tuyen", S3_5t_grouped),
    ("S4: Hon hop (5T nang, 1.9T nhe)", S4_mixed_weight),
    ("S5: Smart Mixed (so sanh cost)", S5_smart_mixed),
    ("S6: Tat ca 5T, khong nhom", S6_5t_nogroup),
    ("S7: Geo Clustering + 5T", S7_geo_cluster_5t),
    ("S8: Hybrid (smart+merge leftover)", S8_hybrid_merge),
    ("S9: Tat ca 8T, nhom tuyen", S9_8t_grouped),
]

res = {name: {'totalCost': 0, 'totalDC': 0, 'totalGC': 0, 'totalTrips': 0, 'daily': []} for name, _ in strats}

for date in dates:
    allpts = date_groups[date]
    direct = [p for p in allpts if not is_gxt(p)]
    gxt = [p for p in allpts if is_gxt(p)]
    
    gxt_cost = 0
    if gxt:
        d2g = haversine(HUB_DC, HUB_GXT) * 2
        tw = sum(p.get('weight', 0) or 0 for p in gxt)
        wr = tw
        while wr > 0:
            chw = min(wr, 7480)
            tt = '8T'
            if chw <= 2090: tt = '1.9T'
            elif chw <= 5500: tt = '5T'
            gxt_cost += trip_cost(tt, d2g, chw, 'TC')
            wr -= chw
    
    if not direct:
        continue
    
    for name, fn in strats:
        trips = fn(direct)
        dc = sum(t['cost'] for t in trips)
        nt = len(trips)
        af = sum(t['fill'] for t in trips) / max(nt, 1)
        trucks = {'1.9T': 0, '5T': 0, '8T': 0}
        for t in trips: trucks[t['truck']] += 1
        
        res[name]['totalCost'] += dc + gxt_cost
        res[name]['totalDC'] += dc
        res[name]['totalGC'] += gxt_cost
        res[name]['totalTrips'] += nt
        res[name]['daily'].append({
            'date': date, 'dc': dc, 'gc': gxt_cost, 'nt': nt,
            'af': round(af, 2), 'trucks': trucks, 'ns': len(direct)
        })

# Rank
ranked = sorted(
    [(name, res[name]) for name, _ in strats],
    key=lambda x: x[1]['totalCost']
)

base_cost = next((r[1]['totalCost'] for r in ranked if 'S1' in r[0]), ranked[0][1]['totalCost'])

print()
print('=' * 140)
print('PHAN TICH TOI UU CHI PHI VAN CHUYEN GIAO THANG')
print(f'Du lieu: {len(dates)} ngay ({dates[0]} -> {dates[-1]})')
print('=' * 140)

print('\nBANG XEP HANG TONG CHI PHI:\n')
print(f'{"Rank":>4} | {"Phuong an":<46} | {"Chi Phi GT":>12} | {"Chi Phi TC":>12} | {"TONG":>12} | {"TB/Ngay":>10} | {"Chuyen":>7} | {"So voi S1":>16}')
print('-' * 140)

for idx, (name, data) in enumerate(ranked):
    diff = data['totalCost'] - base_cost
    pct = (diff / base_cost * 100) if base_cost else 0
    if diff > 0:
        ds = f"+{diff/1e6:.1f}M (+{pct:.1f}%)"
    elif diff < 0:
        ds = f"{diff/1e6:.1f}M ({pct:.1f}%)"
    else:
        ds = "---"
    avg = data['totalCost'] / len(dates)
    at = data['totalTrips'] / len(dates)
    print(f"  {idx+1}  | {name:<46} | {data['totalDC']/1e6:>9.2f}M | {data['totalGC']/1e6:>9.2f}M | {data['totalCost']/1e6:>9.2f}M | {avg/1e6:>7.2f}M | {at:>6.1f} | {ds}")

# Detail top 3
print('\n\nCHI TIET TOP 3:\n')
for idx, (name, data) in enumerate(ranked[:3]):
    avg = data['totalCost'] / len(dates)
    at = data['totalTrips'] / len(dates)
    all_trucks = {'1.9T': 0, '5T': 0, '8T': 0}
    for d in data['daily']:
        for k in all_trucks: all_trucks[k] += d['trucks'].get(k, 0)
    print(f'\n### {idx+1}. {name}')
    print(f'Tong: {data["totalCost"]/1e6:.2f}M | TB/ngay: {avg/1e6:.2f}M | TB chuyen: {at:.1f}')
    print(f'Tong xe: 1.9T={all_trucks["1.9T"]} | 5T={all_trucks["5T"]} | 8T={all_trucks["8T"]}')
    print()
    print(f'{"Ngay":<12} | {"BC":>3} | {"Chuyen":>6} | {"1.9T":>4} | {"5T":>3} | {"8T":>3} | {"CP GT(M)":>9} | {"CP TC(M)":>9} | {"TONG(M)":>9} | {"Fill%":>5}')
    print('-' * 100)
    for d in data['daily']:
        tc = d['dc'] + d['gc']
        print(f'{d["date"]:<12} | {d["ns"]:>3} | {d["nt"]:>6} | {d["trucks"]["1.9T"]:>4} | {d["trucks"]["5T"]:>3} | {d["trucks"]["8T"]:>3} | {d["dc"]/1e6:>9.2f} | {d["gc"]/1e6:>9.2f} | {tc/1e6:>9.2f} | {d["af"]*100:>4.0f}%')

# Save results
out = {
    'analysis_date': dates[-1],
    'data_range': {'from': dates[0], 'to': dates[-1], 'days': len(dates)},
    'ranking': [
        {
            'rank': i+1, 'strategy': n,
            'totalCost': d['totalCost'], 'totalDirectCost': d['totalDC'],
            'avgDailyCost': round(d['totalCost']/len(dates)),
            'avgTrips': round(d['totalTrips']/len(dates), 1),
            'savings': round(base_cost - d['totalCost']),
            'savingsPct': round((base_cost - d['totalCost'])/base_cost*100, 1)
        }
        for i, (n, d) in enumerate(ranked)
    ]
}
with open(os.path.join(BASE_DIR, 'cost_analysis_results.json'), 'w', encoding='utf-8') as f:
    json.dump(out, f, indent=2, ensure_ascii=False)

print('\n\nKet qua da luu vao cost_analysis_results.json')
