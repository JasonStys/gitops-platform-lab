"""Actual disposable K3s/Flux/Helm Git, policy, drift and rollback drill. Created by Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 167
# definition: loopback_port — line 172
# variable: reservation — line 174
# definition: validate_config — line 179
# parameter: cluster — line 179
# parameter: content — line 179
# parameter: port — line 179
# variable: config — line 181
# variable: expected — line 182
# variable: clusters — line 189
# variable: contexts — line 190
# definition: Drill — line 205
# definition: __init__ — line 208
# parameter: output — line 208
# parameter: self — line 208
# definition: run — line 222
# parameter: self — line 223
# parameter: args — line 224
# parameter: cwd — line 226
# parameter: data — line 227
# parameter: valid — line 228
# parameter: timeout — line 229
# parameter: include_error — line 230
# variable: executable — line 233
# variable: command — line 234
# variable: completed — line 235
# definition: kube — line 256
# parameter: args — line 257
# parameter: data — line 257
# parameter: self — line 257
# parameter: valid — line 257
# definition: get — line 266
# parameter: kind — line 267
# parameter: name — line 267
# parameter: namespace — line 267
# parameter: self — line 267
# variable: output — line 270
# definition: wait — line 275
# parameter: predicate — line 275
# parameter: self — line 275
# parameter: timeout — line 275
# variable: deadline — line 277
# definition: check — line 284
# parameter: evidence — line 284
# parameter: name — line 284
# parameter: self — line 284
# parameter: started — line 284
# variable: item — line 286
# definition: commit — line 297
# parameter: path — line 297
# parameter: replicas — line 297
# parameter: revision — line 297
# parameter: self — line 297
# variable: target — line 299
# variable: release — line 300
# definition: ready — line 312
# parameter: replicas — line 312
# parameter: revision — line 312
# parameter: self — line 312
# variable: deployment — line 314
# variable: spec — line 317
# variable: status — line 317
# variable: helm — line 318
# variable: conditions — line 321
# variable: item — line 332
# definition: source_seen — line 336
# parameter: commit — line 336
# parameter: self — line 336
# variable: revision — line 338
# definition: network — line 346
# parameter: expected — line 346
# parameter: namespace — line 346
# parameter: role — line 346
# parameter: self — line 346
# variable: name — line 348
# variable: pod — line 349
# variable: result — line 394
# variable: logs — line 395
# variable: proof — line 398
# definition: bootstrap — line 409
# parameter: self — line 409
# variable: started — line 411
# variable: endpoint — line 412
# variable: lock — line 421
# variable: api_port — line 424
# variable: kubeconfig — line 448
# variable: image_id — line 453
# variable: controllers — line 465
# variable: controller — line 476
# variable: account — line 489
# variable: controller — line 489
# variable: current — line 493
# variable: args — line 494
# variable: args — line 495
# variable: folder — line 526
# variable: bare — line 529
# variable: commit — line 543
# variable: network — line 544
# variable: gateway — line 547
# variable: sync — line 565
# definition: execute — line 583
# parameter: self — line 583
# variable: image_id — line 585
# variable: started — line 586
# variable: promotion — line 587
# variable: started — line 592
# variable: started — line 600
# variable: account — line 601
# variable: expected — line 601
# variable: namespace — line 601
# variable: resource — line 601
# variable: verb — line 601
# variable: result — line 615
# variable: expected — line 638
# variable: namespace — line 638
# variable: role — line 638
# variable: scenario — line 638
# variable: started — line 643
# variable: proof — line 644
# variable: started — line 648
# variable: unsafe — line 649
# variable: result — line 663
# variable: started — line 686
# variable: broken — line 687
# variable: item — line 696
# variable: history — line 710
# variable: item — line 714
# variable: started — line 729
# variable: recovery — line 730
# variable: report — line 737
# definition: close — line 752
# parameter: self — line 752
# definition: diagnostics — line 764
# parameter: self — line 764
# variable: kind — line 768
# variable: name — line 768
# variable: item — line 775
# variable: conditions — line 776
# variable: key — line 784
# variable: condition — line 786
# definition: main — line 799
# variable: parser — line 801
# variable: args — line 804
# variable: drill — line 809
# END CODE MAP

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import Any

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from lab.evidence import SCENARIOS, publish  # noqa: E402


def loopback_port() -> int:
    """Allocate a concrete ephemeral loopback port; k3d must never export literal port zero."""
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as reservation:
        reservation.bind(("127.0.0.1", 0))
        return int(reservation.getsockname()[1])


def validate_config(content: str, cluster: str, port: int) -> None:
    """Require exactly the owned context and concrete loopback TLS endpoint before any kubectl call."""
    config = yaml.safe_load(content)
    expected = "k3d-" + cluster
    if (
        type(port) is not int
        or not 1 <= port <= 65535
        or config.get("current-context") != expected
    ):
        raise ValueError("unexpected kubeconfig context/port")
    clusters = config.get("clusters", [])
    contexts = config.get("contexts", [])
    if (
        len(clusters) != 1
        or clusters[0]["name"] != expected
        or clusters[0]["cluster"]["server"] != f"https://127.0.0.1:{port}"
    ):
        raise ValueError("unexpected kubeconfig endpoint")
    if (
        len(contexts) != 1
        or contexts[0]["name"] != expected
        or contexts[0]["context"]["cluster"] != expected
    ):
        raise ValueError("unexpected kubeconfig binding")


class Drill:
    """Own exactly one newly created named cluster, private kubeconfig and private-bridge read-only Git daemon."""

    def __init__(self, output: Path) -> None:
        """Refuse overwriting prior evidence; every kube command is bound to this newly created context."""
        self.output = output.resolve()
        self.output.mkdir(parents=True, mode=0o700, exist_ok=False)
        self.cluster = "gitops-lab-" + uuid.uuid4().hex[:10]
        self.created = False
        self.git_daemon: subprocess.Popen[bytes] | None = None
        self.checks: list[dict[str, Any]] = []
        self.config = self.output / "owned.kubeconfig"
        self.env = {**os.environ, "KUBECONFIG": str(self.config)}
        self.tools = ROOT / ".tools"
        self.work = self.output / "checkout"
        self.source = self.output / "source"

    def run(
        self,
        args: list[str],
        *,
        cwd: Path = ROOT,
        data: str | None = None,
        valid: tuple[int, ...] = (0,),
        timeout: int = 180,
        include_error: bool = False,
    ) -> str:
        """Run fixed argv, never a shell; bound time/output and use the dedicated kubeconfig only."""
        executable = self.tools / args[0]
        command = [str(executable) if executable.is_file() else args[0], *args[1:]]
        completed = subprocess.run(
            command,
            cwd=cwd,
            env=self.env,
            input=data,
            text=True,
            encoding="utf-8",
            capture_output=True,
            timeout=timeout,
            check=False,
        )
        if len(completed.stdout) > 1024 * 1024 or len(completed.stderr) > 1024 * 1024:
            raise ValueError("command output exceeded bound")
        if completed.returncode not in valid:
            # Owned, synthetic cluster diagnostics only; kubeconfigs and Secrets are never requested.
            raise RuntimeError(
                f"{args[0]} {args[1] if len(args) > 1 else ''} failed: "
                + completed.stderr[-2000:]
            )
        return completed.stderr if include_error else completed.stdout

    def kube(
        self, *args: str, data: str | None = None, valid: tuple[int, ...] = (0,)
    ) -> str:
        """Always select the owned k3d context, not an inherited current production context."""
        return self.run(
            ["kubectl", "--context", "k3d-" + self.cluster, *args],
            data=data,
            valid=valid,
        )

    def get(
        self, kind: str, name: str, namespace: str = "platform-lab"
    ) -> dict[str, Any]:
        """Read one known non-secret resource's bounded JSON."""
        output = self.kube(
            "get", kind, name, "-n", namespace, "--ignore-not-found", "-o", "json"
        )
        return json.loads(output) if output.strip() else {}

    def wait(self, predicate: Any, timeout: int = 180) -> None:
        """Poll an explicit observed state with a finite deadline; errors are retained, not treated as success."""
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            if predicate():
                return
            time.sleep(2)
        raise TimeoutError("owned cluster did not reach the required observed state")

    def check(self, name: str, started: float, evidence: dict[str, Any]) -> None:
        """Record PASS only after preceding live assertions; do not invent or duplicate a scenario."""
        if name not in SCENARIOS or name in {item["name"] for item in self.checks}:
            raise ValueError("invalid scenario")
        self.checks.append(
            {
                "name": name,
                "result": "PASS",
                "duration_ms": round((time.monotonic() - started) * 1000),
                "evidence": evidence,
            }
        )

    def commit(self, revision: str, replicas: int, path: str) -> str:
        """Commit a reviewable values change into the scratch Git repo and push only to its local bare origin."""
        target = self.work / "gitops/release.yml"
        release = yaml.safe_load(target.read_text(encoding="utf-8"))
        release["spec"]["values"].update(
            revision=revision, replicas=replicas, readinessPath=path
        )
        target.write_text(yaml.safe_dump(release, sort_keys=False), encoding="utf-8")
        self.run(["git", "add", "."], cwd=self.work)
        self.run(
            ["git", "commit", "-m", f"Synthetic review: {revision}"], cwd=self.work
        )
        self.run(["git", "push", "origin", "main"], cwd=self.work)
        return self.run(["git", "rev-parse", "HEAD"], cwd=self.work).strip()

    def ready(self, revision: str, replicas: int) -> bool:
        """Require current generation, exact desired/ready replicas, release annotation and Helm Ready=True."""
        deployment = self.get("deployment", "sre")
        if not deployment:
            return False
        spec, status = deployment["spec"], deployment.get("status", {})
        helm = self.get("helmrelease", "sre")
        if not helm:
            return False
        conditions = helm.get("status", {}).get("conditions", [])
        return (
            spec["replicas"] == replicas
            and status.get("readyReplicas", 0) == replicas
            and status.get("observedGeneration") == deployment["metadata"]["generation"]
            and spec["template"]["metadata"]["annotations"]["gitops.platform/revision"]
            == revision
            and any(
                item["type"] == "Ready"
                and item["status"] == "True"
                and item.get("observedGeneration") == helm["metadata"]["generation"]
                for item in conditions
            )
        )

    def source_seen(self, commit: str) -> bool:
        """Confirm the source controller consumed the exact committed scratch revision, not merely any Ready object."""
        revision = (
            self.get("gitrepository", "platform")
            .get("status", {})
            .get("artifact", {})
            .get("revision", "")
        )
        return revision.endswith(commit)

    def network(self, namespace: str, role: str, expected: str) -> dict[str, str]:
        """Run a bounded restricted probe Pod against the exact owned Service; no exec shell or arbitrary target."""
        name = "probe-" + uuid.uuid4().hex[:8]
        pod = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {
                "name": name,
                "namespace": namespace,
                "labels": {"role": role},
            },
            "spec": {
                "restartPolicy": "Never",
                "activeDeadlineSeconds": 20,
                "automountServiceAccountToken": False,
                "securityContext": {
                    "runAsNonRoot": True,
                    "runAsUser": 10001,
                    "runAsGroup": 10001,
                    "seccompProfile": {"type": "RuntimeDefault"},
                },
                "containers": [
                    {
                        "name": "probe",
                        "image": "gitops-sre:lab",
                        "imagePullPolicy": "Never",
                        "args": ["--probe", expected],
                        "securityContext": {
                            "allowPrivilegeEscalation": False,
                            "readOnlyRootFilesystem": True,
                            "capabilities": {"drop": ["ALL"]},
                        },
                        "resources": {
                            "requests": {"cpu": "20m", "memory": "16Mi"},
                            "limits": {"cpu": "100m", "memory": "64Mi"},
                        },
                    }
                ],
            },
        }
        self.kube("apply", "-f", "-", data=json.dumps(pod))
        self.wait(
            lambda: (
                self.get("pod", name, namespace).get("status", {}).get("phase")
                in {"Succeeded", "Failed"}
            ),
            50,
        )
        result = self.get("pod", name, namespace)
        logs = self.kube("logs", name, "-n", namespace)
        if result["status"]["phase"] != "Succeeded":
            raise AssertionError("live network probe failed: " + logs[-500:])
        proof = json.loads(logs)
        if proof != {
            "outcome": "allowed" if expected == "allow" else "blocked",
            "reason": "http-200" if expected == "allow" else "timeout",
        }:
            raise AssertionError("network proof invalid")
        self.kube(
            "delete", "pod", name, "-n", namespace, "--wait=true", "--timeout=30s"
        )
        return proof

    def bootstrap(self) -> str:
        """Create a fresh cluster with enforcement enabled, build/import the own workload, and start real GitOps."""
        started = time.monotonic()
        endpoint = json.loads(self.run(["docker", "context", "inspect"]))[0][
            "Endpoints"
        ]["docker"]["Host"]
        if endpoint != "unix:///var/run/docker.sock":
            raise ValueError(
                "only an explicit local disposable Linux Docker daemon is supported"
            )
        if json.loads(self.run(["k3d", "cluster", "list", "-o", "json"])):
            raise ValueError("use a fresh daemon with no pre-existing k3d clusters")
        lock = json.loads((ROOT / "tools.lock.json").read_text(encoding="utf-8"))
        # This exact new random name is owned even if creation fails part-way through.
        self.created = True
        api_port = loopback_port()
        self.run(
            [
                "k3d",
                "cluster",
                "create",
                self.cluster,
                "--image",
                lock["k3s_image"],
                "--servers",
                "1",
                "--agents",
                "0",
                "--no-lb",
                "--api-port",
                f"127.0.0.1:{api_port}",
                "--kubeconfig-update-default=false",
                "--kubeconfig-switch-context=false",
                "--k3s-arg",
                "--disable=traefik,servicelb,metrics-server@server:*",
            ],
            timeout=240,
        )
        self.created = True
        kubeconfig = self.run(["k3d", "kubeconfig", "get", self.cluster])
        validate_config(kubeconfig, self.cluster, api_port)
        self.config.write_text(kubeconfig, encoding="utf-8")
        self.config.chmod(0o600)
        self.run(["docker", "build", "-t", "gitops-sre:lab", "."], timeout=240)
        image_id = (
            self.run(
                ["docker", "image", "inspect", "gitops-sre:lab", "--format", "{{.Id}}"]
            )
            .strip()
            .removeprefix("sha256:")
        )
        self.run(
            ["k3d", "image", "import", "gitops-sre:lab", "-c", self.cluster],
            timeout=120,
        )
        self.kube("apply", "-f", str(ROOT / "ops/bootstrap.yml"))
        controllers = self.run(
            [
                "flux",
                "install",
                "--version=v2.9.6",
                "--components=source-controller,kustomize-controller,helm-controller",
                "--export",
            ],
            timeout=90,
        )
        self.kube("apply", "-f", "-", data=controllers)
        for controller in (
            "source-controller",
            "kustomize-controller",
            "helm-controller",
        ):
            self.kube(
                "rollout",
                "status",
                "deployment/" + controller,
                "-n",
                "flux-system",
                "--timeout=120s",
            )
        for controller, account in (
            ("kustomize-controller", "reconciler"),
            ("helm-controller", "delivery"),
        ):
            current = self.get("deployment", controller, "flux-system")
            args = current["spec"]["template"]["spec"]["containers"][0]["args"]
            args += [
                "--no-cross-namespace-refs=true",
                "--default-service-account=" + account,
            ]
            self.kube(
                "patch",
                "deployment",
                controller,
                "-n",
                "flux-system",
                "--type=json",
                "-p",
                json.dumps(
                    [
                        {
                            "op": "replace",
                            "path": "/spec/template/spec/containers/0/args",
                            "value": args,
                        }
                    ]
                ),
            )
            self.kube(
                "rollout",
                "status",
                "deployment/" + controller,
                "-n",
                "flux-system",
                "--timeout=120s",
            )
        self.work.mkdir()
        for folder in ("chart", "gitops"):
            shutil.copytree(ROOT / folder, self.work / folder)
        self.source.mkdir()
        bare = self.source / "repo.git"
        self.run(["git", "init", "--bare", str(bare)])
        self.run(["git", "init", "-b", "main"], cwd=self.work)
        self.run(["git", "config", "user.name", "Jason Stys"], cwd=self.work)
        self.run(
            [
                "git",
                "config",
                "user.email",
                "204414589+JasonStys@users.noreply.github.com",
            ],
            cwd=self.work,
        )
        self.run(["git", "remote", "add", "origin", str(bare)], cwd=self.work)
        commit = self.commit("baseline", 1, "/health")
        network = json.loads(
            self.run(["docker", "network", "inspect", "k3d-" + self.cluster])
        )[0]
        gateway = network["IPAM"]["Config"][0]["Gateway"]
        if not ipaddress.ip_address(gateway).is_private:
            raise ValueError("Git daemon requires private Docker bridge binding")
        self.git_daemon = subprocess.Popen(
            [
                sys.executable,
                str(ROOT / "scripts/git_server.py"),
                "--root",
                str(self.source),
                "--bind",
                gateway,
                "--port",
                "9418",
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            env=self.env,
        )
        sync = list(
            yaml.safe_load_all((ROOT / "ops/sync.yml").read_text(encoding="utf-8"))
        )
        sync[0]["spec"]["url"] = f"http://{gateway}:9418/repo.git"
        self.kube("apply", "-f", "-", data=yaml.safe_dump_all(sync))
        self.wait(lambda: self.source_seen(commit) and self.ready("baseline", 1), 240)
        self.check(
            "bootstrap",
            started,
            {
                "ready_replicas": 1,
                "git_commit": commit,
                "image_pull": "Never",
                "control_plane": "private-loopback",
            },
        )
        return image_id

    def execute(self) -> None:
        """Observe ten distinct live cases; a failed assertion cannot produce a successful published report."""
        image_id = self.bootstrap()
        started = time.monotonic()
        promotion = self.commit("promoted", 2, "/health")
        self.wait(lambda: self.source_seen(promotion) and self.ready("promoted", 2))
        self.check(
            "git_promotion", started, {"git_commit": promotion, "ready_replicas": 2}
        )
        started = time.monotonic()
        self.kube("scale", "deployment/sre", "-n", "platform-lab", "--replicas=3")
        if self.get("deployment", "sre")["spec"]["replicas"] != 3:
            raise AssertionError("drift was not injected")
        self.wait(lambda: self.ready("promoted", 2))
        self.check(
            "drift_repair", started, {"injected_replicas": 3, "restored_replicas": 2}
        )
        started = time.monotonic()
        for account, verb, resource, namespace, expected in (
            ("workload", "get", "secrets", "platform-lab", "no"),
            ("workload", "create", "deployments", "platform-lab", "no"),
            ("delivery", "create", "deployments", "platform-lab", "yes"),
            ("delivery", "get", "secrets", "platform-outsider", "no"),
            (
                "reconciler",
                "create",
                "helmreleases.helm.toolkit.fluxcd.io",
                "platform-lab",
                "yes",
            ),
            ("reconciler", "create", "namespaces", "platform-lab", "no"),
        ):
            result = self.kube(
                "auth",
                "can-i",
                verb,
                resource,
                "-n",
                namespace,
                "--as=system:serviceaccount:platform-lab:" + account,
                valid=(0, 1),
            ).strip()
            if result != expected:
                raise AssertionError(
                    "service account scope differs from required result"
                )
        self.check(
            "namespace_rbac",
            started,
            {
                "assertions": 6,
                "runtime_secret_access": False,
                "cross_namespace_delivery": False,
            },
        )
        for scenario, namespace, role, expected in (
            ("allowed_traffic", "platform-client", "reviewer", "allow"),
            ("blocked_pod_label", "platform-client", "unapproved", "deny"),
            ("blocked_namespace", "platform-outsider", "reviewer", "deny"),
        ):
            started = time.monotonic()
            proof = self.network(namespace, role, expected)
            # Positive control after each denial distinguishes a firewall timeout from a dead service.
            self.network("platform-client", "reviewer", "allow")
            self.check(scenario, started, {**proof, "positive_control_after": True})
        started = time.monotonic()
        unsafe = {
            "apiVersion": "v1",
            "kind": "Pod",
            "metadata": {"name": "unsafe-dry-run", "namespace": "platform-lab"},
            "spec": {
                "containers": [
                    {
                        "name": "unsafe",
                        "image": "gitops-sre:lab",
                        "securityContext": {"privileged": True},
                    }
                ]
            },
        }
        result = self.run(
            [
                "kubectl",
                "--context",
                "k3d-" + self.cluster,
                "apply",
                "--dry-run=server",
                "-f",
                "-",
            ],
            data=json.dumps(unsafe),
            valid=(1,),
            include_error=True,
        )
        if "violates PodSecurity" not in result or "restricted" not in result:
            raise AssertionError(
                "expected explicit restricted PodSecurity admission rejection"
            )
        self.check(
            "psa_rejection",
            started,
            {"server_dry_run": True, "privileged_created": False},
        )
        started = time.monotonic()
        broken = self.commit("broken", 2, "/missing")
        self.wait(lambda: self.source_seen(broken))
        self.wait(
            lambda: any(
                item["type"] == "Remediated"
                and item["status"] == "True"
                and item["reason"] == "RollbackSucceeded"
                and item.get("observedGeneration")
                == self.get("helmrelease", "sre")["metadata"]["generation"]
                for item in self.get("helmrelease", "sre")
                .get("status", {})
                .get("conditions", [])
            ),
            180,
        )
        self.wait(
            lambda: (
                self.get("deployment", "sre")["spec"]["template"]["spec"]["containers"][
                    0
                ]["readinessProbe"]["httpGet"]["path"]
                == "/health"
            )
        )
        history = json.loads(
            self.run(["helm", "history", "sre", "-n", "platform-lab", "-o", "json"])
        )
        if (
            not any(item["status"] == "failed" for item in history)
            or history[-1]["status"] != "deployed"
        ):
            raise AssertionError("actual Helm rollback history missing")
        self.network("platform-client", "reviewer", "allow")
        self.check(
            "failed_release_rollback",
            started,
            {
                "git_commit": broken,
                "reason": "RollbackSucceeded",
                "failed_revision_retained": True,
                "healthy_service_after": True,
            },
        )
        started = time.monotonic()
        recovery = self.commit("recovered", 2, "/health")
        self.wait(lambda: self.source_seen(recovery) and self.ready("recovered", 2))
        self.check(
            "git_recovery_commit",
            started,
            {"git_commit": recovery, "ready_replicas": 2},
        )
        report = {
            "schema": 1,
            "author": "Jason Stys",
            "synthetic": True,
            "source_sha": self.run(["git", "rev-parse", "HEAD"]).strip(),
            "workload_source_sha": json.loads(
                (ROOT / "upstream.lock.json").read_text(encoding="utf-8")
            )["commit"],
            "built_image_id": image_id,
            "cluster": "disposable-k3d",
            "checks": self.checks,
        }
        publish(report, self.output / "report")
        print(json.dumps(report, sort_keys=True))

    def close(self) -> None:
        """Stop the owned Git process and delete only the cluster successfully created by this object."""
        if self.git_daemon is not None:
            self.git_daemon.terminate()
            try:
                self.git_daemon.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.git_daemon.kill()
                self.git_daemon.wait(timeout=5)
        if self.created and re.fullmatch(r"gitops-lab-[0-9a-f]{10}", self.cluster):
            self.run(["k3d", "cluster", "delete", self.cluster], timeout=90)

    def diagnostics(self) -> None:
        """Print only known synthetic non-secret resource conditions on failure; never request a kubeconfig/Secret."""
        if not self.config.is_file():
            return
        for kind, name in (
            ("gitrepository", "platform"),
            ("kustomization", "platform"),
            ("helmrelease", "sre"),
            ("deployment", "sre"),
        ):
            try:
                item = self.get(kind, name)
                conditions = item.get("status", {}).get("conditions", [])
                print(
                    json.dumps(
                        {
                            "diagnostic_kind": kind,
                            "conditions": [
                                {
                                    key: str(condition.get(key, ""))[:500]
                                    for key in ("type", "status", "reason", "message")
                                }
                                for condition in conditions[:8]
                            ],
                        }
                    ),
                    flush=True,
                )
            except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
                print(
                    json.dumps({"diagnostic_kind": kind, "state": "unavailable"}),
                    flush=True,
                )


def main() -> int:
    """Run only on an explicitly acknowledged disposable Linux Docker host; never repair a local runtime."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--ack-disposable-docker", action="store_true", required=True)
    args = parser.parse_args()
    if sys.platform != "linux":
        parser.error(
            "use the disposable Linux GitHub Actions runner; local Docker remains unchanged"
        )
    drill = Drill(args.output)
    try:
        drill.execute()
    except Exception:
        drill.diagnostics()
        print(
            json.dumps({"result": "FAIL", "completed_cases": drill.checks}), flush=True
        )
        raise
    finally:
        drill.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
