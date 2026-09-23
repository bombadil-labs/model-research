"""The target-label null responds to a shared axis, not an unrelated one."""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
import choice_slot_replication as replication  # noqa: E402


def _fixture(axis: int) -> np.ndarray:
    h = np.zeros((8, 2, 2, 2, 2, 2, 6, 10), dtype=np.float64)
    for world in (0, 1):
        for goal in (0, 1):
            for order in (0, 1):
                truth = 1 if world == goal else -1
                h[:, :, :, order, world, goal, :, axis] = (
                    .25 * truth * (1 if order == 0 else -1))
    return h


def test_grid_crosses_truth_and_has_fixed_suffix():
    cells, _, _ = replication.make_cells()
    assert len(cells) == 256
    for i in range(0, len(cells), 4):
        quartet = cells[i:i + 4]
        assert [(c.world, c.goal) for c in quartet] == [
            (0, 0), (0, 1), (1, 0), (1, 1)]
        assert len({c.user_text[-200:] for c in quartet}) == 1
        assert all((c.plan_a_name if c.world == c.goal else c.plan_b_name)
                   in c.candidates for c in quartet)


def test_target_flip_null_has_power_for_shared_axis():
    source = _fixture(0)
    repeats = np.zeros((8, 6, 10))
    preflight = {"same_goal_token_length_fraction": 1.0,
                 "goal_1_minus_goal_0_tokens_by_quartet": [0] * 64}
    shared = replication.analyze(source, _fixture(0), repeats,
                                 {"gate_pass": True}, preflight, n_random=10)
    assert shared["route_to_target_block24"] == 1
    assert shared["target_orientation_null"]["p_ge_observed"] == 1 / 256
    assert shared["within_target_block24"] == 1
    assert shared["generic_component_compatible"]

    separate = replication.analyze(source, _fixture(1), repeats,
                                   {"gate_pass": True}, preflight, n_random=10)
    assert separate["route_to_target_block24"] == 0
    assert separate["within_target_block24"] == 1
    assert separate["target_orientation_null"]["p_ge_observed"] == 1
    assert not separate["generic_component_compatible"]
