"""Verify untouched upstream source, workflow permissions/storage rules and reviewed release contracts. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 26
# definition: main — line 31
# variable: upstream — line 33
# variable: expected — line 34
# variable: path — line 34
# variable: workflow — line 37
# variable: source — line 38
# variable: token — line 41
# variable: action — line 50
# variable: release — line 58
# variable: spec — line 59
# END CODE MAP

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.contracts import yaml_bytes  # noqa: E402


def main() -> int:
    """Check source hashes and safe CI/configuration invariants; this is not a live security assessment."""
    upstream = json.loads((ROOT / "upstream.lock.json").read_text(encoding="utf-8"))
    for path, expected in upstream["files"].items():
        if hashlib.sha256((ROOT / path).read_bytes()).hexdigest() != expected:
            raise ValueError("upstream source/notice digest mismatch")
    for workflow in (ROOT / ".github/workflows").glob("*.yml"):
        source = workflow.read_text(encoding="utf-8")
        if any(
            token in source
            for token in (
                "pull_request_target:",
                "actions/upload-artifact",
                "actions/cache",
                "cache: 'pip'",
                "persist-credentials: true",
            )
        ):
            raise ValueError("unsafe event/storage/checkout setting")
        for action in re.findall(r"uses: ([^\s]+)", source):
            if not re.fullmatch(
                r"[A-Za-z0-9_.-]+/[A-Za-z0-9_./-]+@[0-9a-f]{40}", action
            ):
                raise ValueError("immutable action revision required")
        if "contents: read" not in source:
            raise ValueError("read-only global content permission required")
        yaml_bytes(source.encode())
    release = yaml.safe_load((ROOT / "gitops/release.yml").read_text(encoding="utf-8"))
    spec = release["spec"]
    if (
        spec["serviceAccountName"] != "delivery"
        or spec["driftDetection"]["mode"] != "enabled"
        or spec["upgrade"]["remediation"]
        != {"retries": 0, "remediateLastFailure": True, "strategy": "rollback"}
    ):
        raise ValueError("GitOps rollback/drift/impersonation contract changed")
    if (
        spec["values"]["readinessPath"] != "/health"
        or spec["values"]["revision"] != "baseline"
    ):
        raise ValueError("public Git intent must remain healthy")
    print("Pinned upstream and least-privilege/storage-free workflow contracts passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
