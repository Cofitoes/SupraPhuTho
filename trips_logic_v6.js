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
    // STEP 2: DIRECT DELIVERY (Giao thẳng)
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

        const routeGroups = [
            {
                name: "Tuyến 1: Thanh Thủy - Thanh Sơn",
                districts: ["H. Thanh Thủy", "H. Thanh Sơn"]
            },
            {
                name: "Tuyến 2: Yên Lập - Cẩm Khê",
                districts: ["H. Yên Lập", "H. Cẩm Khê"]
            },
            {
                name: "Tuyến 3: Tam Nông - Lâm Thao",
                districts: ["H. Tam Nông", "H. Lâm Thao"]
            },
            {
                name: "Tuyến 4: Đoan Hùng - Phù Ninh",
                districts: ["H. Đoan Hùng", "H. Phù Ninh"]
            },
            {
                name: "Tuyến 5: Hạ Hòa - Thanh Ba",
                districts: ["H. Hạ Hoà", "H. Hạ Hòa", "H. Thanh Ba"]
            }
        ];

        const packGroupIntoTripsLocal = (points, allow5T = true) => {
            let remaining = [...points];
            let groupTrips = [];
            while (remaining.length > 0) {
                let chunk = [];
                let cw = 0, cv = 0;
                let truckType = '1.9T';
                
                let i = 0;
                while (i < remaining.length) {
                    const p = remaining[i];
                    if (cw + (p.weight || 0) <= 2090 && cv + (p.volume || 0) <= 14) {
                        chunk.push(p);
                        cw += (p.weight || 0);
                        cv += (p.volume || 0);
                        remaining.splice(i, 1);
                    } else if (allow5T && cw + (p.weight || 0) <= 5500 && cv + (p.volume || 0) <= 26) {
                        truckType = '5T';
                        chunk.push(p);
                        cw += (p.weight || 0);
                        cv += (p.volume || 0);
                        remaining.splice(i, 1);
                    } else {
                        i++;
                    }
                }
                
                if (chunk.length === 0) {
                    const p = remaining.shift();
                    chunk.push(p);
                    truckType = allow5T ? '5T' : '1.9T';
                    cw += (p.weight || 0);
                    cv += (p.volume || 0);
                }
                
                const trip = createDirectTrip(chunk, hubDC, truckType);
                groupTrips.push(trip);
            }
            return groupTrips;
        };

        // Group points by route group and calculate total weight
        let groupsData = routeGroups.map(group => {
            const groupPoints = directPoints.filter(p => {
                const pDistrict = getDistrictForPoint(p);
                if (!pDistrict) return false;
                return group.districts.some(d => {
                    const normD = d.toLowerCase().replace(/^(h\.|tp\.)\s*/, '').trim();
                    const normP = pDistrict.toLowerCase().replace(/^(h\.|tp\.)\s*/, '').trim();
                    return normD === normP;
                });
            });
            const totalWeight = groupPoints.reduce((sum, p) => sum + (p.weight || 0), 0);
            return {
                group,
                points: groupPoints,
                totalWeight
            };
        }).filter(g => g.points.length > 0);

        // Temporarily pack all groups allowing 5T
        let tempTrips = [];
        groupsData.forEach(g => {
            const trips = packGroupIntoTripsLocal(g.points, true);
            tempTrips.push(...trips.map(t => ({...t, groupRef: g})));
        });

        // Count 5T trucks proposed
        let num5T = tempTrips.filter(t => t.truckType === '5T').length;
        
        let directTrips = [];
        if (num5T <= 2) {
            // Keep the proposed trips
            tempTrips.forEach(t => {
                t.districtsName = t.groupRef.group.name.replace(/^Tuyến \d+:\s*/, '');
            });
            directTrips = tempTrips;
        } else {
            // Rank groups by weight and restrict the excess ones to 1.9T only
            let groupsNeeding5T = [];
            tempTrips.forEach(t => {
                if (t.truckType === '5T' && !groupsNeeding5T.includes(t.groupRef)) {
                    groupsNeeding5T.push(t.groupRef);
                }
            });

            groupsNeeding5T.sort((a, b) => b.totalWeight - a.totalWeight);
            const allowedGroups = groupsNeeding5T.slice(0, 2);

            groupsData.forEach(g => {
                const allow5T = allowedGroups.includes(g);
                const trips = packGroupIntoTripsLocal(g.points, allow5T);
                trips.forEach(t => {
                    t.districtsName = g.group.name.replace(/^Tuyến \d+:\s*/, '');
                });
                directTrips.push(...trips);
            });
        }

        // Sort direct delivery trips by distance for display ordering
        directTrips.sort((a, b) => (a.dist || a.distance || 0) - (b.dist || b.distance || 0));

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
