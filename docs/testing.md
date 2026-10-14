# Risk-based validation strategy

Author: Jason Stys. Unit fixtures are synthetic; live enforcement claims require completed cluster job evidence.

| Risk/boundary | Verification |
| --- | --- |
| Ambiguous/hostile structured input | Duplicate keys, aliases, nonfinite/invalid UTF8, node/byte/depth/document bounds and ordinary files |
| Unsafe chart change | Native Helm ten-case value/schema matrix plus independent closed-resource policy and property-tested replica quota |
| Incorrect permission/network assumptions | Actual impersonated can-i matrix, enforced CNI positive/timeout-negative controls and explicit server-side restricted PSA rejection |
| Git/controller drift or bad readiness | Actual scratch commits with observed exact revision, replica drift repair, current Helm/Deployment conditions and retained failed/rollback history |
| Dead-service false denial | Timeout-only negative oracle plus exact HTTP-200 controls before/after |
| Report/privacy mistakes | Incomplete/duplicate/FAIL suite rejection, closed aggregate fields, private-input nondisclosure, escaped inert HTML and no overwrites |
| Workload/parser behavior | Real loopback HTTP, pinned actual SRE analyzer, bounded server slots and supported smart-HTTP shallow Git clone/write endpoint denials |
| Supply chain/workflow | Full hash-locked dependency audits, Gitleaks history, native actionlint/ShellCheck, actual built image HIGH/CRITICAL scan, security-extended CodeQL |

Strict Ruff/mypy and a 90% **combined statement/branch** coverage gate cover authored `lab` and `workload` modules. There are no coverage exclusions or platform skips. Orchestration/helper/vendor code is not included in that percentage: it is exercised separately by native tests, checksum checks, actual Helm and the live cluster job. This is not repository-wide or path-complete coverage.

Hosted Python lanes: Ubuntu 24.04/3.12, Ubuntu 24.04/3.14, Windows/3.14 and macOS Intel/3.14. Helm runs in native Windows pre-publication and the dedicated Linux job. Actual K3s/Flux/image tests run only on an ephemeral Linux runner; local Docker Desktop is unchanged. A pinned native binary is downloaded only from its fixed official source and verified before execution.

Randomized replica tests use an independent interval oracle over 100 generated integers. Performance tests use five batches of 100 actual parsing/audits, assert correct decisions, and report time/allocation without a hardware-dependent CI threshold. Ten live cases record wall durations and exact selected fingerprints; unit fixture timing/success must not be misrepresented as those measurements.

Gaps: multiple physical nodes/CNIs, production identity/TLS, public HTTP hardening, authenticated Git permissions/signature verification, secret rotation, cluster HA, storage/database recovery, hostile local admin/process containment and formal accessibility/compliance audits. None is implied by green badges. Initial development/CI failures and their corrections belong in the measured validation report; do not remove history or weaken gates.
