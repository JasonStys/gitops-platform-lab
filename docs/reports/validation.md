# Measured validation and author review

Author: Jason Stys. Native Windows validation on 2026-10-13: 111 tests pass with 99.13% combined statement/branch coverage of authored `lab`/`workload`, no skips/exclusions. Strict Ruff/mypy pass. Ten real native Helm cases pass (three accepted/seven rejected), including bool quota and unknown/external values. Real smart-HTTP shallow Git clone/read-only endpoint tests and actual SRE HTTP calculation pass.

The actual warmed parse/audit benchmark is recorded in `benchmark.json`: five batches of 100 decisions, five resources/decision, with a correctness oracle. Its timing is informational and excludes cluster/Helm/network startup. Native Helm results are recorded in `manifest.json`. These are measured outputs, not an assertion of live cluster enforcement.

Author-led security review covers explicit ownership/context, read-only private-bridge Git, bounded input/routes, bool/int distinctions, pod/API identities, selector AND semantics, timeout-only denials, specific PSA errors, exact revision/generation and retained rollback history. Performance review covers bounded tree traversal, constant inventory joins, handler/thread/subprocess deadlines and resource quotas. Correctness review distinguishes healthy deployed pods from a failed desired Git revision. No independent audit, production deployment or certification is claimed.

Prototype review corrected unsupported Git-daemon source design to Flux-compatible real smart HTTP, transient absent-resource handling and the PSA oracle so unrelated errors cannot claim admission enforcement. YAML `on` keys are preserved rather than coerced by a YAML 1.1 bool resolver. Private/temp test data is not published as measured cluster evidence.

Publication acceptance remains pending actual GitHub Actions: all final-main jobs, ten live cluster cases, dependency/image/secret scans and CodeQL findings must be verified and linked here. Nothing in this draft infers a live result from native unit tests. No Docker repair, production access, artifact upload, cache creation or deletion of old Actions runs is authorized by this task.
