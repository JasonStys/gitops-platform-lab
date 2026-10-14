"""Actual native Helm schema/render tests and deterministic measured example maintenance. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 35
# definition: execute — line 41
# parameter: write — line 41
# variable: executable — line 43
# variable: baseline — line 50
# variable: example — line 65
# variable: data — line 66
# variable: cases — line 72
# variable: defaults — line 73
# variable: change — line 79
# variable: expected — line 79
# variable: name — line 79
# variable: directory — line 91
# variable: values — line 92
# variable: result — line 94
# definition: main — line 123
# variable: parser — line 125
# variable: args — line 128
# variable: result — line 129
# variable: stream — line 132
# END CODE MAP

from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.contracts import yaml_bytes  # noqa: E402
from lab.policy import audit  # noqa: E402


def execute(write: bool = False) -> dict[str, Any]:
    """Run real pinned Helm; reject seven invalid values, audit three good renders, and compare the checked example."""
    executable = ROOT / ".tools" / ("helm.exe" if sys.platform == "win32" else "helm")
    subprocess.run(
        [str(executable), "lint", str(ROOT / "chart"), "--strict"],
        check=True,
        capture_output=True,
        timeout=30,
    )
    baseline = yaml_bytes(
        subprocess.check_output(
            [
                str(executable),
                "template",
                "sre",
                str(ROOT / "chart"),
                "-n",
                "platform-lab",
            ],
            timeout=30,
        )
    )
    if audit(baseline)["decision"] != "ALLOW":
        raise ValueError("actual Helm render failed policy")
    example = ROOT / "examples/rendered.json"
    data = json.dumps(baseline, sort_keys=True, indent=2) + "\n"
    if write:
        example.parent.mkdir(exist_ok=True)
        example.write_text(data, encoding="utf-8", newline="\n")
    elif example.read_text(encoding="utf-8") != data:
        raise ValueError("native Helm render and checked example differ")
    cases: list[dict[str, Any]] = []
    defaults = {
        "replicas": 1,
        "image": "gitops-sre:lab",
        "readinessPath": "/health",
        "revision": "baseline",
    }
    for name, change, expected in (
        ("minimum", {}, True),
        ("promotion", {"replicas": 2, "revision": "promoted"}, True),
        ("maximum", {"replicas": 3, "revision": "recovered"}, True),
        ("below-quota", {"replicas": 0}, False),
        ("above-quota", {"replicas": 4}, False),
        ("boolean-count", {"replicas": True}, False),
        ("external-image", {"image": "unreviewed:latest"}, False),
        ("unknown-setting", {"privileged": True}, False),
        ("unknown-revision", {"revision": "unknown"}, False),
        ("unknown-path", {"readinessPath": "/admin"}, False),
    ):
        with tempfile.TemporaryDirectory() as directory:
            values = Path(directory) / "values.json"
            values.write_text(json.dumps({**defaults, **change}), encoding="utf-8")
            result = subprocess.run(
                [
                    str(executable),
                    "template",
                    "sre",
                    str(ROOT / "chart"),
                    "-n",
                    "platform-lab",
                    "-f",
                    str(values),
                ],
                capture_output=True,
                timeout=30,
                check=False,
            )
            if (result.returncode == 0) != expected:
                raise ValueError("native Helm acceptance differs from test oracle")
            if expected and audit(yaml_bytes(result.stdout))["decision"] != "ALLOW":
                raise ValueError("rendered accepted values differ from policy")
            cases.append({"name": name, "expected_allow": expected, "passed": True})
    return {
        "author": "Jason Stys",
        "engine": "native Helm 3.22.0",
        "cases": cases,
        "policy_resources": len(baseline),
        "live_cluster_enforcement": False,
    }


def main() -> int:
    """Validate actual rendering; only an explicit generation flag updates the synthetic checked example."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--write-example", action="store_true")
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = execute(args.write_example)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
