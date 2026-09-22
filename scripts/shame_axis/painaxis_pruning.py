"""Is the pain axis sparse? The pruning curve, after n90 was retired.

Pre-registered in `research/shame-axis/notes/sparsity_prereg.md` and its hour-57 addendum, both
committed before this script produced a number. Offline: SAEs and activation stacks are on disk.

The first attempt measured concentration as "features to 90% of the mass" and the positive control
killed it -- a contrast with exactly one real feature in it still read n90 ~ 400, because a
difference in means between two groups of ~250 in 16,384 dimensions is dense in its noise alone.
This is the statistic arXiv:2602.00986 actually uses: rank features on train, score with the top k
on held-out items, report the whole curve.

Usage:  python scripts/shame_axis/painaxis_pruning.py     # .venv
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from painaxis_sparsity import (CONTROL, PAIN, decode, encode, load_core,  # noqa: E402
                               load_sae)

ROOT = pathlib.Path(__file__).resolve().parents[2]
OUT = ROOT / "research/shame-axis/results/painaxis_sparsity"

KS = [1, 2, 5, 10, 25, 50, 100, 164, 250, 500, 1000, 2000, 4000, 8000, 16384]
ONE_PCT_K = 164
N_FOLDS = 5
N_PERM = 200
N_RANDOM = 50
SEED = 20260922
POINTS = [(9, "16k", "47"), (20, "16k", "47"), (31, "16k", "43"),
          (20, "16k", "14"), (20, "16k", "25"), (20, "16k", "91"), (20, "16k", "189"),
          (20, "131k", "43")]


def auc(scores: np.ndarray, labels: np.ndarray) -> float:
    """Mann-Whitney AUC with mid-ranks for ties."""
    n1, n0 = int(labels.sum()), int((~labels).sum())
    if n1 == 0 or n0 == 0:
        return float("nan")
    order = np.argsort(scores, kind="mergesort")
    ranks = np.empty(scores.size, dtype=float)
    s = scores[order]
    i = 0
    while i < s.size:                     # mid-rank ties
        j = i
        while j + 1 < s.size and s[j + 1] == s[i]:
            j += 1
        ranks[order[i:j + 1]] = 0.5 * (i + j) + 1.0
        i = j + 1
    return float((ranks[labels].sum() - n1 * (n1 + 1) / 2.0) / (n1 * n0))


def pruning_curve(f: np.ndarray, y: np.ndarray, folds: np.ndarray, ks: list[int],
                  pick: str = "top", rng: np.random.Generator | None = None) -> dict[int, float]:
    """Held-out AUC using only k features. Features are ranked on the TRAIN fold and scored on the
    TEST fold, so no feature is ever selected on the data it is evaluated on (non-negotiable 4)."""
    n_feat = f.shape[1]
    out = {}
    for k in ks:
        k = min(k, n_feat)
        scores = np.zeros(f.shape[0])
        for fold in np.unique(folds):
            te, tr = folds == fold, folds != fold
            d = f[tr][y[tr]].mean(0) - f[tr][~y[tr]].mean(0)
            if pick == "top":
                idx = np.argsort(np.abs(d))[::-1][:k]
            else:
                idx = rng.choice(n_feat, size=k, replace=False)
            w = d[idx]
            nrm = np.linalg.norm(w)
            scores[te] = f[te][:, idx] @ (w / nrm if nrm > 0 else w)
        out[k] = auc(scores, y)
    return out


def run_point(acts, cats, layer, width, l0, extraction, rng) -> dict:
    sae = load_sae(layer, width, l0)
    keep = np.isin(cats, PAIN + CONTROL)
    A, c = acts[keep], cats[keep]
    y = np.isin(c, PAIN)
    x = A[:, layer, :].astype(np.float32)

    # ---- amended gate A -------------------------------------------------------------------
    fvu_idx = {}
    for off in (-2, -1, 0, 1, 2):
        i = layer + off
        if 0 <= i < acts.shape[1]:
            xi = A[:, i, :].astype(np.float32)
            fvu_idx[str(i)] = float(((xi - decode(sae, encode(sae, xi))) ** 2).sum() / (xi ** 2).sum())
    best = int(min(fvu_idx, key=fvu_idx.get))
    f = encode(sae, x)
    l0_hit = float((f > 0).sum()) / x.shape[0]
    l0_adv = float(l0)
    gate_a = {"fvu_vs_origin_by_index": fvu_idx, "best_index": best,
              "achieved_l0": l0_hit, "advertised_l0": l0_adv,
              "passes": bool(fvu_idx[str(layer)] < 0.35 and best == layer
                             and abs(l0_hit - l0_adv) / l0_adv < 0.25)}

    folds = rng.permutation(np.arange(x.shape[0]) % N_FOLDS)

    # ---- gate B: the corrected plant, which must peak at k = 1 ------------------------------
    fc_x = x[~y]
    hm = np.zeros(fc_x.shape[0], dtype=bool)
    hm[rng.permutation(fc_x.shape[0])[: fc_x.shape[0] // 2]] = True
    j = int(rng.integers(sae["W_dec"].shape[0]))
    planted = fc_x.copy()
    planted[hm] += 0.2 * float(np.linalg.norm(fc_x, axis=1).mean()) * sae["W_dec"][j]
    pf = encode(sae, planted)
    pfolds = rng.permutation(np.arange(planted.shape[0]) % N_FOLDS)
    pcurve = pruning_curve(pf, hm, pfolds, [1, 10, 100, 16384])
    gate_b = {"planted_feature": j, "curve": {str(k): v for k, v in pcurve.items()},
              "passes": bool(pcurve[1] > 0.9)}

    # ---- treatment, and their own control: random-k at the same k ---------------------------
    obs = pruning_curve(f, y, folds, KS)
    rnd = {k: [] for k in KS}
    for _ in range(N_RANDOM):
        cv = pruning_curve(f, y, folds, KS, pick="random", rng=rng)
        for k in KS:
            rnd[k].append(cv[k])

    # ---- label permutation, at the full dictionary ------------------------------------------
    perm_full = []
    for _ in range(N_PERM):
        yp = rng.permutation(y)
        perm_full.append(pruning_curve(f, yp, folds, [ONE_PCT_K])[ONE_PCT_K])

    # ---- no-signal floor: control vs control ------------------------------------------------
    fc = f[~y]
    split = pruning_curve(fc, hm, pfolds, [ONE_PCT_K, 16384])

    full = obs[min(16384, f.shape[1])]
    at1pct = obs[ONE_PCT_K]
    retention = (at1pct - 0.5) / (full - 0.5) if full > 0.5 else float("nan")
    return {
        "layer": layer, "width": width, "l0": l0, "extraction": extraction,
        "n_features": int(f.shape[1]), "n_pain": int(y.sum()), "n_control": int((~y).sum()),
        "gate_a": gate_a, "gate_b": gate_b,
        "curve": {str(k): obs[k] for k in obs},
        "random_k": {str(k): {"mean": float(np.mean(rnd[k])), "p95": float(np.percentile(rnd[k], 95))}
                     for k in KS},
        "perm_null_at_1pct": {"mean": float(np.mean(perm_full)),
                              "p95": float(np.percentile(perm_full, 95)),
                              "max": float(np.max(perm_full))},
        "split_half_floor": {str(k): v for k, v in split.items()},
        "auc_full": full, "auc_at_1pct": at1pct, "retention_at_1pct": retention,
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    rows = []
    for extraction in ["final_token", "mean"]:
        acts, cats = load_core(extraction)
        for layer, width, l0 in POINTS:
            r = run_point(acts, cats, layer, width, l0, extraction, rng)
            rows.append(r)
            g = f"A:{'ok' if r['gate_a']['passes'] else 'FAIL'} B:{'ok' if r['gate_b']['passes'] else 'FAIL'}"
            print(f"{extraction:12s} L{layer:<2d} {width:>5s} l0={l0:<4s} {g:14s} "
                  f"AUC full {r['auc_full']:.4f}  @164 {r['auc_at_1pct']:.4f} "
                  f"(rand-k {r['random_k'][str(ONE_PCT_K)]['mean']:.4f}, "
                  f"perm {r['perm_null_at_1pct']['mean']:.4f})  retention {r['retention_at_1pct']:.3f}",
                  flush=True)
    (OUT / "pruning.json").write_text(json.dumps(rows, indent=1))

    ok = [r for r in rows if r["gate_a"]["passes"] and r["gate_b"]["passes"]]
    bad = [r for r in rows if r not in ok]
    print(f"\nwrote {OUT/'pruning.json'}")
    if bad:
        print(f"{len(bad)} of {len(rows)} points fail a gate and are not interpretable:")
        for r in bad:
            print(f"  {r['extraction']:12s} L{r['layer']:<2d} {r['width']:>5s} l0={r['l0']:<4s}  "
                  f"A {r['gate_a']['passes']} (fvu {r['gate_a']['fvu_vs_origin_by_index'][str(r['layer'])]:.3f}, "
                  f"L0 {r['gate_a']['achieved_l0']:.1f} vs {r['gate_a']['advertised_l0']:.0f})  "
                  f"B {r['gate_b']['passes']} (k=1 AUC {r['gate_b']['curve']['1']:.3f})")
    if ok:
        print(f"\nVERDICT (pre-registered: sparse if the top {ONE_PCT_K} features retain >= 90% "
              f"of the full-dictionary AUC gain over chance, held out)")
        for r in ok:
            v = "SPARSE" if r["retention_at_1pct"] >= 0.90 else "DENSE"
            print(f"  {r['extraction']:12s} L{r['layer']:<2d} {r['width']:>5s} l0={r['l0']:<4s}  "
                  f"retention {r['retention_at_1pct']:.3f}  -> {v}")


if __name__ == "__main__":
    main()
