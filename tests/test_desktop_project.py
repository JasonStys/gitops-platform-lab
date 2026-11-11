"""Real original policy/reconciliation oracle coverage for the offline desktop controls. Jason Stys."""
# BEGIN CODE MAP (generated; python scripts/code_map.py)
# definition: execute — line 107
# parameter: parameters — line 107
# parameter: tmp_path — line 107
# variable: stage — line 109
# variable: state — line 113
# variable: files — line 114
# variable: kind — line 114
# variable: summary — line 114
# variable: identity — line 115
# definition: test_prepared_real_currentness_oracles — line 133
# parameter: index — line 133
# parameter: queue — line 133
# parameter: tmp_path — line 133
# parameter: verdict — line 133
# variable: _ — line 135
# variable: files — line 135
# variable: summary — line 135
# variable: result — line 136
# variable: row — line 152
# variable: rows — line 154
# variable: row — line 155
# definition: test_real_rendered_policy_oracles — line 159
# parameter: expected — line 159
# parameter: index — line 159
# parameter: tmp_path — line 159
# variable: _ — line 161
# variable: files — line 161
# variable: result — line 162
# variable: rows — line 166
# variable: row — line 167
# definition: test_actual_authorized_rendered_file_formats — line 171
# parameter: format — line 171
# parameter: tmp_path — line 171
# variable: _ — line 173
# variable: data — line 173
# variable: raw — line 174
# variable: source — line 175
# variable: parameters — line 177
# variable: _ — line 179
# variable: files — line 179
# variable: scope — line 181
# variable: raw — line 184
# definition: test_actual_selected_before_after_and_new_intent — line 187
# parameter: tmp_path — line 187
# variable: _ — line 189
# variable: old — line 189
# variable: current — line 190
# variable: paths — line 192
# variable: data — line 193
# variable: name — line 193
# variable: path — line 194
# variable: parameters — line 197
# variable: _ — line 205
# variable: files — line 205
# variable: result — line 206
# variable: scope — line 206
# definition: test_real_single_snapshot_uses_chosen_clock — line 227
# parameter: tmp_path — line 227
# variable: _ — line 229
# variable: data — line 229
# variable: source — line 230
# variable: parameters — line 232
# variable: _ — line 234
# variable: files — line 234
# definition: test_no_ambiguous_controls_or_execution_path — line 252
# parameter: field — line 252
# parameter: tmp_path — line 252
# parameter: value — line 252
# variable: parameters — line 254
# definition: test_bounded_manifest_errors_are_useful_failures — line 261
# parameter: raw — line 261
# parameter: tmp_path — line 261
# variable: source — line 263
# variable: parameters — line 265
# definition: test_explicit_unknown_exercise_and_wrong_snapshot_shape — line 271
# parameter: tmp_path — line 271
# variable: source — line 277
# variable: parameters — line 279
# definition: test_parseable_unrecognized_inventory_remains_a_deny — line 285
# parameter: tmp_path — line 285
# variable: source — line 287
# variable: parameters — line 289
# variable: _ — line 291
# variable: files — line 291
# definition: test_valid_override_cannot_hide_an_invalid_original_declaration — line 296
# parameter: tmp_path — line 296
# variable: _ — line 298
# variable: data — line 298
# variable: source — line 300
# variable: parameters — line 302
# END CODE MAP

import copy
import hashlib
from contextlib import closing

import pytest
import yaml

from lab import desktop_project as project
from lab.desktop_io import canonical, json_value
from lab.desktop_state import Workspace


def execute(tmp_path, parameters):
    """Run actual original engines and persist their exact output with an ordinary isolated owner profile."""
    stage = tmp_path / "stage"
    stage.mkdir()
    with closing(
        Workspace(tmp_path / "profile", project.PRODUCT, project.ROOT, synthetic=True)
    ) as state:
        kind, summary, files = project.analyze(state, parameters, stage)
        identity = state.save(kind, summary, parameters, files)
        assert state.files(identity) == files
        return kind, summary, files


@pytest.mark.parametrize(
    "index,verdict,queue",
    [
        (2, "NEEDS_REVIEW", 2),
        (3, "RECONCILED_ASSERTED", 0),
        (4, "RECONCILED_ASSERTED", 0),
        (5, "INSUFFICIENT_EVIDENCE", 1),
        (6, "INSUFFICIENT_EVIDENCE", 8),
        (7, "NEEDS_REVIEW", 1),
        (8, "NEEDS_REVIEW", 2),
        (9, "RECONCILED_ASSERTED", 0),
    ],
)
def test_prepared_real_currentness_oracles(tmp_path, index, verdict, queue):
    """Literal independent outcomes distinguish pending intent, recovered state, missing/stale proof and dependency failure."""
    _, summary, files = execute(tmp_path, project.scenario(project.SCENARIOS[index]))
    result = json_value(files["reconciliation.json"])
    assert result["verdict"] == verdict and len(result["review_queue"]) == queue
    assert verdict in summary
    if index == 4:
        assert result["intent_changed"] is False
        assert result["transitions"] == [
            {"check": "applied_revision", "before": "FAIL", "after": "PASS"},
            {"check": "observed_generation", "before": "FAIL", "after": "PASS"},
        ]
    if index == 8:
        assert (
            result["intent_changed"] is True
            and result["before_verdict"] == "RECONCILED_ASSERTED"
        )
    if index == 9:
        assert len(result["checks"]) == 7 and not any(
            row["check"] == "transport_evidence" for row in result["checks"]
        )
    for rows in project.views(files).values():
        assert all(len(project.cells(row)) == 4 for row in rows)


@pytest.mark.parametrize("index,expected", [(0, "ALLOW"), (1, "DENY")])
def test_real_rendered_policy_oracles(tmp_path, index, expected):
    """The original exact five-resource policy actually rejects the changed privilege predicate."""
    _, _, files = execute(tmp_path, project.scenario(project.SCENARIOS[index]))
    result = json_value(files["audit.json"])
    assert result["decision"] == expected and result["resources"] == 5
    assert result["live_enforcement_proven"] is False
    assert result["failures"] == ([] if index == 0 else ["container.security"])
    for rows in project.views(files).values():
        assert all(len(project.cells(row)) == 4 for row in rows)


@pytest.mark.parametrize("format", ["json", "yaml"])
def test_actual_authorized_rendered_file_formats(tmp_path, format):
    """Select real bounded JSON/YAML files; parser and original policy are exercised, not mocked."""
    data, _ = project.prepared("rendered-allow")
    raw = canonical(data) if format == "json" else yaml.safe_dump_all(data).encode()
    source = tmp_path / ("private-render." + format)
    source.write_bytes(raw)
    parameters = project.scenario(project.SCENARIOS[0])
    parameters.update(mode=project.MODES[0], manifest=str(source))
    _, _, files = execute(tmp_path, parameters)
    assert json_value(files["audit.json"])["decision"] == "ALLOW"
    scope = json_value(files["input-scope.json"])
    assert scope["source_bytes_sha256"] == hashlib.sha256(raw).hexdigest()
    assert scope["live_cluster_accessed"] is False and source.read_bytes() == raw
    assert all(str(source).encode() not in raw for raw in files.values())


def test_actual_selected_before_after_and_new_intent(tmp_path):
    """Current desired intent can change explicitly without rewriting the retained prior snapshot or pretending recovery."""
    old, _ = project.prepared("recovered")
    current = copy.deepcopy(old)
    current["captured_at_ms"] += 1
    paths = []
    for name, data in [("before", old), ("current", current)]:
        path = tmp_path / (name + ".json")
        path.write_bytes(canonical(data))
        paths.append(path)
    parameters = project.scenario(project.SCENARIOS[4])
    parameters.update(
        mode=project.MODES[2],
        before=str(paths[0]),
        snapshot=str(paths[1]),
        as_of_ms="1000101",
        desired_sha="e" * 40,
    )
    _, _, files = execute(tmp_path, parameters)
    result, scope = (
        json_value(files["reconciliation.json"]),
        json_value(files["input-scope.json"]),
    )
    assert result["verdict"] == "NEEDS_REVIEW" and result["intent_changed"] is True
    assert result["before_verdict"] == "RECONCILED_ASSERTED"
    assert scope["explicit_desired_override"] == "e" * 40
    assert (
        scope["original_desired_sha"] == "b" * 40
        and scope["effective_desired_sha"] == "e" * 40
    )
    assert (
        scope["original_verdict"] == "RECONCILED_ASSERTED"
        and scope["effective_verdict"] == "NEEDS_REVIEW"
    )
    assert scope["original_snapshot_sha256"] != scope["effective_snapshot_sha256"]
    assert paths[0].read_bytes() == canonical(old) and paths[
        1
    ].read_bytes() == canonical(current)


def test_real_single_snapshot_uses_chosen_clock(tmp_path):
    """A caller-selected actual source and review clock go through the original freshness boundary."""
    data, _ = project.prepared("recovered")
    source = tmp_path / "snapshot.json"
    source.write_bytes(canonical(data))
    parameters = project.scenario(project.SCENARIOS[3])
    parameters.update(mode=project.MODES[1], snapshot=str(source), as_of_ms="1300101")
    _, _, files = execute(tmp_path, parameters)
    assert (
        json_value(files["reconciliation.json"])["verdict"] == "INSUFFICIENT_EVIDENCE"
    )


@pytest.mark.parametrize(
    "field,value",
    [
        ("mode", "apply-cluster"),
        ("exercise", "foreign"),
        ("as_of_ms", "NaN"),
        ("as_of_ms", "١"),
        ("as_of_ms", "999999999999999999999"),
        ("max_age_ms", "0"),
        ("desired_sha", "0" * 40),
    ],
)
def test_no_ambiguous_controls_or_execution_path(tmp_path, field, value):
    """Unsupported live modes, coercible Unicode/nonnumbers and invalid intended revisions remain errors."""
    parameters = project.scenario(project.SCENARIOS[3])
    parameters[field] = value
    with pytest.raises(ValueError):
        execute(tmp_path, parameters)


@pytest.mark.parametrize("raw", [b"a: &a {b: *a}", b"a: [", b"[1,2,3]", b"", b"\xff"])
def test_bounded_manifest_errors_are_useful_failures(tmp_path, raw):
    """Alias/syntax/shape/encoding failures never become successful empty reviews or unhandled GUI callbacks."""
    source = tmp_path / "bad.yaml"
    source.write_bytes(raw)
    parameters = project.scenario(project.SCENARIOS[0])
    parameters.update(mode=project.MODES[0], manifest=str(source))
    with pytest.raises(ValueError):
        execute(tmp_path, parameters)


def test_explicit_unknown_exercise_and_wrong_snapshot_shape(tmp_path):
    """Prepared input is a strict closed vocabulary; single-review input must be a workload object."""
    with pytest.raises(ValueError):
        project.scenario("foreign")
    with pytest.raises(ValueError):
        project.prepared("foreign")
    source = tmp_path / "list.json"
    source.write_bytes(b"[]")
    parameters = project.scenario(project.SCENARIOS[3])
    parameters.update(mode=project.MODES[1], snapshot=str(source))
    with pytest.raises(ValueError):
        execute(tmp_path, parameters)


def test_parseable_unrecognized_inventory_remains_a_deny(tmp_path):
    """A syntactically valid but unsupported manifest is an original static DENY, not a successful empty audit."""
    source = tmp_path / "unrecognized.yaml"
    source.write_bytes(b"{}")
    parameters = project.scenario(project.SCENARIOS[0])
    parameters.update(mode=project.MODES[0], manifest=str(source))
    _, _, files = execute(tmp_path, parameters)
    assert json_value(files["audit.json"])["decision"] == "DENY"
    assert json_value(files["audit.json"])["failures"] == ["contract.invalid"]


def test_valid_override_cannot_hide_an_invalid_original_declaration(tmp_path):
    """Explicit expected-revision customization must not silently repair malformed original evidence."""
    data, _ = project.prepared("recovered")
    data["desired_sha"] = "invalid-source-declaration"
    source = tmp_path / "malformed-snapshot.json"
    source.write_bytes(canonical(data))
    parameters = project.scenario(project.SCENARIOS[3])
    parameters.update(mode=project.MODES[1], snapshot=str(source), desired_sha="b" * 40)
    with pytest.raises(ValueError):
        execute(tmp_path, parameters)
    assert source.read_bytes() == canonical(data)
