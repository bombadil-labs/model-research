"""The activation pilot preserves the sign of the goal × route interaction."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "goal_route_activation_pilot_test_target",
    SCRIPTS / "goal_route_activation_pilot.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _states(stories, repeats, *, reverse_late=False, position_code=True):
    saved = {}
    for cell in stories + repeats:
        sign = (1 if cell.world == cell.goal else -1)
        if position_code and cell.plan_order == 1:
            sign *= -1
        if reverse_late and cell.telling == 1:
            sign *= -1
        vec = np.zeros((len(module.BLOCKS), 8), dtype=np.float32)
        vec[:, 0] = sign
        saved[cell.id] = vec
    return saved


def test_synthetic_interaction_transfers_across_domains_and_tellings():
    stories, repeats, _, _ = module._cells()
    saved = _states(stories, repeats)
    report = module.analyze(stories, repeats, saved, n_boot=100, n_random=10)
    assert report["candidate_aligned_interaction"]
    assert np.allclose(report["transfer_curve"], 1)
    assert np.allclose(report["raw_a_oriented_transfer_curve"], 0)
    assert report["exact_orientation_null"]["p_ge_observed"] == 2 / 256
    assert report["positive_domains_by_target_telling"] == [8, 8]
    assert report["max_repeat_l2_by_block"] == [0] * len(module.BLOCKS)


def test_telling_sign_reversal_fails_directed_transfer():
    stories, repeats, _, _ = module._cells()
    saved = _states(stories, repeats, reverse_late=True)
    report = module.analyze(stories, repeats, saved, n_boot=100, n_random=10)
    assert np.allclose(report["transfer_curve"], -1)
    assert not report["candidate_aligned_interaction"]
    assert report["positive_domains_by_target_telling"] == [0, 0]


def test_a_owner_code_cancels_after_position_orientation():
    stories, repeats, _, _ = module._cells()
    saved = _states(stories, repeats, position_code=False)
    report = module.analyze(stories, repeats, saved, n_boot=100, n_random=10)
    assert np.allclose(report["transfer_curve"], 0)
    assert np.allclose(report["raw_a_oriented_transfer_curve"], 1)
    assert not report["candidate_aligned_interaction"]


def test_word_bag_and_local_interactions_are_measured_zero():
    stories, _, _, _ = module._cells()
    assert module._surface_nulls(stories) == {
        "max_abs_full_bag_interaction": 0,
        "max_abs_last_200_char_bag_interaction": 0}
