"""Hour 64: base vs instruct, with crossed rendering. Pre-registered in
`research/shame-axis/notes/crossmodel_prereg.md` (and its amendment).

Four models: Gemma-2-2B base and instruct locally (RTX 3060 Ti, bf16, one text per forward,
forward hooks on every block), and Llama-3.1-70B base and instruct on NDIF (the shared pooled
extractor at a declared subset of blocks). Every model sees the paper's core and control sentences
as raw text, and the 420 scenarios in BOTH renderings: `raw` (the paper's base-model transcript)
and `chat` (the chat template; base models use their instruct sibling's).

Usage:
  python scripts/shame_axis/crossmodel.py extract g2b      # .venv, local GPU, under the shared lock
  python scripts/shame_axis/crossmodel.py extract l70      # .venv312, NDIF
  python scripts/shame_axis/crossmodel.py analyze g2b
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))

import painaxis_scenarios as S  # noqa: E402

OUT = ROOT / "research/shame-axis/results/crossmodel"
CONTROL_SETS = ["Arousal_1P", "Random_1P", "Numb_1P"]
L70_LAYERS = sorted(set(range(0, 80, 4)) | {24, 32, 40, 48, 70, 79})

MODELS = {
    "g2b":    dict(repo="google/gemma-2-2b", sibling="google/gemma-2-2b-it",
                   name="Gemma_2_2B_base", fmt="raw", backend="local", s1=7, s2=13),
    "g2b_it": dict(repo="google/gemma-2-2b-it", sibling="google/gemma-2-2b-it",
                   name="Gemma_2_2B_instruct", fmt="chat", backend="local", s1=10, s2=15),
    "l70":    dict(repo="meta-llama/Llama-3.1-70B", sibling="meta-llama/Llama-3.1-70B-Instruct",
                   name="Llama_3.1_70B_base", fmt="raw", backend="ndif", s1=32, s2=40,
                   layers=L70_LAYERS),
    "l70_it": dict(repo="meta-llama/Llama-3.1-70B-Instruct",
                   sibling="meta-llama/Llama-3.1-70B-Instruct",
                   name="Llama_3.1_70B_instruct", fmt="chat", backend="ndif", s1=24, s2=24,
                   layers=L70_LAYERS),
}


def their_vector_layer(cfg) -> int:
    import torch
    p = S.THEIR_REPO / "results/3.2_pain_vectors/pain_vectors" / cfg["name"] / "pain_vectors.pt"
    return int(torch.load(p, map_location="cpu", weights_only=False)["layer"])


# ----------------------------------------------------------------------------- texts
def texts_for(cfg, tok, sib_tok):
    """(group, texts, add_special_tokens, scenario ids). Chat renders through the sibling's
    template (identical vocabulary asserted); its <bos> is emitted by the template, so the
    tokenizer must not add another."""
    if tok.get_vocab() != sib_tok.get_vocab():
        raise SystemExit(f"{cfg['repo']}: tokenizer vocabulary differs from its instruct sibling")
    ds = json.loads(S.CORE.read_text())["datasets"]
    scen = json.loads(S.SCEN.read_text())
    bad = {b[0] for b in S.validate_candidates(scen)}
    scen = [c for c in scen if c["id"] not in bad]
    groups = [(f"core_{n}", [s["prompt"] for s in ds[n]["sentences"]], True) for n in S.S_SETS]
    groups += [(f"ctrl_{n}", [s["prompt"] for s in ds[n]["sentences"]], True) for n in CONTROL_SETS]
    groups += [("scen_raw", [c["text"] for c in scen], True),
               ("scen_chat", [S.render_chat(c, sib_tok) for c in scen], False)]
    return groups, [c["id"] for c in scen]


def assert_one_bos(tok, texts, add_special):
    bos = tok.bos_token_id
    for t in texts:
        ids = tok(t, add_special_tokens=add_special)["input_ids"]
        if ids.count(bos) != 1 or ids[0] != bos:
            raise SystemExit(f"expected exactly one leading BOS, got {ids[:4]} for {t[:60]!r}")


# ----------------------------------------------------------------------------- local path
def local_pooled(model, tok, texts, add_special):
    """One text per forward: forward hooks on the embedding and every block; final-token and
    mean over all real tokens (unpadded, so the mean needs no mask). Block outputs are
    residuals before any final norm, as on the NDIF path."""
    import torch
    blocks = model.model.layers
    store = {}

    def hook_block(i):
        def h(_m, _a, out):
            x = (out if isinstance(out, torch.Tensor) else out[0])[0].float()
            store[i] = (x[-1].cpu().numpy(), x.mean(0).cpu().numpy())
        return h

    def hook_embed(_m, _a, out):
        x = out[0].float()
        store["e"] = (x[-1].cpu().numpy(), x.mean(0).cpu().numpy())

    handles = [b.register_forward_hook(hook_block(i)) for i, b in enumerate(blocks)]
    handles.append(model.model.embed_tokens.register_forward_hook(hook_embed))
    n, L, d = len(texts), len(blocks), model.config.hidden_size
    ft = np.zeros((n, L, d), np.float32); mn = np.zeros_like(ft)
    eft = np.zeros((n, d), np.float32); emn = np.zeros_like(eft)
    try:
        with torch.no_grad():
            for j, t in enumerate(texts):
                ids = tok(t, return_tensors="pt", add_special_tokens=add_special)["input_ids"].to("cuda")
                store.clear()
                model(input_ids=ids)
                for i in range(L):
                    ft[j, i], mn[j, i] = store[i]
                eft[j], emn[j] = store["e"]
    finally:
        for h in handles:
            h.remove()
    if not all(np.isfinite(a).all() for a in (ft, mn, eft, emn)):
        raise SystemExit("non-finite activations")
    return ft, mn, eft, emn


# ----------------------------------------------------------------------------- extract
def extract(key: str) -> None:
    cfg = MODELS[key]
    out = OUT / key
    (out / "shards").mkdir(parents=True, exist_ok=True)
    from transformers import AutoTokenizer
    sib_tok = AutoTokenizer.from_pretrained(cfg["sibling"])
    if cfg["backend"] == "local":
        import torch
        from transformers import AutoModelForCausalLM
        tok = AutoTokenizer.from_pretrained(cfg["repo"])
        model = AutoModelForCausalLM.from_pretrained(cfg["repo"], torch_dtype=torch.bfloat16,
                                                     device_map="cuda").eval()
        layers = list(range(len(model.model.layers)))
        meta = {"device": "cuda", "dtype": "bfloat16", "torch": torch.__version__}
    else:
        from lsx.core.remote import RemoteLM
        rlm = RemoteLM(cfg["repo"])
        tok = rlm.tok
        layers = cfg["layers"]
        if max(layers) >= len(rlm.blocks):
            raise SystemExit("captured layer beyond the model")
        meta = {"backend": "ndif", "lib_versions": rlm.lib_versions()}
    groups, scen_ids = texts_for(cfg, tok, sib_tok)
    meta.update({"model": cfg["repo"], "their_name": cfg["name"], "captured_layers": layers,
                 "scenario_order": scen_ids, "chat_template_from": cfg["sibling"]})
    (out / "meta.json").write_text(json.dumps(meta, indent=2))
    for gname, texts, add_special in groups:
        assert_one_bos(tok, texts, add_special)
        for s0 in range(0, len(texts), S.SHARD):
            path = out / "shards" / f"{gname}_{s0:04d}.npz"
            chunk = texts[s0:s0 + S.SHARD]
            digest = hashlib.sha256(json.dumps([cfg["repo"], add_special, layers, chunk]).encode()).hexdigest()[:16]
            if path.exists() and str(np.load(path)["digest"]) == digest:
                continue
            t0 = time.time()
            if cfg["backend"] == "local":
                ft, mn, eft, emn = local_pooled(model, tok, chunk, add_special)
            else:
                from lsx.shame_axis import painaxis_remote as pr
                bs = S.BATCH_SCEN if gname.startswith("scen") else S.BATCH
                p = pr.extract_pooled(rlm, chunk, batch_size=bs, add_special_tokens=add_special,
                                      check_every=3, layers=layers)
                ft, mn, eft, emn = p.final_token, p.mean, p.embed_final_token, p.embed_mean
            np.savez_compressed(path, final_token=ft.astype(np.float16), mean=mn.astype(np.float16),
                                embed_final_token=eft.astype(np.float32),
                                embed_mean=emn.astype(np.float32), digest=digest)
            print(f"  {key} {gname}[{s0}] {time.time() - t0:.0f}s", flush=True)
    print(f"EXTRACTION DONE {key}", flush=True)


if __name__ == "__main__":
    {"extract": extract}[sys.argv[1]](sys.argv[2])
