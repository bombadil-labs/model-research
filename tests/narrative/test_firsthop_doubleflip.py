"""Distinguish slot cancellation from a persistent person/world effect."""
from __future__ import annotations

import json
from pathlib import Path
import sys

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/narrative"))

import firsthop_doubleflip as double
import firsthop_swap_grid as grid


def _fixture():
    cells, _, _ = grid.make_cells()
    by = double._by_factors(cells)
    doc = json.loads((grid.ROOT / "research/narrative/prompts/goal_route_cross_v1.json").read_text())
    domains = {r["id"]: r for r in doc["domains"]}
    located = {c.id: {"prompt_length": 100, "prebridge_index": 80,
                      "prebridge_token_id": 1} for c in cells}
    return cells, by, domains, located


def test_double_flip_preserves_slot_but_changes_person():
    cells, by, domains, located = _fixture()
    for c in cells:
        world, plan, both = double._sources(c, by)
        sign = double._validate_pair(c, world, plan, both, domains[c.domain], located)
        assert sign == (1 if (1-c.world) == c.goal else -1)
        assert grid._winner(c, domains[c.domain]) != grid._winner(both, domains[c.domain])
        assert double._first_wins(c, domains[c.domain]) == double._first_wins(both, domains[c.domain])
    c = cells[0]
    world, plan, both = double._sources(c, by)
    located[both.id]["prebridge_index"] += 1
    with pytest.raises(ValueError, match="token signature"):
        double._validate_pair(c, world, plan, both, domains[c.domain], located)


def _synthetic(double_effect: float, *, instrument_ok: bool = True) -> dict:
    cells, by, domains, located = _fixture()
    old = json.loads(double.OLD_REPORT.read_text())
    base = np.asarray(old["candidate_scores"], dtype=np.float64).reshape(128, 7, 2)[:, 0]
    effect_by_arm = {"none": 0., "zero": 0., "world_natural": .6,
                     "plan_matched": .8, "double_natural": double_effect,
                     "double_matched": double_effect, "random": 0.,
                     "last_block": 0.}
    rows, metadata = {}, {}
    for i, c in enumerate(cells):
        world, plan, both = double._sources(c, by)
        sign = double._validate_pair(c, world, plan, both, domains[c.domain], located)
        metadata[c.id] = {"source_sign": sign}
        a = c.candidates.index(c.plan_a_name)
        for arm, value in effect_by_arm.items():
            scores = base[i].copy()
            scores[a] += sign * value
            row = {"scores": scores.tolist(), "flagged": False}
            if arm == "double_natural":
                row["source_state_relative_error"] = 0.
            if arm in ("double_natural", "double_matched"):
                row["period_residual_error"] = 0.
            rows[f"{c.id}|{arm}"] = row
    domains_zero = {c.domain: 0. for c in cells}
    preflight = {"row_zero_only_refused": True, "block24_residual_error": 0.}
    core = {"shortest": 0. if instrument_ok else .1, "longest": 0.,
            "all_prompt_baseline_drift": 0.}
    return double._analysis(cells, rows, metadata, old, domains_zero,
                            preflight, core, {}, {})


def test_cancellation_requires_equivalence_and_both_paired_contrasts():
    cancelled = _synthetic(0.)
    assert cancelled["verdict"] == "slot_cancellation_screen_pass"
    assert all(cancelled["slot_cancellation_gate"].values())
    assert cancelled["paired_contrasts"]["world_minus_double"]["mean"] == pytest.approx(.6)
    assert cancelled["paired_contrasts"]["plan_minus_double"]["mean"] == pytest.approx(.8)
    assert cancelled["arm_reports"]["double_matched"]["domain_bootstrap"]["ci95"] == [0., 0.]

    persistent = _synthetic(.5)
    assert persistent["verdict"] == "cancellation_fails_positive_double"
    assert not persistent["slot_cancellation_gate"]["matched_equivalence"]
    assert all(persistent["positive_double_gate"].values())

    reversed_effect = _synthetic(-.5)
    assert reversed_effect["verdict"] == "cancellation_fails_negative_double"

    unreadable = _synthetic(0., instrument_ok=False)
    assert unreadable["verdict"] == "unreadable_instrument"
    assert not unreadable["slot_cancellation_gate"]["instrument_ok"]
