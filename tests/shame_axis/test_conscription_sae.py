"""The two things `conscription_sae.py` would be silently wrong about.

Neither test loads an SAE or an activation stack, so both run in a bare `pip install pytest numpy`
environment in milliseconds.

1. THE ROW LAYOUT. The hour-54 shards are indexed by position and carry no labels of their own
   (`conscription_pilot.extract` says so in as many words). Every number in this battery is a
   paired within-item contrast, so a row mislabelled by one arm does not produce a wrong-looking
   result -- it produces a plausible one. The layout is therefore asserted, not assumed, and the
   assertion itself is what is pinned here, including that it REJECTS the malformed layouts.

2. THE TOP-K NORMALISATION. The score is a projection onto the unit vector in the direction of the
   scenario-set difference in means, restricted to k features. If the division by `||w||` were
   dropped, every score would scale with the magnitude of the readout's weights and the `top5` and
   `full` columns would not be on comparable scales. The property that pins it is that the score is
   invariant to rescaling `d` and linear in `f`.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))
sys.path.insert(0, str(ROOT / "src"))

C = pytest.importorskip("conscription_sae")


# ------------------------------------------------------------------ 1. the row -> (item, arm) map
def test_expected_order_reproduces_the_hour54_write_order_and_the_check_rejects_damage():
    """Synthetic layout: three items, the five design arms then `enact_norecord` per item, and
    every item's `neutral_b` APPENDED after all of them -- which is the order
    `conscription_pilot.render_all` wrote and the only reason the cached shards stayed valid when
    that arm was added."""
    ids = ["x01", "x02", "x03"]
    order = C.expected_order(ids)

    assert len(order) == len(ids) * 7
    # per item: the five design arms in order, then enact_norecord
    for n, i in enumerate(ids):
        assert order[n * 6: n * 6 + 6] == [(i, a) for a in (*C.ARMS5, C.EXTRA)]
    # then neutral_b for every item, appended last and in item order
    assert order[len(ids) * 6:] == [(i, C.NB) for i in ids]

    C.check_layout(order, n_rows=len(order), n_items=len(ids))

    # ...and the check has to REFUSE each way the layout can be wrong, or it is decoration.
    with pytest.raises(SystemExit):                      # activations and labels disagree
        C.check_layout(order, n_rows=len(order) - 1, n_items=len(ids))
    with pytest.raises(SystemExit):                      # a row dropped
        C.check_layout(order[:-1], n_rows=len(order) - 1, n_items=len(ids))
    with pytest.raises(SystemExit):                      # an item missing an arm, another doubled
        bad = list(order)
        bad[3] = (ids[0], C.ARMS5[0])
        C.check_layout(bad, n_rows=len(bad), n_items=len(ids))
    with pytest.raises(SystemExit):                      # an arm that is not in the design
        bad = list(order)
        bad[3] = (ids[0], "not_an_arm")
        C.check_layout(bad, n_rows=len(bad), n_items=len(ids))
    with pytest.raises(SystemExit):                      # the wrong number of items
        C.check_layout(order, n_rows=len(order), n_items=len(ids) + 1)


def test_derived_order_matches_the_order_the_extraction_recorded():
    """The grid file and the extraction's own `extract_meta.json` are two independent records of
    the same ordering; this is the real-data version of the test above and it is what
    `load_conscription` asserts before it labels a single row. Skipped where the pilot's meta file
    is not on disk (the stacks are gitignored)."""
    meta = C.PILOT / "extract_meta.json"
    if not (meta.exists() and C.GRID.exists()):
        pytest.skip("hour-54 pilot metadata not on disk")
    ids = [it["id"] for it in json.loads(C.GRID.read_text())["items"]]
    recorded = [(i, a) for i, a in json.loads(meta.read_text())["order"]]
    assert C.expected_order(ids) == recorded
    C.check_layout(recorded, n_rows=len(recorded))


# ------------------------------------------------------------------ 2. the top-k score
def test_topk_score_is_a_projection_onto_the_unit_weight_vector():
    rng = np.random.default_rng(7)
    d = np.array([0.0, -4.0, 1.0, 3.0, -0.5])
    f = rng.normal(size=(6, d.size))

    idx = C.rank_features(d, 2)
    assert sorted(idx.tolist()) == [1, 3], "top-k must rank by |d|, not by d"

    s = C.topk_score(f, d, idx)
    w = d[idx]
    assert np.allclose(s, f[:, idx] @ (w / np.linalg.norm(w)))
    # only the selected features contribute: zeroing the rest changes nothing
    g = f.copy()
    g[:, [0, 2, 4]] = 99.0
    assert np.allclose(C.topk_score(g, d, idx), s)

    # invariant to the SCALE of d (this is what the division by ||w|| buys) ...
    for c in (0.001, 5.0, 1000.0):
        assert np.allclose(C.topk_score(f, c * d, C.rank_features(c * d, 2)), s)
    # ... and linear in f
    assert np.allclose(C.topk_score(3.0 * f, d, idx), 3.0 * s)

    # a row equal to d itself scores exactly ||w||: the readout's own length, not something larger
    assert np.allclose(C.topk_score(d[None, :], d, idx), np.linalg.norm(w))

    # k beyond the dictionary is clamped, and the full-dictionary score is the same projection
    assert C.rank_features(d, 500).size == d.size
    assert np.allclose(C.topk_score(f, d, np.arange(d.size)), f @ (d / np.linalg.norm(d)))

    # all-zero weights must return zeros, not NaN -- a dead readout reads 0, it does not poison
    # every downstream contrast with NaN
    z = np.zeros_like(d)
    assert np.allclose(C.topk_score(f, z, np.arange(z.size)), 0.0)
