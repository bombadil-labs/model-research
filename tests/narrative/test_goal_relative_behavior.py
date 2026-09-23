"""The behavioral readout requires a world-dependent choice, not a name bias."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys


SCRIPTS = Path(__file__).resolve().parents[2] / "scripts/narrative"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("goal_relative_behavior_test_target",
                                               SCRIPTS / "goal_relative_behavior.py")
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def _raw(switch: bool) -> dict:
    domains = []
    for di in range(12):
        rows, no_cue = [], []
        for fmt in range(4):
            for world in (0, 1):
                margin = (1 - 2 * world) * 2 if switch else 1
                rows.append({"format": fmt, "world": world,
                             "a_logp": margin, "b_logp": 0})
                no_cue.append({"format": fmt, "world": world,
                               "a_logp": 1, "b_logp": 0})
        domains.append({"domain": str(di), "rows": rows, "no_cue": no_cue})
    return {"domains": domains,
            "sensitivity": [{"good_logp": 1, "bad_logp": 0}] * 2}


def test_grid_builds_identical_no_cue_world_pairs():
    prompts, digest = module.make_prompts()
    assert len(prompts) == 96 and len(digest) == 64
    for di in range(12):
        for fmt in range(4):
            a, b = prompts[di * 8 + fmt * 2:di * 8 + fmt * 2 + 2]
            assert a.no_cue_text == b.no_cue_text
            assert a.text != b.text


def test_world_switch_passes_but_constant_name_preference_fails():
    positive = module.score(_raw(True), n_perm=1000)
    assert positive["cell_accuracy"] == 1
    assert positive["world_switch_fraction"] == 1
    assert positive["both_worlds_correct_fraction"] == 1
    assert positive["no_cue_world_switch_fraction"] == .5
    assert positive["gate_pass"]

    biased = module.score(_raw(False), n_perm=10)
    assert biased["cell_accuracy"] == .5
    assert biased["world_switch_fraction"] == .5
    assert not biased["gate_pass"]
