"""Check that the causal gates separate directional edits from compression."""
from __future__ import annotations

import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts/narrative"))

import firsthop_swap_grid as grid
import firsthop_swap_patch as patch


def _rows(cells, *, compression: bool):
    rows = {}
    for i, cell in enumerate(cells):
        target_sign = 1 if cell.world == cell.goal else -1
        source_sign = -target_sign
        baseline = (source_sign * .5 if i % 8 == 0 else target_sign * 2)
        full = (baseline * .5 if compression else source_sign * 2)
        for arm in patch.ARMS:
            margin = full if arm == "full" else (
                baseline * .5 if compression and arm == "plan_matched" else baseline)
            a = cell.candidates.index(cell.plan_a_name)
            scores = [0.0, 0.0]
            scores[a], scores[1 - a] = margin / 2, -margin / 2
            row = {"scores": scores, "flagged": False}
            if arm == "full":
                row["source_state_relative_error"] = 0.0
            rows[f"{cell.id}|{arm}"] = row
    return rows


def _report(compression: bool):
    cells, _, _ = grid.make_cells()
    doc = json.loads((grid.ROOT / "research/narrative/prompts/goal_route_cross_v1.json").read_text())
    return patch.analyze(cells, _rows(cells, compression=compression), doc,
                         {"row_zero_only_refused": True}, {"shortest": 0.0},
                         {c.domain: 0.0 for c in cells}, {}, {}, {})


def test_directional_swap_passes_both_causal_screens():
    report = _report(compression=False)
    assert report["specific_margin_screen"]
    assert report["choice_redirection_screen"]
    assert report["choice_flips"]["toward_source"] >= 8
    assert report["choice_flips"]["effect_when_source_already_favoured"] > 0


def test_shared_compression_fails_specificity_and_choice():
    report = _report(compression=True)
    assert report["primary_full_effect"]["mean"] > 0
    assert not report["gate_components"]["twice_max_control"]
    assert not report["specific_margin_screen"]
    assert not report["choice_redirection_screen"]
