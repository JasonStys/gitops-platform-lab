"""Actual disposable K3s/Flux/Helm Git, policy, drift and rollback drill. Created by Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 146
# definition: Drill — line 151
# definition: __init__ — line 154
# parameter: output — line 154
# parameter: self — line 154
# definition: run — line 168
# parameter: self — line 169
# parameter: args — line 170
# parameter: cwd — line 172
# parameter: data — line 173
# parameter: valid — line 174
# parameter: timeout — line 175
# parameter: include_error — line 176
# variable: executable — line 179
# variable: command — line 180
# variable: completed — line 181
# definition: kube — line 202
# parameter: args — line 203
# parameter: data — line 203
# parameter: self — line 203
# parameter: valid — line 203
# definition: get — line 212
# parameter: kind — line 213
# parameter: name — line 213
# parameter: namespace — line 213
# parameter: self — line 213
# variable: output — line 216
# definition: wait — line 221
# parameter: predicate — line 221
# parameter: self — line 221
# parameter: timeout — line 221
# variable: deadline — line 223
# definition: check — line 230
# parameter: evidence — line 230
# parameter: name — line 230
# parameter: self — line 230
# parameter: started — line 230
# variable: item — line 232
# definition: commit — line 243
# parameter: path — line 243
# parameter: replicas — line 243
# parameter: revision — line 243
# parameter: self — line 243
# variable: target — line 245
# variable: release — line 246
# definition: ready — line 258
# parameter: replicas — line 258
# parameter: revision — line 258
# parameter: self — line 258
# variable: deployment — line 260
# variable: spec — line 263
# variable: status — line 263
# variable: helm — line 264
# variable: conditions — line 267
# variable: item — line 278
# definition: source_seen — line 282
# parameter: commit — line 282
# parameter: self — line 282
# variable: revision — line 284
# definition: network — line 292
# parameter: expected — line 292
# parameter: namespace — line 292
# parameter: role — line 292
# parameter: self — line 292
# variable: name — line 294
# variable: pod — line 295
# variable: result — line 340
# variable: logs — line 341
# variable: proof — line 344
# definition: bootstrap — line 355
# parameter: self — line 355
# variable: started — line 357
# variable: endpoint — line 358
# variable: lock — line 367
# variable: image_id — line 398
# variable: controllers — line 410
# variable: controller — line 421
# variable: account — line 434
# variable: controller — line 434
# variable: current — line 438
# variable: args — line 439
# variable: args — line 440
# variable: folder — line 471
# variable: bare — line 474
# variable: commit — line 488
# variable: network — line 489
# variable: gateway — line 492
# variable: sync — line 510
# definition: execute — line 528
# parameter: self — line 528
# variable: image_id — line 530
# variable: started — line 531
# variable: promotion — line 532
# variable: started — line 537
# variable: started — line 545
# variable: account — line 546
# variable: expected — line 546
# variable: namespace — line 546
# variable: resource — line 546
# variable: verb — line 546
# variable: result — line 560
# variable: expected — line 583
# variable: namespace — line 583
# variable: role — line 583
# variable: scenario — line 583
# variable: started — line 588
# variable: proof — line 589
# variable: started — line 593
# variable: unsafe — line 594
# variable: result — line 608
# variable: started — line 631
# variable: broken — line 632
# variable: item — line 641
# variable: history — line 655
# variable: item — line 659
# variable: started — line 674
# variable: recovery — line 675
# variable: report — line 682
# definition: close — line 697
# parameter: self — line 697
# definition: main — line 710
# variable: parser — line 712
# variable: args — line 715
# variable: drill — line 720
# END CODE MAP

from __future__ import annotations

import argparse
import ipaddress
import json
import os
import re
import shutil
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
                "127.0.0.1:0",
                "--kubeconfig-update-default=false",
                "--kubeconfig-switch-context=false",
                "--k3s-arg",
                "--disable=traefik,servicelb,metrics-server@server:*",
            ],
            timeout=240,
        )
        self.created = True
        self.config.write_text(
            self.run(["k3d", "kubeconfig", "get", self.cluster]), encoding="utf-8"
        )
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
        print(
            json.dumps({"result": "FAIL", "completed_cases": drill.checks}), flush=True
        )
        raise
    finally:
        drill.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
