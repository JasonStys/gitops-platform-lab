#!/usr/bin/env bash
# Strict portable tests and documentation/source invariants. Created by Jason Stys.
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# END CODE MAP
set -euo pipefail
python -m ruff check lab workload scripts tests
python -m ruff format --check lab workload scripts tests
python -m mypy
python -m pytest --cov --cov-report=term-missing --tb=short
python scripts/code_map.py --check
python scripts/file_guide.py --check
python scripts/validate_repo.py
python scripts/benchmark.py
