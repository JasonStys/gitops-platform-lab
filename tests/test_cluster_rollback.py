"""Observed rollback transition and false-success regressions without Docker or Kubernetes. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: completed_observations — line 84
# variable: helm — line 88
# variable: deployment — line 107
# variable: history — line 126
# definition: instrument — line 139
# parameter: drill — line 140
# parameter: monkeypatch — line 141
# parameter: helm — line 142
# parameter: deployment — line 143
# parameter: history — line 144
# variable: get — line 147
# parameter: kind — line 148
# parameter: name — line 148
# variable: run — line 152
# definition: test_pending_history_is_polled_until_deployed — line 158
# parameter: monkeypatch — line 159
# parameter: tmp_path — line 159
# variable: drill — line 162
# variable: deployment — line 163
# variable: helm — line 163
# variable: history — line 163
# variable: pending — line 164
# variable: get — line 166
# variable: run — line 166
# variable: clock — line 168
# parameter: seconds — line 173
# definition: test_pending_history_keeps_original_deadline — line 195
# parameter: monkeypatch — line 196
# parameter: tmp_path — line 196
# variable: drill — line 199
# variable: deployment — line 200
# variable: helm — line 200
# variable: history — line 200
# variable: _ — line 202
# variable: run — line 202
# variable: clock — line 203
# parameter: seconds — line 208
# definition: test_independent_false_success_conditions — line 243
# parameter: monkeypatch — line 244
# parameter: mutation — line 244
# parameter: tmp_path — line 244
# variable: drill — line 247
# variable: deployment — line 248
# variable: helm — line 248
# variable: history — line 248
# variable: deployment — line 278
# variable: item — line 290
# variable: helm — line 298
# definition: test_invalid_history_fails_closed — line 315
# parameter: history — line 316
# parameter: monkeypatch — line 316
# parameter: tmp_path — line 316
# variable: drill — line 319
# variable: _ — line 320
# variable: deployment — line 320
# variable: helm — line 320
# definition: test_actual_command_error_is_not_a_pending_success — line 326
# parameter: monkeypatch — line 327
# parameter: tmp_path — line 327
# variable: drill — line 330
# variable: deployment — line 331
# variable: helm — line 331
# variable: history — line 331
# variable: _ — line 332
# variable: run — line 332
# END CODE MAP

from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

from scripts import cluster_drill
from scripts.cluster_drill import Drill


def completed_observations() -> tuple[
    dict[str, Any], dict[str, Any], list[dict[str, Any]]
]:
    """Independent controller, Deployment and Helm CLI fixtures for the three-way completion oracle."""
    helm = {
        "metadata": {"generation": 3},
        "status": {
            "conditions": [
                {
                    "type": "Ready",
                    "status": "False",
                    "reason": "RollbackSucceeded",
                    "observedGeneration": 3,
                },
                {
                    "type": "Remediated",
                    "status": "True",
                    "reason": "RollbackSucceeded",
                    "observedGeneration": 3,
                },
            ]
        },
    }
    deployment = {
        "metadata": {"generation": 5},
        "spec": {
            "replicas": 2,
            "template": {
                "metadata": {"annotations": {"gitops.platform/revision": "promoted"}},
                "spec": {
                    "containers": [{"readinessProbe": {"httpGet": {"path": "/health"}}}]
                },
            },
        },
        "status": {
            "readyReplicas": 2,
            "updatedReplicas": 2,
            "replicas": 2,
            "availableReplicas": 2,
            "observedGeneration": 5,
        },
    }
    history = [
        {"revision": 2, "status": "superseded", "chart": "gitops-sre-1.0.0+good"},
        {"revision": 3, "status": "failed", "chart": "gitops-sre-1.0.0+bad"},
        {
            "revision": 4,
            "status": "deployed",
            "chart": "gitops-sre-1.0.0+good",
            "description": "Rollback to 2",
        },
    ]
    return helm, deployment, history


def instrument(
    drill: Drill,
    monkeypatch: pytest.MonkeyPatch,
    helm: dict[str, Any],
    deployment: dict[str, Any],
    history: Any,
) -> tuple[Mock, Mock]:
    """Replace only external reads; exercise the real completion predicate and polling implementation."""
    get = Mock(
        side_effect=lambda kind, name: {"helmrelease": helm, "deployment": deployment}[
            kind
        ]
    )
    run = Mock(return_value=json.dumps(history))
    monkeypatch.setattr(drill, "get", get)
    monkeypatch.setattr(drill, "run", run)
    return get, run


def test_pending_history_is_polled_until_deployed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Healthy restored pods are insufficient while actual Helm storage still says pending rollback."""
    drill = Drill(tmp_path / "owned")
    helm, deployment, history = completed_observations()
    pending = copy.deepcopy(history)
    pending[-1]["status"] = "pending-rollback"
    get, run = instrument(drill, monkeypatch, helm, deployment, history)
    run.side_effect = [json.dumps(pending), json.dumps(history)]
    clock = [0.0]
    monkeypatch.setattr(cluster_drill.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        cluster_drill.time,
        "sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )
    drill.wait(drill.rollback_ready, 180)
    assert clock[0] == 2.0
    assert (
        get.call_count == 4
    )  # Exactly one HelmRelease and one Deployment snapshot per poll.
    assert run.call_count == 2
    assert run.call_args.args[0] == [
        "helm",
        "history",
        "sre",
        "-n",
        "platform-lab",
        "--max",
        "10",
        "-o",
        "json",
    ]
    assert drill.checks == []  # Polling cannot fabricate a recorded live scenario.


def test_pending_history_keeps_original_deadline(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rollback which never deploys still fails at the original 180 second polling deadline."""
    drill = Drill(tmp_path / "owned")
    helm, deployment, history = completed_observations()
    history[-1]["status"] = "pending-rollback"
    _, run = instrument(drill, monkeypatch, helm, deployment, history)
    clock = [0.0]
    monkeypatch.setattr(cluster_drill.time, "monotonic", lambda: clock[0])
    monkeypatch.setattr(
        cluster_drill.time,
        "sleep",
        lambda seconds: clock.__setitem__(0, clock[0] + seconds),
    )
    with pytest.raises(TimeoutError, match="required observed state"):
        drill.wait(drill.rollback_ready, 180)
    assert clock[0] == 180.0
    assert run.call_count == 90
    assert drill.checks == []


@pytest.mark.parametrize(
    "mutation",
    [
        "reconciling",
        "old-generation",
        "failed-remediation",
        "missing-remediation",
        "old-pods",
        "unready-pods",
        "old-ready-pods",
        "surge-pods",
        "unavailable-pods",
        "insufficient-available-pods",
        "broken-path",
        "wrong-revision",
        "empty-deployment",
        "no-failed-revision",
        "latest-failed",
        "successful-upgrade",
        "unknown-target",
        "different-target-chart",
        "missing-chart",
        "failed-before-target",
        "empty-helm",
    ],
)
def test_independent_false_success_conditions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, mutation: str
) -> None:
    """No healthy pods, retained condition, successful upgrade or unrelated history can alone prove rollback."""
    drill = Drill(tmp_path / "owned")
    helm, deployment, history = completed_observations()
    if mutation == "reconciling":
        helm["status"]["conditions"].append({"type": "Reconciling", "status": "True"})
    elif mutation == "old-generation":
        helm["status"]["conditions"][1]["observedGeneration"] = 2
    elif mutation == "failed-remediation":
        helm["status"]["conditions"][1]["reason"] = "RollbackFailed"
    elif mutation == "missing-remediation":
        helm["status"]["conditions"] = []
    elif mutation == "old-pods":
        deployment["status"]["observedGeneration"] = 4
    elif mutation == "unready-pods":
        deployment["status"]["readyReplicas"] = 1
    elif mutation == "old-ready-pods":
        deployment["status"]["updatedReplicas"] = 0
    elif mutation == "surge-pods":
        deployment["status"]["replicas"] = 3
    elif mutation == "unavailable-pods":
        deployment["status"]["unavailableReplicas"] = 1
    elif mutation == "insufficient-available-pods":
        deployment["status"]["availableReplicas"] = 1
    elif mutation == "broken-path":
        deployment["spec"]["template"]["spec"]["containers"][0]["readinessProbe"][
            "httpGet"
        ]["path"] = "/missing"
    elif mutation == "wrong-revision":
        deployment["spec"]["template"]["metadata"]["annotations"][
            "gitops.platform/revision"
        ] = "broken"
    elif mutation == "empty-deployment":
        deployment = {}
    elif mutation == "no-failed-revision":
        history[1]["status"] = "superseded"
    elif mutation == "latest-failed":
        history[-1]["status"] = "failed"
    elif mutation == "successful-upgrade":
        history[-1]["description"] = "Upgrade complete"
    elif mutation == "unknown-target":
        history[-1]["description"] = "Rollback to 1"
    elif mutation == "different-target-chart":
        history[-1]["chart"] = "unrelated-chart-1.0.0"
    elif mutation == "missing-chart":
        for item in history:
            item.pop("chart")
    elif mutation == "failed-before-target":
        history[0]["status"] = "failed"
        history[1]["status"] = "superseded"
        history[-1]["description"] = "Rollback to 3"
        history[-1]["chart"] = history[1]["chart"]
    else:
        helm = {}
    instrument(drill, monkeypatch, helm, deployment, history)
    assert drill.rollback_ready() is False


@pytest.mark.parametrize(
    "history",
    [
        {},
        [],
        [{"revision": True}],
        [{"revision": 0}],
        [{"revision": 2}, {"revision": 2}],
        [{"revision": 2}, {"revision": 1}],
        [{"revision": 1}] * 11,
    ],
)
def test_invalid_history_fails_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, history: Any
) -> None:
    """Malformed, duplicate and reordered revisions fail rather than being interpreted as success."""
    drill = Drill(tmp_path / "owned")
    helm, deployment, _ = completed_observations()
    instrument(drill, monkeypatch, helm, deployment, history)
    with pytest.raises(ValueError):
        drill.rollback_ready()


def test_actual_command_error_is_not_a_pending_success(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A failed actual Helm invocation remains an immediate failure and is not silently retried."""
    drill = Drill(tmp_path / "owned")
    helm, deployment, history = completed_observations()
    _, run = instrument(drill, monkeypatch, helm, deployment, history)
    run.side_effect = RuntimeError("synthetic Helm command failed")
    with pytest.raises(RuntimeError, match="Helm command failed"):
        drill.wait(drill.rollback_ready, 180)
    assert run.call_count == 1
