"""Informational warmed policy parsing/audit benchmark with an actual correctness oracle. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 31
# definition: benchmark — line 37
# variable: content — line 39
# variable: samples — line 40
# variable: _ — line 42
# variable: started — line 43
# variable: _ — line 44
# variable: report — line 45
# variable: _ — line 49
# variable: peak — line 49
# definition: main — line 64
# variable: parser — line 66
# variable: args — line 68
# variable: result — line 69
# variable: stream — line 72
# END CODE MAP

from __future__ import annotations

import argparse
import json
import platform
import statistics
import sys
import time
import tracemalloc
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.contracts import json_bytes  # noqa: E402
from lab.policy import audit  # noqa: E402


def benchmark() -> dict[str, object]:
    """Measure five batches of 100 actual document parses/audits; never gate on hardware-dependent times."""
    content = (ROOT / "examples/rendered.json").read_bytes()
    samples = []
    tracemalloc.start()
    for _ in range(5):
        started = time.perf_counter_ns()
        for _ in range(100):
            report = audit(json_bytes(content))
            if report["decision"] != "ALLOW" or report["resources"] != 5:
                raise ValueError("benchmark correctness oracle failed")
        samples.append(round((time.perf_counter_ns() - started) / 100 / 1_000_000, 3))
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return {
        "python": platform.python_version(),
        "os": platform.system(),
        "batches": 5,
        "audits_per_batch": 100,
        "resources_per_audit": 5,
        "samples_ms": samples,
        "median_ms_per_audit": statistics.median(samples),
        "peak_python_bytes": peak,
        "scope": "warm bounded JSON parse and closed Helm policy; excludes cluster, native Helm and network; informational only",
    }


def main() -> int:
    """Print actual measurements and optionally save a new aggregate report, without replacing prior evidence."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    result = benchmark()
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, sort_keys=True, indent=2) + "\n")
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
