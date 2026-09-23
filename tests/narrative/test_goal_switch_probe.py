"""The interaction cancels goal and recipient main effects and honors exact nulls."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("goal_switch_probe_test_target",
                                               SCRIPTS / "goal_switch_probe.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_frozen_grid_has_linked_and_rotated_goal_pairs():
    grids, digest = module.make_cases(module.GRID)
    assert len(digest) == 64
    assert len(grids["linked"]) == len(grids["rotated"]) == 96
    assert len({c.domain for c in grids["linked"]}) == 12
    for kind in grids:
        cases = grids[kind]
        for i in range(0, 96, 4):
            assert cases[i].text[-200:] == cases[i + 2].text[-200:]
            assert cases[i + 1].text[-200:] == cases[i + 3].text[-200:]


def test_goal_recipient_interaction_survives_main_effects_only_in_linked_grid():
    shape = (12, 2, 2, 2, 29, 4)
    linked, rotated = np.zeros(shape, np.float32), np.zeros(shape, np.float32)
    pre = np.zeros(shape, np.float32)
    for goal in (0, 1):
        for recipient in (0, 1):
            sg, sr = 1 - 2 * goal, 1 - 2 * recipient
            linked[:, :, goal, recipient, 1:, 0] = sg * sr
            rotated[:, :, goal, recipient, 1:, 1] = sg * sr
            for x in (linked, rotated):
                x[:, :, goal, recipient, 1:, 2] = 3 * sg
                x[:, :, goal, recipient, 1:, 3] = 2 * sr
            pre[:, :, goal, recipient, 1:, 2] = 3 * sg

    report = module.score({"linked": (linked, pre), "rotated": (rotated, pre)},
                          n_null=10, n_boot=20)
    assert report["arms"]["linked"]["mid"] == 1
    assert report["arms"]["linked_to_rotated"]["mid"] == .5
    assert report["arms"]["rotated"]["mid"] == 1
    assert report["arms"]["pre_action"]["mid"] == .5
    assert report["arms"]["no_goal"]["mid"] == .5
