"""Fixed synthetic SRE HTTP workload and exact-owned-service connectivity probe. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: TARGET — line 99
# definition: ProbeFailure — line 102
# definition: __init__ — line 105
# parameter: reason — line 105
# parameter: self — line 105
# definition: synthetic — line 120
# variable: events — line 122
# variable: index — line 124
# definition: Server — line 133
# variable: daemon_threads — line 136
# variable: block_on_close — line 137
# variable: allow_reuse_address — line 138
# definition: __init__ — line 140
# parameter: bind — line 140
# parameter: port — line 140
# parameter: self — line 140
# definition: process_request — line 151
# parameter: client_address — line 151
# parameter: request — line 151
# parameter: self — line 151
# definition: process_request_thread — line 162
# parameter: client_address — line 162
# parameter: request — line 162
# parameter: self — line 162
# definition: Handler — line 170
# variable: server — line 173
# definition: setup — line 175
# parameter: self — line 175
# definition: log_message — line 180
# parameter: args — line 180
# parameter: format — line 180
# parameter: self — line 180
# definition: send_error — line 183
# parameter: code — line 184
# parameter: explain — line 184
# parameter: message — line 184
# parameter: self — line 184
# definition: reply — line 189
# parameter: code — line 189
# parameter: data — line 189
# parameter: self — line 189
# variable: body — line 191
# definition: do_GET — line 206
# parameter: self — line 206
# definition: probe — line 216
# parameter: expect — line 216
# variable: opener — line 220
# variable: response — line 222
# variable: outcome — line 230
# variable: reason — line 231
# variable: reason — line 235
# variable: reason — line 237
# variable: reason — line 244
# variable: reason — line 246
# variable: reason — line 250
# variable: outcome — line 251
# variable: outcome — line 253
# variable: reason — line 254
# definition: main — line 263
# variable: parser — line 265
# variable: args — line 269
# variable: server — line 274
# definition: converge — line 288
# parameter: expect — line 288
# variable: attempt — line 290
# variable: observation — line 292
# definition: emit — line 306
# parameter: data — line 306
# parameter: hold — line 306
# variable: released — line 313
# variable: prior — line 314
# parameter: _frame — line 315
# parameter: _number — line 315
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
import time
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
            emit(converge(args.probe), args.hold_observation)
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


def converge(expect: str) -> dict[str, Any]:
    """Disclose bounded new-pod policy onboarding; only eligible blocked positive controls settle, never denials."""
    for attempt in range(1, 7):
        try:
            observation = probe(expect)
        except ProbeFailure as error:
            if (
                expect != "allow"
                or error.reason != "expectation-mismatch"
                or attempt == 6
            ):
                raise
            time.sleep(0.5)
        else:
            return {**observation, "convergence_attempts": attempt}
    raise ValueError("unreachable convergence state")


def emit(data: dict[str, Any], hold: bool) -> None:
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
