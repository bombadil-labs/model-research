"""Offline checks on the hour-58 reference-distribution script.

Neither test loads an SAE or an activation stack. What they pin is the pair of places where this
script can be silently wrong: the shard-row -> scenario mapping (labels attached to the wrong
sentences produce a perfectly well-formed AUC that means nothing), and k90, which is the whole
statistic and has a declared undefined case.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))

R = pytest.importorskip("painaxis_sparsity_reference")


# ------------------------------------------------------- (a) the shard-row -> scenario mapping
def _synthetic(n):
    return [{"id": f"s{i:03d}", "category": "c" + str(i % 3), "text": "x" * i} for i in range(n)]


def test_mapping_follows_the_order_file_and_not_the_json_order():
    """The order file is the extractor's own record of what it fed the model, row by row. If the
    json order were assumed instead, every label would be attached to a different sentence."""
    scen = _synthetic(R.N_SCENARIOS)
    order = [c["id"] for c in reversed(scen)]
    aligned = R.align_scenarios(order, scen, R.N_SCENARIOS)
    assert [c["id"] for c in aligned] == order
    assert aligned[0] is scen[-1]


def test_mapping_rejects_a_row_count_that_is_not_420():
    scen = _synthetic(R.N_SCENARIOS)
    order = [c["id"] for c in scen]
    with pytest.raises(SystemExit):                     # order file shorter than the shards
        R.align_scenarios(order[:-1], scen, R.N_SCENARIOS)
    with pytest.raises(SystemExit):                     # shards short of the pre-registered pool
        R.align_scenarios(order[:419], scen[:419], 419)


def test_mapping_rejects_an_id_with_no_scenario_and_duplicate_ids():
    scen = _synthetic(R.N_SCENARIOS)
    order = [c["id"] for c in scen]
    with pytest.raises(SystemExit):
        R.align_scenarios(["ghost"] + order[1:], scen, R.N_SCENARIOS)
    dupes = scen[:-1] + [dict(scen[0])]
    with pytest.raises(SystemExit):
        R.align_scenarios(order, dupes, R.N_SCENARIOS)


# ------------------------------------------------------------------------------ (b) k90
def test_k90_is_the_smallest_grid_k_reaching_90_percent_retention():
    # full = 0.90, so 0.90 retention needs auc_k >= 0.5 + 0.9 * 0.40 = 0.86
    curve = {1: 0.60, 10: 0.80, 100: 0.87, 1000: 0.89, 16384: 0.90}
    assert R.k90(curve, 0.90) == (100, False)
    assert R.k90({1: 0.60, 10: 0.88, 100: 0.89, 16384: 0.90}, 0.90) == (10, False)


def test_k90_reads_the_grid_in_ascending_k_whatever_order_the_dict_is_in():
    curve = {16384: 0.90, 100: 0.87, 1: 0.60, 1000: 0.89, 10: 0.80}
    assert R.k90(curve, 0.90) == (100, False)


def test_k90_on_an_exact_boundary_falls_to_the_next_k():
    """auc_k = 0.86 against full 0.90 is retention 0.9 in decimal and 0.8999999999999999 in
    binary floating point, so the comparison is False. Pinned rather than patched with an
    epsilon: the threshold is the pre-registered one and is not moved to make a test pass. No
    observed AUC lands on the boundary exactly."""
    assert R.k90({1: 0.60, 100: 0.86, 1000: 0.89, 16384: 0.90}, 0.90) == (1000, False)


def test_k90_falls_back_to_the_full_dictionary_when_nothing_earlier_reaches_it():
    curve = {1: 0.55, 10: 0.60, 16384: 0.80}
    assert R.k90(curve, 0.80) == (16384, False)


def test_k90_is_null_and_flagged_weak_for_a_contrast_at_or_below_the_declared_auc():
    """Pre-registered: a contrast weaker than AUC 0.65 has no well-defined k90 -- the retention
    denominator is a difference of two small numbers and the ratio is noise."""
    assert R.k90({1: 0.55, 16384: 0.64}, 0.64) == (None, True)
    assert R.k90({1: 0.50, 16384: R.WEAK_AUC}, R.WEAK_AUC) == (None, True)   # the boundary is weak
    assert R.k90({1: 0.50, 16384: 0.6501}, 0.6501)[1] is False
    assert R.k90({1: 0.50, 16384: float("nan")}, float("nan")) == (None, True)


def test_k90_of_a_one_feature_contrast_is_1():
    """The shape gate B demands: a contrast carried by a single feature must read k90 = 1."""
    assert R.k90({1: 1.0, 10: 1.0, 16384: 1.0}, 1.0) == (1, False)
