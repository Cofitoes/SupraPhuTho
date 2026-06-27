import os
import re

log_path = r"g:\My Drive\Training AI\Supra Phú Thọ\clean_error.log"

try:
    files_to_clean = [
        r"g:\My Drive\Training AI\Supra Phú Thọ\demo.html",
        r"g:\My Drive\Training AI\Supra Phú Thọ\index.html"
    ]

    for f_path in files_to_clean:
        if os.path.exists(f_path):
            with open(f_path, 'r', encoding='utf-8') as f:
                content = f.read()

            # Clean the HTML form comments and labels (using regex to handle line endings and spacing)
            content = re.sub(r"<!--\s*1\.\s*Chọn\s*Ngày\s*&\s*Mã\s*đơn\s*ConCung\s*-->", "<!-- 1. Chọn Ngày & Mã Đơn / Booking -->", content, flags=re.IGNORECASE)
            content = re.sub(r"Mã\s+Đơn\s+ConCung", "Mã Đơn / Booking", content, flags=re.IGNORECASE)
            content = content.replace("incident-concung-code", "incident-booking-code")
            content = content.replace("concungCodeVal", "bookingCodeVal")
            content = content.replace("concungCode:", "bookingCode:")
            content = content.replace("item.concungCode", "item.bookingCode")

            # Clean JS dead checks
            content = re.sub(r"if\s*\(\s*typeof\s*concungData\s*!==\s*'undefined'\s*\)\s*\{\s*const\s+b\s*=\s*p\.buff\s*\|\|\s*p\.Buff\s*\|\|\s*p\.BUFF;\s*if\s*\(b\)\s*\{\s*const\s+matched\s*=\s*concungData\.find\([^)]+\);\s*if\s*\(matched\s*&&\s*matched\['Trạng thái hệ thống'\]\s*===\s*'Giao hàng thành công'\)\s*\{\s*return\s+false;\s*\}\s*\}\s*\}", "", content)

            with open(f_path, 'w', encoding='utf-8') as f:
                f.write(content)
            with open(log_path, 'a', encoding='utf-8') as log:
                log.write(f"Cleaned ConCung references in: {f_path}\n")

    # Clean download_booking_emails.py
    email_script = r"g:\My Drive\Training AI\Supra Phú Thọ\download_booking_emails.py"
    if os.path.exists(email_script):
        with open(email_script, 'r', encoding='utf-8') as f:
            content = f.read()
        
        content = content.replace('"CONCUNG"', '"SUPRA"')
        content = content.replace("'CONCUNG'", "'SUPRA'")
        
        with open(email_script, 'w', encoding='utf-8') as f:
            f.write(content)
        with open(log_path, 'a', encoding='utf-8') as log:
            log.write(f"Cleaned ConCung references in: {email_script}\n")

    # Delete old files
    old_files = [
        r"g:\My Drive\Training AI\Supra Phú Thọ\fix_all.py",
        r"g:\My Drive\Training AI\Supra Phú Thọ\fix_ghn_lag.py",
        r"g:\My Drive\Training AI\Supra Phú Thọ\remove_concung_safe.py"
    ]
    for f in old_files:
        if os.path.exists(f):
            try:
                os.remove(f)
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"Deleted old file: {f}\n")
            except Exception as e:
                with open(log_path, 'a', encoding='utf-8') as log:
                    log.write(f"Failed to delete {f}: {e}\n")

except Exception as e:
    with open(log_path, 'a', encoding='utf-8') as log:
        log.write(f"ERROR occurred: {e}\n")
