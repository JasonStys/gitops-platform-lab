# Disposable-runner package acquisition — 2026-11-11

Author: Jason Stys. Workflow availability hardening, not a proven DNS repair or product defect.

The exact feature-PR source had already passed its clean Windows compiled functional journey. Its later Validate run failed only in Ubuntu 3.12/3.14 APT installation of `python3-tk`, exit 100, before the affected source/native assertions. Actual logs explicitly report temporary DNS failures for the configured mirrors. Requests to the official fallback locations also failed. This evidence does not establish an application failure, nor prove that changing mirrors cures the underlying resolver/network outage.

Only the disposable Ubuntu 24.04 runner acquisition path changes: confirm hosted Linux/x86_64/Ubuntu version and existing signed mirror-file/keyring contract, then select fixed official HTTPS archive/security mirrors. Existing suites, components and Ubuntu archive signature/keyring verification remain unchanged. APT acquisition uses zero retries and finite 15-second transport timeouts with effective configuration checked. Package names, test/native/sanitizer oracles, original job deadlines, signed hash checks and no-artifact/cache policy remain intact. No local PC DNS, host package source, SDK or Docker configuration is changed.

Actual-workflow regression mutants reject missing/late admission, missing signature guard, foreign mirror, added retries and unauthenticated installation. Full hosted checks must run on the new source; a local YAML policy/actionlint pass is not live APT/DNS evidence. If every official host remains unavailable, the workflow still fails rather than skipping tests, weakening authentication or retrying to obtain a green result.

Primary contracts: [Ubuntu Noble sources.list](https://manpages.ubuntu.com/manpages/noble/man5/sources.list.5.html), [APT mirror transport](https://manpages.debian.org/testing/apt/apt-transport-mirror.1.en.html). The mirror transport selects entries by priority and preserves repository authentication; it cannot guarantee DNS/network availability.

## Actual follow-up validation

[Observed failed PR run](https://github.com/JasonStys/gitops-platform-lab/actions/runs/43035259236). Seven authored-step policy cases, including six missing/late/unsafe mutations, passed locally. The complete source suite passed 259 tests with three explicit capability/platform skips and 96.55% combined coverage, retaining its original 90% floor. Strict lint/types/maps/native actionlint passed. Original clean compiled proof at `e0ea0452169462058053b473d8c33879bceead28` remains historical; a later source-bound native proof and hosted gates must be observed independently. No actual DNS success is claimed by these local checks.
