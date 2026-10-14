"""Incomplete/false success, fingerprint, report-escaping and CLI privacy regression tests. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: test_report_boundaries — line 67
# parameter: case — line 67
# parameter: evidence — line 67
# variable: proof — line 88
# definition: test_render_and_cli — line 101
# parameter: evidence — line 101
# parameter: tmp_path — line 101
# variable: output — line 106
# variable: rendered — line 108
# variable: source — line 113
# variable: valid — line 115
# variable: invalid — line 131
# definition: test_policy_cli — line 151
# parameter: documents — line 151
# parameter: tmp_path — line 151
# variable: source — line 155
# variable: result — line 157
# variable: denied — line 165
# variable: malformed — line 173
# definition: test_cli_in_process — line 182
# parameter: documents — line 183
# parameter: evidence — line 184
# parameter: tmp_path — line 185
# parameter: monkeypatch — line 186
# variable: source — line 191
# END CODE MAP

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import pytest

from lab.__main__ import main
from lab.evidence import publish, validate


@pytest.mark.parametrize(
    "case",
    [
        "schema",
        "author",
        "synthetic",
        "cluster",
        "sha",
        "missing",
        "duplicate",
        "failed",
        "negative-time",
        "bool-time",
        "unknown",
        "extra",
        "empty-proof",
        "proof-array",
        "long-proof",
        "private-newline",
        "bad-key",
        "negative-int",
    ],
)
def test_report_boundaries(evidence: dict[str, Any], case: str) -> None:
    """Only a complete closed PASS suite can render; unsupported private/raw fields cannot slip in."""
    if case in {"schema", "author", "synthetic", "cluster"}:
        evidence[case] = "invalid"
    elif case == "sha":
        evidence["source_sha"] = "0" * 40
    elif case == "missing":
        evidence["checks"].pop()
    elif case == "duplicate":
        evidence["checks"][0] = evidence["checks"][1]
    elif case == "failed":
        evidence["checks"][0]["result"] = "FAIL"
    elif case == "negative-time":
        evidence["checks"][0]["duration_ms"] = -1
    elif case == "bool-time":
        evidence["checks"][0]["duration_ms"] = True
    elif case == "unknown":
        evidence["checks"][0]["name"] = "fabricated"
    elif case == "extra":
        evidence["secret"] = "private"
    else:
        proof = {
            "empty-proof": {},
            "proof-array": [],
            "long-proof": {"x": "x" * 129},
            "private-newline": {"x": "private\n"},
            "bad-key": {"!": "x"},
            "negative-int": {"x": -1},
        }[case]
        evidence["checks"][0]["evidence"] = proof
    with pytest.raises(ValueError):
        validate(evidence)


def test_render_and_cli(evidence: dict[str, Any], tmp_path: Path) -> None:
    """Escape allowed printable strings, refuse replacing prior reports, and never display invalid raw values."""
    evidence["checks"][0]["evidence"] = {
        "test_fixture": "<script>not executable</script>"
    }
    output = tmp_path / "report"
    publish(evidence, output)
    rendered = (output / "drill.html").read_text(encoding="utf-8")
    assert "&lt;script&gt;" in rendered and "<script>" not in rendered
    assert "default-src 'none'" in rendered and "Jason Stys" in rendered
    with pytest.raises(FileExistsError):
        publish(evidence, output)
    source = tmp_path / "report.json"
    source.write_text(json.dumps(evidence), encoding="utf-8")
    valid = subprocess.run(
        [
            sys.executable,
            "-m",
            "lab",
            "report",
            str(source),
            "--output",
            str(tmp_path / "cli"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert valid.returncode == 0
    source.write_text('{"secret":"private-input-123"}', encoding="utf-8")
    invalid = subprocess.run(
        [
            sys.executable,
            "-m",
            "lab",
            "report",
            str(source),
            "--output",
            str(tmp_path / "bad"),
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert (
        invalid.returncode == 2
        and "private-input-123" not in invalid.stdout + invalid.stderr
    )


def test_policy_cli(documents: list[dict[str, Any]], tmp_path: Path) -> None:
    """Native CLI exits ALLOW=0/DENY=1 for actual manifests; malformed/unreadable input is 2."""
    import yaml

    source = tmp_path / "rendered.yml"
    source.write_text(yaml.safe_dump_all(documents), encoding="utf-8")
    result = subprocess.run(
        [sys.executable, "-m", "lab", "audit", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0 and json.loads(result.stdout)["decision"] == "ALLOW"
    source.write_text("kind: Secret\nmetadata: {name: private}", encoding="utf-8")
    denied = subprocess.run(
        [sys.executable, "-m", "lab", "audit", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert denied.returncode == 1 and "private" not in denied.stdout
    source.write_text("x: [", encoding="utf-8")
    malformed = subprocess.run(
        [sys.executable, "-m", "lab", "audit", str(source)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert malformed.returncode == 2


def test_cli_in_process(
    documents: list[dict[str, Any]],
    evidence: dict[str, Any],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Instrument the same CLI branches directly, in addition to the actual subprocess invocations."""
    import yaml

    source = tmp_path / "source.yml"
    source.write_text(yaml.safe_dump_all(documents), encoding="utf-8")
    monkeypatch.setattr(sys, "argv", ["lab", "audit", str(source)])
    assert main() == 0
    source.write_text("kind: Secret", encoding="utf-8")
    assert main() == 1
    source.write_text("x: [", encoding="utf-8")
    assert main() == 2
    source.write_text(json.dumps(evidence), encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["lab", "report", str(source), "--output", str(tmp_path / "direct")],
    )
    assert main() == 0
