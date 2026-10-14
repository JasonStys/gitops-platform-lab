"""Real loopback HTTP, fixed-route privacy, bounded server and positive/timeout-only probe tests. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: test_real_http — line 45
# variable: server — line 47
# variable: thread — line 48
# variable: path — line 51
# variable: status — line 51
# variable: connection — line 57
# variable: response — line 61
# variable: body — line 62
# variable: connection — line 68
# variable: response — line 72
# definition: test_bind_contract — line 86
# parameter: bind — line 86
# parameter: port — line 86
# definition: test_slots_and_disconnected_peer — line 92
# variable: server — line 94
# variable: _ — line 95
# variable: shutdown — line 96
# variable: _ — line 99
# variable: _ — line 106
# variable: _ — line 107
# variable: handler — line 109
# definition: test_denial_is_timeout_only — line 121
# parameter: failure — line 121
# definition: test_probe_non_timeout_and_response — line 129
# variable: response — line 137
# definition: test_main_and_analyzer — line 158
# variable: server — line 171
# END CODE MAP

from __future__ import annotations

import http.client
import json
import threading
import urllib.error
from unittest.mock import Mock, patch

import pytest

from workload.server import Handler, Server, main, probe, synthetic


def test_real_http() -> None:
    """Serve actual native HTTP; verify health, inherited analyzer, private query rejection and method errors."""
    server = Server("127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        for path, status in (
            ("/health", 200),
            ("/work", 200),
            ("/missing", 404),
            ("/health?private-input", 404),
        ):
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_port, timeout=2
            )
            connection.request("GET", path)
            response = connection.getresponse()
            body = response.read()
            assert response.status == status and "private-input" not in body.decode()
            assert response.getheader("X-Content-Type-Options") == "nosniff"
            if path == "/work":
                assert json.loads(body)["analysis"]["availability"]["requests"] == 40
            connection.close()
        connection = http.client.HTTPConnection(
            "127.0.0.1", server.server_port, timeout=2
        )
        connection.request("POST", "/private-method", body=b"private-body")
        response = connection.getresponse()
        assert response.status == 501 and b"private" not in response.read()
        connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    assert not thread.is_alive()


@pytest.mark.parametrize(
    ("bind", "port"),
    [("8.8.8.8", 80), ("127.0.0.1", True), ("0.0.0.0", 65536), ("127.0.0.1", -1)],
)
def test_bind_contract(bind: str, port: int) -> None:
    """A user-supplied arbitrary interface/invalid port cannot expand the server's fixed bind contract."""
    with pytest.raises(ValueError):
        Server(bind, port)


def test_slots_and_disconnected_peer() -> None:
    """Excess connections are refused; thread startup errors release slots, and peer disconnects stay silent."""
    with Server("127.0.0.1", 0) as server:
        assert all(server.slots.acquire(False) for _ in range(8))
        with patch.object(server, "shutdown_request") as shutdown:
            server.process_request(Mock(), ("127.0.0.1", 1))
            shutdown.assert_called_once()
        for _ in range(8):
            server.slots.release()
        with patch(
            "http.server.ThreadingHTTPServer.process_request", side_effect=OSError
        ):
            with pytest.raises(OSError):
                server.process_request(Mock(), ("127.0.0.1", 1))
        assert all(server.slots.acquire(False) for _ in range(8))
        for _ in range(8):
            server.slots.release()
    handler = object.__new__(Handler)
    handler.wfile = Mock()
    handler.wfile.write.side_effect = BrokenPipeError
    handler.send_response = Mock()
    handler.send_header = Mock()
    handler.end_headers = Mock()
    handler.reply(200, {"status": "ok"})


@pytest.mark.parametrize(
    "failure", [TimeoutError(), urllib.error.URLError(TimeoutError())]
)
def test_denial_is_timeout_only(failure: Exception) -> None:
    """Only an actual socket timeout qualifies as a blocked observation; success fails a deny expectation."""
    with patch("urllib.request.OpenerDirector.open", side_effect=failure):
        assert probe("deny") == {"outcome": "blocked", "reason": "timeout"}
        with pytest.raises(ValueError):
            probe("allow")


def test_probe_non_timeout_and_response() -> None:
    """DNS/refused/invalid body/HTTP status failures are not counted as network policy enforcement."""
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=urllib.error.URLError(ConnectionRefusedError()),
    ):
        with pytest.raises(ValueError):
            probe("deny")
    response = Mock()
    response.__enter__ = Mock(return_value=response)
    response.__exit__ = Mock(return_value=False)
    response.status = 200
    response.read.return_value = (
        b'{"author": "Jason Stys", "status": "ok", "synthetic": true}'
    )
    with patch("urllib.request.OpenerDirector.open", return_value=response):
        assert probe("allow")["outcome"] == "allowed"
        with pytest.raises(ValueError):
            probe("deny")
        response.read.return_value = b"wrong body"
        with pytest.raises(ValueError):
            probe("allow")
        response.status = 503
        with pytest.raises(ValueError):
            probe("allow")
    with pytest.raises(ValueError):
        probe("any-target")


def test_main_and_analyzer() -> None:
    """Use a real deterministic inherited analyzer and test both CLI modes without starting an external bind."""
    assert synthetic()["analysis"]["availability"]["bad"] == 0
    with (
        patch("sys.argv", ["server", "--probe", "allow"]),
        patch("workload.server.probe", return_value={"outcome": "allowed"}),
    ):
        assert main() == 0
    with (
        patch("sys.argv", ["server", "--probe", "deny"]),
        patch("workload.server.probe", side_effect=ValueError),
    ):
        assert main() == 1
    with patch("sys.argv", ["server"]), patch("workload.server.Server") as server:
        server.return_value.__enter__.return_value.serve_forever.return_value = None
        assert main() == 0
