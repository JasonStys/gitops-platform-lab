"""Generate/check exact Python, SQL, shell and YAML symbol positions. Created by Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: BEGIN — line 81
# variable: END — line 82
# variable: ROOT — line 83
# definition: mapped — line 86
# parameter: source — line 86
# variable: start — line 89
# variable: finish — line 90
# variable: source — line 91
# variable: tree — line 92
# variable: first — line 93
# variable: insertion — line 94
# variable: records — line 101
# variable: node — line 102
# variable: count — line 109
# variable: header — line 110
# variable: kind — line 114
# variable: line — line 114
# variable: name — line 114
# parameter: item — line 115
# variable: lines — line 120
# definition: main — line 125
# variable: parser — line 127
# variable: arguments — line 129
# variable: stale — line 130
# variable: folder — line 131
# variable: path — line 132
# variable: original — line 133
# variable: expected — line 134
# variable: tree — line 136
# variable: node — line 137
# variable: path — line 148
# variable: original — line 160
# variable: expected — line 161
# definition: shell_mapped — line 170
# parameter: source — line 170
# parameter: suffix — line 170
# variable: prefix — line 172
# variable: begin — line 173
# variable: end — line 173
# variable: start — line 175
# variable: finish — line 176
# variable: source — line 177
# variable: lines — line 178
# variable: insertion — line 179
# variable: insertion — line 181
# variable: records — line 182
# variable: line — line 183
# variable: number — line 183
# variable: name — line 186
# variable: name — line 188
# variable: name — line 191
# variable: name — line 194
# variable: name — line 198
# variable: name — line 201
# variable: name — line 203
# variable: name — line 205
# variable: name — line 207
# variable: name — line 211
# variable: part — line 216
# variable: name — line 218
# variable: name — line 223
# variable: name — line 225
# variable: name — line 227
# variable: name — line 229
# variable: count — line 233
# variable: header — line 234
# variable: kind — line 238
# variable: name — line 238
# variable: number — line 238
# END CODE MAP

from __future__ import annotations

import argparse
import ast
import re
from pathlib import Path

BEGIN = "# BEGIN CODE MAP (generated; python scripts/code_map.py)"
END = "# END CODE MAP"
ROOT = Path(__file__).resolve().parents[1]


def mapped(source: str) -> str:
    """Build a self-consistent line map for definitions, parameters and assigned variables."""
    if "\n" + BEGIN + "\n" in source:
        start = source.index("\n" + BEGIN + "\n") + 1
        finish = source.index("\n" + END + "\n", start) + len(END) + 2
        source = source[:start] + source[finish:]
    tree = ast.parse(source)
    first = tree.body[0] if tree.body else None
    insertion = (
        first.end_lineno
        if isinstance(first, ast.Expr)
        and isinstance(first.value, ast.Constant)
        and isinstance(first.value.value, str)
        else 0
    )
    records: set[tuple[str, str, int]] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            records.add(("definition", node.name, node.lineno))
        elif isinstance(node, ast.arg):
            records.add(("parameter", node.arg, node.lineno))
        elif isinstance(node, ast.Name) and isinstance(node.ctx, ast.Store):
            records.add(("variable", node.id, node.lineno))
    count = len(records) + 2
    header = (
        [BEGIN]
        + [
            f"# {kind}: {name} — line {line + count if line > insertion else line}"
            for kind, name, line in sorted(
                records, key=lambda item: (item[2], item[0], item[1])
            )
        ]
        + [END]
    )
    lines = source.splitlines(keepends=True)
    lines.insert(insertion or 0, "\n".join(header) + "\n")
    return "".join(lines)


def main() -> int:
    """Update authored Python files, or fail if --check finds stale maps or missing contracts."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    arguments = parser.parse_args()
    stale = []
    for folder in ("lab", "workload", "scripts", "tests"):
        for path in sorted((ROOT / folder).glob("*.py")):
            original = path.read_text(encoding="utf-8")
            expected = mapped(original)
            if arguments.check:
                tree = ast.parse(original)
                for node in ast.walk(tree):
                    if isinstance(
                        node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
                    ) and not ast.get_docstring(node):
                        raise ValueError(
                            f"Missing function/class contract: {path.name}:{node.lineno}"
                        )
            if original != expected:
                stale.append(str(path.relative_to(ROOT)))
                if not arguments.check:
                    path.write_text(expected, encoding="utf-8", newline="\n")
    for path in [
        *(ROOT / "scripts").glob("*.ps1"),
        *(ROOT / "scripts").glob("*.sh"),
        *(ROOT / "ops").rglob("*.yml"),
        *(ROOT / "gitops").rglob("*.yml"),
        *(ROOT / "chart").rglob("*.yaml"),
        *(ROOT / "ops").rglob("*.sql"),
        *(ROOT / ".github/workflows").glob("*.yml"),
        *(ROOT / "infra").rglob("*.tf"),
        *(ROOT / "infra").rglob("*.tftest.hcl"),
        *(ROOT / "policies").glob("*.rego"),
    ]:
        original = path.read_text(encoding="utf-8")
        expected = shell_mapped(original, path.suffix)
        if original != expected:
            stale.append(str(path.relative_to(ROOT)))
            if not arguments.check:
                path.write_text(expected, encoding="utf-8", newline="\n")
    print("Code maps current" if not stale else "Code maps: " + ", ".join(stale))
    return 1 if arguments.check and stale else 0


def shell_mapped(source: str, suffix: str) -> str:
    """Map shell symbols, SQL columns/tables and YAML parameters/controls/expressions without execution."""
    prefix = "--" if suffix == ".sql" else "#"
    begin, end = BEGIN.replace("#", prefix, 1), END.replace("#", prefix, 1)
    if "\n" + begin + "\n" in source:
        start = source.index("\n" + begin + "\n") + 1
        finish = source.index("\n" + end + "\n", start) + len(end) + 2
        source = source[:start] + source[finish:]
    lines = source.splitlines(keepends=True)
    insertion = 1 if source.startswith("#!") else 0
    while insertion < len(lines) and lines[insertion].startswith(prefix):
        insertion += 1
    records = {}
    for number, line in enumerate(lines, 1):
        if line.lstrip().startswith(prefix):
            continue
        for name in re.findall(r"\$([A-Za-z_][A-Za-z_0-9]*)", line):
            records.setdefault(("variable", name), number)
        for name in re.findall(r"^function ([A-Za-z0-9_-]+)", line):
            records[("function", name)] = number
        if suffix == ".sh":
            for name in re.findall(r"^(?:export )?([A-Za-z_][A-Za-z_0-9]*)=", line):
                records.setdefault(("variable", name), number)
        if suffix == ".sql":
            for name in re.findall(
                r"\b([A-Za-z_][A-Za-z_0-9]*) (?:TEXT|INTEGER)\b", line
            ):
                records.setdefault(("column", name), number)
            for name in re.findall(r"CREATE TABLE (\w+)", line):
                records[("table", name)] = number
        elif suffix in {".tf", ".hcl", ".rego"}:
            for name in re.findall(r"^\s*(\w+)(?:\([^)]*\))?\s+if\b", line):
                records.setdefault(("rule", name), number)
            for name in re.findall(r"\b(?:every|some)\s+(\w+)\b", line):
                records.setdefault(("variable", name), number)
            for name in re.findall(r"^\s*default\s+(\w+)\s*:=", line):
                records.setdefault(("default", name), number)
            for name in re.findall(
                r"^\s*([A-Za-z_][A-Za-z0-9_.]*)\s*(?:=|:=|if\b)", line
            ):
                records.setdefault(("symbol", name), number)
            for name in re.findall(
                r'^\s*(?:variable|resource|run|mock_resource) "([^"]+)"(?: "([^"]+)")?',
                line,
            ):
                records.setdefault(
                    ("block", ".".join(part for part in name if part)), number
                )
            for name in re.findall(
                r"\b(?:var|local|count|input)\.[A-Za-z0-9_.]+", line
            ):
                records.setdefault(("reference", name), number)
        elif suffix in {".yml", ".yaml"}:
            for name in re.findall(r"^\s*(?:- )?([A-Za-z_][A-Za-z_0-9]*):", line):
                records.setdefault(("parameter", name), number)
            for name in re.findall(r"^\s*- id: ([A-Za-z0-9_-]+)", line):
                records[("control", name)] = number
            for name in re.findall(r"\$\{\{\s*([A-Za-z0-9_.]+)\s*\}\}", line):
                records.setdefault(("expression", name), number)
            for name in re.findall(r"\.(?:Values|Release)\.[A-Za-z_0-9]+", line):
                records.setdefault(("template-reference", name), number)
            if "| quote" in line:
                records.setdefault(("template-function", "quote"), number)
    count = len(records) + 2
    header = [
        begin,
        *(
            f"{prefix} {kind}: {name} — line {number + count if number > insertion else number}"
            for (kind, name), number in records.items()
        ),
        end,
    ]
    lines.insert(insertion, "\n".join(header) + "\n")
    return "".join(lines)


if __name__ == "__main__":
    raise SystemExit(main())
