# Primary sources and implementation rationale

Author: Jason Stys. Reviewed 2026-10-13; exact executable/tool/source pins are in the lock files.

- [Flux installation](https://fluxcd.io/flux/installation/): supported Kubernetes versions, administrator bootstrap and the role of actual controllers.
- [Flux GitRepository](https://fluxcd.io/flux/components/source/gitrepositories/): HTTP/S or SSH source and observed revision. The scratch source implements standard smart HTTP, not unsupported git-daemon URLs.
- [Flux HelmRelease](https://fluxcd.io/flux/components/helm/helmreleases/): drift correction, upgrade remediation, final-failure rollback and condition/history interpretation. This informed the live recovery oracles, not just YAML field names.
- [K3s networking services](https://docs.k3s.io/networking/networking-services): embedded kube-router NetworkPolicy controller, providing an enforcement-capable disposable test environment.
- [Pinned K3s kube-router implementation](https://github.com/k3s-io/kube-router/blob/v2.6.3-k3s1/pkg/controllers/netpol/pod.go): unmatched traffic hits REJECT rules. Actual CI confirmed refusal plus a scoped counter increase; the oracle therefore requires transport, active counters and healthy controls rather than assuming all enforcement manifests as timeout.
- [Kubernetes NetworkPolicy](https://kubernetes.io/docs/concepts/services-networking/network-policies/): selector composition and L3/L4 limits. The AND peer and independent positive controls are explicitly tested.
- [Kubernetes Pod Security admission](https://kubernetes.io/docs/concepts/security/pod-security-admission/): versioned restricted namespace enforcement. The test requires a specific admission denial, not an arbitrary failure.
- [Git HTTP backend](https://git-scm.com/docs/git-http-backend): standard read-only upload-pack discovery/fetch delegated to Git. The wrapper forbids receive-pack routes and bounds inputs.
- [Helm chart schema](https://helm.sh/docs/topics/charts/#schema-files): native values validation supplements independent resource checks; a schema alone does not prove runtime enforcement.
- [Pinned existing SRE analyzer](https://github.com/JasonStys/sre-observability-workbench/tree/3bbe2f4fde0cd82c91ef0946a0c6dd3bed60dc39): actual reused portfolio implementation with retained MIT notice, byte fingerprints and original line maps.

These sources support implementation choices; they do not endorse or certify this lab. Public examples are synthetic and tests use only owned disposable resources.
