# GitOps Platform Lab

[![Validate](https://github.com/JasonStys/gitops-platform-lab/actions/workflows/ci.yml/badge.svg)](https://github.com/JasonStys/gitops-platform-lab/actions/workflows/ci.yml)
[![CodeQL](https://github.com/JasonStys/gitops-platform-lab/actions/workflows/codeql.yml/badge.svg)](https://github.com/JasonStys/gitops-platform-lab/actions/workflows/codeql.yml)

A runnable, disposable Kubernetes lab that proves Git reconciliation, drift repair, scoped service identities, actual NetworkPolicy enforcement and failed-release recovery. Created by **[Jason Stys](https://github.com/JasonStys)** · [Professional contact](https://www.linkedin.com/in/jason-stys-31b30b351/).

## Features

- **Real GitOps:** Flux source/kustomize/helm controllers read a synthetic Git repository, apply namespace-scoped Helm releases, consume exact commits, and restore a deliberately drifted replica count.
- **Existing portfolio workload:** an unchanged, hash-pinned SRE analyzer from [SRE Observability Workbench](https://github.com/JasonStys/sre-observability-workbench/tree/3bbe2f4fde0cd82c91ef0946a0c6dd3bed60dc39), wrapped in a dependency-free, fixed-route synthetic HTTP service. `/health` proves readiness; `/work` runs its actual 40-event SLO calculation.
- **Layered controls:** a closed Helm values schema and independent rendered-resource policy; non-root/read-only/capability-dropped pods; no runtime API token; namespace-scoped reconciliation/delivery service accounts; restricted Pod Security admission.
- **Live networking proof:** a default-deny policy with namespace **AND** pod-label ingress selectors. Denial requires an eligible transport observation plus an increase in scoped live REJECT counters, a verified probe exit, and healthy HTTP controls before/after. Refusal, timeout or DNS failure alone cannot pass. Positive new-Pod onboarding is bounded and its attempt count is reported; negative probes never retry. This is a readiness check, not an instant first-request SLA.
- **Recovery:** a deliberately bad scratch Git revision fails readiness; actual Helm history retains the failed revision and a successful rollback. A later healthy Git commit resolves the failed intent. The public repository never adopts the bad configuration.
- **Evidence and delivery:** bounded parsers, real native HTTP/Git tests, negative/property cases, strict types/lint, native Helm validation, measured benchmarks, inert HTML/JSON reports, hash-pinned tools and storage-free Actions workflows.

This is an educational **single-node disposable lab**, not a production cluster, managed cloud deployment, identity-authenticated business service, compliance certification or universal network-security guarantee. Bootstrap administrators and Flux's installation-level controllers remain trusted. Local Docker Desktop is not repaired or started by native validation.

## Quick start: no Docker needed

Requirements: Python 3.12+. From the repository root on Windows:

```powershell
python -m venv .venv
.venv/Scripts/python -m pip install --require-hashes -r requirements-dev.lock
.venv/Scripts/python -m pytest --cov --cov-report=term-missing
.venv/Scripts/python scripts/bootstrap.py helm-windows
.venv/Scripts/python scripts/manifest_check.py
.venv/Scripts/python scripts/benchmark.py
```

On Linux replace `.venv/Scripts/python` with `.venv/bin/python` and use `helm-linux`. macOS runs the native Python suite; this bootstrap intentionally supports only the reviewed Windows/Linux amd64 Helm artifacts. No unsupported platform is described as a native Helm test.

Inspect offline policy decisions with `python -m lab audit path/to/rendered.yml`. ALLOW exits 0, DENY exits 1, malformed/unreadable input exits 2. Only this chart's closed five-resource inventory is supported; this is not a general-purpose Kubernetes policy engine.

Run the adapter locally with `python -m workload.server`, then visit `http://127.0.0.1:8080/work`. Ctrl+C stops it. The `--pod` bind is only for an owned disposable pod; never expose this unauthenticated synthetic service on a shared host. No user uploads, account data or AI/provider credentials exist.

## Actual disposable cluster drill

Use the **cluster job in [GitHub Actions](https://github.com/JasonStys/gitops-platform-lab/actions)**, or a dedicated Linux amd64 Docker host with no existing k3d clusters:

```bash
python scripts/bootstrap.py helm-linux
python scripts/bootstrap.py flux-linux
python scripts/bootstrap.py k3d-linux
python scripts/bootstrap.py kubectl-linux
python scripts/cluster_drill.py --output out/my-first-drill --ack-disposable-docker
```

The script refuses non-Linux/remote Docker contexts, creates one uniquely named cluster with a loopback API, uses a private kubeconfig, binds a read-only synthetic Git HTTP source to its private Docker bridge and cleans up only its own cluster/process. It never pushes scratch commits to GitHub. Output directories must be new, preserving prior evidence.

Open `out/my-first-drill/report/drill.html` or inspect the JSON. The workload image is built from the reviewed source and digest-pinned base, imported locally, and uses `imagePullPolicy: Never`. Its fixed `gitops-sre:lab` tag is a disposable-lab convenience, **not** an immutable production image reference or provenance signature. The report records the actual built configuration digest. Promote signed OCI digest references and authenticated HTTPS sources before designing a production adaptation.

## Documentation and verification

[Architecture/ADR](docs/architecture.md) · [runbook](docs/runbook.md) · [contracts](docs/contracts.md) · [test strategy](docs/testing.md) · [measured reports](docs/reports/validation.md) · [security boundary](SECURITY.md) · [primary sources](docs/research.md).

The architecture, testing and review guidance shaped the closed chart, explicit ownership guard, negative tests and observed-state acceptance criteria. Source-file headers include exact maintained definitions/parameters/variable maps; functions/classes explain their contracts. JSON/vendor bytes keep their native format and are individually described below. See [contribution conventions](CONTRIBUTING.md).

## Every tracked file

<!-- BEGIN FILE GUIDE -->

| File | Purpose |
| --- | --- |
| [.dockerignore](.dockerignore) | Only the reviewed runtime adapter and pinned analyzer enter the image context. |
| [.gitattributes](.gitattributes) | Portable LF text handling. |
| [.github/workflows/ci.yml](.github/workflows/ci.yml) | Jason Stys: strict cross-platform tests, native Helm, real isolated Flux/K3s enforcement and security. |
| [.github/workflows/codeql.yml](.github/workflows/codeql.yml) | Jason Stys: security-extended Python analysis; no database/Actions artifact uploads. |
| [.gitignore](.gitignore) | Excludes local tools, evidence, kubeconfigs, secrets and caches. |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Contribution and coding conventions. |
| [Dockerfile](Dockerfile) | Dependency-free adapter of Jason Stys's pinned SRE analyzer; non-root, no credentials. |
| [LICENSE](LICENSE) | MIT license for authored code. |
| [README.md](README.md) | GitOps Platform Lab. |
| [SECURITY.md](SECURITY.md) | Security boundary and reporting. |
| [chart/Chart.yaml](chart/Chart.yaml) | Namespaced educational SRE workload, packaged for real Helm reconciliation. Jason Stys. |
| [chart/templates/account.yaml](chart/templates/account.yaml) | Runtime identity has no RoleBinding and no automatically mounted credential. Jason Stys. |
| [chart/templates/deployment.yaml](chart/templates/deployment.yaml) | One restricted workload; image/replica/readiness/revision values are schema-bounded. Jason Stys. |
| [chart/templates/network.yaml](chart/templates/network.yaml) | Default deny plus namespace AND pod label ingress allow; runtime has no egress. Jason Stys. |
| [chart/templates/service.yaml](chart/templates/service.yaml) | Cluster-internal service only; no public ingress or host port. Jason Stys. |
| [chart/values.schema.json](chart/values.schema.json) | Closed native Helm schema with replica/image/readiness/revision limits. |
| [chart/values.yaml](chart/values.yaml) | Closed lab parameters. The local CI image is built/imported, never remotely pulled. Jason Stys. |
| [docs/architecture.md](docs/architecture.md) | ADR-001: an observed, disposable GitOps platform. |
| [docs/contracts.md](docs/contracts.md) | Configuration and evidence contracts. |
| [docs/reports/benchmark.json](docs/reports/benchmark.json) | Measured warm bounded parsing and policy-audit timing/allocation. |
| [docs/reports/ci.json](docs/reports/ci.json) | Verified immutable executable-source CI snapshot and completed job results. |
| [docs/reports/drill.html](docs/reports/drill.html) | Escaped inert HTML rendering of the measured synthetic drill. |
| [docs/reports/drill.json](docs/reports/drill.json) | Actual disposable-cluster Git/RBAC/network/drift/rollback measurements. |
| [docs/reports/manifest.json](docs/reports/manifest.json) | Actual ten-case native Helm schema/render validation. |
| [docs/reports/validation.md](docs/reports/validation.md) | Measured validation and author review. |
| [docs/research.md](docs/research.md) | Primary sources and implementation rationale. |
| [docs/runbook.md](docs/runbook.md) | Operating and recovery runbook. |
| [docs/testing.md](docs/testing.md) | Risk-based validation strategy. |
| [examples/rendered.json](examples/rendered.json) | Actual native Helm render, reproduced and compared by manifest checks. |
| [gitops/kustomization.yml](gitops/kustomization.yml) | Reviewed Git path: one HelmRelease, never cluster-scoped bootstrap permissions. Jason Stys. |
| [gitops/release.yml](gitops/release.yml) | Namespace-scoped Helm delivery with drift repair and final-failure rollback. Jason Stys. |
| [lab/\_\_init\_\_.py](lab/__init__.py) | Bounded offline manifest and measured GitOps evidence tools. Created by Jason Stys. |
| [lab/\_\_main\_\_.py](lab/__main__.py) | Offline policy/report CLI; arbitrary files are not executed or sent anywhere. Jason Stys. |
| [lab/contracts.py](lab/contracts.py) | Strict bounded document loading; inputs are data, never commands. Created by Jason Stys. |
| [lab/evidence.py](lab/evidence.py) | Closed measured drill reports and inert HTML publication, never cluster secrets. Jason Stys. |
| [lab/network.py](lab/network.py) | Observed K3s denial requires transport, active scoped rule counters and external controls. Jason Stys. |
| [lab/policy.py](lab/policy.py) | Fail-closed policies for this one closed Helm workload, not arbitrary Kubernetes. Jason Stys. |
| [ops/bootstrap.yml](ops/bootstrap.yml) | Administrator-only disposable bootstrap, outside the reviewed workload Git path. Jason Stys. |
| [ops/sync.yml](ops/sync.yml) | Public HTTPS source template; disposable drill replaces only the owned source URL. Jason Stys. |
| [pyproject.toml](pyproject.toml) | Strict types, lint, cross-platform tests and branch-inclusive coverage gate. |
| [requirements-dev.in](requirements-dev.in) | Exact validation dependencies plus the runtime graph. |
| [requirements-dev.lock](requirements-dev.lock) | Complete hash-pinned portable validation graph. |
| [requirements.in](requirements.in) | Exact runtime manifest-validation dependencies. |
| [requirements.lock](requirements.lock) | Complete hash-pinned portable runtime dependency graph. |
| [scripts/benchmark.py](scripts/benchmark.py) | Informational warmed policy parsing/audit benchmark with an actual correctness oracle. Jason Stys. |
| [scripts/bootstrap.py](scripts/bootstrap.py) | Install explicit hash-pinned official tools without shell installers or unsafe extraction. Jason Stys. |
| [scripts/cluster\_drill.py](scripts/cluster_drill.py) | Actual disposable K3s/Flux/Helm Git, policy, drift and rollback drill. Created by Jason Stys. |
| [scripts/code\_map.py](scripts/code_map.py) | Generate/check exact Python, SQL, shell and YAML symbol positions. Created by Jason Stys. |
| [scripts/file\_guide.py](scripts/file_guide.py) | Generate exhaustive Git-tracked README summaries without including ignored runtime data. Jason Stys. |
| [scripts/git\_server.py](scripts/git_server.py) | Read-only bounded smart HTTP Git service for owned synthetic CI repositories. Created by Jason Stys. |
| [scripts/manifest\_check.py](scripts/manifest_check.py) | Actual native Helm schema/render tests and deterministic measured example maintenance. Jason Stys. |
| [scripts/scanners.py](scripts/scanners.py) | Install only hash-pinned official Linux scanner binaries. Created by Jason Stys. |
| [scripts/validate.sh](scripts/validate.sh) | Strict portable tests and documentation/source invariants. Created by Jason Stys. |
| [scripts/validate\_repo.py](scripts/validate_repo.py) | Verify untouched upstream source, workflow permissions/storage rules and reviewed release contracts. Jason Stys. |
| [tests/\_\_init\_\_.py](tests/__init__.py) | Synthetic tests by Jason Stys; fixtures are not measured cluster reports. |
| [tests/conftest.py](tests/conftest.py) | Private per-test fixtures, with real Helm-rendered resources and explicitly fake report inputs. Jason Stys. |
| [tests/test\_cluster\_guards.py](tests/test_cluster_guards.py) | Native context/port guard regressions; no Docker or existing Kubernetes cluster is touched. Jason Stys. |
| [tests/test\_contracts.py](tests/test_contracts.py) | Duplicate/alias/type/file/UTF8/size/nesting adversarial inputs and normal parser boundaries. Jason Stys. |
| [tests/test\_evidence.py](tests/test_evidence.py) | Incomplete/false success, fingerprint, report-escaping and CLI privacy regression tests. Jason Stys. |
| [tests/test\_git\_server.py](tests/test_git_server.py) | Real clone/fetch proof for isolated read-only smart HTTP Git; endpoints never accept pushes. Jason Stys. |
| [tests/test\_network.py](tests/test_network.py) | Negative oracles: refusal/timeout alone never prove policy; counts and positive controls are mandatory. Jason Stys. |
| [tests/test\_policy.py](tests/test_policy.py) | Negative security-policy cases, type boundaries, selector semantics and randomized replicas. Jason Stys. |
| [tests/test\_workload.py](tests/test_workload.py) | Real loopback HTTP, route privacy, bounded server and provisional transport/acknowledgement tests. Jason Stys. |
| [tools.lock.json](tools.lock.json) | Official tool archive hashes and immutable K3s image digest. |
| [upstream.lock.json](upstream.lock.json) | Exact SRE repository revision and byte digests of reused source/notice. |
| [vendor/LICENSE](vendor/LICENSE) | Intact MIT notice for the pinned existing SRE analyzer. |
| [vendor/sre/\_\_init\_\_.py](vendor/sre/__init__.py) | Local synthetic SRE workbench. Created by Jason Stys; https://github.com/JasonStys. |
| [vendor/sre/slo.py](vendor/sre/slo.py) | Validate client evidence and calculate exact request-based SLOs. Created by Jason Stys. |
| [workload/\_\_init\_\_.py](workload/__init__.py) | Dependency-free pod adapter for the pinned SRE analyzer. Created by Jason Stys. |
| [workload/server.py](workload/server.py) | Fixed synthetic SRE HTTP workload and exact-owned-service connectivity probe. Jason Stys. |

<!-- END FILE GUIDE -->
