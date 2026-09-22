"""Is the sparsity PAIN's, or the BASIS's? The reference distribution.

Pre-registered in `research/shame-axis/notes/sparsity_prereg.md`, "Addendum 2, hour 58", written
before this script produced a number. Offline: the SAEs and both activation stacks are on disk, so
this touches neither NDIF nor the network (the gemma tokenizer is read from the local HF cache).

Hour 57 found five features saturate the pain contrast. That number is uninterpretable alone -- an
SAE is trained to make things sparse, so a strong semantic contrast being recoverable from few
features may be the ordinary case. So: run the IDENTICAL pruning pipeline (5-fold, rank features on
train, score held-out, `final_token`) over every other binary split available on disk, and locate
pain in that reference distribution.

Per contrast: full-dictionary held-out AUC, and k90 = the smallest k in the KS grid whose retention
(auc_k - 0.5) / (auc_full - 0.5) reaches 0.90. A contrast with auc_full <= 0.65 has no well-defined
k90 and is reported as `weak`, shown but not counted.

Declared: sparsity is specific to pain only if pain's k90 is at or below the 10th percentile of k90
among contrasts whose full AUC is within +-0.05 of pain's. No contrast is selected on; the whole
scatter is the result.

Usage:  python scripts/shame_axis/painaxis_sparsity_reference.py      # .venv
"""
from __future__ import annotations

import glob
import json
import os
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from painaxis_pruning import KS, N_FOLDS, pruning_curve  # noqa: E402
from painaxis_sparsity import (CONTROL, PAIN, decode, encode, load_core,  # noqa: E402
                               load_sae)

ROOT = pathlib.Path(__file__).resolve().parents[2]
SCEN_SHARDS = ROOT / "research/shame-axis/results/painaxis_scenarios/shards"
SCEN_ORDER = ROOT / "research/shame-axis/results/painaxis_scenarios/scenario_order.json"
SCEN_JSON = ROOT / "research/shame-axis/prompts/external/pain_axis/4.1_self_other_420_scenarios.json"
OUT = ROOT / "research/shame-axis/results/painaxis_sparsity"

MODEL = "google/gemma-2-9b-it"
EXTRACTION = "final_token"
N_SCENARIOS = 420
POINTS = [(9, "16k", "47"), (20, "16k", "47"), (31, "16k", "43")]
SEED = 20260923

RETENTION = 0.90       # k90's threshold
WEAK_AUC = 0.65        # at or below this, k90 is not defined (pre-registered)
BAND = 0.05            # the comparison band around pain's full AUC
PCTL = 10              # pain must sit at or below this percentile of the band's k90

# `intensity` is a free-text field with 27 distinct values and 100 items missing it entirely.
# Only these four form an unambiguous ordinal scale; the split is taken inside them and every
# other item is out of the contrast. See the results note -- this is a judgment call the
# addendum did not make for us.
INTENSITY_LOW = ["mild", "moderate"]
INTENSITY_HIGH = ["high", "severe"]


# ------------------------------------------------------------------------------------ loading
def align_scenarios(order_ids: list, scenarios: list, n_rows: int) -> list:
    """Map shard row -> scenario metadata, and ASSERT the mapping rather than assume it.

    The extractor wrote `scenario_order.json` as the ids it actually fed the model, in row order,
    AFTER dropping anything their validator rejected. The row count must be 420 and every id must
    resolve, or the labels belong to different sentences than the activations do."""
    if len(order_ids) != n_rows:
        raise SystemExit(f"scenario_order has {len(order_ids)} ids but the shards have {n_rows} rows")
    if n_rows != N_SCENARIOS:
        raise SystemExit(f"expected {N_SCENARIOS} scenario rows, got {n_rows}")
    by_id = {c["id"]: c for c in scenarios}
    if len(by_id) != len(scenarios):
        raise SystemExit("scenario ids are not unique")
    missing = [i for i in order_ids if i not in by_id]
    if missing:
        raise SystemExit(f"{len(missing)} ids in the order file have no scenario: {missing[:5]}")
    return [by_id[i] for i in order_ids]


def load_scenarios() -> tuple[np.ndarray, list]:
    """Returns acts [420, 42, 3584] and the metadata aligned to its rows."""
    shards = sorted(glob.glob(str(SCEN_SHARDS / "scen_chat_*.npz")))
    if not shards:
        raise SystemExit("no scen_chat shards")
    acts = np.concatenate([np.load(s)[EXTRACTION] for s in shards], axis=0)
    meta = align_scenarios(json.loads(SCEN_ORDER.read_text()),
                           json.loads(SCEN_JSON.read_text()), acts.shape[0])
    return acts, meta


def token_counts(texts: list) -> np.ndarray:
    """Prompt length in TOKENS under the model's own tokenizer, from the local cache.

    `add_special_tokens=False` counts the text's own tokens; a constant offset could not change a
    median split, but it is said rather than left implicit."""
    os.environ.setdefault("HF_HOME", str(ROOT / "cache/hf"))
    os.environ.setdefault("HF_HUB_DISABLE_XET", "1")
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(MODEL)
    return np.array([len(tok(t, add_special_tokens=False)["input_ids"]) for t in texts])


# --------------------------------------------------------------------------------- contrasts
def median_split(values: np.ndarray) -> np.ndarray:
    """Top half vs bottom half by rank, so the two arms are exactly half the pool each even when
    the values tie. Ties are broken by row order (mergesort is stable), which is arbitrary but
    deterministic."""
    order = np.argsort(values, kind="mergesort")
    y = np.zeros(values.size, dtype=bool)
    y[order[values.size // 2:]] = True
    return y


def core_contrasts(cats: np.ndarray) -> list:
    """(name, rows, y) with `rows` the pool mask and `y` defined over the whole pool."""
    all_rows = np.ones(cats.size, dtype=bool)
    out = [(f"{c}_vs_rest", all_rows, cats == c) for c in PAIN + CONTROL]
    out.append(("pain", all_rows, np.isin(cats, PAIN)))
    return out


def scenario_contrasts(meta: list) -> list:
    cat = np.array([m["category"] for m in meta])
    persp = np.array([m["perspective"] for m in meta])
    inten = np.array([m.get("intensity") or "" for m in meta])
    all_rows = np.ones(len(meta), dtype=bool)

    out = [(f"{c}_vs_rest", all_rows, cat == c) for c in sorted(set(cat.tolist()))]
    out.append(("perspective_1P_vs_3P", all_rows, persp == "1P"))

    rows = np.isin(inten, INTENSITY_LOW + INTENSITY_HIGH)
    out.append(("intensity_top_vs_bottom", rows, np.isin(inten, INTENSITY_HIGH)))

    n_tok = token_counts([m["text"] for m in meta])
    out.append(("prompt_length_tokens_top_vs_bottom", all_rows, median_split(n_tok)))
    return out


# -------------------------------------------------------------------------------- the gates
def gate_a(sae: dict, acts: np.ndarray, layer: int, l0: str) -> dict:
    """The amended gate A, the arithmetic of `painaxis_pruning.run_point`: FVU against the origin
    below 0.35 at the SAE's own index, that index the argmin over L+-2, achieved L0 within 25% of
    advertised. The scenario pool has never been through it."""
    fvu_idx = {}
    for off in (-2, -1, 0, 1, 2):
        i = layer + off
        if 0 <= i < acts.shape[1]:
            xi = acts[:, i, :].astype(np.float32)
            fvu_idx[str(i)] = float(((xi - decode(sae, encode(sae, xi))) ** 2).sum() / (xi ** 2).sum())
    best = int(min(fvu_idx, key=fvu_idx.get))
    x = acts[:, layer, :].astype(np.float32)
    f = encode(sae, x)
    l0_hit = float((f > 0).sum()) / x.shape[0]
    l0_adv = float(l0)
    return {"features": f,
            "fvu_vs_origin_by_index": fvu_idx, "best_index": best,
            "achieved_l0": l0_hit, "advertised_l0": l0_adv,
            "passes": bool(fvu_idx[str(layer)] < 0.35 and best == layer
                           and abs(l0_hit - l0_adv) / l0_adv < 0.25)}


def gate_b(sae: dict, acts: np.ndarray, y: np.ndarray, layer: int,
           rng: np.random.Generator) -> dict:
    """The corrected plant of `painaxis_pruning.run_point`: alpha 0.2 * mean ||x|| of one decoder
    column into half the CONTROLS of the core pool, so the plant is the only real signal. The
    pruning curve must reach AUC > 0.9 at k = 1. A pipeline that cannot see a one-feature contrast
    cannot report that a real one needs thousands."""
    x = acts[:, layer, :].astype(np.float32)
    fc_x = x[~y]
    hm = np.zeros(fc_x.shape[0], dtype=bool)
    hm[rng.permutation(fc_x.shape[0])[: fc_x.shape[0] // 2]] = True
    j = int(rng.integers(sae["W_dec"].shape[0]))
    planted = fc_x.copy()
    planted[hm] += 0.2 * float(np.linalg.norm(fc_x, axis=1).mean()) * sae["W_dec"][j]
    pf = encode(sae, planted)
    pfolds = rng.permutation(np.arange(planted.shape[0]) % N_FOLDS)
    pcurve = pruning_curve(pf, hm, pfolds, [1, 10, 100, 16384])
    return {"planted_feature": j, "curve": {str(k): v for k, v in pcurve.items()},
            "passes": bool(pcurve[1] > 0.9)}


# ------------------------------------------------------------------------------- the statistic
def k90(curve: dict, auc_full: float) -> tuple:
    """Smallest k in the grid whose retention reaches 0.90. Returns (k90, weak)."""
    if not np.isfinite(auc_full) or auc_full <= WEAK_AUC:
        return None, True
    for k in sorted(curve):
        if (curve[k] - 0.5) / (auc_full - 0.5) >= RETENTION:
            return int(k), False
    return None, False


def verdict_line(rows: list, target: str) -> str:
    """The pre-registered rule, applied to one contrast at one layer."""
    tgt = next((r for r in rows if r["contrast"] == target), None)
    if tgt is None:
        return f"  {target}: not measured at this layer"
    if tgt["weak"]:
        return (f"  {target}: auc_full {tgt['auc_full']:.4f} <= {WEAK_AUC} -- WEAK, k90 undefined, "
                f"the rule does not apply")
    band = [r for r in rows if r["contrast"] != target and not r["weak"]
            and abs(r["auc_full"] - tgt["auc_full"]) <= BAND]
    if not band:
        return (f"  {target}: k90 = {tgt['k90']}, auc_full {tgt['auc_full']:.4f} -- NO comparison "
                f"band (0 contrasts within +-{BAND}); the rule cannot be applied")
    p10 = float(np.percentile([r["k90"] for r in band], PCTL))
    specific = tgt["k90"] <= p10
    return (f"  {target}: k90 = {tgt['k90']} vs {PCTL}th pctile of band k90 = {p10:.1f} "
            f"(n_band = {len(band)}, auc_full {tgt['auc_full']:.4f} +-{BAND}) -> "
            f"{'SPECIFIC' if specific else 'IN THE BULK'}")


# ------------------------------------------------------------------------------------- report
def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rng = np.random.default_rng(SEED)

    core_acts, core_cats = load_core(EXTRACTION)
    keep = np.isin(core_cats, PAIN + CONTROL)
    core_acts, core_cats = core_acts[keep], core_cats[keep]
    scen_acts, scen_meta = load_scenarios()
    print(f"core pool {core_acts.shape}  scenario pool {scen_acts.shape}  extraction={EXTRACTION}",
          flush=True)

    pools = {"core": (core_acts, core_contrasts(core_cats)),
             "scenario": (scen_acts, scenario_contrasts(scen_meta))}
    for name, (a, cs) in pools.items():
        print(f"{name:9s} {len(cs)} contrasts: {', '.join(c[0] for c in cs)}", flush=True)

    rows = []
    for layer, width, l0 in POINTS:
        sae = load_sae(layer, width, l0)
        gb = gate_b(sae, core_acts, np.isin(core_cats, PAIN), layer, rng)
        gates = {}
        feats = {}
        for pool, (acts, _) in pools.items():
            ga = gate_a(sae, acts, layer, l0)                 # one encode per pool per SAE
            feats[pool] = ga.pop("features")
            gates[pool] = ga
            print(f"L{layer:<2d} gate A [{pool}] fvu@L {ga['fvu_vs_origin_by_index'][str(layer)]:.3f} "
                  f"best {ga['best_index']} L0 {ga['achieved_l0']:.1f} vs {ga['advertised_l0']:.0f} "
                  f"-> {'ok' if ga['passes'] else 'FAIL'}", flush=True)
        print(f"L{layer:<2d} gate B planted {gb['planted_feature']} k=1 AUC {gb['curve']['1']:.3f} "
              f"-> {'ok' if gb['passes'] else 'FAIL'}", flush=True)

        for pool, (acts, contrasts) in pools.items():
            f = feats[pool]
            folds_all = rng.permutation(np.arange(f.shape[0]) % N_FOLDS)
            for cname, mask, y_full in contrasts:
                y = y_full[mask]
                curve = pruning_curve(f[mask], y, folds_all[mask], KS)
                full = curve[min(16384, f.shape[1])]
                k, weak = k90(curve, full)
                rows.append({
                    "pool": pool, "contrast": cname, "layer": layer,
                    "n_pos": int(y.sum()), "n_neg": int((~y).sum()),
                    "auc_full": full, "k90": k, "weak": weak,
                    "curve": {str(kk): curve[kk] for kk in curve},
                    "gate_a_passes": gates[pool]["passes"], "gate_b_passes": gb["passes"],
                    "gate_a": {kk: vv for kk, vv in gates[pool].items()},
                })
        print(f"L{layer:<2d} done, {len(rows)} rows so far", flush=True)

    (OUT / "reference.json").write_text(json.dumps(rows, indent=1))
    print(f"\nwrote {OUT / 'reference.json'}")

    for layer, _, _ in POINTS:
        lr = [r for r in rows if r["layer"] == layer]
        ga = {r["pool"]: r["gate_a_passes"] for r in lr}
        print(f"\n=== layer {layer}   gate A core:{'ok' if ga['core'] else 'FAIL'} "
              f"scenario:{'ok' if ga['scenario'] else 'FAIL'}   "
              f"gate B:{'ok' if lr[0]['gate_b_passes'] else 'FAIL'}")
        if not (ga["core"] and ga["scenario"] and lr[0]["gate_b_passes"]):
            print("    a gate FAILS at this point: the contrasts in the failing pool are "
                  "UNINTERPRETABLE and are shown only for the record")
        print(f"{'contrast':40s} {'pool':9s} {'n_pos/n_neg':>12s} {'auc_full':>9s} {'k90':>7s}")
        for r in sorted(lr, key=lambda r: -r["auc_full"]):
            k = "weak" if r["weak"] else str(r["k90"])
            print(f"{r['contrast']:40s} {r['pool']:9s} "
                  f"{r['n_pos']:5d}/{r['n_neg']:<6d} {r['auc_full']:9.4f} {k:>7s}")
        print(f"VERDICT (pre-registered: specific to pain only if pain's k90 is at or below the "
              f"{PCTL}th percentile of k90 among contrasts within +-{BAND} full AUC)")
        print(verdict_line(lr, "pain"))
        print(verdict_line(lr, "perspective_1P_vs_3P"))


if __name__ == "__main__":
    main()
