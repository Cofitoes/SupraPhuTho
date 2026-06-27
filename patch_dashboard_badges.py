import os

html_files = [
    r"g:\My Drive\Training AI\Supra Phú Thọ\demo.html",
    r"g:\My Drive\Training AI\Supra Phú Thọ\index.html"
]

for f_path in html_files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Replace the trips loop calculation
        old_calc = """                                let c19 = 0, c5 = 0, c8 = 0;
                                let cTransit = 0, cDirect = 0;
                                let totalCost = 0;
                                trips.forEach(t => {
                                    if (t.truckType === '1.9T') c19++;
                                    else if (t.truckType === '5T') c5++;
                                    else if (t.truckType === '8T') c8++;
                                    
                                    if (t.tripType === 'Trung chuyển') cTransit++;
                                    else cDirect++;
                                    
                                    totalCost += (typeof t.cost === 'number' ? t.cost : (t.cost && t.cost.total ? t.cost.total : 0));
                                });
                                item.truck19 = c19;
                                item.truck5 = c5;
                                item.truck8 = c8;
                                item.truckTransit = cTransit;
                                item.truckDirect = cDirect;
                                item.totalCost = totalCost;
                                item.trucksCalculated = true;"""
                                
        new_calc = """                                let c19 = 0, c5 = 0, c8 = 0;
                                let t19 = 0, t5 = 0, t8 = 0;
                                let d19 = 0, d5 = 0, d8 = 0;
                                let cTransit = 0, cDirect = 0;
                                let totalCost = 0;
                                trips.forEach(t => {
                                    const isTransit = t.tripType === 'Trung chuyển';
                                    if (t.truckType === '1.9T') {
                                        c19++;
                                        if (isTransit) t19++; else d19++;
                                    } else if (t.truckType === '5T') {
                                        c5++;
                                        if (isTransit) t5++; else d5++;
                                    } else if (t.truckType === '8T') {
                                        c8++;
                                        if (isTransit) t8++; else d8++;
                                    }
                                    
                                    if (isTransit) cTransit++;
                                    else cDirect++;
                                    
                                    totalCost += (typeof t.cost === 'number' ? t.cost : (t.cost && t.cost.total ? t.cost.total : 0));
                                });
                                item.truck19 = c19;
                                item.truck5 = c5;
                                item.truck8 = c8;
                                item.truckTransit = cTransit;
                                item.truckDirect = cDirect;
                                item.breakdown = {
                                    transit: { t19, t5, t8 },
                                    direct: { d19, d5, d8 }
                                };
                                item.totalCost = totalCost;
                                item.trucksCalculated = true;"""
        content = content.replace(old_calc, new_calc)

        # 2. Replace the running totals line
        old_totals = """                    let totalStoreCount = 0, totalTruck19 = 0, totalTruck5 = 0, totalTruck8 = 0, totalTruckTransit = 0, totalTruckDirect = 0, totalVolume = 0, totalWeight = 0, grandTotalCost = 0;
                    let summaryHTML = BOOKING_SUMMARY.map(item => {
                        totalStoreCount += (item.storeCount || 0);
                        totalTruck19 += (item.truck19 || 0);
                        totalTruck5 += (item.truck5 || 0);
                        totalTruck8 += (item.truck8 || 0);
                        totalTruckTransit += (item.truckTransit || 0);
                        totalTruckDirect += (item.truckDirect || 0);
                        totalVolume += (item.totalVolume || 0);
                        totalWeight += (item.totalWeight || 0);
                        grandTotalCost += (item.totalCost || 0);"""
                        
        new_totals = """                    let totalStoreCount = 0, totalTruck19 = 0, totalTruck5 = 0, totalTruck8 = 0, totalTruckTransit = 0, totalTruckDirect = 0, totalVolume = 0, totalWeight = 0, grandTotalCost = 0;
                    let grandTransit = { t19: 0, t5: 0, t8: 0 };
                    let grandDirect = { d19: 0, d5: 0, d8: 0 };
                    
                    const formatBreakdownHTML = (c19, c5, c8) => {
                        let html = '';
                        if (c19 > 0) html += `<span style="background: rgba(255, 255, 255, 0.05); color: #cbd5e1; border: 1px solid rgba(255, 255, 255, 0.1); padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; margin: 2px; display: inline-block; font-weight: bold;">${c19}x1.9T</span>`;
                        if (c5 > 0) html += `<span style="background: rgba(99, 102, 241, 0.15); color: #a5b4fc; border: 1px solid rgba(99, 102, 241, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; margin: 2px; display: inline-block; font-weight: bold;">${c5}x5T</span>`;
                        if (c8 > 0) html += `<span style="background: rgba(245, 158, 11, 0.15); color: #fde047; border: 1px solid rgba(245, 158, 11, 0.3); padding: 2px 6px; border-radius: 4px; font-size: 0.8rem; margin: 2px; display: inline-block; font-weight: bold;">${c8}x8T</span>`;
                        return html || '<span style="color: var(--text-dim); font-weight: bold;">-</span>';
                    };

                    let summaryHTML = BOOKING_SUMMARY.map(item => {
                        totalStoreCount += (item.storeCount || 0);
                        totalTruck19 += (item.truck19 || 0);
                        totalTruck5 += (item.truck5 || 0);
                        totalTruck8 += (item.truck8 || 0);
                        totalTruckTransit += (item.truckTransit || 0);
                        totalTruckDirect += (item.truckDirect || 0);
                        totalVolume += (item.totalVolume || 0);
                        totalWeight += (item.totalWeight || 0);
                        grandTotalCost += (item.totalCost || 0);
                        
                        if (item.breakdown) {
                            grandTransit.t19 += item.breakdown.transit.t19;
                            grandTransit.t5 += item.breakdown.transit.t5;
                            grandTransit.t8 += item.breakdown.transit.t8;
                            
                            grandDirect.d19 += item.breakdown.direct.d19;
                            grandDirect.d5 += item.breakdown.direct.d5;
                            grandDirect.d8 += item.breakdown.direct.d8;
                        }"""
        content = content.replace(old_totals, new_totals)

        # 3. Replace body rows TDs
        old_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--secondary);">${item.truckTransit > 0 ? item.truckTransit : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${item.truckDirect > 0 ? item.truckDirect : '-'}</td>"""
                            
        new_tds = """                            <td style="padding: 10px; text-align: center; background: rgba(255,255,255,0.02);">${formatBreakdownHTML(item.breakdown ? item.breakdown.transit.t19 : 0, item.breakdown ? item.breakdown.transit.t5 : 0, item.breakdown ? item.breakdown.transit.t8 : 0)}</td>
                            <td style="padding: 10px; text-align: center; background: rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.05);">${formatBreakdownHTML(item.breakdown ? item.breakdown.direct.d19 : 0, item.breakdown ? item.breakdown.direct.d5 : 0, item.breakdown ? item.breakdown.direct.d8 : 0)}</td>"""
        content = content.replace(old_tds, new_tds)

        # 4. Replace summary row TDs
        old_sum_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--secondary);">${totalTruckTransit > 0 ? totalTruckTransit : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${totalTruckDirect > 0 ? totalTruckDirect : '-'}</td>"""
                            
        new_sum_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold;">${formatBreakdownHTML(grandTransit.t19, grandTransit.t5, grandTransit.t8)}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; border-right: 1px solid rgba(255,255,255,0.05);">${formatBreakdownHTML(grandDirect.d19, grandDirect.d5, grandDirect.d8)}</td>"""
        content = content.replace(old_sum_tds, new_sum_tds)

        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched vehicle badges in: {f_path}")
