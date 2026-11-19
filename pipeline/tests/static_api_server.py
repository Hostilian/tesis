"""Local contract-test server for the versioned static JSON GitHub Pages API.

This is deliberately a test fixture, not a live satellite ingestion service.
It serves exactly the committed docs/api/v1/**/index.json records as JSON.
"""

from __future__ import annotations

import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import unquote, urlsplit

API_ROOT = (Path(__file__).resolve().parents[2] / "docs" / "api" / "v1").resolve()


class StaticApiHandler(BaseHTTPRequestHandler):
    server_version = "StaticJSONContract/1.0"

    def _reply(self, status: int, payload: bytes, *, send_body: bool = True) -> None:
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("Allow", "GET, HEAD")
        self.end_headers()
        if send_body:
            self.wfile.write(payload)

    def _serve(self, *, send_body: bool = True) -> None:
        request_path = unquote(urlsplit(self.path).path)
        parts = request_path.strip("/").split("/")
        if parts[:2] != ["api", "v1"] or len(parts) < 3:
            self._reply(404, b'{"detail":"Not found"}', send_body=send_body)
            return

        target = (API_ROOT.joinpath(*parts[2:]) / "index.json").resolve()
        if not target.is_relative_to(API_ROOT) or not target.is_file():
            self._reply(404, b'{"detail":"Not found"}', send_body=send_body)
            return

        # Invalid files should be surfaced as a test failure, not as success.
        payload = target.read_bytes()
        try:
            json.loads(payload)
        except (UnicodeDecodeError, json.JSONDecodeError):
            self._reply(500, b'{"detail":"Invalid static JSON"}', send_body=send_body)
            return
        self._reply(200, payload, send_body=send_body)

    def do_GET(self) -> None:
        self._serve()

    def do_HEAD(self) -> None:
        self._serve(send_body=False)

    def _method_not_allowed(self) -> None:
        self._reply(405, b'{"detail":"Method not allowed"}')

    do_OPTIONS = _method_not_allowed
    do_POST = _method_not_allowed
    do_PUT = _method_not_allowed
    do_PATCH = _method_not_allowed
    do_DELETE = _method_not_allowed
    do_TRACE = _method_not_allowed
    do_CONNECT = _method_not_allowed


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve committed static JSON API for contract tests")
    parser.add_argument("--port", type=int, default=8081)
    args = parser.parse_args()
    with ThreadingHTTPServer(("127.0.0.1", args.port), StaticApiHandler) as server:
        print(f"Serving static API contract on 127.0.0.1:{args.port}", flush=True)
        server.serve_forever()


if __name__ == "__main__":
    main()
