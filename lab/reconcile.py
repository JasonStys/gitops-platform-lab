"""Offline desired/observed release review; healthy old pods cannot prove convergence. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: assess — line 65
# parameter: as_of_ms — line 65
# parameter: max_age_ms — line 65
# parameter: raw — line 65
# variable: clock — line 67
# variable: age_limit — line 68
# variable: data — line 69
# variable: captured — line 98
# variable: name — line 100
# variable: name — line 103
# variable: dependencies — line 123
# variable: name — line 126
# variable: ready — line 126
# variable: freshness — line 145
# variable: checks — line 152
# definition: check — line 154
# parameter: expected — line 154
# parameter: name — line 154
# parameter: observed — line 154
# parameter: reason — line 154
# variable: status — line 156
# variable: name — line 200
# variable: observed — line 203
# variable: row — line 211
# variable: statuses — line 211
# variable: row — line 230
# definition: compare — line 235
# parameter: after — line 235
# parameter: as_of_ms — line 235
# parameter: before — line 235
# parameter: max_age_ms — line 235
# variable: new — line 237
# variable: old — line 237
# variable: indexed — line 245
# variable: row — line 245
# variable: current — line 246
# variable: row — line 246
# variable: name — line 254
# definition: publish — line 260
# parameter: output — line 260
# parameter: result — line 260
# variable: absolute — line 262
# variable: part — line 265
# variable: text — line 268
# variable: rows — line 269
# variable: key — line 273
# variable: row — line 276
# variable: page — line 278
# END CODE MAP

from __future__ import annotations

import hashlib
import html
import json
import re
from pathlib import Path
from typing import Any

from lab.contracts import digest, integer, record


def assess(raw: Any, as_of_ms: int, max_age_ms: int) -> dict[str, Any]:
    """Review one bounded declared workload snapshot; missing/stale/failed evidence remains explicit."""
    clock = integer(as_of_ms, 0, 4102444800000)
    age_limit = integer(max_age_ms, 1, 86400000)
    data = record(
        raw,
        {
            "schema",
            "workload",
            "captured_at_ms",
            "desired_sha",
            "source_sha",
            "applied_sha",
            "generation",
            "observed_generation",
            "desired_replicas",
            "ready_replicas",
            "helm_ready",
            "dependencies",
            "transport_required",
            "transport_result",
            "transport_proof_sha256",
        },
    )
    integer(data["schema"], 1, 1)
    if (
        not isinstance(data["workload"], str)
        or re.fullmatch(
            r"[a-z0-9][a-z0-9.-]{0,62}/[a-z0-9][a-z0-9.-]{0,62}", data["workload"]
        )
        is None
    ):
        raise ValueError("namespace/workload identity required")
    captured = integer(data["captured_at_ms"], 0, 4102444800000)
    digest(data["desired_sha"], 40)
    for name in ("source_sha", "applied_sha"):
        if data[name] is not None:
            digest(data[name], 40)
    for name in (
        "generation",
        "observed_generation",
        "desired_replicas",
        "ready_replicas",
    ):
        if data[name] is not None:
            integer(
                data[name],
                0 if "replicas" in name else 1,
                1000000 if "generation" in name else 3,
            )
    if data["generation"] is None or data["desired_replicas"] is None:
        raise ValueError("declared generation and replica expectation required")
    if (
        type(data["transport_required"]) is not bool
        or data["helm_ready"] is not None
        and type(data["helm_ready"]) is not bool
    ):
        raise ValueError("explicit boolean expectations required")
    dependencies = data["dependencies"]
    if not isinstance(dependencies, dict) or len(dependencies) > 20:
        raise ValueError("bounded declared dependency map required")
    for name, ready in dependencies.items():
        if (
            not isinstance(name, str)
            or re.fullmatch(r"[a-z0-9][a-z0-9.-]{0,62}", name) is None
            or ready is not None
            and type(ready) is not bool
        ):
            raise ValueError("invalid dependency observation")
    if data["transport_result"] not in ("PASS", "FAIL", "UNKNOWN", "NOT_REQUIRED"):
        raise ValueError("invalid transport observation")
    if data["transport_proof_sha256"] is not None:
        digest(data["transport_proof_sha256"])
    if (
        data["transport_required"]
        and data["transport_result"] == "NOT_REQUIRED"
        or not data["transport_required"]
        and data["transport_result"] != "NOT_REQUIRED"
    ):
        raise ValueError("transport expectation/observation mismatch")
    freshness = (
        "future_snapshot"
        if captured > clock
        else "stale_snapshot"
        if clock - captured > age_limit
        else None
    )
    checks = []

    def check(name: str, observed: Any, expected: Any, reason: str) -> None:
        """Keep uncertainty separate from observed mismatch; stale snapshots cannot establish current state."""
        status = (
            "UNKNOWN"
            if freshness or observed is None
            else "PASS"
            if observed == expected
            else "FAIL"
        )
        checks.append(
            {
                "check": name,
                "status": status,
                "reason": freshness or "missing_observation"
                if status == "UNKNOWN"
                else "matches_expectation"
                if status == "PASS"
                else reason,
            }
        )

    check(
        "source_revision",
        data["source_sha"],
        data["desired_sha"],
        "source_has_other_revision",
    )
    check(
        "applied_revision",
        data["applied_sha"],
        data["desired_sha"],
        "healthy_previous_revision_is_not_convergence",
    )
    check(
        "observed_generation",
        data["observed_generation"],
        data["generation"],
        "controller_has_not_observed_declared_generation",
    )
    check(
        "ready_replicas",
        data["ready_replicas"],
        data["desired_replicas"],
        "replica_expectation_not_met",
    )
    check("helm_ready", data["helm_ready"], True, "helm_not_ready")
    for name in sorted(dependencies):
        check("dependency:" + name, dependencies[name], True, "dependency_not_ready")
    if data["transport_required"]:
        observed = (
            None
            if data["transport_result"] == "UNKNOWN"
            or data["transport_result"] == "PASS"
            and data["transport_proof_sha256"] is None
            else data["transport_result"]
        )
        check("transport_evidence", observed, "PASS", "transport_control_failed")
    statuses = {row["status"] for row in checks}
    return {
        "schema": 1,
        "kind": "declared_reconciliation_review",
        "author": "Jason Stys",
        "workload": data["workload"],
        "snapshot_sha256": hashlib.sha256(
            json.dumps(data, sort_keys=True, separators=(",", ":")).encode()
        ).hexdigest(),
        "captured_at_ms": captured,
        "as_of_ms": clock,
        "max_age_ms": age_limit,
        "desired_sha": data["desired_sha"],
        "checks": checks,
        "verdict": "NEEDS_REVIEW"
        if "FAIL" in statuses
        else "INSUFFICIENT_EVIDENCE"
        if "UNKNOWN" in statuses
        else "RECONCILED_ASSERTED",
        "review_queue": [row for row in checks if row["status"] != "PASS"],
        "scope": "Normalized supplied observations, not authenticated cluster acquisition. No cluster access, apply or enforcement. A proof hash is a reference, not a verified network verdict.",
    }


def compare(before: Any, after: Any, as_of_ms: int, max_age_ms: int) -> dict[str, Any]:
    """Compare same-workload chronological observations without confusing old availability with resolved intent."""
    old, new = assess(before, as_of_ms, max_age_ms), assess(after, as_of_ms, max_age_ms)
    if (
        old["workload"] != new["workload"]
        or old["captured_at_ms"] > new["captured_at_ms"]
    ):
        raise ValueError(
            "comparison needs same workload and chronological observations"
        )
    indexed = {row["check"]: row["status"] for row in old["checks"]}
    current = {row["check"]: row["status"] for row in new["checks"]}
    return {
        **new,
        "before_snapshot_sha256": old["snapshot_sha256"],
        "before_verdict": old["verdict"],
        "intent_changed": old["desired_sha"] != new["desired_sha"],
        "transitions": [
            {"check": name, "before": indexed.get(name), "after": current.get(name)}
            for name in sorted(indexed.keys() | current.keys())
            if indexed.get(name) != current.get(name)
        ],
    }


def publish(result: dict[str, Any], output: Path) -> None:
    """Preserve new review evidence in private JSON/inert HTML without overwriting prior files."""
    absolute = output.absolute()
    if any(
        part.is_symlink() or part.is_junction()
        for part in (absolute, *absolute.parents)
    ):
        raise ValueError("linked output refused")
    text = json.dumps(result, sort_keys=True, indent=2)
    rows = "".join(
        "<tr>"
        + "".join(
            f"<td>{html.escape(str(row[key]))}</td>"
            for key in ("check", "status", "reason")
        )
        + "</tr>"
        for row in result["checks"]
    )
    page = (
        '<!doctype html><html lang="en"><meta charset="utf-8"><meta http-equiv="Content-Security-Policy" content="default-src \'none\'; base-uri \'none\'; form-action \'none\'"><title>Reconciliation review — Jason Stys</title><main><h1>Desired and observed release review</h1><p>Created by Jason Stys. Supplied observations; not authenticated cluster acquisition.</p><table><caption>Currentness, readiness and dependencies</caption><tr><th>Check</th><th>Status</th><th>Reason</th></tr>'
        + rows
        + "</table><details><summary>Full review and transitions</summary><pre>"
        + html.escape(text)
        + "</pre></details></main></html>"
    )
    absolute.mkdir(mode=0o700)
    (absolute / "reconciliation.json").write_text(text + "\n", encoding="utf-8")
    (absolute / "reconciliation.html").write_text(page, encoding="utf-8")
