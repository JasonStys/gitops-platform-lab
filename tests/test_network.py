"""Negative oracles: refusal/timeout alone never prove policy; counts and positive controls are mandatory. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: test_denial_requires_observed_packets — line 34
# parameter: reason — line 34
# variable: proof — line 36
# variable: after — line 38
# variable: before — line 38
# definition: test_false_denial_rejected — line 57
# parameter: after — line 58
# parameter: before — line 58
# parameter: expected — line 58
# parameter: proof — line 58
# definition: test_counter_namespace_scope — line 66
# parameter: tmp_path — line 66
# variable: drill — line 68
# variable: lines — line 69
# END CODE MAP

from __future__ import annotations

from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest

from lab.network import validate_observation
from scripts.cluster_drill import Drill


@pytest.mark.parametrize(
    "reason", ["timeout", "connection-refused", "network-unreachable"]
)
def test_denial_requires_observed_packets(reason: str) -> None:
    """Actual transport candidates are accepted only with an independently measured counter increase."""
    proof = {"outcome": "blocked", "reason": reason}
    validate_observation(proof, "deny", 0, 1)
    for before, after in ((0, 0), (1, 1), (2, 1)):
        with pytest.raises(ValueError):
            validate_observation(proof, "deny", before, after)


@pytest.mark.parametrize(
    ("proof", "expected", "before", "after"),
    [
        ({"outcome": "allowed", "reason": "http-200"}, "deny", 0, 1),
        ({"outcome": "blocked", "reason": "timeout"}, "allow", 0, 1),
        ({"outcome": "blocked", "reason": "dns-failure"}, "deny", 0, 1),
        ({"outcome": "blocked", "reason": "http-error"}, "deny", 0, 1),
        ({"outcome": "blocked", "reason": "timeout", "hidden": True}, "deny", 0, 1),
        ({"outcome": "blocked", "reason": "timeout"}, "deny", True, 1),
        ({"outcome": "blocked", "reason": "timeout"}, "deny", 0, True),
        ({"outcome": "blocked", "reason": "timeout"}, "deny", -1, 1),
        ({"outcome": "blocked", "reason": "timeout"}, "unknown", 0, 1),
    ],
)
def test_false_denial_rejected(
    proof: Any, expected: str, before: int, after: int
) -> None:
    """Errors, hidden fields, wrong labels/expectations and invalid/stale counters fail closed."""
    with pytest.raises(ValueError):
        validate_observation(proof, expected, before, after)
    validate_observation({"outcome": "allowed", "reason": "http-200"}, "allow", 0, 0)


def test_counter_namespace_scope(tmp_path: Path) -> None:
    """Node counter parsing reads only the exact owned namespace, not similarly named or unrelated rules."""
    drill = Drill(tmp_path / "owned")
    lines = "\n".join(
        [
            '[2:100] -A KUBE-POD-FW-ONE -m comment --comment "rule to REJECT traffic destined for POD name:sre-one namespace: platform-lab" -j REJECT',
            '[3:100] -A KUBE-POD-FW-TWO -m comment --comment "rule to REJECT traffic destined for POD name:sre-two namespace: platform-lab" -j REJECT',
            '[999:100] -A KUBE-POD-FW-OTHER -m comment --comment "namespace: platform-lab-evil" -j REJECT',
            '[999:100] -A KUBE-POD-FW-OTHER -m comment --comment "namespace: platform-client" -j REJECT',
        ]
    )
    with patch.object(drill, "run", return_value=lines):
        assert drill.reject_count() == 5
    with patch.object(drill, "run", return_value="no matching rules"):
        with pytest.raises(ValueError):
            drill.reject_count()
