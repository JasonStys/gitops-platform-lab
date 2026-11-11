# GitOps Reconciliation Workbench: native application

Created by Jason Stys · [Source and contact](https://github.com/JasonStys) · [Professional profile](https://www.linkedin.com/in/jason-stys-31b30b351/).

Review an authorized rendered chart or supplied workload observations using the original closed five-resource policy and reconciliation engines. Keep desired intent, observed readiness, dependency evidence and transport references separate; no live cluster or controller is started.

## Launch and use

The reviewed Windows portable candidate is `GitOpsPlatformLab.exe`. It bundles CPython 3.14.10, Tcl/Tk 9.0.4, the complete authored GUI and original dependency notices; it requires no separately installed Python, Node, terminal setup, default password or background service. It is a portable application, not an NSIS installer or a signed vendor application. Release/download availability must be verified separately; a source build is not a published download.

1. Choose **Audit authorized rendered manifests** and select a JSON resource array or multi-document YAML file. The actual original policy checks the closed five-resource chart, namespace, service identity, pod security, health probes, replicas and AND-combined ingress selectors. Unknown resources remain denied.
2. Choose snapshot assessment or comparison and select actual authorized current/prior closed JSON snapshots. Set the UTC epoch-millisecond as-of clock and maximum age. A blank clock means now; prepared examples visibly populate their synthetic clock.
3. An optional new desired full SHA changes only the current declared intent. The original snapshot is validated first; original/effective desired revisions, hashes and verdicts remain in evidence. A valid override cannot hide malformed original metadata.
4. Inspect actual checks, review queues and before/after transitions. Healthy old pods do not establish new intent. Missing, stale, future or required-but-absent proof remains inconclusive. A proof hash is a reference, not authenticated cluster acquisition or a verified transport outcome.
5. Ten prepared scenarios run the same engines: closed policy allow/deny; pending/recovered/compared intent; missing proof; stale observations; failed dependency; new desired intent; and explicitly unnecessary transport. Select details, search/filter, export to a new file, and inspect durable saved review history. Delete requires confirmation; Exit waits for worker completion.

## Local data and ownership

The default durable profile is outside the executable and repository: the OS-local application-data directory, then `GitOpsPlatformLab`. An explicitly selected `--profile` remains available; the original CLI paths and data contracts are unchanged. The profile stores sensitive reports, selected paths and saved evidence in owner-local plaintext. There is no multiuser login or encryption claim. Keep it in an OS-protected directory and use only files you are authorized to review.

Before creating/opening SQLite, the app checks lexical ancestors and all fixed database, marker, lock and journal/WAL/SHM files for aliases, nonregular files and multiple links. Ordinary owned recovery sidecars are preserved. An exclusive owner lock prevents a second normal app from adopting the same profile. These static checks do not defend against a malicious process already running as the same OS user. No profile is reset, migrated to a different schema, or automatically deleted on failure.

Inputs use bounded stable descriptor reads, duplicate-safe JSON/closed original parsers and finite evidence/history limits. Export creates a new regular file and refuses overwrite. The native Help and licenses controls work without network access. No telemetry, advertisements, provider keys, HTTP server, plugins, shell eval or arbitrary executable path is introduced. A busy Quit keeps the owner window and lock until the exact worker finishes; no normal-success forced kill is used.

## Build and validate

From a dedicated environment using the reviewed Windows CPython 3.14.10 runtime:

```text
python -m pip install --require-hashes -r requirements-dev.lock -r requirements-native.lock
python -m pip check
python scripts/build_native.py
python scripts/test_native_app.py
```

The build binds the full source SHA, honest dirty flag, actual Python DLL, complete original notices and allowlisted public resources. The consumer runs the actual frozen executable with a minimal system-only environment, drives the same Tk widgets/handlers/mainloop with an explicitly synthetic profile, captures two real screens, exports, normally exits and restarts. CI refuses dirty-source proof and verifies both known frozen PIDs/bootloaders have exited. No external service is adopted and no native artifact/cache upload is added.

The compiled consumer checks all ten scenarios with hardcoded allow/deny/verdict, queue, check and transition expectations, plus actual selected YAML and paired JSON files. It verifies exact export, invalid-input retention, cancel/confirm deletion and identical saved bundle IDs/bytes after a second normal launch.

## Scope and evidence

This is offline review of declarations, not a live collector, network-policy enforcement proof or authenticated cluster identity. No kubectl, Helm, Flux, Docker, account, network listener or apply operation is started by the GUI. The existing real Helm and disposable K3s/Flux gates remain mandatory and separate. Only the authored chart's closed resource inventory is supported.

[Dated local validation and limits](reports/native-workbench-2026-11-11.md). Existing Office guides and older reports retain their recorded source baselines and measurements; they are not rewritten as evidence of this candidate.
