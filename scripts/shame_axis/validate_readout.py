"""Validate the fixed opener readout against the model's own output distribution (INSTRUMENTS §7).

For single-token candidates, log p(c | prompt) from `asserted_remote_patched_logprob` must equal
log_softmax(model.output.logits[:, -1]) computed independently in fp32 -- the logits the model
samples from, softcap included. And the readout must no longer depend on how many candidates share
a job. Three `v0` items, one job per check.
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src")); sys.path.insert(0, str(ROOT / "scripts/shame_axis"))
from lsx.shame_axis import stimuli  # noqa: E402

OUT = ROOT / "research/shame-axis/results/readout_fix/validation.json"


def main() -> None:
    import torch
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob, strip_template_bos, _run_saved
    from painaxis_scenarios import render_chat
    from conscription_openers import OPENERS

    rlm = RemoteLM("google/gemma-2-9b-it")
    items = [it for it in stimuli.load("v0") if it["id"] in ("gaslight_01", "casual_01", "rude_01")] \
        or stimuli.load("v0")[:3]
    single = ["You", "I", "That", "Sure", "As"]
    ids1 = [rlm.tok(c, add_special_tokens=False)["input_ids"] for c in single]
    assert all(len(i) == 1 for i in ids1), f"not single tokens: {ids1}"
    tids = [i[0] for i in ids1]
    mdl = rlm.model
    out = []
    for it in items:
        text = render_chat(it, rlm.tok)
        # independent: the model's own final logits, fp32 log_softmax at the last position
        enc = rlm.tok(strip_template_bos(rlm.tok, text), return_tensors="pt", add_special_tokens=True)
        assert enc["input_ids"][0, 0].item() == rlm.tok.bos_token_id and enc["input_ids"][0, 1].item() != rlm.tok.bos_token_id

        def build(backend):
            with mdl.trace({"input_ids": enc["input_ids"], "attention_mask": enc["attention_mask"]},
                           backend=backend) as tracer:
                lg = mdl.output.logits[0, -1, :].float()
                ref = (lg - torch.logsumexp(lg, dim=-1)).save()
            return tracer
        ref = np.asarray(_run_saved(rlm, build)["ref"], dtype=np.float64)
        indep = ref[tids]
        fixed = asserted_remote_patched_logprob(rlm, text, single)
        one_by_one = np.array([asserted_remote_patched_logprob(rlm, text, [c])[0] for c in single])
        op6 = asserted_remote_patched_logprob(rlm, text, OPENERS)
        op1 = np.array([asserted_remote_patched_logprob(rlm, text, [o])[0] for o in OPENERS])
        row = {"item": it["id"], "indep": indep.tolist(), "fixed": fixed.tolist(),
               "max_abs_fixed_vs_indep": float(np.abs(fixed - indep).max()),
               "max_abs_batch5_vs_batch1": float(np.abs(fixed - one_by_one).max()),
               "max_abs_openers_batch6_vs_batch1": float(np.abs(op6 - op1).max())}
        print(json.dumps(row), flush=True)
        out.append(row)
    OUT.write_text(json.dumps(out, indent=1))
    worst = max(r["max_abs_fixed_vs_indep"] for r in out)
    worst_b = max(max(r["max_abs_batch5_vs_batch1"], r["max_abs_openers_batch6_vs_batch1"]) for r in out)
    print(f"\nfixed vs model.output.logits: max |d| {worst:.2e}   batch invariance: max |d| {worst_b:.2e}")
    print("VALIDATION " + ("PASS" if worst < 0.05 and worst_b < 0.05 else "FAIL"))


if __name__ == "__main__":
    main()
