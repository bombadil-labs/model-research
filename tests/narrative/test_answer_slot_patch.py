"""The causal score contrasts must subtract direct residual pass-through."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location(
    "answer_slot_patch_test_target", SCRIPTS / "answer_slot_patch.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _synthetic(cells, *, direct_only: bool):
    saved, previous = {}, {}
    for c in cells:
        base_margin = 2 if c.goal == 0 else -2
        first_sign = 1 if c.plan_order == 0 else -1
        previous[c.id] = {"scores": [
            (base_margin / 2 if name == c.plan_a_name else -base_margin / 2)
            for name in c.candidates]}
        for arm in module.ARMS:
            offset = 0.0
            if arm == "u_plus_24":
                offset = .5
            elif arm == "u_minus_24":
                offset = -.5
            elif arm == "u_plus_41":
                offset = .5 if direct_only else .1
            elif arm == "u_minus_41":
                offset = -.5 if direct_only else -.1
            elif arm in ("r1_plus_24", "r2_plus_24"):
                offset = .03
            elif arm in ("r1_minus_24", "r2_minus_24"):
                offset = -.03
            margin = base_margin + first_sign * offset
            scores = {c.plan_a_name: margin / 2,
                      c.plan_b_name: -margin / 2}
            saved[f"{c.id}|{arm}"] = {
                "scores": [scores[name] for name in c.candidates],
                "flagged": False}
    reach = {"moved_residual_rows": {arm: 2 for arm in module.ARMS[2:]}}
    return saved, previous, reach


def test_target_balance_and_pass_through_subtraction():
    all_cells, _, _ = module.replication.make_cells()
    cells = module.selected_cells(all_cells)
    assert len(cells) == 64
    assert sum(c.plan_order == c.goal for c in cells) == 32
    saved, previous, reach = _synthetic(cells, direct_only=False)
    report = module.analyze(cells, saved, previous, {}, reach)
    assert report["secondary_total_block24_effect"]["mean"] == .5
    assert report["secondary_direct_block41_effect"]["mean"] > .09
    assert abs(report["primary_net_effect"]["mean"] - .4) < 1e-12
    assert report["primary_net_effect"]["exact_domain_sign_null"][
        "p_ge_observed"] == 1 / 256
    assert report["positive_screen"]


def test_direct_only_bias_cannot_pass_primary():
    cells = module.selected_cells(module.replication.make_cells()[0])
    saved, previous, reach = _synthetic(cells, direct_only=True)
    report = module.analyze(cells, saved, previous, {}, reach)
    assert report["secondary_total_block24_effect"]["mean"] == .5
    assert report["secondary_direct_block41_effect"]["mean"] == .5
    assert report["primary_net_effect"]["mean"] == 0
    assert not report["positive_screen"]
