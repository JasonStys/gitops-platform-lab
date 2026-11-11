# Completed rollback observations

Author: Jason Stys. Date: 2026-11-11.

## Observed failure

Main source `1268259fb52f7eff7c9e040df7967164d28a2ce6`, [run 43083340381, cluster job 130741297263](https://github.com/JasonStys/gitops-platform-lab/actions/runs/43083340381/job/130741297263), passed the first eight real disposable-cluster cases, then failed with `actual Helm rollback history missing`. Its bounded diagnostics showed a healthy Deployment while the HelmRelease still reported `Reconciling=True` and `Running 'rollback' action with timeout of 40s`. The failed history itself was not printed, so its exact status cannot be reconstructed from this log.

The old oracle first waited for a remediation condition, separately waited for a restored readiness path, then sampled Helm history once. These observations do not establish that the asynchronous Helm history update has completed. [Flux documents](https://fluxcd.io/flux/components/helm/helmreleases/#failed-helmrelease) that Remediated conditions persist until a later action completes and that a release may be failing and reconciling concurrently. [Helm 3.22 rollback source](https://github.com/helm/helm/blob/v3.22.0/pkg/action/rollback.go) creates a pending rollback revision before completing and updating its final status.

## Correction and retained boundaries

The real cluster drill now polls all required evidence within the existing **180 second remediation wait**: a single current-generation HelmRelease snapshot with `Remediated=True` and `RollbackSucceeded`, no active Reconciling condition, the observed two-replica `promoted` Deployment with `/health`, and bounded actual Helm history whose newest revision is deployed, explicitly rolls back to an earlier retained matching-chart revision, and retains a failed revision between that target and the deployed rollback. Deployment total, updated, ready and available counts must all be two, with no unavailable pods; healthy old or surge pods alone are insufficient. A successful unrelated upgrade cannot satisfy the history predicate.

The separate subsequent 180 second readiness-path wait and one-shot history assertion are removed. No deadline is increased, no Helm action retry is added, and no failing observation is discarded. Command/JSON errors remain failures. The original positive network control and later exact Git recovery commit still run after rollback completion. These sequential API reads are a completion predicate, not an atomic cluster snapshot.

## Validation scope

The regression suite exercises the real predicate and polling loop with independent controller, Deployment and Helm CLI fixtures. It covers pending-to-deployed history, a permanently pending rollback reaching the unchanged 180 second deadline, active reconciliation despite a retained success condition, stale generations, missing or failed remediation, old or unready pods, wrong readiness/revision, unrelated upgrades, missing failed or target revisions, mismatched charts, malformed or reordered history, and actual command errors. Fixture clocks advance deterministically; they are not measured live-cluster timings.

The corrected local Windows suite on isolated CPython 3.14.10 passed **299 tests**, including 31 new rollback cases, with three existing disclosed platform skips (one POSIX FIFO and two unavailable symbolic-link fixtures). The original `lab`/`workload` combined statement/branch coverage was **96.55%**, above its unchanged 90% floor; orchestration is not included in that percentage. Ruff, formatting, strict mypy, exact source maps, the exhaustive file inventory, pinned-source/workflow contracts and `pip check` also passed. Five informational batches of 100 real offline policy audits measured a 0.755 ms median per audit; that excludes live cluster, Helm and network execution and is not a new performance threshold.

Local execution does not run Docker or alter any existing cluster. The unchanged hosted cluster job must provide the fresh real K3s/Flux/Helm proof before this repair is accepted. Earlier released offline Windows application evidence is historical and is not reclassified by this orchestration-only correction.
