"""Offline policy/report CLI; arbitrary files are not executed or sent anywhere. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: main — line 25
# variable: parser — line 27
# variable: commands — line 28
# variable: policy — line 29
# variable: report — line 31
# variable: args — line 34
# variable: result — line 37
# END CODE MAP

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from lab.contracts import json_bytes, read_bytes, yaml_bytes
from lab.evidence import publish
from lab.policy import audit


def main() -> int:
    """Audit explicit rendered manifests or render a complete measured report; fail with fixed errors."""
    parser = argparse.ArgumentParser(description="GitOps Platform Lab — Jason Stys")
    commands = parser.add_subparsers(dest="command", required=True)
    policy = commands.add_parser("audit")
    policy.add_argument("manifest", type=Path)
    report = commands.add_parser("report")
    report.add_argument("evidence", type=Path)
    report.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "audit":
            result = audit(yaml_bytes(read_bytes(args.manifest)))
            print(json.dumps(result, sort_keys=True))
            return 0 if result["decision"] == "ALLOW" else 1
        publish(json_bytes(read_bytes(args.evidence)), args.output)
    except (ValueError, OSError, UnicodeError, RecursionError, yaml.YAMLError):
        print("Input/output rejected. See docs/runbook.md for bounded contracts.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
