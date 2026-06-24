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
        '5T': { maxW: 4900, maxV: 26 },
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
        const routeName = `${hub.name} -> ` + deliveryPts.map(p => p.name).join(' -> ');
        
        return {
            id: tripId,
            hub: hub.name,
            truckType: truckType,
            points: sequence,
            dist: distFloat,
            totalVolume: totalVol,
            totalWeight: totalWeight,
            cost: totalCost,
            unitCost: totalCost / (totalWeight || 1),
            tripType: 'Đi thẳng',
            groupedPoints: allOriginalPoints,
            routeName: routeName,
            hubProvinces: {}
        };
    };

    // --- CLASSIFY STORES: GXT vs DIRECT ---
    const gxtStoreNames = (typeof GXT_STORE_LIST !== 'undefined') ? GXT_STORE_LIST : [];
    
    const isGXTStore = (storeName, addressOrDistrict = '') => {
        if (!storeName) return false;
        
        const upperStore = storeName.toUpperCase();
        const fullText = (storeName + ' ' + (addressOrDistrict || '')).normalize('NFC').toLowerCase();

        // Ngoại lệ: Các Huyện/Thị xã này luôn đi thẳng do rất gần kho DC
        const directDistricts = ['lâm thao', 'phù ninh', 'tam nông', 'thanh ba', 'thị xã phú thọ', 'tx phú thọ', 'tx. phú thọ'];
        for (let d of directDistricts) {
            if (fullText.includes(d)) return false;
        }

        // 1. Dựa vào mã bưu cục (Hub Code): Các tỉnh này LUÔN LUÔN phải qua kho trung chuyển GXT
        const transitCodes = ['TQG', 'YBI', 'LCI', 'HGG', 'SLA', 'HBH'];
        for (let code of transitCodes) {
            if (upperStore.includes(code)) return true;
        }

        // 2. Chỉ định cứng các điểm đặc biệt LUÔN đi GXT
        const forcedGXTStores = ["WM+ PTO 965 Hùng Vương"];
        if (forcedGXTStores.some(name => upperStore === name.toUpperCase())) return true;

        // 4. Dựa vào danh sách ngoại lệ GXT
        return gxtStoreNames.some(gxtName => {
            const normGXT = gxtName.normalize('NFC').trim().toLowerCase();
            const normStore = storeName.normalize('NFC').trim().toLowerCase();
            return normGXT === normStore || normStore.includes(normGXT) || normGXT.includes(normStore);
        });
    };
    
    // Expose for demo.html UI usage
    if (typeof window !== 'undefined') window.isGXTStore = isGXTStore;

    const gxtPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && isGXTStore(p.name, p.address));
    const directPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && !isGXTStore(p.name, p.address));

    // ========================================
        const getChunkDistance = (hub, points) => {
        if (points.length === 0) return 0;
        const tsp = solveTSP(hub, points);
        let sequence = tsp.sequence || [];
        let dist = 0;
        let last = hub;
        sequence.forEach(p => {
            dist += calculateDistance(last.coords, p.coords);
            last = p;
        });
        if (sequence.length > 0) {
            dist += calculateDistance(sequence[sequence.length - 1].coords, hub.coords);
        }
        return parseFloat(dist.toFixed(2));
    };

    // STEP 1: DIRECT DELIVERY (Giao thẳng) - Heuristic & Local Search
    // ========================================
    // Priority 1: Minimize number of trucks (Greedy Packing)
    // Priority 2: Optimize geographic routes (Local Search minimizing dist^2 to balance trip lengths)
    let directTrips = [];
    if (directPoints.length > 0) {
        let solutionGreedy = [];
        let remaining = [...directPoints];
        // Sort by furthest point first
        remaining.sort((a, b) => calculateDistance(hubDC.coords, b.coords) - calculateDistance(hubDC.coords, a.coords));

        while (remaining.length > 0) {
            const seed = remaining.shift();
            const chunk = [seed];
            let cw = seed.weight || 0;
            let cv = seed.volume || 0;

            // Dynamic capacity to balance trips
            let remW = cw, remV = cv;
            remaining.forEach(p => { remW += (p.weight || 0); remV += (p.volume || 0); });
            let neededTrucks = Math.max(1, Math.ceil(remW / 1900), Math.ceil(remV / 14));
            let dynamicLimit = Math.ceil((remaining.length + 1) / neededTrucks) + 1; // +1 for slack
            let limit = Math.min(15, Math.max(3, dynamicLimit)); // Bound between 3 and 15

            let added = true;
            while (added && chunk.length < limit) {
                added = false;
                let nearestIdx = -1, minDist = Infinity;
                for (let i = 0; i < remaining.length; i++) {
                    const p = remaining[i];
                    if (cw + (p.weight || 0) <= 1900 && cv + (p.volume || 0) <= 14) {
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
            solutionGreedy.push(chunk);
        }

        // ========================================
        // STEP 1.5: OPTIMIZE DIRECT TRIPS (Local Search)
        // ========================================
        let clusters = solutionGreedy;
        if (clusters.length > 1) {
            const evaluateSolution = (solution) => {
                let score = 0;
                let exactCost = 0;
                solution.forEach(chunk => {
                    if (chunk.length === 0) return;
                    const dist = getChunkDistance(hubDC, chunk);
                    score += dist * dist; // Penalize unbalanced distance and long routes
                    if (typeof getTripCost === 'function') {
                        exactCost += getTripCost('1.9T', dist);
                    }
                });
                // Prioritize exact cost, but use distance squared to naturally balance trips geographically
                if (exactCost > 0) {
                    return exactCost + (score * 0.5); 
                }
                return score;
            };

            const isValidChunk = (chunk) => {
                if (chunk.length === 0) return true;
                if (chunk.length > 15) return false;
                let w = 0, v = 0;
                for (let i = 0; i < chunk.length; i++) {
                    w += chunk[i].weight || 0;
                    v += chunk[i].volume || 0;
                }
                if (w > 1900 || v > 14) return false;
                return true;
            };

            let bestScore = evaluateSolution(clusters);
            let improved = true;
            let maxIterations = 400; // Increased iterations for better optimization

            while (improved && maxIterations > 0) {
                improved = false;
                maxIterations--;
                for (let i = 0; i < clusters.length && !improved; i++) {
                    for (let j = 0; j < clusters.length && !improved; j++) {
                        if (i === j) continue;
                        
                        // Try MOVE
                        for (let sIdx = 0; sIdx < clusters[i].length; sIdx++) {
                            const store = clusters[i][sIdx];
                            const newSrc = clusters[i].filter((_, idx) => idx !== sIdx);
                            const newDst = [...clusters[j], store];
                            if (isValidChunk(newSrc) && isValidChunk(newDst)) {
                                const proposed = clusters.map((chunk, idx) => {
                                    if (idx === i) return newSrc;
                                    if (idx === j) return newDst;
                                    return chunk;
                                });
                                const score = evaluateSolution(proposed);
                                if (score < bestScore - 0.01) {
                                    clusters = proposed;
                                    bestScore = score;
                                    improved = true;
                                    break;
                                }
                            }
                        }
                        if (improved) break;
                        
                        // Try SWAP
                        for (let sI = 0; sI < clusters[i].length && !improved; sI++) {
                            for (let sJ = 0; sJ < clusters[j].length; sJ++) {
                                const newSrc = clusters[i].map((s, idx) => idx === sI ? clusters[j][sJ] : s);
                                const newDst = clusters[j].map((s, idx) => idx === sJ ? clusters[i][sI] : s);
                                if (isValidChunk(newSrc) && isValidChunk(newDst)) {
                                    const proposed = clusters.map((chunk, idx) => {
                                        if (idx === i) return newSrc;
                                        if (idx === j) return newDst;
                                        return chunk;
                                    });
                                    const score = evaluateSolution(proposed);
                                    if (score < bestScore - 0.01) {
                                        clusters = proposed;
                                        bestScore = score;
                                        improved = true;
                                        break;
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        clusters.forEach(chunk => {
            if (chunk.length > 0) {
                let cw = chunk.reduce((s, p) => s + (p.weight || 0), 0);
                let cv = chunk.reduce((s, p) => s + (p.volume || 0), 0);
                let tType = '1.9T';
                if (cw > 4900 || cv > 26) tType = '8T';
                else if (cw > 1900 || cv > 14) tType = '5T';
                directTrips.push(createDirectTrip(chunk, hubDC, tType));
            }
        });
    }

    // ========================================
    // STEP 1.8: ENFORCE 120KM EXCEPTION QUOTA
    // ========================================
    let exceptionsCount = directTrips.filter(t => t.distance > 120).length;
    let totalTrips = directTrips.length + 1; // Direct + 1 transit
    let quota = Math.floor(totalTrips * 0.20);
    
    // While we have too many exceptions, split the worst one
    while (exceptionsCount > Math.floor(totalTrips * 0.20)) {
        // Find worst exception trip that can be split (has > 1 delivery point)
        directTrips.sort((a, b) => b.distance - a.distance);
        let splitTripIdx = -1;
        for (let i = 0; i < directTrips.length; i++) {
            const pts = directTrips[i].points.filter(p => p.type === 'DELIVERY');
            if (directTrips[i].distance > 120 && pts.length > 1) {
                splitTripIdx = i;
                break;
            }
        }
        
        if (splitTripIdx === -1) {
            break; // Cannot split anymore! (Maybe all trips > 120km are just 1 point)
        }
        
        const worstTrip = directTrips[splitTripIdx];
        const pts = worstTrip.points.filter(p => p.type === 'DELIVERY');
        // split in half
        const mid = Math.floor(pts.length / 2);
        const t1_pts = pts.slice(0, mid);
        const t2_pts = pts.slice(mid);
        
        const splitTripType = (pts) => {
            let cw = pts.reduce((s, p) => s + (p.weight || 0), 0);
            let cv = pts.reduce((s, p) => s + (p.volume || 0), 0);
            if (cw > 4900 || cv > 26) return '8T';
            if (cw > 1900 || cv > 14) return '5T';
            return '1.9T';
        };
        const newT1 = createDirectTrip(t1_pts, hubDC, splitTripType(t1_pts));
        const newT2 = createDirectTrip(t2_pts, hubDC, splitTripType(t2_pts));
        
        directTrips.splice(splitTripIdx, 1, newT1, newT2);
        
        totalTrips++; // Total trips increases by 1
        exceptionsCount = directTrips.filter(t => t.distance > 120).length;
    }

    // Push direct trips to the main trips array
    directTrips.forEach(t => {
        t.tripType = 'Đi thẳng';
        t.isDirect = true; // Use a boolean flag to avoid encoding bugs
        trips.push(t);
    });

    // STEP 2: TRANSIT (Trung chuyển) - GXT stores → GXT Phú Thọ
    // ========================================
    if (gxtPoints.length > 0) {
        const totalGxtW = gxtPoints.reduce((sum, p) => sum + (p.weight || 0), 0);
        const totalGxtV = gxtPoints.reduce((sum, p) => sum + (p.volume || 0), 0);

        // Distance from Kho DC Win Phú Thọ → GXT Phú Thọ
        const distToGXT = calculateDistance(hubDC.coords, hubGXT.coords);
        const distFloat = parseFloat((distToGXT * 2).toFixed(2)); // Round trip

        // Determine best truck type
        let truckType = '8T';
        if (totalGxtW <= 4900 && totalGxtV <= 26) truckType = '5T';
        if (totalGxtW <= 1900 && totalGxtV <= 14) truckType = '1.9T';

        // If total exceeds 8T, split into multiple transit trips
        const transitChunks = [];
        if (totalGxtW <= TRUCK_LIMITS['8T'].maxW && totalGxtV <= TRUCK_LIMITS['8T'].maxV) {
            transitChunks.push(gxtPoints);
        } else {
            // Pack into chunks fitting 8T sequentially to preserve original booking file order
            let remaining = [...gxtPoints];
            while (remaining.length > 0) {
                const chunk = [];
                let w = 0, v = 0;
                while (remaining.length > 0) {
                    const p = remaining[0];
                    if (w + (p.weight || 0) <= TRUCK_LIMITS['8T'].maxW && v + (p.volume || 0) <= TRUCK_LIMITS['8T'].maxV) {
                        chunk.push(p);
                        w += (p.weight || 0);
                        v += (p.volume || 0);
                        remaining.shift();
                    } else {
                        break;
                    }
                }
                
                // Edge case: if a single point exceeds 8T capacity, it causes infinite loop
                if (chunk.length === 0 && remaining.length > 0) {
                    chunk.push(remaining.shift());
                }
                transitChunks.push(chunk);
            }
        }

        transitChunks.forEach(chunk => {
            const chunkW = chunk.reduce((s, p) => s + (p.weight || 0), 0);
            const chunkV = chunk.reduce((s, p) => s + (p.volume || 0), 0);

            let chunkTruckType = '8T';
            if (chunkW <= 4900 && chunkV <= 26) chunkTruckType = '5T';
            if (chunkW <= 1900 && chunkV <= 14) chunkTruckType = '1.9T';

            // Build store names list for display
            const storeNames = chunk.map(p => p.name);
            const weightInTons = (chunkW / 1000).toFixed(1);

            const tripId = getNextTripId();
            const routeName = `Kho DC Win Phú Thọ -> GXT Phú Thọ (${weightInTons} Tấn)`;

            const loadingFee = (chunkW / 1000) * 200000;

            trips.push({
                id: tripId,
                hub: 'GXT Phú Thọ',
                hubsVisited: ['GXT Phú Thọ'],
                truckType: chunkTruckType,
                points: chunk.map(p => ({
                    name: p.name,
                    type: 'TRANSIT',
                    coords: p.coords,
                    isPoint: true,
                    weight: p.weight || 0,
                    volume: p.volume || 0,
                    originalPoints: [p.name],
                    originalPointObjects: [p]
                })),
                dist: distFloat,
                totalVolume: chunkV,
                totalWeight: chunkW,
                cost: getTripCost(chunkTruckType, distFloat) + loadingFee,
                loadingFee: loadingFee,
                unitCost: getTripCost(chunkTruckType, distFloat) / (chunkW || 1),
                tripType: 'Trung chuyển',
                routeName: routeName,
                hubProvinces: {
                    'GXT Phú Thọ': storeNames.map(n => n)
                }
            });
        });
    }

    // ========================================
    // SORT & RE-SEQUENCE
    // ========================================
    const directFinal = trips.filter(t => t.isDirect);
    const transitFinal = trips.filter(t => !t.isDirect);

    // Sort direct by distance (closest first)
    directFinal.sort((a, b) => a.dist - b.dist);

    const sortedTrips = [...directFinal, ...transitFinal];

    // Re-assign sequential IDs
    sortedTrips.forEach((trip, idx) => {
        trip.id = `LH-${bookingDateStr}-${String(idx + 1).padStart(3, '0')}`;
    });

    // API for Drag and Drop reallocation
    window.recalculateTrip = (trip) => {
        if (trip.tripType !== 'Đi thẳng') return trip;
        const originalPts = trip.points.filter(p => p.type === 'DELIVERY').map(p => {
            // Need to pass the original delivery point format back to createDirectTrip
            return {
                name: p.name,
                coords: p.coords,
                weight: p.weight || 0,
                volume: p.volume || 0,
                originalPoints: p.originalPoints || [p.name]
            };
        });
        const newTrip = createDirectTrip(originalPts, hubDC, '1.9T', trip.id);
        Object.assign(trip, newTrip);
        return trip;
    };

    return sortedTrips;
}
