"""Duplicate/alias/type/file/UTF8/size/nesting adversarial inputs and normal parser boundaries. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: test_integer_negative — line 42
# parameter: value — line 42
# definition: test_json_negative — line 59
# parameter: data — line 59
# definition: test_yaml_negative — line 79
# parameter: data — line 79
# definition: test_structure_caps — line 85
# variable: parse — line 87
# definition: test_digests — line 101
# parameter: value — line 101
# definition: test_records — line 109
# parameter: value — line 109
# definition: test_file_boundaries — line 116
# parameter: tmp_path — line 116
# variable: source — line 118
# END CODE MAP

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pytest
import yaml

from lab.contracts import (
    MAX_BYTES,
    bounded_tree,
    digest,
    integer,
    json_bytes,
    read_bytes,
    record,
    yaml_bytes,
)


@pytest.mark.parametrize("value", [True, False, 1.0, "1", None, -1, 4])
def test_integer_negative(value: object) -> None:
    """Reject bool/coercion/overflow and retain inclusive exact integer boundaries."""
    with pytest.raises(ValueError):
        integer(value, 0, 3)
    assert integer(0, 0, 3) == 0 and integer(3, 0, 3) == 3


@pytest.mark.parametrize(
    "data",
    [
        b'{"x":1,"x":2}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b"\xff",
        b"[" * 40 + b"0" + b"]" * 40,
    ],
)
def test_json_negative(data: bytes) -> None:
    """Reject ambiguous, nonfinite, invalid UTF8 and excessive nested documents."""
    with pytest.raises((ValueError, UnicodeError)):
        json_bytes(data)


@pytest.mark.parametrize(
    "data",
    [
        b"x: 1\nx: 2",
        b"x: &a [1]\ny: *a",
        b"!!python/object/apply:os.system [echo no]",
        b"1: value",
        b"x: 2026-10-13",
        b"x: .inf",
        b"[]",
        b"",
        b"x: " + b"[" * 30 + b"1" + b"]" * 30,
    ],
)
def test_yaml_negative(data: bytes) -> None:
    """Reject aliases, duplicate/non-string keys, executable tags and non-JSON YAML scalar surprises."""
    with pytest.raises((ValueError, yaml.YAMLError)):
        yaml_bytes(data)


def test_structure_caps() -> None:
    """Enforce byte/node/document caps in both parsers; retain normal boolean/string/null data."""
    for parse in (json_bytes, yaml_bytes):
        with pytest.raises(ValueError):
            parse(b" " * (MAX_BYTES + 1))
    with pytest.raises(ValueError):
        bounded_tree([0] * 50_001)
    with pytest.raises(ValueError):
        yaml_bytes(b"x: 1\n---\n" * 101)
    with pytest.raises(ValueError):
        bounded_tree({1: "not-string"})
    assert json_bytes(b'{"a":null,"b":true}') == {"a": None, "b": True}
    assert yaml_bytes(b"x: 1\n---\n\n---\nx: 2") == [{"x": 1}, {"x": 2}]


@pytest.mark.parametrize("value", ["0" * 64, "a" * 63, "A" * 64, 1, "abc"])
def test_digests(value: object) -> None:
    """Invalid fingerprints fail and a well-formed fingerprint is not described as a signature."""
    with pytest.raises(ValueError):
        digest(value)
    assert digest("a" * 64) == "a" * 64


@pytest.mark.parametrize("value", [[], {}, {"x": 1, "extra": 2}, None])
def test_records(value: Any) -> None:
    """Closed record validation must reject absent/additional keys and nonobjects."""
    with pytest.raises(ValueError):
        record(value, {"x"})
    assert record({"x": 1}, {"x"}) == {"x": 1}


def test_file_boundaries(tmp_path: Path) -> None:
    """Read a private ordinary file; directories and oversized files are rejected without exposure."""
    source = tmp_path / "input.json"
    source.write_bytes(json.dumps({"x": 1}).encode())
    assert json_bytes(read_bytes(source)) == {"x": 1}
    with pytest.raises(ValueError):
        read_bytes(tmp_path)
    source.write_bytes(b"x" * (MAX_BYTES + 1))
    with pytest.raises(ValueError):
        read_bytes(source)
