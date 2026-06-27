import os
import subprocess

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"

try:
    # 1. Path to JS files
    logic_path = r"g:\My Drive\Training AI\Supra Phú Thọ\trips_logic_v6.js"
    booking_path = r"g:\My Drive\Training AI\Supra Phú Thọ\booking_data.js"
    store_path = r"g:\My Drive\Training AI\Supra Phú Thọ\store_data.js"
    gxt_path = r"g:\My Drive\Training AI\Supra Phú Thọ\gxt_stores.js"

    # 2. Build JS execution string
    js_code = """
    const fs = require('fs');
    
    // Mock browser environment
    global.window = global;
    global.HUBS = [
        { id: 'QM', name: 'Kho DC Win Phú Thọ', coords: { lat: 21.3879985, lng: 105.1803274 } },
        { id: 'GXT', name: 'GXT Phú Thọ', coords: { lat: 21.3264875, lng: 105.3246094 } }
    ];
    global.CONFIG = { START_TIME: "08:00", AVG_SPEED_KMH: 50, UNLOADING_TIME_MIN: 30 };
    global.calculateDistance = (c1, c2) => {
        if (!c1 || !c2) return 0;
        const R = 6371;
        const dLat = (c2.lat - c1.lat) * Math.PI / 180;
        const dLng = (c2.lng - c1.lng) * Math.PI / 180;
        const a = Math.sin(dLat/2) * Math.sin(dLat/2) +
                  Math.cos(c1.lat * Math.PI / 180) * Math.cos(c2.lat * Math.PI / 180) *
                  Math.sin(dLng/2) * Math.sin(dLng/2);
        return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1-a));
    };
    global.addMinutes = (time, mins) => {
        let [h, m] = time.split(':').map(Number);
        m += mins;
        h += Math.floor(m / 60);
        m %= 60;
        return `${String(h).padStart(2, '0')}:${String(m).padStart(2, '0')}`;
    };
    
    // Load store data, gxt stores, booking data
    eval(fs.readFileSync('""" + store_path.replace('\\', '/') + """', 'utf8'));
    eval(fs.readFileSync('""" + gxt_path.replace('\\', '/') + """', 'utf8'));
    eval(fs.readFileSync('""" + booking_path.replace('\\', '/') + """', 'utf8'));
    
    // Filter booking points for 2026-06-29
    global.DELIVERY_POINTS = BOOKING_DELIVERY_POINTS.filter(p => p.date === '2026-06-29');
    
    // Load logic
    eval(fs.readFileSync('""" + logic_path.replace('\\', '/') + """', 'utf8'));
    
    const trips = generateTrips();
    const transitTrips = trips.filter(t => t.tripType === 'Trung chuyển');
    console.log("TRANSIT_TRIPS_COUNT=" + transitTrips.length);
    transitTrips.forEach((t, i) => {
        console.log(`TRIP_${i+1}: ID=${t.id}, Truck=${t.truckType}, Weight=${t.totalWeight}kg, Volume=${t.totalVolume}m3, Route=${t.route}`);
    });
    """

    # 3. Execute with Node.js
    proc = subprocess.run(["node", "-e", js_code], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", capture_output=True, text=True)
    
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("=== JS Evaluation stdout ===\n")
        log.write(proc.stdout)
        log.write("=== JS Evaluation stderr ===\n")
        log.write(proc.stderr)

except Exception as e:
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write(f"ERROR: {e}\n")
