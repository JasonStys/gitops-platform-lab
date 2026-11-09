"""Independent stale-revision, missing-evidence and desired-intent review tests. Created by Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: snapshot — line 51
# definition: test_old_healthy_pod_is_not_reconciled — line 56
# variable: pending — line 58
# variable: result — line 59
# variable: row — line 61
# variable: row — line 66
# variable: recovered — line 71
# definition: test_unknown_never_clear — line 92
# parameter: change — line 92
# variable: raw — line 94
# variable: clock — line 95
# variable: clock — line 101
# variable: clock — line 103
# definition: test_failed_dependencies_and_changed_intent — line 111
# variable: raw — line 113
# variable: result — line 116
# variable: row — line 117
# variable: after — line 121
# variable: compared — line 125
# definition: test_contract_refusal — line 150
# parameter: field — line 150
# parameter: value — line 150
# variable: raw — line 152
# definition: test_comparison_scope_and_optional_transport — line 158
# variable: raw — line 160
# variable: other — line 161
# variable: other — line 165
# variable: row — line 175
# definition: test_operator_cli_and_preserved_outputs — line 179
# parameter: tmp_path — line 179
# variable: pending — line 181
# variable: args — line 192
# variable: result — line 206
# variable: page — line 208
# END CODE MAP

import copy
import json
from pathlib import Path
from unittest.mock import patch

import pytest

from lab.__main__ import main
from lab.contracts import json_bytes, read_bytes
from lab.reconcile import assess, compare, publish


def snapshot() -> dict[str, object]:
    """Load explicit synthetic recovered observations, not data from any real cluster."""
    return json_bytes(read_bytes(Path("examples/reconciliation-recovered.json")))


def test_old_healthy_pod_is_not_reconciled() -> None:
    """Two healthy replicas at an old applied revision cannot prove the newer Git intent was applied."""
    pending = json_bytes(read_bytes(Path("examples/reconciliation-pending.json")))
    result = assess(pending, 1000100, 300000)
    assert result["verdict"] == "NEEDS_REVIEW"
    assert [(row["check"], row["status"]) for row in result["review_queue"]] == [
        ("applied_revision", "FAIL"),
        ("observed_generation", "FAIL"),
    ]
    assert (
        next(row for row in result["checks"] if row["check"] == "ready_replicas")[
            "status"
        ]
        == "PASS"
    )
    recovered = compare(pending, snapshot(), 1000100, 300000)
    assert recovered["verdict"] == "RECONCILED_ASSERTED"
    assert not recovered["intent_changed"]
    assert len(recovered["transitions"]) == 2


@pytest.mark.parametrize(
    "change",
    [
        "applied_sha",
        "source_sha",
        "observed_generation",
        "ready_replicas",
        "helm_ready",
        "dependency",
        "proof",
        "future",
        "stale",
        "transport-unknown",
    ],
)
def test_unknown_never_clear(change: str) -> None:
    """Absent source/controller/dependency/transport observations and stale snapshots remain inconclusive."""
    raw = snapshot()
    clock = 1000100
    if change == "dependency":
        raw["dependencies"]["identity"] = None
    elif change == "proof":
        raw["transport_proof_sha256"] = None
    elif change == "future":
        clock -= 1
    elif change == "stale":
        clock += 300001
    elif change == "transport-unknown":
        raw["transport_result"] = "UNKNOWN"
    else:
        raw[change] = None
    assert assess(raw, clock, 300000)["verdict"] == "INSUFFICIENT_EVIDENCE"


def test_failed_dependencies_and_changed_intent() -> None:
    """Failed dependency or transport is explicit; dropping a required check is not recorded as a repair."""
    raw = snapshot()
    raw["dependencies"]["identity"] = False
    raw["transport_result"] = "FAIL"
    result = assess(raw, 1000100, 300000)
    assert {row["check"] for row in result["review_queue"]} == {
        "dependency:identity",
        "transport_evidence",
    }
    after = copy.deepcopy(raw)
    after["captured_at_ms"] += 1
    after["desired_sha"] = "e" * 40
    after["dependencies"] = {}
    compared = compare(raw, after, 1000200, 300000)
    assert compared["intent_changed"] and compared["verdict"] == "NEEDS_REVIEW"
    assert {
        "check": "dependency:identity",
        "before": "FAIL",
        "after": None,
    } in compared["transitions"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("schema", True),
        ("workload", "../outside"),
        ("desired_sha", "not-a-sha"),
        ("generation", None),
        ("desired_replicas", None),
        ("helm_ready", "true"),
        ("dependencies", {"identity": "true"}),
        ("dependencies", []),
        ("transport_result", "NOT_REQUIRED"),
        ("transport_required", "true"),
        ("transport_proof_sha256", "bad"),
    ],
)
def test_contract_refusal(field: str, value: object) -> None:
    """Missing expectations, coercible booleans and unsupported scope cannot silently pass."""
    raw = snapshot()
    raw[field] = value
    with pytest.raises(ValueError):
        assess(raw, 1000100, 300000)


def test_comparison_scope_and_optional_transport() -> None:
    """No cross-workload or backwards-time comparison; an explicit unrequired control stays unclaimed."""
    raw = snapshot()
    other = copy.deepcopy(raw)
    other["workload"] = "another/workload"
    with pytest.raises(ValueError):
        compare(raw, other, 1000100, 300000)
    other = copy.deepcopy(raw)
    other["captured_at_ms"] -= 1
    with pytest.raises(ValueError):
        compare(raw, other, 1000100, 300000)
    raw["transport_required"] = False
    with pytest.raises(ValueError):
        assess(raw, 1000100, 300000)
    raw["transport_result"] = "NOT_REQUIRED"
    assert not any(
        row["check"] == "transport_evidence"
        for row in assess(raw, 1000100, 300000)["checks"]
    )


def test_operator_cli_and_preserved_outputs(tmp_path: Path) -> None:
    """An operator runs pending/recovered review and opens immutable, inert comparison output."""
    pending = [
        "lab",
        "reconcile",
        "examples/reconciliation-pending.json",
        "--as-of-ms",
        "1000100",
        "--output",
        str(tmp_path / "pending"),
    ]
    with patch("sys.argv", pending):
        assert main() == 1
    args = [
        "lab",
        "reconcile",
        "examples/reconciliation-recovered.json",
        "--before",
        "examples/reconciliation-pending.json",
        "--as-of-ms",
        "1000100",
        "--output",
        str(tmp_path / "recovered"),
    ]
    with patch("sys.argv", args):
        assert main() == 0
        assert main() == 2
    result = json.loads((tmp_path / "recovered/reconciliation.json").read_text())
    assert result["verdict"] == "RECONCILED_ASSERTED"
    page = (tmp_path / "recovered/reconciliation.html").read_text()
    assert (
        "Content-Security-Policy" in page
        and "Jason Stys" in page
        and "<script" not in page
    )
    with pytest.raises(OSError):
        publish(result, tmp_path / "absent/new")
