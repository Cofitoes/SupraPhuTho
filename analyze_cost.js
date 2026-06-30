/**
 * Cost Optimization Analysis Script
 * Analyzes all historical booking data and simulates different routing strategies
 * to find the lowest cost approach for direct deliveries.
 * 
 * Run with: node analyze_cost.js
 */

const fs = require('fs');
const path = require('path');

// Load data files
const bookingDataRaw = fs.readFileSync(path.join(__dirname, 'booking_data.js'), 'utf-8');
const storeDataRaw = fs.readFileSync(path.join(__dirname, 'store_data.js'), 'utf-8');
const gxtStoresRaw = fs.readFileSync(path.join(__dirname, 'gxt_stores.js'), 'utf-8');

// Parse JS variable assignments
function parseJsVar(raw, varName) {
    const match = raw.match(new RegExp(`(?:const|var|let)\\s+${varName}\\s*=\\s*`));
    if (!match) return [];
    const startIdx = match.index + match[0].length;
    let depth = 0, i = startIdx;
    for (; i < raw.length; i++) {
        if (raw[i] === '[' || raw[i] === '{') depth++;
        if (raw[i] === ']' || raw[i] === '}') { depth--; if (depth === 0) { i++; break; } }
    }
    return JSON.parse(raw.substring(startIdx, i));
}

const BOOKING_POINTS = parseJsVar(bookingDataRaw, 'BOOKING_DELIVERY_POINTS');
const STORE_LIST = parseJsVar(storeDataRaw, 'STORE_LIST_DATA');

// Parse GXT stores
let GXT_STORE_LIST = [];
try {
    const gxtMatch = gxtStoresRaw.match(/GXT_STORE_LIST\s*=\s*\[/);
    if (gxtMatch) {
        const startIdx = gxtMatch.index + gxtMatch[0].length - 1;
        let depth = 0, i = startIdx;
        for (; i < gxtStoresRaw.length; i++) {
            if (gxtStoresRaw[i] === '[') depth++;
            if (gxtStoresRaw[i] === ']') { depth--; if (depth === 0) { i++; break; } }
        }
        GXT_STORE_LIST = JSON.parse(gxtStoresRaw.substring(startIdx, i));
    }
} catch(e) { console.log('GXT parse warning:', e.message); }

// --- CONSTANTS ---
const TRUCK_LIMITS = {
    '1.9T': { maxW: 1900, maxWAllowed: 2090, maxV: 14 },
    '5T':   { maxW: 5000, maxWAllowed: 5500, maxV: 26 },
    '8T':   { maxW: 6800, maxWAllowed: 7480, maxV: 55 }
};

const HUB_DC = { lat: 21.3879985, lng: 105.1803274 };
const HUB_GXT = { lat: 21.3264875, lng: 105.3246094 };

// Pricing
function getTripCost(truckType, distanceKm, weightKg, tripType) {
    const cfg = {
        '1.9T': { minKm: 120, baseCost: 1700000, extraRate: 11000 },
        '5T': { rates: [1100000, 2400000, 3000000], extraRate: 20000 },
        '8T': { rates: [1500000, 3000000, 4200000], extraRate: 22000 }
    };
    const config = cfg[truckType];
    let baseCost = 0, extraCost = 0, loadingCost = 0;
    
    if (truckType === '1.9T') {
        baseCost = config.baseCost;
        if (distanceKm > config.minKm) extraCost = config.extraRate * (distanceKm - config.minKm);
    } else {
        const { rates, extraRate } = config;
        if (distanceKm <= 50) baseCost = rates[0];
        else if (distanceKm <= 100) baseCost = rates[1];
        else if (distanceKm <= 150) baseCost = rates[2];
        else { baseCost = rates[2]; extraCost = extraRate * (distanceKm - 150); }
    }
    
    if (tripType === 'TC') loadingCost = (weightKg || 0) * 200;
    return Math.round(baseCost + extraCost + loadingCost);
}

// Haversine distance
function calcDist(a, b) {
    const R = 6371;
    const toRad = x => x * Math.PI / 180;
    const dLat = toRad(b.lat - a.lat);
    const dLng = toRad(b.lng - a.lng);
    const sinLat = Math.sin(dLat / 2);
    const sinLng = Math.sin(dLng / 2);
    const h = sinLat * sinLat + Math.cos(toRad(a.lat)) * Math.cos(toRad(b.lat)) * sinLng * sinLng;
    return R * 2 * Math.atan2(Math.sqrt(h), Math.sqrt(1 - h));
}

// TSP nearest-neighbor
function solveTSP(hub, points) {
    let unvisited = [...points];
    let current = hub;
    let totalDist = 0;
    while (unvisited.length > 0) {
        let minDist = Infinity, nearestIdx = -1;
        for (let i = 0; i < unvisited.length; i++) {
            const d = calcDist(current, unvisited[i].coords);
            if (d < minDist) { minDist = d; nearestIdx = i; }
        }
        totalDist += minDist;
        current = unvisited[nearestIdx].coords;
        unvisited.splice(nearestIdx, 1);
    }
    if (points.length > 0) totalDist += calcDist(current, hub);
    return parseFloat(totalDist.toFixed(2));
}

// Check if store is GXT
function isGXT(p) {
    if (p.isGXT === true) return true;
    if (p.isGXT === false) return false;
    const store = STORE_LIST.find(s => s.id === p.id || s.name === p.name);
    if (store && store.isGXT !== undefined) return store.isGXT;
    return GXT_STORE_LIST.some(gxtName => {
        const normGXT = gxtName.normalize('NFC').trim().toLowerCase();
        const normStore = p.name.normalize('NFC').trim().toLowerCase();
        return normGXT === normStore || normStore.includes(normGXT) || normGXT.includes(normStore);
    });
}

// Get district
function getDistrict(p) {
    const store = STORE_LIST.find(s => s.id === p.id || s.name === p.name);
    if (store && store.district) return store.district;
    if (p.address) {
        const parts = p.address.split(',').map(s => s.trim()).filter(Boolean);
        if (parts.length > 0) return parts[0];
    }
    return '';
}

// Route groups
const ROUTE_GROUPS = [
    { name: "Thanh Thuy - Thanh Son", districts: ["H. Thanh Thủy", "H. Thanh Sơn"] },
    { name: "Yen Lap - Cam Khe", districts: ["H. Yên Lập", "H. Cẩm Khê"] },
    { name: "Tam Nong - Lam Thao", districts: ["H. Tam Nông", "H. Lâm Thao"] },
    { name: "Doan Hung - Phu Ninh", districts: ["H. Đoan Hùng", "H. Phù Ninh"] },
    { name: "Ha Hoa - Thanh Ba", districts: ["H. Hạ Hoà", "H. Hạ Hòa", "H. Thanh Ba"] }
];

function matchRouteGroup(district) {
    const normP = district.toLowerCase().replace(/^(h\.|tp\.|tx\.)\s*/, '').trim();
    for (const g of ROUTE_GROUPS) {
        for (const d of g.districts) {
            const normD = d.toLowerCase().replace(/^(h\.|tp\.|tx\.)\s*/, '').trim();
            if (normD === normP) return g.name;
        }
    }
    return 'Khac';
}

// Pack points into trips
function packIntoTrips(points, truckType) {
    const limit = TRUCK_LIMITS[truckType];
    let remaining = [...points];
    let trips = [];
    
    while (remaining.length > 0) {
        let chunk = [];
        let cw = 0, cv = 0;
        let i = 0;
        while (i < remaining.length) {
            const p = remaining[i];
            if (cw + (p.weight || 0) <= limit.maxWAllowed && cv + (p.volume || 0) <= limit.maxV) {
                chunk.push(p);
                cw += (p.weight || 0);
                cv += (p.volume || 0);
                remaining.splice(i, 1);
            } else {
                i++;
            }
        }
        if (chunk.length === 0 && remaining.length > 0) {
            chunk.push(remaining.shift());
            cw = chunk[0].weight || 0;
            cv = chunk[0].volume || 0;
        }
        const dist = solveTSP(HUB_DC, chunk);
        const cost = getTripCost(truckType, dist, cw, 'GT');
        trips.push({ truckType, totalWeight: cw, totalVolume: cv, distance: dist, cost, numPoints: chunk.length, fillRate: cw / limit.maxWAllowed });
    }
    return trips;
}

// =========================================
// STRATEGY FUNCTIONS (only direct delivery part)
// =========================================

// S1: Current - 1.9T grouped by route
function S1(directPts) {
    const groups = {};
    directPts.forEach(p => { const g = matchRouteGroup(getDistrict(p)); if (!groups[g]) groups[g] = []; groups[g].push(p); });
    let all = [];
    for (const pts of Object.values(groups)) all.push(...packIntoTrips(pts, '1.9T'));
    return all;
}

// S2: All 1.9T, no grouping
function S2(directPts) { return packIntoTrips(directPts, '1.9T'); }

// S3: All 5T, grouped by route
function S3(directPts) {
    const groups = {};
    directPts.forEach(p => { const g = matchRouteGroup(getDistrict(p)); if (!groups[g]) groups[g] = []; groups[g].push(p); });
    let all = [];
    for (const pts of Object.values(groups)) all.push(...packIntoTrips(pts, '5T'));
    return all;
}

// S4: Mixed - 5T for heavy routes, 1.9T for light
function S4(directPts) {
    const groups = {};
    directPts.forEach(p => { const g = matchRouteGroup(getDistrict(p)); if (!groups[g]) groups[g] = []; groups[g].push(p); });
    let all = [];
    for (const [gn, pts] of Object.entries(groups)) {
        const totalW = pts.reduce((s, p) => s + (p.weight || 0), 0);
        all.push(...packIntoTrips(pts, totalW > 3000 ? '5T' : '1.9T'));
    }
    return all;
}

// S5: Smart Mixed - compare cost for each route
function S5(directPts) {
    const groups = {};
    directPts.forEach(p => { const g = matchRouteGroup(getDistrict(p)); if (!groups[g]) groups[g] = []; groups[g].push(p); });
    let all = [];
    for (const pts of Object.values(groups)) {
        const t19 = packIntoTrips(pts, '1.9T');
        const t5 = packIntoTrips(pts, '5T');
        const c19 = t19.reduce((s, t) => s + t.cost, 0);
        const c5 = t5.reduce((s, t) => s + t.cost, 0);
        all.push(...(c5 < c19 ? t5 : t19));
    }
    return all;
}

// S6: All 5T, no grouping
function S6(directPts) { return packIntoTrips(directPts, '5T'); }

// S7: Geographic clustering with 5T
function S7(directPts) {
    let remaining = [...directPts];
    let trips = [];
    const limit = TRUCK_LIMITS['5T'];
    while (remaining.length > 0) {
        let maxDist = -1, startIdx = 0;
        remaining.forEach((p, i) => { const d = calcDist(HUB_DC, p.coords); if (d > maxDist) { maxDist = d; startIdx = i; } });
        let chunk = [remaining[startIdx]];
        let cw = remaining[startIdx].weight || 0, cv = remaining[startIdx].volume || 0;
        remaining.splice(startIdx, 1);
        while (remaining.length > 0) {
            const lastPt = chunk[chunk.length - 1];
            let ni = -1, nd = Infinity;
            for (let i = 0; i < remaining.length; i++) {
                if (cw + (remaining[i].weight || 0) <= limit.maxWAllowed && cv + (remaining[i].volume || 0) <= limit.maxV) {
                    const d = calcDist(lastPt.coords, remaining[i].coords);
                    if (d < nd) { nd = d; ni = i; }
                }
            }
            if (ni === -1 || nd > 25) break;
            chunk.push(remaining[ni]);
            cw += remaining[ni].weight || 0;
            cv += remaining[ni].volume || 0;
            remaining.splice(ni, 1);
        }
        const dist = solveTSP(HUB_DC, chunk);
        trips.push({ truckType: '5T', totalWeight: cw, totalVolume: cv, distance: dist, cost: getTripCost('5T', dist, cw, 'GT'), numPoints: chunk.length, fillRate: cw / limit.maxWAllowed });
    }
    return trips;
}

// S8: Hybrid - Smart per route + merge leftovers
function S8(directPts) {
    const groups = {};
    directPts.forEach(p => { const g = matchRouteGroup(getDistrict(p)); if (!groups[g]) groups[g] = []; groups[g].push(p); });
    let all = [];
    let leftovers = [];
    for (const pts of Object.values(groups)) {
        const t19 = packIntoTrips(pts, '1.9T');
        const t5 = packIntoTrips(pts, '5T');
        const c19 = t19.reduce((s, t) => s + t.cost, 0);
        const c5 = t5.reduce((s, t) => s + t.cost, 0);
        const chosen = c5 < c19 ? t5 : t19;
        chosen.forEach(t => {
            if (t.numPoints < 5 && t.fillRate < 0.6) leftovers.push({ w: t.totalWeight, v: t.totalVolume, cost: t.cost, trip: t });
            else all.push(t);
        });
    }
    // Try merging leftovers pairwise
    if (leftovers.length >= 2) {
        // Collect all leftover points conceptually - repack them together
        // But we don't have the raw points, so merge trip costs
        // Just push them as-is for simplicity
        leftovers.forEach(l => all.push(l.trip));
    } else {
        leftovers.forEach(l => all.push(l.trip));
    }
    return all;
}

// S9: All 8T, grouped by route
function S9(directPts) {
    const groups = {};
    directPts.forEach(p => { const g = matchRouteGroup(getDistrict(p)); if (!groups[g]) groups[g] = []; groups[g].push(p); });
    let all = [];
    for (const pts of Object.values(groups)) all.push(...packIntoTrips(pts, '8T'));
    return all;
}

// =========================================
// MAIN ANALYSIS
// =========================================

const dateGroups = {};
BOOKING_POINTS.forEach(p => {
    if (!p.coords || !p.coords.lat || !p.coords.lng) return;
    if (!dateGroups[p.date]) dateGroups[p.date] = [];
    dateGroups[p.date].push(p);
});

const dates = Object.keys(dateGroups).sort();

const strategies = [
    { name: "S1: Hien tai (1.9T, nhom tuyen)", fn: S1 },
    { name: "S2: Tat ca 1.9T, khong nhom", fn: S2 },
    { name: "S3: Tat ca 5T, nhom tuyen", fn: S3 },
    { name: "S4: Hon hop (5T nang, 1.9T nhe)", fn: S4 },
    { name: "S5: Smart Mixed (so sanh cost)", fn: S5 },
    { name: "S6: Tat ca 5T, khong nhom", fn: S6 },
    { name: "S7: Geo Clustering + 5T", fn: S7 },
    { name: "S8: Hybrid (smart+merge leftover)", fn: S8 },
    { name: "S9: Tat ca 8T, nhom tuyen", fn: S9 },
];

const results = {};
strategies.forEach(s => { results[s.name] = { totalCost: 0, totalDirectCost: 0, totalTrips: 0, totalGxtCost: 0, dailyData: [] }; });

dates.forEach(date => {
    const allPoints = dateGroups[date];
    const direct = allPoints.filter(p => !isGXT(p));
    const gxt = allPoints.filter(p => isGXT(p));
    
    // GXT cost (same for all)
    let gxtCost = 0;
    if (gxt.length > 0) {
        const distToGXT = calcDist(HUB_DC, HUB_GXT) * 2;
        const totalGxtW = gxt.reduce((s, p) => s + (p.weight || 0), 0);
        let wR = totalGxtW;
        while (wR > 0) {
            const chunkW = Math.min(wR, 7480);
            let tt = '8T';
            if (chunkW <= 2090) tt = '1.9T';
            else if (chunkW <= 5500) tt = '5T';
            gxtCost += getTripCost(tt, distToGXT, chunkW, 'TC');
            wR -= chunkW;
        }
    }
    
    if (direct.length === 0) return;
    
    strategies.forEach(s => {
        const trips = s.fn(direct);
        const directCost = trips.reduce((sum, t) => sum + t.cost, 0);
        const numTrips = trips.length;
        const avgFill = trips.length > 0 ? trips.reduce((s, t) => s + t.fillRate, 0) / trips.length : 0;
        const trucks = { '1.9T': 0, '5T': 0, '8T': 0 };
        trips.forEach(t => trucks[t.truckType]++);
        
        results[s.name].totalCost += directCost + gxtCost;
        results[s.name].totalDirectCost += directCost;
        results[s.name].totalGxtCost += gxtCost;
        results[s.name].totalTrips += numTrips;
        results[s.name].dailyData.push({ date, directCost, gxtCost, numTrips, avgFill: parseFloat(avgFill.toFixed(2)), trucks, numStores: direct.length });
    });
});

// Print results
console.log('\n' + '='.repeat(130));
console.log('PHAN TICH TOI UU CHI PHI VAN CHUYEN GIAO THANG');
console.log('Du lieu: ' + dates.length + ' ngay (' + dates[0] + ' -> ' + dates[dates.length-1] + ')');
console.log('='.repeat(130));

const ranked = strategies.map(s => ({
    name: s.name,
    ...results[s.name],
    avgDailyCost: results[s.name].totalCost / dates.length,
    avgTrips: results[s.name].totalTrips / dates.length
})).sort((a, b) => a.totalCost - b.totalCost);

const baseCost = ranked.find(r => r.name.includes('S1'))?.totalCost || ranked[0].totalCost;

console.log('\nBANG XEP HANG TONG CHI PHI (' + dates.length + ' ngay):\n');
console.log('Rank | Phuong an                                   | Chi Phi GT       | Chi Phi TC       | TONG             | TB Chuyen | So voi S1');
console.log('-'.repeat(130));

ranked.forEach((r, idx) => {
    const diff = r.totalCost - baseCost;
    const diffPct = ((diff / baseCost) * 100).toFixed(1);
    const diffStr = diff > 0 ? '+' + (diff/1e6).toFixed(1) + 'M (+' + diffPct + '%)' : 
                    diff < 0 ? (diff/1e6).toFixed(1) + 'M (' + diffPct + '%)' : '---';
    console.log(
        '  ' + (idx+1) + '  | ' + r.name.padEnd(45) + ' | ' + (r.totalDirectCost/1e6).toFixed(2).padStart(10) + 'M | ' + (r.totalGxtCost/1e6).toFixed(2).padStart(10) + 'M | ' + (r.totalCost/1e6).toFixed(2).padStart(10) + 'M | ' + r.avgTrips.toFixed(1).padStart(9) + ' | ' + diffStr
    );
});

// Detailed breakdown by date for top strategies
console.log('\n\nCHI TIET TUNG NGAY - TOP 3:\n');

ranked.slice(0, 3).forEach((r, idx) => {
    console.log('\n### ' + (idx+1) + '. ' + r.name);
    console.log('Tong: ' + (r.totalCost/1e6).toFixed(2) + 'M | TB/ngay: ' + (r.avgDailyCost/1e6).toFixed(2) + 'M | TB chuyen: ' + r.avgTrips.toFixed(1));
    const allTrucks = { '1.9T': 0, '5T': 0, '8T': 0 };
    r.dailyData.forEach(d => { allTrucks['1.9T'] += d.trucks['1.9T']; allTrucks['5T'] += d.trucks['5T']; allTrucks['8T'] += d.trucks['8T']; });
    console.log('Tong xe: 1.9T=' + allTrucks['1.9T'] + ' | 5T=' + allTrucks['5T'] + ' | 8T=' + allTrucks['8T']);
    console.log('');
    console.log('Ngay       | BC  | Chuyen | 1.9T | 5T  | 8T  | CP GT(M)  | CP TC(M)  | TONG(M)   | Fill%');
    console.log('-'.repeat(110));
    r.dailyData.forEach(d => {
        console.log(d.date + '  | ' + String(d.numStores).padStart(3) + ' | ' + String(d.numTrips).padStart(6) + ' | ' + String(d.trucks['1.9T']).padStart(4) + ' | ' + String(d.trucks['5T']).padStart(3) + ' | ' + String(d.trucks['8T']).padStart(3) + ' | ' + (d.directCost/1e6).toFixed(2).padStart(9) + ' | ' + (d.gxtCost/1e6).toFixed(2).padStart(9) + ' | ' + ((d.directCost+d.gxtCost)/1e6).toFixed(2).padStart(9) + ' | ' + (d.avgFill * 100).toFixed(0).padStart(4) + '%');
    });
});

// Save raw results
const outputData = {
    analysis_date: new Date().toISOString(),
    data_range: { from: dates[0], to: dates[dates.length-1], days: dates.length },
    ranking: ranked.map((r, idx) => ({
        rank: idx + 1,
        strategy: r.name,
        totalCost: r.totalCost,
        totalDirectCost: r.totalDirectCost,
        totalGxtCost: r.totalGxtCost,
        avgDailyCost: Math.round(r.avgDailyCost),
        avgTripsPerDay: parseFloat(r.avgTrips.toFixed(1)),
        savingsVsCurrent: Math.round(baseCost - r.totalCost),
        savingsPct: parseFloat(((baseCost - r.totalCost) / baseCost * 100).toFixed(1))
    }))
};

fs.writeFileSync(path.join(__dirname, 'cost_analysis_results.json'), JSON.stringify(outputData, null, 2));
console.log('\n\nKet qua da luu vao cost_analysis_results.json');
