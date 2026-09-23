"""The exploratory distance metric detects a rotated domain geometry."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("goal_relative_rdm_test_target",
                                               SCRIPTS / "goal_relative_rdm.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_distance_geometry_survives_rotation_and_requires_domain_match():
    rng = np.random.default_rng(5)
    base = rng.normal(size=(12, 29, 8))
    rotation, _ = np.linalg.qr(rng.normal(size=(8, 8)))
    state = np.stack([base, base @ rotation, base @ rotation.T, -base], axis=1)
    assert np.isclose(module.rdm_transfer(state), 1)
    assert module.rdm_transfer(state, np.roll(np.arange(12), 1)) < .5


def test_effects_remove_main_effects_from_interaction():
    final = np.zeros((12, 2, 2, 2, 2, 29, 3), dtype=float)
    for world in (0, 1):
        for recipient in (0, 1):
            final[:, :, :, world, recipient, 1:, 0] = 1 - 2 * world
            final[:, :, :, world, recipient, 1:, 1] = 1 - 2 * recipient
            final[:, :, :, world, recipient, 1:, 2] = (
                (1 - 2 * world) * (1 - 2 * recipient))
    result = module.effects(final)
    assert np.all(result["interaction"][..., :2] == 0)
    assert np.all(result["world_main"][..., 1:] == 0)
    assert np.all(result["recipient_main"][..., (0, 2)] == 0)
