"""
Web Server for WinCustomizer Studio
Provides REST API endpoints and Server-Sent Events (SSE) for real-time progress updates.
"""

import os
import sys
import json
import queue
import threading
import urllib.parse
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
import logging

# Ensure parent directory is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from wincustomizer.iso_handler import ISOHandler
from wincustomizer.orchestrator import CustomizationOrchestrator
from wincustomizer.presets import APPX_CATALOG, TWEAK_PRESETS, DEBLOAT_PROFILES

logger = logging.getLogger("WinCustomizer.WebServer")
logging.basicConfig(level=logging.INFO)

# Global queue for SSE events
sse_clients = []

def broadcast_log(message: str):
    data = f"data: {json.dumps({'message': message})}\n\n"
    dead_clients = []
    for client in sse_clients:
        try:
            client.wfile.write(data.encode('utf-8'))
            client.wfile.flush()
        except Exception:
            dead_clients.append(client)
    for dc in dead_clients:
        if dc in sse_clients:
            sse_clients.remove(dc)

class CustomizerRequestHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        # Silence standard HTTP access logging to keep console clean
        pass

    def _set_headers(self, content_type="application/json", status=200):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        if path == "/api/presets":
            self._set_headers()
            response = {
                "appx_catalog": APPX_CATALOG,
                "tweak_presets": TWEAK_PRESETS,
                "debloat_profiles": DEBLOAT_PROFILES
            }
            self.wfile.write(json.dumps(response).encode('utf-8'))

        elif path == "/api/events":
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache")
            self.send_header("Connection", "keep-alive")
            self.send_header("Access-Control-Allow-Origin", "*")
            self.end_headers()

            sse_clients.append(self)
            # Keep connection open until disconnect
            try:
                while True:
                    # Heartbeat
                    self.wfile.write(": keepalive\n\n".encode('utf-8'))
                    self.wfile.flush()
                    threading.Event().wait(15)
            except Exception:
                if self in sse_clients:
                    sse_clients.remove(self)

        else:
            # Serve static files
            if getattr(sys, 'frozen', False):
                base_web_dir = os.path.join(sys._MEIPASS, "web")
            else:
                base_web_dir = os.path.dirname(__file__)

            if path == "/":
                file_path = os.path.join(base_web_dir, "static", "index.html")
                content_type = "text/html"
            else:
                rel_path = path.lstrip("/")
                file_path = os.path.join(base_web_dir, "static", rel_path)
                if file_path.endswith(".css"):
                    content_type = "text/css"
                elif file_path.endswith(".js"):
                    content_type = "application/javascript"
                elif file_path.endswith(".png"):
                    content_type = "image/png"
                elif file_path.endswith(".svg"):
                    content_type = "image/svg+xml"
                else:
                    content_type = "text/plain"

            if os.path.exists(file_path) and os.path.isfile(file_path):
                self._set_headers(content_type=content_type)
                with open(file_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.send_error(404, "File Not Found")

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        content_len = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_len).decode('utf-8')
        data = json.loads(body) if body else {}

        if path == "/api/inspect-iso":
            iso_path = data.get("iso_path", "")
            if not os.path.exists(iso_path):
                self._set_headers(status=400)
                self.wfile.write(json.dumps({"error": f"ISO file path does not exist: {iso_path}"}).encode('utf-8'))
                return

            try:
                handler = ISOHandler(work_dir="work")
                broadcast_log(f"Extracting & inspecting ISO: {iso_path}...")
                handler.extract_iso(iso_path, progress_callback=broadcast_log)
                info = handler.get_image_info()
                self._set_headers()
                self.wfile.write(json.dumps({"success": True, "editions": info}).encode('utf-8'))
            except Exception as e:
                self._set_headers(status=500)
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))

        elif path == "/api/start-build":
            iso_path = data.get("iso_path", "")
            edition_index = int(data.get("edition_index", 1))
            debloat_profile = data.get("debloat_profile", "max_privacy")
            custom_appx = data.get("custom_appx", [])
            tweaks = data.get("tweaks", {})
            unattended_config = data.get("unattended_config", {})
            drivers_dir = data.get("drivers_dir", None)

            def worker():
                try:
                    orchestrator = CustomizationOrchestrator(work_dir="work", output_dir="dist")
                    output_iso = orchestrator.run_pipeline(
                        iso_path=iso_path,
                        edition_index=edition_index,
                        debloat_profile=debloat_profile,
                        custom_appx=custom_appx,
                        tweaks=tweaks,
                        unattended_config=unattended_config,
                        drivers_dir=drivers_dir,
                        log_callback=broadcast_log
                    )
                    broadcast_log(f"BUILD_SUCCESS:{output_iso}")
                except Exception as e:
                    broadcast_log(f"BUILD_ERROR:{str(e)}")

            threading.Thread(target=worker, daemon=True).start()
            self._set_headers()
            self.wfile.write(json.dumps({"success": True, "message": "Build pipeline started."}).encode('utf-8'))

        else:
            self.send_error(404, "Endpoint Not Found")

def run_server(port=5000):
    server_address = ('', port)
    httpd = ThreadingHTTPServer(server_address, CustomizerRequestHandler)
    print(f"\n=======================================================")
    print(f" WinCustomizer Studio Web Dashboard Live at:")
    print(f" http://localhost:{port}")
    print(f"=======================================================\n")
    httpd.serve_forever()

if __name__ == "__main__":
    run_server()
