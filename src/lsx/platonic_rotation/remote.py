"""The two NDIF calls this line makes: capture keys at every layer, and generate under a key swap.

Both go through `lsx.core.remote.RemoteLM` (tokenizer padding read back, one-<bos> assertion) and
`lsx.ndif.ProxyAuthBackend`. Positions are absolute indices computed HERE from from-the-end
offsets and the padded length, under an asserted left-padding (INSTRUMENTS §4b); block outputs are
resolved by type, never by index (INSTRUMENTS §4).

A trace block's source runs on the deployment, so nothing inside one may reference an `lsx`
object: the request then fails to unpickle server-side ("No module named 'lsx'"). Only locals that
are torch tensors, python ints/lists, the nnsight model and its blocks appear inside the blocks.
"""
from __future__ import annotations

import time
from typing import Sequence

import numpy as np

from lsx.core.remote import RemoteLM, _encode


def _submit(model, build, attempts: int = 5) -> dict:
    """Build a trace, submit, poll. Retries transport errors and deployment-side failures (the NDIF
    GPU is shared; an OOM there is usually a co-tenant, so retry rather than redesign)."""
    from lsx.ndif import ProxyAuthBackend
    last = None
    for i in range(attempts):
        try:
            backend = ProxyAuthBackend(model.to_model_key())
            return backend.wait(build(backend), timeout=900.0)
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"    NDIF attempt {i + 1}/{attempts} failed: {type(e).__name__}: {str(e)[:200]}",
                  flush=True)
            time.sleep(10 * (i + 1))
    raise last


def _encode_left(rlm: RemoteLM, prompts: Sequence[str]):
    if rlm.padding_side != "left":
        raise RuntimeError(f"expected left padding, tokenizer reports {rlm.padding_side!r}")
    ids, mask = _encode(rlm, list(prompts))
    if not bool(mask[:, -1].all()):
        raise RuntimeError("a row ends in padding: the batch is not left-padded")
    return ids, mask


def _positions(mask, negs: Sequence[int]):
    """Absolute column of each row's key, from its from-the-end index. Never inside padding."""
    import torch
    S = mask.shape[1]
    pos = torch.as_tensor([S + int(n) for n in negs])
    rows = torch.arange(len(negs))
    if not bool(mask[rows, pos].all()) or bool((pos < 0).any()):
        raise RuntimeError("a key position resolves into padding")
    return rows, pos


def capture_keys(rlm: RemoteLM, prompts: Sequence[str], negs: Sequence[int]) -> np.ndarray:
    """Hidden state (output of block l) at each row's key position, every layer: [B, L, d] f16."""
    import torch
    ids, mask = _encode_left(rlm, prompts)
    rows, pos = _positions(mask, negs)
    model, blocks = rlm.model, rlm.blocks
    n_layers = len(blocks)

    def build(backend):
        with model.trace({"input_ids": ids, "attention_mask": mask}, backend=backend) as tracer:
            hs = []
            for l in range(n_layers):
                r = blocks[l].output
                h = r if isinstance(r, torch.Tensor) else r[0]      # by type, never by index
                hs.append(h[rows, pos].float())
            out = torch.stack(hs, 1).half().save()
        return tracer

    arr = _submit(model, build)["out"].numpy()
    if arr.shape[:2] != (len(prompts), n_layers) or not np.isfinite(arr).all():
        raise RuntimeError(f"bad capture: shape {arr.shape}, finite={np.isfinite(arr).all()}")
    return arr


def generate(rlm: RemoteLM, prompts: Sequence[str], *, max_new_tokens: int = 8,
             negs: Sequence[int] | None = None, layers: Sequence[int] | None = None,
             vecs: np.ndarray | None = None) -> list[str]:
    """Greedy continuations. With `vecs`, row i's hidden state at its key position is OVERWRITTEN
    by vecs[i] at the output of block layers[i]; rows with layers[i] < 0 run unpatched. The write
    happens on the prompt's forward pass, and later steps read it back through the KV cache."""
    import torch
    ids, mask = _encode_left(rlm, prompts)
    model, blocks = rlm.model, rlm.blocks
    groups = []
    if vecs is not None:
        rows, pos = _positions(mask, negs)
        lay = np.asarray(layers)
        v = torch.as_tensor(np.asarray(vecs, dtype=np.float32))
        for l in sorted(set(int(x) for x in lay if x >= 0)):       # ascending: module order
            sel = torch.as_tensor(np.flatnonzero(lay == l))
            groups.append((l, rows[sel], pos[sel], v[sel]))

    def build(backend):
        with model.generate({"input_ids": ids, "attention_mask": mask},
                            max_new_tokens=max_new_tokens, do_sample=False,
                            backend=backend) as tracer:
            for l, rws, ps, vs in groups:
                r = blocks[l].output
                h = r if isinstance(r, torch.Tensor) else r[0]
                h[rws, ps] = vs.to(h.device, h.dtype)
            gen = model.generator.output.save()
        return tracer

    gen = _submit(model, build)["gen"]
    if gen.shape[0] != len(prompts):
        raise RuntimeError(f"generation returned {gen.shape[0]} rows for {len(prompts)} prompts")
    return rlm.tok.batch_decode(gen[:, ids.shape[1]:], skip_special_tokens=True)
