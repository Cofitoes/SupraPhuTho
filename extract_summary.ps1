$ErrorActionPreference = "Stop"
$folderPath = $PSScriptRoot
$dataFolderPath = "$folderPath\Data_Booking"
$failedFiles = @()

function Read-XlsxPure([string]$filePath) {
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    
    $zip = [System.IO.Compression.ZipFile]::OpenRead($filePath)
    
    $sharedStrings = @()
    $ssEntry = $zip.Entries | Where-Object { $_.FullName -eq "xl/sharedStrings.xml" }
    if ($ssEntry) {
        $stream = $ssEntry.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        $xmlContent = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        
        $xml = [xml]$xmlContent
        $siNodes = $xml.SelectNodes("//*[local-name()='si']")
        foreach ($si in $siNodes) {
            $tNode = $si.SelectSingleNode("*[local-name()='t']")
            if ($tNode) {
                $sharedStrings += $tNode.InnerText
            } else {
                $rNodes = $si.SelectNodes("*[local-name()='r']/*[local-name()='t']")
                $text = ""
                foreach ($r in $rNodes) {
                    $text += $r.InnerText
                }
                $sharedStrings += $text
            }
        }
    }
    
    # 1. Read xl/workbook.xml to find the data sheet rId
    $wbEntry = $zip.Entries | Where-Object { $_.FullName -eq "xl/workbook.xml" }
    if (-not $wbEntry) {
        $zip.Dispose()
        throw "Could not find xl/workbook.xml"
    }
    $stream = $wbEntry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $wbXml = [xml]$reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    
    $sheets = $wbXml.SelectNodes("//*[local-name()='sheet']")
    $targetRId = $null
    foreach ($sheet in $sheets) {
        $name = $sheet.GetAttribute("name")
        # Target the sheet that is NOT named "Summary"
        if ($name -notmatch "Summary") {
            $targetRId = $sheet.Attributes | Where-Object { $_.LocalName -eq "id" } | Select-Object -ExpandProperty Value
            break
        }
    }
    
    # Fallback to the first sheet if no non-Summary sheet is found
    if (-not $targetRId -and $sheets.Count -gt 0) {
        $targetRId = $sheets[0].Attributes | Where-Object { $_.LocalName -eq "id" } | Select-Object -ExpandProperty Value
    }
    
    # 2. Read xl/_rels/workbook.xml.rels to map rId to worksheet path
    $relsEntry = $zip.Entries | Where-Object { $_.FullName -eq "xl/_rels/workbook.xml.rels" }
    if (-not $relsEntry) {
        $zip.Dispose()
        throw "Could not find xl/_rels/workbook.xml.rels"
    }
    $stream = $relsEntry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $relsXml = [xml]$reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    
    $targetPath = $null
    $relationships = $relsXml.SelectNodes("//*[local-name()='Relationship']")
    foreach ($rel in $relationships) {
        if ($rel.GetAttribute("Id") -eq $targetRId) {
            $targetPath = "xl/" + $rel.GetAttribute("Target")
            break
        }
    }
    
    if (-not $targetPath) {
        $targetPath = "xl/worksheets/sheet2.xml"
    }
    
    $sheetEntry = $zip.Entries | Where-Object { $_.FullName -eq $targetPath }
    if (-not $sheetEntry) {
        $sheetEntry = $zip.Entries | Where-Object { $_.FullName -eq "xl/worksheets/sheet2.xml" }
        if (-not $sheetEntry) {
            $sheetEntry = $zip.Entries | Where-Object { $_.FullName -like "xl/worksheets/sheet*.xml" } | Sort-Object FullName | Select-Object -First 1
        }
    }
    if (-not $sheetEntry) {
        $zip.Dispose()
        throw "No worksheets found in excel file."
    }
    
    $stream = $sheetEntry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $xmlContent = $reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    $zip.Dispose()
    
    $xml = [xml]$xmlContent
    $rows = $xml.SelectNodes("//*[local-name()='row']")
    
    $dataTable = New-Object System.Data.DataTable
    $cols = @("F1", "F2", "F7", "F8", "F9", "F10")
    foreach ($col in $cols) {
        $dataTable.Columns.Add($col) | Out-Null
    }
    
    function Get-ColIndex([string]$cellRef) {
        $letters = $cellRef -replace '\d+'
        $idx = 0
        for ($i = 0; $i -lt $letters.Length; $i++) {
            $idx = $idx * 26 + ([char]$letters[$i] - [char]'A' + 1)
        }
        return $idx - 1
    }
    
    foreach ($row in $rows) {
        $cNodes = $row.SelectNodes("*[local-name()='c']")
        $rowData = @{}
        foreach ($c in $cNodes) {
            $ref = $c.GetAttribute("r")
            $colIdx = Get-ColIndex $ref
            $colNum = $colIdx + 1
            
            if ($colNum -eq 1 -or $colNum -eq 2 -or $colNum -eq 7 -or $colNum -eq 8 -or $colNum -eq 9 -or $colNum -eq 10) {
                $val = ""
                $vNode = $c.SelectSingleNode("*[local-name()='v']")
                if ($vNode) {
                    $val = $vNode.InnerText
                    $t = $c.GetAttribute("t")
                    if ($t -eq "s") {
                        $idx = [int]$val
                        if ($idx -ge 0 -and $idx -lt $sharedStrings.Length) {
                            $val = $sharedStrings[$idx]
                        }
                    }
                }
                $colName = ""
                if ($colNum -eq 1) { $colName = "F1" }
                elseif ($colNum -eq 2) { $colName = "F2" }
                elseif ($colNum -eq 7) { $colName = "F7" }
                elseif ($colNum -eq 8) { $colName = "F8" }
                elseif ($colNum -eq 9) { $colName = "F9" }
                elseif ($colNum -eq 10) { $colName = "F10" }
                
                $rowData[$colName] = $val
            }
        }
        
        if ($rowData.Count -gt 0) {
            $newRow = $dataTable.NewRow()
            foreach ($col in $cols) {
                if ($rowData[$col] -ne $null) {
                    $newRow[$col] = $rowData[$col]
                } else {
                    $newRow[$col] = ""
                }
            }
            $dataTable.Rows.Add($newRow)
        }
    }
    
    return ,$dataTable
}

function Read-XlsxSummary([string]$filePath) {
    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    
    $zip = [System.IO.Compression.ZipFile]::OpenRead($filePath)
    
    $sharedStrings = @()
    $ssEntry = $zip.Entries | Where-Object { $_.FullName -eq "xl/sharedStrings.xml" }
    if ($ssEntry) {
        $stream = $ssEntry.Open()
        $reader = New-Object System.IO.StreamReader($stream)
        $xmlContent = $reader.ReadToEnd()
        $reader.Close()
        $stream.Close()
        
        $xml = [xml]$xmlContent
        $siNodes = $xml.SelectNodes("//*[local-name()='si']")
        foreach ($si in $siNodes) {
            $tNode = $si.SelectSingleNode("*[local-name()='t']")
            if ($tNode) {
                $sharedStrings += $tNode.InnerText
            } else {
                $rNodes = $si.SelectNodes("*[local-name()='r']/*[local-name()='t']")
                $text = ""
                foreach ($r in $rNodes) {
                    $text += $r.InnerText
                }
                $sharedStrings += $text
            }
        }
    }
    
    $wbEntry = $zip.Entries | Where-Object { $_.FullName -eq "xl/workbook.xml" }
    if (-not $wbEntry) {
        $zip.Dispose()
        throw "Could not find xl/workbook.xml"
    }
    $stream = $wbEntry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $wbXml = [xml]$reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    
    $sheets = $wbXml.SelectNodes("//*[local-name()='sheet']")
    $targetRId = $null
    foreach ($sheet in $sheets) {
        $name = $sheet.GetAttribute("name")
        if ($name -match "Summary") {
            $targetRId = $sheet.Attributes | Where-Object { $_.LocalName -eq "id" } | Select-Object -ExpandProperty Value
            break
        }
    }
    
    if (-not $targetRId) {
        $zip.Dispose()
        return $null
    }
    
    $relsEntry = $zip.Entries | Where-Object { $_.FullName -eq "xl/_rels/workbook.xml.rels" }
    if (-not $relsEntry) {
        $zip.Dispose()
        throw "Could not find xl/_rels/workbook.xml.rels"
    }
    $stream = $relsEntry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $relsXml = [xml]$reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    
    $targetPath = $null
    $relationships = $relsXml.SelectNodes("//*[local-name()='Relationship']")
    foreach ($rel in $relationships) {
        if ($rel.GetAttribute("Id") -eq $targetRId) {
            $targetPath = "xl/" + $rel.GetAttribute("Target")
            break
        }
    }
    
    if (-not $targetPath) {
        $zip.Dispose()
        return $null
    }
    
    $sheetEntry = $zip.Entries | Where-Object { $_.FullName -eq $targetPath }
    if (-not $sheetEntry) {
        $zip.Dispose()
        return $null
    }
    
    $stream = $sheetEntry.Open()
    $reader = New-Object System.IO.StreamReader($stream)
    $xmlContent = $reader.ReadToEnd()
    $reader.Close()
    $stream.Close()
    $zip.Dispose()
    
    $xml = [xml]$xmlContent
    $rows = $xml.SelectNodes("//*[local-name()='row']")
    
    $buffMap = @{}
    
    function Get-ColIndexInternal([string]$cellRef) {
        $letters = $cellRef -replace '\d+'
        $idx = 0
        for ($i = 0; $i -lt $letters.Length; $i++) {
            $idx = $idx * 26 + ([char]$letters[$i] - [char]'A' + 1)
        }
        return $idx - 1
    }
    
    foreach ($row in $rows) {
        $cNodes = $row.SelectNodes("*[local-name()='c']")
        $storeCode = ""
        $buffVal = ""
        foreach ($c in $cNodes) {
            $ref = $c.GetAttribute("r")
            $colIdx = Get-ColIndexInternal $ref
            $colNum = $colIdx + 1
            
            if ($colNum -eq 3 -or $colNum -eq 8) {
                $val = ""
                $vNode = $c.SelectSingleNode("*[local-name()='v']")
                if ($vNode) {
                    $val = $vNode.InnerText
                    $t = $c.GetAttribute("t")
                    if ($t -eq "s") {
                        $idx = [int]$val
                        if ($idx -ge 0 -and $idx -lt $sharedStrings.Length) {
                            $val = $sharedStrings[$idx]
                        }
                    }
                }
                if ($colNum -eq 3) { $storeCode = ([string]$val).Trim() }
                elseif ($colNum -eq 8) { $buffVal = ([string]$val).Trim() }
            }
        }
        if (-not [string]::IsNullOrWhiteSpace($storeCode) -and -not [string]::IsNullOrWhiteSpace($buffVal) -and $storeCode -ne "Ma CH") {
            $buffMap[$storeCode] = $buffVal
        }
    }
    
    return $buffMap
}

function Safe-ParseDouble([string]$val) {
    if ([string]::IsNullOrWhiteSpace($val)) { return 0.0 }
    $normalized = $val.Replace(",", ".")
    $outVal = 0.0
    if ([double]::TryParse($normalized, [System.Globalization.NumberStyles]::Any, [System.Globalization.CultureInfo]::InvariantCulture, [ref]$outVal)) {
        return $outVal
    }
    return 0.0
}

# Danh sách pattern loại trừ (đã xếp tay, không muốn trùng lặp với dữ liệu tự động)
# Dùng regex để tránh vấn đề encoding Unicode trong tên file
$excludedPatterns = @(
    "DCMQ-CC.*ADHOC.*12\.06\.2026"
)

$rawFiles = Get-ChildItem -Path $dataFolderPath -Filter "*.xlsx" | Where-Object {
    $matched = $_.Name -match "MQ-CC" -and $_.Name -notmatch "^\~\$"
    if ($matched) {
        foreach ($pattern in $excludedPatterns) {
            if ($_.Name -match $pattern) {
                Write-Host "EXCLUDED (da xep tay): $($_.Name)"
                $matched = $false
                break
            }
        }
    }
    $matched
}

# NhÃ³m cÃ¡c tá»‡p tin theo tÃªn chuáº©n hÃ³a (loáº¡i bá» tá»« khÃ³a UPDATE) Ä‘á»ƒ trÃ¡nh trÃ¹ng láº·p giá»¯a file gá»‘c vÃ  file update
$filesByName = @{}
foreach ($file in $rawFiles) {
    # Loáº¡i bá» tá»« khÃ³a UPDATE vÃ  cÃ¡c dáº¥u (1), (2) thá»«a Ä‘á»ƒ chuáº©n hÃ³a tÃªn
    $normName = $file.Name -replace '\s*[-_]?\s*UPDATE\s*', ''
    $normName = $normName -replace '\s*\(\d+\)', ''
    $normName = $normName -replace '\[|\]', ''
    $normName = $normName.ToLower().Trim()
    
    if (-not $filesByName.ContainsKey($normName)) {
        $filesByName[$normName] = @()
    }
    $filesByName[$normName] += [PSCustomObject]@{
        File = $file
        Name = $file.Name
        IsUpdate = $file.Name -match "UPDATE"
        LastWriteTime = $file.LastWriteTime
    }
}

$files = @()
foreach ($key in $filesByName.Keys) {
    $group = $filesByName[$key]
    if ($group.Count -eq 1) {
        $files += $group[0].File
    } else {
        # CÃ³ nhiá»u phiÃªn báº£n cá»§a cÃ¹ng má»™t tá»‡p (gá»‘c & update), Æ°u tiÃªn tá»‡p UPDATE hoáº·c tá»‡p má»›i nháº¥t
        $updates = $group | Where-Object { $_.IsUpdate }
        if ($updates) {
            $best = $updates | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $files += $best.File
            Write-Host "Deduplicated: selected update file: $($best.Name) and ignored others in group."
        } else {
            $best = $group | Sort-Object LastWriteTime -Descending | Select-Object -First 1
            $files += $best.File
            Write-Host "Deduplicated: selected latest file: $($best.Name) and ignored others in group."
        }
    }
}

# Load Store Data for mapping
$storeJs = Get-Content "$folderPath\store_data.js" -Raw
$storeJson = $storeJs.Replace("const STORE_LIST_DATA = ", "").Trim("`r`n ;")
$storeData = $storeJson | ConvertFrom-Json
$storeLookup = @{}
foreach ($s in $storeData) {
    $storeLookup[([string]$s.id)] = $s
}

$summary = @{}
$bookingPoints = @{}

foreach ($file in $files) {
    Write-Output "Processing file: $($file.Name)"
    $filePath = $file.FullName
    $tempId = [guid]::NewGuid().ToString("N")
    $tempPath = Join-Path $env:TEMP "temp_extract_$tempId.xlsx"
    $conn = $null
    
    # TrÃ­ch xuáº¥t ngÃ y tá»« tÃªn file Excel (dáº¡ng dd.MM.yyyy hoáº·c dd.MM)
    $fileDateStr = ""
    if ($file.Name -match '(\d{1,2})\.(\d{1,2})\.(\d{4})') {
        $dd = $Matches[1].PadLeft(2, '0')
        $mm = $Matches[2].PadLeft(2, '0')
        $yyyy = $Matches[3]
        $fileDateStr = "$yyyy-$mm-$dd"
    } elseif ($file.Name -match '(\d{1,2})\.(\d{1,2})') {
        $dd = $Matches[1].PadLeft(2, '0')
        $mm = $Matches[2].PadLeft(2, '0')
        $yyyy = "2026"
        $fileDateStr = "$yyyy-$mm-$dd"
    } else {
        # Fallback vá» ngÃ y sá»­a Ä‘á»•i file náº¿u tÃªn file khÃ´ng chá»©a ngÃ y
        $fileDateStr = $file.LastWriteTime.ToString("yyyy-MM-dd")
    }
    
    try {
        # Copy to local temp file to prevent locking issue with Google Drive sync / Excel open
        # Use -LiteralPath to correctly handle brackets in source file path
        Copy-Item -LiteralPath $filePath -Destination $tempPath -Force
        
        $fileBuffMap = Read-XlsxSummary $tempPath
        $dt = Read-XlsxPure $tempPath
        
        foreach ($row in $dt.Rows) {
            $row_F1 = $row["F1"]
            if ($row_F1 -eq $null -or [System.Convert]::IsDBNull($row_F1) -or [string]::IsNullOrWhiteSpace($row_F1)) {
                continue
            }
            $f1 = [string]$row_F1
            $dateStr = ""
            # Lá»c cÃ¡c dÃ²ng Ä‘Æ¡n hÃ ng há»£p lá»‡ (mÃ£ phiáº¿u xuáº¥t chá»©a chuá»—i 6 chá»¯ sá»‘ liÃªn tiáº¿p)
            if ($f1 -match "(\d{6})") {
                $dateStr = $fileDateStr
            } else {
                continue
            }

            if (-not $summary.ContainsKey($dateStr)) {
                $summary[$dateStr] = @{
                    date = $dateStr
                    stores = @{}
                    boxes = 0
                    items = 0
                    vol = 0.0
                    weight = 0.0
                    bookings = 0
                }
            }

            $summary[$dateStr].bookings++

            $storeCode = [string]$row["F2"]
            if (-not [string]::IsNullOrWhiteSpace($storeCode)) {
                $storeCode = $storeCode.Trim()
                $summary[$dateStr].stores[$storeCode] = $true
            }

            $f7Str = [string]$row["F7"]
            $f8Str = [string]$row["F8"]
            $f9Str = [string]$row["F9"]
            $f10Str = [string]$row["F10"]
            
            $vVol = Safe-ParseDouble $f9Str
            $vWeight = Safe-ParseDouble $f10Str
            $vBoxes = Safe-ParseDouble $f7Str
            $vItems = Safe-ParseDouble $f8Str

            $summary[$dateStr].boxes += $vBoxes
            $summary[$dateStr].items += $vItems
            $summary[$dateStr].vol += $vVol
            $summary[$dateStr].weight += $vWeight
            
            if (-not [string]::IsNullOrWhiteSpace($storeCode)) {
                $bpKey = "$dateStr|$storeCode"
                if (-not $bookingPoints.ContainsKey($bpKey)) {
                    $bookingPoints[$bpKey] = @{
                        id = $storeCode
                        date = $dateStr
                        volume = 0.0
                        weight = 0.0
                        pcs = 0.0
                        buffs = @()
                    }
                }
                $bookingPoints[$bpKey].volume += $vVol
                $bookingPoints[$bpKey].weight += $vWeight
                $bookingPoints[$bpKey].pcs += $vItems
                
                # Láº¥y BUFF tá»« báº£ng Summary, náº¿u trá»‘ng thÃ¬ fallback vá» f1 (MÃ£ Phiáº¿u Xuáº¥t)
                $buffVal = ""
                if ($fileBuffMap -and $fileBuffMap.ContainsKey($storeCode)) {
                    $buffVal = $fileBuffMap[$storeCode]
                }
                if ([string]::IsNullOrWhiteSpace($buffVal)) {
                    $buffVal = $f1
                }
                
                if (-not [string]::IsNullOrWhiteSpace($buffVal) -and $bookingPoints[$bpKey].buffs -notcontains $buffVal) {
                    $bookingPoints[$bpKey].buffs += $buffVal
                }
            }
        }
    } catch {
        Write-Error "Failed to process $($file.Name): $_"
        $failedFiles += $file.Name
    } finally {
        if ($conn) {
            if ($conn.State -eq 'Open') {
                $conn.Close()
            }
            $conn.Dispose()
        }
        if (Test-Path $tempPath) {
            Remove-Item -Path $tempPath -Force -ErrorAction SilentlyContinue
        }
    }
}

$results = @()
foreach ($key in $summary.Keys | Sort-Object) {
    $item = $summary[$key]
    $results += @{
        date = $item.date
        bookingCount = $item.bookings
        storeCount = $item.stores.Count
        totalBoxes = [math]::Round($item.boxes, 2)
        totalItems = [math]::Round($item.items, 2)
        totalVolume = [math]::Round($item.vol, 2)
        totalWeight = [math]::Round($item.weight, 2)
    }
}

$jsonObj = $results | ConvertTo-Json -Depth 5 -Compress
$timestamp = [DateTimeOffset]::UtcNow.ToUnixTimeMilliseconds()
$jsContent = "const BOOKING_SUMMARY = $jsonObj;`nconst LAST_UPDATE_TIME = $timestamp;"
Set-Content -Path "$folderPath\summary_data.js" -Value $jsContent -Encoding UTF8
Write-Output "Successfully generated summary_data.js with $($results.Count) records."

$bookingList = @()
foreach ($bp in $bookingPoints.Values) {
    $store = $storeLookup[$bp.id]
    $buffStr = $bp.buffs -join ", "
    if ($store) {
        $bookingList += @{
            id = $bp.id
            date = $bp.date
            volume = [math]::Round($bp.volume, 5)
            weight = [math]::Round($bp.weight, 4)
            pcs = $bp.pcs
            buff = $buffStr
            name = $store.name
            region = $store.region
            coords = $store.coords
        }
    } else {
        $bookingList += @{
            id = $bp.id
            date = $bp.date
            volume = [math]::Round($bp.volume, 5)
            weight = [math]::Round($bp.weight, 4)
            pcs = $bp.pcs
            buff = $buffStr
            name = "Unknown Store - $($bp.id)"
            region = "Unknown"
        }
    }
}

$bookingJson = $bookingList | ConvertTo-Json -Depth 5 -Compress
Set-Content -Path "$folderPath\booking_data.js" -Value "const BOOKING_DELIVERY_POINTS = $bookingJson;" -Encoding UTF8
Write-Output "Successfully generated booking_data.js with $($bookingList.Count) delivery points."

# Throw error if any file failed to process so run_pipeline.ps1 can report it
if ($failedFiles.Count -gt 0) {
    throw "There are $($failedFiles.Count) Excel files that failed to process: $($failedFiles -join ', '). Please check the file structure."
}

