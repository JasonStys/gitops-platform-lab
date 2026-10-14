"""Native context/port guard regressions; no Docker or existing Kubernetes cluster is touched. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: fixture_config — line 23
# definition: test_concrete_loopback_and_config — line 42
# definition: test_foreign_endpoint_rejected — line 61
# parameter: case — line 61
# variable: config — line 63
# variable: port — line 64
# variable: port — line 66
# variable: port — line 68
# END CODE MAP

from __future__ import annotations

from typing import Any

import pytest
import yaml

from scripts.cluster_drill import loopback_port, validate_config


def fixture_config() -> dict[str, Any]:
    """Build a synthetic no-credential config solely for endpoint/context contract tests."""
    return {
        "current-context": "k3d-gitops-lab-123456789a",
        "clusters": [
            {
                "name": "k3d-gitops-lab-123456789a",
                "cluster": {"server": "https://127.0.0.1:54321"},
            }
        ],
        "contexts": [
            {
                "name": "k3d-gitops-lab-123456789a",
                "context": {"cluster": "k3d-gitops-lab-123456789a"},
            }
        ],
    }


def test_concrete_loopback_and_config() -> None:
    """A real OS-allocated port is nonzero; a matching synthetic context remains accepted."""
    assert 1 <= loopback_port() <= 65535
    validate_config(yaml.safe_dump(fixture_config()), "gitops-lab-123456789a", 54321)


@pytest.mark.parametrize(
    "case",
    [
        "zero",
        "bool-port",
        "context",
        "external",
        "zero-endpoint",
        "extra-cluster",
        "binding",
        "name",
    ],
)
def test_foreign_endpoint_rejected(case: str) -> None:
    """Port zero and any foreign context/endpoint/binding fail before running a Kubernetes command."""
    config = fixture_config()
    port = 54321
    if case == "zero":
        port = 0
    elif case == "bool-port":
        port = True
    elif case == "context":
        config["current-context"] = "production"
    elif case == "external":
        config["clusters"][0]["cluster"]["server"] = "https://production.invalid:54321"
    elif case == "zero-endpoint":
        config["clusters"][0]["cluster"]["server"] = "https://127.0.0.1:0"
    elif case == "extra-cluster":
        config["clusters"].append(config["clusters"][0])
    elif case == "binding":
        config["contexts"][0]["context"]["cluster"] = "production"
    else:
        config["clusters"][0]["name"] = "production"
    with pytest.raises(ValueError):
        validate_config(yaml.safe_dump(config), "gitops-lab-123456789a", port)
