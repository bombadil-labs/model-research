"""Validate the decision trees (`nodes.yaml`) that `docs/PROGRAM_v2.md` rules R1-R5 and D run on.

The program's rules are only worth anything if they are checked from data, not declared in prose:
a hop count an agent states for itself is a label, and labels are how every earlier process layer
in this repository decayed. So the tree lives in `research/<line>/nodes.yaml` (and shared
infrastructure in `docs/nodes.yaml`), and this script computes what the rules need from it.

Schema, one entry per node:

    id:            lower-case slug, unique within the file
    title:         the question, one line
    kind:          test | retire | decide | infra | writeup
    claims:        [claim ids in the line's claims.yaml]        (empty allowed for infra/decide)
    parent:        node id in the same file, or null. A test's outcome `child` must name it back.
    chain_from:    {experiments: [unit, ...]} -- an EARLIER chain, run before nodes existed, that
                   this node continues; one listed unit per hop, so the count is not a free number
    motivated_by:  note:line that prompted the node                       (required for tests)
    status:        proposed | funded | running | done | stopped | retired | defaulted
    retrospective: true when the outcome table was written after the result (C1 only)
    budget:        {ndif_jobs: N, wall_hours: H}         (metered; required for test/infra/writeup)
    spent:         {ndif_jobs: N, wall_hours: H}
    procedure:     free text the outcome table assumes (ignored by the checker)
    outcomes:      [{if: result, then: response, child: node id}]
    end_state:     true when the outcome table states the chain's end      (required at hop >= 3)
    author_decision: the id of a record in docs/decisions.yaml for THIS node (rule D)
                   (required at hop >= 4 before a test is funded)
    default:       for decide/retire nodes, the `if` text of one of its TERMINAL outcomes; for a
                   test that can escalate, the response that runs if nobody decides
    decide_by:     YYYY-MM-DD; defaults run only after the file is `accepted`

`accepted` (top level) is null until the author accepts PROGRAM_v2; set, it must be the id of a
record in `docs/decisions.yaml` whose node is `accept-program-v2`. A decision record is the
author's own message, copied verbatim by the agent from the Claude session it was made in, with
that session's link (rule D). Hop is COMPUTED: the depth along `parent` links (a root is hop 1)
plus the units listed in `chain_from.experiments`.

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
DECISIONS = ROOT / "docs" / "decisions.yaml"
ACCEPT_NODE = "accept-program-v2"
sys.path.insert(0, str(ROOT / "scripts"))
import check_claims as cc  # noqa: E402  -- the claims statuses and terminality live there, once

ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")
DECISION_ID_RE = re.compile(r"^D-\d{3,}$")
SESSION_RE = re.compile(r"^https://claude\.ai/code/session_[A-Za-z0-9]+$")
KINDS = {"test", "retire", "decide", "infra", "writeup"}
STATUSES = {"proposed", "funded", "running", "done", "stopped", "retired", "defaulted"}
LIVE = {"proposed", "funded", "running"}          # a node in one of these still owes a result
COMMITTED = {"funded", "running", "done"}         # the author's go has been spent on it
THEN = {"continue", "holds", "narrow", "falsify", "withdraw", "retire", "underpowered",
        "unreadable", "escalate", "close"}
TERMINAL = {"close", "retire", "underpowered", "withdraw", "falsify", "narrow", "holds"}
NOT_A_DEFAULT = re.compile(r"^\s*(fund|continue|run|extend|keep running)\b", re.I)
OVERRUN = 1.5


def _date(v) -> dt.date | None:
    if isinstance(v, dt.datetime):
        return v.date()
    if isinstance(v, dt.date):
        return v
    try:
        return dt.date.fromisoformat(str(v))
    except (TypeError, ValueError):
        return None


def _num(x):
    return x if isinstance(x, (int, float)) and not isinstance(x, bool) and x >= 0 else None


def load_decisions(path: pathlib.Path | None = None) -> tuple[dict, list[str]]:
    """Rule D's log: {id: record}, and the problems with it.

    Agents post and commit under the author's account, so neither a commit's author field nor a
    GitHub comment can tell his text from theirs. The author chose to decide in chat instead
    (D-001), so a decision is his message copied VERBATIM from the Claude session it was made in,
    with that session's link: anyone can open the transcript and check the quote. A record with no
    quote or no session link is not a decision, whatever it says.
    """
    path = path or DECISIONS
    if not path.exists():
        return {}, []
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        return {}, [f"{path.name}: not valid YAML ({e})"]
    recs = doc.get("decisions") if isinstance(doc, dict) else None
    if not isinstance(recs, list):
        return {}, [f"{path.name}: `decisions` must be a list"]
    out, errs = {}, []
    for i, r in enumerate(recs):
        if not isinstance(r, dict):
            errs.append(f"{path.name}[{i}]: a decision must be a mapping")
            continue
        did = r.get("id")
        tag = f"{path.name}[{did or i}]"
        if not isinstance(did, str) or not DECISION_ID_RE.match(did):
            errs.append(f"{tag}: id must look like D-001")
            continue
        if did in out:
            errs.append(f"{tag}: duplicate id")
        if _date(r.get("date")) is None:
            errs.append(f"{tag}: needs a `date`")
        for f in ("node", "outcome", "quote"):
            if not str(r.get(f) or "").strip():
                errs.append(f"{tag}: needs `{f}`" + (" -- the author's words, verbatim" if f == "quote" else ""))
        if not SESSION_RE.match(str(r.get("session") or "")):
            errs.append(f"{tag}: needs the `session` link the quote was copied from")
        out[did] = r
    return out, errs


def decided(ref, node: str, decisions: dict) -> bool:
    """Is `ref` a well-formed decision record for `node`?"""
    r = decisions.get(ref) if isinstance(ref, str) else None
    return bool(r) and r.get("node") == node and bool(str(r.get("quote") or "").strip()) \
        and bool(SESSION_RE.match(str(r.get("session") or "")))


def hops(nodes: dict, errs: list[str] | None = None) -> dict:
    """{id: hop}: depth along parent links, plus one per unit listed in `chain_from.experiments`."""
    errs = errs if errs is not None else []
    out: dict = {}

    def earlier(nid, n) -> int:
        cf = n.get("chain_from")
        if cf is None:
            return 0
        exps = cf.get("experiments") if isinstance(cf, dict) else None
        if not isinstance(exps, list) or not exps or not all(isinstance(x, str) and x.strip() for x in exps):
            errs.append(f"[{nid}]: chain_from.experiments must list the earlier chain's units, one per hop")
            return 0
        return len(exps)

    def walk(nid, seen):
        if nid in out:
            return out[nid]
        if nid in seen:
            errs.append(f"[{nid}]: parent links form a cycle")
            return 0
        n = nodes[nid]
        p = n.get("parent")
        p = p if isinstance(p, str) and p in nodes else None
        h = (walk(p, seen | {nid}) if p else 0) + 1 + earlier(nid, n)
        out[nid] = h
        return h

    for nid in nodes:
        walk(nid, frozenset())
    return out


def _empty_report(accepted=None) -> dict:
    return {"nodes": 0, "by_status": {}, "max_hop": 0, "due": [], "needs_go": [], "uncovered": [],
            "accepted": accepted}


def check_file(path: pathlib.Path, claims: dict | None, today: dt.date,
               decisions: dict | None = None) -> tuple[list[str], dict]:
    """Errors, plus a report: nodes by status, max hop, defaults due, uncovered open claims."""
    decisions = load_decisions()[0] if decisions is None else decisions
    tag0 = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else path.name
    try:
        doc = yaml.safe_load(path.read_text()) or {}
    except yaml.YAMLError as e:
        return [f"{tag0}: not valid YAML ({e})"], _empty_report()
    errs: list[str] = []
    if not isinstance(doc, dict):
        return [f"{tag0}: the file must be a mapping with `nodes:`"], _empty_report()
    raw = doc.get("nodes") or []
    if not isinstance(raw, list):
        errs.append(f"{tag0}: `nodes` must be a list")
        raw = []
    accepted = doc.get("accepted")
    if accepted is not None and not decided(accepted, ACCEPT_NODE, decisions):
        errs.append(f"{tag0}: `accepted` {accepted!r} is not a decision record for "
                    f"{ACCEPT_NODE!r} in docs/decisions.yaml (rule D)")
    nodes: dict = {}
    for i, n in enumerate(raw):
        if not isinstance(n, dict):
            errs.append(f"{tag0}[{i}]: a node must be a mapping")
            continue
        nid = n.get("id")
        if not isinstance(nid, str) or not ID_RE.match(nid):
            errs.append(f"{tag0}[{i}]: id {nid!r} must be a lower-case slug")
            continue
        if nid in nodes:
            errs.append(f"{tag0}[{nid}]: duplicate id")
        nodes[nid] = n
    herrs: list[str] = []
    hop = hops(nodes, herrs)
    errs += [f"{tag0}{e}" for e in herrs]
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
        if p is not None and (not isinstance(p, str) or p not in nodes):
            errs.append(f"{tag}: parent {p!r} is not a node in this file")
        cl = n.get("claims") or []
        if not isinstance(cl, list):
            errs.append(f"{tag}: `claims` must be a list")
            cl = []
        for c in cl:
            if claims is None:
                errs.append(f"{tag}: names claim {c!r} but this file belongs to no line")
            elif c not in claims:
                errs.append(f"{tag}: names claim {c!r}, which is not in the line's claims.yaml")
        outs = n.get("outcomes") or []
        if not isinstance(outs, list) or not all(isinstance(o, dict) for o in outs):
            errs.append(f"{tag}: `outcomes` must be a list of {{if, then}} mappings")
            outs = []
        # R1: a test says what prompted it, as note:line
        if kind == "test" and not re.match(r".+:\d+", str(n.get("motivated_by") or "")):
            errs.append(f"{tag}: a test's `motivated_by` must be note:line (R1)")
        # R2: a test fixes its responses before its data
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
            if kind == "test" and o.get("then") == "continue" and not ch:
                errs.append(f"{tag}: `continue` must name its child (R2)")
            # R3: a test's child points back, or its hop would restart at 1
            if kind == "test" and ch in nodes and nodes[ch].get("parent") != nid:
                errs.append(f"{tag}: child {ch!r} must name {nid!r} as its parent, or its hop restarts (R3)")
        # R4: nothing lapses through silence
        escalates = any(o.get("then") == "escalate" for o in outs)
        d, by = n.get("default"), _date(n.get("decide_by"))
        if nid == ACCEPT_NODE:
            # the one decision with no default: a plan an agent wrote cannot accept itself by silence
            if d is not None:
                errs.append(f"{tag}: accepting PROGRAM_v2 must have no default (R4's exception)")
        elif kind in ("decide", "retire") or escalates:
            if not str(d or "").strip():
                errs.append(f"{tag}: a decision or escalation needs a `default` (R4)")
            elif NOT_A_DEFAULT.match(str(d)):
                errs.append(f"{tag}: default {d!r} spends; a default never funds or continues (R4)")
            elif kind in ("decide", "retire"):
                hit = [o for o in outs if str(o.get("if") or "").strip() == str(d).strip()]
                if not hit:
                    errs.append(f"{tag}: default {d!r} is not the `if` of one of its outcomes (R4)")
                elif hit[0].get("then") not in TERMINAL:
                    errs.append(f"{tag}: default {d!r} leads to {hit[0].get('then')!r}; "
                                "a default is terminal (R4)")
            if by is None:
                errs.append(f"{tag}: a decision or escalation needs a `decide_by` date (R4)")
            elif accepted and by < today and status in LIVE and kind in ("decide", "retire"):
                due.append(f"{nid} (default {d!r}, due {by})")
        # R3: hops are computed, and the cap is enforced at the third and fourth hop of a test
        h = hop.get(nid, 0)
        if kind == "test" and h >= 3:
            if not n.get("end_state"):
                errs.append(f"{tag}: hop {h}: the outcome table must state the chain's end (R3)")
            if any(o.get("then") == "continue" for o in outs):
                errs.append(f"{tag}: hop {h}: an end-state table cannot continue (R3)")
        ad = n.get("author_decision")
        if ad is not None and not decided(ad, nid, decisions):
            errs.append(f"{tag}: author_decision {ad!r} is not a decision record for this node "
                        "in docs/decisions.yaml (rule D)")
        if kind == "test" and h >= 4 and not decided(ad, nid, decisions):
            if status in COMMITTED:
                errs.append(f"{tag}: hop {h} is funded without the author's recorded decision "
                            "(R3, rule D)")
            elif status in LIVE:
                needs_go.append(f"{nid} (hop {h})")
        # R5: budgets are metered, and a node past 1.5x that has not stopped is a failure (§8.3)
        for k in ("budget", "spent"):
            if n.get(k) is not None and not isinstance(n.get(k), dict):
                errs.append(f"{tag}: `{k}` must be a mapping of metered units")
        b = n.get("budget") if isinstance(n.get("budget"), dict) else {}
        s = n.get("spent") if isinstance(n.get("spent"), dict) else {}
        if kind in ("test", "infra", "writeup") and not any(
                _num(b.get(u)) for u in ("ndif_jobs", "wall_hours")):
            errs.append(f"{tag}: needs a metered budget, NDIF jobs or wall hours (R5)")
        for u in ("ndif_jobs", "wall_hours"):
            for val, nm in ((b.get(u), "budget"), (s.get(u), "spent")):
                if val is not None and _num(val) is None:
                    errs.append(f"{tag}: {nm}.{u} {val!r} is not a non-negative number")
            bu, su = _num(b.get(u)), _num(s.get(u))
            if bu is not None and su is not None and su > OVERRUN * bu and status != "stopped":
                errs.append(f"{tag}: spent {su} {u} against a budget of {bu} (>{OVERRUN}x) "
                            f"and is {status}, not stopped (R5, §8.3)")
    covered = {c for n in nodes.values() if n.get("status") in LIVE
               for c in (n.get("claims") if isinstance(n.get("claims"), list) else [])}
    uncovered = sorted(c for c, st in (claims or {}).items()
                       if not cc.STATUS.get(st, False) and c not in covered)
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
    total = 0
    targets = []
    decisions, derrs = load_decisions()
    for e in derrs:
        print(f"  FAIL {e}")
    total += len(derrs)
    if len(argv) > 1:
        if not (RESEARCH / argv[1] / "claims.yaml").exists():
            print(f"  FAIL no research line {argv[1]!r}")
            return 1
        lines = [RESEARCH / argv[1]]
    else:
        lines = sorted(p for p in RESEARCH.iterdir() if p.is_dir())
    for d in lines:
        if not (d / "claims.yaml").exists():
            continue
        if (d / "nodes.yaml").exists():
            targets.append((d / "nodes.yaml", line_claims(d)))
        else:
            print(f"  FAIL research/{d.name}: has claims.yaml but no nodes.yaml (R1)")
            total += 1
    if len(argv) <= 1 and SHARED.exists():
        targets.append((SHARED, None))
    for path, claims in targets:
        errs, r = check_file(path, claims, today, decisions)
        state = "accepted" if r["accepted"] else "PROPOSED (not accepted; nothing funded, no default runs)"
        name = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
        print(f"{name:32s} {r['nodes']} nodes · max hop {r['max_hop']} · {state}")
        print(f"    by status: {r['by_status']}")
        for x in r["needs_go"]:
            print(f"    needs the author's go: {x}")
        for x in r["due"]:
            print(f"    DEFAULT DUE: {x}")
        if r["uncovered"]:
            print(f"    open claims with no live node: {r['uncovered']}")
        for e in errs:
            print(f"  FAIL {e}")
        total += len(errs)
    # every decision names a real node and one of that node's own outcomes
    all_nodes = {}
    for path, _ in targets:
        try:
            for n in (yaml.safe_load(path.read_text()) or {}).get("nodes") or []:
                if isinstance(n, dict) and isinstance(n.get("id"), str):
                    all_nodes[n["id"]] = n
        except (yaml.YAMLError, AttributeError):
            pass
    for did, r in decisions.items():
        n = all_nodes.get(r.get("node"))
        if n is None:
            print(f"  FAIL decisions.yaml[{did}]: node {r.get('node')!r} is in no nodes.yaml")
            total += 1
        elif not any(str(o.get("if") or "").strip() == str(r.get("outcome") or "").strip()
                     for o in (n.get("outcomes") or []) if isinstance(o, dict)):
            print(f"  FAIL decisions.yaml[{did}]: outcome {r.get('outcome')!r} is not one of "
                  f"{r.get('node')!r}'s outcomes")
            total += 1
    print(f"docs/decisions.yaml              {len(decisions)} decision(s) recorded")
    print(f"\n{'OK' if not total else str(total) + ' problem(s)'}")
    return 1 if total else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
