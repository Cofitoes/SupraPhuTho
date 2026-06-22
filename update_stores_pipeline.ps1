$ErrorActionPreference = "Stop"
$folderPath = $PSScriptRoot

# ========================================================
# CẤU HÌNH GOOGLE SHEETS
# ========================================================
# 1. Điền link Google Trang tính của bạn vào đây (sau khi Save as Google Sheets và chia sẻ "Bất kỳ ai có liên kết đều có thể xem")
$googleSheetUrl = ""

# 2. Điền link Web App Google Apps Script (Chỉ cần nếu chọn Phương án 2 - Ghi tọa độ ngược lại trang tính)
$googleScriptUrl = ""
# ========================================================

$excelPath = "$folderPath\Danh_sach_Winmart.xlsx"
if (-not (Test-Path $excelPath)) {
    if (Test-Path "$folderPath\DS_Cua_Hang.xlsm") {
        $excelPath = "$folderPath\DS_Cua_Hang.xlsm"
    } elseif (Test-Path "$folderPath\DS_Cua_Hang.xlsx") {
        $excelPath = "$folderPath\DS_Cua_Hang.xlsx"
    }
}
$isUsingGSheet = $false
$tempExcelPath = $null

if ($googleSheetUrl -and $googleSheetUrl -ne "HAY_DIEN_LINK_TRANG_TINH_CUA_BAN_VAO_DAY") {
    if ($googleSheetUrl -match "spreadsheets/d/([a-zA-Z0-9-_]+)") {
        $sheetId = $Matches[1]
        $downloadUrl = "https://docs.google.com/spreadsheets/d/$sheetId/export?format=xlsx"
        $tempExcelPath = Join-Path $env:TEMP "DS_Cua_Hang_GSheet.xlsx"
        Write-Host "Dang tai danh sach cua hang tu Google Sheets (ID: $sheetId)..."
        try {
            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
            Invoke-WebRequest -Uri $downloadUrl -OutFile $tempExcelPath -UseBasicParsing
            $excelPath = $tempExcelPath
            $isUsingGSheet = $true
            Write-Host "Tai thanh cong. Su dung du lieu tu Google Sheets."
        } catch {
            Write-Warning "Loi khi tai tu Google Sheets: $_. He thong se tu dong quay lai dung file Excel cuc bo."
        }
    } else {
        Write-Warning "Link Google Sheets khong dung dinh dang. He thong se dung file Excel cuc bo."
    }
}

$excel = $null

$wb = $null

try {
    Write-Host "Step 2: Khoi dong Excel COM..."
    $excel = New-Object -ComObject Excel.Application
    $excel.Visible = $false
    $excel.DisplayAlerts = $false
    $excel.EnableEvents = $false
    $excel.AskToUpdateLinks = $false

    function Convert-ExcelDateToFloat ($val) {
        if ($val -is [System.DateTime]) {
            $dt = $val
        } elseif ($val -is [double] -or $val -is [float]) {
            # Check if it could be an OADate representing a date in our range
            # Excel OADate for 2000-01-01 is 36526, for 2030-12-31 is 47848
            if ($val -ge 36526 -and $val -le 47848) {
                try {
                    $dt = [DateTime]::FromOADate($val)
                } catch {
                    return $val
                }
            } else {
                return $val
            }
        } else {
            # Try to parse string as date if possible
            try {
                $dt = [DateTime]([string]$val)
            } catch {
                return $val
            }
        }

        if ($dt) {
            $month = $dt.Month
            $day = $dt.Day
            $year = $dt.Year
            
            if ($month -in 8, 9, 10, 11, 12) {
                if ($day -eq 1 -and $year -ge 2000) {
                    $yearStr = [string]$year
                    return $month + ([double]$year / [Math]::Pow(10, $yearStr.Length))
                } elseif ($day -ne 1 -and $year -ge 2000 -and $year -le 2030) {
                    $dayStr = [string]$day
                    return $month + ([double]$day / [Math]::Pow(10, $dayStr.Length))
                }
            }
            
            # Standard OADate conversion
            return [DateTime]::ToOADate($dt)
        }
        return $val
    }

    function Normalize-Coordinate ($val, $isLat) {
        if ([string]::IsNullOrWhiteSpace($val)) {
            return $null
        }
        
        $val = Convert-ExcelDateToFloat $val
        
        try {
            $valStr = ([string]$val).Trim().Replace(',', '.')
            $f_val = [double]$valStr
            
            if ($f_val -eq 0) {
                return 0.0
            }
            
            $sign = 1.0
            if ($f_val -lt 0) {
                $sign = -1.0
            }
            $abs_val = [Math]::Abs($f_val)
            
            if ($isLat) {
                # Lat in Vietnam [8.0, 25.0]
                if ($abs_val -gt 25.0) {
                    while ($abs_val -gt 25.0) {
                        $abs_val /= 10.0
                    }
                } elseif ($abs_val -lt 8.0 -and $abs_val -gt 0) {
                    while ($abs_val -lt 8.0) {
                        $abs_val *= 10.0
                    }
                }
            } else {
                # Lng in Vietnam [102.0, 110.0]
                if ($abs_val -gt 110.0) {
                    while ($abs_val -gt 110.0) {
                        $abs_val /= 10.0
                    }
                } elseif ($abs_val -lt 102.0 -and $abs_val -gt 0) {
                    while ($abs_val -lt 102.0) {
                        $abs_val *= 10.0
                    }
                }
            }
            
            return $sign * $abs_val
        } catch {
            return $null
        }
    }

    function Is-Mock-Coordinate ($lat, $lng) {
        if ([string]::IsNullOrWhiteSpace($lat) -or [string]::IsNullOrWhiteSpace($lng)) {
            return $true
        }
        try {
            $f_lat = [double]$lat
            $f_lng = [double]$lng
            if ($f_lat -eq 0 -or $f_lng -eq 0) {
                return $true
            }
            # Check Vietnam bounding box
            if ($f_lat -lt 8.0 -or $f_lat -gt 25.0 -or $f_lng -lt 102.0 -or $f_lng -gt 110.0) {
                return $true
            }
        } catch {
            return $true
        }
        
        $latStr = [string]$lat
        $lngStr = [string]$lng
        if ($latStr -match '\.\d*85$' -and $lngStr -match '\.\d*42$') {
            return $true
        }
        return $false
    }

    function Geocode-Address ($address) {
        # 1. Clean complex metadata prefixes (Thua dat, To ban do, TDP, etc.)
        $cleanAddress = $address
        $cleanAddress = $cleanAddress -replace '(?i)Thửa\s+(đất\s+)?(số\s+)?[\d\w.-]+(\s+và\s+Thửa\s+đất\s+số\s+[\d\w.-]+)?,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)Thửa\s+đất\s+số\s+[\d\w-]+\s+tờ\s+[\d\w\s]+QL\d+\w*,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)Thửa\s+đất\s+[\d\w-]+\s+tờ\s+[\d\w\s]+,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)Thửa\s+[\d\w-]+\s+tờ\s+[\d\w\s]+,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)Tờ\s+bản\s+dồ\s+[\d\w\s]+,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)Tờ\s+bản\s+đồ\s+[\d\w\s]+,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)Tổ\s+dân\s+phố\s+[\d\w\s]+,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)TDP\s+[\d\w\s]+,\s*', ''
        $cleanAddress = $cleanAddress -replace '(?i)Khu\s+khố\s*', 'Khu phố '
        
        # Split by comma and filter empty parts
        $rawParts = $cleanAddress -split ','
        $parts = New-Object System.Collections.Generic.List[string]
        foreach ($p in $rawParts) {
            $trimmed = $p.Trim()
            if (-not [string]::IsNullOrWhiteSpace($trimmed)) {
                $parts.Add($trimmed)
            }
        }
        
        # Strip administrative prefixes (Thanh pho, Tinh, Phuong, Xa, Huyen, etc.) for fallback matching
        $cleanParts = New-Object System.Collections.Generic.List[string]
        foreach ($p in $parts) {
            $cp = $p -replace '(?i)^(Thành phố|Tỉnh|Quận|Huyện|Thị xã|Thị trấn|Phường|Xã|Thôn|Xóm|Khối|Khu phố|Khu)\s+', ''
            $cleanParts.Add($cp.Trim())
        }
        
        # Generate candidates in order of preference
        $queries = New-Object System.Collections.Generic.List[string]
        
        # Full original address
        $queries.Add($address.Trim())
        
        # Cleaned address (without thua, to, etc.)
        if ($parts.Count -gt 0) {
            $queries.Add(($parts -join ', ').Trim())
        }
        
        # Cleaned address without administrative prefixes
        if ($cleanParts.Count -gt 0) {
            $queries.Add(($cleanParts -join ', ').Trim())
        }
        
        # Left-to-right subsets (stripping most specific details)
        for ($i = 1; $i -lt $parts.Count; $i++) {
            $queries.Add(($parts[$i..($parts.Count - 1)] -join ', ').Trim())
            $queries.Add(($cleanParts[$i..($cleanParts.Count - 1)] -join ', ').Trim())
        }
        
        # Fallback: Ward/Commune + Province (e.g. "Xuan Lam, Thanh Hoa")
        if ($parts.Count -ge 3) {
            $queries.Add(($parts[0] + ", " + $parts[-1]).Trim())
            $queries.Add(($cleanParts[0] + ", " + $cleanParts[-1]).Trim())
            if ($parts.Count -ge 4) {
                $queries.Add(($parts[1] + ", " + $parts[-1]).Trim())
                $queries.Add(($cleanParts[1] + ", " + $cleanParts[-1]).Trim())
            }
        }
        
        # Fallback: District alone or District + Province
        if ($parts.Count -ge 2) {
            $queries.Add($parts[-2].Trim())
            $queries.Add($cleanParts[-2].Trim())
        }
        
        # Fallback: Province alone
        if ($parts.Count -ge 1) {
            $queries.Add($parts[-1].Trim())
            $queries.Add($cleanParts[-1].Trim())
        }
        
        # Deduplicate queries while preserving order
        $dedupedQueries = New-Object System.Collections.Generic.List[string]
        foreach ($q in $queries) {
            $qTrim = $q.Trim() -replace ',\s*,', ','
            if (-not $dedupedQueries.Contains($qTrim) -and $qTrim.Length -gt 2) {
                $dedupedQueries.Add($qTrim)
            }
        }
        
        foreach ($query in $dedupedQueries) {
            $uri = "https://nominatim.openstreetmap.org/search?format=json&q=" + [uri]::EscapeDataString($query) + "&countrycodes=vn"
            try {
                $req = [System.Net.WebRequest]::Create($uri)
                # Use unique, compliant User-Agent
                $req.UserAgent = "LogisticsHub-Bot-Contact-admin-at-logistics.vn/3.0"
                $req.Timeout = 8000
                $res = $req.GetResponse()
                $reader = New-Object System.IO.StreamReader($res.GetResponseStream())
                $jsonStr = $reader.ReadToEnd()
                $reader.Close()
                
                $data = $jsonStr | ConvertFrom-Json
                if ($data -and $data.Count -gt 0) {
                    # Found coordinates!
                    return @{ lat = $data[0].lat; lng = $data[0].lon; queryUsed = $query }
                }
            } catch {
                Write-Host "     [Warning] Geocode failed for query '$query': $_"
            }
            # Be polite to Nominatim
            Start-Sleep -Milliseconds 1200
        }
        return $null
    }

    # Nạp cache tọa độ từ store_data.js hiện tại để tránh geocode lại các cửa hàng cũ
    $coordsCache = @{}
    $storeDataPath = "$folderPath\store_data.js"
    if (Test-Path $storeDataPath) {
        try {
            $storeJs = Get-Content $storeDataPath -Raw
            $storeJson = $storeJs.Replace("const STORE_LIST_DATA = ", "").Trim("`r`n ;")
            $storeData = $storeJson | ConvertFrom-Json
            foreach ($s in $storeData) {
                if ($s.id -and $s.coords -and $s.coords.lat -and $s.coords.lng) {
                    if (-not (Is-Mock-Coordinate $s.coords.lat $s.coords.lng)) {
                        $coordsCache[([string]$s.id)] = $s.coords
                    }
                }
            }
            Write-Host "Da nap $($coordsCache.Count) toa do tu cache (store_data.js) de toi uu hoa."
        } catch {
            Write-Warning "Khong the nap cache toa do: $_"
        }
    }

    Write-Host "Opening workbook: $excelPath"
    $wb = $excel.Workbooks.Open($excelPath)
    $ws = $wb.Worksheets.Item(1)
    
    # Fetch all data into memory in one COM call!
    $usedRange = $ws.UsedRange
    $values = $usedRange.Value2
    $rowCount = $usedRange.Rows.Count
    Write-Host "Loaded $rowCount rows from Excel to memory."
    
    $idIndex = $null
    $nameIndex = $null
    $addressIndex = $null
    $provinceIndex = $null
    $regionIndex = $null
    $latIndex = $null
    $lngIndex = $null

    $colCount = $usedRange.Columns.Count
    for ($c = 1; $c -le $colCount; $c++) {
        $headerVal = [string]$values[1, $c]
        if ([string]::IsNullOrWhiteSpace($headerVal)) { continue }
        $headerVal = $headerVal.Trim()
        
        if ($headerVal -match "(?i)Ma Cua Hang|ID|Mã cửa hàng|Site Store") { $idIndex = $c }
        elseif ($headerVal -match "(?i)Ten Cua Hang|Name|Tên cửa hàng") { $nameIndex = $c }
        elseif ($headerVal -match "(?i)Dia Chi|Address|Địa chỉ" -and $headerVal -notmatch "Website") { $addressIndex = $c }
        elseif ($headerVal -match "(?i)Tinh|Province|Tỉnh|Tỉnh giao") { $provinceIndex = $c }
        elseif ($headerVal -match "(?i)Khu Vuc|Region|Khu vực") { $regionIndex = $c }
        elseif ($headerVal -match "(?i)Vi Do|Lat|Vĩ độ" -and $headerVal -notmatch "Website") { $latIndex = $c }
        elseif ($headerVal -match "(?i)Kinh Do|Lng|Kinh độ|Long" -and $headerVal -notmatch "Website") { $lngIndex = $c }
    }

    # Fallback to default indices if not found
    if (-not $idIndex) { $idIndex = 1 }
    if (-not $nameIndex) { $nameIndex = 2 }
    if (-not $addressIndex) { $addressIndex = 3 }
    if (-not $provinceIndex) { $provinceIndex = 4 }
    
    if (-not $latIndex) {
        if ([string]$values[1, 4] -match "Tỉnh|Province") { $latIndex = 6 }
        else { $latIndex = 5 }
    }
    if (-not $lngIndex) {
        if ([string]$values[1, 4] -match "Tỉnh|Province") { $lngIndex = 7 }
        else { $lngIndex = 6 }
    }
    
    Write-Host "Excel headers checked. ID Col: $idIndex, Name Col: $nameIndex, Address Col: $addressIndex, Region Col: $regionIndex, Lat Col: $latIndex, Lng Col: $lngIndex"
    
    $storeList = @()
    $hasUpdates = $false
    $updatedCount = 0
    
    for ($row = 2; $row -le $rowCount; $row++) {
        $id = [string]$values[$row, $idIndex]
        if ([string]::IsNullOrWhiteSpace($id)) {
            continue
        }
        
        $name = [string]$values[$row, $nameIndex]
        $address = [string]$values[$row, $addressIndex]
        
        $region = $null
        if ($regionIndex) {
            $region = [string]$values[$row, $regionIndex]
        }
        
        $latVal = $values[$row, $latIndex]
        $lngVal = $values[$row, $lngIndex]
        
        # Normalize and clean coordinates first
        $normLat = Normalize-Coordinate $latVal $true
        $normLng = Normalize-Coordinate $lngVal $false
        $hasNormalized = $false
        if ($normLat -ne $latVal -or $normLng -ne $lngVal) {
            $hasNormalized = $true
            $latVal = $normLat
            $lngVal = $normLng
            if ($hasNormalized -and -not $isUsingGSheet) {
                $ws.Cells.Item($row, $latIndex) = $latVal
                $ws.Cells.Item($row, $lngIndex) = $lngVal
                $hasUpdates = $true
            }
        }
        
        # Check if coordinates need geocoding
        $needGeocode = $false
        if (Is-Mock-Coordinate $latVal $lngVal) {
            # Kiểm tra xem có sẵn tọa độ trong bộ nhớ đệm không
            $idStr = [string]$id
            if ($coordsCache.ContainsKey($idStr)) {
                $latVal = $coordsCache[$idStr].lat
                $lngVal = $coordsCache[$idStr].lng
                Write-Host "Row $row - Resolved ID $id from cache: $latVal, $lngVal"
            } else {
                $needGeocode = $true
            }
        }

        if ($needGeocode) {
            Write-Host "Row $row - Geocoding ID $id : $address"
            $result = Geocode-Address $address
            
            if ($result) {
                $newLat = [double]$result.lat
                $newLng = [double]$result.lng
                
                if ($isUsingGSheet) {
                    # Ghi ngược lại Google Sheets nếu có cài Apps Script Web App
                    if ($googleScriptUrl) {
                        Write-Host "   -> Dang gui cap nhat toa do len Google Sheets Web App..."
                        try {
                            $body = @{
                                action = "updateCoords"
                                storeId = $id
                                lat = $newLat
                                lng = $newLng
                            } | ConvertTo-Json
                            [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
                            $resPost = Invoke-RestMethod -Uri $googleScriptUrl -Method Post -Body $body -ContentType "application/json" -TimeoutSec 10
                            Write-Host "   -> Ket qua tu Web App: $resPost"
                        } catch {
                            Write-Warning "   -> Khong the cap nhat len Google Sheets qua Web App: $_"
                        }
                    }
                } else {
                    # Ghi truc tiep vao file Excel cuc bo
                    $ws.Cells.Item($row, $latIndex) = $newLat
                    $ws.Cells.Item($row, $lngIndex) = $newLng
                }
                
                Write-Host "   -> Updated: $newLat, $newLng (Used: $($result.queryUsed))"
                $latVal = $newLat
                $lngVal = $newLng
                $hasUpdates = $true
                $updatedCount++
            } else {
                Write-Host "   -> [Failed] Could not resolve address"
            }
            Start-Sleep -Milliseconds 1200
        } else {
            # Normalize to double
            $latVal = [double]$latVal
            $lngVal = [double]$lngVal
        }
        
        $coords = $null
        if ($latVal -and $lngVal) {
            $coords = @{
                lat = $latVal
                lng = $lngVal
            }
        }
        
        $storeList += @{
            id = $id
            name = $name
            address = $address
            region = $region
            coords = $coords
        }
    }
    
    if ($hasUpdates) {
        if ($isUsingGSheet) {
            Write-Host "Da cap nhat $updatedCount toa do moi vao cache store_data.js (khong ghi truc tiep len file Google Sheets)."
        } else {
            Write-Host "Saving Excel workbook..."
            $wb.Save()
            Write-Host "Excel saved successfully. Updated $updatedCount coordinates."
        }
    } else {
        Write-Host "No coordinates needed update."
    }
    
    # Save store_data.js
    $json = $storeList | ConvertTo-Json -Depth 5 -Compress
    Set-Content -Path "$folderPath\store_data.js" -Value "const STORE_LIST_DATA = $json;" -Encoding UTF8
    Write-Host "Successfully generated store_data.js with $($storeList.Count) stores."
    
} catch {
    Write-Error "Failed: $_"
    throw $_
} finally {
    if ($wb) {
        $wb.Close($false)
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wb) | Out-Null
    }
    if ($excel) {
        $excel.Quit()
        [System.Runtime.InteropServices.Marshal]::ReleaseComObject($excel) | Out-Null
        [System.GC]::Collect()
        [System.GC]::WaitForPendingFinalizers()
    }
    if ($tempExcelPath -and (Test-Path $tempExcelPath)) {
        Remove-Item -Path $tempExcelPath -Force -ErrorAction SilentlyContinue
        Write-Host "Cleaned up temporary Google Sheets download file."
    }
}




