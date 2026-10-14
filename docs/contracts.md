# Configuration and evidence contracts

Author: Jason Stys.

## Helm and rendered policy

Four closed values: replicas (integer 1–3, never bool), fixed `gitops-sre:lab` image, readiness `/health` or deliberately test-only `/missing`, revision `baseline/promoted/broken/recovered`. Native Helm rejects any other key, value or type. Independent policy rejects `/missing` and `broken`, even though they remain available to the explicitly isolated rollback fixture.

The renderer must produce exactly one Deployment, Service, ServiceAccount and two NetworkPolicies with known names in `platform-lab`. Extra kinds, identities, fields, host settings, containers, volume mounts, external images or credentials fail closed. Pod/service/resource/probe/security settings are exact. Known bool/int fields are checked by type; Python's `True == 1` cannot satisfy an integer predicate.

Default deny covers ingress/egress. The only runtime ingress peer combines the approved namespace selector and reviewer pod selector **within the same peer**, giving AND semantics. Separate peers would be OR and are rejected/tested. Traffic is TCP/8080 only. Probe namespaces get DNS plus the exact workload path; the workload itself has no egress allowance. CNI enforcement must be measured, not inferred from an ALLOW static report.

## Parsing and errors

At most 1 MiB per file/document, 50,000 bounded-tree nodes/parser events, depth 24 and 100 YAML object documents. JSON rejects duplicate keys, nonfinite values and invalid UTF8. Safe YAML rejects aliases, duplicate/non-string keys, executable tags, non-JSON scalar objects and excessive input. Boolean resolution is limited to true/false variants so `on`/`yes` are not YAML 1.1 surprises. Empty documents are ignored; arrays are not resource documents. Only explicit ordinary input files are read; the leaf cannot be a link/reparse point. This is not an adversarial filesystem sandbox.

Audit returns stable policy codes without raw values. ALLOW/DENY/malformed CLI exits are 0/1/2. Input contents are never shell code, fetched URLs, templates to execute or provider prompts.

## Cluster ownership

Linux amd64 local Docker socket only, no existing k3d clusters, explicit acknowledgement, one random `gitops-lab-<10 hex>` cluster. Dedicated `out/.../owned.kubeconfig` and exact context accompany every kubectl operation. The default user context is neither switched nor used. The API binds loopback; source HTTP binds the verified private Docker bridge. Only the newly owned name/process is cleaned up; ignored output is retained privately for inspection.

## Measured reports

Exactly ten named distinct PASS cases are required for a successful report: bootstrap, Git promotion, drift repair, namespace RBAC, allowed traffic, denied pod label, denied namespace, server-side PSA rejection, failed-release rollback and later Git recovery. Time is monotonic measured milliseconds, bounded 0–1,800,000. Source/workload revisions and built image configuration digest are well-formed nonzero fingerprints. These do not authenticate a collector or prove observed facts independently.

Proof records contain only small printable ASCII strings, bounded integers and booleans; no raw Secrets, kubeconfigs, private headers, arbitrary logs or paths. Publication uses a new directory, writes canonical selected JSON and escaped network-inert HTML. Unit test fake reports are explicitly labeled test fixtures and never published as cluster measurements.

Git source revision is observed exactly; readiness requires the current Deployment generation, requested/ready replicas, revision annotation and current Helm Ready condition. Drift injection is proved by the API write receipt, so immediate repair cannot erase that observation.

Network denial requires an eligible timeout/refusal/unreachable transport observation **and** an increase in the exact workload namespace's real kube-router REJECT packet counters. DNS/HTTP/unknown errors are rejected; refusal or timeout without new policy packets also fails. Counters are sampled only for denied cases; positive-control records' zero counter fields are unused placeholders, not node measurements. The probe registers an explicit bounded SIGUSR1 acknowledgement before flushing its receipt; the owned host reads counters while the Pod remains active, then acknowledges and verifies its successful exit. Pod completion can reset counters, so sampling only afterward is invalid. Active deadline: 60 seconds; acknowledgement wait: 30 seconds. Healthy controls before/after distinguish a tested rejection from a dead service. This is a controlled single-node test, not formal traffic attribution in a shared production cluster.

New positive-control Pods allow at most six attempts for label/IP-set policy onboarding, with a 0.5-second gap and a two-second per-request transport timeout. Only an eligible blocked positive observation is retried; DNS, malformed HTTP and unknown errors fail immediately. Every successful receipt discloses `convergence_attempts`; negative probes must remain single-shot. Permanent positive blockage fails at the sixth attempt. The host waits at most 20 seconds for the receipt, then uses the acknowledgement protocol above. This tests eventual onboarding readiness, not instant first-request availability or a production latency SLA.

PSA requires explicit `violates PodSecurity`/restricted denial, not any kubectl error. Rollback requires a current Remediated/RollbackSucceeded condition, restored probe, healthy service and actual retained failed/deployed Helm history.
