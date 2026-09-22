"""Sanity gates for the held-out-tale classifier and signal alignment."""
from __future__ import annotations

import importlib.util
from pathlib import Path
import sys

import numpy as np
import pytest


SCRIPT = Path(__file__).resolve().parents[2] / "scripts/narrative/propp_spike.py"
spec = importlib.util.spec_from_file_location("propp_spike_test_target", SCRIPT)
module = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = module
spec.loader.exec_module(module)


def test_signal_character_selects_one_real_token():
    offsets = [(0, 0), (0, 4), (5, 11)]
    assert module.token_for_signal(offsets, 11) == 2
    with pytest.raises(ValueError, match="maps to 0 tokens"):
        module.token_for_signal(offsets, 5)


def test_story_held_out_classifier_detects_signal_above_floors():
    # Identical text and position for every event make both baselines exactly chance.
    # A class signal shared by all 15 tales must transfer to every held-out tale.
    # One tale has only one annotation, so bootstrap resamples vary in event count.
    events = [module.Event(t, label, 10, 0.5, "ordinary words nearby")
              for t in range(15) for label in (module.LABELS if t else ("A",))]
    acts = np.zeros((len(events), 29, 8), dtype=np.float32)
    for i, event in enumerate(events):
        acts[i, 1:, module.LABELS.index(event.label)] = 1
    result = module.score(acts, events, n_perm=10, n_boot=20)
    assert result["primary_mid_balanced_accuracy"] == 1.0
    assert result["controls_balanced_accuracy"] == {
        "text": .2, "position": .2, "combined": .2, "layer_0": .2,
    }
    assert result["primary_gain_over_strongest_baseline"] == .8


def test_missing_training_class_refuses_scoring():
    events = [module.Event(t, label, 10, .5, "ordinary words nearby")
              for t in range(15) for label in (module.LABELS if t == 0 else ("A", "H", "I", "K"))]
    acts = np.ones((len(events), 29, 8), dtype=np.float32)
    with pytest.raises(ValueError, match="training fold lacks classes"):
        module.score(acts, events, n_perm=1, n_boot=1)
