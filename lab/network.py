"""Observed K3s denial requires transport, active scoped rule counters and external controls. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: validate_observation — line 18
# parameter: after — line 18
# parameter: before — line 18
# parameter: expected — line 18
# parameter: proof — line 18
# variable: item — line 20
# END CODE MAP

from __future__ import annotations

from typing import Any

from lab.contracts import integer, record


def validate_observation(proof: Any, expected: str, before: int, after: int) -> None:
    """Reject dead-service/generic-error false positives: denial needs eligible transport AND new policy packets."""
    item = record(proof, {"outcome", "reason"})
    integer(before, 0, 1_800_000)
    integer(after, 0, 1_800_000)
    if expected == "allow":
        if item != {"outcome": "allowed", "reason": "http-200"}:
            raise ValueError("positive control did not reach owned service")
    elif expected == "deny":
        if (
            item["outcome"] != "blocked"
            or item["reason"]
            not in {"timeout", "connection-refused", "network-unreachable"}
            or after <= before
        ):
            raise ValueError("transport alone is not evidence of policy rejection")
    else:
        raise ValueError("unknown network expectation")
