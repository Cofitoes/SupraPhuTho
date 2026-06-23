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
    
    const isGXTStore = (storeName) => {
        return gxtStoreNames.some(gxtName => {
            const normGXT = gxtName.normalize('NFC').trim().toLowerCase();
            const normStore = storeName.normalize('NFC').trim().toLowerCase();
            return normGXT === normStore || normStore.includes(normGXT) || normGXT.includes(normStore);
        });
    };

    const gxtPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && isGXTStore(p.name));
    const directPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && !isGXTStore(p.name));

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

    // STEP 1: DIRECT DELIVERY (Giao thẳng) - K-Means Clustering
    // ========================================
    let directTrips = [];
    if (directPoints.length > 0) {
        let totalW = 0; let totalV = 0;
        directPoints.forEach(p => { totalW += (p.weight || 0); totalV += (p.volume || 0); });
        
        let K = Math.max(1, Math.ceil(totalW / 1900), Math.ceil(totalV / 14), Math.ceil(directPoints.length / 15));
        if (K > directPoints.length) K = directPoints.length;

        // Initialize K centroids (spread them out)
        let centroids = [];
        let remainingForCentroid = [...directPoints];
        remainingForCentroid.sort((a, b) => calculateDistance(hubDC.coords, b.coords) - calculateDistance(hubDC.coords, a.coords));
        for (let i = 0; i < K; i++) {
            if (i === 0) {
                centroids.push({ ...remainingForCentroid[0].coords });
            } else {
                let maxMinDist = -1;
                let bestPt = remainingForCentroid[0];
                for (let pt of remainingForCentroid) {
                    let minDist = Infinity;
                    for (let c of centroids) {
                        let d = calculateDistance(pt.coords, c);
                        if (d < minDist) minDist = d;
                    }
                    if (minDist > maxMinDist) {
                        maxMinDist = minDist;
                        bestPt = pt;
                    }
                }
                centroids.push({ ...bestPt.coords });
            }
        }

        // K-Means iteration
        let clusters = Array.from({length: K}, () => []);
        let changed = true;
        let iter = 0;
        while (changed && iter < 50) {
            changed = false;
            let newClusters = Array.from({length: K}, () => []);
            directPoints.forEach(p => {
                let bestK = 0; let minDist = Infinity;
                for (let i = 0; i < K; i++) {
                    let d = calculateDistance(p.coords, centroids[i]);
                    if (d < minDist) { minDist = d; bestK = i; }
                }
                newClusters[bestK].push(p);
            });
            for (let i = 0; i < K; i++) {
                if (clusters[i].length !== newClusters[i].length) changed = true;
            }
            clusters = newClusters;
            for (let i = 0; i < K; i++) {
                if (clusters[i].length > 0) {
                    let sumLat = 0; let sumLng = 0;
                    clusters[i].forEach(p => { sumLat += p.coords.lat; sumLng += p.coords.lng; });
                    centroids[i] = { lat: sumLat / clusters[i].length, lng: sumLng / clusters[i].length };
                }
            }
            iter++;
        }

        // Capacity constraint balancing (force valid chunks)
        let isValid = false;
        let balanceIter = 0;
        while (!isValid && balanceIter < 50) {
            isValid = true;
            for (let i = 0; i < K; i++) {
                let w = clusters[i].reduce((sum, p) => sum + (p.weight||0), 0);
                let v = clusters[i].reduce((sum, p) => sum + (p.volume||0), 0);
                if (w > 1900 || v > 14 || clusters[i].length > 15) {
                    isValid = false;
                    clusters[i].sort((a,b) => calculateDistance(b.coords, centroids[i]) - calculateDistance(a.coords, centroids[i]));
                    let moved = false;
                    for (let p of clusters[i]) {
                        let bestAltK = -1; let minAltDist = Infinity;
                        for (let j = 0; j < K; j++) {
                            if (i === j) continue;
                            let altW = clusters[j].reduce((sum, pt) => sum + (pt.weight||0), 0);
                            let altV = clusters[j].reduce((sum, pt) => sum + (pt.volume||0), 0);
                            if (altW + (p.weight||0) <= 1900 && altV + (p.volume||0) <= 14 && clusters[j].length < 15) {
                                let d = calculateDistance(p.coords, centroids[j]);
                                if (d < minAltDist) {
                                    minAltDist = d;
                                    bestAltK = j;
                                }
                            }
                        }
                        if (bestAltK !== -1) {
                            clusters[bestAltK].push(p);
                            clusters[i] = clusters[i].filter(pt => pt !== p);
                            moved = true;
                            break;
                        }
                    }
                    if (!moved) {
                        K++;
                        clusters.push([]);
                        centroids.push({ ...clusters[i][0].coords });
                        isValid = false;
                        break;
                    }
                }
            }
            balanceIter++;
        }

        // ========================================
        // STEP 1.5: OPTIMIZE DIRECT TRIPS (Local Search)
        // ========================================
        if (clusters.length > 1) {
            const evaluateSolution = (solution) => {
                let score = 0;
                let weights = [];
                solution.forEach(chunk => {
                    if (chunk.length === 0) return;
                    const dist = getChunkDistance(hubDC, chunk);
                    score += dist * dist;
                    weights.push(chunk.reduce((sum, p) => sum + (p.weight||0), 0));
                });
                // Penalty for unbalance (optional, heavily penalize unbalance)
                if (weights.length > 0) {
                    let avgW = weights.reduce((a,b)=>a+b, 0) / weights.length;
                    let variance = weights.reduce((sum, w) => sum + Math.pow(w - avgW, 2), 0) / weights.length;
                    score += variance * 0.1; // Add weight variance penalty to encourage balancing
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

            let solution = clusters;
            let bestScore = evaluateSolution(solution);
            let improved = true;
            let maxIterations = 300;
            
            while (improved && maxIterations > 0) {
                improved = false;
                maxIterations--;
                for (let i = 0; i < solution.length && !improved; i++) {
                    for (let j = 0; j < solution.length && !improved; j++) {
                        if (i === j) continue;
                        // Try MOVE
                        for (let sIdx = 0; sIdx < solution[i].length; sIdx++) {
                            const store = solution[i][sIdx];
                            const newSrc = solution[i].filter((_, idx) => idx !== sIdx);
                            const newDst = [...solution[j], store];
                            if (isValidChunk(newSrc) && isValidChunk(newDst)) {
                                const proposed = solution.map((chunk, idx) => {
                                    if (idx === i) return newSrc;
                                    if (idx === j) return newDst;
                                    return chunk;
                                });
                                const score = evaluateSolution(proposed);
                                if (score < bestScore - 0.01) {
                                    solution = proposed;
                                    bestScore = score;
                                    improved = true;
                                    break;
                                }
                            }
                        }
                        if (improved) break;
                        // Try SWAP
                        for (let sI = 0; sI < solution[i].length && !improved; sI++) {
                            for (let sJ = 0; sJ < solution[j].length; sJ++) {
                                const newSrc = solution[i].map((s, idx) => idx === sI ? solution[j][sJ] : s);
                                const newDst = solution[j].map((s, idx) => idx === sJ ? solution[i][sI] : s);
                                if (isValidChunk(newSrc) && isValidChunk(newDst)) {
                                    const proposed = solution.map((chunk, idx) => {
                                        if (idx === i) return newSrc;
                                        if (idx === j) return newDst;
                                        return chunk;
                                    });
                                    const score = evaluateSolution(proposed);
                                    if (score < bestScore - 0.01) {
                                        solution = proposed;
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
            clusters = solution;
        }

        clusters.forEach(chunk => {
            if (chunk.length > 0) {
                directTrips.push(createDirectTrip(chunk, hubDC, '1.9T'));
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
        
        const newT1 = createDirectTrip(t1_pts, hubDC, '1.9T');
        const newT2 = createDirectTrip(t2_pts, hubDC, '1.9T');
        
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
            // Pack into chunks fitting 8T
            let remaining = [...gxtPoints];
            remaining.sort((a, b) => (b.weight || 0) - (a.weight || 0));
            while (remaining.length > 0) {
                const chunk = [];
                let w = 0, v = 0;
                for (let i = remaining.length - 1; i >= 0; i--) {
                    const p = remaining[i];
                    if (w + (p.weight || 0) <= TRUCK_LIMITS['8T'].maxW && v + (p.volume || 0) <= TRUCK_LIMITS['8T'].maxV) {
                        chunk.push(p);
                        w += (p.weight || 0);
                        v += (p.volume || 0);
                        remaining.splice(i, 1);
                    }
                }
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
                cost: getTripCost(chunkTruckType, distFloat),
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
