"""Owner-local desktop profile, bounded durable bundles and non-overwriting export. Jason Stys.

No host collection, network listener, shell command or public account is involved.
An exclusive OS lock owns one marked profile; SQLite keeps actual core outputs.
"""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# variable: MAX_FILE — line 137
# variable: MAX_BUNDLE — line 138
# variable: MAX_HISTORY — line 139
# variable: MAX_RUNS — line 140
# definition: package_identity — line 143
# parameter: root — line 144
# parameter: product — line 145
# parameter: version — line 146
# parameter: names — line 147
# parameter: resource_limits — line 148
# variable: path — line 151
# variable: value — line 154
# variable: limits — line 178
# variable: value — line 181
# variable: name — line 184
# variable: identity — line 190
# definition: profile_path — line 208
# parameter: name — line 208
# variable: base — line 211
# variable: base — line 213
# variable: base — line 215
# definition: unlinked — line 219
# parameter: path — line 219
# variable: path — line 221
# variable: p — line 222
# definition: admit_existing — line 227
# parameter: path — line 227
# variable: info — line 230
# definition: Workspace — line 242
# definition: __init__ — line 245
# parameter: path — line 246
# parameter: product — line 246
# parameter: resources — line 246
# parameter: self — line 246
# parameter: synthetic — line 246
# variable: name — line 255
# variable: marker — line 264
# variable: expected — line 265
# variable: stream — line 269
# variable: actual — line 272
# variable: flags — line 280
# variable: info — line 288
# variable: database — line 302
# variable: connection — line 314
# definition: connect — line 335
# parameter: self — line 335
# variable: name — line 339
# variable: connection — line 346
# definition: close — line 356
# parameter: self — line 356
# definition: save — line 362
# parameter: self — line 363
# parameter: kind — line 364
# parameter: summary — line 365
# parameter: parameters — line 366
# parameter: files — line 367
# variable: name — line 375
# variable: value — line 380
# variable: data — line 384
# variable: total — line 384
# variable: data — line 385
# variable: connection — line 387
# variable: count — line 389
# variable: size — line 390
# variable: identity — line 397
# variable: data — line 417
# variable: name — line 417
# definition: history — line 422
# parameter: self — line 422
# variable: connection — line 424
# variable: rows — line 425
# variable: row — line 431
# definition: _rows — line 434
# parameter: connection — line 435
# parameter: identity — line 435
# parameter: self — line 435
# variable: count — line 438
# variable: largest — line 438
# variable: total — line 438
# variable: rows — line 444
# variable: row — line 452
# variable: row — line 459
# definition: files — line 464
# parameter: identity — line 464
# parameter: self — line 464
# variable: connection — line 468
# variable: rows — line 470
# variable: _digest — line 471
# variable: data — line 471
# variable: name — line 471
# definition: remove — line 473
# parameter: expected — line 473
# parameter: identity — line 473
# parameter: self — line 473
# variable: connection — line 477
# variable: rows — line 479
# variable: _data — line 480
# variable: digest — line 480
# variable: manifest — line 480
# variable: name — line 480
# definition: export — line 486
# parameter: identity — line 486
# parameter: parent — line 486
# parameter: product — line 486
# parameter: self — line 486
# variable: files — line 488
# variable: parent — line 491
# variable: target — line 494
# variable: data — line 496
# variable: name — line 496
# variable: stream — line 499
# END CODE MAP

from __future__ import annotations

import hashlib
import os
import re
import secrets
import sqlite3
import stat
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from .desktop_io import Rejected, canonical, json_value, read_bytes
from .inputs import file_hash

MAX_FILE = 32 * 1024 * 1024
MAX_BUNDLE = 64 * 1024 * 1024
MAX_HISTORY = 128 * 1024 * 1024
MAX_RUNS = 20


def package_identity(
    root: Path,
    product: str,
    version: str,
    names: tuple[str, ...],
    resource_limits: dict[str, int] | None = None,
) -> dict[str, Any]:
    """Bind frozen resource bytes to reviewed source metadata before opening a durable profile."""
    path = root / "native-release.json"
    if not path.exists() and not getattr(sys, "frozen", False):
        return {"source": "development", "source_dirty": True}
    value = json_value(read_bytes(path, 16384))
    if not isinstance(value, dict) or set(value) != {
        "schema",
        "product",
        "version",
        "source",
        "source_dirty",
        "resources",
    }:
        raise Rejected("invalid package identity")
    if (
        type(value["schema"]) is not int
        or value["schema"] != 1
        or value["product"] != product
        or value["version"] != version
        or not isinstance(value["source"], str)
        or re.fullmatch("[a-f0-9]{40}", value["source"]) is None
        or type(value["source_dirty"]) is not bool
    ):
        raise Rejected("invalid package source identity")
    if not isinstance(value["resources"], dict) or set(value["resources"]) != set(
        names
    ):
        raise Rejected("incomplete package resources")
    limits = resource_limits or {}
    if set(limits) - set(names) or any(
        type(value) is not int or not MAX_FILE <= value <= 128 * 1024 * 1024
        for value in limits.values()
    ):
        raise Rejected("invalid fixed package resource bounds")
    for name in names:
        if (
            file_hash(root / name, limits.get(name, MAX_FILE))
            != value["resources"][name]
        ):
            raise Rejected("package resource hash mismatch")
    identity = {"source": value["source"], "source_dirty": value["source_dirty"]}
    if getattr(sys, "frozen", False):
        if (
            sys.version_info[:3] != (3, 14, 10)
            or "python314.dll" not in value["resources"]
        ):
            raise Rejected(
                "frozen application requires patched CPython3.14.10 and its verified runtime DLL"
            )
        identity.update(
            {
                "python_version": sys.version.split()[0],
                "python_dll_sha256": value["resources"]["python314.dll"],
            }
        )
    return identity


def profile_path(name: str) -> Path:
    """Select a version-independent OS-local workspace, never the executable directory."""
    if sys.platform == "win32":
        base = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    elif sys.platform == "darwin":
        base = Path.home() / "Library/Application Support"
    else:
        base = Path(os.environ.get("XDG_DATA_HOME", Path.home() / ".local/share"))
    return base / "JasonStys" / name


def unlinked(path: Path) -> Path:
    """Reject linked ancestors before normalizing a caller-selected local path."""
    path = path.absolute()
    if any(p.is_symlink() or p.is_junction() for p in (path, *path.parents)):
        raise Rejected("linked workspace or output path")
    return path.resolve()


def admit_existing(path: Path) -> None:
    """Refuse pre-existing linked/nonregular fixed state before initialization can write through an alias."""
    try:
        info = path.lstat()
    except FileNotFoundError:
        return
    if (
        not stat.S_ISREG(info.st_mode)
        or info.st_nlink != 1
        or getattr(info, "st_file_attributes", 0)
        & getattr(stat, "FILE_ATTRIBUTE_REPARSE_POINT", 0)
    ):
        raise Rejected("fixed workspace state must be unlinked one-link regular files")


class Workspace:
    """One-owner plaintext history; preserving evidence does not authenticate its publisher or analyst."""

    def __init__(
        self, path: Path, product: str, resources: Path, *, synthetic: bool = False
    ) -> None:
        """Open only a new or explicitly marked profile and take an exclusive nonblocking OS lock."""
        self.path = unlinked(path)
        if self.path.is_relative_to(resources.resolve()) or self.path.is_relative_to(
            Path(sys.executable).parent.resolve()
        ):
            raise Rejected("workspace must be outside the application installation")
        self.path.mkdir(parents=True, exist_ok=True, mode=0o700)
        for name in (
            "profile.json",
            "instance.lock",
            "history.sqlite",
            "history.sqlite-journal",
            "history.sqlite-wal",
            "history.sqlite-shm",
        ):
            admit_existing(self.path / name)
        marker = self.path / "profile.json"
        expected = {"schema": 1, "product": product, "synthetic_acceptance": synthetic}
        if not marker.exists():
            if any(self.path.iterdir()):
                raise Rejected("unknown nonempty workspace; no files were reset")
            with marker.open("xb") as stream:
                os.chmod(marker, 0o600)
                stream.write(canonical(expected))
        actual = json_value(read_bytes(marker, 4096))
        if (
            not isinstance(actual, dict)
            or actual != expected
            or type(actual.get("schema")) is not int
            or type(actual.get("synthetic_acceptance")) is not bool
        ):
            raise Rejected("workspace belongs to another application or profile type")
        flags = (
            os.O_RDWR
            | os.O_CREAT
            | getattr(os, "O_NOFOLLOW", 0)
            | getattr(os, "O_NONBLOCK", 0)
        )
        self.lock = os.open(self.path / "instance.lock", flags, 0o600)
        try:
            info = os.fstat(self.lock)
            if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1:
                raise Rejected("workspace lock must be a regular one-link file")
            if info.st_size == 0:
                os.write(self.lock, b"0")
            os.lseek(self.lock, 0, os.SEEK_SET)
            if sys.platform == "win32":
                import msvcrt

                msvcrt.locking(self.lock, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self.lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            database = self.path / "history.sqlite"
            if (
                database.is_symlink()
                or database.is_junction()
                or database.exists()
                and (
                    not stat.S_ISREG(database.lstat().st_mode)
                    or database.lstat().st_nlink != 1
                )
            ):
                raise Rejected("linked history database")
            self.database = database
            with closing(self.connect()) as connection, connection:
                connection.executescript("""
                    CREATE TABLE IF NOT EXISTS run(id INTEGER PRIMARY KEY, created TEXT NOT NULL, kind TEXT NOT NULL,
                        summary TEXT NOT NULL, parameters TEXT NOT NULL) STRICT;
                    CREATE TABLE IF NOT EXISTS bundle(run_id INTEGER NOT NULL REFERENCES run(id), name TEXT NOT NULL,
                        payload BLOB NOT NULL, sha256 TEXT NOT NULL, PRIMARY KEY(run_id,name)) STRICT;
                    CREATE TABLE IF NOT EXISTS counter(id INTEGER PRIMARY KEY CHECK(id=1),next_id INTEGER NOT NULL CHECK(next_id>0)) STRICT;
                    INSERT OR IGNORE INTO counter VALUES(1,(SELECT coalesce(max(id),0)+1 FROM run));
                """)
                if (
                    connection.execute("PRAGMA integrity_check").fetchone() != ("ok",)
                    or connection.execute("PRAGMA foreign_key_check").fetchall()
                ):
                    raise Rejected(
                        "history integrity check failed; retain a private backup"
                    )
            os.chmod(database, 0o600)
        except BaseException:
            os.close(self.lock)
            raise

    def connect(self) -> sqlite3.Connection:
        """Use short transactions and no shared mutable SQLite connection across GUI/worker threads."""
        if self.lock < 0:
            raise Rejected("workspace is closed")
        for name in (
            "history.sqlite",
            "history.sqlite-journal",
            "history.sqlite-wal",
            "history.sqlite-shm",
        ):
            admit_existing(self.path / name)
        connection = sqlite3.connect(self.database, timeout=5)
        try:
            connection.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, MAX_FILE + 8192)
            connection.execute("PRAGMA foreign_keys=ON")
            connection.execute("PRAGMA synchronous=FULL")
        except BaseException:
            connection.close()
            raise
        return connection

    def close(self) -> None:
        """Release only this process's owned lock; saved bundles are never removed during shutdown."""
        if self.lock >= 0:
            os.close(self.lock)
            self.lock = -1

    def save(
        self,
        kind: str,
        summary: str,
        parameters: dict[str, str],
        files: dict[str, bytes],
    ) -> int:
        """Atomically retain a completed real-core bundle; finite limits fail without evicting earlier evidence."""
        if (
            not files
            or len(files) > 8
            or any(
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", name) is None
                for name in files
            )
        ):
            raise Rejected("invalid output bundle names")
        if (
            sum(len(value.encode("utf-8")) for value in parameters.values())
            > 512 * 1024
        ):
            raise Rejected("desktop parameter text exceeds its limit")
        total = sum(len(data) for data in files.values())
        if total > MAX_BUNDLE or any(len(data) > MAX_FILE for data in files.values()):
            raise Rejected("desktop bundle exceeds its documented byte limit")
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            count = connection.execute("SELECT count(*) FROM run").fetchone()[0]
            size = connection.execute(
                "SELECT coalesce(sum(length(payload)),0) FROM bundle"
            ).fetchone()[0]
            if count >= MAX_RUNS or size + total > MAX_HISTORY:
                raise Rejected(
                    "desktop history is full; export backups and explicitly remove selected local analyses"
                )
            identity = int(
                connection.execute("SELECT next_id FROM counter WHERE id=1").fetchone()[
                    0
                ]
            )
            connection.execute(
                "INSERT INTO run(id,created,kind,summary,parameters) VALUES(?,?,?,?,?)",
                (
                    identity,
                    datetime.now(UTC).isoformat(),
                    kind,
                    summary[:500],
                    canonical(parameters).decode(),
                ),
            )
            connection.execute("UPDATE counter SET next_id=next_id+1 WHERE id=1")
            connection.executemany(
                "INSERT INTO bundle VALUES(?,?,?,?)",
                [
                    (identity, name, data, hashlib.sha256(data).hexdigest())
                    for name, data in files.items()
                ],
            )
        return identity

    def history(self) -> list[dict[str, Any]]:
        """List bounded local history newest first without reading all private report payloads."""
        with closing(self.connect()) as connection:
            rows = connection.execute(
                "SELECT id,created,kind,summary FROM run ORDER BY id DESC LIMIT ?",
                (MAX_RUNS,),
            ).fetchall()
        return [
            dict(zip(("id", "created", "kind", "summary"), row, strict=True))
            for row in rows
        ]

    def _rows(
        self, connection: sqlite3.Connection, identity: int
    ) -> list[tuple[str, bytes, str]]:
        """Check row/aggregate bounds before fetching BLOBs inside the caller's SQLite snapshot."""
        count, total, largest = connection.execute(
            "SELECT count(*),coalesce(sum(length(payload)),0),coalesce(max(length(payload)),0) FROM bundle WHERE run_id=?",
            (identity,),
        ).fetchone()
        if not 1 <= count <= 8 or total > MAX_BUNDLE or largest > MAX_FILE:
            raise Rejected("saved analysis is missing or outside byte/count limits")
        rows = connection.execute(
            "SELECT name,payload,sha256 FROM bundle WHERE run_id=?", (identity,)
        ).fetchall()
        if (
            not rows
            or len(rows) > 8
            or any(
                re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,95}", row[0]) is None
                for row in rows
            )
        ):
            raise Rejected("saved analysis is missing or malformed")
        if any(
            not isinstance(row[1], bytes)
            or hashlib.sha256(row[1]).hexdigest() != row[2]
            for row in rows
        ):
            raise Rejected("saved analysis hash/size check failed")
        return rows

    def files(self, identity: int) -> dict[str, bytes]:
        """Read only one exact existing bundle and verify every stored byte hash before rendering/export."""
        if type(identity) is not int or identity < 1:
            raise Rejected("select a saved analysis first")
        with closing(self.connect()) as connection:
            connection.execute("BEGIN")
            rows = self._rows(connection, identity)
        return {name: bytes(data) for name, data, _digest in rows}

    def remove(self, identity: int, expected: str) -> None:
        """Delete only one explicitly confirmed exact local bundle; original input/export files are never removed."""
        if type(identity) is not int or identity < 1:
            raise Rejected("select a saved analysis first")
        with closing(self.connect()) as connection, connection:
            connection.execute("BEGIN IMMEDIATE")
            rows = self._rows(connection, identity)
            manifest = {name: digest for name, _data, digest in rows}
            if hashlib.sha256(canonical(manifest)).hexdigest() != expected:
                raise Rejected("saved bundle changed after selection")
            connection.execute("DELETE FROM bundle WHERE run_id=?", (identity,))
            connection.execute("DELETE FROM run WHERE id=?", (identity,))

    def export(self, identity: int, parent: Path, product: str) -> Path:
        """Copy a verified bundle into a new owner-selected directory; do not overwrite or execute its contents."""
        files = self.files(identity)
        if re.fullmatch(r"[a-z0-9][a-z0-9-]{1,79}", product) is None:
            raise Rejected("invalid export product namespace")
        parent = unlinked(parent)
        if not parent.is_dir():
            raise Rejected("select an existing private export parent")
        target = parent / f"{product}-run-{identity}-{secrets.token_hex(4)}"
        target.mkdir(mode=0o700)
        for name, data in files.items():
            if Path(name).name != name or ":" in name:
                raise Rejected("invalid saved export name")
            with (target / name).open("xb") as stream:
                os.chmod(stream.name, 0o600)
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
        return target
