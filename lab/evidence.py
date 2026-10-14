"""Closed measured drill reports and inert HTML publication, never cluster secrets. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: SCENARIOS — line 34
# definition: validate — line 48
# parameter: raw — line 48
# variable: report — line 50
# variable: checks — line 74
# variable: names — line 77
# variable: raw_check — line 78
# variable: check — line 79
# variable: proof — line 87
# variable: key — line 90
# variable: value — line 90
# variable: char — line 103
# definition: publish — line 114
# parameter: output — line 114
# parameter: raw — line 114
# variable: report — line 116
# variable: body — line 117
# variable: rows — line 118
# variable: check — line 120
# variable: document — line 122
# END CODE MAP

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from lab.contracts import bounded_tree, digest, integer, record

SCENARIOS = {
    "bootstrap",
    "git_promotion",
    "drift_repair",
    "namespace_rbac",
    "allowed_traffic",
    "blocked_pod_label",
    "blocked_namespace",
    "psa_rejection",
    "failed_release_rollback",
    "git_recovery_commit",
}


def validate(raw: Any) -> dict[str, Any]:
    """Validate complete measured cases and bounded aggregate fingerprints; incomplete suites are rejected."""
    report = record(
        raw,
        {
            "schema",
            "author",
            "synthetic",
            "source_sha",
            "workload_source_sha",
            "built_image_id",
            "cluster",
            "checks",
        },
    )
    integer(report["schema"], 1, 1)
    if (
        report["schema"] != 1
        or report["author"] != "Jason Stys"
        or report["synthetic"] is not True
        or report["cluster"] != "disposable-k3d"
    ):
        raise ValueError("report identity invalid")
    digest(report["source_sha"], 40)
    digest(report["workload_source_sha"], 40)
    digest(report["built_image_id"])
    checks = report["checks"]
    if not isinstance(checks, list) or len(checks) != len(SCENARIOS):
        raise ValueError("complete suite required")
    names: set[str] = set()
    for raw_check in checks:
        check = record(raw_check, {"name", "result", "duration_ms", "evidence"})
        if (
            check["name"] not in SCENARIOS
            or check["name"] in names
            or check["result"] != "PASS"
        ):
            raise ValueError("failed, duplicate or unknown scenario")
        integer(check["duration_ms"], 0, 1_800_000)
        proof = check["evidence"]
        if not isinstance(proof, dict) or not 1 <= len(proof) <= 12:
            raise ValueError("bounded proof required")
        for key, value in proof.items():
            if (
                not isinstance(key, str)
                or not key.isascii()
                or not key.replace("_", "").isalnum()
                or len(key) > 64
            ):
                raise ValueError("proof field invalid")
            if (
                type(value) not in (str, bool, int)
                or isinstance(value, str)
                and (
                    len(value) > 128
                    or any(ord(char) < 32 or ord(char) > 126 for char in value)
                )
            ):
                raise ValueError("proof value invalid")
            if type(value) is int:
                integer(value, 0, 1_800_000)
        names.add(check["name"])
    bounded_tree(report)
    return report


def publish(raw: Any, output: Path) -> None:
    """Publish validated synthetic aggregate JSON/escaped HTML in a new directory, never overwrite."""
    report = validate(raw)
    body = json.dumps(report, sort_keys=True, indent=2, allow_nan=False)
    rows = "".join(
        f"<tr><td>{html.escape(check['name'])}</td><td>PASS</td><td>{check['duration_ms']}</td></tr>"
        for check in report["checks"]
    )
    document = (
        """<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta http-equiv="Content-Security-Policy" content="default-src 'none'; base-uri 'none'; form-action 'none'; object-src 'none'"><title>GitOps Platform Lab — Jason Stys</title><h1>GitOps Platform Lab</h1><p>Created by Jason Stys · github.com/JasonStys · LinkedIn: jason-stys-31b30b351</p><p>Measured synthetic disposable-cluster exercise. Not production authorization or a universal security guarantee.</p><table><caption>Observed checks and duration in milliseconds</caption><tr><th>Scenario</th><th>Result</th><th>Duration</th></tr>"""
        + rows
        + "</table><h2>Aggregate evidence</h2><pre>"
        + html.escape(body)
        + "</pre><p>Help: README and docs/runbook.md. No kubeconfigs, secrets or raw private logs are embedded.</p></html>"
    )
    output.mkdir(parents=True, mode=0o700, exist_ok=False)
    (output / "drill.json").write_text(body + "\n", encoding="utf-8", newline="\n")
    (output / "drill.html").write_text(document, encoding="utf-8", newline="\n")
