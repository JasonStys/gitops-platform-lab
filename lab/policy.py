"""Fail-closed policies for this one closed Helm workload, not arbitrary Kubernetes. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: NAMESPACE — line 45
# variable: KINDS — line 46
# definition: require — line 49
# parameter: code — line 49
# parameter: condition — line 49
# parameter: failures — line 49
# definition: scalar_types — line 55
# parameter: value — line 55
# variable: numbers — line 57
# variable: booleans — line 71
# variable: child — line 78
# variable: key — line 78
# variable: child — line 88
# definition: audit — line 92
# parameter: documents — line 92
# variable: failures — line 94
# variable: inventory — line 95
# variable: item — line 101
# variable: metadata — line 104
# variable: identity — line 106
# variable: service — line 119
# variable: account — line 140
# variable: default — line 150
# variable: ingress — line 164
# definition: deployment — line 203
# parameter: failures — line 203
# parameter: raw — line 203
# variable: item — line 205
# variable: spec — line 207
# variable: template — line 238
# variable: metadata — line 239
# variable: annotations — line 241
# variable: pod — line 248
# variable: container — line 278
# END CODE MAP

from __future__ import annotations

from typing import Any

from lab.contracts import bounded_tree, integer, record

NAMESPACE = "platform-lab"
KINDS = {"Deployment", "Service", "ServiceAccount", "NetworkPolicy"}


def require(condition: bool, code: str, failures: list[str]) -> None:
    """Record a stable policy code without including any raw manifest value in the report."""
    if not condition:
        failures.append(code)


def scalar_types(value: Any) -> None:
    """Keep Kubernetes bool/integer fields distinct: Python's True == 1 must not bypass a predicate."""
    numbers = {
        "replicas",
        "revisionHistoryLimit",
        "progressDeadlineSeconds",
        "maxSurge",
        "maxUnavailable",
        "terminationGracePeriodSeconds",
        "runAsUser",
        "runAsGroup",
        "containerPort",
        "periodSeconds",
        "timeoutSeconds",
        "failureThreshold",
    }
    booleans = {
        "automountServiceAccountToken",
        "runAsNonRoot",
        "allowPrivilegeEscalation",
        "readOnlyRootFilesystem",
    }
    if isinstance(value, dict):
        for key, child in value.items():
            if (
                key in numbers
                and type(child) is not int
                or key in booleans
                and type(child) is not bool
            ):
                raise ValueError("incorrect scalar type")
            scalar_types(child)
    elif isinstance(value, list):
        for child in value:
            scalar_types(child)


def audit(documents: list[dict[str, Any]]) -> dict[str, Any]:
    """Check exact resource inventory, restricted pod fields, probes, RBAC identity and netpol semantics."""
    failures: list[str] = []
    inventory: dict[tuple[str, str], dict[str, Any]] = {}
    try:
        bounded_tree(documents)
        scalar_types(documents)
        if len(documents) != 5:
            raise ValueError("unexpected resource count")
        for item in documents:
            if item.get("kind") not in KINDS:
                raise ValueError("kind not permitted")
            metadata = record(item["metadata"], {"name", "namespace"})
            require(metadata["namespace"] == NAMESPACE, "resource.namespace", failures)
            identity = (item["kind"], metadata["name"])
            if identity in inventory:
                raise ValueError("duplicate resource")
            inventory[identity] = item
        if set(inventory) != {
            ("Deployment", "sre"),
            ("Service", "sre"),
            ("ServiceAccount", "workload"),
            ("NetworkPolicy", "default-deny"),
            ("NetworkPolicy", "reviewer-ingress"),
        }:
            raise ValueError("unexpected identity")
        deployment(inventory[("Deployment", "sre")], failures)
        service = record(
            inventory[("Service", "sre")], {"apiVersion", "kind", "metadata", "spec"}
        )
        require(
            service["apiVersion"] == "v1"
            and service["spec"]
            == {
                "type": "ClusterIP",
                "selector": {"app": "sre"},
                "ports": [
                    {
                        "name": "http",
                        "port": 8080,
                        "targetPort": "http",
                        "protocol": "TCP",
                    }
                ],
            },
            "service.private",
            failures,
        )
        account = record(
            inventory[("ServiceAccount", "workload")],
            {"apiVersion", "kind", "metadata", "automountServiceAccountToken"},
        )
        require(
            account["apiVersion"] == "v1"
            and account["automountServiceAccountToken"] is False,
            "account.token",
            failures,
        )
        default = record(
            inventory[("NetworkPolicy", "default-deny")],
            {"apiVersion", "kind", "metadata", "spec"},
        )
        require(
            default["apiVersion"] == "networking.k8s.io/v1"
            and default["spec"]
            == {
                "podSelector": {},
                "policyTypes": ["Ingress", "Egress"],
            },
            "network.default-deny",
            failures,
        )
        ingress = record(
            inventory[("NetworkPolicy", "reviewer-ingress")],
            {"apiVersion", "kind", "metadata", "spec"},
        )
        require(
            ingress["apiVersion"] == "networking.k8s.io/v1"
            and ingress["spec"]
            == {
                "podSelector": {"matchLabels": {"app": "sre"}},
                "policyTypes": ["Ingress"],
                "ingress": [
                    {
                        "from": [
                            {
                                "namespaceSelector": {
                                    "matchLabels": {"gitops.platform/client": "allowed"}
                                },
                                "podSelector": {"matchLabels": {"role": "reviewer"}},
                            }
                        ],
                        "ports": [{"protocol": "TCP", "port": 8080}],
                    }
                ],
            },
            "network.and-selectors",
            failures,
        )
    except (KeyError, TypeError, ValueError):
        failures.append("contract.invalid")
    return {
        "author": "Jason Stys",
        "scope": "closed synthetic Helm chart",
        "resources": len(documents),
        "decision": "DENY" if failures else "ALLOW",
        "failures": sorted(set(failures)),
        "live_enforcement_proven": False,
    }


def deployment(raw: dict[str, Any], failures: list[str]) -> None:
    """Validate one bounded Deployment; additional container/host/volume fields fail closed."""
    item = record(raw, {"apiVersion", "kind", "metadata", "spec"})
    require(item["apiVersion"] == "apps/v1", "deployment.version", failures)
    spec = record(
        item["spec"],
        {
            "replicas",
            "revisionHistoryLimit",
            "progressDeadlineSeconds",
            "strategy",
            "selector",
            "template",
        },
    )
    integer(spec["replicas"], 1, 3)
    require(
        spec["revisionHistoryLimit"] == 3 and spec["progressDeadlineSeconds"] == 60,
        "deployment.bounds",
        failures,
    )
    require(
        spec["strategy"]
        == {
            "type": "RollingUpdate",
            "rollingUpdate": {"maxSurge": 1, "maxUnavailable": 0},
        },
        "deployment.rollout",
        failures,
    )
    require(
        spec["selector"] == {"matchLabels": {"app": "sre"}},
        "deployment.selector",
        failures,
    )
    template = record(spec["template"], {"metadata", "spec"})
    metadata = record(template["metadata"], {"labels", "annotations"})
    require(metadata["labels"] == {"app": "sre"}, "deployment.labels", failures)
    annotations = record(metadata["annotations"], {"gitops.platform/revision"})
    require(
        annotations["gitops.platform/revision"]
        in {"baseline", "promoted", "recovered"},
        "deployment.reviewed-revision",
        failures,
    )
    pod = record(
        template["spec"],
        {
            "serviceAccountName",
            "automountServiceAccountToken",
            "terminationGracePeriodSeconds",
            "securityContext",
            "containers",
        },
    )
    require(
        pod["serviceAccountName"] == "workload"
        and pod["automountServiceAccountToken"] is False,
        "pod.identity",
        failures,
    )
    require(pod["terminationGracePeriodSeconds"] == 5, "pod.shutdown", failures)
    require(
        pod["securityContext"]
        == {
            "runAsNonRoot": True,
            "runAsUser": 10001,
            "runAsGroup": 10001,
            "seccompProfile": {"type": "RuntimeDefault"},
        },
        "pod.security",
        failures,
    )
    if not isinstance(pod["containers"], list) or len(pod["containers"]) != 1:
        raise ValueError("one container required")
    container = record(
        pod["containers"][0],
        {
            "name",
            "image",
            "imagePullPolicy",
            "args",
            "ports",
            "securityContext",
            "resources",
            "readinessProbe",
            "livenessProbe",
        },
    )
    require(
        container["name"] == "sre"
        and container["image"] == "gitops-sre:lab"
        and container["imagePullPolicy"] == "Never"
        and container["args"] == ["--pod"],
        "container.owned-image",
        failures,
    )
    require(
        container["ports"] == [{"name": "http", "containerPort": 8080}],
        "container.port",
        failures,
    )
    require(
        container["securityContext"]
        == {
            "allowPrivilegeEscalation": False,
            "readOnlyRootFilesystem": True,
            "capabilities": {"drop": ["ALL"]},
        },
        "container.security",
        failures,
    )
    require(
        container["resources"]
        == {
            "requests": {"cpu": "50m", "memory": "32Mi"},
            "limits": {"cpu": "500m", "memory": "128Mi"},
        },
        "container.resources",
        failures,
    )
    require(
        container["readinessProbe"]
        == {
            "httpGet": {"path": "/health", "port": "http"},
            "periodSeconds": 2,
            "timeoutSeconds": 1,
            "failureThreshold": 2,
        },
        "container.readiness",
        failures,
    )
    require(
        container["livenessProbe"]
        == {
            "httpGet": {"path": "/health", "port": "http"},
            "periodSeconds": 5,
            "timeoutSeconds": 1,
            "failureThreshold": 3,
        },
        "container.liveness",
        failures,
    )
