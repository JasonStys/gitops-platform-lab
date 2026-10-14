"""Actual disposable K3s/Flux/Helm Git, policy, drift and rollback drill. Created by Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 174
# definition: loopback_port — line 179
# variable: reservation — line 181
# definition: validate_config — line 186
# parameter: cluster — line 186
# parameter: content — line 186
# parameter: port — line 186
# variable: config — line 188
# variable: expected — line 189
# variable: clusters — line 196
# variable: contexts — line 197
# definition: Drill — line 212
# definition: __init__ — line 215
# parameter: output — line 215
# parameter: self — line 215
# definition: run — line 229
# parameter: self — line 230
# parameter: args — line 231
# parameter: cwd — line 233
# parameter: data — line 234
# parameter: valid — line 235
# parameter: timeout — line 236
# parameter: include_error — line 237
# variable: executable — line 240
# variable: command — line 241
# variable: completed — line 242
# definition: kube — line 263
# parameter: args — line 264
# parameter: data — line 264
# parameter: self — line 264
# parameter: valid — line 264
# definition: get — line 273
# parameter: kind — line 274
# parameter: name — line 274
# parameter: namespace — line 274
# parameter: self — line 274
# variable: output — line 277
# definition: wait — line 282
# parameter: predicate — line 282
# parameter: self — line 282
# parameter: timeout — line 282
# variable: deadline — line 284
# definition: check — line 291
# parameter: evidence — line 291
# parameter: name — line 291
# parameter: self — line 291
# parameter: started — line 291
# variable: item — line 293
# definition: commit — line 304
# parameter: path — line 304
# parameter: replicas — line 304
# parameter: revision — line 304
# parameter: self — line 304
# variable: target — line 306
# variable: release — line 307
# definition: ready — line 319
# parameter: replicas — line 319
# parameter: revision — line 319
# parameter: self — line 319
# variable: deployment — line 321
# variable: spec — line 324
# variable: status — line 324
# variable: helm — line 325
# variable: conditions — line 328
# variable: item — line 339
# definition: source_seen — line 343
# parameter: commit — line 343
# parameter: self — line 343
# variable: revision — line 345
# definition: network — line 353
# parameter: expected — line 353
# parameter: namespace — line 353
# parameter: role — line 353
# parameter: self — line 353
# variable: name — line 355
# variable: pod — line 356
# variable: before — line 393
# variable: result — line 402
# variable: logs — line 403
# variable: proof — line 418
# definition: reject_count — line 429
# parameter: self — line 429
# variable: source — line 431
# variable: counts — line 440
# variable: line — line 441
# variable: match — line 447
# definition: bootstrap — line 454
# parameter: self — line 454
# variable: started — line 456
# variable: endpoint — line 457
# variable: lock — line 466
# variable: api_port — line 469
# variable: kubeconfig — line 493
# variable: image_id — line 498
# variable: controllers — line 510
# variable: controller — line 521
# variable: account — line 534
# variable: controller — line 534
# variable: current — line 538
# variable: args — line 539
# variable: args — line 540
# variable: folder — line 571
# variable: bare — line 574
# variable: commit — line 588
# variable: network — line 589
# variable: gateway — line 592
# variable: sync — line 610
# definition: execute — line 628
# parameter: self — line 628
# variable: image_id — line 630
# variable: started — line 631
# variable: promotion — line 632
# variable: started — line 637
# variable: started — line 645
# variable: account — line 646
# variable: expected — line 646
# variable: namespace — line 646
# variable: resource — line 646
# variable: verb — line 646
# variable: result — line 660
# variable: expected — line 683
# variable: namespace — line 683
# variable: role — line 683
# variable: scenario — line 683
# variable: started — line 688
# variable: proof — line 689
# variable: started — line 693
# variable: unsafe — line 694
# variable: result — line 708
# variable: started — line 731
# variable: broken — line 732
# variable: item — line 741
# variable: history — line 755
# variable: item — line 759
# variable: started — line 774
# variable: recovery — line 775
# variable: report — line 782
# definition: close — line 797
# parameter: self — line 797
# definition: diagnostics — line 809
# parameter: self — line 809
# variable: kind — line 813
# variable: name — line 813
# variable: item — line 820
# variable: conditions — line 821
# variable: key — line 829
# variable: condition — line 831
# definition: main — line 844
# variable: parser — line 846
# variable: args — line 849
# variable: drill — line 854
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
        before = self.reject_count() if expected == "deny" else 0
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
            if expected == "deny":
                print(
                    json.dumps(
                        {
                            "diagnostic_network": "denied-probe",
                            "reject_packets_before": before,
                            "reject_packets_after": self.reject_count(),
                            "probe": json.loads(logs),
                        }
                    ),
                    flush=True,
                )
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

    def reject_count(self) -> int:
        """Measure only this workload namespace's actual kube-router REJECT rule packet counters on the owned node."""
        source = self.run(
            [
                "docker",
                "exec",
                "k3d-" + self.cluster + "-server-0",
                "iptables-save",
                "-c",
            ]
        )
        counts = []
        for line in source.splitlines():
            if (
                "KUBE-POD-FW-" in line
                and "namespace: platform-lab" in line
                and "-j REJECT" in line
            ):
                match = re.match(r"\[(\d+):\d+\]", line)
                if match:
                    counts.append(int(match.group(1)))
        if not counts:
            raise ValueError("required workload REJECT counters unavailable")
        return sum(counts)

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
