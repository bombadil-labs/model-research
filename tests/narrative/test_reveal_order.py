"""The late-reveal test keeps the truth table fixed across three text orders."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "reveal_order_test_target", SCRIPTS / "reveal_order.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _saved(cells, margin):
    rows = {}
    for cell in cells:
        scores = {cell.plan_a_name: float(margin(cell)), cell.plan_b_name: 0.0}
        rows[cell.id] = {"scores": [scores[name] for name in cell.candidates]}
    return rows


def test_grid_and_symbolic_reader():
    controls, stories, repeats, source, _, bags = module.make_cells()
    assert (len(controls), len(stories), len(repeats)) == (192, 384, 24)
    assert bags == {"full_interaction_l1_max": 0,
                    "suffix_interaction_l1_max": 0,
                    "n_measured_quartets": 144}
    for group in (controls, stories):
        for i in range(0, len(group), 4):
            assert [(c.world, c.goal) for c in group[i:i + 4]] == [
                (0, 0), (0, 1), (1, 0), (1, 1)]

    saved = _saved(controls + stories + repeats,
                   lambda c: 2 if c.world == c.goal else -2)
    control = module.report_group(controls, saved, source["controls"],
                                  treatment=False)
    story = module.report_group(stories, saved, source["domains"],
                                treatment=True)
    repeat = module.repeat_report(stories, repeats, saved)
    assert all(x["joint_success"] == 16 for x in control["formats"].values())
    assert all(x["joint_success"] == 32 for x in story["formats"].values())
    assert story["paired"]["all_format_success"] == 32
    assert story["paired"]["exact_orientation_null"]["p_ge_observed"] == 1 / 256
    assert all(x["gate_pass"] for x in story["formats"].values())
    assert story["paired"]["gate_pass"]
    assert repeat["gate_pass"] and repeat["max_abs_margin_difference"] == 0


def test_ordinal_shortcut_and_reveal_only_failure():
    _, stories, _, source, _, _ = module.make_cells()
    same = {row["id"]: row["fact_order"][0] == row["fact_order"][1]
            for row in source["domains"]}
    ordinal = _saved(stories, lambda c: (2 if c.world == c.goal else -2) *
                     (1 if same[c.domain] else -1))
    report = module.report_group(stories, ordinal, source["domains"],
                                 treatment=True)
    assert report["paired"]["all_format_success"] == 16
    assert report["formats"]["chronological"]["fact_order_quadrants"] == {
        "00": 1.0, "01": 0.0, "10": 0.0, "11": 1.0}
    assert not report["formats"]["chronological"]["gate_pass"]

    reveal_bad = _saved(stories, lambda c: (2 if c.world == c.goal else -2) *
                        (-1 if c.telling == 1 else 1))
    report = module.report_group(stories, reveal_bad, source["domains"],
                                 treatment=True)
    assert report["formats"]["chronological"]["joint_success"] == 32
    assert report["formats"]["late_reveal"]["joint_success"] == 0
    assert report["formats"]["near_adjacent"]["joint_success"] == 32
    assert report["paired"]["all_format_success"] == 0
    assert not report["paired"]["gate_pass"]
