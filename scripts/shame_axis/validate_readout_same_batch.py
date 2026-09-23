"""Same-batch validation of the fixed opener readout (INSTRUMENTS §7), raised in review.

`validate_readout.py` compared the scorer (one padded batch) with `model.output.logits` from a
separate unbatched job, and batch composition alone moves bf16 scores by ~0.1, so its 0.05 gate
could not isolate the softcap fix. Here everything is read inside ONE trace on the scorer's own
ids, mask, candidate mask and column slice:

  fixed  = log_softmax(tanh(lm_head.output / cap) * cap), fp32   -- the fixed scorer's formula
  old    = log_softmax(lm_head.output) in bf16                  -- the pre-fix formula
  model  = log_softmax(model.output.logits), fp32               -- what the model samples from

and the scorer itself is run on the same batch and must reproduce `fixed`.

Gate, declared before running: the model's softcapped logits are bf16, stored in steps of 0.125
at |logit| 16-30, so per candidate |fixed - model| <= 0.125 x (candidate tokens). The fix is
confirmed if that holds for every candidate AND the median |old - model| is at least 3x the
median |fixed - model|. The scorer must match `fixed` to 1e-3.

Usage:  python scripts/shame_axis/validate_readout_same_batch.py   # .venv312, NDIF
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts/shame_axis"))
from lsx.shame_axis import stimuli  # noqa: E402

OUT = ROOT / "research/shame-axis/results/readout_fix/validation_same_batch.json"
ITEMS = ("gaslight_01", "neutral_01", "critique_01")   # one per tier A / N / B; the first draft guessed ids
STEP = 0.125


def _batch(rlm, lead, candidates):
    """The scorer's own encoding, lead mask and column slice, reproduced line for line."""
    from lsx.core.remote import strip_template_bos, _encode, _add_special, assert_single_bos
    lead = strip_template_bos(rlm.tok, lead)
    texts = [f"{lead}{c}" for c in candidates]
    ids, mask = _encode(rlm, texts)
    assert_single_bos(ids, mask, rlm.tok.bos_token_id)
    n_lead = len(rlm.tok(lead, add_special_tokens=_add_special(rlm, [lead]))["input_ids"])
    tgt = ids[:, 1:]
    score_mask = mask[:, 1:].clone().float()
    n_real = mask.sum(dim=1)
    for r in range(len(texts)):
        pad = int(mask.shape[1] - n_real[r]) if rlm.padding_side == "left" else 0
        score_mask[r, : pad + n_lead - 1] = 0.0
    first = int((score_mask.sum(0) > 0).nonzero().min())
    return ids, mask, tgt[:, first:], score_mask[:, first:], first


def main() -> None:
    import torch
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob, _run_saved
    from painaxis_scenarios import render_chat
    from conscription_openers import OPENERS

    rlm = RemoteLM("google/gemma-2-9b-it")
    cap = float(rlm.model.config.final_logit_softcapping)
    lm_head, mdl = rlm.model.lm_head, rlm.model
    items = {it["id"]: it for it in stimuli.load("v0")}
    sets = {"single": ["You", "I", "That", "Sure", "As"], "openers": list(OPENERS)}
    rows = []
    for iid in ITEMS:
        text = render_chat(items[iid], rlm.tok)
        for name, cands in sets.items():
            ids, mask, tgt, smask, first = _batch(rlm, text, cands)

            def build(backend):
                with mdl.trace({"input_ids": ids, "attention_mask": mask}, backend=backend) as tracer:
                    raw = lm_head.output[:, first:-1, :]
                    fx = torch.tanh(raw.float() / cap) * cap
                    fixed = ((fx.gather(-1, tgt.unsqueeze(-1).to(fx.device)).squeeze(-1)
                              - torch.logsumexp(fx, dim=-1)) * smask.to(fx.device)).sum(-1).save()
                    old = ((raw.gather(-1, tgt.unsqueeze(-1).to(raw.device)).squeeze(-1).float()
                            - torch.logsumexp(raw, dim=-1).float()) * smask.to(raw.device)).sum(-1).save()
                    ml = mdl.output.logits[:, first:-1, :].float()
                    model = ((ml.gather(-1, tgt.unsqueeze(-1).to(ml.device)).squeeze(-1)
                              - torch.logsumexp(ml, dim=-1)) * smask.to(ml.device)).sum(-1).save()
                return tracer
            got = _run_saved(rlm, build)
            fixed, old, model = (np.asarray(got[k], dtype=np.float64).ravel() for k in ("fixed", "old", "model"))
            scorer = asserted_remote_patched_logprob(rlm, text, cands)
            ntok = smask.sum(-1).numpy()
            row = {"item": iid, "set": name, "candidates": cands, "n_tokens": ntok.tolist(),
                   "fixed": fixed.tolist(), "old": old.tolist(), "model": model.tolist(),
                   "scorer": scorer.tolist(),
                   "abs_fixed_model": np.abs(fixed - model).tolist(),
                   "abs_old_model": np.abs(old - model).tolist(),
                   "bound": (STEP * ntok).tolist(),
                   "max_abs_scorer_fixed": float(np.abs(scorer - fixed).max())}
            print(json.dumps({k: row[k] for k in ("item", "set", "abs_fixed_model", "abs_old_model",
                                                  "max_abs_scorer_fixed")}), flush=True)
            rows.append(row)
    fm = np.concatenate([r["abs_fixed_model"] for r in rows])
    om = np.concatenate([r["abs_old_model"] for r in rows])
    within = all(np.all(np.array(r["abs_fixed_model"]) <= np.array(r["bound"])) for r in rows)
    ratio = float(np.median(om) / max(np.median(fm), 1e-12))
    scorer_ok = max(r["max_abs_scorer_fixed"] for r in rows) <= 1e-3
    verdict = "PASS" if within and ratio >= 3 and scorer_ok else "FAIL"
    summ = {"rows": rows, "median_abs_fixed_model": float(np.median(fm)),
            "max_abs_fixed_model": float(fm.max()), "median_abs_old_model": float(np.median(om)),
            "old_over_fixed_median": ratio, "all_within_bf16_bound": within,
            "scorer_reproduces_fixed": scorer_ok, "verdict": verdict}
    OUT.write_text(json.dumps(summ, indent=1))
    print(f"\nfixed vs model: median {np.median(fm):.4f} max {fm.max():.4f}   old vs model: median "
          f"{np.median(om):.4f}   ratio {ratio:.1f}   within bound {within}   scorer==fixed {scorer_ok}")
    print("SAME-BATCH VALIDATION " + verdict)


if __name__ == "__main__":
    main()
