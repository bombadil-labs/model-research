"""Validate the decision trees (`nodes.yaml`) that `docs/PROGRAM_v2.md` rules R1-R4 run on.

The program's rules are only worth anything if they are checked from data, not declared in prose:
a hop count an agent states for itself is a label, and labels are how every earlier process layer
in this repository decayed. So the tree lives in `research/<line>/nodes.yaml` (and shared
infrastructure in `docs/nodes.yaml`), and this script computes what the rules need from it.

Schema, one entry per node:

    id:            lower-case slug, unique within the file
    title:         the question, one line
    kind:          test | retire | decide | infra | writeup
    claims:        [claim ids in the line's claims.yaml]        (empty allowed for infra/decide)
    parent:        node id in the same file, or null
    chain_from:    {note: where, hops: N} -- an EARLIER chain, run before nodes existed, that this
                   node continues; its hops count toward this node's hop
    motivated_by:  note:line that prompted the node
    status:        proposed | funded | running | done | stopped | retired | defaulted
    budget:        {ndif_jobs: N, wall_hours: H}               (metered units; tokens optional)
    spent:         {ndif_jobs: N, wall_hours: H}
    outcomes:      [{if: result, then: response, child: node id (optional)}]
    end_state:     true when the outcome table states the chain's end      (required at hop >= 3)
    author_decision: a reference to the author's own text (rule D)         (required at hop >= 4
                   before the node is funded)
    default:       the cheapest terminal option, executed at `decide_by` without a decision
                   (required for decide and retire nodes, and for any node that can escalate)
    decide_by:     YYYY-MM-DD                                   (required with `default`)

Hop is COMPUTED: the depth along `parent` links (a root is hop 1), plus `chain_from.hops`.

Usage:  python scripts/check_nodes.py               # every file
        python scripts/check_nodes.py narrative     # one line
Exits non-zero on any failure.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"
SHARED = ROOT / "docs" / "nodes.yaml"
sys.path.insert(0, str(ROOT / "scripts"))
import check_claims as cc  # noqa: E402  -- the claims statuses and terminality live there, once

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
KINDS = {"test", "retire", "decide", "infra", "writeup"}
STATUSES = {"proposed", "funded", "running", "done", "stopped", "retired", "defaulted"}
LIVE = {"proposed", "funded", "running"}          # a node in one of these still owes a result
COMMITTED = {"funded", "running", "done"}         # the author's go has been spent on it
THEN = {"continue", "holds", "narrow", "falsify", "withdraw", "retire", "underpowered",
        "unreadable", "escalate", "close"}
NOT_A_DEFAULT = re.compile(r"^\s*(fund|continue|run|extend)\b", re.I)
OVERRUN = 1.5


def _date(v) -> dt.date | None:
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except (TypeError, ValueError):
        return None


def hops(nodes: dict) -> tuple[dict, list[str]]:
    """{id: hop}, computed from parent links plus any earlier chain; and any cycle errors."""
    out, errs = {}, []

    def walk(nid, seen):
        if nid in out:
            return out[nid]
        if nid in seen:
            errs.append(f"[{nid}]: parent links form a cycle")
            return 0
        n = nodes[nid]
        base = int((n.get("chain_from") or {}).get("hops") or 0)
        p = n.get("parent")
        h = (walk(p, seen | {nid}) if p in nodes else 0) + 1 + base
        out[nid] = h
        return h

    for nid in nodes:
        walk(nid, frozenset())
    return out, errs


def check_file(path: pathlib.Path, claims: dict | None, today: dt.date) -> tuple[list[str], dict]:
    """Errors, plus a report: nodes by status, max hop, defaults due, uncovered open claims."""
    tag0 = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name
    doc = yaml.safe_load(path.read_text()) or {}
    raw = doc.get("nodes") or []
    errs: list[str] = []
    nodes: dict = {}
    for i, n in enumerate(raw):
        nid = n.get("id")
        if not nid or not ID_RE.match(str(nid)):
            errs.append(f"{tag0}[{i}]: id {nid!r} must be a lower-case slug")
            continue
        if nid in nodes:
            errs.append(f"{tag0}[{nid}]: duplicate id")
        nodes[nid] = n
    hop, cyc = hops(nodes)
    errs += [f"{tag0}{e}" for e in cyc]
    due, needs_go = [], []
    for nid, n in nodes.items():
        tag = f"{tag0}[{nid}]"
        for f in ("title", "kind", "status"):
            if not n.get(f):
                errs.append(f"{tag}: missing `{f}`")
        kind, status = n.get("kind"), n.get("status")
        if kind and kind not in KINDS:
            errs.append(f"{tag}: kind {kind!r} is not one of {sorted(KINDS)}")
        if status and status not in STATUSES:
            errs.append(f"{tag}: status {status!r} is not one of {sorted(STATUSES)}")
        p = n.get("parent")
        if p is not None and p not in nodes:
            errs.append(f"{tag}: parent {p!r} is not a node in this file")
        # every claim a node names must exist, or the tree and the table have drifted apart
        for c in n.get("claims") or []:
            if claims is None:
                errs.append(f"{tag}: names claim {c!r} but this file belongs to no line")
            elif c not in claims:
                errs.append(f"{tag}: names claim {c!r}, which is not in the line's claims.yaml")
        # R2: a test fixes its responses before its data
        outs = n.get("outcomes") or []
        if kind == "test" and not outs:
            errs.append(f"{tag}: a test node needs its outcome table before its data (R2)")
        for o in outs:
            if o.get("then") not in THEN:
                errs.append(f"{tag}: outcome response {o.get('then')!r} is not one of {sorted(THEN)}")
            if not str(o.get("if") or "").strip():
                errs.append(f"{tag}: an outcome without its `if` cannot be applied")
            ch = o.get("child")
            if ch is not None and ch not in nodes:
                errs.append(f"{tag}: outcome child {ch!r} is not a node in this file")
        # R4: nothing lapses through silence
        escalates = any(o.get("then") == "escalate" for o in outs)
        if kind in ("decide", "retire") or escalates:
            d, by = n.get("default"), _date(n.get("decide_by"))
            if not str(d or "").strip():
                errs.append(f"{tag}: a decision or escalation needs a `default` (R4)")
            elif NOT_A_DEFAULT.match(str(d)):
                errs.append(f"{tag}: default {d!r} spends; a default is the cheapest terminal option")
            if by is None:
                errs.append(f"{tag}: a decision or escalation needs a `decide_by` date (R4)")
            elif by < today and status in LIVE and kind in ("decide", "retire"):
                due.append(f"{nid} (default {d!r}, due {by})")
        # R3: hops are computed, and the cap is enforced at the third and fourth hop
        h = hop.get(nid, 0)
        if kind == "test" and h >= 3 and not n.get("end_state"):
            errs.append(f"{tag}: hop {h}: the outcome table must state the chain's end (R3)")
        if h >= 4 and not n.get("author_decision"):
            if status in COMMITTED:
                errs.append(f"{tag}: hop {h} is funded without an author decision (R3, rule D)")
            elif status in LIVE:
                needs_go.append(f"{nid} (hop {h})")
        # R5: budgets are metered, and a node at 1.5x stops
        b, s = n.get("budget") or {}, n.get("spent") or {}
        for unit in ("ndif_jobs", "wall_hours"):
            if b.get(unit) and s.get(unit) and s[unit] > OVERRUN * b[unit] and status in LIVE:
                errs.append(f"{tag}: spent {s[unit]} {unit} against a budget of {b[unit]} "
                            f"(>{OVERRUN}x) and is still {status}; it must stop and escalate (R5)")
    covered = {c for n in nodes.values() if n.get("status") in LIVE
               for c in n.get("claims") or []}
    uncovered = sorted(c for c, st in (claims or {}).items()
                       if not cc.STATUS.get(st, False) and c not in covered)
    accepted = doc.get("accepted")
    if accepted and uncovered:
        errs.append(f"{tag0}: open claims with no node: {uncovered} (R1)")
    by_status: dict = {}
    for n in nodes.values():
        by_status[n.get("status")] = by_status.get(n.get("status"), 0) + 1
    return errs, {"nodes": len(nodes), "by_status": by_status, "max_hop": max(hop.values(), default=0),
                  "due": due, "needs_go": needs_go, "uncovered": uncovered, "accepted": accepted}


def line_claims(d: pathlib.Path) -> dict:
    doc = yaml.safe_load((d / "claims.yaml").read_text()) or {}
    return {c["id"]: c.get("status") for c in doc.get("claims") or [] if c.get("id")}


def main(argv: list[str], today: dt.date | None = None) -> int:
    today = today or dt.date.today()
    targets = []
    lines = [RESEARCH / argv[1]] if len(argv) > 1 else sorted(p for p in RESEARCH.iterdir() if p.is_dir())
    for d in lines:
        if (d / "nodes.yaml").exists():
            targets.append((d / "nodes.yaml", line_claims(d)))
    if len(argv) <= 1 and SHARED.exists():
        targets.append((SHARED, None))
    total = 0
    for path, claims in targets:
        errs, r = check_file(path, claims, today)
        state = "accepted" if r["accepted"] else "PROPOSED (not accepted; nothing here is funded)"
        print(f"{path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path):32s} {r['nodes']} nodes · max hop {r['max_hop']} · {state}")
        print(f"    by status: {r['by_status']}")
        for x in r["needs_go"]:
            print(f"    needs the author's go: {x}")
        for x in r["due"]:
            print(f"    DEFAULT DUE: {x}")
        if r["uncovered"]:
            print(f"    open claims with no node: {r['uncovered']}")
        for e in errs:
            print(f"  FAIL {e}")
        total += len(errs)
    print(f"\n{'OK' if not total else str(total) + ' problem(s)'}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
