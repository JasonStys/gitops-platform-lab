"""Real clone/fetch proof for isolated read-only smart HTTP Git; endpoints never accept pushes. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: command — line 36
# parameter: args — line 36
# parameter: cwd — line 36
# definition: test_real_git_clone_and_endpoint_denials — line 43
# parameter: tmp_path — line 43
# variable: bare — line 45
# variable: work — line 47
# variable: expected — line 55
# variable: server — line 58
# variable: thread — line 59
# variable: target — line 62
# variable: clone — line 63
# variable: body — line 79
# variable: headers — line 79
# variable: method — line 79
# variable: path — line 79
# variable: status — line 79
# variable: connection — line 99
# variable: response — line 103
# END CODE MAP

from __future__ import annotations

import http.client
import subprocess
import threading
from pathlib import Path

import pytest

from scripts.git_server import GitServer


def command(args: list[str], cwd: Path) -> str:
    """Execute fixed synthetic Git fixture argv, with no shell, credentials or production repository."""
    return subprocess.check_output(
        ["git", *args], cwd=cwd, stderr=subprocess.DEVNULL, text=True, timeout=15
    ).strip()


def test_real_git_clone_and_endpoint_denials(tmp_path: Path) -> None:
    """Real Git speaks smart HTTP v2 and clones the expected commit; traversal/write/malformed bodies fail."""
    bare = tmp_path / "repo.git"
    command(["init", "--bare", str(bare)], tmp_path)
    work = tmp_path / "source"
    work.mkdir()
    command(["init", "-b", "main"], work)
    command(["config", "user.name", "Synthetic Test"], work)
    command(["config", "user.email", "test@example.invalid"], work)
    (work / "data.txt").write_text("fictional test data", encoding="utf-8")
    command(["add", "."], work)
    command(["commit", "-m", "Synthetic fixture"], work)
    expected = command(["rev-parse", "HEAD"], work)
    command(["remote", "add", "origin", str(bare)], work)
    command(["push", "origin", "main"], work)
    server = GitServer(tmp_path, "127.0.0.1", 0)
    thread = threading.Thread(target=server.serve_forever)
    thread.start()
    try:
        target = f"http://127.0.0.1:{server.server_port}/repo.git"
        clone = tmp_path / "clone"
        command(
            [
                "-c",
                "http.proxy=",
                "clone",
                "--depth",
                "1",
                "--branch",
                "main",
                target,
                str(clone),
            ],
            tmp_path,
        )
        assert command(["rev-parse", "HEAD"], clone) == expected
        for method, path, body, headers, status in (
            ("GET", "/repo.git/info/refs?service=git-receive-pack", None, {}, 403),
            ("POST", "/repo.git/git-receive-pack", b"no", {}, 403),
            ("GET", "/../private", None, {}, 403),
            ("GET", "/repo.git/info/refs?service=git-upload-pack", b"no", {}, 400),
            (
                "POST",
                "/repo.git/git-upload-pack",
                b"no",
                {"Content-Type": "wrong"},
                400,
            ),
            (
                "POST",
                "/repo.git/git-upload-pack",
                b"no",
                {"Transfer-Encoding": "chunked"},
                400,
            ),
        ):
            connection = http.client.HTTPConnection(
                "127.0.0.1", server.server_port, timeout=3
            )
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            assert response.status == status and response.read() == b""
            connection.close()
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=3)
    assert not thread.is_alive()
    with pytest.raises(ValueError):
        GitServer(tmp_path, "8.8.8.8", 0)
    with pytest.raises(ValueError):
        GitServer(tmp_path / "missing", "127.0.0.1", 0)
