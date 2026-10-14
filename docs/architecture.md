# ADR-001: an observed, disposable GitOps platform

Status: accepted for this educational lab. Date: 2026-10-13. Author/maintainer: Jason Stys. This is author-led implementation/review, not independent approval.

## Context and requirements

Demonstrate useful platform-engineering evidence beyond static YAML: reviewed Git intent, real controller reconciliation, scoped identities, actual networking denial, readiness failures and recovery. Keep testing isolated from existing machines/clusters, retain reproducibility and negative evidence, and add no Actions artifact/cache storage. Native Windows/macOS tests must work without Docker repair.

## Decision

Use Python for bounded validation, an existing SRE workload adapter, orchestration and evidence; Helm for closed packaging; Flux for actual pull/reconciliation; k3d/K3s for an explicitly owned disposable Linux cluster. K3s includes NetworkPolicy enforcement, so the networking test does not assume a kind-default CNI enforces policies.

```text
scratch Git commit -> Flux GitRepository -> Kustomization (reconciler SA)
                                             |
                                             v
                                      HelmRelease (delivery SA)
                                             |
                                   Helm -> restricted workload
                                             |
                                  failed readiness -> rollback
                                             |
                                     later Git recovery commit
```

The copied upstream analyzer is byte-pinned to one existing repository revision and retains its notice/maps. Its new dependency-free adapter exposes only fixed synthetic GET routes; no editable requests or user data enter it. Source/values files are actual scratch Git commits; no CI run writes branches to GitHub. A read-only smart HTTP server binds only the private cluster bridge and delegates Git packets to Git's standard backend. Production source templates use public HTTPS instead.

Native Helm and independent Python policies reject unsafe values/resources before deployment. The rollback drill deliberately introduces a known bad revision **only in scratch Git**, bypassing that preflight to exercise the runtime safety net. The public baseline stays healthy. A rollback repairs deployed state but cannot make the bad Git intention correct; a later Git commit is necessary.

## Alternatives and consequences

Static snapshots would be simpler but cannot prove CNI/RBAC/controller behavior. A production cloud cluster would add credentials, costs and authority beyond this portfolio task. Argo CD is a valid alternative but adds a UI/login surface unnecessary for these controller/evidence goals. K3s's built-in network enforcement reduces CNI setup; the tradeoff is a single-node test topology, not proof for all distributions.

Bootstrap requires administrator rights and installs trusted controllers. Impersonated service accounts constrain the demonstrated namespace writes. This is not a claim that the controllers themselves lack cluster privileges or that the Docker daemon is safely shared with hostile tenants. Runtime pods have no RBAC grant or automatically mounted token. Delivery necessarily accesses selected namespace resources and Helm storage Secrets; reconciliation cannot create roles or namespaces.

The local imported image tag is fixed for the disposable node and never remotely pulled. Its built configuration digest is measured, not a signature/OCI provenance assertion. The Python base and K3s OCI index are digest-pinned; Flux/tool releases are version/hash-pinned. Runtime Alpine security upgrades are fetched at build time, so this is reproducible **source/configuration**, not byte-identical builds or a full signed supply-chain system.

## Complexity and capacity

Parsers cap bytes, events, nodes, documents and depth. Tree validation is O(V) time with O(depth) traversal space; materialized parsing is O(V) memory. The five-resource policy is O(V) over its bounded input with constant-sized inventory joins. Report checking/publication is O(C + text bytes), with exactly ten allowed cases. The upstream SRE analyzer processes 40 fixed events, not arbitrary user workloads. Native HTTP/Git service concurrency is capped at eight handlers; subprocess/socket deadlines are explicit. Post-completion output caps assume a trusted synthetic repository/backend and are not hostile-process memory containment.

Measure warm parser/audit time separately from cluster/network/Helm time. Cluster polling uses finite deadlines rather than timing thresholds masquerading as performance regressions. For production revisit multi-node/CNI matrices, authentication/TLS, immutable signed images, controller admission/RBAC, secret management, high availability, audit retention and rollback of external state. No such deployment is authorized or claimed here.
