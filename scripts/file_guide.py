"""Generate exhaustive Git-tracked README summaries without including ignored runtime data. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: ROOT — line 32
# variable: BEGIN — line 33
# variable: END — line 33
# variable: SPECIAL — line 34
# definition: description — line 57
# parameter: path — line 57
# variable: content — line 61
# variable: line — line 68
# definition: main — line 73
# variable: parser — line 75
# variable: args — line 77
# variable: files — line 78
# variable: rows — line 86
# variable: path — line 87
# variable: label — line 88
# variable: readme — line 90
# variable: original — line 91
# variable: begin — line 92
# variable: end — line 92
# variable: expected — line 93
# END CODE MAP

from __future__ import annotations

import argparse
import ast
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BEGIN, END = "<!-- BEGIN FILE GUIDE -->", "<!-- END FILE GUIDE -->"
SPECIAL = {
    ".gitattributes": "Portable LF text handling.",
    ".gitignore": "Excludes local tools, evidence, kubeconfigs, secrets and caches.",
    ".dockerignore": "Only the reviewed runtime adapter and pinned analyzer enter the image context.",
    "LICENSE": "MIT license for authored code.",
    "vendor/LICENSE": "Intact MIT notice for the pinned existing SRE analyzer.",
    "pyproject.toml": "Strict types, lint, cross-platform tests and branch-inclusive coverage gate.",
    "requirements.in": "Exact runtime manifest-validation dependencies.",
    "requirements-dev.in": "Exact validation dependencies plus the runtime graph.",
    "requirements.lock": "Complete hash-pinned portable runtime dependency graph.",
    "requirements-dev.lock": "Complete hash-pinned portable validation graph.",
    "upstream.lock.json": "Exact SRE repository revision and byte digests of reused source/notice.",
    "tools.lock.json": "Official tool archive hashes and immutable K3s image digest.",
    "chart/values.schema.json": "Closed native Helm schema with replica/image/readiness/revision limits.",
    "examples/rendered.json": "Actual native Helm render, reproduced and compared by manifest checks.",
    "docs/reports/manifest.json": "Actual ten-case native Helm schema/render validation.",
    "docs/reports/benchmark.json": "Measured warm bounded parsing and policy-audit timing/allocation.",
    "docs/reports/drill.json": "Actual disposable-cluster Git/RBAC/network/drift/rollback measurements.",
    "docs/reports/drill.html": "Escaped inert HTML rendering of the measured synthetic drill.",
    "docs/reports/ci.json": "Verified immutable executable-source CI snapshot and completed job results.",
}


def description(path: str) -> str:
    """Require an actual file purpose; unknown formats fail instead of silently omitting files."""
    if path in SPECIAL:
        return SPECIAL[path]
    content = (ROOT / path).read_text(encoding="utf-8")
    if path.endswith(".py"):
        return (ast.get_docstring(ast.parse(content)) or "").splitlines()[0]
    if path.endswith(".md"):
        return content.splitlines()[0].lstrip("# ") + "."
    if path.endswith((".yml", ".yaml", ".sh")) or path == "Dockerfile":
        return next(
            line.lstrip("# ") for line in content.splitlines() if line.startswith("# ")
        )
    raise ValueError("missing tracked-file purpose: " + path)


def main() -> int:
    """Generate/check summaries for every staged/tracked file; stage intended new files first."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    files = (
        subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT)
        .decode()
        .rstrip("\0")
        .split("\0")
    )
    if files == [""]:
        raise ValueError("stage intended files first")
    rows = ["| File | Purpose |", "| --- | --- |"]
    for path in sorted(files):
        label = path.replace("_", "\\_")
        rows.append(f"| [{label}]({path}) | {description(path).replace('|', '/')} |")
    readme = ROOT / "README.md"
    original = readme.read_text(encoding="utf-8")
    begin, end = original.index(BEGIN) + len(BEGIN), original.index(END)
    expected = original[:begin] + "\n\n" + "\n".join(rows) + "\n\n" + original[end:]
    if args.check and expected != original:
        raise ValueError("README inventory stale")
    if not args.check:
        readme.write_text(expected, encoding="utf-8", newline="\n")
    print(f"README inventory current: {len(files)} files")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
