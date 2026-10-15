"""The node validator: the program's rules checked from data rather than declared in prose.

Each test pins one way a decision tree could let a chain run on without anyone deciding: a hop
count that is declared or reset instead of computed, a fourth hop funded without the author, a
decision with no terminal default, a budget overrun that keeps running, a tree that drifts from its
claims table, and an "author decision" that is not the author's recorded words.
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


SESSION = "https://claude.ai/code/session_013zLwtWkVdkTDNgy7DbpQCP"


def record(node, outcome="accept", **kw):
    r = {"id": "D-001", "date": "2026-10-15", "node": node, "outcome": outcome,
         "quote": "yes, accept it", "session": SESSION}
    r.update(kw)
    return r


def run(tmp_path, nodes, *, accepted=None, claims=CLAIMS, today=TODAY, raw=None, decisions=None):
    p = tmp_path / "nodes.yaml"
    p.write_text(raw if raw is not None else
                 yaml.safe_dump({"line": "demo", "accepted": accepted, "nodes": nodes}))
    return cn.check_file(p, claims, today, decisions or {})


def node(nid, parent=None, **kw):
    n = {"id": nid, "title": "A question?", "kind": "test", "claims": ["open-claim"],
         "parent": parent, "status": "proposed", "motivated_by": "notes/x.md:3",
         "budget": {"ndif_jobs": 10},
         "outcomes": [{"if": "it moves", "then": "holds"}, {"if": "it does not", "then": "retire"}]}
    n.update(kw)
    return n


def decision(nid, default="retire", **kw):
    n = {"id": nid, "title": "Which?", "kind": "decide", "claims": [], "parent": None,
         "status": "proposed", "default": default, "decide_by": "2026-10-29",
         "outcomes": [{"if": "retire", "then": "retire"}, {"if": "fund it", "then": "continue"}]}
    n.update(kw)
    return n


def exps(k):
    return {"experiments": [f"unit {i}" for i in range(k)]}


def test_the_repositorys_own_trees_validate():
    assert cn.main(["check_nodes.py"], today=TODAY) == 0


def test_hop_is_computed_from_parents_plus_listed_earlier_units():
    nodes = {"a": node("a"), "b": node("b", "a"), "c": node("c", "b"),
             "d": node("d", chain_from=exps(6))}
    assert cn.hops(nodes) == {"a": 1, "b": 2, "c": 3, "d": 7}


def test_an_earlier_chain_must_list_its_units_not_state_a_number(tmp_path):
    errs, _ = run(tmp_path, [node("a", chain_from={"hops": -3})])
    assert any("chain_from.experiments" in e for e in errs)


def test_a_child_that_does_not_name_its_parent_cannot_restart_its_hop(tmp_path):
    c = node("c", chain_from=exps(2), end_state=True,
             outcomes=[{"if": "x", "then": "holds", "child": "d"}])
    errs, _ = run(tmp_path, [c, node("d", status="funded")])
    assert any("must name 'c' as its parent" in e for e in errs)


def test_a_fourth_hop_funded_without_a_recorded_author_decision_is_refused(tmp_path):
    n = node("d", chain_from=exps(3), end_state=True, status="funded",
             author_decision="the author said yes in chat")
    errs, _ = run(tmp_path, [n])
    assert any("funded without the author's recorded decision" in e for e in errs)
    assert any("not a decision record for this node" in e for e in errs)


def test_a_proposed_fourth_hop_is_listed_as_needing_the_authors_go(tmp_path):
    errs, r = run(tmp_path, [node("d", chain_from=exps(3), end_state=True)])
    assert errs == [] and r["needs_go"] == ["d (hop 4)"]


def test_the_third_hop_must_state_the_chains_end_and_cannot_continue(tmp_path):
    errs, _ = run(tmp_path, [node("c", chain_from=exps(2))])
    assert any("hop 3" in e and "end" in e for e in errs)
    cont = node("c", chain_from=exps(2), end_state=True,
                outcomes=[{"if": "x", "then": "continue", "child": "d"}])
    errs, _ = run(tmp_path, [cont, node("d", "c", end_state=True)])
    assert any("cannot continue" in e for e in errs)


def test_continue_must_name_its_child(tmp_path):
    errs, _ = run(tmp_path, [node("a", outcomes=[{"if": "x", "then": "continue"}])])
    assert any("must name its child" in e for e in errs)


def test_a_decisions_default_must_be_one_of_its_terminal_outcomes(tmp_path):
    errs, _ = run(tmp_path, [decision("d", default="")])
    assert any("needs a `default`" in e for e in errs)
    errs, _ = run(tmp_path, [decision("d", default="fund the sweep")])
    assert any("spends" in e for e in errs)
    errs, _ = run(tmp_path, [decision("d", default="yes")])
    assert any("not the `if` of one of its outcomes" in e for e in errs)
    errs, _ = run(tmp_path, [decision("d", default="fund it",
                                      outcomes=[{"if": "fund it", "then": "continue"}])])
    assert errs  # either the spending word or the non-terminal response catches it
    errs, _ = run(tmp_path, [decision("d")])
    assert errs == []


def test_an_escalation_needs_a_default_and_a_date(tmp_path):
    errs, _ = run(tmp_path, [node("a", outcomes=[{"if": "surprise", "then": "escalate"}])])
    assert any("needs a `default`" in e for e in errs) and any("decide_by" in e for e in errs)


def test_defaults_are_due_only_once_the_plan_is_accepted(tmp_path):
    d = decision("d", kind="retire", claims=["open-claim"], decide_by="2026-10-01")
    errs, r = run(tmp_path, [d])
    assert errs == [] and r["due"] == []
    errs, r = run(tmp_path, [d], accepted="D-001",
                  decisions={"D-001": record(cn.ACCEPT_NODE)})
    assert errs == [] and r["due"] and "retire" in r["due"][0]


def test_acceptance_must_be_a_recorded_decision_for_the_acceptance_node(tmp_path):
    errs, _ = run(tmp_path, [decision("d")], accepted="yes per the author")
    assert any("rule D" in e for e in errs)
    errs, _ = run(tmp_path, [decision("d")], accepted="D-001",
                  decisions={"D-001": record("some-other-node")})
    assert any("rule D" in e for e in errs)


def test_accepting_the_program_is_the_one_decision_without_a_default(tmp_path):
    acc = decision(cn.ACCEPT_NODE, default=None, decide_by=None,
                   outcomes=[{"if": "accept", "then": "close"}, {"if": "reject", "then": "close"}])
    errs, _ = run(tmp_path, [acc])
    assert errs == []
    errs, _ = run(tmp_path, [dict(acc, default="accept", decide_by="2026-10-29")])
    assert any("no default" in e for e in errs)


def test_a_decision_record_needs_the_verbatim_quote_and_its_session(tmp_path):
    p = tmp_path / "decisions.yaml"
    good = record("d15-rule-d")
    p.write_text(yaml.safe_dump({"decisions": [good]}))
    recs, errs = cn.load_decisions(p)
    assert errs == [] and "D-001" in recs
    for bad in ({"quote": ""}, {"session": "the chat"}, {"id": "decision one"}):
        p.write_text(yaml.safe_dump({"decisions": [dict(good, **bad)]}))
        assert cn.load_decisions(p)[1], bad


def test_an_author_decision_must_be_recorded_for_that_very_node(tmp_path):
    n = node("d", chain_from=exps(3), end_state=True, status="funded", author_decision="D-001")
    errs, _ = run(tmp_path, [n], decisions={"D-001": record("another-node")})
    assert any("not a decision record for this node" in e for e in errs)
    errs, _ = run(tmp_path, [n], decisions={"D-001": record("d")})
    assert errs == []


def test_the_repositorys_decision_log_is_well_formed():
    recs, errs = cn.load_decisions()
    assert errs == [] and recs["D-001"]["node"] == "d15-rule-d"


def test_a_node_naming_a_claim_the_table_lacks_is_refused(tmp_path):
    errs, _ = run(tmp_path, [node("a", claims=["no-such-claim"])])
    assert any("not in the line's claims.yaml" in e for e in errs)


def test_a_node_past_one_and_a_half_times_its_budget_fails_unless_stopped(tmp_path):
    n = node("a", budget={"ndif_jobs": 100}, spent={"ndif_jobs": 300})
    for status in ("running", "done"):
        errs, _ = run(tmp_path, [dict(n, status=status)])
        assert any("not stopped" in e for e in errs), status
    errs, _ = run(tmp_path, [dict(n, status="stopped")])
    assert errs == []


def test_a_test_needs_a_metered_budget_and_a_note_line(tmp_path):
    errs, _ = run(tmp_path, [node("a", budget=None, motivated_by="a feeling")])
    assert any("metered budget" in e for e in errs) and any("note:line" in e for e in errs)


def test_a_test_without_its_outcome_table_is_refused(tmp_path):
    errs, _ = run(tmp_path, [node("a", outcomes=[])])
    assert any("outcome table before its data" in e for e in errs)


def test_parent_cycles_are_caught(tmp_path):
    errs, _ = run(tmp_path, [node("a", "b"), node("b", "a")])
    assert any("cycle" in e for e in errs)


def test_once_accepted_every_open_claim_needs_a_live_node(tmp_path):
    n = node("a", status="done")
    errs, r = run(tmp_path, [n])
    assert errs == [] and r["uncovered"] == ["open-claim"]
    errs, _ = run(tmp_path, [n], accepted="D-001", decisions={"D-001": record(cn.ACCEPT_NODE)})
    assert any("open claims with no node" in e for e in errs)


@pytest.mark.parametrize("bad", [
    {"chain_from": "notes/x.md:3"},
    {"budget": 250},
    {"budget": {"ndif_jobs": "~400"}, "spent": {"ndif_jobs": "12"}},
    {"decide_by": dt.datetime(2026, 10, 1, 12), "outcomes": [{"if": "x", "then": "escalate"}],
     "default": "close"},
    {"outcomes": "see the prereg"},
    {"parent": ["a"]},
])
def test_malformed_values_are_reported_never_crash(tmp_path, bad):
    errs, _ = run(tmp_path, [node("a", **bad)])
    assert isinstance(errs, list)


def test_malformed_files_are_reported_never_crash(tmp_path):
    for raw in ("nodes: {a: 1}\n", "nodes:\n  - just a string\n", "- a\n- b\n", "nodes: [\n"):
        errs, _ = run(tmp_path, None, raw=raw)
        assert errs, raw


def test_an_unknown_line_is_a_failure_not_ok():
    assert cn.main(["check_nodes.py", "narative"], today=TODAY) == 1
