# ========================================================
# AUTO CHECK EMAIL - Tự động quét email và cập nhật Booking
# Chạy liên tục, lặp lại mỗi 30 phút
# ========================================================
Set-Location $PSScriptRoot
$ErrorActionPreference = "Continue"

$intervalMinutes = 30
$logFile = ".\auto_check_email.log"

function Write-Log([string]$message) {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $line = "[$timestamp] $message"
    Write-Host $line
    Add-Content -Path $logFile -Value $line -Encoding UTF8
}

Write-Host "========================================================"
Write-Host "  AUTO CHECK EMAIL - Cap nhat Booking tu dong moi $intervalMinutes phut"
Write-Host "  Nhan Ctrl+C de dung."
Write-Host "========================================================"
Write-Host ""

while ($true) {
    Write-Log "=== BAT DAU QUET EMAIL VA CAP NHAT BOOKING ==="
    
    $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
    if (-not (Test-Path $pythonPath)) {
        $pythonPath = "python"
    }
    $env:PYTHONIOENCODING = "utf-8"
    
    # Buoc 1: Tai file dinh kem tu Email
    try {
        Write-Log "Buoc 1/4: Dang quet email va tai file Booking..."
        & $pythonPath ".\download_booking_emails.py" 2>&1 | ForEach-Object { Write-Log "  [EMAIL] $_" }
        Write-Log "Buoc 1/4: Hoan thanh!"
    } catch {
        Write-Log "LOI Buoc 1: $_"
    }

    # Buoc 2: Tai gio xuat xac nhan
    try {
        Write-Log "Buoc 2/4: Dang quet email gio xuat xac nhan..."
        & $pythonPath ".\fetch_confirm_times.py" 2>&1 | ForEach-Object { Write-Log "  [CONFIRM] $_" }
        Write-Log "Buoc 2/4: Hoan thanh!"
    } catch {
        Write-Log "LOI Buoc 2: $_"
    }

    # Buoc 3: Trich xuat thong tin bien so xe
    try {
        Write-Log "Buoc 3/4: Dang trich xuat thong tin xe..."
        & $pythonPath ".\extract_vehicles.py" 2>&1 | ForEach-Object { Write-Log "  [VEHICLE] $_" }
        Write-Log "Buoc 3/4: Hoan thanh!"
    } catch {
        Write-Log "LOI Buoc 3: $_"
    }

    # Buoc 4: Xu ly file Booking thanh booking_data.js
    try {
        Write-Log "Buoc 4/4: Dang xu ly file Booking..."
        & $pythonPath ".\process_winmart_booking.py" 2>&1 | ForEach-Object { Write-Log "  [BOOKING] $_" }
        Write-Log "Buoc 4/4: Hoan thanh!"
    } catch {
        Write-Log "LOI Buoc 4: $_"
    }

    # Dong bo toa do
    try {
        Write-Log "Dong bo toa do cho Booking..."
        $storeJsonStr = (Get-Content ".\store_data.js" -Raw).Trim() -replace '^const STORE_LIST_DATA = ', ''
        if ($storeJsonStr.EndsWith(';')) { $storeJsonStr = $storeJsonStr.Substring(0, $storeJsonStr.Length - 1) }
        $storeData = $storeJsonStr | ConvertFrom-Json
        $storeMap = @{}
        foreach ($s in $storeData) {
            if ($s.coords) { $storeMap[$s.id] = $s.coords }
        }
        
        $bookingJsonStr = (Get-Content ".\booking_data.js" -Raw).Trim() -replace '^const BOOKING_DELIVERY_POINTS = ', ''
        if ($bookingJsonStr.EndsWith(';')) { $bookingJsonStr = $bookingJsonStr.Substring(0, $bookingJsonStr.Length - 1) }
        $bookingData = $bookingJsonStr | ConvertFrom-Json
        
        $updated = 0
        foreach ($b in $bookingData) {
            if ($storeMap.ContainsKey($b.id)) {
                if (-not $b.coords -or $b.coords.lat -ne $storeMap[$b.id].lat -or $b.coords.lng -ne $storeMap[$b.id].lng) {
                    $b.coords = $storeMap[$b.id]
                    $updated++
                }
            }
        }
        
        if ($updated -gt 0) {
            $newJson = $bookingData | ConvertTo-Json -Depth 5 -Compress
            Set-Content -Path ".\booking_data.js" -Value "const BOOKING_DELIVERY_POINTS = $newJson;" -Encoding UTF8
            Write-Log "Da cap nhat $updated toa do booking!"
        } else {
            Write-Log "Toa do booking da dong bo."
        }
    } catch {
        Write-Log "LOI dong bo toa do: $_"
    }

    # Git Sync
    try {
        Write-Log "Dang dong bo len GitHub..."
        # Sync demo.html to index.html
        if (Test-Path "demo.html") {
            Copy-Item -Path "demo.html" -Destination "index.html" -Force
        }
        
        $gitPath = "C:\Program Files\Git\cmd\git.exe"
        if (-not (Test-Path $gitPath)) { $gitPath = "git" }
        
        $env:GIT_TERMINAL_PROMPT = "0"
        $env:GIT_EDITOR = "true"
        
        & $gitPath add -u 2>&1 | Out-Null
        & $gitPath add "vehicle_data.js" "departure_times.js" "incidents_data.js" "checkin_data.js" 2>$null
        
        $diff = & $gitPath diff --cached --name-only
        if ($diff) {
            & $gitPath commit -m "Auto-update booking data (scheduled)" 2>&1 | Out-Null
            & $gitPath pull origin main --rebase 2>&1 | Out-Null
            & $gitPath push origin main 2>&1 | Out-Null
            Write-Log "Da day du lieu len GitHub thanh cong!"
        } else {
            Write-Log "Khong co thay doi can dong bo."
        }
    } catch {
        Write-Log "LOI Git sync: $_"
    }

    Write-Log "=== HOAN THANH! Doi $intervalMinutes phut cho lan tiep theo... ==="
    Write-Host ""
    
    # Doi 30 phut
    Start-Sleep -Seconds ($intervalMinutes * 60)
}
