"""Negative security-policy cases, type boundaries, selector semantics and randomized replicas. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: selected — line 49
# parameter: documents — line 50
# parameter: kind — line 50
# parameter: name — line 50
# variable: item — line 55
# definition: replace — line 60
# parameter: path — line 60
# parameter: root — line 60
# parameter: value — line 60
# variable: cursor — line 62
# variable: part — line 63
# variable: cursor — line 64
# definition: test_real_render_allow — line 68
# parameter: documents — line 68
# variable: report — line 70
# definition: test_deployment_negative — line 175
# parameter: documents — line 176
# parameter: path — line 176
# parameter: value — line 176
# variable: report — line 180
# definition: test_closed_inventory — line 200
# parameter: case — line 200
# parameter: documents — line 200
# variable: pod — line 202
# definition: test_access_boundaries — line 238
# parameter: case — line 238
# parameter: documents — line 238
# variable: ingress — line 240
# variable: peer — line 252
# definition: test_replica_property — line 266
# parameter: documents — line 266
# definition: property_case — line 270
# parameter: count — line 270
# END CODE MAP

from __future__ import annotations

from typing import Any

import pytest
from hypothesis import given
from hypothesis import strategies as st

from lab.policy import audit


def selected(
    documents: list[dict[str, Any]], kind: str, name: str = "sre"
) -> dict[str, Any]:
    """Find the one named resource in a private test fixture."""
    return next(
        item
        for item in documents
        if item["kind"] == kind and item["metadata"]["name"] == name
    )


def replace(root: Any, path: tuple[str | int, ...], value: Any) -> None:
    """Replace one explicit nested fixture value for an independently labeled negative case."""
    cursor = root
    for part in path[:-1]:
        cursor = cursor[part]
    cursor[path[-1]] = value


def test_real_render_allow(documents: list[dict[str, Any]]) -> None:
    """Actual five-resource Helm render passes, without claiming live policy enforcement."""
    report = audit(documents)
    assert report["decision"] == "ALLOW" and not report["live_enforcement_proven"]


@pytest.mark.parametrize(
    ("path", "value"),
    [
        (("apiVersion",), "v1"),
        (("metadata", "namespace"), "kube-system"),
        (("spec", "replicas"), True),
        (("spec", "replicas"), 0),
        (("spec", "replicas"), 4),
        (("spec", "revisionHistoryLimit"), 100),
        (("spec", "progressDeadlineSeconds"), 999),
        (("spec", "strategy", "rollingUpdate", "maxSurge"), True),
        (("spec", "strategy", "rollingUpdate", "maxUnavailable"), 1),
        (("spec", "selector", "matchLabels"), {"app": "other"}),
        (("spec", "template", "metadata", "labels"), {"app": "other"}),
        (
            ("spec", "template", "metadata", "annotations", "gitops.platform/revision"),
            "broken",
        ),
        (("spec", "template", "spec", "serviceAccountName"), "default"),
        (("spec", "template", "spec", "automountServiceAccountToken"), True),
        (("spec", "template", "spec", "terminationGracePeriodSeconds"), 999),
        (("spec", "template", "spec", "securityContext", "runAsNonRoot"), 1),
        (("spec", "template", "spec", "securityContext", "runAsUser"), 0),
        (
            ("spec", "template", "spec", "securityContext", "seccompProfile"),
            {"type": "Unconfined"},
        ),
        (
            ("spec", "template", "spec", "containers", 0, "image"),
            "outside.invalid/unreviewed:latest",
        ),
        (("spec", "template", "spec", "containers", 0, "imagePullPolicy"), "Always"),
        (("spec", "template", "spec", "containers", 0, "args"), ["--unsafe"]),
        (
            ("spec", "template", "spec", "containers", 0, "ports", 0, "containerPort"),
            80,
        ),
        (
            (
                "spec",
                "template",
                "spec",
                "containers",
                0,
                "securityContext",
                "allowPrivilegeEscalation",
            ),
            True,
        ),
        (
            (
                "spec",
                "template",
                "spec",
                "containers",
                0,
                "securityContext",
                "readOnlyRootFilesystem",
            ),
            False,
        ),
        (
            (
                "spec",
                "template",
                "spec",
                "containers",
                0,
                "securityContext",
                "capabilities",
            ),
            {"add": ["NET_ADMIN"]},
        ),
        (("spec", "template", "spec", "containers", 0, "resources"), {}),
        (
            (
                "spec",
                "template",
                "spec",
                "containers",
                0,
                "readinessProbe",
                "httpGet",
                "path",
            ),
            "/missing",
        ),
        (
            (
                "spec",
                "template",
                "spec",
                "containers",
                0,
                "livenessProbe",
                "timeoutSeconds",
            ),
            True,
        ),
    ],
)
def test_deployment_negative(
    documents: list[dict[str, Any]], path: tuple[str | int, ...], value: Any
) -> None:
    """Every labeled unsafe mutation is denied without echoing the private/external value."""
    replace(selected(documents, "Deployment"), path, value)
    report = audit(documents)
    assert report["decision"] == "DENY"
    assert "outside.invalid" not in str(report)


@pytest.mark.parametrize(
    "case",
    [
        "extra-pod",
        "extra-container",
        "duplicate",
        "missing",
        "wrong-name",
        "host-network",
        "host-volume",
        "sidecar",
        "bad-kind",
        "bad-object",
    ],
)
def test_closed_inventory(documents: list[dict[str, Any]], case: str) -> None:
    """Unknown fields/resources/identities and elevated host access cannot evade an allowlist."""
    pod = selected(documents, "Deployment")["spec"]["template"]["spec"]
    if case == "extra-pod":
        pod["nodeName"] = "host"
    elif case == "extra-container":
        pod["containers"][0]["envFrom"] = [{"secretRef": {"name": "private"}}]
    elif case == "duplicate":
        documents[0] = documents[1]
    elif case == "missing":
        documents.pop()
    elif case == "wrong-name":
        documents[0]["metadata"]["name"] = "other"
    elif case == "host-network":
        pod["hostNetwork"] = True
    elif case == "host-volume":
        pod["volumes"] = [{"hostPath": {"path": "/"}}]
    elif case == "sidecar":
        pod["containers"].append(pod["containers"][0])
    elif case == "bad-kind":
        documents[0]["kind"] = "ClusterRoleBinding"
    else:
        del documents[0]["metadata"]
    assert audit(documents)["decision"] == "DENY"


@pytest.mark.parametrize(
    "case",
    [
        "public-service",
        "token",
        "no-egress-deny",
        "or-selector",
        "wrong-port",
        "any-pod",
        "all-namespaces",
    ],
)
def test_access_boundaries(documents: list[dict[str, Any]], case: str) -> None:
    """NetworkPolicy namespace/pod selectors must be ANDed in one peer, not separate permissive peers."""
    ingress = selected(documents, "NetworkPolicy", "reviewer-ingress")["spec"]
    if case == "public-service":
        selected(documents, "Service")["spec"]["type"] = "LoadBalancer"
    elif case == "token":
        selected(documents, "ServiceAccount", "workload")[
            "automountServiceAccountToken"
        ] = True
    elif case == "no-egress-deny":
        selected(documents, "NetworkPolicy", "default-deny")["spec"]["policyTypes"] = [
            "Ingress"
        ]
    elif case == "or-selector":
        peer = ingress["ingress"][0]["from"][0]
        ingress["ingress"][0]["from"] = [
            {"namespaceSelector": peer["namespaceSelector"]},
            {"podSelector": peer["podSelector"]},
        ]
    elif case == "wrong-port":
        ingress["ingress"][0]["ports"][0]["port"] = 80
    elif case == "any-pod":
        ingress["podSelector"] = {}
    else:
        ingress["ingress"][0]["from"][0]["namespaceSelector"] = {}
    assert audit(documents)["decision"] == "DENY"


def test_replica_property(documents: list[dict[str, Any]]) -> None:
    """Exercise 100 independently generated integer counts; only 1–3 satisfy the closed quota."""

    @given(st.integers(-100, 100))
    def property_case(count: int) -> None:
        """Check the independent arithmetic oracle against the actual chart policy."""
        selected(documents, "Deployment")["spec"]["replicas"] = count
        assert (audit(documents)["decision"] == "ALLOW") == (1 <= count <= 3)

    property_case()
