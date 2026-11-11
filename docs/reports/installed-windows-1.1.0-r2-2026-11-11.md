# Installed Windows 1.1.0: validation and user guide

By Jason Stys. 11 November 2026.

The independently downloaded installed application uses exact clean runtime source `89fffbae0bd2fe1f74e2954edb8b981be42e5b6f`. Historical reports and Office editions remain unchanged.

## Purpose and practical improvements

Audit supplied Kubernetes manifests and captured controller snapshots using the original closed policy engine. Compare desired and observed revision/generation evidence while keeping local review separate from live cluster enforcement.

The original project retains declarative GitOps configuration, Helm tests and policy/snapshot assessment. The new desktop GUI adds local manifest and snapshot selection, explicit original-versus-effective policy limits, exact comparisons, retained immutable history and complete evidence export.

## Actual validation

**Independent distribution: Passed.** Downloaded provider assets, sidecar and installed file identities matched. The complete installed app was used; installation resources remained byte-identical.

**Actual app use and restart: Passed.** Twelve real installed workflows and twelve reopened evidence bundles passed the original full native consumer, including original/effective policy checks and two normal exits.

**Source and security: Passed.** All current main workflows passed before publication. All configured exact-source processed CodeQL categories had zero raw findings and zero open alerts.

**Individual shortcut: Verified.** Desktop and Start-menu targets were read back against the installed version. Normal default-profile shortcut activation is separate from full installed executable acceptance.

## Illustrated operation and implementation

The [four-page application guide](windows-application-guide-1.1.0-r2.docx) contains two actual installed screenshots, a practical user journey and immutable code. Its [review manifest](windows-application-guide-1.1.0-r2.json) records exact document, image, code and page identities.

Download the matching version and checksum from Releases. This is an unsigned per-user portable Windows x64 app; keep its complete accompanying files together. No system Python installation or Docker change is needed.

Use the individual Desktop icon and in-app help. Inputs, saved evidence and exports stay outside the installation. Preserve older versions and your own profiles; tests used only separate synthetic inputs.

Assessment uses supplied files and captured snapshots; the GUI does not access a live cluster, install Helm, invoke Docker or perform policy enforcement.

An observed snapshot can be stale or unauthenticated. A local review preserves its exact supplied identity and limitations rather than proving current live-system state.

Only synthetic prepared inputs and isolated retained profiles were used. Ordinary user accounts and local Docker were not opened or changed. Shortcut target read-back and full installed-executable tests are separate from ordinary default-profile icon activation. This documentation revision still requires its own original hosted gates and processed security analyses.
