"""The role-swap scorer must detect a shared displacement and honor exact nulls."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/narrative/role_swap_probe.py"
spec = importlib.util.spec_from_file_location("role_swap_probe_test_target", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_grid_has_24_matched_pairs():
    grid = Path(__file__).resolve().parents[2] / "research/narrative/prompts/role_swap_v1.json"
    cases, _ = module.make_grid(grid)
    assert len(cases) == 48
    assert len({c.domain for c in cases}) == 12
    assert all(cases[i].text[-200:] == cases[i + 1].text[-200:]
               for i in range(0, len(cases), 2))


def test_scoring_detects_shared_relation_with_zero_controls():
    rng = np.random.default_rng(1)
    full = np.zeros((12, 2, 2, 29, 16), dtype=np.float32)
    local = np.zeros_like(full)
    for domain in range(12):
        for order in range(2):
            base = rng.normal(size=(29, 16)).astype(np.float32)
            full[domain, order, 0] = base
            full[domain, order, 1] = base
            full[domain, order, 0, 1:, 0] += 1
            full[domain, order, 1, 1:, 0] -= 1
    result = module.score(full, local, n_null=10, n_boot=20)
    assert result["mid_pair_accuracy"] == 1.0
    assert result["layer_0_pair_accuracy"] == .5
    assert result["local_only_pair_accuracy"] == .5
