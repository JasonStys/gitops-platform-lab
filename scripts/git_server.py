"""Read-only bounded smart HTTP Git service for owned synthetic CI repositories. Created by Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: CAP — line 71
# definition: GitServer — line 74
# variable: daemon_threads — line 77
# variable: block_on_close — line 78
# variable: allow_reuse_address — line 79
# definition: __init__ — line 81
# parameter: bind — line 81
# parameter: port — line 81
# parameter: root — line 81
# parameter: self — line 81
# definition: process_request — line 92
# parameter: client_address — line 92
# parameter: request — line 92
# parameter: self — line 92
# definition: process_request_thread — line 103
# parameter: client_address — line 103
# parameter: request — line 103
# parameter: self — line 103
# definition: GitHandler — line 111
# variable: server — line 114
# definition: setup — line 116
# parameter: self — line 116
# definition: log_message — line 121
# parameter: args — line 121
# parameter: format — line 121
# parameter: self — line 121
# definition: send_error — line 124
# parameter: code — line 125
# parameter: explain — line 125
# parameter: message — line 125
# parameter: self — line 125
# definition: do_GET — line 132
# parameter: self — line 132
# definition: do_POST — line 136
# parameter: self — line 136
# definition: backend — line 140
# parameter: method — line 140
# parameter: self — line 140
# variable: parts — line 142
# variable: lengths — line 158
# variable: size — line 161
# variable: body — line 170
# variable: environment — line 173
# variable: key — line 175
# variable: value — line 175
# variable: result — line 190
# variable: headers — line 200
# variable: payload — line 200
# variable: entries — line 201
# variable: line — line 202
# definition: main — line 222
# variable: parser — line 224
# variable: args — line 228
# variable: server — line 229
# END CODE MAP

from __future__ import annotations

import argparse
import ipaddress
import os
import subprocess
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

CAP = 1024 * 1024


class GitServer(ThreadingHTTPServer):
    """Private-address server limited to eight requests; no receive-pack or directory listing route."""

    daemon_threads = False
    block_on_close = True
    allow_reuse_address = False

    def __init__(self, root: Path, bind: str, port: int) -> None:
        """Require an owned explicit repo.git directory and private IP, not an external bind."""
        if (
            not ipaddress.ip_address(bind).is_private
            or not (root / "repo.git/HEAD").is_file()
        ):
            raise ValueError("owned repository/private bind required")
        self.root = root.resolve()
        self.slots = threading.BoundedSemaphore(8)
        super().__init__((bind, port), GitHandler)

    def process_request(self, request: Any, client_address: Any) -> None:
        """Refuse excess connections rather than allocating unlimited threads."""
        if not self.slots.acquire(blocking=False):
            self.shutdown_request(request)
            return
        try:
            super().process_request(request, client_address)
        except BaseException:
            self.slots.release()
            raise

    def process_request_thread(self, request: Any, client_address: Any) -> None:
        """Release the request slot even if the CGI backend/parser fails."""
        try:
            super().process_request_thread(request, client_address)
        finally:
            self.slots.release()


class GitHandler(BaseHTTPRequestHandler):
    """Only exact clone/fetch endpoints are allowed; Git's own HTTP backend handles Git packets."""

    server: GitServer

    def setup(self) -> None:
        """Bound socket lifetime before reading client headers or body."""
        self.request.settimeout(5)
        super().setup()

    def log_message(self, format: str, *args: Any) -> None:
        """Never log raw headers, URLs, queries or request bodies."""

    def send_error(
        self, code: int, message: str | None = None, explain: str | None = None
    ) -> None:
        """Return a fixed error rather than reflecting request/parser information."""
        self.send_response(code)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_GET(self) -> None:
        """Permit only read-only smart HTTP discovery for repo.git."""
        self.backend("GET")

    def do_POST(self) -> None:
        """Permit only bounded upload-pack fetch packets; receive-pack writes are unreachable."""
        self.backend("POST")

    def backend(self, method: str) -> None:
        """Run fixed Git argv and CGI paths; content is never interpreted as a shell command."""
        parts = urlsplit(self.path)
        if (
            method == "GET"
            and (
                parts.path != "/repo.git/info/refs"
                or parts.query != "service=git-upload-pack"
            )
        ) or (
            method == "POST"
            and (parts.path != "/repo.git/git-upload-pack" or parts.query)
        ):
            self.send_error(403)
            return
        try:
            if self.headers.get("Transfer-Encoding"):
                raise ValueError("chunked input not accepted")
            lengths = self.headers.get_all("Content-Length", [])
            if len(lengths) > 1:
                raise ValueError("duplicate length")
            size = int(lengths[0]) if lengths else 0
            if not 0 <= size <= CAP or method == "GET" and size != 0:
                raise ValueError("invalid body size")
            if (
                method == "POST"
                and self.headers.get("Content-Type")
                != "application/x-git-upload-pack-request"
            ):
                raise ValueError("invalid content type")
            body = self.rfile.read(size)
            if len(body) != size:
                raise ValueError("truncated body")
            environment = {
                key: value
                for key, value in os.environ.items()
                if not key.startswith("GIT_")
            }
            environment.update(
                GIT_PROJECT_ROOT=str(self.server.root),
                GIT_HTTP_EXPORT_ALL="1",
                PATH_INFO=parts.path,
                REQUEST_METHOD=method,
                QUERY_STRING="service=git-upload-pack" if method == "GET" else "",
                CONTENT_TYPE="application/x-git-upload-pack-request",
                CONTENT_LENGTH=str(size),
                REMOTE_ADDR="127.0.0.1",
            )
            if self.headers.get("Git-Protocol") == "version=2":
                environment["HTTP_GIT_PROTOCOL"] = "version=2"
            result = subprocess.run(
                ["git", "http-backend"],
                input=body,
                env=environment,
                capture_output=True,
                timeout=15,
                check=True,
            )
            if len(result.stdout) > 8 * CAP:
                raise ValueError("backend output exceeds bound")
            headers, payload = result.stdout.split(b"\r\n\r\n", 1)
            entries = dict(
                line.decode("ascii").split(": ", 1) for line in headers.split(b"\r\n")
            )
            if "Status" in entries:
                raise ValueError("backend status failed")
            self.send_response(200)
            self.send_header("Content-Type", entries["Content-Type"])
            self.send_header("Content-Length", str(len(payload)))
            self.send_header("Cache-Control", "no-store")
            self.end_headers()
            self.wfile.write(payload)
        except (
            ValueError,
            OSError,
            subprocess.SubprocessError,
            UnicodeError,
            KeyError,
        ):
            self.send_error(400)


def main() -> int:
    """Run with explicit repository/private address; no external credential or push endpoint is offered."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--bind", required=True)
    parser.add_argument("--port", type=int, default=9418)
    args = parser.parse_args()
    with GitServer(args.root, args.bind, args.port) as server:
        server.serve_forever()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
