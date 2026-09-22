"""Is the pain axis sparse? The Gemma Scope reading.

Pre-registered in `research/shame-axis/notes/sparsity_prereg.md`, committed before a single number
existed. Offline: the SAEs and the scenario activation stacks are both already on disk, so this
touches neither NDIF nor the network.

arXiv:2602.00986 finds reward information in under 1% of neurons, causally load-bearing. The pain
axis is a dense difference-in-means direction with a 63% lexical floor. If aversive valence is a
subsystem of the same kind, it is concentrated; if the axis is a lexical-plus-self/other readout,
it is spread. Sparsity discriminates.

Usage:  python scripts/shame_axis/painaxis_sparsity.py        # .venv
"""
from __future__ import annotations

import glob
import json
import pathlib

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
SHARDS = ROOT / "research/shame-axis/results/painaxis_scenarios/shards"
DATASETS = ROOT / "research/shame-axis/prompts/external/pain_axis/3.1_pain_and_control_datasets.json"
SAE_ROOT = ROOT / "cache/hf/hub/models--google--gemma-scope-9b-it-res/snapshots"
OUT = ROOT / "research/shame-axis/results/painaxis_sparsity"

PAIN = ["A1", "A2", "A3", "A4", "A5"]
CONTROL = ["B", "C1", "C2", "D", "E"]
CORE_SETS = ["S1_1P", "S2_1P", "ControlSupplement_1P"]
EXTRACTIONS = ["final_token", "mean"]
N_PERM = 200
ONE_PCT = 164          # under 1% of a 16,384-feature dictionary; the pre-registered threshold
SEED = 20260921


# ------------------------------------------------------------------------------------ loading
def load_core(extraction: str) -> tuple[np.ndarray, np.ndarray]:
    """Returns acts [n, 42, 3584] and categories [n], in prompt order across the core sets."""
    ds = json.loads(DATASETS.read_text())["datasets"]
    acts, cats = [], []
    for name in CORE_SETS:
        shards = sorted(glob.glob(str(SHARDS / f"core_{name}_*.npz")))
        if not shards:
            raise SystemExit(f"no shards for core_{name}")
        a = np.concatenate([np.load(s)[extraction] for s in shards], axis=0)
        c = [s["category"] for s in ds[name]["sentences"]]
        if len(c) != a.shape[0]:
            raise SystemExit(f"{name}: {a.shape[0]} activations but {len(c)} categories")
        acts.append(a)
        cats.extend(c)
    return np.concatenate(acts, axis=0), np.array(cats)


def load_sae(layer: int, width: str, l0: str) -> dict:
    p = glob.glob(str(SAE_ROOT / f"*/layer_{layer}/width_{width}/average_l0_{l0}/params.npz"))
    if not p:
        raise SystemExit(f"no SAE at layer {layer} width {width} l0 {l0}")
    z = np.load(p[0])
    return {k: z[k].astype(np.float32) for k in ("W_enc", "W_dec", "b_enc", "b_dec", "threshold")}


def encode(sae: dict, x: np.ndarray) -> np.ndarray:
    """JumpReLU: relu(pre) gated on pre > threshold."""
    pre = x @ sae["W_enc"] + sae["b_enc"]
    return np.where(pre > sae["threshold"], np.maximum(pre, 0.0), 0.0)


def decode(sae: dict, f: np.ndarray) -> np.ndarray:
    return f @ sae["W_dec"] + sae["b_dec"]


def fvu(sae: dict, x: np.ndarray) -> float:
    """Fraction of variance unexplained by the SAE reconstruction."""
    r = decode(sae, encode(sae, x))
    return float(((x - r) ** 2).sum() / ((x - x.mean(0)) ** 2).sum())


# ------------------------------------------------------------------------------ concentration
def concentration(f_diff: np.ndarray) -> dict:
    mass = np.abs(f_diff)
    total = float(mass.sum())
    if total <= 0:
        return {"n50": -1, "n90": -1, "pr": -1.0, "topk": {}, "total_mass": 0.0}
    order = np.argsort(mass)[::-1]
    cum = np.cumsum(mass[order]) / total
    sq = f_diff ** 2
    p = sq / sq.sum()
    return {
        "n50": int(np.searchsorted(cum, 0.50) + 1),
        "n90": int(np.searchsorted(cum, 0.90) + 1),
        "pr": float(1.0 / np.sum(p ** 2)),
        "topk": {str(k): float(cum[min(k, cum.size) - 1]) for k in (1, 5, 10, 50, 100, 500)},
        "total_mass": total,
        "argmax": int(order[0]),
    }


def diff_from_feats(f: np.ndarray, pain_mask: np.ndarray) -> np.ndarray:
    """The encode does not depend on the labels, so it is done once and the permutations move the
    mask over the already-encoded matrix. Re-encoding per draw made the null 200x its own cost."""
    return f[pain_mask].mean(0) - f[~pain_mask].mean(0)


def feature_diff(sae: dict, x: np.ndarray, pain_mask: np.ndarray) -> np.ndarray:
    return diff_from_feats(encode(sae, x), pain_mask)


# ------------------------------------------------------------------------------------- report
def run_point(acts: np.ndarray, cats: np.ndarray, layer: int, width: str, l0: str,
              extraction: str, rng: np.random.Generator) -> dict:
    sae = load_sae(layer, width, l0)
    keep = np.isin(cats, PAIN + CONTROL)
    x_all, c_all = acts[keep], cats[keep]
    pain_mask = np.isin(c_all, PAIN)
    x = x_all[:, layer, :].astype(np.float32)

    # --- gate A: the capture convention ---------------------------------------------------
    gate_a = {}
    for off in (-1, 0, 1):
        idx = layer + off
        if 0 <= idx < acts.shape[1]:
            gate_a[str(idx)] = fvu(sae, x_all[:, idx, :].astype(np.float32))
    best = min(gate_a, key=gate_a.get)
    a_ok = (int(best) == layer) and gate_a[str(layer)] < 0.5

    # --- gate B: a planted single-feature contrast ------------------------------------------
    j = int(rng.integers(sae["W_dec"].shape[0]))
    scale = float(np.linalg.norm(x, axis=1).mean())
    planted = x.copy()
    planted[pain_mask] += scale * sae["W_dec"][j]
    c_planted = concentration(feature_diff(sae, planted, pain_mask))
    b_ok = c_planted["argmax"] == j and c_planted["n90"] <= 5

    # --- treatment ---------------------------------------------------------------------------
    f = encode(sae, x)
    obs = concentration(diff_from_feats(f, pain_mask))

    # --- nulls --------------------------------------------------------------------------------
    perm = []
    for _ in range(N_PERM):
        m = rng.permutation(pain_mask)
        perm.append(concentration(diff_from_feats(f, m)))
    fc = f[~pain_mask]
    half = rng.permutation(fc.shape[0])[: fc.shape[0] // 2]
    hm = np.zeros(fc.shape[0], dtype=bool)
    hm[half] = True
    split = concentration(diff_from_feats(fc, hm))

    def band(key):
        v = np.array([pp[key] for pp in perm], dtype=float)
        return {"mean": float(v.mean()), "p05": float(np.percentile(v, 5)),
                "p95": float(np.percentile(v, 95)), "min": float(v.min())}

    return {
        "layer": layer, "width": width, "l0": l0, "extraction": extraction,
        "n_pain": int(pain_mask.sum()), "n_control": int((~pain_mask).sum()),
        "n_features": int(sae["W_dec"].shape[0]),
        "gate_a": {"fvu_by_index": gate_a, "best_index": int(best), "passes": bool(a_ok)},
        "gate_b": {"planted_feature": j, "recovered": c_planted["argmax"],
                   "n90": c_planted["n90"], "passes": bool(b_ok)},
        "observed": obs,
        "perm_null": {"n50": band("n50"), "n90": band("n90"), "pr": band("pr")},
        "split_half_floor": {"n50": split["n50"], "n90": split["n90"], "pr": split["pr"]},
        "features_active_either_group": int((f.max(0) > 0).sum()),
    }


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)
    points = [(9, "16k", "47"), (20, "16k", "47"), (31, "16k", "43"),
              (20, "16k", "14"), (20, "16k", "25"), (20, "16k", "91"), (20, "16k", "189"),
              (20, "131k", "43")]
    rows = []
    for extraction in EXTRACTIONS:
        acts, cats = load_core(extraction)
        for layer, width, l0 in points:
            r = run_point(acts, cats, layer, width, l0, extraction, rng)
            rows.append(r)
            g = f"A:{'ok' if r['gate_a']['passes'] else 'FAIL'} B:{'ok' if r['gate_b']['passes'] else 'FAIL'}"
            print(f"{extraction:12s} L{layer:<2d} {width:>5s} l0={l0:<4s} {g:14s} "
                  f"FVU {r['gate_a']['fvu_by_index'][str(layer)]:.3f}  "
                  f"n90 {r['observed']['n90']:5d} (null {r['perm_null']['n90']['mean']:7.1f}, "
                  f"min {r['perm_null']['n90']['min']:7.1f})  PR {r['observed']['pr']:8.1f}",
                  flush=True)
    (OUT / "sparsity.json").write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {OUT/'sparsity.json'}")

    bad = [r for r in rows if not (r["gate_a"]["passes"] and r["gate_b"]["passes"])]
    if bad:
        print(f"\n!! {len(bad)} of {len(rows)} points FAIL a gate. Per the pre-registration those "
              f"points are not interpretable.")
    ok = [r for r in rows if r["gate_a"]["passes"] and r["gate_b"]["passes"]]
    if ok:
        print(f"\nVERDICT on the {len(ok)} interpretable points "
              f"(pre-registered threshold: 90% of the mass within ~{ONE_PCT} features)")
        for r in ok:
            n90, nullb = r["observed"]["n90"], r["perm_null"]["n90"]
            sparse = n90 <= ONE_PCT and n90 < nullb["p05"]
            print(f"  {r['extraction']:12s} L{r['layer']:<2d} {r['width']:>5s} l0={r['l0']:<4s}  "
                  f"n90 = {n90:5d} / {r['n_features']}  null [{nullb['p05']:.0f}, {nullb['p95']:.0f}]"
                  f"  -> {'SPARSE' if sparse else 'DENSE'}")


if __name__ == "__main__":
    main()
