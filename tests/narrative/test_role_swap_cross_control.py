"""A balanced held-out score must separate role content from sentence order."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("role_swap_cross_control_test_target",
                                               SCRIPTS / "role_swap_cross_control.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_order_artifact_does_not_count_as_goal_transfer():
    goal = np.zeros((12, 2, 29, 3), dtype=float)
    neutral = np.zeros_like(goal)
    goal[..., 0] = 1
    neutral[..., 2] = 1
    goal[:, 0, :, 1] = neutral[:, 0, :, 1] = 3
    goal[:, 1, :, 1] = neutral[:, 1, :, 1] = -3
    goal, neutral = module.unit(goal), module.unit(neutral)

    self_scores, _ = module.cross_scores(goal, goal)
    cross_scores, _ = module.cross_scores(goal, neutral)
    same_order = module.order_scores(goal, neutral, reverse=False)
    reverse_order = module.order_scores(goal, neutral, reverse=True)

    assert np.all(self_scores == 1)
    assert np.all(cross_scores == .5)
    assert np.all(same_order == 1)
    assert np.all(reverse_order == 0)
