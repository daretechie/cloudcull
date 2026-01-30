import http.server
import socketserver
import os
import json
import logging
from urllib.parse import urlparse

# Configuration
PORT = 8080
WEB_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "dashboard/dist")
LOG_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "logs/sniper.log")
REPORT_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "report.json")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - [DashboardServer] - %(message)s')
logger = logging.getLogger("DashboardServer")

class SecureDashboardHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        
        # API: Logs
        if parsed.path == '/api/logs':
            self.send_response(200)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            try:
                if os.path.exists(LOG_FILE):
                    with open(LOG_FILE, 'rb') as f: # Binary to handle potential encoding issues
                        # Read last 100KB to avoid massive payloads
                        f.seek(0, 2)
                        size = f.tell()
                        f.seek(max(0, size - 100000))
                        content = f.read()
                        self.wfile.write(content)
                else:
                    self.wfile.write(b"No logs available.")
            except Exception as e:
                logger.error(f"Failed to read logs: {e}")
                self.wfile.write(f"Error reading logs: {e}".encode())
            return

        # API: Report
        if parsed.path == '/api/report':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            try:
                if os.path.exists(REPORT_FILE):
                    with open(REPORT_FILE, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.wfile.write(json.dumps({"error": "No report found. Run audit first."}).encode())
            except Exception as e:
                logger.error(f"Failed to read report: {e}")
                self.wfile.write(json.dumps({"error": str(e)}).encode())
            return
            
        # Static Files (SPA fallback)
        # If file doesn't exist, serve index.html for client-side routing
        path = self.translate_path(self.path)
        if not os.path.exists(path) and not parsed.path.startswith('/api/'):
            self.path = '/index.html'
            
        return super().do_GET()

if __name__ == "__main__":
    if not os.path.exists(WEB_DIR):
        logger.warning(f"Web directory {WEB_DIR} not found. Please run 'npm run build' in 'dashboard/'.")
        os.makedirs(WEB_DIR, exist_ok=True)
        with open(os.path.join(WEB_DIR, "index.html"), "w") as f:
            f.write("<h1>Dashboard not built. Run 'npm run build' in dashboard/ directory.</h1>")

    logger.info(f"Serving Secure Dashboard at http://localhost:{PORT}")
    logger.info("API Endpoints: /api/logs, /api/report")
    
    with socketserver.TCPServer(("", PORT), SecureDashboardHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
