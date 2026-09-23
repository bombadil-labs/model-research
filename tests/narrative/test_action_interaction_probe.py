"""The action contrast must retain event information after shared person binding cancels."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("action_interaction_probe_test_target",
                                               SCRIPTS / "action_interaction_probe.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_reverse_grid_keeps_pairs_and_pre_action_boundary():
    path = Path(__file__).resolve().parents[2] / "research/narrative/prompts/role_swap_v1.json"
    forward, reverse, _, pre = module.reverse_cases(path)
    assert len(forward) == len(reverse) == len(pre) == 48
    assert all(forward[i].text[:pre[i] + 1] == reverse[i].text[:pre[i] + 1]
               for i in range(48))
    assert all(reverse[i].text[-200:] == reverse[i + 1].text[-200:]
               for i in range(0, 48, 2))


def test_action_interaction_separates_binding_from_event_signal():
    shape = (12, 2, 2, 29, 4)
    gf, gr, gp = (np.zeros(shape, dtype=np.float32) for _ in range(3))
    nf, nr, np_ = (np.zeros(shape, dtype=np.float32) for _ in range(3))

    def set_delta(x, vec):
        vec = np.asarray(vec, dtype=np.float32)
        x[:, :, 0, 1:] = vec
        x[:, :, 1, 1:] = -vec

    set_delta(gf, [1, 2, 0, 0])
    set_delta(gr, [1, -2, 0, 0])
    set_delta(gp, [1, 0, 0, 0])
    set_delta(nf, [0, 0, 1, 1])
    set_delta(nr, [0, 0, 1, -1])
    set_delta(np_, [0, 0, 1, 0])

    report = module.score({"goal": gf, "neutral": nf},
                          {"goal": (gr, gp), "neutral": (nr, np_)},
                          n_null=10, n_boot=20)
    arms = report["arms"]
    assert arms["goal_action_interaction"]["mid"] == 1
    assert arms["goal_to_neutral_action_interaction"]["mid"] == .5
    assert arms["goal_pre_action_binding"]["mid"] == 1
    assert arms["goal_reverse_event"]["mid"] == 1
    assert arms["no_action"]["mid"] == .5
