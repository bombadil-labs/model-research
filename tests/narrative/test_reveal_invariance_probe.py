"""The scorer separates an invariant relation from timing and clause-order cues."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("reveal_invariance_probe_test_target",
                                               SCRIPTS / "reveal_invariance_probe.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_grid_keeps_world_and_telling_words_fixed():
    cases, digest = module.make_cases(module.GRID)
    assert len(cases) == 192 and len(digest) == 64
    assert [cases[i].domain for i in range(0, 192, 16)] == [
        d["id"] for d in module.json.loads(module.GRID.read_text())["domains"]]
    assert module.lexical_baseline(cases, mode="local") == .5
    assert module.lexical_baseline(cases, mode="whole") == .5
    assert module.lexical_baseline(cases, mode="recipient_clause") > .5


def _stacks(kind: str) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    shape = (12, 2, 2, 2, 2, 29, 4)
    final = np.zeros(shape, np.float32)
    bridge = np.zeros(shape, np.float32)
    body = np.zeros(shape, np.float32)
    for timing in (0, 1):
        for clause in (0, 1):
            for world in (0, 1):
                for recipient in (0, 1):
                    sign = (1 - 2 * world) * (1 - 2 * recipient)
                    if kind == "relation":
                        factor = 1
                    elif kind == "clause_order":
                        factor = 1 - 2 * clause
                    elif kind == "timing":
                        factor = 1 - 2 * timing
                    else:
                        raise ValueError(kind)
                    final[:, timing, clause, world, recipient, 1:, 0] = sign * factor
                    final[:, timing, clause, world, recipient, 1:, 1] = 2 * (1 - 2 * world)
                    final[:, timing, clause, world, recipient, 1:, 2] = 3 * (1 - 2 * recipient)
                    bridge[:, timing, clause, world, recipient, 1:, 1] = 2 * (1 - 2 * world)
                    if timing == 0:
                        body[:, timing, clause, world, recipient, 1:, 1] = 2 * (1 - 2 * world)
    return final, bridge, body


def test_doubly_transformed_transfers_refuse_position_artifacts():
    relation = module.score(_stacks("relation"), n_null=10, n_boot=20)
    assert relation["primary_mid"] == 1
    assert all(relation["arms"][f"{a}_to_{b}"]["mid"] == 1
               for a, b in module.PRIMARY_EDGES)
    assert relation["exact_arms"] == {"pre_handover": .5, "no_world": .5}
    assert relation["body_world_displacement_mid"]["late"] == 0
    assert relation["body_world_displacement_mid"]["early"] > 0

    for kind in ("clause_order", "timing"):
        artifact = module.score(_stacks(kind), n_null=10, n_boot=20)
        assert artifact["primary_mid"] == 0
        assert all(artifact["arms"][f"{f}_to_{f}"]["mid"] == 1
                   for f in range(4))
