"""Open problem 4i: does the h8 readout's permutation arm really sit below its null?

Hour 48 recorded the permutation arm below chance on 25 of 25 replication rows (mean -0.117, sign
test p ~ 3e-8) and attributed it to the uncentered cosine ranking being "partly a norm ranking".
Two facts make that attribution doubtful before any model is run:

* the labels are shuffled BEFORE the level means are fitted, so the permuted directions are
  exchangeable across levels, and the arm's mean over target items is then exactly chance in
  expectation under ANY scoring function, norm-sensitive or not;
* every row was run with `seed=0`, and `readout_battery`'s permutation RNG depends only on the seed
  and the training-set size, so every grid of the same shape received the SAME shuffles. The 25
  rows are a few draw sets counted many times, not 25 independent observations.

This script re-extracts each Qwen2.5-1.5B grid live through `build_stack` (every extraction
assertion runs), gates seed 0 against the committed rows bit-for-bit, then re-runs ONLY the
permutation arm at many independent seeds. If the arm is biased, its mean over seeds stays below
chance; if hour 48's residue was the seed-0 draw set, the mean over seeds sits at chance and seed 0
is an outlier explained by how much its shuffles happened to agree with the true labels.

Nothing in the battery is modified. The treatment, random and no-patch arms are not re-run: the
treatment and no-patch arms draw no random numbers, and the question here is about one arm's null.

    flock /tmp/model-research-local.lock .venv/bin/python scripts/narrative/permutation_seed_audit.py \
        --model <Qwen2.5-1.5B snapshot dir> --seeds 64
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import pathlib
import platform
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
RESULTS = ROOT / "research/narrative/results"
CACHE = ROOT / "cache/permutation_seed_audit"

# The grids with committed Qwen2.5-1.5B rows: hour 50's five live grids, plus the reference grid
# hour 48 measured on the cached path.
GRIDS = ["narrative_factors_v2", "narrative_factors_v1", "narrative_factors_gpt_v1",
         "narrative_theme_gpt_v1", "narrative_theme_v1", "narrative_mood_v1"]
N_PERM = 32  # hour 48's setting everywhere
DRAW_SWEEP = (32, 64, 128, 256)


def committed_rows() -> dict:
    """{(grid, factor): (permutation arm value, layer, source)} from the committed Qwen-1.5B rows."""
    out = {}
    for r in json.loads((RESULTS / "phase2_h8_replications.json").read_text()):
        if r["model"] == "Qwen2.5-1.5B":
            out[(r["grid"], r["factor"])] = (r["arms"]["permutation"], r["layer"], "h48 cached")
    for g in json.loads((RESULTS / "phase2_qwen_live_replications.json").read_text()):
        for r in g["rows"]:
            out[(g["grid"], r["factor"])] = (r["arms"]["permutation"], r["layer"], "h50 live")
    return out


def overlap_excess(gridspec: dict, n_perm: int, seed: int) -> dict:
    """Per draw, how far the shuffled labels still agree with the true ones, reproducing
    `readout_battery`'s permutation RNG exactly (same generator, same call order, same sizes).

    For factor n and level l, f_lm is the fraction of items shuffled INTO level l whose true level
    is m. The permuted direction for l is then sum_m f_lm * D_m (the true level directions sum to
    zero on a balanced grid), so its alignment with the true contrast is f_ll - mean_{m != l} f_lm.
    Zero in expectation; positive means the shuffle leaked some of the true labels back in.
    Returned per factor as an [n_perm] vector averaged over scenes and levels, plus `composed`, the
    sum over factors (the composed direction is a sum of factor directions).
    """
    F = gridspec["factors"]
    names = list(F)
    S = gridspec["scenes"]
    combos = list(itertools.product(*[F[n] for n in names]))
    perm_rng = np.random.default_rng(1000 + seed)
    out = {n: np.zeros(n_perm) for n in names}
    for s in S:
        labels = [c for t in S if t != s for c in combos]
        true = np.array(labels, dtype=object)
        for p in range(n_perm):
            sh = true[perm_rng.permutation(len(labels))]
            for i, n in enumerate(names):
                acc = []
                for lvl in F[n]:
                    into = true[[k for k in range(len(sh)) if sh[k][i] == lvl]]
                    f = {m: float(np.mean([c[i] == m for c in into])) for m in F[n]}
                    acc.append(f[lvl] - np.mean([f[m] for m in F[n] if m != lvl]))
                out[n][p] += float(np.mean(acc)) / len(S)
    out["composed"] = sum(out[n] for n in names)
    return out


def stack_for(lm, grid: str, model_dir: str):
    """The live stack, cached on disk keyed by grid and checkpoint so a rerun costs no forward
    passes. The cache is a convenience; the gate below re-checks it against the committed rows."""
    from lsx.narrative import phase2

    gridspec = phase2.normalized_grid(grid)
    key = hashlib.sha256(f"{grid}|{model_dir}".encode()).hexdigest()[:16]
    path = CACHE / f"{grid}_{key}.npz"
    if path.exists():
        z = np.load(path)
        return gridspec, {k: z[k] for k in gridspec["spans"]}, {"cached": str(path.relative_to(ROOT))}
    X, stack = phase2.stack_matrix_from_build_stack(lm, gridspec)
    CACHE.mkdir(parents=True, exist_ok=True)
    np.savez(path, **X)
    return gridspec, X, {"acts_digest": stack.provenance.get("acts_digest"),
                         "stack_signature": stack.provenance.get("stack_signature")}


def perm_arm_means(X: dict, gridspec: dict, layer: int, seed: int) -> dict:
    """The permutation arm exactly as `_replication_rows_core` computes it (its mean over every
    draw and item), plus each draw's mean, for one seed."""
    from lsx.narrative import phase2

    b = phase2.readout_battery(X, gridspec, layer, n_perm=N_PERM, n_rand=0, seed=seed)
    out = {}
    for factor, arm in [("composed", b["composed"]), *b["B"].items()]:
        draws = [float(np.mean(d)) for d in arm["perm"]]
        out[factor] = {"value": float(np.mean(np.concatenate(arm["perm"]))), "draw_means": draws}
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--model", required=True, help="Qwen2.5-1.5B snapshot directory (pins weights and tokenizer)")
    ap.add_argument("--revision", default="8faed761d45a263340a0528343f099c05c9a4323")
    ap.add_argument("--seeds", type=int, default=64)
    ap.add_argument("--out", default=str(RESULTS / "permutation_seed_audit.json"))
    args = ap.parse_args()

    import torch
    from lsx import LM
    from lsx.narrative import phase2

    torch.manual_seed(0)
    lm = LM.from_pretrained(args.model, device="cpu", dtype=torch.float32)
    ref = committed_rows()
    t0 = time.time()
    report = {"model": "Qwen/Qwen2.5-1.5B", "revision": args.revision,
              "device": "cpu", "dtype": "float32",
              "environment": f"claude.ai cloud container, {platform.platform()}, torch {torch.__version__}",
              "n_perm": N_PERM, "seeds": list(range(args.seeds)), "grids": {}}

    for grid in GRIDS:
        gridspec, X, prov = stack_for(lm, grid, args.model)
        n_layers = next(iter(X.values())).shape[0]
        layer = phase2.mid_depth(n_layers)
        per_seed = [perm_arm_means(X, gridspec, layer, s) for s in range(args.seeds)]
        ov = {s: overlap_excess(gridspec, N_PERM, s) for s in range(args.seeds)}
        chance = {"composed": (len(list(itertools.product(*gridspec["factors"].values()))) + 1) / 2,
                  **{n: (len(v) + 1) / 2 for n, v in gridspec["factors"].items()}}
        rows = {}
        for factor in chance:
            vals = np.array([ps[factor]["value"] for ps in per_seed])
            dev = vals - chance[factor]
            # the gate: seed 0 must be the committed number, or nothing below means anything
            committed, c_layer, source = ref.get((grid, factor), (None, None, None))
            gate = None if committed is None else bool(c_layer == layer and abs(vals[0] - committed) < 1e-9)
            if gate is False:
                raise SystemExit(f"GATE FAILED {grid}/{factor}: seed 0 reads {vals[0]!r}, "
                                 f"committed {committed!r} ({source}, layer {c_layer} vs {layer})")
            # within-seed: does the draw's label overlap predict the draw's mean?
            x = np.concatenate([ov[s][factor] for s in range(args.seeds)])
            y = np.concatenate([per_seed[s][factor]["draw_means"] for s in range(args.seeds)]) - chance[factor]
            slope, intercept = np.polyfit(x, y, 1)
            seed_ov = np.array([ov[s][factor].mean() for s in range(args.seeds)])
            se = float(dev.std(ddof=1) / np.sqrt(len(dev)))
            rows[factor] = {
                "chance": chance[factor], "committed_seed0": committed, "committed_source": source,
                "seed0_reproduced": gate,
                "seed0_dev": float(dev[0]),
                "mean_dev_over_seeds": float(dev.mean()), "se_over_seeds": se,
                "t_vs_chance": float(dev.mean() / se) if se > 0 else None,
                "frac_seeds_below_chance": float(np.mean(dev < 0)),
                "seed0_percentile": float(np.mean(dev <= dev[0])),
                "seed0_overlap_excess": float(seed_ov[0]),
                "overlap_excess_sd_over_seeds": float(seed_ov.std(ddof=1)),
                "draw_level_fit": {"slope": float(slope), "intercept_at_zero_overlap": float(intercept),
                                   "r": float(np.corrcoef(x, y)[0, 1]), "n_draws": int(len(x))},
                "seed_level_r_overlap_vs_dev": float(np.corrcoef(seed_ov, dev)[0, 1]),
                "per_seed_dev": dev.tolist(),
            }
        # Hour 48's own prediction, tested: "the band shrinks with draws and the bias does not, so
        # this arm would be refused at roughly 60-100 draws". Seed 0, more draws, the measured band
        # `pooled_draw_arm` uses (3 sd(draw means) / sqrt(n_draws)).
        sweep = {}
        for n_perm in DRAW_SWEEP:
            b = phase2.readout_battery(X, gridspec, layer, n_perm=n_perm, n_rand=0, seed=0)
            for factor, arm in [("composed", b["composed"]), *b["B"].items()]:
                means = np.array([np.mean(d) for d in arm["perm"]])
                dev = float(np.mean(np.concatenate(arm["perm"])) - chance[factor])
                band = float(3 * means.std(ddof=1) / np.sqrt(len(means)))
                sweep.setdefault(factor, []).append(
                    {"n_perm": n_perm, "dev": dev, "band": band, "refused": abs(dev) > band})
        for factor in rows:
            rows[factor]["seed0_draw_sweep"] = sweep[factor]
        report["grids"][grid] = {"layer": layer, "n_layers": n_layers, "provenance": prov, "rows": rows}
        print(f"{grid}: " + "  ".join(f"{f} seed0 {r['seed0_dev']:+.3f} mean {r['mean_dev_over_seeds']:+.4f}"
                                      f"±{r['se_over_seeds']:.4f}" for f, r in rows.items()), flush=True)

    # The across-row question hour 48 asked, asked properly: with seed 0 everywhere the rows share
    # draws; with an independent seed per row they do not. How often are ALL rows below chance?
    all_rows = [(g, f, np.array(r["per_seed_dev"])) for g, G in report["grids"].items() for f, r in G["rows"].items()]
    shared = np.array([[d[s] < 0 for _, _, d in all_rows] for s in range(args.seeds)])
    rng = np.random.default_rng(4)
    indep = np.array([[d[rng.integers(args.seeds)] < 0 for _, _, d in all_rows] for _ in range(10000)])
    # one seed per GRID: a grid's rows share their draws by construction (one permuted fit serves
    # every factor), which is legitimate; what is not is sharing them ACROSS grids
    grids = list(report["grids"])
    per_grid = []
    for _ in range(10000):
        pick = {g: rng.integers(args.seeds) for g in grids}
        per_grid.append([d[pick[g]] < 0 for g, _, d in all_rows])
    per_grid = np.array(per_grid)
    report["across_rows"] = {
        "n_rows": len(all_rows),
        "seed0_rows_below": int(shared[0].sum()),
        "shared_seed_all_below_rate": float(np.mean(shared.all(axis=1))),
        "shared_seed_mean_rows_below": float(shared.sum(axis=1).mean()),
        "independent_seed_all_below_rate": float(np.mean(indep.all(axis=1))),
        "independent_seed_mean_rows_below": float(indep.sum(axis=1).mean()),
        "seed_per_grid_all_below_rate": float(np.mean(per_grid.all(axis=1))),
        "mean_dev_seed0": float(np.mean([d[0] for _, _, d in all_rows])),
        "mean_dev_over_seeds": float(np.mean([d.mean() for _, _, d in all_rows])),
    }
    report["wall_seconds"] = round(time.time() - t0, 1)
    pathlib.Path(args.out).write_text(json.dumps(report, indent=1) + "\n")
    print(json.dumps(report["across_rows"], indent=1))


if __name__ == "__main__":
    main()
