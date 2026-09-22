"""Stimulus snapshots are immutable and every version traces back to the paper's own set."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lsx.shame_axis import stimuli  # noqa: E402


def committed_versions():
    return sorted(p.name for p in stimuli.STIMULI.iterdir() if (p / "manifest.json").exists())


@pytest.mark.parametrize("version", committed_versions())
def test_every_committed_snapshot_matches_its_manifest(version):
    items = stimuli.load(version)            # raises SnapshotCorrupted on any drift
    assert stimuli.manifest(version)["n_items"] == len(items)


@pytest.mark.parametrize("version", committed_versions())
def test_every_version_descends_from_v0(version):
    assert stimuli.lineage(version)[0] == "v0"


def test_v0_is_the_published_set_verbatim():
    assert stimuli.load("v0") == json.loads(stimuli.SOURCE.read_text())


@pytest.mark.parametrize("version", [v for v in committed_versions() if v != "v0"])
def test_edit_log_reconstructs_the_version_from_its_parent(version):
    """Replaying a version's edit log on its parent must give exactly that version, so the log is
    a complete account of what changed and nothing was edited off the books."""
    man = stimuli.manifest(version)
    items = {it["id"]: dict(it) for it in stimuli.load(man["parent"])}
    order = [it["id"] for it in stimuli.load(man["parent"])]
    for e in man["edits"]:
        assert e["reason"]
        if e["op"] == "add":
            items[e["id"]] = e["item"]; order.append(e["id"])
        elif e["op"] == "change":
            assert items[e["id"]].get(e["field"]) == e["before"]
            items[e["id"]][e["field"]] = e["after"]
        elif e["op"] == "remove":
            items.pop(e["id"]); order.remove(e["id"])
    assert [items[i] for i in order] == stimuli.load(version)


def test_derive_and_diff_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(stimuli, "STIMULI", tmp_path)
    (tmp_path / "v0").mkdir()
    base = [{"id": "a", "text": "one"}, {"id": "b", "text": "two"}]
    stimuli._write("v0", base, {"version": "v0", "parent": None, "edits": []})
    stimuli.derive("v0", "v1", [
        {"op": "change", "id": "a", "field": "text", "after": "ONE", "reason": "r1"},
        {"op": "add", "item": {"id": "c", "text": "three"}, "reason": "r2"},
        {"op": "remove", "id": "b", "reason": "r3"}], "test")
    d = stimuli.diff("v0", "v1")
    assert d["added"] == ["c"] and d["removed"] == ["b"] and d["changed"] == {"a": {"text": ("one", "ONE")}}
    with pytest.raises(FileExistsError):
        stimuli.derive("v0", "v1", [], "again")
    with pytest.raises(ValueError):
        stimuli.derive("v0", "v2", [{"op": "remove", "id": "a", "reason": ""}], "no reason")
    # tampering is caught
    p = tmp_path / "v1" / "items.json"
    p.write_text(p.read_text().replace("ONE", "one!"))
    with pytest.raises(stimuli.SnapshotCorrupted):
        stimuli.load("v1")
