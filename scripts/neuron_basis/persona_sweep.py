"""Persona battery, first pass: push one down-projection column by alpha residual norms and read
the reply by generation, with every arm (research/neuron-basis/notes/persona_arms_prereg_DRAFT.md).

Arms (--arm, repeatable):
  no_patch        unhooked generate (the reference reply)
  zero_patch      Patch(layer=L+1, add_vector(0 * column)) through the identical generate call;
                  declared null: reply verbatim equal to no_patch (the h34 lesson: doing nothing
                  THROUGH the patch path must read as nothing)
  random_column   c * W_down[:, j], j uniform over d_mlp, sign in {+1, -1}, --n draws per sign
  dense_manifold  sum over ALL columns of W_down with random signs, normalised to the column
                  shift norm: dense in the neuron basis, on the model's own write manifold
  random_dense    isotropic Gaussian of matched norm: OFF-manifold, reported as such (review e)
  pc_judge        no patch, system message puts the model in a persona: the judge must read it
  pc_patch        the mean-difference direction (persona-system minus assistant-system) at the
                  last prompt position, injected like a column at the same alpha grid: if this
                  cannot produce a persona, the dose grid or the hook is wrong (review a)
  treatment       explicit columns from --column L:j:sign
  skip_path       the treatment shift at the final-norm input (Patch layer == n_layers). NOT a
                  pass-through arm: top-of-stack steering with a different relative dose, reported
                  with alpha * r_L / r_top in the row (review d)

Decode: greedy with repetition_penalty=1.0 set EXPLICITLY. The shipped generation_config.json
carries repetition_penalty 1.1, which HF applies even under do_sample=False; the resolved config
is dumped into every row. Chat template with an explicit system message (--system; the template
injects "You are Qwen, created by Alibaba Cloud..." when none is given, and that is recorded
too). r_L is pooled over the prompt positions of every prompt (one dose per layer), first token
excluded; r_L_gen (over the no_patch reply's generated positions) is reported beside it.

The patch is `Patch(layer=L+1, fn=add_vector(shift))`: a forward-pre-hook on block L+1's input,
i.e. the residual after block L, every position, every generation step (notes/operation.md).
r_L is the median residual norm after block L over the prompt's tokens excluding the first,
measured per prompt on an unpatched forward. Every patched generation asserts the hook fired and
moved the residual by exactly the shift (INSTRUMENTS §4). Batch-of-one throughout. Greedy.

Resumable: one JSONL line per cell, keyed by `cell`; existing cells are skipped. Every line
carries the model checkpoint and revision, dtype, device, core code version and chat-template hash.

Usage:
  python scripts/neuron_basis/persona_sweep.py --layer 12 --alpha 1.0 2.0 --arm random_column \
      --n 40 --prompts who_are_you --out research/neuron-basis/results/first_pass/L12.jsonl
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time

import numpy as np
import torch

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

from lsx.core import extract as core_extract           # noqa: E402
from lsx.model import LM, Patch                         # noqa: E402
from lsx.neuron_basis import (dose_scale, down_proj, matched_dense_direction, median_residual_norm,  # noqa: E402
                              write_direction)
from lsx.steer import add_vector                        # noqa: E402

PROMPTS = ROOT / "research/neuron-basis/prompts/self_identification_v1.json"
MODEL = "Qwen/Qwen2.5-1.5B-Instruct"


def render(lm: LM, user_text: str, system: str | None) -> str:
    msgs = ([{"role": "system", "content": system}] if system else []) + [{"role": "user", "content": user_text}]
    return lm.tok.apply_chat_template(msgs, tokenize=False, add_generation_prompt=True)


def degenerate(ids: list[int]) -> dict:
    """Declared degeneracy detector (review g): fraction of tokens inside a repeated 4-gram, and
    the distinct-2 ratio. Calibrated in the run on the no_patch replies (must read 0) and on
    planted loops (must read 1); see calibrate_degeneracy()."""
    n = len(ids)
    if n < 4:
        return {"rep4_frac": 0.0, "distinct2": 1.0, "degenerate": n == 0}
    grams = {}
    for i in range(n - 3):
        grams.setdefault(tuple(ids[i:i + 4]), []).append(i)
    covered = set()
    for g, pos in grams.items():
        if len(pos) > 1:
            for i in pos:
                covered.update(range(i, i + 4))
    rep4 = len(covered) / n
    bigrams = {tuple(ids[i:i + 2]) for i in range(n - 1)}
    d2 = len(bigrams) / max(1, n - 1)
    return {"rep4_frac": rep4, "distinct2": d2, "degenerate": bool(rep4 > 0.3 or d2 < 0.4)}


def calibrate_degeneracy(no_patch_ids: list[list[int]]) -> dict:
    clean = [degenerate(x)["degenerate"] for x in no_patch_ids]
    planted = [degenerate((x[:8] or [1, 2, 3, 4, 5, 6, 7, 8]) * 8)["degenerate"] for x in no_patch_ids]
    return {"no_patch_flagged": sum(clean), "planted_loops_flagged": sum(planted), "n": len(clean),
            "passed": sum(clean) == 0 and sum(planted) == len(planted)}


@torch.no_grad()
def residual_after(lm: LM, text: str, layer_after: int) -> np.ndarray:
    """[seq, d] residual entering block layer_after+1 (== after block layer_after), unpatched."""
    enc = lm.tok(text, return_tensors="pt")
    out = lm.model(**enc, output_hidden_states=True)
    # hidden_states[k] is the residual after block k-1 (k=0 is the embedding), so after block L
    # is index L+1. Qwen's last entry is post-norm (INSTRUMENTS, rediscovery), never used here.
    assert layer_after + 1 < len(out.hidden_states) - 1
    return out.hidden_states[layer_after + 1][0].float().cpu().numpy()


class Moved:
    """Wrap a patch fn so the generation can assert the hook fired and moved the residual by the
    shift it was given, on the first call (prompt) and every step after."""
    def __init__(self, shift: np.ndarray):
        self.shift = torch.as_tensor(shift, dtype=torch.float32)
        self.calls = 0
        self.max_err = 0.0          # max |delta - shift| over every entry, every call
        self.max_abs = 0.0          # max |hidden| seen, which sets the bf16 rounding tolerance
        self.min_cos = 1.0          # cosine of the per-position delta with the shift
        self.inner = add_vector(shift)

    def __call__(self, hidden: torch.Tensor) -> torch.Tensor:
        out = self.inner(hidden)
        delta = (out.float() - hidden.float())
        sh = self.shift.to(delta.device)
        self.max_err = max(self.max_err, float((delta - sh).abs().max()))
        self.max_abs = max(self.max_abs, float(hidden.float().abs().max()))
        cos = torch.nn.functional.cosine_similarity(delta.reshape(-1, delta.shape[-1]),
                                                    sh.expand(delta.numel() // delta.shape[-1], -1), dim=-1)
        self.min_cos = min(self.min_cos, float(cos.min()))
        self.calls += 1
        return out


def repetition_flag(ids: list[int], n: int = 8, times: int = 3) -> bool:
    grams: dict[tuple, int] = {}
    for i in range(len(ids) - n + 1):
        g = tuple(ids[i:i + n]); grams[g] = grams.get(g, 0) + 1
        if grams[g] >= times:
            return True
    return False


@torch.no_grad()
def reply_nll(lm: LM, prompt_ids: torch.Tensor, reply_ids: torch.Tensor) -> float:
    """Mean NLL of the reply tokens under the UNSTEERED model (no hooks registered)."""
    ids = torch.cat([prompt_ids, reply_ids], dim=1)
    logits = lm.model(input_ids=ids).logits[0].float()
    lp = torch.log_softmax(logits[prompt_ids.shape[1] - 1:-1], dim=-1)
    tgt = reply_ids[0]
    return float(-lp[torch.arange(len(tgt)), tgt].mean())


@torch.no_grad()
def generate(lm: LM, text: str, patches: list[Patch], max_new: int):
    enc = lm.tok(text, return_tensors="pt")
    with lm.patched(patches):
        out = lm.model.generate(**enc, max_new_tokens=max_new, do_sample=False,
                                repetition_penalty=1.0, temperature=None, top_p=None, top_k=None,
                                pad_token_id=lm.tok.pad_token_id)
    reply_ids = out[:, enc.input_ids.shape[1]:]
    return enc.input_ids, reply_ids


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default=MODEL)
    ap.add_argument("--dtype", default="f32", choices=["bf16", "f32"],
                    help="f32: bf16 cannot add a small shift faithfully next to Qwen's massive activations (pilot, hour 67)")
    ap.add_argument("--system", default="You are a helpful assistant.",
                    help="explicit system message; '' uses the template's injected default")
    ap.add_argument("--persona-system", default="You are Blackbeard, a pirate captain. Stay in character and never say you are an AI.")
    ap.add_argument("--layer", type=int, required=True, help="L: residual AFTER block L is patched")
    ap.add_argument("--alpha", type=float, nargs="+", required=True)
    ap.add_argument("--arm", action="append", required=True,
                    choices=["no_patch", "zero_patch", "random_column", "dense_manifold", "random_dense",
                             "pc_judge", "pc_patch", "treatment", "skip_path"])
    ap.add_argument("--n", type=int, default=20, help="draws per (alpha, sign) for random arms")
    ap.add_argument("--signs", type=int, nargs="+", default=[1, -1])
    ap.add_argument("--column", action="append", default=[], help="L:j:sign for treatment/skip_path")
    ap.add_argument("--prompts", nargs="+", default=["who_are_you"])
    ap.add_argument("--max-new-tokens", type=int, default=64)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    a = ap.parse_args()

    spec = json.loads(PROMPTS.read_text())
    prompts = {k: spec["prompts"][k] for k in a.prompts}
    a.out.parent.mkdir(parents=True, exist_ok=True)
    done = set()
    if a.out.exists():
        for line in a.out.read_text().splitlines():
            if line.strip():
                done.add(json.loads(line)["cell"])

    torch.set_num_threads(max(1, torch.get_num_threads()))
    dtype = torch.bfloat16 if a.dtype == "bf16" else torch.float32
    t0 = time.time()
    lm = LM.from_pretrained(a.model, device="cpu", dtype=dtype)
    revision = None
    try:   # the snapshot directory name is the commit hash of the checkpoint actually loaded
        from huggingface_hub import snapshot_download
        revision = pathlib.Path(snapshot_download(a.model, local_files_only=True)).name
    except Exception:
        import glob, os
        hits = glob.glob(os.path.join(os.environ.get("HF_HOME", ""), "hub", "models--" + a.model.replace("/", "--"), "snapshots", "*"))
        revision = pathlib.Path(hits[0]).name if len(hits) == 1 else None
    L = a.layer
    assert 0 <= L < lm.n_layers - 1, "need a block after L to patch into"
    block = lm.blocks[L]
    d_mlp = write_direction(block, 0).shape[0] and lm.model.config.intermediate_size
    prov = {"model": a.model, "revision": revision, "dtype": a.dtype, "device": "cpu",
            "core_code_version": core_extract.code_version(),
            "chat_template": core_extract.chat_template(lm), "libs": core_extract.lib_versions(),
            "prompt_set": spec["version"], "max_new_tokens": a.max_new_tokens, "greedy": True,
            "batch_size": 1, "patch_site": f"residual after block {L} (Patch layer {L+1})",
            "d_mlp": d_mlp, "n_layers": lm.n_layers, "d_model": lm.d_model,
            "system": a.system or "<template default>", "persona_system": a.persona_system,
            "decode": {"do_sample": False, "repetition_penalty": 1.0, "shipped_generation_config": lm.model.generation_config.to_dict()}}
    print(f"loaded {a.model}@{revision} in {time.time()-t0:.1f}s; L={L} d_mlp={d_mlp}", flush=True)

    # ONE r_L per layer: pooled over the prompt positions of every prompt, first token excluded
    # (review f). Per-prompt medians and per-position norms go into the artifact for checking.
    texts = {k: render(lm, v, a.system or None) for k, v in prompts.items()}
    persona_texts = {k: render(lm, v, a.persona_system) for k, v in prompts.items()}
    per_prompt, norms_all, first_ids = {}, [], {}
    for k, text in texts.items():
        h = residual_after(lm, text, L)
        per_prompt[k] = median_residual_norm(h)
        norms_all.extend(np.linalg.norm(h[1:], axis=1).tolist())
        first_ids[k] = int(lm.tok(text).input_ids[0])
    r_pool = float(np.median(norms_all))
    r_l = {k: r_pool for k in prompts}
    # the pre-final-norm residual norm, for the skip_path arm's relative dose
    h_top = residual_after(lm, next(iter(texts.values())), lm.n_layers - 2)   # after block n-2 = input to last block
    r_top = median_residual_norm(h_top)
    prov.update({"r_L_pooled": r_pool, "r_L_per_prompt": per_prompt, "r_top_proxy_after_block": lm.n_layers - 2,
                 "r_top": r_top, "first_token_id": first_ids, "prompt_position_norms_L": norms_all})
    print(f"r_L pooled {r_pool:.2f} per-prompt {({k: round(v, 2) for k, v in per_prompt.items()})} r_top~{r_top:.1f}", flush=True)

    # pc_patch direction: persona-system minus assistant-system at the last prompt position,
    # mean over prompts (review a). Fit on the same prompts it is scored on: it is a positive
    # control for the PATCH PATH, not a finding, and is labelled so.
    pc_dir = None
    if "pc_patch" in a.arm:
        diffs = [residual_after(lm, persona_texts[k], L)[-1] - residual_after(lm, texts[k], L)[-1] for k in prompts]
        pc_dir = np.mean(diffs, axis=0)
        prov["pc_patch_direction_norm"] = float(np.linalg.norm(pc_dir))

    rng = np.random.default_rng(a.seed)
    # Draws are fixed by seed and draw index, independent of which arms/alphas are requested, so a
    # resumed or extended run reuses the same columns.
    col_draws = [(int(rng.integers(d_mlp)), int(s)) for s in a.signs for _ in range(a.n)]
    dense_seeds = [int(x) for x in rng.integers(2**31 - 1, size=a.n * len(a.signs))]
    treat = [tuple(int(x) for x in c.split(":")) for c in a.column]
    for (l, _, _) in treat:
        assert l == L, f"--column layer {l} != --layer {L}"

    cells = []
    for pk in prompts:
        for arm in ("no_patch", "zero_patch", "pc_judge"):
            if arm in a.arm:
                cells.append(dict(arm=arm, prompt=pk, alpha=0.0, sign=0, column=(col_draws[0][0] if arm == "zero_patch" else None), draw=None))
        for alpha in a.alpha:
            if "random_column" in a.arm:
                for i, (j, s) in enumerate(col_draws):
                    cells.append(dict(arm="random_column", prompt=pk, alpha=alpha, sign=s, column=j, draw=i))
            for arm in ("dense_manifold", "random_dense"):
                if arm in a.arm:
                    for i, sd in enumerate(dense_seeds):
                        cells.append(dict(arm=arm, prompt=pk, alpha=alpha, sign=1, column=None, draw=i, dense_seed=sd))
            if "pc_patch" in a.arm:
                for s_ in (1, -1):
                    cells.append(dict(arm="pc_patch", prompt=pk, alpha=alpha, sign=s_, column=None, draw=None))
            for arm in ("treatment", "skip_path"):
                if arm in a.arm:
                    for (_, j, s) in treat:
                        cells.append(dict(arm=arm, prompt=pk, alpha=alpha, sign=s, column=j, draw=None))

    def cell_key(c):
        return f"L{L}|{c['arm']}|{c['prompt']}|a{c['alpha']}|s{c['sign']}|c{c['column']}|d{c['draw']}"

    base_resid = {k: residual_after(lm, t, L) for k, t in texts.items()}
    mean_resid = np.mean([h[1:].mean(axis=0) for h in base_resid.values()], axis=0)
    W_down = down_proj(block).weight.detach().double().cpu().numpy()      # [d_model, d_mlp]
    no_patch_reply: dict[str, str] = {}
    no_patch_ids: list[list[int]] = []
    todo = [c for c in cells if cell_key(c) not in done]
    print(f"{len(cells)} cells, {len(done)} done, {len(todo)} to run", flush=True)
    with a.out.open("a") as f:
        for n_done, c in enumerate(todo, 1):
            t = time.time()
            text = persona_texts[c["prompt"]] if c["arm"] == "pc_judge" else texts[c["prompt"]]
            patches, moved, shift_norm, extra = [], None, 0.0, {}
            if c["arm"] not in ("no_patch", "pc_judge"):
                target = c["alpha"] * r_l[c["prompt"]]          # every shift has this norm
                if c["arm"] == "zero_patch":
                    shift = 0.0 * write_direction(block, c["column"])
                elif c["arm"] == "random_dense":
                    ref = np.zeros(lm.d_model); ref[0] = target
                    shift = matched_dense_direction(ref, np.random.default_rng(c["dense_seed"]))
                elif c["arm"] == "dense_manifold":
                    signs = np.random.default_rng(c["dense_seed"]).choice([-1.0, 1.0], size=d_mlp)
                    v = (W_down * signs).sum(axis=1)
                    shift = v * (target / np.linalg.norm(v))
                elif c["arm"] == "pc_patch":
                    shift = c["sign"] * pc_dir * (target / np.linalg.norm(pc_dir))
                else:
                    col = write_direction(block, c["column"])
                    shift = dose_scale(r_l[c["prompt"]], col, c["alpha"], c["sign"]) * col
                shift_norm = float(np.linalg.norm(shift))
                h0 = base_resid[c["prompt"]]
                extra = {"shift_cos_mean_resid": float(np.dot(shift, mean_resid) / (np.linalg.norm(shift) * np.linalg.norm(mean_resid) + 1e-12)) if shift_norm else 0.0,
                         "shift_frac_on_top3_dims": float(np.sort(np.abs(shift))[-3:].sum() / (np.abs(shift).sum() + 1e-12)) if shift_norm else 0.0,
                         "realised_norm_ratio": float(np.median(np.linalg.norm(h0[1:] + shift, axis=1) / np.linalg.norm(h0[1:], axis=1)))}
                moved = Moved(shift)
                layer = lm.n_layers if c["arm"] == "skip_path" else L + 1
                if c["arm"] == "skip_path":
                    extra["relative_dose_top"] = float(c["alpha"] * r_l[c["prompt"]] / r_top)
                patches = [Patch(layer=layer, fn=moved)]
            prompt_ids, reply_ids = generate(lm, text, patches, a.max_new_tokens)
            if moved is not None and c["arm"] != "zero_patch":
                # The add happens in the model dtype. bf16 keeps 8 significant bits, so an entry of
                # magnitude M rounds by up to M * 2^-8; Qwen residuals carry a few massive
                # dimensions (hundreds), so the tolerance is set by the largest entry the hook saw,
                # not by r_L. Direction is checked separately: the per-position delta must point
                # along the shift.
                # f32 keeps 24 bits: the same rounding argument at 2^-20 of the largest entry.
                tol = (moved.max_abs * 2 ** -7 + 1e-3) if a.dtype == "bf16" else (moved.max_abs * 2 ** -20 + 1e-4)
                assert moved.calls >= 1, "patch hook never fired"
                assert moved.max_err < tol, (f"patch did not move the residual by the shift "
                                             f"(max err {moved.max_err:.3f} > tol {tol:.3f})")
                assert moved.min_cos > 0.99, f"delta is not along the shift (min cos {moved.min_cos:.3f})"
            ids = reply_ids[0].tolist()
            reply = lm.tok.decode(reply_ids[0], skip_special_tokens=True)
            if c["arm"] == "no_patch":
                no_patch_reply[c["prompt"]] = reply
                no_patch_ids.append(ids)
            if c["arm"] == "zero_patch":
                ref = no_patch_reply.get(c["prompt"])
                extra["zero_patch_equals_no_patch"] = (ref == reply) if ref is not None else None
                assert ref is None or ref == reply, "ZERO-SHIFT PATCH CHANGED THE REPLY: the patch path is not inert (h34)"
            nll = reply_nll(lm, prompt_ids, reply_ids) if len(ids) else float("nan")
            row = dict(cell=cell_key(c), layer=L, **c, r_l=r_l[c["prompt"]], shift_norm=shift_norm,
                       reply=reply, n_tokens=len(ids), repetition=repetition_flag(ids), **degenerate(ids), **extra,
                       reply_nll_unsteered=nll, hook_calls=(moved.calls if moved else 0),
                       hook_max_err=(moved.max_err if moved else 0.0),
                       hook_max_abs=(moved.max_abs if moved else 0.0), hook_min_cos=(moved.min_cos if moved else 1.0),
                       seconds=round(time.time() - t, 1),
                       provenance=prov)
            f.write(json.dumps(row) + "\n"); f.flush()
            if n_done % 10 == 0 or n_done == len(todo):
                print(f"  {n_done}/{len(todo)}  {row['cell']}  {row['seconds']}s  {reply[:60]!r}", flush=True)
    if no_patch_ids:
        cal = calibrate_degeneracy(no_patch_ids)
        gen_norms = []
        for k, text in texts.items():
            if k in no_patch_reply and no_patch_reply[k]:
                h = residual_after(lm, text + no_patch_reply[k], L)
                gen_norms.extend(np.linalg.norm(h[len(lm.tok(text).input_ids):], axis=1).tolist())
        side = {"degeneracy_calibration": cal, "r_L_gen": (float(np.median(gen_norms)) if gen_norms else None),
                "r_L_pooled": r_pool, "r_L_gen_over_r_L": (float(np.median(gen_norms) / r_pool) if gen_norms else None)}
        a.out.with_suffix(".sidecar.json").write_text(json.dumps({**prov, **side}, indent=1))
        print("sidecar:", {k: side[k] for k in ("degeneracy_calibration", "r_L_gen_over_r_L")}, flush=True)


if __name__ == "__main__":
    main()
