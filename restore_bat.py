import os

log = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"
if os.path.exists(log):
    try:
        os.remove(log)
    except:
        pass

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

if os.path.exists(__file__):
    os.remove(__file__)
