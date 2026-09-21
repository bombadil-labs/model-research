"""The claims validator, and the one property that makes a claims table worth keeping.

A table that lists only the questions you answered will report a line CLOSED while its open
problems run to a page — which is exactly what the first triage of the narrative line did. These
tests pin the rules that stop a table rotting into decoration: a terminal claim must point at its
answer, a retraction must name what replaced it, and the closure count must be computed rather
than asserted.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
yaml = pytest.importorskip("yaml")
cc = pytest.importorskip("check_claims")

BASE = {"id": "a-claim", "claim": "The thing is true of the model.", "status": "holds",
        "where": "docs/EXPERIMENTS.md", "evidence": "h1", "superseded_by": None}


def write(tmp_path, claims, line="demo"):
    d = tmp_path / line; d.mkdir(parents=True, exist_ok=True)
    (d / "docs").mkdir(exist_ok=True)
    (d / "docs" / "EXPERIMENTS.md").write_text("log")
    (d / "claims.yaml").write_text(yaml.safe_dump({"line": line, "claims": claims}))
    return d


def test_every_status_in_the_spec_is_classified_terminal_or_not():
    assert set(cc.STATUS) == {"open", "running", "holds", "narrowed", "falsified",
                              "withdrawn", "retired"}
    assert [s for s, t in cc.STATUS.items() if not t] == ["open", "running"]


def test_retired_is_terminal_so_a_line_can_close_without_answering_everything():
    """Without this, a question judged not worth answering has no terminal state and the line
    can never close except by answering all of them."""
    assert cc.STATUS["retired"] is True


def test_a_clean_table_passes(tmp_path):
    d = write(tmp_path, [BASE])
    errs, term, n = cc.check_line(d)
    assert errs == [] and (term, n) == (1, 1)


def test_terminal_claim_without_a_where_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "where": ""}])
    errs, _, _ = cc.check_line(d)
    assert any("cannot be answered without pointing at the answer" in e for e in errs)


def test_open_claim_without_a_where_is_allowed(tmp_path):
    """An unanswered question has nothing to point at yet — that must not be an error, or the
    table will quietly lose its open rows and report the line closed."""
    d = write(tmp_path, [{**BASE, "status": "open", "where": ""}])
    errs, term, n = cc.check_line(d)
    assert errs == [] and (term, n) == (0, 1)


def test_withdrawn_without_superseded_by_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "status": "withdrawn"}])
    errs, _, _ = cc.check_line(d)
    assert any("requires `superseded_by`" in e for e in errs)


def test_withdrawn_with_superseded_by_passes(tmp_path):
    d = write(tmp_path, [{**BASE, "status": "withdrawn", "superseded_by": "The corrected run."}])
    assert cc.check_line(d)[0] == []


def test_duplicate_ids_fail(tmp_path):
    d = write(tmp_path, [BASE, {**BASE, "claim": "A different assertion entirely here."}])
    assert any("duplicate id" in e for e in cc.check_line(d)[0])


def test_a_topic_is_not_a_claim(tmp_path):
    d = write(tmp_path, [{**BASE, "claim": "Era."}])
    errs, _, _ = cc.check_line(d)
    assert any("topic, not an assertion" in e or "full stop" in e for e in errs)


def test_unknown_status_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "status": "probably"}])
    assert any("is not one of" in e for e in cc.check_line(d)[0])


def test_where_pointing_at_a_missing_file_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "where": "docs/NOPE.md"}])
    assert any("does not exist" in e for e in cc.check_line(d)[0])


def test_the_real_lines_validate_and_neither_is_falsely_closed():
    """The repo's own tables, checked on every run. A line reporting CLOSED while its
    open-problems list is non-empty is the failure this whole file exists to catch."""
    for line in ("narrative", "shame-axis"):
        d = ROOT / "research" / line
        errs, term, n = cc.check_line(d)
        assert errs == [], f"{line}: {errs}"
        assert n > 0, f"{line}: no claims"
        assert term < n, f"{line} reports CLOSED ({term}/{n}) — verify that is really true"
