"""The h8 readout's permutation arm, calibrated on synthetic SIGNAL as well as noise.

`test_core_phase2.test_the_readout_battery_reads_chance_on_noise_in_every_arm` checks every arm on
activations that carry no factor. That is the noise half of the calibration rule in
`docs/DELEGATION.md`; this is the signal half, and it is the half open problem 4i needed. Hour 48
saw the permutation arm below chance on 25 of 25 rows and attributed it to the uncentered cosine
ranking being "partly a norm ranking". The labels are shuffled before the fit, so the permuted
level directions are exchangeable and the arm's mean is chance in expectation under any scoring
function. These tests hold the arm to that on a grid with a strong factor signal, a large shared
component (so the cosine is far from centered) and norms that depend on level, which is the
condition under which a norm ranking would have to show up.
"""
from __future__ import annotations

import numpy as np

from lsx.narrative import phase2


def _signal_grid(norm_spread: float, seed: int = 7) -> tuple[dict, dict]:
    gs = phase2.normalized_grid("narrative_factors_v1")
    names = list(gs["factors"])
    gen = np.random.default_rng(seed)
    d = 48
    common = gen.normal(size=d) * 4.0
    dirs = {n: {lvl: gen.normal(size=d) for lvl in gs["factors"][n]} for n in names}
    X = {}
    for key in gs["spans"]:
        lv = dict(zip(names, key.split("/")[1:]))
        v = common + sum(3.0 * dirs[n][lv[n]] for n in names) + gen.normal(size=d) * 2.0
        v = v * np.prod([1 + norm_spread * gs["factors"][n].index(lv[n]) for n in names])
        X[key] = np.tile(v, (2, 1))
    return gs, X


def _perm_devs(gs: dict, X: dict, seeds: range) -> dict:
    out = {n: [] for n in ["composed", *gs["factors"]]}
    for s in seeds:
        b = phase2.readout_battery(X, gs, 1, n_perm=4, n_rand=0, seed=s)
        out["composed"].append(np.mean(b["composed"]["perm"]) - 5.0)
        for n in gs["factors"]:
            out[n].append(np.mean(b["B"][n]["perm"]) - 2.0)
    return {k: np.array(v) for k, v in out.items()}


def test_the_permutation_arm_is_unbiased_on_a_strong_signal_grid_with_level_dependent_norms():
    gs, X = _signal_grid(norm_spread=1.0)
    b = phase2.readout_battery(X, gs, 1, n_perm=0, n_rand=0)
    # the grid really carries the signal the arm must not leak: the treatment is a perfect lens
    assert all(np.mean(b["B"][n]["treatment"]) == 1.0 for n in gs["factors"])
    for name, dev in _perm_devs(gs, X, range(60)).items():
        se = dev.std(ddof=1) / np.sqrt(len(dev))
        assert abs(dev.mean()) < 4 * se, (name, dev.mean(), se)

