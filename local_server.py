import os
import json
import sys
import subprocess
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer

PORT = 8080
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))

class LogisticsHandler(SimpleHTTPRequestHandler):
    def translate_path(self, path):
        # Strip query parameters and fragment identifiers
        path = path.split('?', 1)[0].split('#', 1)[0]
        # Serve static files from WORKSPACE_DIR
        return os.path.join(WORKSPACE_DIR, path.lstrip('/'))

    def do_POST(self):
        if self.path == '/api/incident':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                incident = json.loads(post_data.decode('utf-8'))
                inc_id = incident.get('id', 'INC-UNKNOWN')
                
                # Write directly to Su_Co folder
                folder = os.path.join(WORKSPACE_DIR, "Su_Co")
                if not os.path.exists(folder):
                    os.makedirs(folder)
                    
                file_path = os.path.join(folder, f"SuCo_{inc_id}.json")
                with open(file_path, 'w', encoding='utf-8') as f:
                    json.dump(incident, f, indent=4, ensure_ascii=False)
                
                print(f"[SERVER] Ghi nhan su co thanh cong: {inc_id}")
                
                # Removed auto-run of process_incidents.py based on user request
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": "Incident saved directly to Su_Co!"}).encode('utf-8'))
                
            except Exception as e:
                print(f"[SERVER] Loi khi ghi nhan su co: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        elif self.path == '/api/checkin-upload':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                file_name = data.get('fileName', '')
                image_base64 = data.get('imageBase64', '')
                
                if not file_name or not image_base64:
                    raise ValueError("File name and imageBase64 are required!")
                
                if ',' in image_base64:
                    image_base64 = image_base64.split(',', 1)[1]
                
                import base64
                image_bytes = base64.b64decode(image_base64)
                
                # Write directly to NCC Checkin folder
                folder = os.path.join(WORKSPACE_DIR, "NCC Checkin")
                if not os.path.exists(folder):
                    os.makedirs(folder)
                    
                file_path = os.path.join(folder, file_name)
                with open(file_path, 'wb') as f:
                    f.write(image_bytes)
                
                print(f"[SERVER] Upload check-in thanh cong: {file_name}")
                
                # Removed auto-run of process_checkin.py based on user request
                
                # Send success response
                self.send_response(200)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "success", "message": f"Check-in photo saved to {file_name}!"}).encode('utf-8'))
                
            except Exception as e:
                print(f"[SERVER] Loi khi upload check-in photo: {e}")
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                self.wfile.write(json.dumps({"status": "error", "message": str(e)}).encode('utf-8'))
        else:
            super().do_POST()

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

def run():
    os.chdir(WORKSPACE_DIR)
    server_address = ('', PORT)
    httpd = ThreadingHTTPServer(server_address, LogisticsHandler)
    url = f"http://localhost:{PORT}/index.html"
    print(f"========================================================")
    print(f"Logistics Hub Local Server running at {url}")
    print(f"Giao dien tu dong mo tren Microsoft Edge. Nhan Ctrl+C de dung.")
    print(f"========================================================")
    
    # Auto-open dashboard in Microsoft Edge
    try:
        edge_path = "C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe"
        if os.path.exists(edge_path):
            webbrowser.register('edge', None, webbrowser.BackgroundBrowser(edge_path))
            webbrowser.get('edge').open(url)
        else:
            webbrowser.open(url)
    except Exception:
        webbrowser.open(url)
    
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopping server...")
        httpd.server_close()

if __name__ == '__main__':
    run()

