"""Real loopback HTTP, route privacy, bounded server and provisional transport/acknowledgement tests. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: test_real_http — line 55
# variable: server — line 57
# variable: thread — line 58
# variable: path — line 61
# variable: status — line 61
# variable: connection — line 67
# variable: response — line 71
# variable: body — line 72
# variable: connection — line 78
# variable: response — line 82
# definition: test_bind_contract — line 96
# parameter: bind — line 96
# parameter: port — line 96
# definition: test_slots_and_disconnected_peer — line 102
# variable: server — line 104
# variable: _ — line 105
# variable: shutdown — line 106
# variable: _ — line 109
# variable: _ — line 116
# variable: _ — line 117
# variable: handler — line 119
# definition: test_timeout_is_provisional — line 131
# parameter: failure — line 131
# definition: test_probe_non_timeout_and_response — line 139
# variable: response — line 146
# definition: test_main_and_analyzer — line 167
# definition: test_safe_transport_diagnostics — line 186
# parameter: error — line 186
# parameter: reason — line 186
# variable: failure — line 194
# variable: server — line 211
# definition: test_observation_receipt — line 216
# parameter: monkeypatch — line 216
# variable: registration — line 223
# variable: gate — line 224
# END CODE MAP

from __future__ import annotations

import errno
import http.client
import json
import socket
import threading
import urllib.error
from unittest.mock import Mock, patch

import pytest

from workload.server import Handler, ProbeFailure, Server, emit, main, probe, synthetic


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
def test_timeout_is_provisional(failure: Exception) -> None:
    """Timeout is a provisional observation, not a policy verdict; the host oracle supplies counters/controls."""
    with patch("urllib.request.OpenerDirector.open", side_effect=failure):
        assert probe("deny") == {"outcome": "blocked", "reason": "timeout"}
        with pytest.raises(ValueError):
            probe("allow")


def test_probe_non_timeout_and_response() -> None:
    """Refusal is only a provisional observation, while invalid HTTP/DNS responses remain failures."""
    with patch(
        "urllib.request.OpenerDirector.open",
        side_effect=urllib.error.URLError(ConnectionRefusedError()),
    ):
        assert probe("deny") == {"outcome": "blocked", "reason": "connection-refused"}
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


@pytest.mark.parametrize(
    ("error", "reason"),
    [
        (socket.gaierror(), "dns-failure"),
        (ConnectionRefusedError(), "connection-refused"),
        (OSError(errno.EHOSTUNREACH, "private message"), "network-unreachable"),
        (OSError(123, "private message"), "transport-error"),
    ],
)
def test_safe_transport_diagnostics(error: Exception, reason: str) -> None:
    """Classify actual failures without treating them as a timeout or disclosing exception contents."""
    with patch(
        "urllib.request.OpenerDirector.open", side_effect=urllib.error.URLError(error)
    ):
        if reason in {"connection-refused", "network-unreachable"}:
            assert probe("deny") == {"outcome": "blocked", "reason": reason}
        else:
            with pytest.raises(ProbeFailure) as failure:
                probe("deny")
            assert failure.value.reason == reason and "private" not in str(
                failure.value
            )
    with (
        patch("sys.argv", ["server", "--probe", "deny"]),
        patch("workload.server.probe", side_effect=ProbeFailure(reason)),
    ):
        assert main() == 1
    with pytest.raises(ValueError):
        ProbeFailure("private unapproved text")
    with (
        patch("sys.argv", ["server", "--probe", "deny"]),
        patch("workload.server.probe", side_effect=ValueError),
    ):
        assert main() == 1
    with patch("sys.argv", ["server"]), patch("workload.server.Server") as server:
        server.return_value.__enter__.return_value.serve_forever.return_value = None
        assert main() == 0


def test_observation_receipt(monkeypatch: pytest.MonkeyPatch) -> None:
    """Observation registers a fixed acknowledgement handler before flushing, times out and restores it."""
    import signal

    monkeypatch.setattr(signal, "SIGUSR1", 10, raising=False)
    with (
        patch("signal.getsignal", return_value=signal.SIG_DFL),
        patch("signal.signal") as registration,
        patch("threading.Event") as gate,
    ):
        gate.return_value.wait.return_value = True
        emit({"outcome": "test-fixture"}, True)
        assert registration.call_count == 2
        gate.return_value.wait.assert_called_once_with(30)
        gate.return_value.wait.return_value = False
        with pytest.raises(ValueError):
            emit({"outcome": "test-fixture"}, True)
    monkeypatch.delattr(signal, "SIGUSR1")
    with pytest.raises(ValueError):
        emit({"outcome": "test-fixture"}, True)
