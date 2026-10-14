# Operating and recovery runbook

Author: Jason Stys. Scope: owned synthetic native tests or an explicitly disposable Linux CI host.

## First success and help

Follow the README native setup. `python -m lab --help` lists the offline audit/report commands; `python -m workload.server --help` lists fixed service/probe modes. Native validation never starts Docker. `/work` shows the existing SRE analyzer's selected synthetic availability/latency results; this is a demonstration, not a customer API.

For a real cluster, use the Actions `cluster` job or a new dedicated Docker daemon. Install only the explicit reviewed tools, then run the acknowledged drill. Do not point it at a customer network/remote Docker context or another kubeconfig. Never paste access tokens or administrator kubeconfigs into public issues.

The run creates its private output/kubeconfig and cluster, installs real Flux controllers, imports the built own image, then commits baseline/promotion/broken/recovery scratch revisions. A namespace/pod-label traffic matrix, six RBAC checks, drift injection, server-side privileged admission denial and observed Helm rollback are required. Successful reporting happens only after every actual assertion. Measurements are in `out/<new-name>/report/`; aggregates are also printed in the CI log. View the HTML locally, without publicly serving the ignored output tree.

## Expected failure signals

- DENY: check stable policy codes, not a score. Fix the reviewed chart/values and re-run real Helm plus independent audit.
- Parser/CLI exit 2: duplicate/nonfinite/deep/oversized/non-UTF8 input, wrong supported structure, ordinary-file violation, or an existing output directory. Use a new output name; do not overwrite prior evidence.
- Git source not Ready: verify the owned read-only HTTP server and source URL, exact branch/ref, private bridge, controller events and source revision. Flux supports HTTP/S or SSH sources; the test server uses real smart HTTP, not a simulated “Git update”.
- RBAC failure: inspect the specific role/impersonated SA and namespace. Never give the tenant a cluster-admin binding to make a test pass.
- Unexpected network result: confirm positive control, DNS, actual K3s policy controller and increasing scoped REJECT counters while the probe is active. A refused/dead/DNS-failed service alone is not policy enforcement. New positive Pods may need bounded label/IP-set onboarding: inspect the disclosed attempt count (maximum six); permanent blockage still fails. Negative probes never retry, and DNS/malformed HTTP errors fail immediately. The fixed acknowledgement lets the probe exit only after its receipt/counters are collected; inspect that protocol if a Pod disappears before observation. Do not remove negative probes or count generic errors as success.
- Failed upgrade: HelmRelease can stay not Ready after a successful rollback because desired Git is still bad. Preserve failed history/condition evidence; commit the healthy revision rather than treating old running pods as successful reconciliation.
- Image advisory: upgrade/rebuild the appropriate dependency/base and re-run the entire gate. Do not suppress a vulnerability just for a green badge.

## Cleanup and rollback boundaries

The drill stops only its source process and deletes only the validated new cluster name, including partial creation failures. It leaves private local output so results remain inspectable. A hard kill/host crash can interrupt cleanup; inspect the owned name and dedicated kubeconfig before manually deleting **that exact lab cluster**. Never use broad cluster/container/volume prune commands. Do not remove another person's clusters or user files.

The native server can be stopped with Ctrl+C. The CI runner is ephemeral and uploads no artifacts/caches. Existing Actions runs are not deleted. Private ignored outputs contain temporary kubeconfigs; keep them protected and remove only explicitly selected disposable evidence when it is no longer needed.

This lab's rollback restores Kubernetes workload state, not database transactions, external side effects or a production traffic SLA. There is no migration, hosted account or paid infrastructure deployment in this task. A future production adaptation requires a fresh design/authority review. Contact Jason via the README links for help, without disclosing credentials.
