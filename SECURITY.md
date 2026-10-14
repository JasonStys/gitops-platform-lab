# Security boundary and reporting

Created by Jason Stys. Contact privately through [GitHub](https://github.com/JasonStys) or [LinkedIn](https://www.linkedin.com/in/jason-stys-31b30b351/); do not put secrets or live kubeconfigs in public issues.

## Threat model

Protected boundaries are the closed rendered-chart policy, bounded data parser, pod runtime identity, namespace-scoped delivery/reconciliation, selected NetworkPolicy paths and failed rollout behavior. Adversarial cases include aliases/duplicates/nonfinite/deep inputs, host access, extra resources/containers, API token mounting, namespace/selector mistakes, unreachable/malformed service responses and incorrect readiness.

Trust the owned filesystem, official checksum sources, reviewed dependency graph, Linux Docker daemon, K3s control plane, cluster administrator, Flux controllers, Git executable and scratch source creator. k3d uses privileged control-plane containers on the disposable runner. This is **not** hostile multi-tenant Docker isolation. The local root/administrator can alter source, image tags, roles, reports and measurements. Neither report hashes nor Git object IDs authenticate a collector.

The Git server accepts only exact read-only smart HTTP clone/fetch routes and caps request size, socket lifetime, backend time and active handlers. It carries only synthetic chart/configuration data on a private bridge, without credentials. This HTTP setup is not suitable for production: use authenticated HTTPS/SSH and separately establish trusted source/signature policy. Python's development HTTP servers are not presented as public hardened servers.

Runtime pods have no automatically mounted Kubernetes credential and no RoleBinding. Delivery can manage selected namespaced resources, including Helm storage Secrets, **only** in `platform-lab`. Reconciliation can manage HelmRelease objects there. The Flux installer still uses administrator rights; controller flags plus service-account impersonation constrain the demonstrated workload writes, not all controller/bootstrap privileges.

NetworkPolicy proves only observed TCP/8080 paths for the tested CNI/single-node topology. It is label-based L3/L4 access, not user authentication, mTLS, encryption or protection from a trusted namespace administrator relabeling pods. Node/control-plane traffic, other CNIs/protocols, host-level threats and production availability are not certified. Readiness rollback is not transactional rollback of external databases or side effects.

Raw kubeconfigs, scratch repositories, tool binaries and runtime output are ignored by Git. Reports publish selected synthetic aggregates only, never Secrets, credentials, private identities or host logs. No third-party telemetry/ad network is included. Keep the ignored `out/` tree private; it contains temporary administrator kubeconfigs even after the cluster is removed. File checks reject leaf links/reparse points, but assume no hostile concurrent filesystem mutation or parent-path administrator interference.

Advisory audits and image scans are point-in-time. A passing CI run does not prove absence of all defects or future vulnerabilities. Do not disable gates or mark findings false just to obtain a green badge.
