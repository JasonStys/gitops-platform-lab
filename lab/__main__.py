"""Offline policy/report CLI; arbitrary files are not executed or sent anywhere. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: main — line 29
# variable: parser — line 31
# variable: commands — line 32
# variable: policy — line 33
# variable: report — line 35
# variable: review — line 38
# variable: args — line 44
# variable: result — line 47
# variable: snapshot — line 51
# variable: result — line 52
# END CODE MAP

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from lab import reconcile
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
    review = commands.add_parser("reconcile")
    review.add_argument("snapshot", type=Path)
    review.add_argument("--before", type=Path)
    review.add_argument("--as-of-ms", type=int, required=True)
    review.add_argument("--max-age-ms", type=int, default=300000)
    review.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.command == "audit":
            result = audit(yaml_bytes(read_bytes(args.manifest)))
            print(json.dumps(result, sort_keys=True))
            return 0 if result["decision"] == "ALLOW" else 1
        if args.command == "reconcile":
            snapshot = json_bytes(read_bytes(args.snapshot))
            result = (
                reconcile.compare(
                    json_bytes(read_bytes(args.before)),
                    snapshot,
                    args.as_of_ms,
                    args.max_age_ms,
                )
                if args.before
                else reconcile.assess(snapshot, args.as_of_ms, args.max_age_ms)
            )
            reconcile.publish(result, args.output)
            print(
                json.dumps(
                    {
                        "verdict": result["verdict"],
                        "review_items": len(result["review_queue"]),
                    }
                )
            )
            return int(result["verdict"] != "RECONCILED_ASSERTED")
        publish(json_bytes(read_bytes(args.evidence)), args.output)
    except (ValueError, OSError, UnicodeError, RecursionError, yaml.YAMLError):
        print("Input/output rejected. See docs/runbook.md for bounded contracts.")
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
