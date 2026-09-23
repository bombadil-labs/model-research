"""The fact flip is the only source of a positive paired plan margin."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import pytest


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "fact_flip_twohop_test_target", SCRIPTS / "fact_flip_twohop.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _saved(cells, margin):
    rows = {}
    for cell in cells:
        scores = {cell.plan_a_name: float(margin(cell)), cell.plan_b_name: 0.0}
        rows[cell.id] = {"scores": [scores[name] for name in cell.candidates]}
    return rows


def test_grid_crosses_orders_and_preserves_world_word_bag():
    controls, stories, duplicates, generated, doc, _ = module.make_cells()
    assert (len(controls), len(stories), len(duplicates), len(generated)) == (
        64, 128, 8, 32)
    assert module.shortcut_baselines(doc) == {
        "bag_world_difference_tokens": 0,
        "plan_world_difference_tokens": 0,
        "direct_route_target_cooccurrences": 0,
        "same_ordinal_correct_domain_fraction": .5,
        "target_first_correct_domain_fraction": .5,
        "symbolic_graph_cell_accuracy": 1.0}
    for cells in (controls, stories):
        for a, b in zip(cells[::2], cells[1::2]):
            assert (a.world, b.world) == (0, 1)
            assert (a.plan_a_name, a.plan_b_name) == (
                b.plan_a_name, b.plan_b_name)
            assert module._words(a.user_text) == module._words(b.user_text)
            assert a.user_text[-200:] == b.user_text[-200:]
    assert [c.id for c in duplicates] == [f"duplicate:{i:02d}" for i in range(8)]
    assert len({c.domain for c in controls} & {c.domain for c in stories}) == 0


def test_paired_shift_cancels_fixed_name_bias_and_detects_symbolic_signal():
    controls, stories, duplicates, _, doc, _ = module.make_cells()
    ideal = _saved(controls + stories, lambda c: 2 if c.world == 0 else -2)
    ideal.update(_saved(duplicates, lambda c: 2))
    direct = module.paired_report(controls, ideal, doc["controls"],
                                  treatment=False)
    primary = module.paired_report(stories, ideal, doc["domains"],
                                   treatment=True, n_boot=100)
    repeat = module.repeat_report(stories, duplicates, ideal)
    assert direct["gate_pass"] and direct["correct_shifts"] == 32
    assert primary["gate_pass_without_controls"]
    assert primary["correct_shifts"] == 64
    assert primary["exact_orientation_null"]["p_ge_observed"] == 1 / 256
    assert all(v == 1 for v in primary["fact_order_quadrants"].values())
    assert repeat["gate_pass"] and repeat["max_abs_margin_difference"] == 0

    name_bias = _saved(controls + stories,
                       lambda c: 2 if c.plan_a_name == c.candidates[0] else -2)
    direct_bias = module.paired_report(controls, name_bias, doc["controls"],
                                       treatment=False)
    story_bias = module.paired_report(stories, name_bias, doc["domains"],
                                      treatment=True, n_boot=100)
    assert direct_bias["correct_shifts"] == 0
    assert story_bias["correct_shifts"] == 0
    assert not direct_bias["gate_pass"]
    assert not story_bias["gate_pass_without_controls"]


def test_same_clause_ordinal_shortcut_fails_two_quadrants():
    _, stories, _, _, doc, _ = module.make_cells()
    orders = {row["id"]: tuple(row["fact_order"]) for row in doc["domains"]}

    def margin(cell):
        rule_right = orders[cell.domain][0] == orders[cell.domain][1]
        return (2 if cell.world == 0 else -2) * (1 if rule_right else -1)

    saved = _saved(stories, margin)
    report = module.paired_report(stories, saved, doc["domains"],
                                  treatment=True, n_boot=100)
    assert report["correct_shift_fraction"] == .5
    assert report["fact_order_quadrants"] == {
        "00": 1.0, "01": 0.0, "10": 0.0, "11": 1.0}
    assert not report["gate_pass_without_controls"]


def test_cache_rejects_changed_fingerprint_and_duplicate(tmp_path):
    path = tmp_path / "cells.jsonl"
    path.write_text('{"id":"x","fp":"old","scores":[1.0,0.0]}\n')
    with pytest.raises(ValueError, match="stale or duplicate"):
        module._load_cache(path, {"x": "new"}, generation=False)
    path.write_text(path.read_text() * 2)
    with pytest.raises(ValueError, match="stale or duplicate"):
        module._load_cache(path, {"x": "old"}, generation=False)


def test_generated_answer_requires_one_name():
    names = ("Lena", "Mara")
    assert module.parse_generation("Mara.\n", names) == "Mara"
    assert module.parse_generation("Lena", names) == "Lena"
    assert module.parse_generation("I choose Mara", names) is None
    assert module.parse_generation("Mara or Lena", names) is None
