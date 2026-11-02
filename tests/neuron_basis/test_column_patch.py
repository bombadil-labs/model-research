"""The claim in research/neuron-basis/notes/operation.md that the library recipe (add
c * W_down[:, n] to the residual after block L) and the Granite recipe (pre-hook on down_proj
adding c * e_n) are ONE operation, asserted on the tiny model rather than stated."""
import numpy as np
import pytest

from lsx.neuron_basis import (dose_scale, down_proj, matched_dense_direction, median_residual_norm,
                              write_direction)


def test_write_direction_is_a_column(tiny_lm):
    blk = tiny_lm.blocks[1]
    w = down_proj(blk).weight
    col = write_direction(blk, 3)
    assert col.shape == (tiny_lm.d_model,)
    np.testing.assert_allclose(col, w[:, 3].detach().double().numpy())
    with pytest.raises(IndexError):
        write_direction(blk, w.shape[1])


def test_dose_scale_adds_one_residual_norm():
    col = np.array([3.0, 4.0])             # norm 5
    assert dose_scale(10.0, col, 1.0) == pytest.approx(2.0)
    assert dose_scale(10.0, col, 0.5, -1) == pytest.approx(-1.0)
    assert np.linalg.norm(dose_scale(10.0, col, 1.0) * col) == pytest.approx(10.0)


def test_median_norm_excludes_first_token():
    r = np.zeros((4, 2)); r[0] = [100.0, 0]; r[1:] = [[3, 4], [3, 4], [6, 8]]
    assert median_residual_norm(r) == pytest.approx(5.0)


def test_dense_arm_matches_norm():
    rng = np.random.default_rng(0)
    shift = np.array([1.0, 2.0, 2.0])
    d = matched_dense_direction(shift, rng)
    assert np.linalg.norm(d) == pytest.approx(3.0)


def test_library_form_equals_granite_form(tiny_lm):
    """Granite: pre-hook on block L's down_proj adding c*e_n. Library: add c*W_down[:, n] to the
    residual entering block L+1. Same residual, to float tolerance."""
    torch = pytest.importorskip("torch")
    L, n, c = 1, 5, 7.5
    blk = tiny_lm.blocks[L]
    enc = tiny_lm.tok(["the thesis is that a particle"], return_tensors="pt")
    col = torch.as_tensor(write_direction(blk, n), dtype=torch.float32)

    def capture(store):
        def hook(_m, _i, out):
            store.append((out[0] if isinstance(out, tuple) else out).detach().clone())
        return hook

    base, granite, library = [], [], []
    h = blk.register_forward_hook(capture(base))
    tiny_lm.model(**enc); h.remove()

    def pre(_m, args):
        x = args[0].clone(); x[..., n] += c; return (x,)
    h1 = down_proj(blk).register_forward_pre_hook(pre)
    h2 = blk.register_forward_hook(capture(granite))
    tiny_lm.model(**enc); h1.remove(); h2.remove()

    library.append(base[0] + c * col)
    assert torch.allclose(granite[0], library[0], atol=1e-5), \
        "a down_proj pre-hook of c*e_n is not the same as adding c*W_down[:, n] after the block"
    assert not torch.allclose(granite[0], base[0]), "the patch reached nothing"
