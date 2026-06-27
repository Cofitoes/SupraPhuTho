import os

html_files = [
    r"g:\My Drive\Training AI\Supra Phú Thọ\demo.html",
    r"g:\My Drive\Training AI\Supra Phú Thọ\index.html"
]

for f_path in html_files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Inject Clear Cache button in HTML
        # Target area:
        # <button class="btn-primary" id="btn-run-optimization" style="display: inline-block;">Chạy Tối Ưu
        #     Tuyến</button>
        # We replace this block with the new layout
        old_btn_block = """                            <button class="btn-primary" id="btn-run-optimization" style="display: inline-block;">Chạy Tối Ưu
                                Tuyến</button>"""
        new_btn_block = """                            <button class="btn-primary" id="btn-run-optimization" style="display: inline-block;">Chạy Tối Ưu Tuyến</button>
                            <button class="btn-primary" id="btn-clear-cache" style="background-color: #ef4444; border-color: #ef4444;"><i class="fas fa-trash-alt"></i> Xóa Cache Hiển Thị</button>"""
        
        content = content.replace(old_btn_block, new_btn_block)
        # Fallback in case of slight space differences
        content = content.replace(
            '<button class="btn-primary" id="btn-run-optimization" style="display: inline-block;">Chạy Tối Ưu Tuyến</button>',
            '<button class="btn-primary" id="btn-run-optimization" style="display: inline-block;">Chạy Tối Ưu Tuyến</button>\n                            <button class="btn-primary" id="btn-clear-cache" style="background-color: #ef4444; border-color: #ef4444;"><i class="fas fa-trash-alt"></i> Xóa Cache Hiển Thị</button>'
        )

        # 2. Inject showToastNotification and update generateGhnTripsByDate function definition
        old_ghn_def = "        window.generateGhnTripsByDate = function () {"
        new_ghn_def = """        function showToastNotification(message, isSuccess = true) {
            const toastId = 'toast-' + Date.now();
            const bgStyle = isSuccess ? 'background: #10b981;' : 'background: #ef4444;';
            const icon = isSuccess ? 'fa-check-circle' : 'fa-exclamation-circle';
            const toastHtml = `
                <div class="toast" id="${toastId}" style="${bgStyle} position: fixed; bottom: 20px; top: auto; right: 20px; z-index: 999999;">
                    <i class="fas ${icon}" style="font-size: 1.25rem;"></i>
                    <p style="margin:0; font-size:0.95rem; font-weight:600;">${message}</p>
                </div>
            `;
            document.body.insertAdjacentHTML('beforeend', toastHtml);
            setTimeout(() => {
                const toast = document.getElementById(toastId);
                if (toast) {
                    toast.classList.add('hide');
                    setTimeout(() => toast.remove(), 500);
                }
            }, 3000);
        }

        window.generateGhnTripsByDate = function (forceRecalculate = false) {"""
        
        content = content.replace(old_ghn_def, new_ghn_def)

        # 3. Inject caching checks at the start of generateGhnTripsByDate
        old_ghn_start = """            let formattedDate = val;

            if (typeof BOOKING_DELIVERY_POINTS === 'undefined') {"""
        new_ghn_start = """            let formattedDate = val;

            const cacheKey = 'supra_trips_ghn_cache_' + val;
            const cachedData = localStorage.getItem(cacheKey);

            if (!forceRecalculate && cachedData) {
                try {
                    const cachedTrips = JSON.parse(cachedData);
                    if (cachedTrips && cachedTrips.length > 0) {
                        globalTrips = cachedTrips;
                        window.renderTripsTable();
                        return;
                    }
                } catch (err) {
                    console.error('Failed to load GHN trips from cache:', err);
                }
            }

            if (typeof BOOKING_DELIVERY_POINTS === 'undefined') {"""

        content = content.replace(old_ghn_start, new_ghn_start)

        # 4. Save GHN trips to cache and fetch distances
        old_ghn_end = """            if (typeof generateTrips === 'function') {
                globalTrips = safeGenerateTrips();
                window.renderTripsTable(); // Re-render main table if needed
            }"""
        new_ghn_end = """            if (typeof generateTrips === 'function') {
                globalTrips = safeGenerateTrips();
                localStorage.setItem(cacheKey, JSON.stringify(globalTrips));
                window.renderTripsTable();
                const runId = ++currentRunId;
                fetchActualDistances(globalTrips, runId, val);
            }"""

        content = content.replace(old_ghn_end, new_ghn_end)

        # 5. Inject cache check in standard optimization button click handler
        old_opt_handler = """            document.getElementById('btn-run-optimization').addEventListener('click', () => {
                const runId = ++currentRunId;
                const dateVal = document.getElementById('global-date-filter').value;

                try {
                    globalTrips = safeGenerateTrips();"""
        new_opt_handler = """            document.getElementById('btn-run-optimization').addEventListener('click', (e) => {
                const runId = ++currentRunId;
                const dateVal = document.getElementById('global-date-filter').value;

                const cacheKey = 'supra_trips_cache_' + dateVal;
                const cachedData = localStorage.getItem(cacheKey);

                const isProgrammatic = e && (e.isTrusted === false || e.pointerType === '');
                const shouldLoadCache = isProgrammatic && cachedData && !window.forceRecalculate;

                if (shouldLoadCache) {
                    try {
                        const cachedTrips = JSON.parse(cachedData);
                        if (cachedTrips && cachedTrips.length > 0) {
                            globalTrips = cachedTrips;
                            DELIVERY_POINTS.forEach(p => {
                                let isInTrip = false;
                                let isTransit = false;
                                for (const trip of globalTrips) {
                                    const isDirectPoint = trip.points.some(pt => pt.name === p.name) || (trip.groupedPoints && trip.groupedPoints.includes(p.name));
                                    const isTransitPoint = trip.points.some(pt => pt.originalPoints && pt.originalPoints.includes(p.name));
                                    if (isDirectPoint || isTransitPoint) {
                                        isInTrip = true;
                                        if (trip.tripType === 'Trung chuyển') {
                                            isTransit = true;
                                        }
                                        break;
                                    }
                                }
                                if (p.coords && p.coords.lat && p.coords.lng) {
                                    p.isScheduled = isInTrip;
                                    if (isInTrip) {
                                        p.error = isTransit ? 'Chuyển về GXT' : null;
                                    } else {
                                        p.error = 'Không thỏa logic ghép chuyến';
                                    }
                                } else {
                                    p.isScheduled = false;
                                    p.error = 'Lỗi Tọa Độ';
                                }
                            });
                            window.renderPendingPoints();
                            renderResults();
                            calculateOTP();
                            return;
                        }
                    } catch (err) {
                        console.error('Failed to load standard trips from cache:', err);
                    }
                }

                window.forceRecalculate = false;

                try {
                    globalTrips = safeGenerateTrips();"""

        content = content.replace(old_opt_handler, new_opt_handler)

        # 6. Save standard calculated state to cache initially and after OSRM progressive updates
        old_osrm_save = """                                        const details = getTripCostDetails(t.truckType, t.dist, t.totalWeight, t.tripType);
                                        t.costBase = details.baseCost;
                                        t.costExtraKm = details.extraCost;
                                        t.costBocXep = details.loadingCost;
                                        t.cost = details.totalCost;
                                        
                                        t.unitCost = t.cost / (t.totalWeight || 1);
                                    }
                                }
                            } catch (err) {"""
        new_osrm_save = """                                        const details = getTripCostDetails(t.truckType, t.dist, t.totalWeight, t.tripType);
                                        t.costBase = details.baseCost;
                                        t.costExtraKm = details.extraCost;
                                        t.costBocXep = details.loadingCost;
                                        t.cost = details.totalCost;
                                        
                                        t.unitCost = t.cost / (t.totalWeight || 1);

                                        localStorage.setItem('supra_trips_cache_' + dateVal, JSON.stringify(trips));
                                    }
                                }
                            } catch (err) {"""

        content = content.replace(old_osrm_save, new_osrm_save)

        # Also add initial cache save in opt handler
        old_opt_save_target = """                    window.renderPendingPoints();
                    renderResults();
                    calculateOTP();

                    // Background asynchronous OSRM routing fetches
                    fetchActualDistances(globalTrips, runId, dateVal);"""
        new_opt_save_target = """                    window.renderPendingPoints();
                    renderResults();
                    calculateOTP();

                    localStorage.setItem(cacheKey, JSON.stringify(globalTrips));

                    // Background asynchronous OSRM routing fetches
                    fetchActualDistances(globalTrips, runId, dateVal);"""

        content = content.replace(old_opt_save_target, new_opt_save_target)

        # 7. Register btn-clear-cache listener inside DOMContentLoaded
        # We search for the place where btn-run-optimization is bound
        old_opt_listener_spot = "            document.getElementById('btn-run-optimization').addEventListener('click', (e) => {"
        new_opt_listener_spot = """            // Register clear cache button listener
            const btnClear = document.getElementById('btn-clear-cache');
            if (btnClear) {
                btnClear.addEventListener('click', () => {
                    const dateVal = document.getElementById('global-date-filter').value;
                    for (let i = localStorage.length - 1; i >= 0; i--) {
                        const key = localStorage.key(i);
                        if (key && (key.startsWith('supra_trips_cache_') || key.startsWith('supra_trips_ghn_cache_'))) {
                            localStorage.removeItem(key);
                        }
                    }
                    window.lastGeneratedType = '';
                    window.forceRecalculate = true;
                    showToastNotification('Đã xóa toàn bộ cache hiển thị và tính toán lại!');
                    const activeLi = document.querySelector('nav li.active');
                    const activeTab = activeLi ? activeLi.dataset.tab : '';
                    if (activeTab === 'create-ghn-trips') {
                        if (typeof window.generateGhnTripsByDate === 'function') {
                            window.generateGhnTripsByDate(true);
                        }
                    } else {
                        const btnOpt = document.getElementById('btn-run-optimization');
                        if (btnOpt) btnOpt.click();
                    }
                });
            }

            document.getElementById('btn-run-optimization').addEventListener('click', (e) => {"""

        content = content.replace(old_opt_listener_spot, new_opt_listener_spot)

        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched clear cache system in: {f_path}")
