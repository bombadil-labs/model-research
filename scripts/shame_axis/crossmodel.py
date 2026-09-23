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
                                                     low_cpu_mem_usage=True).to("cuda").eval()
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
            bs = (1 if cfg["backend"] == "ndif" else None) if gname.startswith("scen") else S.BATCH
            digest = hashlib.sha256(json.dumps([cfg["repo"], add_special, layers, bs, chunk]).encode()).hexdigest()[:16]
            if path.exists() and str(np.load(path)["digest"]) == digest:
                continue
            t0 = time.time()
            if cfg["backend"] == "local":
                ft, mn, eft, emn = local_pooled(model, tok, chunk, add_special)
            else:
                from lsx.shame_axis import painaxis_remote as pr
                # Scenarios one per job on NDIF (prereg amendment 2): no padding, nothing to equate.
                p = pr.extract_pooled(rlm, chunk, batch_size=bs, add_special_tokens=add_special,
                                      check_every=3, layers=layers)
                ft, mn, eft, emn = p.final_token, p.mean, p.embed_final_token, p.embed_mean
            np.savez_compressed(path, final_token=ft.astype(np.float16), mean=mn.astype(np.float16),
                                embed_final_token=eft.astype(np.float32),
                                embed_mean=emn.astype(np.float32), digest=digest)
            print(f"  {key} {gname}[{s0}] {time.time() - t0:.0f}s", flush=True)
    print(f"EXTRACTION DONE {key}", flush=True)


# ----------------------------------------------------------------------------- analyze
N_NULL, N_BOOT, SEED = 200, 2000, 64


def _load(out, prefix, n, key):
    parts = []
    for s0 in range(0, n, S.SHARD):
        z = np.load(out / "shards" / f"{prefix}_{s0:04d}.npz")
        parts.append(z[key].astype(np.float32))
    a = np.concatenate(parts)
    if a.shape[0] != n:
        raise SystemExit(f"{prefix}/{key}: {a.shape[0]} rows, expected {n}")
    return a


def _split(z, strata):
    return float(z[strata == "self_directed"].mean() - z[strata == "vicarious_empathic"].mean())


def _auc(X, y, seed=SEED):
    from sklearn.linear_model import LogisticRegression
    from sklearn.model_selection import StratifiedKFold, cross_val_predict
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import roc_auc_score
    clf = make_pipeline(StandardScaler(), LogisticRegression(C=0.1, max_iter=2000))
    p = cross_val_predict(clf, X, y, cv=StratifiedKFold(5, shuffle=True, random_state=seed),
                          method="predict_proba")[:, 1]
    return float(roc_auc_score(y, p))


def analyze(key: str) -> None:
    import csv
    import torch
    cfg = MODELS[key]
    out = OUT / key
    meta = json.loads((out / "meta.json").read_text())
    layers = meta["captured_layers"]
    col = {L: i for i, L in enumerate(layers)}
    ds = json.loads(S.CORE.read_text())["datasets"]
    scen = {c["id"]: c for c in json.loads(S.SCEN.read_text())}
    order = meta["scenario_order"]
    strata = np.array([scen[i]["stratum"] for i in order])
    core = {n: _load(out, f"core_{n}", len(ds[n]["sentences"]), "final_token") for n in S.S_SETS}
    core_e = {n: _load(out, f"core_{n}", len(ds[n]["sentences"]), "embed_mean") for n in S.S_SETS}
    cats = {n: [x["category"] for x in ds[n]["sentences"]] for n in S.S_SETS}
    ctrl = {n: _load(out, f"ctrl_{n}", len(ds[n]["sentences"]), "final_token") for n in CONTROL_SETS}
    sc = {r: _load(out, f"scen_{r}", len(order), "final_token") for r in ("raw", "chat")}
    sc_e = {r: _load(out, f"scen_{r}", len(order), "embed_mean") for r in ("raw", "chat")}

    def vecs(L):
        i = col[L]
        return S.build_vectors({n: core[n][:, i] for n in S.S_SETS}, cats,
                               {n: ctrl[n][:, i] for n in CONTROL_SETS})

    rep = {"model": cfg["repo"], "captured_layers": layers, "device": meta.get("device", "ndif")}
    # --- step 1: replication gate -----------------------------------------------------------
    tv = torch.load(S.THEIR_REPO / "results/3.2_pain_vectors/pain_vectors" / cfg["name"] / "pain_vectors.pt",
                    map_location="cpu", weights_only=False)
    VL = int(tv["layer"])
    if VL in col:
        v = vecs(VL)
        rep["vector_cos_at_their_layer"] = {k: float(S.unit(v[k]) @ S.unit(tv[k].float().numpy()))
                                            for k in ("s1_pain_vector", "s2_pain_vector")}
    theirs = {r["id"]: r for r in csv.DictReader(open(S.THEIR_REPO / "results/4.1_self_other/per_model"
                                                      / f"screen_v2_{cfg['name']}.csv", encoding="utf-8"))}
    rep["replication"] = {}
    for tag in ("s1", "s2"):
        L = cfg[tag]
        v = vecs(L)
        for vn in ("s1_pain_vector", "s2_pain_vector"):
            z = S.zscore_pool(sc[cfg["fmt"]][:, col[L]] @ S.unit(v[vn]))
            t = np.array([float(theirs[i][f"{vn}_z"]) for i in order])
            rep["replication"][f"{tag}_layer_{L}:{vn}"] = float(np.corrcoef(z, t)[0, 1])
    best = max(rep["replication"], key=lambda k: rep["replication"][k] if k.endswith("s2_pain_vector") else -9)
    screen_L = int(best.split("_layer_")[1].split(":")[0])
    rep["screen_layer"] = screen_L
    rep["gate_pass"] = rep["replication"][best] >= 0.99
    print(json.dumps({k: rep[k] for k in ("vector_cos_at_their_layer", "replication", "screen_layer",
                                          "gate_pass") if k in rep}, indent=1), flush=True)

    # --- step 2: the split, network vs floor, both renderings, every captured layer -----------
    fv = S.build_vectors(core_e, cats, {})["s2_pain_vector"]
    rng = np.random.default_rng(SEED)
    rep["renderings"] = {}
    per_item = {}
    for r in ("raw", "chat"):
        floor_z = S.zscore_pool(sc_e[r] @ S.unit(fv))
        curve = []
        for L in layers:
            i = col[L]
            z = S.zscore_pool(sc[r][:, i] @ S.unit(vecs(L)["s2_pain_vector"]))
            rand = [abs(_split(S.zscore_pool(sc[r][:, i] @ S.unit(rng.standard_normal(sc[r].shape[-1]))), strata))
                    for _ in range(N_NULL)]
            shuf = []
            for _ in range(N_NULL // 4):
                c2 = {n: list(rng.permutation(cats[n])) for n in S.S_SETS}
                vs = S.build_vectors({n: core[n][:, i] for n in S.S_SETS}, c2, {})["s2_pain_vector"]
                shuf.append(abs(_split(S.zscore_pool(sc[r][:, i] @ S.unit(vs)), strata)))
            net = _split(z, strata)
            curve.append({"layer": L, "net_split": net, "floor_split": _split(floor_z, strata),
                          "contribution": net - _split(floor_z, strata),
                          "self_mean_z": float(z[strata == "self_directed"].mean()),
                          "vic_mean_z": float(z[strata == "vicarious_empathic"].mean()),
                          "rand_q95": float(np.quantile(rand, .95)),
                          "shuffled_q95": float(np.quantile(shuf, .95)),
                          "net_above_nulls": bool(abs(net) > max(np.quantile(rand, .95), np.quantile(shuf, .95)))})
            if L == screen_L:
                per_item[r] = {"net_z": z.tolist(), "floor_z": floor_z.tolist()}
        rep["renderings"][r] = curve
    rep["per_item_at_screen_layer"] = per_item
    rep["strata"] = strata.tolist()

    # --- amendment 1: decoding ---------------------------------------------------------------
    sv = np.isin(strata, ["self_directed", "vicarious_empathic"])
    ysv = (strata[sv] == "self_directed").astype(int)
    pain_X = np.concatenate([core["S1_1P"], core["S2_1P"]])
    pain_y = np.array([c.startswith("A") for c in cats["S1_1P"] + cats["S2_1P"]], dtype=int)
    rep["decoding"] = []
    for L in layers:
        i = col[L]
        rep["decoding"].append({"layer": L,
                                "self_vs_vic_auc_raw": _auc(sc["raw"][sv, i], ysv),
                                "self_vs_vic_auc_chat": _auc(sc["chat"][sv, i], ysv),
                                "pain_vs_control_auc": _auc(pain_X[:, i], pain_y)})
    (out / "summary.json").write_text(json.dumps(rep, indent=1))
    print(f"wrote {out / 'summary.json'}", flush=True)


def compare(family: str) -> None:
    """Delta_post = contribution(instruct) - contribution(base), paired over items, per rendering."""
    base, inst = {"g2b": ("g2b", "g2b_it"), "l70": ("l70", "l70_it")}[family]
    A = json.loads((OUT / base / "summary.json").read_text())
    B = json.loads((OUT / inst / "summary.json").read_text())
    if not (A["gate_pass"] and B["gate_pass"]):
        print("REPLICATION GATE FAILED -- not interpreted", A["gate_pass"], B["gate_pass"])
    strata = np.array(A["strata"])
    s_idx, v_idx = np.flatnonzero(strata == "self_directed"), np.flatnonzero(strata == "vicarious_empathic")
    rng = np.random.default_rng(SEED)
    res = {}
    for r in ("raw", "chat"):
        def contrib(m, si, vi):
            n, f = np.array(m["per_item_at_screen_layer"][r]["net_z"]), np.array(m["per_item_at_screen_layer"][r]["floor_z"])
            return (n[si].mean() - n[vi].mean()) - (f[si].mean() - f[vi].mean())
        def parts(m, si, vi):
            n = np.array(m["per_item_at_screen_layer"][r]["net_z"])
            return n[si].mean(), n[vi].mean()
        obs = contrib(B, s_idx, v_idx) - contrib(A, s_idx, v_idx)
        boots, dself, dvic = [], [], []
        for _ in range(N_BOOT):
            si, vi = rng.choice(s_idx, s_idx.size), rng.choice(v_idx, v_idx.size)
            boots.append(contrib(B, si, vi) - contrib(A, si, vi))
            (bs, bv), (as_, av) = parts(B, si, vi), parts(A, si, vi)
            dself.append(bs - as_); dvic.append(bv - av)
        (bs, bv), (as_, av) = parts(B, s_idx, v_idx), parts(A, s_idx, v_idx)
        res[r] = {"contribution_base": contrib(A, s_idx, v_idx), "contribution_instruct": contrib(B, s_idx, v_idx),
                  "delta_post": obs, "delta_post_ci95": list(map(float, np.quantile(boots, [.025, .975]))),
                  "delta_self_mean_z": bs - as_, "delta_self_ci95": list(map(float, np.quantile(dself, [.025, .975]))),
                  "delta_vic_mean_z": bv - av, "delta_vic_ci95": list(map(float, np.quantile(dvic, [.025, .975])))}
    res["format_effect"] = {m: float(
        (lambda M: (lambda c: c("chat") - c("raw"))(lambda r: (np.array(M["per_item_at_screen_layer"][r]["net_z"])[s_idx].mean()
            - np.array(M["per_item_at_screen_layer"][r]["net_z"])[v_idx].mean()) - (np.array(M["per_item_at_screen_layer"][r]["floor_z"])[s_idx].mean()
            - np.array(M["per_item_at_screen_layer"][r]["floor_z"])[v_idx].mean())))(M)) for m, M in (("base", A), ("instruct", B))}
    (OUT / f"compare_{family}.json").write_text(json.dumps(res, indent=1))
    print(json.dumps(res, indent=1))


if __name__ == "__main__":
    {"extract": extract, "analyze": analyze, "compare": compare}[sys.argv[1]](sys.argv[2])
