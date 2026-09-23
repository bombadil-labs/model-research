"""The goal-relative scorer keeps semantic orientation separate from sentence order."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("goal_relative_probe_test_target",
                                               SCRIPTS / "goal_relative_probe.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_grid_declares_opposed_goal_service_and_has_no_bag_shortcut():
    cases, digest = module.make_cases(module.GRID)
    assert len(cases) == 192 and len(digest) == 64
    domains = module.json.loads(module.GRID.read_text())["domains"]
    assert [cases[i].domain for i in range(0, 192, 16)] == [d["id"] for d in domains]
    for di, d in enumerate(domains):
        assert {d["a_useful_status"], d["b_useful_status"]} == {
            d["good_status"], d["bad_status"]}
        assert d["a_useful_status"] in cases[di * 16].cue
        assert d["b_useful_status"] in cases[di * 16 + 2].cue
    for mode in ("local", "whole", "recipient_fact", "circumstance"):
        assert module.lexical_baseline(cases, mode=mode) == .5


def _stacks(kind: str) -> tuple[np.ndarray, np.ndarray]:
    shape = (12, 2, 2, 2, 2, 29, 4)
    final = np.zeros(shape, np.float32)
    bridge = np.zeros(shape, np.float32)
    for fact in (0, 1):
        for cue in (0, 1):
            for world in (0, 1):
                for recipient in (0, 1):
                    relation = (1 - 2 * world) * (1 - 2 * recipient)
                    if kind == "relation":
                        factor = 1
                    elif kind == "fact_order":
                        factor = 1 - 2 * fact
                    elif kind == "cue_order":
                        factor = 1 - 2 * cue
                    else:
                        raise ValueError(kind)
                    final[:, fact, cue, world, recipient, 1:, 0] = relation * factor
                    final[:, fact, cue, world, recipient, 1:, 1] = 2 * (1 - 2 * world)
                    final[:, fact, cue, world, recipient, 1:, 2] = 3 * (1 - 2 * recipient)
                    bridge[:, fact, cue, world, recipient, 1:, 1] = 2 * (1 - 2 * world)
    return final, bridge


def test_double_order_transfer_accepts_relation_and_rejects_order_signs():
    relation = module.score(_stacks("relation"), n_null=10, n_boot=20)
    assert relation["primary_mid"] == 1
    assert relation["transfer_groups_mid"] == {
        "within_format": 1, "fact_order_only": 1, "cue_order_only": 1}
    assert relation["exact_arms"] == {"pre_handover": .5, "no_world": .5}

    for kind in ("fact_order", "cue_order"):
        artifact = module.score(_stacks(kind), n_null=10, n_boot=20)
        assert artifact["primary_mid"] == 0
        assert artifact["transfer_groups_mid"]["within_format"] == 1
