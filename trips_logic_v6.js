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
        '1.9T': { maxW: 1900, maxWAllowed: 1900 * 1.1, maxV: 14 },
        '5T': { maxW: 5000, maxWAllowed: 5000 * 1.1, maxV: 26 }, // As per Logic_Chia_Tuyen.docx: 5000kg
        '8T': { maxW: 6800, maxWAllowed: 6800 * 1.1, maxV: 55 }
    };

    // --- HELPER FUNCTIONS ---
    const getTripCostDetails = (truckType, distanceKm, weightKg, tripType) => {
        const cfg = (typeof pricingConfig !== 'undefined') ? pricingConfig : {
            '1.9T': { minKm: 120, baseCost: 1700000, extraRate: 11000 },
            '5T': { rates: [1100000, 2400000, 3000000], extraRate: 20000 },
            '8T': { rates: [1500000, 3000000, 4200000], extraRate: 22000 }
        };
        const config = cfg[truckType];
        let baseCost = 0;
        let extraCost = 0;
        let loadingCost = 0;

        if (config) {
            if (truckType === '1.9T') {
                const { minKm, baseCost: cfgBaseCost, extraRate } = config;
                baseCost = cfgBaseCost;
                if (distanceKm > minKm) {
                    extraCost = extraRate * (distanceKm - minKm);
                }
            } else if (truckType === '5T' || truckType === '8T') {
                const { rates, extraRate } = config;
                if (distanceKm <= 50) {
                    baseCost = rates[0];
                } else if (distanceKm <= 100) {
                    baseCost = rates[1];
                } else if (distanceKm <= 150) {
                    baseCost = rates[2];
                } else {
                    baseCost = rates[2];
                    extraCost = extraRate * (distanceKm - 150);
                }
            }
        }

        if (tripType === 'Trung chuyển') {
            loadingCost = (weightKg || 0) * 200;
        }

        return {
            baseCost: Math.round(baseCost),
            extraCost: Math.round(extraCost),
            loadingCost: Math.round(loadingCost),
            totalCost: Math.round(baseCost + extraCost + loadingCost)
        };
    };

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

        const costDetails = getTripCostDetails(truckType, distFloat, totalWeight, 'Đi thẳng');

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
            routeName: `Kho DC Win Phú Thọ -> ${deliveryPts.map(p => p.name.replace(/^WM\+\s*/, '')).join(' -> ')}`,
            truckType: truckType, vehicle: truckType,
            dist: distFloat,
            totalVolume: parseFloat(totalVol.toFixed(2)),
            totalWeight: totalWeight,
            type: 'DELIVERY',
            points: sequence,
            costBase: costDetails.baseCost,
            costExtraKm: costDetails.extraCost,
            costBocXep: costDetails.loadingCost,
            cost: costDetails.totalCost,
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

    const gxtStoreNames = (typeof GXT_STORE_LIST !== 'undefined') ? GXT_STORE_LIST : [];
    const isGXTStore = (p) => {
        if (typeof window.checkIsGXTStore === 'function') {
            return window.checkIsGXTStore(p.name, p.id);
        }
        if (p.isGXT === true) return true;
        if (p.isGXT === false) return false;
        return gxtStoreNames.some(gxtName => {
            const normGXT = gxtName.normalize('NFC').trim().toLowerCase();
            const normStore = p.name.normalize('NFC').trim().toLowerCase();
            return normGXT === normStore || normStore.includes(normGXT) || normGXT.includes(normStore);
        });
    };

    const gxtPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && isGXTStore(p));
    let directPoints = DELIVERY_POINTS.filter(p => p.coords && p.coords.lat && p.coords.lng && !isGXTStore(p));

    if (gxtPoints.length === 0 && directPoints.length === 0) {
        console.warn('DEBUG: Both gxtPoints and directPoints are EMPTY! DELIVERY_POINTS length: ' + DELIVERY_POINTS.length);
    }


    // ========================================
    // STEP 1: TRANSIT (Trung chuyển) - GXT stores
    // ========================================
    if (gxtPoints.length > 0) {
        const distToGXT = calculateDistance(hubDC.coords, hubGXT.coords);
        const distFloat = parseFloat((distToGXT * 2).toFixed(2)); // Round trip

        // Pack GXT points into chunks using First-Fit Decreasing (FFD) bin packing
        const sortedGxt = [...gxtPoints].sort((a, b) => (b.weight || 0) - (a.weight || 0));
        let chunks = [];
        sortedGxt.forEach(p => {
            let packed = false;
            for (let i = 0; i < chunks.length; i++) {
                let c = chunks[i];
                if (c.w + (p.weight || 0) <= TRUCK_LIMITS['8T'].maxWAllowed && c.v + (p.volume || 0) <= TRUCK_LIMITS['8T'].maxV) {
                    c.points.push(p);
                    c.w += (p.weight || 0);
                    c.v += (p.volume || 0);
                    packed = true;
                    break;
                }
            }
            if (!packed) {
                chunks.push({
                    points: [p],
                    w: (p.weight || 0),
                    v: (p.volume || 0)
                });
            }
        });

        let tcCounter = 1;
        chunks.forEach(chunk => {
            const w = chunk.w;
            const v = chunk.v;
            
            // Determine best truck type for this chunk
            let truckType = '8T';
            if (w <= TRUCK_LIMITS['5T'].maxWAllowed && v <= TRUCK_LIMITS['5T'].maxV) truckType = '5T';
            if (w <= TRUCK_LIMITS['1.9T'].maxWAllowed && v <= TRUCK_LIMITS['1.9T'].maxV) truckType = '1.9T';

            const weightInTons = parseFloat((w / 1000).toFixed(2));
            const costDetails = getTripCostDetails(truckType, distFloat, w, 'Trung chuyển');
            
            const trip = {
                id: `TC-GXT-${bookingDateStr}-${String(tcCounter).padStart(3, '0')}`,
                tripType: 'Trung chuyển',
                districtsName: 'Trung chuyển GXT',
                route: `Kho DC Win Phú Thọ -> GXT Phú Thọ (${weightInTons} Tấn)`,
                routeName: `Kho DC Win Phú Thọ -> GXT Phú Thọ (${weightInTons} Tấn)`,
                truckType: truckType, vehicle: truckType,
                totalWeight: w,
                totalVolume: parseFloat(v.toFixed(2)),
                distance: distFloat,
                dist: distFloat,
                hub: 'GXT Phú Thọ',
                hubsVisited: ['GXT Phú Thọ'],
                costBase: costDetails.baseCost,
                costExtraKm: costDetails.extraCost,
                costBocXep: costDetails.loadingCost,
                cost: costDetails.totalCost,
                points: [
                    {
                        name: 'GXT Phú Thọ',
                        coords: hubGXT.coords,
                        arrival: CONFIG.START_TIME,
                        type: 'HUB_DELIVERY',
                        isPoint: true,
                        originalPoints: chunk.points.map(p => p.name)
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
        });
    }

    // ========================================
    // STEP 2: DIRECT DELIVERY (Giao thẳng) - Gom Huyện + Nâng tải
    // ========================================
    if (directPoints.length > 0) {
        // Helper to resolve district for a delivery point
        const getDistrictForPoint = (p) => {
            if (typeof STORE_LIST_DATA !== 'undefined' && Array.isArray(STORE_LIST_DATA)) {
                const store = STORE_LIST_DATA.find(s => 
                    (p.id && s.id && s.id.toLowerCase() === p.id.toLowerCase()) || 
                    (p.name && s.name && s.name.toLowerCase() === p.name.toLowerCase())
                );
                if (store && store.district) return store.district;
            }
            if (p.address) {
                let parts = p.address.split(',').map(part => part.trim()).filter(Boolean);
                if (parts.length > 0) {
                    let last = parts[parts.length - 1];
                    if (last.toLowerCase() === 'việt nam' || last.toLowerCase() === 'vietnam') {
                        parts.pop();
                    }
                }
                if (parts.length > 1) {
                    let district = parts[parts.length - 2];
                    district = district.replace(/\d+/g, '').replace(/^(Quận|Huyện|Thị xã|Thị Xã|Thành phố|Thành Phố|TP\.?)\s+/i, '').replace(/\.+$/, '').trim();
                    if (district && !/^(H\.|Q\.|TP\.|Tx\.)/i.test(district)) {
                        if (district.toLowerCase().includes('việt trì') || district.toLowerCase().includes('hòa bình') || district.toLowerCase().includes('phủ lý') || district.toLowerCase().includes('nam định')) {
                            district = 'TP. ' + district;
                        } else if (district.toLowerCase().includes('phú thọ') || district.toLowerCase().includes('thị xã')) {
                            district = 'Tx. ' + district;
                        } else {
                            district = 'H. ' + district;
                        }
                    }
                    return district;
                }
            }
            return '';
        };

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

        const splitLargeDirectPoints = (points) => {
            const result = [];
            points.forEach(p => {
                const is8TException = (p.weight && p.weight > 5000) || (p.volume && p.volume > 26);
                const maxW = is8TException ? 7480 : 5000;
                const maxV = is8TException ? 55 : 26;
                if ((p.weight && p.weight > maxW) || (p.volume && p.volume > maxV)) {
                    let remW = p.weight || 0;
                    let remV = p.volume || 0;
                    let partIndex = 1;
                    while (remW > 0 || remV > 0) {
                        let fractionW = remW > 0 ? Math.min(1, maxW / remW) : 1;
                        let fractionV = remV > 0 ? Math.min(1, maxV / remV) : 1;
                        let fraction = Math.min(fractionW, fractionV);
                        
                        let takeW = parseFloat((remW * fraction).toFixed(2));
                        let takeV = parseFloat((remV * fraction).toFixed(2));
                        
                        if (takeW <= 0.01 && takeV <= 0.01) break;
                        if (takeW > remW) takeW = remW;
                        if (takeV > remV) takeV = remV;

                        result.push({
                            ...p,
                            name: `${p.name} (Phần ${partIndex})`,
                            weight: takeW,
                            volume: takeV,
                            originalPoints: p.originalPoints || [p.name],
                            use8TException: is8TException
                        });
                        
                        remW = parseFloat((remW - takeW).toFixed(2));
                        remV = parseFloat((remV - takeV).toFixed(2));
                        partIndex++;
                    }
                } else {
                    result.push({
                        ...p,
                        use8TException: is8TException
                    });
                }
            });
            return result;
        };

        let processedDirect = splitLargeDirectPoints(directPoints);
        let directTrips = [];

        // Exception 8T - run directly as single trips
        let remainingDirect = [];
        processedDirect.forEach(p => {
            if (p.use8TException) {
                const trip = createDirectTrip([p], hubDC, '8T');
                trip.districtsName = 'Ngoại lệ 8T';
                directTrips.push(trip);
            } else {
                remainingDirect.push(p);
            }
        });

        // Fixed route groups definition
        const ROUTE_GROUPS = [
            { id: 1, name: 'Tuyến 1: Thanh Thủy - Thanh Sơn', districts: ['Thanh Thủy', 'Thanh Sơn', 'Thanh Thuỷ'], points: [] },
            { id: 2, name: 'Tuyến 2: Yên Lập - Cẩm Khê', districts: ['Yên Lập', 'Cẩm Khê'], points: [] },
            { id: 3, name: 'Tuyến 3: Tam Nông - Lâm Thao', districts: ['Tam Nông', 'Lâm Thao'], points: [] },
            { id: 4, name: 'Tuyến 4: Đoan Hùng - Phù Ninh', districts: ['Đoan Hùng', 'Phù Ninh'], points: [] },
            { id: 5, name: 'Tuyến 5: Hạ Hòa - Thanh Ba', districts: ['Hạ Hòa', 'Hạ Hoà', 'Thanh Ba'], points: [] }
        ];
        let fallbackPoints = [];

        // Group points
        remainingDirect.forEach(p => {
            const distName = getDistrictForPoint(p);
            let matched = false;
            if (distName) {
                const normalized = distName.normalize('NFC').trim().toLowerCase();
                for (const group of ROUTE_GROUPS) {
                    for (const d of group.districts) {
                        const normD = d.normalize('NFC').trim().toLowerCase();
                        if (normalized === normD || normalized.includes(normD) || normD.includes(normalized)) {
                            group.points.push(p);
                            matched = true;
                            break;
                        }
                    }
                    if (matched) break;
                }
            }
            if (!matched) {
                fallbackPoints.push(p);
            }
        });

        // Resolve fallback points
        fallbackPoints.forEach(p => {
            let bestGroupId = 3;
            let minDist = Infinity;
            ROUTE_GROUPS.forEach(g => {
                if (g.points.length > 0) {
                    g.points.forEach(gp => {
                        const d = calculateDistance(p.coords, gp.coords);
                        if (d < minDist) {
                            minDist = d;
                            bestGroupId = g.id;
                        }
                    });
                }
            });
            const group = ROUTE_GROUPS.find(g => g.id === bestGroupId);
            group.points.push(p);
        });

        // Route Merging Logic (< 5 stores)
        let activeGroups = ROUTE_GROUPS.filter(g => g.points.length > 0);
        let mergedAny = true;
        while (mergedAny) {
            mergedAny = false;
            let bestMerge = null;
            
            for (let i = 0; i < activeGroups.length; i++) {
                const src = activeGroups[i];
                if (src.points.length > 0 && src.points.length < 5) {
                    for (let j = 0; j < activeGroups.length; j++) {
                        const tgt = activeGroups[j];
                        if (src.id === tgt.id || tgt.points.length === 0) continue;
                        
                        const distTgt = getChunkDistance(hubDC, tgt.points);
                        const wTgt = tgt.points.reduce((s,p) => s + (p.weight||0), 0);
                        const vTgt = tgt.points.reduce((s,p) => s + (p.volume||0), 0);
                        let truckTypeTgt = '1.9T';
                        if (wTgt > 2090 || vTgt > 14) truckTypeTgt = '5T';
                        const costTgt = getTripCostDetails(truckTypeTgt, distTgt, wTgt, 'Đi thẳng').totalCost;
                        
                        const mergedPoints = [...tgt.points, ...src.points];
                        const distMerged = getChunkDistance(hubDC, mergedPoints);
                        const wMerged = mergedPoints.reduce((s,p) => s + (p.weight||0), 0);
                        const vMerged = mergedPoints.reduce((s,p) => s + (p.volume||0), 0);
                        let truckTypeMerged = '1.9T';
                        if (wMerged > 2090 || vMerged > 14) truckTypeMerged = '5T';
                        if (wMerged > 5500 || vMerged > 26) truckTypeMerged = '8T';
                        
                        const costMerged = getTripCostDetails(truckTypeMerged, distMerged, wMerged, 'Đi thẳng').totalCost;
                        const costIncrease = costMerged - costTgt;
                        
                        if (costIncrease <= 1300000) {
                            if (bestMerge === null || costIncrease < bestMerge.costIncrease) {
                                bestMerge = {
                                    srcId: src.id,
                                    tgtId: tgt.id,
                                    costIncrease: costIncrease,
                                    mergedPoints: mergedPoints
                                };
                            }
                        }
                    }
                }
            }
            
            if (bestMerge) {
                const srcGroup = activeGroups.find(g => g.id === bestMerge.srcId);
                const tgtGroup = activeGroups.find(g => g.id === bestMerge.tgtId);
                tgtGroup.points = bestMerge.mergedPoints;
                srcGroup.points = [];
                activeGroups = activeGroups.filter(g => g.points.length > 0);
                mergedAny = true;
            }
        }

        // Packing options
        const packGroupPoints = (points, allow5T) => {
            const sortedPoints = [...points].sort((a,b) => (b.weight||0) - (a.weight||0));
            const maxW19T = 2090;
            const maxV19T = 14;
            const maxW5T = 5500;
            const maxV5T = 26;
            
            let tripsList = [];
            
            if (allow5T) {
                let pointsFor5T = [];
                let remainingPoints = [];
                let w5t = 0, v5t = 0;
                
                sortedPoints.forEach(p => {
                    if (w5t + (p.weight||0) <= maxW5T && v5t + (p.volume||0) <= maxV5T) {
                        pointsFor5T.push(p);
                        w5t += (p.weight||0);
                        v5t += (p.volume||0);
                    } else {
                        remainingPoints.push(p);
                    }
                });
                
                if (pointsFor5T.length > 0) {
                    tripsList.push({ points: pointsFor5T, type: '5T' });
                }
                
                let chunks19T = [];
                remainingPoints.forEach(p => {
                    let packed = false;
                    for (let i = 0; i < chunks19T.length; i++) {
                        let c = chunks19T[i];
                        if (c.w + (p.weight||0) <= maxW19T && c.v + (p.volume||0) <= maxV19T) {
                            c.points.push(p);
                            c.w += (p.weight||0);
                            c.v += (p.volume||0);
                            packed = true;
                            break;
                        }
                    }
                    if (!packed) {
                        chunks19T.push({
                            points: [p],
                            w: (p.weight||0),
                            v: (p.volume||0)
                        });
                    }
                });
                
                chunks19T.forEach(c => {
                    tripsList.push({ points: c.points, type: '1.9T' });
                });
            } else {
                let chunks19T = [];
                sortedPoints.forEach(p => {
                    let packed = false;
                    for (let i = 0; i < chunks19T.length; i++) {
                        let c = chunks19T[i];
                        if (c.w + (p.weight||0) <= maxW19T && c.v + (p.volume||0) <= maxV19T) {
                            c.points.push(p);
                            c.w += (p.weight||0);
                            c.v += (p.volume||0);
                            packed = true;
                            break;
                        }
                    }
                    if (!packed) {
                        chunks19T.push({
                            points: [p],
                            w: (p.weight||0),
                            v: (p.volume||0)
                        });
                    }
                });
                
                chunks19T.forEach(c => {
                    tripsList.push({ points: c.points, type: '1.9T' });
                });
            }
            return tripsList;
        };

        const calculateTripsCost = (tripsList) => {
            let totalCost = 0;
            tripsList.forEach(t => {
                const dist = getChunkDistance(hubDC, t.points);
                const w = t.points.reduce((s,p) => s + (p.weight||0), 0);
                const costDetails = getTripCostDetails(t.type, dist, w, 'Đi thẳng');
                totalCost += costDetails.totalCost;
            });
            return totalCost;
        };

        // Determine best groups to upgrade to 5T (max 2)
        const groupStats = activeGroups.map(g => {
            const tripsNoUpgrade = packGroupPoints(g.points, false);
            const costNoUpgrade = calculateTripsCost(tripsNoUpgrade);
            
            const tripsWithUpgrade = packGroupPoints(g.points, true);
            const costWithUpgrade = calculateTripsCost(tripsWithUpgrade);
            
            const saving = costNoUpgrade - costWithUpgrade;
            
            return {
                group: g,
                saving: saving,
                tripsNoUpgrade: tripsNoUpgrade,
                tripsWithUpgrade: tripsWithUpgrade
            };
        });

        groupStats.sort((a,b) => b.saving - a.saving);

        let upgraded5TCount = 0;
        groupStats.forEach(stat => {
            if (stat.saving > 0 && upgraded5TCount < 2) {
                stat.tripsWithUpgrade.forEach(t => {
                    const trip = createDirectTrip(t.points, hubDC, t.type);
                    trip.districtsName = stat.group.name.replace(/^(Tuyến \d+:\s*)/i, '').trim();
                    directTrips.push(trip);
                    if (t.type === '5T') {
                        upgraded5TCount++;
                    }
                });
            } else {
                stat.tripsNoUpgrade.forEach(t => {
                    const trip = createDirectTrip(t.points, hubDC, t.type);
                    trip.districtsName = stat.group.name.replace(/^(Tuyến \d+:\s*)/i, '').trim();
                    directTrips.push(trip);
                });
            }
        });

        // Sort direct trips by distance for UI presentation
        directTrips.sort((a, b) => (a.dist || 0) - (b.dist || 0));
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
