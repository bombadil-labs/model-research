"""The goal-reversal decision rule must survive name and sentence crossing."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "goal_reversal_behavior_test_target", SCRIPTS / "goal_reversal_behavior.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _scores(cells, margin):
    saved = {}
    for cell in cells:
        a_score = margin(cell)
        scores = {cell.plan_a_name: a_score, cell.plan_b_name: 0.0}
        saved[cell.id] = {"scores": [scores[name] for name in cell.candidates]}
    return saved


def test_frozen_grid_and_lexical_ceiling():
    cal, stories, neutral, generated, doc, _ = module.make_cells()
    assert (len(cal), len(stories), len(neutral), len(generated)) == (32, 192, 48, 48)
    assert all(a.user_text != b.user_text for a, b in zip(stories[::2], stories[1::2]))
    for a, b in zip(stories[::2], stories[1::2]):
        assert a.plan_a_name == b.plan_a_name
        assert a.plan_b_name == b.plan_b_name
        assert a.user_text.replace(doc["domains"][int(a.id.split(":")[1])]["goals"][0][a.paraphrase], "<GOAL>", 1) == \
            b.user_text.replace(doc["domains"][int(b.id.split(":")[1])]["goals"][1][b.paraphrase], "<GOAL>", 1)
    base = module.lexical_baselines(doc)
    assert base["goal_type_to_withhold_accuracy"] == .5
    assert base["goal_type_to_contain_accuracy"] == .5
    assert base["goal_category_to_semantic_accuracy"] == 45 / 48
    assert base["goal_category_correct_reversal"] == 21 / 24


def test_calibration_rejects_name_and_position_bias():
    cal, _, _, _, _, _ = module.make_cells()
    ideal = _scores(cal, lambda c: 2 if c.goal == 0 else -2)
    assert module.calibration_report(cal, ideal)["gate_pass"]
    name_bias = _scores(cal, lambda c: 2 if c.plan_a_name == c.candidates[0] else -2)
    assert not module.calibration_report(cal, name_bias)["gate_pass"]
    position_bias = _scores(cal, lambda c: 2 if c.plan_order == 0 else -2)
    assert not module.calibration_report(cal, position_bias)["gate_pass"]


def test_story_gate_requires_correct_reversal_across_both_names():
    _, stories, neutral, _, doc, _ = module.make_cells()
    saved = _scores(stories, lambda c: 2 if c.goal == 0 else -2)
    saved.update(_scores(neutral, lambda c: 1))
    ideal = module.story_report(stories, neutral, saved, doc, n_boot=100)
    assert ideal["correct_reversal_fraction"] == 1
    assert ideal["both_name_assignments_fraction"] == 1
    assert ideal["exact_orientation_null"]["p_ge_observed"] == 1 / 4096
    assert ideal["gate_pass_without_generation"]

    # A consistent preference for one name can pass a naive cell average but
    # cannot reverse with the goal once the plans exchange names.
    saved = _scores(stories, lambda c: 2 if c.plan_a_name == c.candidates[0] else -2)
    saved.update(_scores(neutral, lambda c: 1))
    biased = module.story_report(stories, neutral, saved, doc, n_boot=100)
    assert biased["correct_reversal_fraction"] == 0
    assert not biased["gate_pass_without_generation"]


def test_generated_answer_must_be_one_bare_name():
    names = ("Lena", "Mara")
    assert module.parse_generation("Mara.\n", names) == "Mara"
    assert module.parse_generation("Lena", names) == "Lena"
    assert module.parse_generation("I choose Mara", names) is None
    assert module.parse_generation("Mara or Lena", names) is None
