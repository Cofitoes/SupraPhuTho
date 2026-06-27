import os
import subprocess

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"

try:
    # 1. Run the patcher script first to apply cache button and logic changes
    patcher = r"g:\My Drive\Training AI\Supra Phú Thọ\patch_clear_cache.py"
    if os.path.exists(patcher):
        subprocess.run(["python", patcher], check=True)
        os.remove(patcher)
        with open(log_path, 'a', encoding='utf-8') as log:
            log.write("Successfully patched caching code and deleted patcher.\n")

    # 2. Find git executable
    git_path = r"C:\Program Files\Git\cmd\git.exe"
    if not os.path.exists(git_path):
        git_path = "git"

    # 3. Add files and commit
    files_to_commit = ["demo.html", "index.html", "run_pipeline.ps1", "download_booking_emails.py"]
    for f in files_to_commit:
        f_full = os.path.join(r"g:\My Drive\Training AI\Supra Phú Thọ", f)
        if os.path.exists(f_full):
            subprocess.run([git_path, "add", f], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    
    # Check if there are changes to commit
    status_proc = subprocess.run([git_path, "status", "--porcelain"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", capture_output=True, text=True)
    if status_proc.stdout.strip():
        subprocess.run([git_path, "commit", "-m", "Clean ConCung and implement Clear Cache button with localStorage caching"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
        subprocess.run([git_path, "push", "origin", "main"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
        with open(log_path, 'a', encoding='utf-8') as log:
            log.write("Successfully committed and pushed changes to GitHub.\n")
    else:
        with open(log_path, 'a', encoding='utf-8') as log:
            log.write("No changes detected to commit.\n")

    # 4. Restore Cap_Nhat_Du_Lieu_Auto.bat
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
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write("Restored Cap_Nhat_Du_Lieu_Auto.bat to original content.\n")

    # 5. Self delete
    os.remove(__file__)
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write("Self deleted push_changes.py successfully.\n")

except Exception as e:
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"ERROR: {e}\n")
