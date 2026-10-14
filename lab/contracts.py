"""Strict bounded document loading; inputs are data, never commands. Created by Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: MAX_BYTES — line 75
# definition: integer — line 78
# parameter: high — line 78
# parameter: low — line 78
# parameter: value — line 78
# definition: record — line 85
# parameter: fields — line 85
# parameter: value — line 85
# definition: digest — line 92
# parameter: size — line 92
# parameter: value — line 92
# definition: bounded_tree — line 103
# parameter: budget — line 103
# parameter: depth — line 103
# parameter: value — line 103
# variable: budget — line 106
# variable: child — line 111
# variable: key — line 111
# variable: child — line 116
# definition: unique — line 126
# parameter: pairs — line 126
# variable: result — line 128
# variable: key — line 129
# variable: value — line 129
# definition: read_bytes — line 136
# parameter: path — line 136
# variable: info — line 138
# variable: stream — line 145
# variable: data — line 146
# definition: json_bytes — line 152
# parameter: data — line 152
# variable: value — line 156
# definition: ClosedLoader — line 161
# variable: pattern — line 168
# variable: tag — line 168
# variable: entries — line 169
# variable: key — line 169
# definition: mapping — line 178
# parameter: deep — line 179
# parameter: loader — line 179
# parameter: node — line 179
# variable: result — line 182
# variable: key_node — line 183
# variable: value_node — line 183
# variable: key — line 184
# definition: yaml_bytes — line 194
# parameter: data — line 194
# variable: text — line 198
# variable: count — line 199
# variable: depth — line 199
# variable: event — line 200
# variable: count — line 201
# variable: depth — line 207
# variable: depth — line 211
# variable: documents — line 214
# variable: documents — line 215
# variable: item — line 215
# variable: item — line 217
# END CODE MAP

from __future__ import annotations

import json
import math
import re
import stat
from pathlib import Path
from typing import Any

import yaml
from yaml.nodes import MappingNode

MAX_BYTES = 1024 * 1024


def integer(value: object, low: int, high: int) -> int:
    """Return an explicitly bounded integer; bool, floats and coercible strings are rejected."""
    if type(value) is not int or not low <= value <= high:
        raise ValueError("bounded integer required")
    return value


def record(value: Any, fields: set[str]) -> dict[str, Any]:
    """Require an exact string-keyed record without hidden/unknown fields."""
    if not isinstance(value, dict) or set(value) != fields:
        raise ValueError("closed record required")
    return value


def digest(value: object, size: int = 64) -> str:
    """Require a nonzero lowercase hex digest or revision, not an authenticity assertion."""
    if (
        not isinstance(value, str)
        or not re.fullmatch(rf"[0-9a-f]{{{size}}}", value)
        or int(value, 16) == 0
    ):
        raise ValueError("invalid digest")
    return value


def bounded_tree(value: Any, depth: int = 0, budget: list[int] | None = None) -> None:
    """Reject excessive nesting/nodes, nonfinite numbers, non-string keys and non-JSON YAML objects."""
    if budget is None:
        budget = [50_000]
    budget[0] -= 1
    if depth > 24 or budget[0] < 0:
        raise ValueError("document structure exceeds bounds")
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ValueError("string keys required")
            bounded_tree(child, depth + 1, budget)
    elif isinstance(value, list):
        for child in value:
            bounded_tree(child, depth + 1, budget)
    elif (
        type(value) not in (str, int, float, bool, type(None))
        or isinstance(value, float)
        and not math.isfinite(value)
    ):
        raise ValueError("only finite JSON-compatible values permitted")


def unique(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys so one consumer cannot see a different hidden configuration."""
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate key")
        result[key] = value
    return result


def read_bytes(path: Path) -> bytes:
    """Read one bounded ordinary explicit file; reject links/reparse points before opening."""
    info = path.lstat()
    if (
        not stat.S_ISREG(info.st_mode)
        or path.is_symlink()
        or getattr(info, "st_file_attributes", 0) & 1024
    ):
        raise ValueError("ordinary file required")
    with path.open("rb") as stream:
        data = stream.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise ValueError("document too large")
    return data


def json_bytes(data: bytes) -> Any:
    """Parse bounded UTF-8 JSON, duplicate-aware, without NaN or executable deserialization."""
    if len(data) > MAX_BYTES:
        raise ValueError("document too large")
    value = json.loads(data.decode("utf-8"), object_pairs_hook=unique)
    bounded_tree(value)
    return value


class ClosedLoader(yaml.SafeLoader):
    """Safe YAML loader with duplicate-key rejection; aliases are rejected before construction."""


# Copy, never mutate PyYAML's shared resolver table. Restrict booleans to true/false,
# so GitHub's "on" key and selector strings are not coerced by YAML 1.1 surprises.
ClosedLoader.yaml_implicit_resolvers = {
    key: [(tag, pattern) for tag, pattern in entries if tag != "tag:yaml.org,2002:bool"]
    for key, entries in ClosedLoader.yaml_implicit_resolvers.items()
}
ClosedLoader.add_implicit_resolver(
    "tag:yaml.org,2002:bool",
    re.compile(r"^(?:true|True|TRUE|false|False|FALSE)$"),
    list("tTfF"),
)


def mapping(
    loader: ClosedLoader, node: MappingNode, deep: bool = False
) -> dict[str, Any]:
    """Construct a closed YAML map; merge keys cannot replace an explicit duplicate silently."""
    result: dict[str, Any] = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if not isinstance(key, str) or key in result:
            raise ValueError("duplicate/non-string YAML key")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


ClosedLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, mapping)


def yaml_bytes(data: bytes) -> list[dict[str, Any]]:
    """Load at most 100 Kubernetes documents; reject aliases/deep input before allocating a tree."""
    if len(data) > MAX_BYTES:
        raise ValueError("document too large")
    text = data.decode("utf-8")
    count = depth = 0
    for event in yaml.parse(text, Loader=ClosedLoader):
        count += 1
        if isinstance(event, yaml.events.AliasEvent):
            raise ValueError("YAML aliases prohibited")
        if isinstance(
            event, (yaml.events.SequenceStartEvent, yaml.events.MappingStartEvent)
        ):
            depth += 1
        if isinstance(
            event, (yaml.events.SequenceEndEvent, yaml.events.MappingEndEvent)
        ):
            depth -= 1
        if depth > 24 or count > 50_000:
            raise ValueError("YAML structure exceeds bounds")
    documents = list(yaml.load_all(text, Loader=ClosedLoader))
    documents = [item for item in documents if item is not None]
    if not 1 <= len(documents) <= 100 or any(
        not isinstance(item, dict) for item in documents
    ):
        raise ValueError("bounded object documents required")
    bounded_tree(documents)
    return documents
