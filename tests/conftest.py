"""Private per-test fixtures, with real Helm-rendered resources and explicitly fake report inputs. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 20
# definition: documents — line 24
# definition: evidence — line 32
# variable: name — line 49
# END CODE MAP

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any

import pytest

from lab.evidence import SCENARIOS

ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def documents() -> list[dict[str, Any]]:
    """Return an independent copy of the checked real Helm render, never mutate a shared test fixture."""
    return copy.deepcopy(
        json.loads((ROOT / "examples/rendered.json").read_text(encoding="utf-8"))
    )


@pytest.fixture
def evidence() -> dict[str, Any]:
    """Fake closed-record input for validation tests only; no cluster success is claimed by this fixture."""
    return {
        "schema": 1,
        "author": "Jason Stys",
        "synthetic": True,
        "source_sha": "a" * 40,
        "workload_source_sha": "b" * 40,
        "built_image_id": "c" * 64,
        "cluster": "disposable-k3d",
        "checks": [
            {
                "name": name,
                "result": "PASS",
                "duration_ms": 1,
                "evidence": {"test_fixture": True},
            }
            for name in sorted(SCENARIOS)
        ],
    }
