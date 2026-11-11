"""Bounded regular descriptor reads and strict finite JSON for owner-local desktop state. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: Rejected — line 36
# definition: read_bytes — line 40
# parameter: limit — line 40
# parameter: path — line 40
# variable: descriptor — line 49
# variable: stream — line 56
# variable: content — line 59
# definition: pairs — line 67
# parameter: items — line 67
# variable: result — line 69
# variable: name — line 70
# variable: value — line 70
# definition: nonfinite — line 77
# parameter: value — line 77
# definition: finite_float — line 82
# parameter: value — line 82
# variable: result — line 84
# definition: json_value — line 90
# parameter: content — line 90
# definition: canonical — line 103
# parameter: value — line 103
# END CODE MAP

from __future__ import annotations

import json
import math
import os
import stat
from pathlib import Path
from typing import Any


class Rejected(ValueError):
    """Input or output was refused; messages deliberately exclude raw host contents."""


def read_bytes(path: Path, limit: int) -> bytes:
    """Read at most limit bytes from a regular final path; refuse links and devices."""
    try:
        if (
            path.is_symlink()
            or path.is_junction()
            or not stat.S_ISREG(path.lstat().st_mode)
        ):
            raise Rejected("input must be a regular file, not a link")
        descriptor = os.open(
            path,
            os.O_RDONLY
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
            | getattr(os, "O_BINARY", 0),
        )
        with os.fdopen(descriptor, "rb") as stream:
            if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                raise Rejected("input changed file type")
            content = stream.read(limit + 1)
        if len(content) > limit:
            raise Rejected("input exceeds its size limit")
        return content
    except OSError as error:
        raise Rejected("input unavailable") from error


def pairs(items: list[tuple[str, Any]]) -> dict[str, Any]:
    """Reject duplicate JSON keys instead of allowing ambiguous last-value-wins parsing."""
    result: dict[str, Any] = {}
    for name, value in items:
        if name in result:
            raise Rejected("duplicate JSON key")
        result[name] = value
    return result


def nonfinite(value: str) -> None:
    """Refuse NaN/Infinity even though Python's default JSON decoder accepts them."""
    raise Rejected("non-finite JSON value")


def finite_float(value: str) -> float:
    """Reject exponent-overflow infinities as well as explicitly named NaN/Infinity constants."""
    result = float(value)
    if not math.isfinite(result):
        raise Rejected("non-finite JSON number")
    return result


def json_value(content: bytes) -> Any:
    """Parse UTF-8 JSON with finite values and unambiguous keys; fail on deep/malformed data."""
    try:
        return json.loads(
            content,
            object_pairs_hook=pairs,
            parse_constant=nonfinite,
            parse_float=finite_float,
        )
    except (UnicodeError, ValueError, RecursionError) as error:
        raise Rejected("invalid or ambiguous JSON") from error


def canonical(value: Any) -> bytes:
    """Encode finite, stable JSON for hashing and public-safe synthetic evidence."""
    return (
        json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False) + "\n"
    ).encode()
