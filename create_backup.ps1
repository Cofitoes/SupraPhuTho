$files = @(
    "index.html",
    "demo.html",
    "style.css",
    "trips_logic2.js",
    "run_pipeline.ps1",
    "update_stores_pipeline.ps1",
    "extract_summary.ps1",
    "register_protocol.ps1",
    "Cap_Nhat_Du_Lieu.bat",
    "vercel.json",
    "download_booking_emails.py",
    "fetch_confirm_times.py",
    "extract_vehicles.py",
    "process_checkin.py",
    "update_store_data.py",
    "auto_add_new_stores.py",
    "project_context.md",
    "DS_Cua_Hang.xlsm",
    "store_data.js",
    "booking_data.js",
    "summary_data.js",
    "email_data.js",
    "departure_times.js",
    "vehicle_data.js",
    "checkin_data.js",
    "process_incidents.py",
    "incidents_data.js",
    "local_server.py",
    "Chay_Giao_Dien.bat",
    "dat_lich_tu_dong.ps1",
    "Dat_Lich_Tu_Dong.bat"
)

$workDir = $PSScriptRoot
$tempZip = Join-Path $env:TEMP "backup_temp.zip"
if (Test-Path $tempZip) { Remove-Item $tempZip -Force }

# Create temporary zip archive of the files
$filePaths = $files | ForEach-Object { Join-Path $workDir $_ }
Compress-Archive -Path $filePaths -DestinationPath $tempZip -Force

# Convert zip to Base64
$bytes = [System.IO.File]::ReadAllBytes($tempZip)
$base64 = [System.Convert]::ToBase64String($bytes)

# Get current date info
$date = Get-Date
$dateStr = $date.ToString("yyyy-MM-dd")
$fileDateStr = "$($date.Day)$($date.Month)$($date.Year)"

# Create the self-extracting hybrid BAT/PowerShell restore script
$restoreScriptContent = @"
<# :
@echo off
powershell -NoProfile -ExecutionPolicy Bypass -Command "iex ((Get-Content -LiteralPath '%~f0' -Encoding UTF8) -join [char]10)"
exit /b
#>
# Self-extracting restore script for Logistics Hub Setup
# Backup Date: $dateStr
# Created by Antigravity

`$confirm = Read-Host "Ban co muon khoi phuc toan bo thiet lap (setup) cua Logistics Hub tu file sao luu nay khong? (Y/N)"
if (`$confirm -ne "Y" -and `$confirm -ne "y") {
    Write-Host "Da huy khoi phuc."
    Exit
}

Write-Host "Dang khoi phuc cac file thiet lap..."
`$base64Data = "$base64"

`$tempZip = Join-Path `$env:TEMP "restore_temp.zip"
`$bytes = [System.Convert]::FromBase64String(`$base64Data)
[System.IO.File]::WriteAllBytes(`$tempZip, `$bytes)

`$currentDir = Get-Location
Expand-Archive -Path `$tempZip -DestinationPath `$currentDir -Force
Remove-Item `$tempZip -Force

Write-Host "Da khoi phuc thanh cong toan bo 31 file thiet lap va du lieu vao thu muc hien tai:"
Write-Host "1. index.html"
Write-Host "2. demo.html"
Write-Host "3. style.css"
Write-Host "4. trips_logic2.js"
Write-Host "5. run_pipeline.ps1"
Write-Host "6. update_stores_pipeline.ps1"
Write-Host "7. extract_summary.ps1"
Write-Host "8. register_protocol.ps1"
Write-Host "9. Cap_Nhat_Du_Lieu.bat"
Write-Host "10. vercel.json"
Write-Host "11. download_booking_emails.py"
Write-Host "12. fetch_confirm_times.py"
Write-Host "13. extract_vehicles.py"
Write-Host "14. process_checkin.py"
Write-Host "15. update_store_data.py"
Write-Host "16. auto_add_new_stores.py"
Write-Host "17. project_context.md"
Write-Host "18. DS_Cua_Hang.xlsm"
Write-Host "19. store_data.js"
Write-Host "20. booking_data.js"
Write-Host "21. summary_data.js"
Write-Host "22. email_data.js"
Write-Host "23. departure_times.js"
Write-Host "24. vehicle_data.js"
Write-Host "25. checkin_data.js"
Write-Host "26. process_incidents.py"
Write-Host "27. incidents_data.js"
Write-Host "28. local_server.py"
Write-Host "29. Chay_Giao_Dien.bat"
Write-Host "30. dat_lich_tu_dong.ps1"
Write-Host "31. Dat_Lich_Tu_Dong.bat"
Write-Host ""
Write-Host "Dang tu dong chay dang ky lai giao thuc logisticsupdate://..."
powershell.exe -ExecutionPolicy Bypass -File ".\register_protocol.ps1"

Write-Host "Hoan thanh! Hay F5 lai trang hoac bat dau chay file bat de dong bo du lieu."
Pause
"@

# Clean old backup files from workDir
Get-ChildItem -Path $workDir -Filter "backup*.bat" | ForEach-Object {
    Remove-Item $_.FullName -Force -ErrorAction SilentlyContinue
}

$outputScriptPath = Join-Path $workDir "backup$fileDateStr.bat"
Set-Content -Path $outputScriptPath -Value $restoreScriptContent -Encoding UTF8
Write-Host "Backup script created successfully at $outputScriptPath"
Remove-Item $tempZip -Force

