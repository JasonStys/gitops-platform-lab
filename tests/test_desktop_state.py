"""Independent offline desktop ownership, byte-bound, SQLite and non-overwrite regressions. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: state — line 95
# parameter: tmp_path — line 95
# variable: workspace — line 97
# definition: test_atomic_history_export_reopen_and_exclusive_owner — line 106
# parameter: state — line 106
# parameter: tmp_path — line 106
# variable: files — line 108
# variable: identity — line 112
# variable: first — line 119
# variable: second — line 120
# variable: path — line 122
# variable: reopened — line 124
# definition: test_foreign_marker_is_never_reset — line 140
# parameter: marker — line 140
# parameter: tmp_path — line 140
# variable: root — line 142
# variable: original — line 144
# definition: test_unknown_install_and_profile_type_boundaries — line 152
# parameter: tmp_path — line 152
# variable: unknown — line 154
# variable: real — line 163
# definition: test_nonportable_or_traversal_bundle_name_rejected — line 176
# parameter: name — line 176
# parameter: state — line 176
# definition: test_finite_storage_rejects_without_evicting_previous_evidence — line 183
# parameter: monkeypatch — line 183
# parameter: state — line 183
# variable: identity — line 186
# variable: limit — line 187
# variable: payload — line 187
# variable: value — line 187
# variable: patch — line 193
# definition: test_tamper_missing_export_namespace_and_collision — line 212
# parameter: monkeypatch — line 212
# parameter: state — line 212
# parameter: tmp_path — line 212
# variable: identity — line 214
# variable: invalid — line 215
# parameter: _count — line 222
# variable: existing — line 223
# variable: connection — line 228
# definition: test_confirmed_retention_rejects_stale_manifest_and_never_reuses_identity — line 237
# parameter: state — line 238
# parameter: tmp_path — line 238
# variable: original — line 241
# variable: identity — line 242
# variable: exported — line 243
# variable: manifest — line 244
# variable: data — line 245
# variable: name — line 245
# variable: expected — line 247
# definition: test_corrupt_database_preserves_bytes_and_releases_lock — line 265
# parameter: state — line 265
# parameter: tmp_path — line 265
# variable: _ — line 269
# definition: test_os_local_version_independent_path_selection — line 279
# parameter: monkeypatch — line 280
# parameter: platform — line 280
# parameter: tmp_path — line 280
# parameter: variable — line 280
# variable: result — line 287
# definition: test_frozen_package_identity_binds_exact_resources_before_state — line 295
# parameter: defect — line 296
# parameter: monkeypatch — line 296
# parameter: tmp_path — line 296
# variable: names — line 299
# variable: name — line 300
# variable: hashes — line 302
# variable: name — line 304
# variable: metadata — line 306
# definition: test_frozen_runtime_requires_patched_version_and_actual_bound_dll — line 345
# parameter: monkeypatch — line 346
# parameter: tmp_path — line 346
# variable: names — line 349
# variable: payload — line 350
# variable: digest — line 352
# variable: metadata — line 353
# variable: result — line 368
# END CODE MAP

import hashlib
import json
import sqlite3
from contextlib import closing

import pytest

from lab import desktop_state as module
from lab.desktop_io import Rejected


@pytest.fixture
def state(tmp_path):
    """Own an isolated temporary profile; never select a real OS-default workspace."""
    workspace = module.Workspace(
        tmp_path / "profile", "fixture-app", tmp_path / "installation"
    )
    try:
        yield workspace
    finally:
        workspace.close()


def test_atomic_history_export_reopen_and_exclusive_owner(state, tmp_path):
    """Durable exact bytes survive reopening, exported files are private copies, and no listener/profile is adopted."""
    files = {
        "report.json": b'{"synthetic":true}\n',
        "report.html": b"<p>inert fictional evidence</p>",
    }
    identity = state.save(
        "x'); DROP TABLE run;--", "fictional case", {"input": "authorized.json"}, files
    )
    assert identity == 1 and state.files(identity) == files
    with pytest.raises((OSError, Rejected)):
        module.Workspace(state.path, "fixture-app", tmp_path / "installation")
    assert state.history()[0]["kind"] == "x'); DROP TABLE run;--"
    first = state.export(identity, tmp_path, "fixture-app")
    second = state.export(identity, tmp_path, "fixture-app")
    assert first != second
    assert {path.name: path.read_bytes() for path in first.iterdir()} == files
    state.close()
    reopened = module.Workspace(state.path, "fixture-app", tmp_path / "installation")
    try:
        assert reopened.files(1) == files and len(reopened.history()) == 1
    finally:
        reopened.close()


@pytest.mark.parametrize(
    "marker",
    [
        [],
        {"schema": True, "product": "fixture-app", "synthetic_acceptance": False},
        {"schema": 1, "product": "fixture-app", "synthetic_acceptance": 0},
        {"schema": 1, "product": "other-app", "synthetic_acceptance": False},
    ],
)
def test_foreign_marker_is_never_reset(tmp_path, marker):
    """Unknown/ambiguous profile identity cannot be mistaken for an empty usable database."""
    root = tmp_path / "unknown"
    root.mkdir()
    original = json.dumps(marker).encode()
    (root / "profile.json").write_bytes(original)
    with pytest.raises(Rejected):
        module.Workspace(root, "fixture-app", tmp_path / "installation")
    assert (root / "profile.json").read_bytes() == original
    assert not (root / "history.sqlite").exists()


def test_unknown_install_and_profile_type_boundaries(tmp_path):
    """Acceptance cannot enter an existing normal profile; installation and unrelated documents remain untouched."""
    unknown = tmp_path / "unknown"
    unknown.mkdir()
    (unknown / "document").write_bytes(b"keep")
    with pytest.raises(Rejected, match="unknown"):
        module.Workspace(unknown, "fixture-app", tmp_path / "install")
    with pytest.raises(Rejected, match="outside"):
        module.Workspace(
            tmp_path / "install/subdir", "fixture-app", tmp_path / "install"
        )
    real = module.Workspace(tmp_path / "real", "fixture-app", tmp_path / "install")
    real.close()
    with pytest.raises(Rejected):
        module.Workspace(
            tmp_path / "real", "fixture-app", tmp_path / "install", synthetic=True
        )
    assert (unknown / "document").read_bytes() == b"keep"


@pytest.mark.parametrize(
    "name",
    ["../outside.json", "..", "", "C:stream", "folder\\report.json", "x/y", "é.json"],
)
def test_nonportable_or_traversal_bundle_name_rejected(state, name):
    """No report name can become a path, alternate stream, parent directory or ambiguous portable output."""
    with pytest.raises(Rejected, match="names"):
        state.save("fixture", "case", {}, {name: b"inert"})
    assert state.history() == []


def test_finite_storage_rejects_without_evicting_previous_evidence(state, monkeypatch):
    """History/individual/aggregate caps are fail-closed and never drop older completed runs automatically."""
    assert module.MAX_FILE == 32 * 1024 * 1024 and module.MAX_RUNS == 20
    identity = state.save("fixture", "one", {}, {"report.json": b"0123456789"})
    for limit, value, payload in [
        ("MAX_FILE", 9, b"0123456789"),
        ("MAX_BUNDLE", 9, b"0123456789"),
        ("MAX_HISTORY", 19, b"0123456789"),
        ("MAX_RUNS", 1, b"x"),
    ]:
        with monkeypatch.context() as patch:
            patch.setattr(module, limit, value)
            with pytest.raises(Rejected):
                state.save("fixture", "two", {}, {"report.json": payload})
        assert (
            len(state.history()) == 1
            and state.files(identity)["report.json"] == b"0123456789"
        )
    with pytest.raises(Rejected):
        state.save(
            "fixture",
            "large parameters",
            {"field": "x" * (512 * 1024 + 1)},
            {"report.json": b"x"},
        )
    with pytest.raises(Rejected):
        state.save("fixture", "empty", {}, {})


def test_tamper_missing_export_namespace_and_collision(state, tmp_path, monkeypatch):
    """Hash mismatches and unavailable/malicious output selections never masquerade as successful exports."""
    identity = state.save("fixture", "one", {}, {"report.json": b"original"})
    for invalid in (0, True, 99):
        with pytest.raises(Rejected):
            state.files(invalid)
    with pytest.raises(Rejected):
        state.export(identity, tmp_path, "../escape")
    with pytest.raises(Rejected):
        state.export(identity, tmp_path / "missing", "fixture-app")
    monkeypatch.setattr(module.secrets, "token_hex", lambda _count: "fixed")
    existing = tmp_path / "fixture-app-run-1-fixed"
    existing.mkdir()
    (existing / "keep").write_bytes(b"unchanged")
    with pytest.raises(FileExistsError):
        state.export(identity, tmp_path, "fixture-app")
    with closing(state.connect()) as connection, connection:
        connection.execute(
            "UPDATE bundle SET payload=? WHERE run_id=?", (b"changed", identity)
        )
    with pytest.raises(Rejected, match="hash"):
        state.files(identity)
    assert (existing / "keep").read_bytes() == b"unchanged"


def test_confirmed_retention_rejects_stale_manifest_and_never_reuses_identity(
    state, tmp_path
):
    """Only one exact local bundle is removed; exports remain intact and later run IDs are not recycled."""
    original = {"report.json": b"original"}
    identity = state.save("fixture", "one", {}, original)
    exported = state.export(identity, tmp_path, "fixture-app")
    manifest = {
        name: hashlib.sha256(data).hexdigest() for name, data in original.items()
    }
    expected = hashlib.sha256(module.canonical(manifest)).hexdigest()
    with pytest.raises(Rejected):
        state.remove(identity, "a" * 64)
    assert state.files(identity) == original
    state.remove(identity, expected)
    assert (
        state.history() == [] and (exported / "report.json").read_bytes() == b"original"
    )
    with pytest.raises(Rejected):
        state.remove(identity, expected)
    with pytest.raises(Rejected):
        state.remove(True, expected)
    assert state.save("fixture", "two", {}, original) == identity + 1
    state.close()
    with pytest.raises(Rejected, match="closed"):
        state.history()


def test_corrupt_database_preserves_bytes_and_releases_lock(state, tmp_path):
    """A broken existing SQLite file yields a rejection, never a reset, and closes the failed connection/lock."""
    state.close()
    state.database.write_bytes(b"not a SQLite database")
    for _ in range(2):
        with pytest.raises(sqlite3.DatabaseError):
            module.Workspace(state.path, "fixture-app", tmp_path / "install")
    assert state.database.read_bytes() == b"not a SQLite database"


@pytest.mark.parametrize(
    "platform,variable",
    [("win32", "LOCALAPPDATA"), ("darwin", None), ("linux", "XDG_DATA_HOME")],
)
def test_os_local_version_independent_path_selection(
    tmp_path, monkeypatch, platform, variable
):
    """Selecting a platform path does not create or inspect a real user workspace."""
    monkeypatch.setattr(module.sys, "platform", platform)
    monkeypatch.setattr(module.Path, "home", lambda: tmp_path)
    if variable:
        monkeypatch.setenv(variable, str(tmp_path))
    result = module.profile_path("FixtureWorkbench")
    assert result.is_relative_to(tmp_path) and result.name == "FixtureWorkbench"
    assert not result.exists()


@pytest.mark.parametrize(
    "defect", [None, "source", "schema", "dirty", "missing", "hash", "extra"]
)
def test_frozen_package_identity_binds_exact_resources_before_state(
    tmp_path, monkeypatch, defect
):
    """A version label or successful compilation cannot authorize missing/mismatched bundled resource bytes."""
    names = ("policy.yml", "notices.txt")
    for name in names:
        (tmp_path / name).write_bytes(b"authored inert fixture")
    hashes = {
        name: hashlib.sha256((tmp_path / name).read_bytes()).hexdigest()
        for name in names
    }
    metadata = {
        "schema": 1,
        "product": "fixture-app",
        "version": "1.1.0",
        "source": "a" * 40,
        "source_dirty": False,
        "resources": hashes,
    }
    if defect == "source":
        metadata["source"] = "main"
    if defect == "schema":
        metadata["schema"] = True
    if defect == "dirty":
        metadata["source_dirty"] = 0
    if defect == "missing":
        del hashes["policy.yml"]
    if defect == "hash":
        (tmp_path / "notices.txt").write_bytes(b"changed")
    if defect == "extra":
        metadata["private_path"] = "not allowed"
    (tmp_path / "native-release.json").write_text(json.dumps(metadata))
    if defect:
        with pytest.raises(Rejected):
            module.package_identity(tmp_path, "fixture-app", "1.1.0", names)
    else:
        assert module.package_identity(tmp_path, "fixture-app", "1.1.0", names) == {
            "source": "a" * 40,
            "source_dirty": False,
        }
    (tmp_path / "native-release.json").unlink()
    assert (
        module.package_identity(tmp_path, "fixture-app", "1.1.0", names)["source_dirty"]
        is True
    )
    monkeypatch.setattr(module.sys, "frozen", True, raising=False)
    with pytest.raises(Rejected):
        module.package_identity(tmp_path, "fixture-app", "1.1.0", names)


def test_frozen_runtime_requires_patched_version_and_actual_bound_dll(
    tmp_path, monkeypatch
):
    """Inert resource fixtures test gate shape; actual executable acceptance separately proves the real interpreter DLL."""
    names = ("python314.dll",)
    payload = b"inert DLL hash fixture; never loaded or executed"
    (tmp_path / names[0]).write_bytes(payload)
    digest = hashlib.sha256(payload).hexdigest()
    metadata = {
        "schema": 1,
        "product": "fixture-app",
        "version": "1.1.0",
        "source": "a" * 40,
        "source_dirty": False,
        "resources": {names[0]: digest},
    }
    (tmp_path / "native-release.json").write_text(json.dumps(metadata))
    monkeypatch.setattr(module.sys, "frozen", True, raising=False)
    monkeypatch.setattr(module.sys, "version_info", (3, 14, 6))
    with pytest.raises(Rejected, match="patched"):
        module.package_identity(tmp_path, "fixture-app", "1.1.0", names)
    monkeypatch.setattr(module.sys, "version_info", (3, 14, 10))
    monkeypatch.setattr(module.sys, "version", "3.14.10 (inert gate fixture)")
    result = module.package_identity(tmp_path, "fixture-app", "1.1.0", names)
    assert (
        result["python_version"] == "3.14.10" and result["python_dll_sha256"] == digest
    )
    metadata["resources"] = {}
    (tmp_path / "native-release.json").write_text(json.dumps(metadata))
    with pytest.raises(Rejected, match="patched"):
        module.package_identity(tmp_path, "fixture-app", "1.1.0", ())
