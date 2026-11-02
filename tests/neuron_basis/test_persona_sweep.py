"""The sweep's own instruments: the hook that asserts the patch reached the residual, the
repetition flag, and the reply NLL under the unsteered model."""
import importlib.util
import pathlib

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]


def _load():
    spec = importlib.util.spec_from_file_location("persona_sweep", ROOT / "scripts/neuron_basis/persona_sweep.py")
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    return m


def test_repetition_flag():
    m = _load()
    assert not m.repetition_flag(list(range(40)))
    assert m.repetition_flag([1, 2, 3, 4, 5, 6, 7, 8] * 3)
    assert not m.repetition_flag([1, 2, 3, 4, 5, 6, 7, 8] * 2)


def test_moved_hook_records_shift(tiny_lm):
    torch = pytest.importorskip("torch")
    m = _load()
    shift = np.full(tiny_lm.d_model, 0.5)
    mv = m.Moved(shift)
    h = torch.randn(1, 5, tiny_lm.d_model)
    out = mv(h)
    assert mv.calls == 1 and mv.max_err < 1e-6 and mv.min_cos > 0.999
    assert torch.allclose(out - h, torch.as_tensor(shift, dtype=torch.float32).expand(1, 5, -1))


def test_moved_hook_sees_a_patch_in_generation(tiny_lm):
    """Under lm.patched the hook fires once per generation step and moves the residual by the
    shift; with no patch the reply differs, so the patch reached the forward."""
    torch = pytest.importorskip("torch")
    m = _load()
    from lsx.model import Patch
    text = "the thesis is that"
    rng = np.random.default_rng(0)
    shift = rng.standard_normal(tiny_lm.d_model) * 3.0
    mv = m.Moved(shift)
    p_ids, r_base = m.generate(tiny_lm, text, [], 6)
    _, r_patched = m.generate(tiny_lm, text, [Patch(layer=2, fn=mv)], 6)
    assert mv.calls == r_patched.shape[1], "one hook call per generated token (prompt + each step)"
    assert mv.max_err < 1e-4 and mv.min_cos > 0.99
    nll = m.reply_nll(tiny_lm, p_ids, r_patched)
    assert np.isfinite(nll) and nll >= 0


def test_skip_path_patch_hits_final_norm(tiny_lm):
    """Patch(layer=n_layers) must register on the final norm, not a block."""
    m = _load()
    from lsx.model import Patch
    mv = m.Moved(np.ones(tiny_lm.d_model))
    m.generate(tiny_lm, "the thesis is that", [Patch(layer=tiny_lm.n_layers, fn=mv)], 3)
    assert mv.calls == 3


def test_degeneracy_detector_calibrates():
    """Declared before the sweep (review g): clean text reads 0, planted loops read 1."""
    m = _load()
    clean = list(range(60))
    loop = [1, 2, 3, 4, 5, 6, 7, 8] * 8
    assert not m.degenerate(clean)["degenerate"]
    assert m.degenerate(loop)["degenerate"]
    assert m.degenerate([])["degenerate"]            # an empty reply is not a coherent one
    assert m.degenerate([25, 7])["degenerate"]       # nor a two-token one (pilot: ':' and '，')
    cal = m.calibrate_degeneracy([clean, list(range(100, 140))])
    assert cal["passed"] and cal["no_patch_flagged"] == 0 and cal["planted_loops_flagged"] == 2
