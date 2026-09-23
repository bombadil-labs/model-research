"""Statistics and decision logic for hour 65 (scripts/shame_axis/shame_pain.py)."""
import itertools
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[2] / "scripts/shame_axis"))
import shame_pain as sp  # noqa: E402


def test_exact_signflip_matches_brute_force():
    rng = np.random.default_rng(0)
    d = rng.normal(0.3, 1, 10)
    brute = np.mean([np.mean(np.array(s) * d) >= d.mean() - 1e-12
                     for s in itertools.product((-1, 1), repeat=10)])
    assert sp.signflip_p(d, rng) == brute


def test_signflip_floor_and_identity():
    rng = np.random.default_rng(1)
    assert sp.signflip_p(np.ones(20), rng) == 1 / 2 ** 20
    p40 = sp.signflip_p(np.ones(40), rng)
    assert p40 == 1 / sp.N_FLIP40


def test_alpha_is_effect_at_equal_valence():
    dv = np.linspace(-1, 1, 40)
    a, b = sp.alpha_fit(0.5 + 2 * dv, dv)
    assert abs(a - 0.5) < 1e-12 and abs(b - 2) < 1e-12


def _rep(track, pos=True, alpha_lo=0.1):
    cell = lambda t: {"tracks_shame": t, "alpha_ci": [alpha_lo, 1.0]}
    return {k: {"positive_control_pass": pos, "cells": {a: cell(track[(k, a)]) for a in sp.AUTHORS}}
            for k in ("g2b_it", "l70_it")}


def test_decision_rules():
    all_true = {(k, a): True for k in ("g2b_it", "l70_it") for a in sp.AUTHORS}
    assert sp.decide(_rep(all_true))["status"] == "holds"
    none = {k: False for k in all_true}
    assert sp.decide(_rep(none, alpha_lo=-0.1))["status"] == "falsified"
    # no cell tracks shame, but valence-adjusted alpha is positive somewhere: not falsified
    assert sp.decide(_rep(none, alpha_lo=0.1))["status"] == "narrowed"
    one_author = {(k, a): a == "claude" for k, a in all_true}
    assert sp.decide(_rep(one_author))["status"] == "narrowed"
    assert sp.decide(_rep(all_true, pos=False))["status"] == "open"
    assert sp.decide({"g2b_it": _rep(all_true)["g2b_it"]})["status"] == "incomplete"


def test_items_are_the_committed_stimuli():
    rows = sp.items()
    assert len(rows) == 200
    assert sum(r["arm"] == "base" for r in rows) == 40
    assert all(r["text"].endswith(". I feel:") for r in rows)


def test_cell_needs_its_positive_control():
    cell = {"delta": 0.5, "p": 0.001, "clears_nulls": True, "network_contribution_ci": [0.1, 0.9],
            "alpha_ci": [0.1, 0.9], "delta_D": 0.4, "p_D": 0.001}
    assert sp.tracks_shame(cell, True)
    assert not sp.tracks_shame(cell, False)
    for k, bad in (("delta_D", -0.1), ("p_D", 0.2), ("alpha_ci", [-0.1, 0.9]), ("clears_nulls", False)):
        assert not sp.tracks_shame({**cell, k: bad}, True)
