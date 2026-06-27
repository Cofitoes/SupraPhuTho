Set-Location $PSScriptRoot
$ErrorActionPreference = "Stop"

try {
    if (Test-Path "delete_old_files.py") {
        Write-Host "Running delete_old_files.py..."
        python .\delete_old_files.py
        Remove-Item -Path "delete_old_files.py" -Force -ErrorAction SilentlyContinue
    }
} catch {}

$lockFile = ".\update_in_progress.lock"
$statusFile = ".\update_status.js"

function Write-Status([string]$status, [string]$step, [int]$progress, [string]$message = "") {
    $timestamp = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")
    $obj = @{
        status = $status
        step = $step
        progress = $progress
        message = $message
        timestamp = $timestamp
    }
    $json = $obj | ConvertTo-Json -Compress
    $content = "window.UPDATE_STATUS = $json;"
    Set-Content -Path $statusFile -Value $content -Encoding UTF8
}

# 1. Acquire Lock
$currentPid = $PID
if (Test-Path $lockFile) {
    try {
        $existingPidStr = (Get-Content $lockFile -Raw).Trim()
        if (-not [string]::IsNullOrWhiteSpace($existingPidStr)) {
            $existingPid = [int]$existingPidStr
            $proc = Get-Process -Id $existingPid -ErrorAction SilentlyContinue
            # Verify if the process exists AND is a powershell process to prevent recycled PID blocks
            if ($existingPid -ne $currentPid -and $proc -and ($proc.ProcessName -like "*powershell*" -or $proc.ProcessName -like "*pwsh*")) {
                Write-Status "error" "Loi trung lap tien trinh" 0 "Mot tien trinh cap nhat khac (PID $existingPid) dang chay. Vui long doi."
                Write-Host "Another process (PID $existingPid) is running. Exiting."
                exit 0
            }
        }
    } catch {
        # Ignore and overwrite
    }
}

$currentPid | Set-Content -Path $lockFile -Force

# Set environment variables for non-interactive Git operations
$env:GIT_TERMINAL_PROMPT = "0"
$env:GIT_EDITOR = "true"

function Sync-Git-Data {
    Write-Status "running" "Dang dong bo du lieu len link online..." 95
    Write-Host "Syncing data to online link via Git..."
    
    # Automatically synchronize demo.html and index.html to prevent divergence
    if (Test-Path "demo.html") {
        Copy-Item -Path "demo.html" -Destination "index.html" -Force
        Write-Host "Synchronized demo.html to index.html successfully."
    }
    
    $gitPath = "C:\Program Files\Git\cmd\git.exe"
    if (-not (Test-Path $gitPath)) {
        $gitPath = "git"
    }

    try {
        # Stage all updated tracked changes (ignores untracked raw excel and gsheet files)
        & $gitPath add -u
        
        # Explicitly stage dynamic data files to guarantee they are tracked and synced even if recreated
        & $gitPath add "*.js" "*.html" "*.py" "Lichsu*.md" "vehicle_data.js" "departure_times.js" "incidents_data.js" "checkin_data.js" "Form*.xlsb" "Data_Booking/Booking Supra*" 2>$null
        
        if ($LASTEXITCODE -ne 0) {
            # Ignore minor errors if files do not exist
        }
        
        # Check if changes exist in staging
        $diff = & $gitPath diff --cached --name-only
        if ($diff) {
            Write-Host "Changes to commit:`n$diff"
            & $gitPath commit -m "Auto-update booking data and system files from dashboard"
            if ($LASTEXITCODE -ne 0) {
                throw "Khong the tao commit moi (git commit failed)."
            }
            $maxRetries = 3
            $success = $false
            for ($i = 1; $i -le $maxRetries; $i++) {
                Write-Host "Attempt $i to sync with GitHub..."
                
                # Pull before push using rebase to avoid merge commits
                Write-Host "Pulling latest changes from remote..."
                & $gitPath pull origin main --rebase
                if ($LASTEXITCODE -ne 0) {
                    Write-Warning "Rebase failed! Aborting rebase to keep working directory clean..."
                    & $gitPath rebase --abort | Out-Null
                    
                    if ($i -eq $maxRetries) {
                        throw "Khong the tai du lieu moi tu GitHub (git pull --rebase failed). Co the do xung dot file."
                    }
                    Start-Sleep -Seconds 5
                    continue
                }
                
                # Push changes to GitHub
                Write-Host "Pushing changes to GitHub..."
                & $gitPath push origin main
                if ($LASTEXITCODE -eq 0) {
                    $success = $true
                    Write-Host "Git push completed successfully!"
                    break
                }
                
                Write-Warning "Push failed. Remote may have changed."
                if ($i -eq $maxRetries) {
                    throw "Khong the day du lieu len GitHub (git push failed) sau $maxRetries lan thu."
                }
                Start-Sleep -Seconds 5
            }
            
            if (-not $success) {
                throw "Dong bo Github that bai hoan toan."
            }
        } else {
            Write-Host "No changes detected. No push needed."
        }
    } catch {
        $err = $_.ToString()
        Write-Warning "Git Sync failed: $err"
        throw $_
    }
}

function Pre-Sync-Git {
    Write-Host "Running Git Pre-Sync to align with remote..."
    $gitPath = "C:\Program Files\Git\cmd\git.exe"
    if (-not (Test-Path $gitPath)) {
        $gitPath = "git"
    }

    try {
        # 1. Fetch latest remote changes
        & $gitPath fetch origin main
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "Git fetch failed. Skipping pre-sync."
            return
        }

        # Get local and remote SHAs
        $localSHA = (& $gitPath rev-parse HEAD).Trim()
        $remoteSHA = (& $gitPath rev-parse origin/main).Trim()

        if ($localSHA -eq $remoteSHA) {
            Write-Host "Local branch is already up-to-date with remote."
            return
        }

        # Check if we have local-only commits
        $localOnlyCommits = & $gitPath log origin/main..HEAD --format="%s"
        
        # Check if all local-only commits are auto-updates
        $allAutoUpdate = $true
        if ($localOnlyCommits) {
            foreach ($subject in $localOnlyCommits) {
                if ($subject -and $subject -notlike "*Auto-update*") {
                    $allAutoUpdate = $false
                    break
                }
            }
        }

        if ($allAutoUpdate) {
            Write-Host "Local commits are only auto-updates. Resetting to origin/main to prevent conflicts..."
            & $gitPath reset --hard origin/main
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Git reset --hard failed."
            } else {
                Write-Host "Successfully aligned local repository with origin/main."
            }
        } else {
            Write-Host "Detected custom local commits. Attempting a pull --rebase..."
            & $gitPath pull origin main --rebase
            if ($LASTEXITCODE -ne 0) {
                Write-Warning "Rebase failed! Aborting rebase..."
                & $gitPath rebase --abort | Out-Null
            }
        }
    } catch {
        Write-Warning "Git Pre-Sync failed: $_"
    }
}

try {
    Write-Status "running" "Khoi dong & Kiem tra tep du lieu..." 10
    Start-Sleep -Milliseconds 500

    # Align Git with remote before running updates to prevent conflicts
    Pre-Sync-Git

    # 0. Tá»± Ä‘á»™ng táº£i file Ä‘Ã­nh kÃ¨m tá»« Email khÃ¡ch hÃ ng gá»­i Ä‘áº¿n (náº¿u cÃ³)
    try {
        Write-Status "running" "Dang quet email va tai file Booking..." 15
        Write-Host "Running download_booking_emails.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\download_booking_emails.py"
    } catch {
        Write-Warning "Khong the tai tu dong email booking: $_"
    }

    # 0.1 Tá»± Ä‘á»™ng táº£i giá» xuáº¥t xÃ¡c nháº­n tá»« Email cá»§a khÃ¡ch hÃ ng gá»­i Ä‘áº¿n (náº¿u cÃ³)
    try {
        Write-Status "running" "Dang quet email va tai gio xuat xac nhan..." 20
        Write-Host "Running fetch_confirm_times.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\fetch_confirm_times.py"
    } catch {
        Write-Warning "Khong the tai tu dong gio xuat tu email: $_"
    }

    # 0.2 Tá»± Ä‘á»™ng trÃ­ch xuáº¥t thÃ´ng tin biá»ƒn sá»‘ xe tá»« email pháº£n há»“i (náº¿u cÃ³)
    try {
        Write-Status "running" "Dang chay tu dong trich xuat thong tin xe..." 22
        Write-Host "Running extract_vehicles.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\extract_vehicles.py"
    } catch {
        Write-Warning "Khong the chay extract_vehicles.py: $_"
    }

    # 0.4. Tá»± Ä‘á»™ng phÃ¡t hiá»‡n vÃ  thÃªm cá»­a hÃ ng má»›i tá»« file booking
    try {
        Write-Status "running" "Dang phat hien cua hang moi tu Booking..." 23
        Write-Host "Running auto_add_new_stores.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\auto_add_new_stores.py"
    } catch {
        Write-Warning "Khong the chay auto_add_new_stores.py: $_"
    }

    # 0.5. Đã tắt update_store_data.py vì script này chuyên biệt cho file JSON của Con Cung
    # try {
    #     Write-Status "running" "Dong bo danh sach cua hang qua Python..." 25
    #     Write-Host "Running update_store_data.py..."
    #     $env:PYTHONIOENCODING = "utf-8"
    #     $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
    #     if (-not (Test-Path $pythonPath)) {
    #         $pythonPath = "python"
    #     }
    #     & $pythonPath ".\update_store_data.py"
    # } catch {
    #     Write-Warning "Khong the chay update_store_data.py: $_"
    # }

    try {
        Write-Status "running" "Dong bo danh sach cua hang & Phan giai toa do..." 30
        Write-Host "Running update_winmart_stores.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\update_winmart_stores.py"
    } catch {
        Write-Warning "Khong the chay update_winmart_stores.py: $_"
    }

    try {
        Write-Status "running" "Trich xuat du lieu Booking Winmart..." 60
        Write-Host "Running process_winmart_booking.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\process_winmart_booking.py"
    } catch {
        Write-Warning "Khong the chay process_winmart_booking.py: $_"
    }

    try {
        Write-Status "running" "Dong bo toa do cho Booking..." 90
        Write-Host "Syncing store coordinates to booking_data.js..."
        $storeJsonStr = (Get-Content ".\store_data.js" -Raw).Trim() -replace '^const STORE_LIST_DATA = ', ''
        if ($storeJsonStr.EndsWith(';')) { $storeJsonStr = $storeJsonStr.Substring(0, $storeJsonStr.Length - 1) }
        $storeData = $storeJsonStr | ConvertFrom-Json
        $storeMap = @{}
        foreach ($s in $storeData) {
            if ($s.coords) { $storeMap[$s.id] = $s.coords }
        }
        
        $bookingJsonStr = (Get-Content -Path ".\booking_data.js" -Encoding UTF8 -Raw).Trim() -replace '^const BOOKING_DELIVERY_POINTS = ', ''
        if ($bookingJsonStr.EndsWith(';')) { $bookingJsonStr = $bookingJsonStr.Substring(0, $bookingJsonStr.Length - 1) }
        $bookingData = $bookingJsonStr | ConvertFrom-Json
        
        $updated = 0
        foreach ($b in $bookingData) {
            if ($storeMap.ContainsKey($b.id)) {
                $hasCoords = $b.PSObject.Properties.Match('coords').Count -gt 0
                if (-not $hasCoords -or -not $b.coords -or $b.coords.lat -ne $storeMap[$b.id].lat -or $b.coords.lng -ne $storeMap[$b.id].lng) {
                    if (-not $hasCoords) {
                        $b | Add-Member -MemberType NoteProperty -Name "coords" -Value $storeMap[$b.id]
                    } else {
                        $b.coords = $storeMap[$b.id]
                    }
                    $updated++
                }
            }
        }
        
        if ($updated -gt 0) {
            $newJson = $bookingData | ConvertTo-Json -Depth 5 -Compress
            # Write without BOM for compatibility
    $jsContent = "const BOOKING_DELIVERY_POINTS = $newJson;"
    $utf8NoBom = New-Object System.Text.UTF8Encoding $false
    [System.IO.File]::WriteAllText("$PWD\booking_data.js", $jsContent, $utf8NoBom)
            Write-Host "Updated $updated booking coordinates!"
        } else {
            Write-Host "No updates needed for booking_data.js"
        }
    } catch {
        Write-Warning "Khong the dong bo toa do cho Booking: $_"
    }

    # 1.6. Cháº¡y tá»± Ä‘á»™ng quÃ©t vÃ  Ä‘á»“ng bá»™ Sá»± Cá»‘
    try {
        Write-Status "running" "Dang quet va dong bo du lieu su co..." 94
        Write-Host "Running process_incidents.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\process_incidents.py"
    } catch {
        Write-Warning "Khong the chay tu dong dong bo su co: $_"
    }

    # 1.7. Đong bo ma van don tu Google Sheets
    try {
        Write-Status "running" "Dang dong bo ma van don GHN tu Google Sheets..." 95
        Write-Host "Running update_data.py..."
        $env:PYTHONIOENCODING = "utf-8"
        $pythonPath = "C:\Users\ADMIN\AppData\Local\Programs\Python\Python312\python.exe"
        if (-not (Test-Path $pythonPath)) {
            $pythonPath = "python"
        }
        & $pythonPath ".\update_data.py"
    } catch {
        Write-Warning "Khong the chay dong bo ma van don GHN: $_"
    }

    # 2. Deploy to online link (GitHub -> Vercel)
    Sync-Git-Data

    Write-Status "success" "Hoan thanh cap nhat!" 100
    Write-Host "Pipeline completed successfully!"

} catch {
    $err = $_.ToString()
    Write-Host "Error occurred: $err"
    $cleanErr = $err -replace "'", "" -replace '"', ""
    Write-Status "error" "Loi trong qua trinh cap nhat" 0 "Chi tiet loi: $cleanErr"
} finally {
    if (Test-Path $lockFile) {
        Remove-Item -Path $lockFile -Force -ErrorAction SilentlyContinue
    }
}

