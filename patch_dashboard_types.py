import os

html_files = [
    r"g:\My Drive\Training AI\Supra Phú Thọ\demo.html",
    r"g:\My Drive\Training AI\Supra Phú Thọ\index.html"
]

for f_path in html_files:
    if os.path.exists(f_path):
        with open(f_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 1. Update colspan
        content = content.replace(
            '<th colspan="3"\n                                        style="padding: 10px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05);">\n                                        Xe Sử Dụng</th>',
            '<th colspan="2"\n                                        style="padding: 10px; text-align: center; border-bottom: 1px solid rgba(255,255,255,0.05); border-right: 1px solid rgba(255,255,255,0.05);">\n                                        Xe Sử Dụng</th>'
        )

        # 2. Update subheaders
        old_subheaders = """                                <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-dim);">
                                    <th
                                        style="padding: 5px 10px; text-align: center; font-size: 0.85rem; color: var(--text-main);">
                                        1.9T</th>
                                    <th
                                        style="padding: 5px 10px; text-align: center; font-size: 0.85rem; color: var(--secondary);">
                                        5T</th>
                                    <th
                                        style="padding: 5px 10px; text-align: center; font-size: 0.85rem; color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">
                                        8T</th>
                                </tr>"""
        new_subheaders = """                                <tr style="border-bottom: 1px solid var(--border-color); color: var(--text-dim);">
                                    <th
                                        style="padding: 5px 10px; text-align: center; font-size: 0.85rem; color: var(--secondary);">
                                        Trung Chuyển</th>
                                    <th
                                        style="padding: 5px 10px; text-align: center; font-size: 0.85rem; color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">
                                        Giao Thẳng</th>
                                </tr>"""
        content = content.replace(old_subheaders, new_subheaders)

        # 3. Update trips calculation in renderSummaryTable
        old_calc = """                                let c19 = 0, c5 = 0, c8 = 0;
                                let totalCost = 0;
                                trips.forEach(t => {
                                    if (t.truckType === '1.9T') c19++;
                                    else if (t.truckType === '5T') c5++;
                                    else if (t.truckType === '8T') c8++;
                                    totalCost += (typeof t.cost === 'number' ? t.cost : (t.cost && t.cost.total ? t.cost.total : 0));
                                });
                                item.truck19 = c19;
                                item.truck5 = c5;
                                item.truck8 = c8;
                                item.totalCost = totalCost;"""
        new_calc = """                                let c19 = 0, c5 = 0, c8 = 0;
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
                                item.totalCost = totalCost;"""
        content = content.replace(old_calc, new_calc)

        # 4. Update running totals
        old_totals = """                    let totalStoreCount = 0, totalTruck19 = 0, totalTruck5 = 0, totalTruck8 = 0, totalVolume = 0, totalWeight = 0, grandTotalCost = 0;
                    let summaryHTML = BOOKING_SUMMARY.map(item => {
                        totalStoreCount += (item.storeCount || 0);
                        totalTruck19 += (item.truck19 || 0);
                        totalTruck5 += (item.truck5 || 0);
                        totalTruck8 += (item.truck8 || 0);"""
        new_totals = """                    let totalStoreCount = 0, totalTruck19 = 0, totalTruck5 = 0, totalTruck8 = 0, totalTruckTransit = 0, totalTruckDirect = 0, totalVolume = 0, totalWeight = 0, grandTotalCost = 0;
                    let summaryHTML = BOOKING_SUMMARY.map(item => {
                        totalStoreCount += (item.storeCount || 0);
                        totalTruck19 += (item.truck19 || 0);
                        totalTruck5 += (item.truck5 || 0);
                        totalTruck8 += (item.truck8 || 0);
                        totalTruckTransit += (item.truckTransit || 0);
                        totalTruckDirect += (item.truckDirect || 0);"""
        content = content.replace(old_totals, new_totals)

        # 5. Update TD cells in table body
        old_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02);">${item.truck19 > 0 ? item.truck19 : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--secondary);">${item.truck5 > 0 ? item.truck5 : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${item.truck8 > 0 ? item.truck8 : '-'}</td>"""
        new_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--secondary);">${item.truckTransit > 0 ? item.truckTransit : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${item.truckDirect > 0 ? item.truckDirect : '-'}</td>"""
        content = content.replace(old_tds, new_tds)

        # 6. Update summary row TD cells
        old_sum_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold;">${totalTruck19 > 0 ? totalTruck19 : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--secondary);">${totalTruck5 > 0 ? totalTruck5 : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${totalTruck8 > 0 ? totalTruck8 : '-'}</td>"""
        new_sum_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--secondary);">${totalTruckTransit > 0 ? totalTruckTransit : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${totalTruckDirect > 0 ? totalTruckDirect : '-'}</td>"""
        content = content.replace(old_sum_tds, new_sum_tds)

        with open(f_path, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"Patched vehicle types in: {f_path}")
