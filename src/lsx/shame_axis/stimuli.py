"""Versioned stimulus snapshots, derived from the paper's own 420 scenarios.

Every version is an immutable directory `research/shame-axis/prompts/stimuli/<version>/` holding
`items.json` and `manifest.json`. `v0` is their published set, verbatim. Every later version names
its parent and carries an explicit edit log -- one entry per changed, added or removed item, with
the before/after text and a reason -- so any two versions can be diffed item by item and any
result can be traced to the exact text it was measured on.

A snapshot is never edited after it is committed. `load()` refuses one whose items no longer
hash to its manifest; a change is a new version. That is what makes differential analysis honest:
the same item id in two versions is either byte-identical or listed in an edit log.
"""
from __future__ import annotations

import hashlib
import json
import pathlib

ROOT = pathlib.Path(__file__).resolve().parents[3]
STIMULI = ROOT / "research/shame-axis/prompts/stimuli"
SOURCE = ROOT / "research/shame-axis/prompts/external/pain_axis/4.1_self_other_420_scenarios.json"


class SnapshotCorrupted(RuntimeError):
    pass


def item_sha(item: dict) -> str:
    return hashlib.sha256(json.dumps(item, sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]


def _paths(version: str) -> tuple[pathlib.Path, pathlib.Path]:
    d = STIMULI / version
    return d / "items.json", d / "manifest.json"


def load(version: str) -> list[dict]:
    """Items of `version`, after verifying every item against the manifest."""
    ip, mp = _paths(version)
    items = json.loads(ip.read_text())
    man = json.loads(mp.read_text())
    got = {it["id"]: item_sha(it) for it in items}
    if len(got) != len(items):
        raise SnapshotCorrupted(f"{version}: duplicate item ids")
    if got != man["item_sha"]:
        bad = sorted(k for k in set(got) | set(man["item_sha"]) if got.get(k) != man["item_sha"].get(k))
        raise SnapshotCorrupted(f"{version}: {len(bad)} items differ from the manifest, e.g. {bad[:5]}. "
                                "Snapshots are immutable; derive a new version instead.")
    return items


def manifest(version: str) -> dict:
    return json.loads(_paths(version)[1].read_text())


def _write(version: str, items: list[dict], man: dict) -> None:
    ip, mp = _paths(version)
    if ip.exists() or mp.exists():
        raise FileExistsError(f"stimuli version {version} already exists; snapshots are immutable")
    ip.parent.mkdir(parents=True, exist_ok=True)
    man["n_items"] = len(items)
    man["item_sha"] = {it["id"]: item_sha(it) for it in items}
    ip.write_text(json.dumps(items, indent=1, ensure_ascii=False) + "\n")
    mp.write_text(json.dumps(man, indent=1, ensure_ascii=False) + "\n")


def create_v0() -> None:
    """Their 420 scenarios, byte-for-byte in content, with the source file's hash recorded."""
    raw = SOURCE.read_bytes()
    items = json.loads(raw)
    _write("v0", items, {
        "version": "v0", "parent": None,
        "source": str(SOURCE.relative_to(ROOT)), "source_sha256": hashlib.sha256(raw).hexdigest(),
        "description": "The paper's 420 self/other scenarios as published. Nothing changed, "
                       "including two known defects kept deliberately (see known_defects).",
        "known_defects": {
            "gaslight_06": "literal template placeholder 'X' in the published text",
            "gaslight_14": "literal template placeholder 'X' in the published text",
            "gaslight_19": "labelled perspective 3P but is a multi-turn exchange with an assistant hedge, not a third-party frame",
            "gaslight_20": "labelled perspective 3P but is a multi-turn exchange with an assistant hedge, not a third-party frame",
        },
        "edits": [],
    })


def derive(parent: str, version: str, edits: list[dict], description: str) -> list[dict]:
    """New snapshot = parent + edits. Each edit is one of
         {"op": "add",    "item": {...}, "reason": str}
         {"op": "change", "id": str, "field": str, "after": value, "reason": str}
         {"op": "remove", "id": str, "reason": str}
    'change' records the before value itself. Every edit must carry a reason."""
    items = {it["id"]: dict(it) for it in load(parent)}
    order = [it["id"] for it in load(parent)]
    log = []
    for e in edits:
        if not e.get("reason"):
            raise ValueError(f"edit without a reason: {e}")
        if e["op"] == "add":
            iid = e["item"]["id"]
            if iid in items:
                raise ValueError(f"add: {iid} already exists in {parent}")
            items[iid] = dict(e["item"]); order.append(iid)
            log.append({"op": "add", "id": iid, "item": e["item"], "reason": e["reason"]})
        elif e["op"] == "change":
            before = items[e["id"]].get(e["field"])
            items[e["id"]][e["field"]] = e["after"]
            log.append({"op": "change", "id": e["id"], "field": e["field"], "before": before,
                        "after": e["after"], "reason": e["reason"]})
        elif e["op"] == "remove":
            log.append({"op": "remove", "id": e["id"], "item": items.pop(e["id"]), "reason": e["reason"]})
            order.remove(e["id"])
        else:
            raise ValueError(f"unknown op {e['op']}")
    out = [items[i] for i in order]
    _write(version, out, {"version": version, "parent": parent, "description": description,
                          "edits": log})
    return out


def diff(a: str, b: str) -> dict:
    """Item-level difference between any two versions: added, removed, changed (with fields)."""
    A = {it["id"]: it for it in load(a)}
    B = {it["id"]: it for it in load(b)}
    changed = {}
    for i in set(A) & set(B):
        if A[i] != B[i]:
            changed[i] = {k: (A[i].get(k), B[i].get(k)) for k in set(A[i]) | set(B[i])
                          if A[i].get(k) != B[i].get(k)}
    return {"added": sorted(set(B) - set(A)), "removed": sorted(set(A) - set(B)),
            "changed": changed, "unchanged": sorted(i for i in set(A) & set(B) if A[i] == B[i])}


def lineage(version: str) -> list[str]:
    out, v = [], version
    while v is not None:
        out.append(v); v = manifest(v)["parent"]
    return out[::-1]
