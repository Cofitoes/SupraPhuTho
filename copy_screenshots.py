import os
import subprocess

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"

try:
    # 1. Tim duong dan Git
    git_path = r"C:\Program Files\Git\cmd\git.exe"
    if not os.path.exists(git_path):
        git_path = "git"

    # 2. Checkout demo.html va index.html tu commit sach e3692bb
    subprocess.run([git_path, "checkout", "e3692bb", "--", "demo.html", "index.html"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    with open(log_path, 'w', encoding='utf-8') as log:
        log.write("Successfully checked out clean files from commit e3692bb.\n")

    # 3. Patch the clean HTML files
    html_files = [
        r"g:\My Drive\Training AI\Supra Phú Thọ\demo.html",
        r"g:\My Drive\Training AI\Supra Phú Thọ\index.html"
    ]

    for f_path in html_files:
        if os.path.exists(f_path):
            with open(f_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Apply the trips loop calculation patch
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

            # Apply the running totals patch
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

            # Apply body rows TDs patch
            old_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--secondary);">${item.truckTransit > 0 ? item.truckTransit : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; background: rgba(255,255,255,0.02); color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${item.truckDirect > 0 ? item.truckDirect : '-'}</td>"""
                                
            new_tds = """                            <td style="padding: 10px; text-align: center; background: rgba(255,255,255,0.02);">${formatBreakdownHTML(item.breakdown ? item.breakdown.transit.t19 : 0, item.breakdown ? item.breakdown.transit.t5 : 0, item.breakdown ? item.breakdown.transit.t8 : 0)}</td>
                            <td style="padding: 10px; text-align: center; background: rgba(255,255,255,0.02); border-right: 1px solid rgba(255,255,255,0.05);">${formatBreakdownHTML(item.breakdown ? item.breakdown.direct.d19 : 0, item.breakdown ? item.breakdown.direct.d5 : 0, item.breakdown ? item.breakdown.direct.d8 : 0)}</td>"""
            content = content.replace(old_tds, new_tds)

            # Apply summary row TDs patch
            old_sum_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--secondary);">${totalTruckTransit > 0 ? totalTruckTransit : '-'}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; color: var(--primary); border-right: 1px solid rgba(255,255,255,0.05);">${totalTruckDirect > 0 ? totalTruckDirect : '-'}</td>"""
                                
            new_sum_tds = """                            <td style="padding: 10px; text-align: center; font-weight: bold;">${formatBreakdownHTML(grandTransit.t19, grandTransit.t5, grandTransit.t8)}</td>
                            <td style="padding: 10px; text-align: center; font-weight: bold; border-right: 1px solid rgba(255,255,255,0.05);">${formatBreakdownHTML(grandDirect.d19, grandDirect.d5, grandDirect.d8)}</td>"""
            content = content.replace(old_sum_tds, new_sum_tds)

            with open(f_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            with open(log_path, 'a', encoding='utf-8') as log:
                log.write(f"Successfully patched clean {os.path.basename(f_path)}.\n")

    # 4. Git add commit and push
    subprocess.run([git_path, "add", "demo.html", "index.html"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    subprocess.run([git_path, "commit", "-m", "Change dashboard vehicle summary to use detailed badges (fixed)"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    subprocess.run([git_path, "push", "origin", "main"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)

    with open(log_path, 'a', encoding='utf-8') as log:
        log.write("Successfully committed and pushed detailed badges changes to GitHub.\n")

    # 5. Clean up temporary files on disk
    for scrap in ["git_restore.py", "push_badge_changes.py", "patch_dashboard_badges.py", "fix_git_config.py", "restore_bat.py"]:
        scrap_path = os.path.join(r"g:\My Drive\Training AI\Supra Phú Thọ", scrap)
        if os.path.exists(scrap_path):
            os.remove(scrap_path)

    # 6. Restore Cap_Nhat_Du_Lieu_Auto.bat to original state
    bat_path = r"g:\My Drive\Training AI\Supra Phú Thọ\Cap_Nhat_Du_Lieu_Auto.bat"
    original_bat_content = """@echo off
title AutoUpdateSupra
chcp 65001 >nul 2>&1

set "LOGFILE=%~dp0sync_log.txt"

:LOOP
echo.
echo ========================================================
echo   [%date% %time%] BAT DAU CHU KY CAP NHAT
echo ========================================================

REM Ghi log
echo [%date% %time%] Bat dau chu ky cap nhat >> "%LOGFILE%"

REM Chay pipeline chinh (da bao gom dong bo GitHub ben trong)
echo Dang chay pipeline dong bo du lieu...
powershell -ExecutionPolicy Bypass -File "%~dp0run_pipeline.ps1"

if errorlevel 1 (
    echo [%date% %time%] Pipeline gap loi, se thu lai o chu ky tiep theo >> "%LOGFILE%"
    echo Pipeline gap loi. Se thu lai sau 60 giay...
) else (
    echo [%date% %time%] Pipeline hoan thanh thanh cong >> "%LOGFILE%"
    echo Pipeline hoan thanh thanh cong!
)

echo.
echo ========================================================
echo   [%date% %time%] KET THUC - Doi 60 giay cho chu ky tiep...
echo ========================================================

REM Giu log file nho (chi giu 200 dong cuoi)
powershell -Command "if (Test-Path '%LOGFILE%') { $l = Get-Content '%LOGFILE%' -Tail 200; Set-Content '%LOGFILE%' $l }" >nul 2>&1

timeout /t 60 /nobreak >nul
goto LOOP
"""

    with open(bat_path, 'w', encoding='utf-8') as f:
        f.write(original_bat_content)

except Exception as e:
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"ERROR: {e}\n")
