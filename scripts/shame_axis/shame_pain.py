"""Hour 65: shame vs witness on the S2 pain axis. Pre-registered in
`research/shame-axis/notes/shame_vs_pain_prereg.md`; stimuli in
`research/shame-axis/prompts/stimuli/shame_pain_v1/`.

Usage:
  python scripts/shame_axis/shame_pain.py valence          # .venv, local, before any activation is read
  python scripts/shame_axis/shame_pain.py extract g2b      # .venv, local GPU, under the shared lock
  python scripts/shame_axis/shame_pain.py extract l70      # .venv312, NDIF, batch 1
  python scripts/shame_axis/shame_pain.py analyze          # every model with shards on disk

The pain vectors come from hour 64's stacks (`results/crossmodel/<key>/shards`), which are
digest-checked here and never re-extracted.
"""
from __future__ import annotations

import hashlib
import itertools
import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))

import crossmodel as X  # noqa: E402
import painaxis_scenarios as S  # noqa: E402
import shame_pain_validate as V  # noqa: E402

OUT = ROOT / "research/shame-axis/results/shame_pain"
AUTHORS = ("claude", "gpt")
SEED = 20260923
N_RAND, N_SHUF, N_SHUF_CURVE, N_BOOT, N_FLIP40 = 1000, 250, 50, 10_000, 100_000
VALENCE_MODEL = "distilbert-base-uncased-finetuned-sst-2-english"
DIGEST_RECIPES: dict[str, set] = {}
STIM_FILES = ("bases.json", "clauses_claude.json", "clauses_gpt.json")
STIM_SHA = {"clauses_claude.json": "98752b034c6d9f885b0ff3cd7268a954a6a73fd716ab533fccdbcf841021fa0f",
            "clauses_gpt.json": "1e18089af2fee9b458f8160e4f257f23393d592c00d004a97c82b7b42b25e08b"}


# ----------------------------------------------------------------------------- items
def items() -> list[dict]:
    """The 200 sentences in a fixed order: per base, base then each author's shame and witness."""
    for name, sha in STIM_SHA.items():
        if hashlib.sha256((V.DIR / name).read_bytes()).hexdigest() != sha:
            raise SystemExit(f"{name} differs from its committed hash")
    bases = json.loads((V.DIR / "bases.json").read_text())
    docs = {a: {i["base_id"]: i for i in json.loads((V.DIR / f"clauses_{a}.json").read_text())["items"]}
            for a in AUTHORS}
    out = []
    for b in bases:
        cat = b["base_id"].split("-")[0]
        out.append(dict(base_id=b["base_id"], cat=cat, author=None, arm="base", text=b["base"]))
        for a in AUTHORS:
            for arm in ("shame", "witness"):
                out.append(dict(base_id=b["base_id"], cat=cat, author=a, arm=arm,
                                text=V.build(b["base"], docs[a][b["base_id"]][arm])))
    if len(out) != 200 or len({r["text"] for r in out}) != 200:
        raise SystemExit("expected 200 distinct sentences")
    return out


# ----------------------------------------------------------------------------- valence
def valence() -> None:
    """logit(negative) - logit(positive) per sentence, without the trailing ' I feel:'."""
    import torch
    from transformers import AutoModelForSequenceClassification, AutoTokenizer
    from huggingface_hub import snapshot_download
    path = snapshot_download(VALENCE_MODEL)
    rev = pathlib.Path(path).name
    tok = AutoTokenizer.from_pretrained(path)
    model = AutoModelForSequenceClassification.from_pretrained(path).eval()
    neg, pos = model.config.label2id["NEGATIVE"], model.config.label2id["POSITIVE"]
    rows = items()
    texts = [r["text"][: -len(" I feel:")] for r in rows]
    with torch.no_grad():
        logits = model(**tok(texts, return_tensors="pt", padding=True)).logits
    val = (logits[:, neg] - logits[:, pos]).tolist()
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "valence.json").write_text(json.dumps(
        {"model": VALENCE_MODEL, "revision": rev, "device": "cpu", "torch": torch.__version__,
         "score": "logit(NEGATIVE) - logit(POSITIVE)", "texts": texts, "valence": val}, indent=1))
    print("valence written", rev, flush=True)


# ----------------------------------------------------------------------------- extract
def extract(key: str) -> None:
    cfg = X.MODELS[key]
    out = OUT / key
    (out / "shards").mkdir(parents=True, exist_ok=True)
    rows = items()
    texts = [r["text"] for r in rows]
    if cfg["backend"] == "local":
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
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
        meta = {"backend": "ndif", "lib_versions": rlm.lib_versions()}
    hour64 = json.loads((X.OUT / key / "meta.json").read_text())["captured_layers"]
    if layers != hour64:
        raise SystemExit(f"{key}: captured layers differ from hour 64's")
    X.assert_one_bos(tok, texts, True)
    meta.update({"model": cfg["repo"], "captured_layers": layers, "items": rows})
    (out / "meta.json").write_text(json.dumps(meta, indent=1))
    bs = 1 if cfg["backend"] == "ndif" else None
    for s0 in range(0, len(texts), S.SHARD):
        path = out / "shards" / f"sp_{s0:04d}.npz"
        chunk = texts[s0:s0 + S.SHARD]
        digest = hashlib.sha256(json.dumps([cfg["repo"], True, layers, bs, chunk]).encode()).hexdigest()[:16]
        if path.exists() and str(np.load(path)["digest"]) == digest:
            continue
        t0 = time.time()
        if cfg["backend"] == "local":
            ft, mn, eft, emn = X.local_pooled(model, tok, chunk, True)
        else:
            from lsx.shame_axis import painaxis_remote as pr
            p = pr.extract_pooled(rlm, chunk, batch_size=1, add_special_tokens=True,
                                  check_every=3, layers=layers)
            ft, mn, eft, emn = p.final_token, p.mean, p.embed_final_token, p.embed_mean
        np.savez_compressed(path, final_token=ft.astype(np.float16), mean=mn.astype(np.float16),
                            embed_final_token=eft.astype(np.float32),
                            embed_mean=emn.astype(np.float32), digest=digest)
        print(f"  {key} sp[{s0}] {time.time() - t0:.0f}s", flush=True)
    print(f"EXTRACTION DONE {key}", flush=True)


# ----------------------------------------------------------------------------- statistics
def signflip_p(d: np.ndarray, rng: np.random.Generator) -> float:
    """One-sided P(mean of sign-flipped d >= observed). Exact for n <= 20, else N_FLIP40 draws."""
    d = np.asarray(d, np.float64)
    obs = d.mean()
    n = len(d)
    if n <= 20:
        hits = 0
        for chunk in range(0, 2 ** n, 1 << 16):
            k = np.arange(chunk, min(chunk + (1 << 16), 2 ** n))[:, None]
            signs = 1 - 2 * ((k >> np.arange(n)) & 1)
            hits += int(((signs * d).mean(1) >= obs - 1e-12).sum())
        return hits / 2 ** n
    signs = rng.choice([-1.0, 1.0], size=(N_FLIP40 - 1, n))
    return (1 + int(((signs * d).mean(1) >= obs - 1e-12).sum())) / N_FLIP40


def boot_ci(stat, n: int, rng: np.random.Generator) -> list[float]:
    idx = rng.integers(0, n, size=(N_BOOT, n))
    vals = np.array([stat(i) for i in idx])
    return [float(np.quantile(vals, .025)), float(np.quantile(vals, .975))]


def alpha_fit(d: np.ndarray, dv: np.ndarray) -> tuple[float, float]:
    A = np.column_stack([np.ones_like(dv), dv])
    (a, b), *_ = np.linalg.lstsq(A, d, rcond=None)
    return float(a), float(b)


def tracks_shame(cell: dict, positive_control_pass: bool) -> bool:
    """The five frozen criteria, and the model's positive control (prereg, "Decision")."""
    return bool(positive_control_pass
                and cell["delta"] > 0 and cell["p"] <= .05 and cell["clears_nulls"]
                and cell["network_contribution_ci"][0] > 0 and cell["alpha_ci"][0] > 0
                and cell["delta_D"] > 0 and cell["p_D"] <= .05)


def _hour64_stacks(key: str):
    """Core and control final-token stacks and the embed_mean core stack, digest-checked."""
    out = X.OUT / key
    meta = json.loads((out / "meta.json").read_text())
    cfg = X.MODELS[key]
    ds = json.loads(S.CORE.read_text())["datasets"]
    for n in S.S_SETS + X.CONTROL_SETS:
        prefix = ("core_" if n in S.S_SETS else "ctrl_") + n
        texts = [s["prompt"] for s in ds[n]["sentences"]]
        for s0 in range(0, len(texts), S.SHARD):
            chunk = texts[s0:s0 + S.SHARD]
            # Two recipes: before hour-64 amendment 2 the digest had no batch size; the core and
            # control batches never changed (S.BATCH), so either one names the same content.
            recipes = {"pre_amendment_2": [cfg["repo"], True, meta["captured_layers"], chunk],
                       "post_amendment_2": [cfg["repo"], True, meta["captured_layers"], S.BATCH, chunk]}
            got = str(np.load(out / "shards" / f"{prefix}_{s0:04d}.npz")["digest"])
            match = [k for k, r in recipes.items()
                     if hashlib.sha256(json.dumps(r).encode()).hexdigest()[:16] == got]
            if not match:
                raise SystemExit(f"{key}: hour-64 shard {prefix}_{s0:04d} fails its digest")
            DIGEST_RECIPES.setdefault(key, set()).add(match[0])
    core = {n: X._load(out, f"core_{n}", len(ds[n]["sentences"]), "final_token") for n in S.S_SETS}
    core_e = {n: X._load(out, f"core_{n}", len(ds[n]["sentences"]), "embed_mean") for n in S.S_SETS}
    ctrl = {n: X._load(out, f"ctrl_{n}", len(ds[n]["sentences"]), "final_token") for n in X.CONTROL_SETS}
    cats = {n: [x["category"] for x in ds[n]["sentences"]] for n in S.S_SETS}
    return meta["captured_layers"], core, core_e, ctrl, cats


def _index(rows):
    """Row indices: base[b], shame[a][b], witness[a][b] over the 40 bases, and base categories."""
    bids = [r["base_id"] for r in rows if r["arm"] == "base"]
    pos = {(r["base_id"], r["author"], r["arm"]): i for i, r in enumerate(rows)}
    base = np.array([pos[(b, None, "base")] for b in bids])
    sh = {a: np.array([pos[(b, a, "shame")] for b in bids]) for a in AUTHORS}
    wi = {a: np.array([pos[(b, a, "witness")] for b in bids]) for a in AUTHORS}
    is_a1 = np.array([b.startswith("A1") for b in bids])
    return bids, base, sh, wi, is_a1


def _deltas(z, sh, wi):
    return {a: z[sh[a]] - z[wi[a]] for a in AUTHORS}


def analyze_model(key: str, rows, val) -> dict:
    layers, core, core_e, ctrl, cats = _hour64_stacks(key)
    col = {L: i for i, L in enumerate(layers)}
    mine = json.loads((OUT / key / "meta.json").read_text())
    if mine["captured_layers"] != layers or [r["text"] for r in mine["items"]] != [r["text"] for r in rows]:
        raise SystemExit(f"{key}: extraction meta does not match items or hour-64 layers")
    ft = X._load(OUT / key, "sp", len(rows), "final_token")
    em = X._load(OUT / key, "sp", len(rows), "embed_mean")
    screen = json.loads((X.OUT / key / "summary.json").read_text())["screen_layer"]
    bids, base, sh, wi, is_a1 = _index(rows)
    dval = {a: val[sh[a]] - val[wi[a]] for a in AUTHORS}
    rng = np.random.default_rng(SEED)

    fv = S.build_vectors(core_e, cats, {})["s2_pain_vector"]
    floor_z = S.zscore_pool(em @ S.unit(fv))
    floor_d = _deltas(floor_z, sh, wi)

    curve = []
    cells = {}
    for L in layers:
        i = col[L]
        v = S.build_vectors({n: core[n][:, i] for n in S.S_SETS}, cats,
                            {n: ctrl[n][:, i] for n in X.CONTROL_SETS})["s2_pain_vector"]
        z = S.zscore_pool(ft[:, i] @ S.unit(v))
        d = _deltas(z, sh, wi)
        posctl = float(z[base[is_a1]].mean() - z[base[~is_a1]].mean())
        # nulls: |mean delta| per author and |positive control| on random and shuffled directions
        rnull = {a: [] for a in AUTHORS}; rpos = []
        for _ in range(N_RAND):
            zr = S.zscore_pool(ft[:, i] @ S.unit(rng.standard_normal(ft.shape[-1])))
            for a, dd in _deltas(zr, sh, wi).items():
                rnull[a].append(abs(dd.mean()))
            rpos.append(abs(zr[base[is_a1]].mean() - zr[base[~is_a1]].mean()))
        snull = {a: [] for a in AUTHORS}; spos = []
        for _ in range(N_SHUF if L == screen else N_SHUF_CURVE):  # amendment 1
            c2 = {n: list(rng.permutation(cats[n])) for n in S.S_SETS}
            vs = S.build_vectors({n: core[n][:, i] for n in S.S_SETS}, c2, {})["s2_pain_vector"]
            zs = S.zscore_pool(ft[:, i] @ S.unit(vs))
            for a, dd in _deltas(zs, sh, wi).items():
                snull[a].append(abs(dd.mean()))
            spos.append(abs(zs[base[is_a1]].mean() - zs[base[~is_a1]].mean()))
        row = {"layer": L, "positive_control": posctl,
               "positive_control_rand_q95": float(np.quantile(rpos, .95)),
               "positive_control_shuf_q95": float(np.quantile(spos, .95)),
               "rewording_floor": float(z[wi["claude"]].mean() + z[wi["gpt"]].mean()) / 2 - float(z[base].mean()),
               "authors": {}}
        row["positive_control_pass"] = bool(posctl > max(row["positive_control_rand_q95"],
                                                         row["positive_control_shuf_q95"]))
        for a in AUTHORS:
            dd = d[a]
            q_r, q_s = float(np.quantile(rnull[a], .95)), float(np.quantile(snull[a], .95))
            row["authors"][a] = {"delta": float(dd.mean()),
                                 "delta_A1": float(dd[is_a1].mean()), "delta_D": float(dd[~is_a1].mean()),
                                 "rand_q95": q_r, "shuf_q95": q_s,
                                 "clears_nulls": bool(abs(dd.mean()) > max(q_r, q_s)),
                                 "rewording_floor": float((z[wi[a]] - z[base]).mean())}
            if L == screen:
                net = dd - floor_d[a]
                al, be = alpha_fit(dd, dval[a])
                cell = dict(row["authors"][a])
                cell.update({
                    "p": signflip_p(dd, rng),
                    "p_D": signflip_p(dd[~is_a1], rng), "p_A1": signflip_p(dd[is_a1], rng),
                    "ci": boot_ci(lambda ix: dd[ix].mean(), 40, rng),
                    "floor_delta": float(floor_d[a].mean()),
                    "network_contribution": float(net.mean()),
                    "network_contribution_ci": boot_ci(lambda ix: net[ix].mean(), 40, rng),
                    "alpha": al, "beta": be,
                    "alpha_ci": boot_ci(lambda ix: alpha_fit(dd[ix], dval[a][ix])[0], 40, rng),
                    "per_base_delta": dd.tolist()})
                cell["dval_range"] = [float(dval[a].min()), float(dval[a].max())]
                cell["tracks_shame"] = tracks_shame(cell, row["positive_control_pass"])
                cells[a] = cell
        curve.append(row)
        print(f"  {key} L{L} done", flush=True)
    screen_row = next(r for r in curve if r["layer"] == screen)
    return {"model": X.MODELS[key]["repo"], "screen_layer": screen,
            "positive_control_pass": screen_row["positive_control_pass"],
            "cells": cells, "curve": curve, "base_ids": bids, "device": mine.get("device", "ndif"),
            "hour64_digest_recipes": sorted(DIGEST_RECIPES.get(key, ()))}


def decide(rep: dict) -> dict:
    inst = [k for k in ("g2b_it", "l70_it") if k in rep]
    if len(inst) < 2:
        return {"status": "incomplete", "why": f"instruct models analysed: {inst}"}
    readable = [k for k in inst if rep[k]["positive_control_pass"]]
    if not readable:
        return {"status": "open", "why": "both instruct models fail the positive control"}
    tracks = {(k, a): rep[k]["cells"][a]["tracks_shame"] for k in readable for a in AUTHORS}
    if len(readable) == 2 and all(tracks.values()):
        return {"status": "holds", "cells": {f"{k}/{a}": v for (k, a), v in tracks.items()}}
    if (len(readable) == 2 and not any(tracks.values())
            and all(rep[k]["cells"][a]["alpha_ci"][0] <= 0 for k in readable for a in AUTHORS)):
        return {"status": "falsified", "cells": {f"{k}/{a}": v for (k, a), v in tracks.items()}}
    return {"status": "narrowed", "unreadable": [k for k in inst if k not in readable],
            "cells": {f"{k}/{a}": v for (k, a), v in tracks.items()}}


def analyze() -> None:
    rows = items()
    vdoc = json.loads((OUT / "valence.json").read_text())
    if vdoc["texts"] != [r["text"][: -len(" I feel:")] for r in rows]:
        raise SystemExit("valence file does not match the items")
    val = np.array(vdoc["valence"])
    rep = {}
    for key in X.MODELS:
        if (OUT / key / "meta.json").exists():
            rep[key] = analyze_model(key, rows, val)
    post = {}
    for fam, (b, it) in {"gemma2_2b": ("g2b", "g2b_it"), "llama31_70b": ("l70", "l70_it")}.items():
        if b in rep and it in rep:
            rng = np.random.default_rng(SEED + 1)
            post[fam] = {}
            for a in AUTHORS:
                diff = np.array(rep[it]["cells"][a]["per_base_delta"]) - np.array(rep[b]["cells"][a]["per_base_delta"])
                post[fam][a] = {"delta_post": float(diff.mean()),
                                "ci": boot_ci(lambda ix: diff[ix].mean(), 40, rng)}
    summary = {"models": rep, "delta_post": post, "decision": decide(rep),
               "valence_model": {k: vdoc[k] for k in ("model", "revision")}}
    (OUT / "summary.json").write_text(json.dumps(summary, indent=1))
    print(json.dumps(summary["decision"], indent=1))


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "valence":
        valence()
    elif cmd == "extract":
        extract(sys.argv[2])
    elif cmd == "analyze":
        analyze()
    else:
        raise SystemExit(__doc__)
