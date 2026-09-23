"""Counterbalanced scorer distinguishes relation, clause position and plan polarity."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("consequence_order_probe_test_target",
                                               SCRIPTS / "consequence_order_probe.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_grid_is_balanced_and_mapping_words_match():
    cases, digest = module.make_cases(module.GRID)
    assert len(cases) == 192 and len(digest) == 64
    for group_start in range(0, 192, 16):
        group = cases[group_start:group_start + 16]
        assert len({x.domain for x in group}) == 1
        for task_order in (0, 1):
            block = group[task_order * 8:task_order * 8 + 8]
            for recipient in (0, 1):
                assert len({block[k].text[-200:] for k in
                            (recipient, recipient + 2, recipient + 4, recipient + 6)}) == 1


def _states(kind: str) -> tuple[np.ndarray, np.ndarray]:
    shape = (12, 2, 2, 2, 2, 29, 3)
    final = np.zeros(shape, dtype=np.float32)
    pre = np.zeros(shape, dtype=np.float32)
    polarity = np.array([d["a_has_original_active_task"]
                         for d in module.json.loads(module.GRID.read_text())["domains"]])
    for di in range(12):
        for clause in (0, 1):
            for mapping in (0, 1):
                for recipient in (0, 1):
                    sign = (1 - 2 * mapping) * (1 - 2 * recipient)
                    if kind == "relation":
                        factor = 1
                    elif kind == "clause_position":
                        factor = 1 - 2 * clause
                    elif kind == "active_polarity":
                        factor = 1 if polarity[di] else -1
                    else:
                        raise ValueError(kind)
                    final[di, :, clause, mapping, recipient, 1:, 0] = sign * factor
                    final[di, :, clause, mapping, recipient, 1:, 1] = 2 * (1 - 2 * mapping)
                    final[di, :, clause, mapping, recipient, 1:, 2] = 3 * (1 - 2 * recipient)
                    pre[di, :, clause, mapping, recipient, 1:, 1] = 2 * (1 - 2 * mapping)
    return final, pre


def test_cross_order_and_polarity_controls_on_synthetic_states():
    relation = module.score(_states("relation"), n_null=10, n_boot=20)
    assert relation["primary_cross_order_mid"] == 1
    assert relation["polarity_halves_mid"] == {"active_A": 1, "restrictive_A": 1}
    assert relation["arms"]["pre_action"]["mid"] == .5
    assert relation["arms"]["local_only"]["mid"] == .5

    position = module.score(_states("clause_position"), n_null=10, n_boot=20)
    assert position["primary_cross_order_mid"] == 0
    assert position["arms"]["within_clause_0"]["mid"] == 1
    assert position["arms"]["within_clause_1"]["mid"] == 1

    polarity = module.score(_states("active_polarity"), n_null=10, n_boot=20)
    assert polarity["primary_cross_order_mid"] == 0
    assert polarity["polarity_halves_mid"] == {"active_A": 0, "restrictive_A": 0}
