"""Minimal webhook server for live position payloads.

POST JSON to /api/positions/callback and it will save payloads under Position Files
as a timestamped JSON backup.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from datetime import datetime
import json

BASE_DIR = Path(__file__).parent
POSITION_DIR = BASE_DIR / "Position Files"
HOST = "0.0.0.0"
PORT = 8765


class PositionWebhookHandler(BaseHTTPRequestHandler):
    def _send_json(self, code, payload):
        body = json.dumps(payload).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_POST(self):
        if self.path != "/api/positions/callback":
            self._send_json(404, {"ok": False, "error": "Not found"})
            return

        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length) if length > 0 else b""
            payload = json.loads(raw.decode("utf-8")) if raw else {}
        except Exception as ex:
            self._send_json(400, {"ok": False, "error": f"Invalid JSON: {ex}"})
            return

        POSITION_DIR.mkdir(parents=True, exist_ok=True)
        ts = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        out_file = POSITION_DIR / f"api_positions_{ts}.json"
        out_file.write_text(json.dumps(payload, indent=2), encoding="utf-8")

        self._send_json(
            200,
            {
                "ok": True,
                "saved": str(out_file.name),
                "message": "Payload saved. Position Files remains your backup source.",
            },
        )

    def log_message(self, fmt, *args):
        # Keep console output concise
        return


if __name__ == "__main__":
    server = HTTPServer((HOST, PORT), PositionWebhookHandler)
    print(f"Callback URL: http://localhost:{PORT}/api/positions/callback")
    print("Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
