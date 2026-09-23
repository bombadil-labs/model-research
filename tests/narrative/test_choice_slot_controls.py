"""The control grid and transfer analysis preserve the factorial role sign."""
from __future__ import annotations

from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
import choice_slot_analyze as analysis  # noqa: E402
import choice_slot_controls as controls  # noqa: E402


def test_property_grid_crosses_truth_with_name_and_sentence_order():
    cells, _, _ = controls.make_property_cells()
    assert len(cells) == 128
    for i in range(0, len(cells), 4):
        quartet = cells[i:i + 4]
        assert [(c.world, c.goal) for c in quartet] == [
            (0, 0), (0, 1), (1, 0), (1, 1)]
        assert all((c.plan_a_name if c.world == c.goal else c.plan_b_name)
                   in c.candidates for c in quartet)
        assert len({c.user_text[-200:] for c in quartet}) == 1
    # Swapping sentence order changes first-mentioned person without changing
    # role A, which is why the planned I_first sign flips on the order axis.
    a, b = cells[0], cells[4]
    assert a.plan_a_name == b.plan_a_name
    assert a.user_text.index(a.plan_a_name) < a.user_text.index(a.plan_b_name)
    assert b.user_text.index(b.plan_a_name) > b.user_text.index(b.plan_b_name)


def _fixture(n_domain: int, axis: int) -> np.ndarray:
    h = np.zeros((n_domain, 2, 2, 2, 2, 2, 6, 10), dtype=np.float64)
    for d in range(n_domain):
        for telling in (0, 1):
            for name in (0, 1):
                for order in (0, 1):
                    for world in (0, 1):
                        for goal in (0, 1):
                            truth = 1 if world == goal else -1
                            h[d, telling, name, order, world, goal, :, axis] = (
                                .25 * truth * (1 if order == 0 else -1))
    return h


def test_transfer_distinguishes_shared_from_task_specific_slot():
    source = _fixture(8, 0)
    direct = _fixture(4, 0)
    property_shared = _fixture(4, 0)
    property_other = _fixture(4, 1)
    repeats = {"direct": np.zeros((4, 6, 10)),
               "property": np.zeros((4, 6, 10))}
    behavior = {"direct": True, "property": True}
    preflight = {"direct": {"same_goal_token_length_fraction": 1.0,
                             "goal_1_minus_goal_0_tokens_by_quartet": [0] * 32},
                 "property": {"same_goal_token_length_fraction": 1.0,
                               "goal_1_minus_goal_0_tokens_by_quartet": [0] * 32}}
    shared = analysis.analyze(source, {"direct": direct,
                                       "property": property_shared},
                              repeats, behavior, preflight, n_random=10)
    assert shared["batteries"]["direct"]["route_to_target_primary"] == 1
    assert shared["batteries"]["property"]["within_target_primary"] == 1
    assert shared["property_to_route"]["primary"] == 1
    separate = analysis.analyze(source, {"direct": direct,
                                         "property": property_other},
                                repeats, behavior, preflight, n_random=10)
    assert separate["batteries"]["property"]["route_to_target_primary"] == 0
    assert separate["batteries"]["property"]["within_target_primary"] == 1
    assert separate["property_to_route"]["primary"] == 0
    assert separate["registered_reading"] == "task_dependent_code"
