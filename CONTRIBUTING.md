# Contribution and coding conventions

Created by Jason Stys. Keep the lab small, typed, readable, explicitly bounded and honest about its scope. Use named contracts and stable data-only error codes; do not execute uploaded content, interpolate shell strings, remove negative assertions, suppress advisories or expand cluster privileges without a reviewed design change.

Run Ruff lint/format, mypy, pytest with branch-inclusive coverage, native Helm cases and source/README map checks. The actual cluster job is required before claiming networking, RBAC, drift or rollback worked. Unit fixture PASS records are only parser tests, never production/drill evidence.

Every authored Python function/class has its own contract. Generate exact code-header maps after formatting with `python scripts/code_map.py`; check with `--check`. YAML/Helm/shell headers identify declared fields and template references. Intact upstream source retains its original maps/notice and hashes; update its lock and explain changes when deliberately moving the upstream revision. Natural JSON/lock formats do not receive invalid comments.

Stage intended files, run `python scripts/file_guide.py` and verify `--check`. Every tracked file must have a README purpose. Keep deep paths, private output, kubeconfigs, accounts, environments and tools out of the repository.

Prefer a reviewed Git change to manual production state edits. The CI drift/failure mutations are explicitly owned synthetic experiments. Never point the drill at a existing cluster, remote Docker daemon or customer network. Keep the fixed workload image tag confined to disposable local imports; production requires a separate image/source identity design.
