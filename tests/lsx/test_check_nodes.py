"""The node validator: the program's rules checked from data rather than declared in prose.

Each test pins one way a decision tree could let a chain run on without anyone deciding: a hop
count that is declared instead of computed, a fourth hop funded without the author, a decision
with no default, a budget overrun that keeps running, and a tree that drifts from its claims table.
"""
from __future__ import annotations

import datetime as dt
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
yaml = pytest.importorskip("yaml")
cn = pytest.importorskip("check_nodes")

TODAY = dt.date(2026, 10, 15)
CLAIMS = {"open-claim": "open", "done-claim": "holds"}


def run(tmp_path, nodes, *, accepted=None, claims=CLAIMS, today=TODAY):
    p = tmp_path / "nodes.yaml"
    p.write_text(yaml.safe_dump({"line": "demo", "accepted": accepted, "nodes": nodes}))
    return cn.check_file(p, claims, today)


def test(nid, parent=None, **kw):
    n = {"id": nid, "title": "A question?", "kind": "test", "claims": ["open-claim"],
         "parent": parent, "status": "proposed",
         "outcomes": [{"if": "it moves", "then": "holds"}, {"if": "it does not", "then": "retire"}]}
    n.update(kw)
    return n


test.__test__ = False  # a fixture builder, not a pytest test


def test_the_repositorys_own_trees_validate():
    assert cn.main(["check_nodes.py"], today=TODAY) == 0


def test_hop_is_computed_from_parents_plus_an_earlier_chain_never_declared():
    nodes = {"a": test("a"), "b": test("b", "a"), "c": test("c", "b", end_state=True),
             "d": test("d", chain_from={"note": "x", "hops": 5})}
    h, errs = cn.hops(nodes)
    assert errs == [] and h == {"a": 1, "b": 2, "c": 3, "d": 6}


def test_a_fourth_hop_funded_without_the_author_is_refused(tmp_path):
    nodes = [test("a"), test("b", "a"), test("c", "b", end_state=True),
             test("d", "c", end_state=True, status="funded")]
    errs, _ = run(tmp_path, nodes)
    assert any("hop 4 is funded without an author decision" in e for e in errs)
    nodes[-1]["author_decision"] = "PR comment by the author, 2026-10-20"
    errs, _ = run(tmp_path, nodes)
    assert errs == []


def test_a_proposed_fourth_hop_is_listed_as_needing_the_authors_go_not_refused(tmp_path):
    nodes = [test("d", chain_from={"note": "x", "hops": 3}, end_state=True)]
    errs, r = run(tmp_path, nodes)
    assert errs == [] and r["needs_go"] == ["d (hop 4)"]


def test_the_third_hop_must_state_the_chains_end(tmp_path):
    errs, _ = run(tmp_path, [test("a"), test("b", "a"), test("c", "b")])
    assert any("hop 3" in e and "end" in e for e in errs)


def test_a_decision_needs_a_cheap_default_and_a_date(tmp_path):
    dec = {"id": "d", "title": "Which?", "kind": "decide", "claims": [], "parent": None,
           "status": "proposed"}
    errs, _ = run(tmp_path, [dec])
    assert any("needs a `default`" in e for e in errs) and any("decide_by" in e for e in errs)
    errs, _ = run(tmp_path, [dict(dec, default="fund the sweep", decide_by="2026-10-29")])
    assert any("spends" in e for e in errs)
    errs, _ = run(tmp_path, [dict(dec, default="retire", decide_by="2026-10-29")])
    assert errs == []


def test_an_escalation_is_a_decision_and_needs_a_default_too(tmp_path):
    n = test("a", outcomes=[{"if": "surprise", "then": "escalate"}])
    errs, _ = run(tmp_path, [n])
    assert any("needs a `default`" in e for e in errs)


def test_a_passed_date_is_reported_as_a_default_due(tmp_path):
    dec = {"id": "d", "title": "Which?", "kind": "retire", "claims": ["open-claim"],
           "parent": None, "status": "proposed", "default": "retire", "decide_by": "2026-10-01"}
    errs, r = run(tmp_path, [dec])
    assert errs == [] and r["due"] and "retire" in r["due"][0]


def test_a_node_naming_a_claim_the_table_lacks_is_refused(tmp_path):
    errs, _ = run(tmp_path, [test("a", claims=["no-such-claim"])])
    assert any("not in the line's claims.yaml" in e for e in errs)


def test_a_node_past_one_and_a_half_times_its_budget_must_stop(tmp_path):
    n = test("a", budget={"ndif_jobs": 100}, spent={"ndif_jobs": 151}, status="running")
    errs, _ = run(tmp_path, [n])
    assert any("must stop and escalate" in e for e in errs)
    errs, _ = run(tmp_path, [dict(n, status="stopped")])
    assert errs == []


def test_a_test_without_its_outcome_table_is_refused(tmp_path):
    errs, _ = run(tmp_path, [test("a", outcomes=[])])
    assert any("outcome table before its data" in e for e in errs)


def test_parent_cycles_are_caught(tmp_path):
    errs, _ = run(tmp_path, [test("a", "b"), test("b", "a")])
    assert any("cycle" in e for e in errs)


def test_once_accepted_every_open_claim_needs_a_live_node(tmp_path):
    n = test("a", status="done")
    errs, r = run(tmp_path, [n])
    assert errs == [] and r["uncovered"] == ["open-claim"]
    errs, _ = run(tmp_path, [n], accepted="abc1234")
    assert any("open claims with no node" in e for e in errs)
