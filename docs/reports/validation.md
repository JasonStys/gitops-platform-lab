# Measured validation and author review

Author: Jason Stys. Native Windows validation on 2026-10-13 and actual hosted validation on 2026-10-14 UTC: 138 tests pass with 99.25% combined statement/branch coverage of authored `lab`/`workload`, no skips/exclusions. Strict Ruff/mypy pass. Ten real native Helm cases pass (three accepted/seven rejected), including bool quota and unknown/external values. Real smart-HTTP shallow Git clone/read-only endpoint tests and actual SRE HTTP calculation pass.

The actual warmed parse/audit [benchmark](benchmark.json) records five batches of 100 decisions, five resources/decision, with a correctness oracle: median 0.662 ms/decision and peak Python allocation 37,109 bytes on Windows/Python 3.14.6. Timing is informational and excludes cluster/Helm/network startup. Native Helm results are recorded in [manifest.json](manifest.json). These particular files do not assert live cluster enforcement; that evidence is separate below.

Author-led security review covers explicit ownership/context, read-only private-bridge Git, bounded input/routes, bool/int distinctions, pod/API identities, selector AND semantics, transport-plus-counter denials with positive controls, specific PSA errors, exact revision/generation and retained rollback history. Performance review covers bounded tree traversal, constant inventory joins, handler/thread/subprocess deadlines and resource quotas. Correctness review distinguishes healthy deployed pods from a failed desired Git revision. No independent audit, production deployment or certification is claimed.

Prototype review corrected unsupported Git-daemon source design to Flux-compatible real smart HTTP, transient absent-resource handling and the PSA oracle so unrelated errors cannot claim admission enforcement. YAML `on` keys are preserved rather than coerced by a YAML 1.1 bool resolver. Private/temp test data is not published as measured cluster evidence.

## Verified executable-source CI

Source [055222e584c483ad4f195b087e32bd82cb5d0a30](https://github.com/JasonStys/gitops-platform-lab/commit/055222e584c483ad4f195b087e32bd82cb5d0a30) passed every actual job in [Validate run 38492293844](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38492293844), completed 2026-10-14T00:53:50Z. Each Ubuntu 3.12/3.14, Windows 3.14 and macOS Intel 3.14 lane independently logged 138 passing tests and 99.25% statement/branch coverage. The dedicated Helm job passed the real ten-case matrix. The security job passed complete runtime/dev advisory audits, Gitleaks history, actionlint and ShellCheck with no advisory suppression or gate reductions.

[CodeQL run 38492293884](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38492293884) passed security-extended Python analysis; the open-alert API returned zero findings at 2026-10-14T00:55:08Z. [ci.json](ci.json) records this immutable executable-source snapshot. Current README badges/Actions show the documentation-only follow-up, which must pass the same workflows before final acceptance; no self-referential commit hash is fabricated.

## Actual disposable cluster measurements

[drill.json](drill.json) is the actual aggregate extracted from the completed cluster job, not a unit fixture. [drill.html](drill.html) is generated from that validated aggregate. The built image configuration digest is `201849adcd52842a645901824621f26430692f8520d16ff2b5768ff68dd5f179`; it is not an OCI signature or authenticity certificate.

| Case | Observed evidence | Duration ms |
| --- | --- | --- |
| Bootstrap | Exact baseline Git revision, one Ready replica, loopback API | 68,372 |
| Git promotion | Exact promoted revision, two Ready replicas | 14,585 |
| Drift repair | API receipt accepted replicas=3; observed restoration to 2 | 12,475 |
| Namespace RBAC | Six actual can-i assertions; no runtime Secret or cross-namespace delivery access | 181 |
| Allowed traffic | Exact HTTP 200 and successful follow-up control | 8,973 |
| Wrong pod label | Refusal plus scoped REJECT packets 0→1, verified exit and healthy follow-up | 11,187 |
| Wrong namespace | Refusal plus scoped REJECT packets 0→1, verified exit and healthy follow-up | 9,234 |
| Pod Security admission | Specific restricted admission denial; privileged Pod never created | 595 |
| Failed upgrade rollback | Current RollbackSucceeded condition, retained failed Helm revision, restored health | 59,585 |
| Later Git recovery | Exact recovered revision, two Ready replicas and current Helm Ready | 56,239 |

The actual built workload image scan detected Alpine 3.24.1, checked 30 OS packages and found zero HIGH/CRITICAL vulnerabilities at that point. Trivy reported no language-specific package files; the workload is dependency-free and pip is removed. This is not claimed as a complete CPython source/vulnerability audit or a full cluster/control-plane image scan. Runtime/development Python package graphs are separately advisory-audited. Point-in-time results cannot prove absence of future defects.

## Development failures retained and corrected

- [Initial run 38489312031](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38489312031): k3d exported literal API port zero. A concrete OS-allocated port and context/endpoint guard now precede every cluster operation. Kubernetes validation was not disabled.
- [Run 38489741797](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38489741797): a denied probe's generic error hid its actual transport. Safe allowlisted diagnostics and node counters were added; generic failures were not accepted.
- [Run 38490393993](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38490393993): fast drift correction beat the next read. The API write receipt now proves injection independently of subsequent repair.
- [Run 38490712926](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38490712926): refusal was observed, but post-completion counters were zero. Sampling after Pod cleanup is not valid packet evidence.
- [Run 38491378366](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38491378366): a PID-1 process-stop assumption did not hold the probe. A registered, bounded acknowledgement handshake replaced it.
- [Run 38491732568](https://github.com/JasonStys/gitops-platform-lab/actions/runs/38491732568): active sampling demonstrated refusal plus REJECT packets 0→1. The former timeout-only expectation was incorrect for the actual K3s implementation. The final oracle requires eligible transport, fresh scoped counter increase, verified program exit and healthy controls. Native regressions reject stale/zero counters, DNS/HTTP errors and wrong expectations.

All failures remain available; no run history was deleted to create a green appearance. No local Docker repair or production access occurred. This repo creates zero Actions artifacts/caches and publishes only selected synthetic aggregates. Account-wide billing details are not in the repository. Future production identity, HA, authenticated source/image trust and multi-node/CNI assurance remain explicitly outside scope.
