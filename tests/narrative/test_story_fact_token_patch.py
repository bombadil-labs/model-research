"""Independent factor and decision checks for the one-period patch."""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/narrative"))
import goal_route_cross as cross  # noqa: E402
import story_fact_token_patch as patch  # noqa: E402


def _fixture():
    _, stories, _, _, doc, _ = cross.make_cells()
    cells = patch.selected_cells(stories, doc)
    domains = {r["id"]: r for r in doc["domains"]}
    return cells, doc, domains


def test_lexical_prompt_changes_only_final_destination_and_sign_uses_graph():
    cells, doc, domains = _fixture()
    signs = set()
    for cell in cells:
        row = domains[cell.domain]
        lex = patch.lexical_cell(cell, row, doc)
        bridge = doc["bridge"]
        informative = cell.user_text[:-len(bridge)]
        lex_informative = lex.user_text[:-len(bridge)]
        destinations = ((row["target"], row["foil"]) if cell.world == 0
                        else (row["foil"], row["target"]))
        last = 1 - row["fact_order"][1]
        old = doc["second_hop_template"].format(
            link=row["links"][last], destination=destinations[last])
        new = doc["second_hop_template"].format(
            link=row["links"][last], destination=destinations[1 - last])
        assert informative.endswith(old)
        assert lex_informative == informative[:-len(old)] + new
        assert lex.user_text.endswith(bridge)
        signs.add(patch.symbolic_source_sign(cell, row))
    assert signs == {-1, 1}


def _synthetic_rows(full: float, lexical: float):
    cells, doc, domains = _fixture()
    rows, pair_metrics = {}, {}
    treatment = {"none": 0., "zero": 0., "full": full,
                 "lex_natural": lexical, "lex_matched": lexical,
                 "plan_matched": .01, "random": 0., "last_block": 0.}
    for cell in cells:
        sign = patch.symbolic_source_sign(cell, domains[cell.domain])
        pair_metrics[cell.id] = {"source_sign": sign, "full_norm": 10.,
                                 "lexical_norm": 8., "lexical_over_full_norm": .8,
                                 "plan_norm": 4.}
        for arm, value in treatment.items():
            by_name = {cell.plan_a_name: sign * value, cell.plan_b_name: 0.}
            rows[f"{cell.id}|{arm}"] = {"scores": [by_name[c] for c in
                                                  cell.candidates], "flagged": False}
    token_audit = {d["id"]: [0] if d["id"] in patch.MATCHED else [-1, 1]
                   for d in doc["domains"]}
    captures = {c.id: {"relative_l2_error": 0.} for c in cells}
    return cells, rows, pair_metrics, token_audit, captures


def test_positive_causal_and_beyond_noun_gates_are_separate():
    cells, rows, metrics, token_audit, captures = _synthetic_rows(.50, .20)
    report = patch.analyze(cells, rows, metrics, token_audit, captures,
                           {"row_zero_only_refused": True}, {"shortest": 0.,
                                                              "longest": 0.})
    assert report["full_causal_screen"]
    assert report["beyond_last_noun_screen"]
    assert report["primary_full_effect"]["exact_null"]["p_ge_observed"] == 1 / 256
    assert all(v["exact_null"]["p_ge_observed"] == 1 / 32 for v in
               report["beyond_last_noun_surplus"].values())
    assert report["choice_flips"]["toward_source"] == 128

    cells, rows, metrics, token_audit, captures = _synthetic_rows(.50, .50)
    report = patch.analyze(cells, rows, metrics, token_audit, captures,
                           {"row_zero_only_refused": True}, {"shortest": 0.,
                                                              "longest": 0.})
    assert report["full_causal_screen"]
    assert not report["beyond_last_noun_screen"]
