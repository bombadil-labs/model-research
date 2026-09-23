"""The crossed goal and route graph must defeat single-factor readouts."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "goal_route_cross_test_target", SCRIPTS / "goal_route_cross.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _saved(cells, margin):
    rows = {}
    for cell in cells:
        scores = {cell.plan_a_name: float(margin(cell)), cell.plan_b_name: 0.0}
        rows[cell.id] = {"scores": [scores[name] for name in cell.candidates]}
    return rows


def test_grid_has_four_cell_truth_table_and_matched_worlds():
    controls, stories, duplicates, generations, doc, _ = module.make_cells()
    assert (len(controls), len(stories), len(duplicates), len(generations)) == (
        128, 256, 16, 64)
    assert module.shortcut_baselines(doc) == {
        "goal_only_joint_success": 0.0,
        "world_only_joint_success": 0.0,
        "same_ordinal_joint_success": .5,
        "target_first_joint_success": .5,
        "symbolic_graph_joint_success": 1.0}
    for group in (controls, stories):
        for i in range(0, len(group), 4):
            four = group[i:i + 4]
            assert [(c.world, c.goal) for c in four] == [
                (0, 0), (0, 1), (1, 0), (1, 1)]
            for goal in (0, 1):
                a, b = four[goal], four[2 + goal]
                assert module.base._words(a.user_text) == module.base._words(b.user_text)
                assert len(a.user_text) == len(b.user_text)
                assert a.user_text[-200:] == b.user_text[-200:]
    assert [c.id for c in duplicates] == [
        f"duplicate:{di:02d}:{goal}" for di in range(8) for goal in (0, 1)]


def test_symbolic_interaction_passes_and_single_factor_rules_fail():
    controls, stories, duplicates, _, doc, _ = module.make_cells()
    ideal = _saved(controls + stories,
                   lambda c: 2 if c.world == c.goal else -2)
    ideal.update(_saved(duplicates, lambda c: 2 if c.world == c.goal else -2))
    control = module.paired_report(controls, ideal, doc["controls"], treatment=False)
    story = module.paired_report(stories, ideal, doc["domains"],
                                 treatment=True, n_boot=100)
    repeat = module.repeat_report(stories, duplicates, ideal)
    assert control["gate_pass"] and control["joint_success"] == 32
    assert story["gate_pass_without_controls"]
    assert story["joint_success"] == 64
    assert story["goal_0_correct_shifts"] == 64
    assert story["goal_1_correct_shifts"] == 64
    assert story["strict_four_cell_choices"] == 64
    assert story["exact_orientation_null"]["p_ge_observed"] == 1 / 256
    assert repeat["gate_pass"] and repeat["max_abs_margin_difference"] == 0

    for margin in (lambda c: 2 if c.goal == 0 else -2,
                   lambda c: 2 if c.world == 0 else -2,
                   lambda c: 2 if c.plan_a_name == c.candidates[0] else -2):
        saved = _saved(stories, margin)
        report = module.paired_report(stories, saved, doc["domains"],
                                      treatment=True, n_boot=100)
        assert report["joint_success"] == 0
        assert not report["gate_pass_without_controls"]


def test_ordinal_shortcut_fails_crossed_fact_order_quadrants():
    _, stories, _, _, doc, _ = module.make_cells()
    same = {row["id"]: row["fact_order"][0] == row["fact_order"][1]
            for row in doc["domains"]}
    saved = _saved(stories, lambda c: (2 if c.world == c.goal else -2) *
                   (1 if same[c.domain] else -1))
    report = module.paired_report(stories, saved, doc["domains"],
                                  treatment=True, n_boot=100)
    assert report["joint_success"] == 32
    assert report["fact_order_quadrants"] == {
        "00": 1.0, "01": 0.0, "10": 0.0, "11": 1.0}
    assert not report["gate_pass_without_controls"]


def test_generation_four_cell_mapping():
    _, stories, _, generations, _, _ = module.make_cells()
    saved = _saved(stories, lambda c: 2 if c.world == c.goal else -2)
    generated = {c.id: {"text": (c.plan_a_name if c.world == c.goal
                                 else c.plan_b_name) + "."} for c in generations}
    report = module.generation_report(generations, saved, generated)
    assert report["parseable_fraction"] == 1
    assert report["forced_choice_agreement"] == 1
    assert report["all_four_correct_sets"] == 16
