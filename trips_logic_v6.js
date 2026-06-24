function generateTrips() {
    const trips = [];

    // --- HUB DEFINITIONS ---
    let hubDC = HUBS.find(h => h.id === 'QM' || h.name === 'Kho DC Win Phú Thọ');
    if (hubDC) {
        hubDC.name = 'Kho DC Win Phú Thọ';
        hubDC.coords = { lat: 21.3885189, lng: 105.1738604 };
    } else {
        hubDC = { id: 'QM', name: 'Kho DC Win Phú Thọ', coords: { lat: 21.3885189, lng: 105.1738604 } };
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
            truckType: truckType, vehicle: truckType,
            dist: distFloat,
            totalVolume: parseFloat(totalVol.toFixed(2)),
            totalWeight: totalWeight,
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

    // Ensure coords are objects
    DELIVERY_POINTS.forEach(p => {
        if (typeof p.coords === 'string') {
            try { p.coords = JSON.parse(p.coords); } catch(e) {}
        }
    });

    const gxtPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && p.isGXT === true);
    let directPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && p.isGXT !== true);

    if (gxtPoints.length === 0 && directPoints.length === 0) {
        document.body.innerHTML += '<div style="position:fixed; top:50px; left:0; right:0; background: orange; color: white; padding: 20px; z-index:9999; font-size: 20px;">DEBUG: Both gxtPoints and directPoints are EMPTY! DELIVERY_POINTS length: ' + DELIVERY_POINTS.length + '</div>';
    }


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
                truckType: truckType, vehicle: truckType,
                totalWeight: w,
                totalVolume: parseFloat(v.toFixed(2)),
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

            const limit = 15; // Mới nhất: tối đa 15 điểm giao
            let added = true;
            
            while (added && chunk.length < limit) {
                added = false;
                let nearestIdx = -1, minDist = Infinity;
                
                for (let i = 0; i < remaining.length; i++) {
                    const p = remaining[i];
                    
                    if (cw + (p.weight || 0) <= chunkMaxW && cv + (p.volume || 0) <= chunkMaxV) {
                        // Greedily pick nearest point to the last point in chunk
                        const d = calculateDistance(chunk[chunk.length - 1].coords, p.coords);
                        if (d < minDist) { minDist = d; nearestIdx = i; }
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
    return trips;
}


window.safeGenerateTrips = function() {
    try {
        return generateTrips();
    } catch(e) {
        document.body.innerHTML += '<div style="position:fixed; top:0; left:0; right:0; background: red; color: white; padding: 20px; z-index:9999; font-size: 20px;">' + e.toString() + '<br>' + e.stack + '</div>';
        return [];
    }
}
