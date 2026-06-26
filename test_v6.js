const HUBS = [{id:'QM', name:'Kho DC Win Phú Thọ', coords:{lat:21, lng:105}}];
const CONFIG = {START_TIME: '06:00', AVG_SPEED_KMH: 40, UNLOADING_TIME_MIN: 15};
function calculateDistance(c1, c2) { return 10; }
function addMinutes(t, m) { return t; }
function getTripCost(v, d) { return 1000; }
const DELIVERY_POINTS = [{name:'WM+ 1', weight: 500, volume: 5, coords:{lat:21, lng:105}, isGXT: true}, {name:'WM+ 2', weight: 500, volume: 5, coords:{lat:21, lng:105}}];
function generateTrips() {
    const trips = [];

    // --- HUB DEFINITIONS ---
    let hubDC = HUBS.find(h => h.id === 'QM' || h.name === 'Kho DC Win Phú Thọ');
    if (hubDC) {
        hubDC.name = 'Kho DC Win Phú Thọ';
        hubDC.coords = { lat: 21.3879985, lng: 105.1803274 };
    } else {
        hubDC = { id: 'QM', name: 'Kho DC Win Phú Thọ', coords: { lat: 21.3879985, lng: 105.1803274 } };
        HUBS.unshift(hubDC);
    }

    // GXT Phú Thọ hub (88GF+HRX, Hy Cương, Phú Thọ)
    let hubGXT = HUBS.find(h => h.name === 'GXT Phú Thọ');
    if (hubGXT) {
        hubGXT.coords = { lat: 21.3264875, lng: 105.3246094 };
    } else {
        hubGXT = { id: 'GXT', name: 'GXT Phú Thọ', coords: { lat: 21.3264875, lng: 105.3246094 } };
        HUBS.push(hubGXT);
    }

    // Remove old hubs that don't belong to this project
    const validHubNames = ['Kho DC Win Phú Thọ', 'GXT Phú Thọ'];
    for (let i = HUBS.length - 1; i >= 0; i--) {
        if (!validHubNames.includes(HUBS[i].name)) {
            HUBS.splice(i, 1);
        }
    }

    // --- DATE DETECTION ---
    let bookingDateStr = '';
    if (typeof DELIVERY_POINTS !== 'undefined' && DELIVERY_POINTS.length > 0 && DELIVERY_POINTS[0].date) {
        bookingDateStr = DELIVERY_POINTS[0].date.replace(/-/g, '');
    } else {
        bookingDateStr = new Date().toISOString().slice(0, 10).replace(/-/g, '');
    }

    // --- TRUCK LIMITS ---
    const TRUCK_LIMITS = {
        '1.9T': { maxW: 1900, maxV: 14 },
        '5T': { maxW: 5000, maxV: 26 }, // As per Logic_Chia_Tuyen.docx: 5000kg
        '8T': { maxW: 6800, maxV: 55 }
    };

    // --- HELPER FUNCTIONS ---
    let tripCounter = 0;
    const getNextTripId = () => {
        tripCounter++;
        return `LH-${bookingDateStr}-${String(tripCounter).padStart(3, '0')}`;
    };

    const solveTSP = (hub, points) => {
        let unvisited = [...points];
        let current = hub;
        let sequence = [];
        let time = CONFIG.START_TIME;
        while (unvisited.length > 0) {
            let nearestIdx = -1;
            let minDist = Infinity;
            for (let i = 0; i < unvisited.length; i++) {
                const d = calculateDistance(current.coords, unvisited[i].coords);
                if (d < minDist) { minDist = d; nearestIdx = i; }
            }
            const next = unvisited[nearestIdx];
            time = addMinutes(time, Math.round((minDist / CONFIG.AVG_SPEED_KMH) * 60));
            sequence.push({ ...next, arrival: time, type: 'DELIVERY', isPoint: true });
            time = addMinutes(time, CONFIG.UNLOADING_TIME_MIN);
            current = next;
            unvisited.splice(nearestIdx, 1);
        }
        return { sequence, lastTime: time };
    };

    const createDirectTrip = (points, hub, truckType, existingId = null) => {
        const tsp = solveTSP(hub, points);
        let sequence = tsp.sequence || [];
        let time = tsp.lastTime || CONFIG.START_TIME;
        let dist = 0;
        let last = hub;
        sequence.forEach(p => {
            dist += calculateDistance(last.coords, p.coords);
            last = p;
        });
        if (sequence.length > 0) {
            const returnD = calculateDistance(sequence[sequence.length-1].coords, hub.coords);
            dist += returnD;
            time = addMinutes(time, Math.round((returnD / CONFIG.AVG_SPEED_KMH) * 60));
        }
        sequence.push({ name: hub.name, coords: hub.coords, arrival: time, type: 'HUB_RETURN' });

        const tripId = existingId || getNextTripId();
        const distFloat = parseFloat(dist.toFixed(2));
        const totalVol = points.reduce((s,p) => s + (p.volume||0), 0);
        const totalWeight = points.reduce((s,p) => s + (p.weight||0), 0);

        let totalCost = 0;
        const testCost = getTripCost('1.9T', 10);
        if (typeof testCost === 'number') {
            totalCost = getTripCost(truckType, distFloat);
        } else {
            const costObj = getTripCost(totalVol, distFloat);
            totalCost = (costObj && costObj.total) ? costObj.total : 0;
        }

        const allOriginalPoints = [];
        points.forEach(p => {
            if (p.originalPoints) {
                allOriginalPoints.push(...p.originalPoints);
            } else {
                allOriginalPoints.push(p.name);
            }
        });

        const deliveryPts = sequence.filter(p => p.type !== 'HUB_RETURN');
        
        return {
            id: tripId,
            route: `Kho DC Win Phú Thọ -> ${deliveryPts.map(p => p.name.replace(/^WM\+\s*/, '')).join(' -> ')}`,
            vehicle: truckType,
            dist: distFloat,
            volume: parseFloat(totalVol.toFixed(2)),
            weight: totalWeight,
            type: 'DELIVERY',
            points: sequence,
            cost: totalCost,
            tripType: 'Đi thẳng',
            groupedPoints: allOriginalPoints,
            hub: 'Kho DC Win Phú Thọ',
            hubsVisited: ['Kho DC Win Phú Thọ']
        };
    };

    // --- CLASSIFY STORES ---
    const gxtPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && p.isGXT === true);
    let directPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && p.isGXT !== true);

    // ========================================
    // STEP 1: TRANSIT (Trung chuyển) - GXT stores
    // ========================================
    if (gxtPoints.length > 0) {
        const totalGxtW = gxtPoints.reduce((sum, p) => sum + (p.weight || 0), 0);
        const totalGxtV = gxtPoints.reduce((sum, p) => sum + (p.volume || 0), 0);

        // Calculate direct distance DC -> GXT
        const distToGXT = calculateDistance(hubDC.coords, hubGXT.coords);
        const distFloat = parseFloat((distToGXT * 2).toFixed(2)); // Round trip

        // Pack into chunks fitting 8T, then 5T, then 1.9T sequentially
        let remainingGXT = [...gxtPoints];
        let tcCounter = 1;

        while (remainingGXT.length > 0) {
            let chunk = [];
            let w = 0, v = 0;
            
            // Try to pack up to 8T limit
            while (remainingGXT.length > 0) {
                const p = remainingGXT[0];
                if (w + (p.weight || 0) <= TRUCK_LIMITS['8T'].maxW && v + (p.volume || 0) <= TRUCK_LIMITS['8T'].maxV) {
                    chunk.push(p);
                    w += (p.weight || 0);
                    v += (p.volume || 0);
                    remainingGXT.shift();
                } else {
                    break; // Move to next truck
                }
            }

            // Determine best truck type for this chunk
            let truckType = '8T';
            if (w <= TRUCK_LIMITS['5T'].maxW && v <= TRUCK_LIMITS['5T'].maxV) truckType = '5T';
            if (w <= TRUCK_LIMITS['1.9T'].maxW && v <= TRUCK_LIMITS['1.9T'].maxV) truckType = '1.9T';

            const weightInTons = parseFloat((w / 1000).toFixed(2));
            
            let tripCost = 0;
            const testCost = getTripCost('1.9T', 10);
            if (typeof testCost === 'number') {
                tripCost = getTripCost(truckType, distFloat);
            } else {
                const costObj = getTripCost(v, distFloat);
                tripCost = (costObj && costObj.total) ? costObj.total : 0;
            }
            
            const trip = {
                id: `TC-GXT-${bookingDateStr}-${String(tcCounter).padStart(3, '0')}`,
                tripType: 'Trung chuyển',
                route: `Kho DC Win Phú Thọ -> GXT Phú Thọ (${weightInTons} Tấn)`,
                vehicle: truckType,
                weight: w,
                volume: parseFloat(v.toFixed(2)),
                distance: distFloat,
                dist: distFloat,
                hub: 'GXT Phú Thọ',
                hubsVisited: ['GXT Phú Thọ'],
                cost: tripCost,
                points: [
                    {
                        name: 'GXT Phú Thọ',
                        coords: hubGXT.coords,
                        arrival: CONFIG.START_TIME,
                        type: 'HUB_DELIVERY',
                        isPoint: true,
                        originalPoints: chunk.map(p => p.name)
                    },
                    {
                        name: 'Kho DC Win Phú Thọ',
                        coords: hubDC.coords,
                        arrival: addMinutes(CONFIG.START_TIME, 120),
                        type: 'HUB_RETURN'
                    }
                ]
            };
            trips.push(trip);
            tcCounter++;
        }
    }

    // ========================================
    // STEP 2: DIRECT DELIVERY (Giao thẳng)
    // ========================================
    if (directPoints.length > 0) {
        let remaining = [...directPoints];
        let directTrips = [];

        while (remaining.length > 0) {
            // Find farthest point as seed
            let seedIdx = 0;
            let maxDist = -1;
            for (let i = 0; i < remaining.length; i++) {
                const d = calculateDistance(hubDC.coords, remaining[i].coords);
                if (d > maxDist) { maxDist = d; seedIdx = i; }
            }

            const seed = remaining[seedIdx];
            let chunk = [seed];
            remaining.splice(seedIdx, 1);

            let cw = seed.weight || 0;
            let cv = seed.volume || 0;

            // Logic: Base limit is 1.9T. If ANY single store > 1.9T, limit becomes 5T.
            let chunkMaxW = TRUCK_LIMITS['1.9T'].maxW;
            let chunkMaxV = TRUCK_LIMITS['1.9T'].maxV;
            
            if (cw > TRUCK_LIMITS['1.9T'].maxW || cv > TRUCK_LIMITS['1.9T'].maxV) {
                chunkMaxW = TRUCK_LIMITS['5T'].maxW;
                chunkMaxV = TRUCK_LIMITS['5T'].maxV;
            }

            const limit = 20; // Mới nhất: tối đa 20 điểm giao
            let added = true;
            
            // Calculate seed round trip distance to set allowed distance limit for this trip
            const seedRT = calculateDistance(hubDC.coords, seed.coords) * 2;
            const allowedLimit = Math.max(120, seedRT + 15); // Strict 120km limit, but allow far seeds + 15km buffer
            
            while (added && chunk.length < limit) {
                added = false;
                let nearestIdx = -1, minDist = Infinity;
                
                for (let i = 0; i < remaining.length; i++) {
                    const p = remaining[i];
                    
                    if (cw + (p.weight || 0) <= chunkMaxW && cv + (p.volume || 0) <= chunkMaxV) {
                        // Greedily pick nearest point to the last point in chunk
                        const d = calculateDistance(chunk[chunk.length - 1].coords, p.coords);
                        
                        // Check if adding this point keeps the trip round-trip distance within limits
                        const prospectivePoints = [...chunk, p];
                        const tsp = solveTSP(hubDC, prospectivePoints);
                        let prospectiveDist = 0;
                        let last = hubDC;
                        tsp.sequence.forEach(pt => {
                            prospectiveDist += calculateDistance(last.coords, pt.coords);
                            last = pt;
                        });
                        prospectiveDist += calculateDistance(last.coords, hubDC.coords);
                        
                        if (prospectiveDist <= allowedLimit) {
                            if (d < minDist) {
                                minDist = d;
                                nearestIdx = i;
                            }
                        }
                    }
                }
                
                if (nearestIdx !== -1) {
                    const p = remaining[nearestIdx];
                    cw += p.weight || 0; cv += p.volume || 0;
                    chunk.push(p);
                    remaining.splice(nearestIdx, 1);
                    added = true;
                }
            }
            
            // Build the trip
            let truckType = '1.9T';
            if (cw > TRUCK_LIMITS['1.9T'].maxW || cv > TRUCK_LIMITS['1.9T'].maxV) {
                truckType = '5T';
            }
            
            const trip = createDirectTrip(chunk, hubDC, truckType);
            directTrips.push(trip);
        }

        trips.push(...directTrips);
    }

    // Export trips
    window.GHN_TRIPS = trips;
    if (typeof updateTripTables === 'function') {
        updateTripTables(trips);
    }
}

generateTrips();
console.log('OK');
