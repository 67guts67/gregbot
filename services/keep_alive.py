
import os
from threading import Thread
from http.server import HTTPServer, BaseHTTPRequestHandler


class Handler(BaseHTTPRequestHandler):

    def _send_headers(self):
        self.send_response(200)
        self.send_header(
            "Content-type",
            "text/plain"
        )
        self.end_headers()


    def do_GET(self):
        self._send_headers()
        self.wfile.write(b"OK")


    def do_HEAD(self):
        self._send_headers()



def run_server():
    port = int(os.environ.get("PORT", 10000))

    HTTPServer(
        ("0.0.0.0", port),
        Handler
    ).serve_forever()



def start():
    Thread(
        target=run_server,
        daemon=True
    ).start()