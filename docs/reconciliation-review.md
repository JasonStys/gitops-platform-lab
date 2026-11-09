# Desired and observed release review

Created by Jason Stys. Healthy pods from a previous revision do not prove a new Git release converged. The offline `reconcile` workflow keeps source revision, applied revision, observed generation, replica/Helm readiness, dependencies and required transport evidence separate.

```bash
mkdir -p out
python -m lab reconcile examples/reconciliation-pending.json --as-of-ms 1000100 --output out/pending-review
python -m lab reconcile examples/reconciliation-recovered.json --before examples/reconciliation-pending.json --as-of-ms 1000100 --output out/recovery-review
```

The first synthetic snapshot has two ready replicas but an old applied commit and old observed generation; it returns NEEDS_REVIEW and exit1. The second has matching source/applied intent, matching generation, ready dependencies and a referenced transport check; it returns RECONCILED_ASSERTED and exit0. The comparison shows the two repaired observations without claiming that old readiness resolved new intent. Open the new directory's `reconciliation.html`; JSON contains exact semantic snapshot hashes, each check/reason, review queue and transitions. Existing outputs are never replaced. Exit2 rejects malformed inputs or unavailable output.

Schema1 is a closed record shown in the examples. `workload` is namespace/name, desired/source/applied revisions are full40-hex Git SHAs (observed values may be null), desired generation and replica count are explicit, observed generation/replicas/Helm readiness may be null. `dependencies` declares up to20 named required dependencies with true/false/null observations. `captured_at_ms`, `--as-of-ms` and `--max-age-ms` (default five minutes, max one day) determine freshness; future or older evidence makes checks UNKNOWN. Comparison requires the same workload and chronological snapshots, while explicitly labeling changed desired intent or removed checks.

When transport is required, its result is PASS/FAIL/UNKNOWN and PASS needs a nonzero64-hex `transport_proof_sha256` reference. Without a proof reference it remains UNKNOWN. When not required the result must be NOT_REQUIRED; no claim is made. This normalized input is **supplied observation data, not authenticated acquisition**. A hash references evidence but does not validate its underlying verdict. Use the unchanged real cluster/network drill for live enforcement proof; it still requires scoped counters, eligible transport and healthy controls. This workflow does not substitute a timeout for network denial.

Any explicit failed check yields NEEDS_REVIEW; otherwise any UNKNOWN yields INSUFFICIENT_EVIDENCE. Only all supplied known checks matching expectations yields RECONCILED_ASSERTED. Ownership, input completeness and freshness clocks are operator responsibilities. No Kubernetes/Docker process, reconciliation, workload command, apply, host change or arbitrary network request is made. Reports contain no kubeconfigs, raw logs or secrets and load no scripts/assets. Keep real snapshots private. Existing real Flux/Helm/transport tests and gates remain unchanged.
