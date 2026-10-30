"""Cheapest Bot: a tiny read-only HTTP service. Python 3 stdlib only.

Endpoints (GET only, no auth, no logging, CORS open):
  GET /                -> static page (public/index.html)
  GET /api/models      -> data/models.json
  GET /api/benchmark   -> data/benchmark.json
  GET /api/cheapest?task=short|long|code&max_input_k=N[&billing=any|allowance]
  GET /healthz         -> ok

Run: HOST=127.0.0.1 PORT=8787 python3 server.py   (put a reverse proxy with TLS in front)
"""
import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

import cheapest

HERE = os.path.dirname(os.path.abspath(__file__))


def _read(rel):
    with open(os.path.join(HERE, rel), "rb") as f:
        return f.read()


class Handler(BaseHTTPRequestHandler):
    server_version = "cheapest-bot"
    sys_version = ""

    def log_message(self, *args):  # no access logs, no IPs
        pass

    def _send(self, code, body, ctype="application/json; charset=utf-8", head=False):
        if isinstance(body, (dict, list)):
            body = (json.dumps(body, indent=2, ensure_ascii=False) + "\n").encode()
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, HEAD, OPTIONS")
        self.send_header("Cache-Control", "public, max-age=300")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "no-referrer")
        if ctype.startswith("text/html"):
            self.send_header("Content-Security-Policy",
                             "default-src 'self'; style-src 'self' 'unsafe-inline'; script-src 'self' 'unsafe-inline'")
        self.end_headers()
        if not head:
            self.wfile.write(body)

    def _route(self, head=False):
        u = urlparse(self.path)
        if u.path in ("/", "/index.html"):
            return self._send(200, _read("public/index.html"), "text/html; charset=utf-8", head)
        if u.path == "/api/models":
            return self._send(200, _read("data/models.json"), head=head)
        if u.path == "/api/benchmark":
            return self._send(200, _read("data/benchmark.json"), head=head)
        if u.path == "/healthz":
            return self._send(200, b"ok\n", "text/plain; charset=utf-8", head)
        if u.path == "/api/cheapest":
            q = {k: v[0] for k, v in parse_qs(u.query).items()}
            try:
                mik = q.get("max_input_k")
                if mik is not None:
                    if not mik.isdigit():
                        raise ValueError("max_input_k must be an integer from 0 to 10000")
                    mik = int(mik)
                res = cheapest.cheapest(q.get("task", "short"), mik, q.get("billing", "any"))
            except ValueError as e:
                return self._send(400, {"error": str(e)}, head=head)
            return self._send(200, res, head=head)
        return self._send(404, {"error": "not found"}, head=head)

    def do_GET(self):
        self._route()

    def do_HEAD(self):
        self._route(head=True)

    def do_OPTIONS(self):
        self._send(204, b"", "text/plain")

    def _no(self):
        self._send(405, {"error": "read-only service"})

    do_POST = do_PUT = do_PATCH = do_DELETE = _no


if __name__ == "__main__":
    host = os.environ.get("HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8787"))
    print(f"cheapest-bot listening on http://{host}:{port}")
    ThreadingHTTPServer((host, port), Handler).serve_forever()
