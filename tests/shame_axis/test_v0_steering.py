"""Hour 62b's design, checked without NDIF: the cell enumeration, the random directions, the dose
arithmetic, and the per-chunk handling of the moved-candidates assertion."""
from __future__ import annotations

import importlib.util
import pathlib
import sys
from collections import Counter

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))
_spec = importlib.util.spec_from_file_location("v0_steering", ROOT / "scripts/shame_axis/v0_steering.py")
V = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(V)


def test_21_cells_per_item_with_the_right_arms():
    ids = ["a", "b", "c"]
    cells = V.enumerate_cells(ids)
    assert len(cells) == 21 * len(ids)
    for it in ids:
        mine = [c for c in cells if c["item"] == it]
        assert len(mine) == 21
        assert Counter(c["arm"] for c in mine) == {"no_patch": 1, "treatment": 4, "random": 12,
                                                    "pass_through": 4}
        assert mine[0]["arm"] == "no_patch" and mine[0]["alpha"] == 0.0   # base comes first
        for arm in ("treatment", "pass_through"):
            assert sorted(c["alpha"] for c in mine if c["arm"] == arm) == sorted(V.ALPHAS)
        rnd = [(c["dir"], c["alpha"]) for c in mine if c["arm"] == "random"]
        assert sorted(rnd) == sorted((f"rand{k}", a) for k in range(3) for a in V.ALPHAS)
        assert {c["layer"] for c in mine if c["arm"] in ("treatment", "random")} == {12}
        assert {c["layer"] for c in mine if c["arm"] == "pass_through"} == {41}
        assert {c["dir"] for c in mine if c["arm"] == "pass_through"} == {V.TREAT_DIR}
    assert len({V.cell_key(c) for c in cells}) == len(cells)         # resumable: keys unique
    assert 0.0 not in V.ALPHAS and sorted(V.ALPHAS) == [-0.2, -0.1, 0.1, 0.2]


def test_random_directions_unit_seeded_reproducible():
    r1, r2 = V.random_directions(), V.random_directions()
    assert r1.shape == (3, V.D_MODEL)
    np.testing.assert_allclose(np.linalg.norm(r1, axis=1), 1.0, atol=1e-12)
    np.testing.assert_array_equal(r1, r2)
    assert not np.allclose(r1, V.random_directions(seed=V.RANDOM_SEED + 1))
    assert len({tuple(np.round(x[:5], 12)) for x in r1}) == 3              # three distinct
    assert np.abs(r1 @ r1.T - np.eye(3)).max() < 0.1                       # near-orthogonal at d=3584


def test_shift_scale_arithmetic():
    hbar = 124.9353
    rnd = V.random_directions()
    u = rnd[0]
    for a in V.ALPHAS:
        s = V.shift_scale(a, hbar)
        assert s == pytest.approx(a * hbar)
        shift = u * s                                   # what remote.py adds: patch_vec * scale
        assert np.linalg.norm(shift) == pytest.approx(abs(a) * hbar)
        # random arm is norm-matched to treatment at the same alpha
        assert np.linalg.norm(rnd[1] * s) == pytest.approx(np.linalg.norm(shift))
    assert V.shift_scale(-0.2, hbar) == -V.shift_scale(0.2, hbar)


def test_total_mass_is_logsumexp():
    lp = np.array([-1.0, -2.0, -3.0, -40.0, -5.0, -6.0])
    assert V.total_mass(lp) == pytest.approx(np.log(np.exp(lp).sum()))


def test_moved_count_parses_the_library_message():
    from lsx.core import checks
    with pytest.raises(checks.MovedCandidates) as e:
        checks.assert_moved_candidates(np.zeros(6), np.array([1, 1, 0, 1, 1, 1.0]), batch=6)
    assert V._moved_count(str(e.value)) == (5, 6)


def test_h36_signature_aborts_but_a_quantised_non_move_does_not(monkeypatch):
    """Five of six moving is recorded. Row 0 alone moving is adjudicated at batch 1, where a
    batch-row bug cannot exist: abort if the other rows move there, record if they do not."""
    import lsx.core.remote as R
    from lsx.core import checks
    base = np.array([-17.0, -25.0, 0.0, -19.0, -35.0, -45.0])

    def fake(moved, batch1_moves=True):
        def f(rlm, lead, cands, *, base=None, **kw):
            n = len(cands)
            sc = np.full(n, -0.5 if ("patch_vec" in kw and batch1_moves) else -1.0)
            if base is not None:
                sc = base + np.array([1.0 if (j < moved if moved > 1 else j == 0) else 0.0 for j in range(n)])
                checks.assert_moved_candidates(base, sc, batch=n)
            return sc
        return f

    monkeypatch.setattr(R, "asserted_remote_patched_logprob", fake(5))
    lp, chunk, short = V._score(None, "x", np.ones(4), 1.0, 12, base)
    assert chunk == 6 and len(short) == 1 and short[0]["moved"] == 5
    # row 0 alone moved, and at batch 1 the other rows DO move: h36, abort
    monkeypatch.setattr(R, "asserted_remote_patched_logprob", fake(1))
    monkeypatch.setattr(V, "STRICT_H36", True)
    with pytest.raises(V.H36Signature):
        V._score(None, "x", np.ones(4), 1.0, 12, base)
    monkeypatch.setattr(V, "STRICT_H36", False)          # the rule after the reach checks
    lp, chunk, short = V._score(None, "x", np.ones(4), 1.0, 12, base)
    assert short[0]["batch1_check"]["rows_that_move_at_batch1"] == [1, 2, 3, 4, 5]
    # row 0 alone moved, and at batch 1 the other rows do not move either: grain, recorded
    monkeypatch.setattr(R, "asserted_remote_patched_logprob", fake(1, batch1_moves=False))
    lp, chunk, short = V._score(None, "x", np.ones(4), 1.0, 12, base)
    assert short and short[0]["batch1_check"]["unmoved_rows_at_batch1"]


def test_verdict_rule():
    treat = {-0.2: -1.0, -0.1: -0.5, 0.1: 0.5, 0.2: 1.0}
    rand = {0.1: [0.1, -0.1, 0.05, -0.05, 0.0, 0.02], 0.2: [0.2, -0.2, 0.1, -0.1, 0, 0.3]}
    pas = {a: 0.1 * a for a in treat}
    assert V.verdict_for(treat, rand, pas)["verdict"] == "causal on this readout"
    small = {a: 0.01 * np.sign(a) for a in treat}
    assert V.verdict_for(small, rand, pas)["verdict"] == "correlate, not cause"
    wrong = {a: -v for a, v in treat.items()}
    assert V.verdict_for(wrong, rand, pas)["verdict"] == "mixed"


def test_signflip_band_is_centered_and_detects_a_shift():
    rng = np.random.default_rng(0)
    sf = V.signflip(np.full(20, 1.0) + rng.normal(0, 0.1, 20), rng)
    assert sf["p"] < 0.001 and sf["band_lo"] < 0 < sf["band_hi"]
    sf0 = V.signflip(rng.normal(0, 1, 20), rng)
    assert sf0["band_lo"] < sf0["mean"] < sf0["band_hi"] or sf0["p"] < 0.05


def test_h36_is_row_zero_only():
    assert V._is_h36("patch moved 1/3 sequences; ... (deltas [0.375, 0.0, 0.0])")
    assert not V._is_h36("patch moved 1/3 sequences; ... (deltas [0.0, 0.0, 0.375])")
    assert not V._is_h36("patch moved 5/6 sequences; ... (deltas [-0.375, 0.25, 0.0, -1.0, -1.1, -1.3])")
    assert not V._is_h36("patch moved 0/1 sequences; ... (deltas [0.0])")
