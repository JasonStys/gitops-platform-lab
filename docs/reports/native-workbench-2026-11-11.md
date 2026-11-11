# Native offline workbench validation — 2026-11-11

Author: Jason Stys. This report describes source/candidate validation, not a completed release, installation, desktop shortcut or hosted-main claim.

## Implemented user workflow

Review an authorized rendered chart or supplied workload observations using the original closed five-resource policy and reconciliation engines. Keep desired intent, observed readiness, dependency evidence and transport references separate; no live cluster or controller is started.

The compiled consumer checks all ten scenarios with hardcoded allow/deny/verdict, queue, check and transition expectations, plus actual selected YAML and paired JSON files. It verifies exact export, invalid-input retention, cancel/confirm deletion and identical saved bundle IDs/bytes after a second normal launch.

## Measured local scope

- Initial authored-source suite at `e0ea0452169462058053b473d8c33879bceead28` before the separately documented runner-policy tests: 252 passed, 3 explicit platform/capability skips; combined statement/branch coverage 96.55%, above the original 90% floor. No original coverage exclusions or floor reduction was added. The skips are one POSIX-only FIFO case and two symbolic-link fixtures the current Windows token cannot create. Actual NTFS hardlink cases pass locally; real FIFO/symbolic-link cases remain a hosted Linux obligation.
- Strict Ruff, format and mypy checks retain the original modules. Meaningful unit cases exercise exact domain results, invalid input, bounded source reads, NTFS hardlinks, fixed mutable-file/sidecar admission, persistent history and actual GUI handler behavior. Source tests are distinct from compiled acceptance.
- A dirty-source development candidate already passed 12 original-engine workflows and two normal native launches with unchanged bundle history. The coherent clean-source build and exact hosted PR/main checks must be observed separately; the dirty prototype is not release evidence.
- The new Windows Actions job builds the actual one-file application using pinned CPython 3.14.10 and the complete hash-locked graph, audits packaging dependencies, and runs the unchanged full compiled consumer. It uploads no application packages, profiles, screenshots, private receipts or caches to Actions storage. Original security, cross-platform, real-container/cluster and release gates remain in place.

## Security and interpretation

This is offline review of declarations, not a live collector, network-policy enforcement proof or authenticated cluster identity. No kubectl, Helm, Flux, Docker, account, network listener or apply operation is started by the GUI. The existing real Helm and disposable K3s/Flux gates remain mandatory and separate. Only the authored chart's closed resource inventory is supported.

Profiles and chosen paths are sensitive plaintext for a trusted OS owner. Static alias/hardlink checks are not same-user adversary isolation. No live host, cloud, cluster or operational deployment was accessed by this native test. Docker Desktop and normal account profiles were unchanged. PyInstaller resource hashes and source metadata are integrity/diagnostic bindings, not Authenticode signing, malware certification or a legal/compliance opinion.

See [native usage and profile lifecycle](../native-application.md). Historical reports remain dated at their original source identities.

## Observed HTTP-test failure retained

One complete development run observed Windows `ConnectionAbortedError` in the original real Git endpoint-denial test after its real clone had succeeded. A separate owned-server diagnostic made 120 independent inert invalid requests with the original expected statuses and no aborts. The test now reports the exact failed case/method and always closes its client connection, without retries, relaxed statuses or ignored exceptions. The focused original test and subsequent full suite passed. The initial failure remains privately preserved; its root cause was not established and a later pass does not prove an operating-system or server fault was repaired. Production server behavior was not changed.

[Subsequent setup-only runner correction and expanded local suite](runner-network-2026-11-11.md). No runtime/oracle/floor reduction was made.
