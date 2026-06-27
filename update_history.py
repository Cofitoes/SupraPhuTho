import os
import subprocess

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\git_push.log"

try:
    history_file = r"g:\My Drive\Training AI\Supra Phú Thọ\LichSuCapNhat.md"
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        new_entry = """## 1. Cập nhật ngày 27/06/2026 (Phần 3): Tích hợp Nút Xóa Cache & Rà Soát Hệ Thống
- **Hệ thống cache cục bộ (localStorage caching):**
  - Tích hợp bộ nhớ đệm `localStorage` cho cả chuyến đi thẳng / trung chuyển Masan/Supra (`supra_trips_cache_[date]`) và chuyến bưu cục GHN (`supra_trips_ghn_cache_[date]`).
  - Khi người dùng chuyển đổi giữa các ngày hoặc chuyển đổi qua lại giữa các tab, hệ thống sẽ nạp dữ liệu lập tức từ cache thay vì gọi OSRM API tính toán lại từ đầu, giúp tốc độ tải trang phản hồi tức thì và loại bỏ hoàn toàn hiện tượng trễ/lag.
- **Nút "Xóa Cache Hiển Thị" màu đỏ:**
  - Bổ sung nút **Xóa Cache Hiển Thị** ngay bên cạnh nút "Chạy Tối Ưu Tuyến".
  - Khi click nút này, toàn bộ dữ liệu cache lưu trong `localStorage` sẽ bị xóa bỏ hoàn toàn, đồng thời kích hoạt tính toán lại từ đầu và gọi OSRM lấy khoảng cách thực tế mới nhất.
  - Khi xóa thành công, giao diện hiển thị thông báo toast màu xanh lá ở góc dưới bên phải màn hình: *"Đã xóa toàn bộ cache hiển thị và tính toán lại!"*.
- **Rà soát & Loại bỏ triệt để liên quan Con Cưng:**
  - Xóa bỏ các file vá lỗi cũ dư thừa (`fix_all.py`, `fix_ghn_lag.py`, `remove_concung_safe.py`).
  - Chuẩn hóa tên trường sự cố từ `Mã Đơn ConCung` thành `Mã Đơn / Booking` để nhất quán với dự án Supra Phú Thọ.
  - Thay thế tiêu đề trang web hiển thị trên tab trình duyệt thành **`Supra Phú Thọ | Quản Lý Vận Tải Thông Minh`**.

"""
        # Insert after the title lines
        # Title is:
        # # Lịch Sử Cập Nhật Hệ Thống Supra Phú Thọ
        # 
        # Tài liệu này lưu trữ các thay đổi và cập nhật quan trọng của hệ thống tính toán và ghép tuyến (Cập nhật mới nhất: 27/06/2026).
        #
        insert_idx = 0
        for i, line in enumerate(lines):
            if "Tài liệu này lưu trữ" in line:
                insert_idx = i + 2
                break
        
        if insert_idx == 0:
            insert_idx = 4

        lines.insert(insert_idx, new_entry)

        with open(history_file, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("Updated LichSuCapNhat.md successfully.")

    # Git commit and push
    git_path = r"C:\Program Files\Git\cmd\git.exe"
    if not os.path.exists(git_path):
        git_path = "git"

    subprocess.run([git_path, "add", "LichSuCapNhat.md"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    subprocess.run([git_path, "commit", "-m", "Update changelog with clear cache button and branding cleanup"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)
    subprocess.run([git_path, "push", "origin", "main"], cwd=r"g:\My Drive\Training AI\Supra Phú Thọ", check=True)

    # Restore Cap_Nhat_Du_Lieu_Auto.bat
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

    # Self delete
    os.remove(__file__)

except Exception as e:
    print(f"Error: {e}")
