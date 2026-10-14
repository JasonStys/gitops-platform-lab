"""Fixed synthetic SRE HTTP workload and exact-owned-service connectivity probe. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: TARGET — line 74
# definition: synthetic — line 77
# variable: events — line 79
# variable: index — line 81
# definition: Server — line 90
# variable: daemon_threads — line 93
# variable: block_on_close — line 94
# variable: allow_reuse_address — line 95
# definition: __init__ — line 97
# parameter: bind — line 97
# parameter: port — line 97
# parameter: self — line 97
# definition: process_request — line 108
# parameter: client_address — line 108
# parameter: request — line 108
# parameter: self — line 108
# definition: process_request_thread — line 119
# parameter: client_address — line 119
# parameter: request — line 119
# parameter: self — line 119
# definition: Handler — line 127
# variable: server — line 130
# definition: setup — line 132
# parameter: self — line 132
# definition: log_message — line 137
# parameter: args — line 137
# parameter: format — line 137
# parameter: self — line 137
# definition: send_error — line 140
# parameter: code — line 141
# parameter: explain — line 141
# parameter: message — line 141
# parameter: self — line 141
# definition: reply — line 146
# parameter: code — line 146
# parameter: data — line 146
# parameter: self — line 146
# variable: body — line 148
# definition: do_GET — line 163
# parameter: self — line 163
# definition: probe — line 173
# parameter: expect — line 173
# variable: opener — line 177
# variable: response — line 179
# variable: outcome — line 187
# variable: outcome — line 191
# variable: outcome — line 193
# definition: main — line 202
# variable: parser — line 204
# variable: args — line 207
# variable: server — line 212
# END CODE MAP

from __future__ import annotations

import argparse
import http.client
import json
import socket
import sys
import threading
import urllib.error
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

# The same unchanged analyzer runs locally and in a pod; it has no runtime dependencies.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "vendor"))
from sre.slo import Event, Policy, assess  # noqa: E402

TARGET = "http://sre.platform-lab.svc.cluster.local:8080/health"


def synthetic() -> dict[str, Any]:
    """Use 40 fixed successful synthetic events; the analyzer is the pinned prior portfolio implementation."""
    events = [
        Event(index, 1000 + index, 100, 200, f"{index:032x}", f"{index:016x}")
        for index in range(1, 41)
    ]
    return {
        "author": "Jason Stys",
        "synthetic": True,
        "analysis": assess(events, Policy(), 1040, 40),
    }


class Server(ThreadingHTTPServer):
    """At most eight active handlers, one-second socket timeout; binding is explicit, not remotely configurable."""

    daemon_threads = False
    block_on_close = True
    allow_reuse_address = False

    def __init__(self, bind: str, port: int) -> None:
        """Bind only loopback for native tests, or the pod interface for the cluster-owned workload."""
        if (
            bind not in {"127.0.0.1", "0.0.0.0"}
            or type(port) is not int
            or not 0 <= port <= 65535
        ):
            raise ValueError("invalid bind")
        self.slots = threading.BoundedSemaphore(8)
        super().__init__((bind, port), Handler)

    def process_request(self, request: Any, client_address: Any) -> None:
        """Refuse excess clients without unbounded thread creation; always release failed startup slots."""
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        """Release the concurrency slot even on malformed requests or disconnected peers."""
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class Handler(BaseHTTPRequestHandler):
    """Only fixed GET endpoints; no uploads, auth, dynamic inputs, request reflection or raw logging."""

    server: Server

    def setup(self) -> None:
        """Set a one-second socket limit before invoking the standard HTTP parser."""
        self.request.settimeout(1)
        super().setup()

    def log_message(self, format: str, *args: Any) -> None:
        """Suppress default request logs so raw headers, paths and queries are not persisted."""

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        """Return a fixed body, never the parser's untrusted text."""
        self.reply(code, {"error": "request rejected"})

    def reply(self, code: int, data: dict[str, Any]) -> None:
        """Emit small fixed JSON with no-sniff/cache headers; safely tolerate a disconnected peer."""
        body = json.dumps(data, sort_keys=True, allow_nan=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header(
            "Content-Security-Policy", "default-src 'none'; frame-ancestors 'none'"
        )
        self.end_headers()
        try:
            self.wfile.write(body)
        except (TimeoutError, BrokenPipeError, ConnectionResetError):
            pass

    def do_GET(self) -> None:
        """Serve exact health/work paths only; query strings and unknown routes are rejected."""
        if self.path == "/health":
            self.reply(200, {"status": "ok", "author": "Jason Stys", "synthetic": True})
        elif self.path == "/work":
            self.reply(200, synthetic())
        else:
            self.reply(404, {"error": "route unavailable"})


def probe(expect: str) -> dict[str, str]:
    """Probe only the owned cluster Service; deny is proved only by a timeout, never any generic failure."""
    if expect not in {"allow", "deny"}:
        raise ValueError("invalid expectation")
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(TARGET, timeout=2) as response:
            if (
                response.status != 200
                or response.read(4096)
                != b'{"author": "Jason Stys", "status": "ok", "synthetic": true}'
            ):
                raise ValueError("unexpected service response")
    except TimeoutError:
        outcome = "blocked"
    except urllib.error.URLError as error:
        if not isinstance(error.reason, (TimeoutError, socket.timeout)):
            raise ValueError("non-timeout is not proof of policy") from None
        outcome = "blocked"
    else:
        outcome = "allowed"
    if outcome != {"allow": "allowed", "deny": "blocked"}[expect]:
        raise ValueError("network expectation failed")
    return {
        "outcome": outcome,
        "reason": "http-200" if outcome == "allowed" else "timeout",
    }


def main() -> int:
    """Run the fixed probe or server; pod bind requires an explicit acknowledgement and no credentials."""
    parser = argparse.ArgumentParser(description="Synthetic SRE adapter — Jason Stys")
    parser.add_argument("--probe", choices=["allow", "deny"])
    parser.add_argument("--pod", action="store_true")
    args = parser.parse_args()
    try:
        if args.probe:
            print(json.dumps(probe(args.probe), sort_keys=True))
        else:
            with Server("0.0.0.0" if args.pod else "127.0.0.1", 8080) as server:
                server.serve_forever()
    except (ValueError, OSError, http.client.HTTPException):
        print('{"error":"owned workload check failed"}')
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
