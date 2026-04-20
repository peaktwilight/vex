"""Minimal OpenAI-compatible chat-completions server used as a fake LLM for
contract / promptfoo tests.

Usage::

    python tests/contract/fixtures/fake_provider.py --port 18080

Then point an OpenAI-compat client at ``http://127.0.0.1:18080/v1`` with any
non-empty API key. Every request returns the same canned response — enough
for promptfoo/inspect-ai style adapters to exercise their request/response
plumbing without touching a real model.

Intentionally stdlib-only (``http.server``, ``json``, ``argparse``) so it can
be launched from a test without pulling extra dependencies.
"""

from __future__ import annotations

import argparse
import json
import time
import uuid
from http.server import BaseHTTPRequestHandler, HTTPServer


CANNED_CONTENT = "contract-fake-response"


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, format: str, *args) -> None:  # noqa: A002 - stdlib signature
        # Silence default stderr logging so tests don't get noisy output.
        return

    def _write_json(self, status: int, body: dict) -> None:
        payload = json.dumps(body).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def do_POST(self) -> None:  # noqa: N802 - http.server API
        if self.path not in {"/v1/chat/completions", "/chat/completions"}:
            self._write_json(404, {"error": {"message": f"unknown path {self.path}"}})
            return

        length = int(self.headers.get("Content-Length") or 0)
        _body = self.rfile.read(length) if length else b"{}"

        response = {
            "id": f"chatcmpl-{uuid.uuid4().hex[:12]}",
            "object": "chat.completion",
            "created": int(time.time()),
            "model": "fake-provider/contract",
            "choices": [
                {
                    "index": 0,
                    "message": {"role": "assistant", "content": CANNED_CONTENT},
                    "finish_reason": "stop",
                }
            ],
            "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        }
        self._write_json(200, response)

    def do_GET(self) -> None:  # noqa: N802 - http.server API
        if self.path in {"/healthz", "/v1/models"}:
            self._write_json(200, {"status": "ok"})
            return
        self._write_json(404, {"error": {"message": f"unknown path {self.path}"}})


def run(host: str, port: int) -> None:
    server = HTTPServer((host, port), _Handler)
    try:
        server.serve_forever()
    finally:
        server.server_close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=18080)
    args = parser.parse_args()
    run(args.host, args.port)


if __name__ == "__main__":
    main()
