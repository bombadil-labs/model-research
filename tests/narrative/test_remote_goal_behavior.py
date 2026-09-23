"""Remote choice ranking balances names, plan order and circumstance worlds."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("remote_goal_behavior_test_target",
                                               SCRIPTS / "remote_goal_behavior.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_grid_keeps_no_cue_twins_and_makes_only_declared_name_change():
    cal, stories, no_cue, digests = module.make_cells()
    assert (len(cal), len(stories), len(no_cue)) == (16, 96, 96)
    assert len(digests) == 2
    assert [(c.name_order, c.plan_order) for c in cal[:4]] == [
        (0, 0), (0, 1), (1, 0), (1, 1)]
    assert all("Oren" not in c.user_text for c in cal + stories + no_cue)
    assert any("Otto" in c.user_text for c in cal)
    for i in range(0, 96, 2):
        assert no_cue[i].user_text == no_cue[i + 1].user_text
        assert (no_cue[i].candidate_a, no_cue[i].candidate_b) == (
            no_cue[i + 1].candidate_a, no_cue[i + 1].candidate_b)


def test_calibration_and_story_gates_require_content_not_stable_name_bias():
    cal, stories, no_cue, _ = module.make_cells()
    saved = {c.id: {"scores": [2.0, 0.0]} for c in cal}
    positive = module.calibration_report(cal, saved)
    assert positive["gate_pass"] and positive["correct_of_16"] == 16
    saved[cal[1].id] = {"scores": [-1.0, 0.0]}
    assert not module.calibration_report(cal, saved)["gate_pass"]

    for c in stories:
        saved[c.id] = {"scores": [2.0 if c.world == 0 else -2.0, 0.0]}
    for c in no_cue:
        saved[c.id] = {"scores": [1.0, 0.0]}
    strong = module.story_report(stories, no_cue, saved)
    assert strong["cell_accuracy"] == 1
    assert strong["world_switch_fraction"] == 1
    assert strong["no_cue_world_switch_fraction"] == .5
    assert strong["gate_pass"]

    for c in stories:
        saved[c.id] = {"scores": [1.0, 0.0]}
    biased = module.story_report(stories, no_cue, saved, n_perm=10)
    assert biased["cell_accuracy"] == .5
    assert biased["world_switch_fraction"] == .5
    assert not biased["gate_pass"]
