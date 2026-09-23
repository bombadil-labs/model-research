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
    assert len(rows) == 8 and len(clozes) == 6 and len(digest) == 64
    for i in range(0, 8, 2):
        a, b = rows[i:i + 2]
        assert a["id"] == b["id"]
        assert a["good"] == b["bad"] and a["bad"] == b["good"]


def test_selector_refuses_single_name_order_and_takes_first_eligible():
    def result(index, margins):
        return {"index": index, "cloze": str(index),
                "rows": [{"good_logp": x, "bad_logp": 0} for x in margins]}

    scores, chosen = module.select([
        result(0, [.9, -.01] * 4),
        result(1, [.2] * 8),
        result(2, [.8] * 8),
    ], 3)
    assert not scores[0]["eligible"] and scores[0]["correct_of_8"] == 4
    assert chosen == 1
