"""Factor-orientation checks for the frozen first-hop behavioral gate."""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/narrative"))

import firsthop_swap_behavior as behavior
import firsthop_swap_grid as grid


def _scores(cells, rule):
    saved = {}
    for cell in cells:
        margin = float(rule(cell))
        a = cell.candidates.index(cell.plan_a_name)
        scores = [0.0, 0.0]
        scores[a], scores[1 - a] = margin / 2, -margin / 2
        saved[cell.id] = {"scores": scores}
    return saved


def test_graph_correct_choices_pass_joint_and_strict_gate():
    cells, _, _ = grid.make_cells()
    doc = json.loads((grid.ROOT / "research/narrative/prompts/goal_route_cross_v1.json").read_text())
    scores = _scores(cells, lambda c: 2 if c.world == c.goal else -2)
    report = behavior._analyze(cells, scores, doc, {}, {})
    assert report["eligible_for_patch"]
    assert report["joint_success"] == report["strict_four_cell_correct"] == 32
    assert report["baseline_source_winner_favoured_cells"] == 0
    assert report["exact_null"]["p_ge_observed"] == 1 / 256
    assert all(n == 8 for n in report["fact_order_quadrants"].values())


def test_world_only_choice_cannot_pass_both_goal_contrasts():
    cells, _, _ = grid.make_cells()
    doc = json.loads((grid.ROOT / "research/narrative/prompts/goal_route_cross_v1.json").read_text())
    scores = _scores(cells, lambda c: 2 if c.world == 0 else -2)
    report = behavior._analyze(cells, scores, doc, {}, {})
    assert report["joint_success"] == 0
    assert not report["eligible_for_patch"]
