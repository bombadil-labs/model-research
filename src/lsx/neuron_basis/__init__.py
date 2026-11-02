"""Neuron-basis line: the arithmetic of pushing one down-projection column.

Every "steer one MLP neuron" recipe this line replicates is `h_L += c * W_down[:, n]` after
block L (`research/neuron-basis/notes/operation.md`). This module holds the column lookup and the
dose formula and nothing else: the patch itself is `lsx.model.Patch` with `lsx.steer.add_vector`,
because a column add IS a direction add and gets the same arms.

Imports only the core. Never imports from another line.
"""
from __future__ import annotations

import numpy as np
import torch
from torch import nn


def down_proj(block: nn.Module) -> nn.Linear:
    """The MLP's output projection of a decoder block, across the architectures this repo runs
    (Qwen2/3, Llama, Gemma name it `mlp.down_proj`; GPT-2 style `mlp.c_proj`; NeoX
    `mlp.dense_4h_to_h`). Raises rather than guessing."""
    for path in ("mlp.down_proj", "mlp.c_proj", "mlp.dense_4h_to_h"):
        obj = block
        try:
            for attr in path.split("."):
                obj = getattr(obj, attr)
        except AttributeError:
            continue
        if isinstance(obj, nn.Linear):
            return obj
    raise ValueError(f"no MLP output projection found on {type(block).__name__}")


def write_direction(block: nn.Module, n: int) -> np.ndarray:
    """Neuron n's write direction: column n of W_down, shape [d_model], float64 numpy.

    HF `nn.Linear.weight` is [out_features, in_features] = [d_model, d_mlp], so the column is
    `weight[:, n]`. The READ direction (a row of up/gate) is a different vector and is not what
    any steering recipe touches."""
    w = down_proj(block).weight
    if not 0 <= n < w.shape[1]:
        raise IndexError(f"neuron {n} out of range for d_mlp={w.shape[1]}")
    return w[:, n].detach().to(torch.float64).cpu().numpy()


def median_residual_norm(resid: np.ndarray) -> float:
    """r_L: median L2 norm over a prompt's tokens EXCLUDING the first, whose norm is an outlier
    on every model this repo has measured. `resid` is [seq, d] for one prompt."""
    resid = np.asarray(resid, dtype=np.float64)
    if resid.ndim != 2 or resid.shape[0] < 2:
        raise ValueError("need [seq, d] with at least two tokens to exclude the first")
    return float(np.median(np.linalg.norm(resid[1:], axis=1)))


def dose_scale(r_l: float, column: np.ndarray, alpha: float, sign: int = +1) -> float:
    """c = sign * alpha * r_L / ||column||, so that alpha = 1 adds one typical residual vector."""
    if sign not in (+1, -1):
        raise ValueError("sign must be +1 or -1")
    norm = float(np.linalg.norm(column))
    if norm == 0.0:
        raise ValueError("zero column")
    return sign * alpha * r_l / norm


def matched_dense_direction(column_shift: np.ndarray, rng: np.random.Generator) -> np.ndarray:
    """The random-dense arm: a Gaussian direction with the SAME norm as the column shift
    `c * W_down[:, n]`, so the two arms differ in sparsity and nothing else."""
    v = rng.standard_normal(column_shift.shape[0])
    return v * (np.linalg.norm(column_shift) / np.linalg.norm(v))
