"""Fixed synthetic SRE HTTP workload and exact-owned-service connectivity probe. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: TARGET — line 94
# definition: ProbeFailure — line 97
# definition: __init__ — line 100
# parameter: reason — line 100
# parameter: self — line 100
# definition: synthetic — line 115
# variable: events — line 117
# variable: index — line 119
# definition: Server — line 128
# variable: daemon_threads — line 131
# variable: block_on_close — line 132
# variable: allow_reuse_address — line 133
# definition: __init__ — line 135
# parameter: bind — line 135
# parameter: port — line 135
# parameter: self — line 135
# definition: process_request — line 146
# parameter: client_address — line 146
# parameter: request — line 146
# parameter: self — line 146
# definition: process_request_thread — line 157
# parameter: client_address — line 157
# parameter: request — line 157
# parameter: self — line 157
# definition: Handler — line 165
# variable: server — line 168
# definition: setup — line 170
# parameter: self — line 170
# definition: log_message — line 175
# parameter: args — line 175
# parameter: format — line 175
# parameter: self — line 175
# definition: send_error — line 178
# parameter: code — line 179
# parameter: explain — line 179
# parameter: message — line 179
# parameter: self — line 179
# definition: reply — line 184
# parameter: code — line 184
# parameter: data — line 184
# parameter: self — line 184
# variable: body — line 186
# definition: do_GET — line 201
# parameter: self — line 201
# definition: probe — line 211
# parameter: expect — line 211
# variable: opener — line 215
# variable: response — line 217
# variable: outcome — line 225
# variable: reason — line 226
# variable: reason — line 230
# variable: reason — line 232
# variable: reason — line 239
# variable: reason — line 241
# variable: reason — line 245
# variable: outcome — line 246
# variable: outcome — line 248
# variable: reason — line 249
# definition: main — line 258
# variable: parser — line 260
# variable: args — line 264
# variable: server — line 269
# definition: emit — line 283
# parameter: data — line 283
# parameter: hold — line 283
# variable: released — line 290
# variable: prior — line 291
# parameter: _frame — line 292
# parameter: _number — line 292
# END CODE MAP

from __future__ import annotations

import argparse
import errno
import http.client
import json
import signal
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


class ProbeFailure(ValueError):
    """Stable transport/result diagnostic, never the raw request, URL, credentials or exception text."""

    def __init__(self, reason: str) -> None:
        """Require a fixed allowlisted diagnostic code, not arbitrary private strings."""
        if reason not in {
            "connection-refused",
            "network-unreachable",
            "dns-failure",
            "transport-error",
            "unexpected-response",
            "expectation-mismatch",
        }:
            raise ValueError("invalid diagnostic")
        self.reason = reason
        super().__init__(reason)


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
    """Return a provisional owned-Service transport observation; only the host counter/control oracle proves denial."""
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
                raise ProbeFailure("unexpected-response")
    except TimeoutError:
        outcome = "blocked"
        reason = "timeout"
    except urllib.error.URLError as error:
        if not isinstance(error.reason, (TimeoutError, socket.timeout)):
            if isinstance(error.reason, ConnectionRefusedError):
                reason = "connection-refused"
            elif isinstance(error.reason, socket.gaierror):
                reason = "dns-failure"
            elif isinstance(error.reason, OSError) and error.reason.errno in {
                errno.EHOSTUNREACH,
                errno.ENETUNREACH,
                errno.EPERM,
                errno.EACCES,
            }:
                reason = "network-unreachable"
            else:
                reason = "transport-error"
            if reason not in {"connection-refused", "network-unreachable"}:
                raise ProbeFailure(reason) from None
        else:
            reason = "timeout"
        outcome = "blocked"
    else:
        outcome = "allowed"
        reason = "http-200"
    if outcome != {"allow": "allowed", "deny": "blocked"}[expect]:
        raise ProbeFailure("expectation-mismatch")
    return {
        "outcome": outcome,
        "reason": reason,
    }


def main() -> int:
    """Run the fixed probe or server; pod bind requires an explicit acknowledgement and no credentials."""
    parser = argparse.ArgumentParser(description="Synthetic SRE adapter — Jason Stys")
    parser.add_argument("--probe", choices=["allow", "deny"])
    parser.add_argument("--pod", action="store_true")
    parser.add_argument("--hold-observation", action="store_true")
    args = parser.parse_args()
    try:
        if args.probe:
            emit(probe(args.probe), args.hold_observation)
        else:
            with Server("0.0.0.0" if args.pod else "127.0.0.1", 8080) as server:
                server.serve_forever()
    except ProbeFailure as error:
        emit(
            {"error": "owned workload check failed", "reason": error.reason},
            args.hold_observation,
        )
        return 1
    except (ValueError, OSError, http.client.HTTPException):
        print('{"error":"owned workload check failed"}')
        return 1
    return 0


def emit(data: dict[str, str], hold: bool) -> None:
    """Flush a receipt after registering a bounded SIGUSR1 acknowledgement; PID 1 cannot rely on SIGSTOP."""
    if not hold:
        print(json.dumps(data, sort_keys=True), flush=True)
        return
    if not hasattr(signal, "SIGUSR1"):
        raise ValueError("observation requires Linux pod")
    released = threading.Event()
    prior = signal.getsignal(signal.SIGUSR1)
    signal.signal(signal.SIGUSR1, lambda _number, _frame: released.set())
    try:
        print(json.dumps(data, sort_keys=True), flush=True)
        if not released.wait(30):
            raise ValueError("observation acknowledgement deadline")
    finally:
        signal.signal(signal.SIGUSR1, prior)


if __name__ == "__main__":
    raise SystemExit(main())
