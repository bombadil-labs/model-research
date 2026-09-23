"""Cloze selection uses only prewritten controls and requires both name orders."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("elicitor_calibration_test_target",
                                               SCRIPTS / "elicitor_calibration.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_control_grid_swaps_names_without_changing_plans():
    rows, clozes, digest = module.make_controls()
    assert len(rows) == 16 and len(clozes) == 6 and len(digest) == 64
    for i in range(0, 16, 4):
        a, b, c, d = rows[i:i + 4]
        assert len({r["id"] for r in (a, b, c, d)}) == 1
        assert a["good"] == b["good"] == c["bad"] == d["bad"]
        assert a["bad"] == b["bad"] == c["good"] == d["good"]
        assert a["plan_order"] == c["plan_order"] == 0
        assert b["plan_order"] == d["plan_order"] == 1
        assert a["story"] != b["story"]


def test_selector_refuses_single_name_or_plan_order_and_takes_first_eligible():
    def result(index, margins):
        return {"index": index, "cloze": str(index),
                "rows": [{"good_logp": x, "bad_logp": 0} for x in margins]}

    scores, chosen = module.select([
        result(0, [.9, -.01] * 8),
        result(1, [.9] * 8 + [-.01] * 8),
        result(2, [.2] * 16),
        result(3, [.8] * 16),
    ], 4)
    assert not scores[0]["eligible"] and scores[0]["correct_of_16"] == 8
    assert scores[0]["position_effect"] > 0
    assert not scores[1]["eligible"] and scores[1]["correct_of_16"] == 8
    assert chosen == 2
