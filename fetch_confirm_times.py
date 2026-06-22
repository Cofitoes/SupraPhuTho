import imaplib
import email
from email.header import decode_header
import sys
import json
import re
import os
import traceback

# Fix print encoding issues on Windows
sys.stdout.reconfigure(encoding='utf-8')

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

IMAP_SERVER = "imap.gmail.com"
EMAIL_ACCOUNT = "cuongnd@ghn.vn"
APP_PASSWORD = os.environ.get("EMAIL_APP_PASSWORD", "")


# File path to output departure times JavaScript
OUTPUT_JS_PATH = r"g:\My Drive\Training AI\Supra Phú Thọ\departure_times.js"

def decode_mime_header(header_value):
    if not header_value:
        return ""
    decoded_parts = decode_header(header_value)
    result = []
    for text, encoding in decoded_parts:
        if isinstance(text, bytes):
            try:
                result.append(text.decode(encoding if encoding else "utf-8", errors="ignore"))
            except Exception:
                result.append(text.decode("latin1", errors="ignore"))
        else:
            result.append(str(text))
    return "".join(result)

def fetch_confirm_times():
    extracted_data = {}
    stock_out_dates = {}
    try:
        if not APP_PASSWORD:
            print("[LỖI] Thiếu Mật khẩu ứng dụng Email! Vui lòng cấu hình EMAIL_APP_PASSWORD trong file .env")
            return

        print("Connecting to IMAP Gmail...")
        mail = imaplib.IMAP4_SSL(IMAP_SERVER)
        mail.login(EMAIL_ACCOUNT, APP_PASSWORD)
        print("Logged in successfully!")
        
        # Mở folder Tất cả thư thay vì inbox để đảm bảo quét được toàn bộ email (kể cả email bị lưu trữ/phân loại nhãn riêng)
        folder_name = '"[Gmail]/T&HqU-t c&HqM- th&AbA-"'
        print(f"Selecting folder: {folder_name}...")
        status, _ = mail.select(folder_name)
        if status != "OK":
            print("Failed to select, trying '[Gmail]/All Mail'...")
            status, _ = mail.select('"[Gmail]/All Mail"')
        if status != "OK":
            print("Failed to select All Mail, fallback to 'inbox'...")
            mail.select("inbox")
        
        # Search for emails containing "ORDER" in the subject (highly optimized search for booking threads)
        print("Searching for emails containing 'ORDER' in SUBJECT...")
        mail.literal = "ORDER".encode('utf-8')
        status, messages = mail.search('UTF-8', 'SUBJECT')
            
        if status == "OK" and messages[0]:
            email_ids = messages[0].split()
            print(f"Found {len(email_ids)} matching emails in All Mail.")
            
            # Tăng lên quét 50 email cuối cùng để quét đủ sâu trong Tất cả thư
            for e_id in email_ids[-50:]:
                try:
                    _, msg_data = mail.fetch(e_id, "(RFC822)")
                    for response_part in msg_data:
                        if isinstance(response_part, tuple):
                            msg = email.message_from_bytes(response_part[1])
                            subject = decode_mime_header(msg["Subject"])
                            sender = decode_mime_header(msg["From"])
                            
                            body = ""
                            if msg.is_multipart():
                                for part in msg.walk():
                                    content_type = part.get_content_type()
                                    content_disp = str(part.get("Content-Disposition"))
                                    if content_type == "text/plain" and "attachment" not in content_disp:
                                        payload = part.get_payload(decode=True)
                                        if payload:
                                            body = payload.decode('utf-8', errors='ignore')
                                            break
                            else:
                                payload = msg.get_payload(decode=True)
                                if payload:
                                    body = payload.decode('utf-8', errors='ignore')
                                    
                            if body:
                                # Xóa phần trích dẫn (quoted text) của email cũ để không bị nhầm lẫn ngày
                                quote_match = re.search(r'(Vào\s+(?:Thứ|Chủ|Lúc).*?đã viết:|On\s+.*?wrote:)', body, re.IGNORECASE | re.DOTALL)
                                if quote_match:
                                    body = body[:quote_match.start()]
                                body = re.sub(r'(?m)^>.*$', '', body)
                                
                                # Chỉ lấy các email thuộc phân hệ DCPT
                                if "DCPT".upper() not in subject.upper():
                                    continue
                                    
                                print(f"Processing email from {sender}: {subject}")
                                # 1. Ưu tiên tìm ngày Booking trong Body mà không đi cùng từ khóa 'Xuất'
                                date_match = re.search(r'(?<![Xx]uất\s)(?<![Xx]uất\shàng\s)ngày\s*\*?\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', body)
                                
                                # 2. Nếu không có trong Body, tìm trong Subject
                                if not date_match:
                                    date_match = re.search(r'(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', subject)
                                    
                                # 3. Nếu vẫn không thấy, mới fallback tìm ngày Xuất trong Body
                                if not date_match:
                                    date_match = re.search(r'[Xx]uất\s+(?:hàng\s+)?ngày\s*\*?\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', body)
                                    
                                if date_match:
                                    d, m, y = date_match.groups()
                                    date_str = f"{y}-{m.zfill(2)}-{d.zfill(2)}"
                                    
                                    # Trích xuất ngày xuất hàng thực tế từ body (ví dụ: Xuất ngày 27/05/2026)
                                    # Parse Stock Out Date from email
                                    current_email_stock_out = None
                                    stock_out_match = re.search(r'[Xx]uất\s+(?:hàng\s+)?ngày\s*\*?\s*(\d{1,2})\s*/\s*(\d{1,2})\s*/\s*(\d{4})', body)
                                    if stock_out_match:
                                        sd, sm, sy = stock_out_match.groups()
                                        current_email_stock_out = f"{sd.zfill(2)}/{sm.zfill(2)}/{sy}"
                                        print(f"  -> Match Date: {date_str}, Stock Out: {current_email_stock_out}")
                                        
                                        # Initialize dict if not present
                                        if date_str not in stock_out_dates:
                                            stock_out_dates[date_str] = {}
                                    else:
                                        print(f"  -> Found Booking Date {date_str} but no Stock Out date.")
                                    
                                    # Parse XE ... : ...H
                                    lines = body.split("\n")
                                    found_specific_vehicles = False
                                    trip_times = {}
                                    for line in lines:
                                        line = line.strip()
                                        xe_match = re.search(r'[Xx][Ee]\s*(\d+(?:\s*\+\s*\d+)*)\s*:\s*(\d+)\s*[Hh]', line)
                                        if xe_match:
                                            found_specific_vehicles = True
                                            trips_group, hour_str = xe_match.groups()
                                            hour = int(hour_str)
                                            formatted_time = f"{str(hour).zfill(2)}:00"
                                            
                                            trips = [int(t.strip()) for t in trips_group.split("+") if t.strip().isdigit()]
                                            for trip_num in trips:
                                                trip_times[str(trip_num)] = formatted_time
                                                if current_email_stock_out:
                                                    stock_out_dates[date_str][str(trip_num)] = current_email_stock_out
                                    
                                    # If email has a global stock out date but NO specific vehicles mentioned, apply to "all"
                                    if current_email_stock_out and not found_specific_vehicles:
                                        stock_out_dates[date_str]["all"] = current_email_stock_out
                                                
                                    if trip_times:
                                        if date_str not in extracted_data:
                                            extracted_data[date_str] = {}
                                        extracted_data[date_str].update(trip_times)
                                        
                except Exception as fe:
                    print(f"Error fetching email {e_id}: {fe}")
        else:
            print("No matching emails found.")
            
        mail.close()
        mail.logout()
        
        # Write to departure_times.js in the workspace
        js_content = f"const DEPARTURE_TIMES = {json.dumps(extracted_data, ensure_ascii=False, indent=2)};\n"
        js_content += f"const STOCK_OUT_DATES = {json.dumps(stock_out_dates, ensure_ascii=False, indent=2)};\n"
        with open(OUTPUT_JS_PATH, "w", encoding="utf-8") as js_file:
            js_file.write(js_content)
        print(f"Successfully generated {OUTPUT_JS_PATH} with {len(extracted_data)} dates and {len(stock_out_dates)} stock out dates.")
        
    except Exception as e:
        print(f"Error: {e}")
        traceback.print_exc()

if __name__ == "__main__":
    fetch_confirm_times()
