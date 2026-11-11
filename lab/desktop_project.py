"""Practical offline manifest and reconciliation review using original closed GitOps engines. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 97
# variable: PRODUCT — line 98
# variable: PROFILE — line 98
# variable: TITLE — line 99
# variable: VERSION — line 99
# variable: BANNER — line 100
# variable: COLUMNS — line 103
# variable: RESOURCES — line 109
# variable: RESOURCE_LIMITS — line 118
# variable: MODES — line 119
# variable: REVIEW_MODE — line 125
# variable: CHOICES — line 126
# variable: FIELDS — line 140
# variable: ACTIVE_FIELDS — line 149
# variable: SCENARIOS — line 155
# variable: HELP — line 167
# definition: scenario — line 172
# parameter: name — line 172
# definition: integer_control — line 188
# parameter: high — line 188
# parameter: low — line 188
# parameter: value — line 188
# variable: number — line 192
# definition: prepared — line 198
# parameter: name — line 198
# variable: data — line 203
# variable: deployment — line 205
# variable: row — line 205
# variable: data — line 210
# variable: before — line 213
# variable: data — line 215
# variable: before — line 219
# variable: before — line 229
# definition: analyze — line 240
# parameter: parameters — line 241
# parameter: stage — line 241
# parameter: state — line 241
# variable: mode — line 244
# variable: raw_hash — line 247
# variable: before — line 248
# variable: exercise — line 250
# variable: before — line 251
# variable: data — line 251
# variable: manifest — line 252
# variable: manifest — line 254
# variable: raw — line 255
# variable: raw_hash — line 259
# variable: data — line 261
# variable: before — line 269
# variable: scope — line 272
# variable: row — line 283
# variable: result — line 288
# variable: files — line 293
# variable: original — line 299
# variable: clock_text — line 302
# variable: clock — line 303
# variable: age — line 308
# variable: original_review — line 309
# variable: wanted — line 310
# variable: result — line 315
# variable: files — line 332
# variable: path — line 334
# definition: views — line 344
# parameter: files — line 344
# variable: scope — line 346
# variable: result — line 348
# variable: name — line 352
# variable: result — line 356
# variable: row — line 359
# variable: row — line 362
# variable: row — line 365
# definition: cells — line 371
# parameter: row — line 371
# variable: kind — line 373
# END CODE MAP

from __future__ import annotations

import copy
import hashlib
import sys
import time
from pathlib import Path
from typing import Any

import yaml

from . import reconcile
from .contracts import json_bytes, yaml_bytes
from .desktop_io import Rejected, canonical, json_value
from .desktop_state import Workspace
from .inputs import read_source
from .policy import audit

ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parents[1]))
PRODUCT, PROFILE = "gitops-platform-lab", "GitOpsPlatformLab"
TITLE, VERSION = "GitOps Reconciliation Workbench", "1.1.0"
BANNER = (
    "Offline declared observations only: no cluster access, apply or live enforcement."
)
COLUMNS = (
    "Resource / expectation",
    "Before / observation",
    "Current / reason",
    "Decision / status",
)
RESOURCES = (
    "examples/rendered.json",
    "examples/reconciliation-pending.json",
    "examples/reconciliation-recovered.json",
    "notices.txt",
    "app.ico",
    "python314.dll",
    "yaml/_yaml.cp314-win_amd64.pyd",
)
RESOURCE_LIMITS: dict[str, int] = {}
MODES = (
    "Audit authorized rendered manifests",
    "Assess authorized workload snapshot",
    "Compare authorized workload observations",
    "Review prepared offline exercise",
)
REVIEW_MODE = None
CHOICES = {
    "exercise": (
        "rendered-allow",
        "rendered-deny",
        "pending",
        "recovered",
        "comparison",
        "missing-proof",
        "stale",
        "failed-dependency",
        "new-intent",
        "transport-not-required",
    )
}
FIELDS = (
    ("manifest", "Authorized rendered JSON / multi-document YAML", "file"),
    ("snapshot", "Authorized current closed snapshot JSON", "file"),
    ("before", "Authorized prior same-workload snapshot JSON", "file"),
    ("as_of_ms", "Review clock: UTC epoch milliseconds (blank = now)", "text"),
    ("max_age_ms", "Maximum snapshot age, 1–86400000 ms", "text"),
    ("desired_sha", "Optional new desired revision: full source SHA", "text"),
    ("exercise", "Prepared full-app exercise", "choice"),
)
ACTIVE_FIELDS = {
    MODES[0]: ("manifest",),
    MODES[1]: ("snapshot", "as_of_ms", "max_age_ms", "desired_sha"),
    MODES[2]: ("snapshot", "before", "as_of_ms", "max_age_ms", "desired_sha"),
    MODES[3]: ("exercise", "as_of_ms", "max_age_ms", "desired_sha"),
}
SCENARIOS = (
    "Original closed five-resource rendered policy",
    "Forbidden privilege escalation remains denied",
    "Healthy old pods do not establish new intent",
    "Matching current revision and generation",
    "Before/after genuine declared reconciliation",
    "Missing transport proof stays unknown",
    "Stale observation stays inconclusive",
    "Failed identity dependency needs review",
    "New desired intent stays separate from readiness",
    "Explicitly unnecessary transport requirement",
)
HELP = """Audit the original closed five-resource platform-lab chart using an authorized rendered JSON array or multi-document YAML. The original policy checks exact resource inventory, namespace, pod identity, non-root/read-only/capability limits, readiness/liveness, replicas and AND-combined ingress selectors. ALLOW is a static closed-policy decision, not live network enforcement. Unknown resources/fields remain denied; this is not a general Kubernetes scanner or arbitrary Rego/plugin runner.
Assess or compare supplied closed workload snapshots. Enter an explicit UTC epoch-millisecond as-of clock and age limit; blank clock means current time. Prepared examples visibly set their synthetic clock. Optional new desired SHA changes only the CURRENT declaration and is recorded separately with original/effective hashes. Healthy old pods cannot clear new Git intent; missing revisions/generation/dependencies/required proof and stale/future observations stay UNKNOWN. Same-workload chronological comparison retains before evidence and explicit intent_changed. A proof hash is a reference, not authenticated cluster acquisition or a verified transport verdict.
No kubectl, Helm, Flux, Docker, cluster, credentials, network listener, apply, live collector or enforcement is started. Original real cluster/Helm CI drills remain separate mandatory gates. Prepared examples exercise the same actual offline engines, not fake cluster responses. Review checks, queues, transitions, full detail, search/filter and exact no-overwrite export. Saved reports/paths are sensitive owner-local plaintext, not encryption or multiuser authentication. Exit retains worker/profile ownership until completion."""


def scenario(name: str) -> dict[str, str]:
    """Populate ordinary controls with an explicit synthetic clock; selection alone never runs a review."""
    if name not in SCENARIOS:
        raise Rejected("unknown prepared GitOps exercise")
    return {
        "mode": MODES[3],
        "manifest": "",
        "snapshot": "",
        "before": "",
        "as_of_ms": "1000100",
        "max_age_ms": "300000",
        "desired_sha": "",
        "exercise": CHOICES["exercise"][SCENARIOS.index(name)],
    }


def integer_control(value: str, low: int, high: int) -> int:
    """Reject ambiguous/nondecimal controls before the original engine validates clock semantics."""
    if not value.isascii() or not value.isdecimal() or len(value) > 16:
        raise Rejected("enter a bounded decimal clock/age")
    number = int(value)
    if not low <= number <= high:
        raise Rejected("clock/age outside supported bounds")
    return number


def prepared(name: str) -> tuple[Any, Any | None]:
    """Return independent inert original-format inputs, never fabricate a live cluster result."""
    if name not in CHOICES["exercise"]:
        raise Rejected("unknown prepared GitOps exercise")
    if name.startswith("rendered-"):
        data = json_bytes(read_source(ROOT / "examples/rendered.json", 1024 * 1024))
        if name == "rendered-deny":
            deployment = next(row for row in data if row["kind"] == "Deployment")
            deployment["spec"]["template"]["spec"]["containers"][0]["securityContext"][
                "allowPrivilegeEscalation"
            ] = True
        return data, None
    data = json_bytes(
        read_source(ROOT / "examples/reconciliation-recovered.json", 1024 * 1024)
    )
    before = None
    if name == "pending":
        data = json_bytes(
            read_source(ROOT / "examples/reconciliation-pending.json", 1024 * 1024)
        )
    elif name == "comparison":
        before = json_bytes(
            read_source(ROOT / "examples/reconciliation-pending.json", 1024 * 1024)
        )
    elif name == "missing-proof":
        data["transport_proof_sha256"] = None
    elif name == "stale":
        data["captured_at_ms"] = 1
    elif name == "failed-dependency":
        data["dependencies"]["identity"] = False
    elif name == "new-intent":
        before = copy.deepcopy(data)
        data["desired_sha"] = "e" * 40
    elif name == "transport-not-required":
        data.update(
            transport_required=False,
            transport_result="NOT_REQUIRED",
            transport_proof_sha256=None,
        )
    return data, before


def analyze(
    state: Workspace, parameters: dict[str, str], stage: Path
) -> tuple[str, str, dict[str, bytes]]:
    """Preserve original policy/currentness/transition semantics and record any explicit changed declaration."""
    mode = parameters.get("mode")
    if mode not in MODES:
        raise Rejected("choose a supported offline GitOps operation")
    raw_hash = None
    before = None
    if mode == MODES[3]:
        exercise = parameters.get("exercise", "")
        data, before = prepared(exercise)
        manifest = exercise.startswith("rendered-")
    else:
        manifest = mode == MODES[0]
        raw = read_source(
            Path(parameters.get("manifest" if manifest else "snapshot", "")),
            1024 * 1024,
        )
        raw_hash = hashlib.sha256(raw).hexdigest()
        try:
            data = (
                (json_bytes(raw) if raw.lstrip().startswith(b"[") else yaml_bytes(raw))
                if manifest
                else json_bytes(raw)
            )
        except (yaml.YAMLError, UnicodeError, RecursionError):
            raise Rejected("bounded manifest/snapshot parse failed") from None
        if mode == MODES[2]:
            before = json_bytes(
                read_source(Path(parameters.get("before", "")), 1024 * 1024)
            )
    scope: dict[str, Any] = {
        "schema": 1,
        "mode": mode,
        "source_bytes_sha256": raw_hash,
        "live_cluster_accessed": False,
        "live_enforcement_proven": False,
    }
    if manifest:
        if (
            not isinstance(data, list)
            or len(data) > 100
            or any(not isinstance(row, dict) for row in data)
        ):
            raise Rejected(
                "rendered manifests must be a bounded object array or YAML stream"
            )
        result = audit(data)
        scope.update(
            effective_manifest_sha256=hashlib.sha256(canonical(data)).hexdigest(),
            scope="Actual original closed static chart policy; no native Helm render or live enforcement occurred in this GUI.",
        )
        files = {"audit.json": canonical(result), "input-scope.json": canonical(scope)}
        return (
            "closed-manifest-audit",
            f"{result['decision']}: {result['resources']} resources; {len(result['failures'])} policy failures; no live enforcement",
            files,
        )
    original = copy.deepcopy(data)
    if not isinstance(data, dict):
        raise Rejected("closed workload snapshot object required")
    clock_text = parameters.get("as_of_ms", "")
    clock = (
        integer_control(clock_text, 0, 4102444800000)
        if clock_text
        else time.time_ns() // 1_000_000
    )
    age = integer_control(parameters.get("max_age_ms", ""), 1, 86400000)
    original_review = reconcile.assess(original, clock, age)
    wanted = parameters.get("desired_sha", "")
    if wanted:
        from .contracts import digest

        data["desired_sha"] = digest(wanted, 40)
    result = (
        reconcile.compare(before, data, clock, age)
        if before is not None
        else reconcile.assess(data, clock, age)
    )
    scope.update(
        original_snapshot_sha256=hashlib.sha256(canonical(original)).hexdigest(),
        effective_snapshot_sha256=hashlib.sha256(canonical(data)).hexdigest(),
        explicit_desired_override=wanted or None,
        original_desired_sha=original["desired_sha"],
        effective_desired_sha=data["desired_sha"],
        desired_override_changed=original["desired_sha"] != data["desired_sha"],
        original_verdict=original_review["verdict"],
        effective_verdict=result["verdict"],
        scope="Supplied declared observations, not authenticated acquisition. Only current desired intent is overridden; prior observation remains unchanged. Hash references do not establish live transport enforcement.",
    )
    reconcile.publish(result, stage / "review")
    files = {
        path.name: read_source(path, 4 * 1024 * 1024)
        for path in (stage / "review").iterdir()
    }
    files["input-scope.json"] = canonical(scope)
    return (
        "declared-reconciliation-review",
        f"{result['verdict']}; {len(result['review_queue'])} review checks; observed intent stays separate",
        files,
    )


def views(files: dict[str, bytes]) -> dict[str, list[dict[str, Any]]]:
    """Expose complete policy failures or check/transition queues without treating a filtered page as completeness proof."""
    scope = {"kind": "scope", **json_value(files["input-scope.json"])}
    if "audit.json" in files:
        result = json_value(files["audit.json"])
        return {
            "Static policy decision": [{"kind": "audit", **result}],
            "Static policy failures": [
                {"kind": "failure", "code": name} for name in result["failures"]
            ],
            "Unfiltered scope": [scope],
        }
    result = json_value(files["reconciliation.json"])
    return {
        "All current expectation checks": [
            {"kind": "check", **row} for row in result["checks"]
        ],
        "Review queue: failures and unknown": [
            {"kind": "check", **row} for row in result["review_queue"]
        ],
        "Before / after transitions": [
            {"kind": "transition", **row} for row in result.get("transitions", [])
        ],
        "Full verdict and unfiltered scope": [{"kind": "verdict", **result}, scope],
    }


def cells(row: dict[str, Any]) -> tuple[str, str, str, str]:
    """Render literal status/transition labels while preserving complete source hashes and reasons in detail."""
    kind = row["kind"]
    if kind == "check":
        return (
            str(row["check"]),
            "Declared expectation",
            str(row["reason"]),
            str(row["status"]),
        )
    if kind == "transition":
        return (
            str(row["check"]),
            str(row["before"]),
            str(row["after"]),
            "Explicit transition",
        )
    if kind == "audit":
        return (
            "Closed five-resource policy",
            str(row["resources"]) + " resources",
            str(len(row["failures"])) + " failures",
            str(row["decision"]),
        )
    if kind == "failure":
        return str(row["code"]), "Static policy", "Original failure retained", "DENY"
    if kind == "verdict":
        return (
            str(row["workload"]),
            "Supplied observations",
            str(len(row["review_queue"])) + " review checks",
            str(row["verdict"]),
        )
    if "original_desired_sha" in row:
        return (
            "Original / effective desired intent",
            str(row["original_desired_sha"])[:12] + "…",
            str(row["effective_desired_sha"])[:12] + "…",
            "Explicit changed declaration"
            if row["desired_override_changed"]
            else "Unchanged declaration",
        )
    return (
        "Offline source and scope",
        "No cluster access",
        "No live enforcement proof",
        "Local declarations only",
    )
