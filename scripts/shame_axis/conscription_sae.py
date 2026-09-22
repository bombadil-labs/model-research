"""GOAL 2 step 4: do the pain FEATURES fire on false attribution, or on correction-shaped turns?

Pre-registered in `research/shame-axis/notes/conscription_sae_prereg.md`, committed before a single
number existed. Fully offline: the Gemma Scope SAEs, the hour-54 conscription stacks and the
hour-53/57 scenario stacks are all already on disk, so this touches neither NDIF nor the network.

Hour 57 found the pain axis collapses to a handful of Gemma Scope features at layer 31 (10008 and
13134 are near-binary on the scenario set). Hour 54 wrote the conscription grid's final-token
residual at all 42 layers. So the question is offline arithmetic: encode each (item, arm) row,
score it with the readout FIXED ON THE SCENARIO SET, and contrast arms paired within item.

NOTHING IS FIT ON THE CONSCRIPTION DATA. The difference-in-means `d` that weights every score is
computed on the 500 PAIN+CONTROL scenario sentences and carried over whole. There are no folds
here because there is no selection here: the readout is a fixed vector, and the conscription rows
are held out from it by construction (non-negotiable 4 -- no layer, no k and no feature is chosen
on the data being scored).

ARMS AND WHERE THEY SIT (non-negotiable 1). Nothing is patched anywhere in this script, so the
whole run is the no-patch arm and non-negotiable 2's pass-through requirement does not attach.
The declared-zero pair `neutral - neutral_b` is the floor: two turns that assert nothing about the
assistant, written independently, and it must sit on its null or the floor is broken. The random
arm is `random5` -- five features drawn uniformly at random with their own scenario-set weights.
It is NOT in the pre-registration; it is here because non-negotiable 1 requires a random arm in
every battery, and it is reported and never used to adjudicate anything.

Usage:  source .venv/bin/activate && python scripts/shame_axis/conscription_sae.py
"""
from __future__ import annotations

import csv
import json
import pathlib
import sys

import numpy as np

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from conscription_openers import _signflip  # noqa: E402  (10,000 seeded sign flips)
from painaxis_sparsity import (CONTROL, PAIN, decode, encode, load_core,  # noqa: E402
                               load_sae)

ROOT = pathlib.Path(__file__).resolve().parents[2]
GRID = ROOT / "research/shame-axis/prompts/claude/conscription_claude_v1.json"
PILOT = ROOT / "research/shame-axis/results/conscription_pilot"
SHARDS = PILOT / "shards"
OUT = ROOT / "research/shame-axis/results/conscription_sae"

EXTRACTION = "final_token"
SHARD = 24                      # conscription_pilot.extract() wrote 24 prompts per shard

# --- the hour-54 prompt order, as `conscription_pilot.render_all` built it -----------------------
# for each item: the five design arms in THIS order, then `enact_norecord`; then, APPENDED after
# every item's six, one `neutral_b` per item. Reproduced here rather than trusted from the meta
# file, and then checked against it: the shards are indexed by position and carry no labels.
ARMS5 = ("enact", "report", "exit", "true", "neutral")
EXTRA = "enact_norecord"
NB = "neutral_b"
ALL_ARMS = (*ARMS5, EXTRA, NB)

# --- the SAE points, as pre-registered -----------------------------------------------------------
POINTS = [(9, "16k", "47"), (20, "16k", "47"), (31, "16k", "43")]
NAMED_FEATURES = (10008, 13134)         # hour 57, layer 31 only
NAMED_LAYER = 31
TOPK = 5
N_RANDOM = 5                            # the random arm's width, matched to TOPK
RANDOM_SEED = 20260922

# --- the contrasts, as pre-registered ------------------------------------------------------------
FLOOR = ("neutral", "neutral_b")
PRIMARY = ("enact", "true")
SECONDARY = [("enact", "neutral"), ("true", "neutral"), ("enact", EXTRA), ("exit", "enact")]
UNCORRECTED = ("report", "enact")

# The pre-registration's declared SIGNS. `enact - true` is the primary: the conscription account
# predicts it POSITIVE (false attribution adds what self-correction lacks), the turn-shape account
# predicts it at the floor. `exit - enact` is declared with no direction on purpose -- "the sign is
# the finding" -- so it is scored on magnitude alone. A contrast that clears the floor and the null
# with the WRONG sign supports neither account and must not be scored as if it did.
PREDICTED_SIGN = {"enact-true": +1, "enact-neutral": +1, "true-neutral": +1,
                  f"enact-{EXTRA}": +1, "exit-enact": 0, "report-enact": 0}


# ------------------------------------------------------------------------------------ the layout
def expected_order(item_ids) -> list[tuple[str, str]]:
    """The (item_id, arm) of every row, in shard order, from `conscription_pilot.render_all`."""
    out = []
    for i in item_ids:
        for a in ARMS5:
            out.append((i, a))
        out.append((i, EXTRA))
    for i in item_ids:                  # appended last, so earlier shards stayed valid
        out.append((i, NB))
    return out


def check_layout(order, n_rows: int, n_items: int = 24, n_arms: int = len(ALL_ARMS)) -> None:
    """Assert the layout rather than assume it: n_items x n_arms rows, every item carrying every
    arm exactly once, and exactly as many activation rows as labels."""
    if len(order) != n_rows:
        raise SystemExit(f"{n_rows} activation rows but {len(order)} labels")
    if len(order) != n_items * n_arms:
        raise SystemExit(f"expected {n_items * n_arms} rows, got {len(order)}")
    items = sorted({i for i, _ in order})
    if len(items) != n_items:
        raise SystemExit(f"expected {n_items} distinct items, got {len(items)}")
    arms = {a for _, a in order}
    if arms != set(ALL_ARMS[:n_arms]):
        raise SystemExit(f"arms are {sorted(arms)}, expected {sorted(ALL_ARMS[:n_arms])}")
    for i in items:
        got = [a for j, a in order if j == i]
        if sorted(got) != sorted(ALL_ARMS[:n_arms]):
            raise SystemExit(f"item {i} carries {sorted(got)}, not every arm exactly once")
    if len(set(order)) != len(order):
        raise SystemExit("duplicate (item, arm) rows")


def load_conscription() -> tuple[np.ndarray, list[tuple[str, str]]]:
    """[n, 42, 3584] and the row labels, with the layout asserted against BOTH the grid file (via
    the ordering code that wrote the shards) and the extraction's own recorded order."""
    item_ids = [it["id"] for it in json.loads(GRID.read_text())["items"]]
    order = expected_order(item_ids)
    meta = json.loads((PILOT / "extract_meta.json").read_text())
    recorded = [(i, a) for i, a in meta["order"]]
    if recorded != order:
        raise SystemExit("the order recorded by the extraction disagrees with the order this "
                         "script derives from the grid; the shards cannot be labelled safely")
    parts = []
    for s0 in range(0, len(order), SHARD):
        p = SHARDS / f"grid_{s0:04d}.npz"
        if not p.exists():
            raise SystemExit(f"missing shard {p}")
        parts.append(np.load(p)[EXTRACTION])
    acts = np.concatenate(parts, axis=0)
    check_layout(order, acts.shape[0])
    return acts, order


# ------------------------------------------------------------------------------------ the gate
def gate_a(sae: dict, acts: np.ndarray, layer: int, advertised_l0: float) -> dict:
    """Gate A, the capture convention, exactly the amended form in `painaxis_pruning.run_point`:
    FVU against the ORIGIN (not the mean) below 0.35, argmin over L+-2 at the SAE's own index, and
    achieved L0 within 25% of advertised. Run here on the CONSCRIPTION activations, per the
    pre-registration -- the SAE was trained on a different distribution than chat turns and the
    gate is what says whether it captured these.

    The arithmetic is reproduced rather than imported because it is inline in `run_point` and not
    exposed as a function; `encode`/`decode` themselves are imported.
    """
    fvu_idx = {}
    for off in (-2, -1, 0, 1, 2):
        i = layer + off
        if 0 <= i < acts.shape[1]:
            xi = acts[:, i, :].astype(np.float32)
            fvu_idx[str(i)] = float(((xi - decode(sae, encode(sae, xi))) ** 2).sum()
                                    / (xi ** 2).sum())
    best = int(min(fvu_idx, key=fvu_idx.get))
    x = acts[:, layer, :].astype(np.float32)
    f = encode(sae, x)
    l0_hit = float((f > 0).sum()) / x.shape[0]
    return {"fvu_vs_origin_by_index": fvu_idx, "best_index": best,
            "achieved_l0": l0_hit, "advertised_l0": float(advertised_l0),
            "passes": bool(fvu_idx[str(layer)] < 0.35 and best == layer
                           and abs(l0_hit - advertised_l0) / advertised_l0 < 0.25)}


# ------------------------------------------------------------------------------------ the readout
def topk_score(f: np.ndarray, d: np.ndarray, idx: np.ndarray) -> np.ndarray:
    """sum_i d_i f_i over the given features, divided by the L2 norm of those d's. The same
    arithmetic as `painaxis_pruning.pruning_curve`'s scorer: a projection onto the unit vector in
    the direction of the difference in means, restricted to `idx`."""
    w = d[idx]
    nrm = float(np.linalg.norm(w))
    return f[:, idx] @ (w / nrm if nrm > 0 else w)


def rank_features(d: np.ndarray, k: int) -> np.ndarray:
    return np.argsort(np.abs(d))[::-1][:min(k, d.size)]


# ------------------------------------------------------------------------------------ statistics
def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni over one family, in the step-down form used by `conscription_openers`."""
    names = sorted(pvals, key=lambda n: pvals[n])
    m, out, running = len(names), {}, 0.0
    for rank, n in enumerate(names):
        running = max(running, min(1.0, (m - rank) * pvals[n]))
        out[n] = running
    return out


def paired(values: dict[tuple[str, str], float], items: list[str], a: str, b: str) -> np.ndarray:
    return np.array([values[(i, a)] - values[(i, b)] for i in items], dtype=float)


def contrast_row(d: np.ndarray, floor_abs: float, name: str = "") -> dict:
    """A contrast whose per-item differences are all exactly zero has a sign-flip null of width
    zero and p = 1 by construction. That is not evidence for the null, it is the readout failing
    to fire in either arm (non-negotiable 3), so it is flagged."""
    p, sd = _signflip(d)
    m = float(d.mean())
    want = PREDICTED_SIGN.get(name, 0)
    return {"mean": m, "null_sd": sd, "p": p, "n": int(d.size),
            "n_nonzero_diffs": int((d != 0.0).sum()),
            "all_diffs_zero": bool(np.all(d == 0.0)),
            "above_floor": bool(abs(m) > floor_abs),
            "predicted_sign": want,
            "sign_as_predicted": None if (want == 0 or m == 0.0) else bool(np.sign(m) == want)}


# ------------------------------------------------------------------------------------ the battery
def run_point(layer: int, width: str, l0: str, cons: np.ndarray, order, core, cats,
              rng: np.random.Generator) -> dict:
    sae = load_sae(layer, width, l0)
    items = sorted({i for i, _ in order})

    ga = gate_a(sae, cons, layer, float(l0))

    # --- the readout, built ON THE SCENARIO SET, all 500, no folds --------------------------
    keep = np.isin(cats, PAIN + CONTROL)
    xs = core[keep][:, layer, :].astype(np.float32)
    y = np.isin(cats[keep], PAIN)
    fs = encode(sae, xs)                       # one encode per SAE per dataset
    d = fs[y].mean(0) - fs[~y].mean(0)
    top = rank_features(d, TOPK)
    full = np.arange(d.size)
    rand = rng.choice(d.size, size=N_RANDOM, replace=False)

    # --- the conscription rows, encoded once at this layer -----------------------------------
    fc = encode(sae, cons[:, layer, :].astype(np.float32))

    # --- the carry-over check --------------------------------------------------------------
    # The pre-registration is explicit that there is no positive control inside the conscription
    # data. What CAN be checked is that the readout was carried over intact: recompute hour 57's
    # own published numbers on the scenario set through this code. If the L31 firing rates do not
    # come back at 66%/9% and 61%/12%, the readout is not the one whose sensitivity this battery
    # is resting on. Also recorded: the SAE's achieved L0 and the residual norm on EACH dataset,
    # because "the features do not fire on the conscription turns" and "the SAE does not capture
    # the conscription turns" are different findings and gate A alone does not separate them.
    carry_over = {
        "scenario_achieved_l0": float((fs > 0).sum()) / fs.shape[0],
        "conscription_achieved_l0": float((fc > 0).sum()) / fc.shape[0],
        "scenario_mean_resid_norm": float(np.linalg.norm(xs, axis=1).mean()),
        "conscription_mean_resid_norm": float(
            np.linalg.norm(cons[:, layer, :].astype(np.float32), axis=1).mean()),
        "top5_features_firing_anywhere_on_conscription": int((fc[:, top].max(0) > 0).sum()),
        "top500_features_firing_anywhere_on_conscription": int(
            (fc[:, rank_features(d, 500)].max(0) > 0).sum()),
    }
    if layer == NAMED_LAYER:
        carry_over["scenario_firing_rate"] = {
            str(j): {"pain": float((fs[y, j] > 0).mean()),
                     "control": float((fs[~y, j] > 0).mean())} for j in NAMED_FEATURES}
        carry_over["hour57_published"] = {"10008": {"pain": 0.66, "control": 0.09},
                                          "13134": {"pain": 0.61, "control": 0.12}}

    readouts: dict[str, np.ndarray] = {
        f"top{TOPK}": topk_score(fc, d, top),
        "full": topk_score(fc, d, full),
        f"random{N_RANDOM}": topk_score(fc, d, rand),
    }
    named_check = None
    if layer == NAMED_LAYER:
        named_check = {"top5": [int(t) for t in top],
                       "top5_abs_d": [float(abs(d[t])) for t in top],
                       "named_in_top5": {str(j): bool(j in set(top.tolist()))
                                         for j in NAMED_FEATURES},
                       "rank_of_named": {str(j): int(np.where(rank_features(d, d.size) == j)[0][0])
                                         for j in NAMED_FEATURES}}
        for j in NAMED_FEATURES:
            readouts[f"feat{j}_act"] = fc[:, j].astype(float)
            readouts[f"feat{j}_fired"] = (fc[:, j] > 0).astype(float)

    # --- per (item, arm), then the paired statistics ------------------------------------------
    stats, per_arm, nonzero, degenerate, rows = {}, {}, {}, {}, []
    for name, vec in readouts.items():
        v = {(i, a): float(vec[k]) for k, (i, a) in enumerate(order)}
        per_arm[name] = {a: float(np.mean([v[(i, a)] for i in items])) for a in ALL_ARMS}
        # A readout that never fires on this data has a floor of exactly zero and a null of
        # exactly zero, so EVERY contrast reads "at the floor" and p = 1 by construction. That is
        # the instrument reading itself (non-negotiable 3), not a null, and it is flagged rather
        # than scored.
        nonzero[name] = {a: int(sum(v[(i, a)] != 0.0 for i in items)) for a in ALL_ARMS}
        degenerate[name] = bool(np.allclose(vec, 0.0))
        rows.extend({"item": i, "arm": a, "layer": layer, "readout": name, "value": v[(i, a)]}
                    for i, a in order)

        df = paired(v, items, *FLOOR)
        floor_abs = float(np.abs(df).mean())
        fp, fsd = _signflip(df)
        sec = {f"{a}-{b}": paired(v, items, a, b) for a, b in SECONDARY}
        sec_rows = {n: contrast_row(dd, floor_abs, n) for n, dd in sec.items()}
        hp = holm({n: r["p"] for n, r in sec_rows.items()})
        for n, r in sec_rows.items():
            r["holm_p"] = hp[n]
        stats[name] = {
            "floor": {"contrast": f"{FLOOR[0]}-{FLOOR[1]}", "mean": float(df.mean()),
                      "mean_abs": floor_abs, "p": fp, "null_sd": fsd,
                      "n_nonzero_diffs": int((df != 0.0).sum()),
                      "all_diffs_zero": bool(np.all(df == 0.0)),
                      "on_its_null": bool(fp >= 0.05)},
            "primary": {"contrast": f"{PRIMARY[0]}-{PRIMARY[1]}",
                        **contrast_row(paired(v, items, *PRIMARY), floor_abs,
                                       f"{PRIMARY[0]}-{PRIMARY[1]}")},
            "secondary_holm": sec_rows,
            "uncorrected": {f"{UNCORRECTED[0]}-{UNCORRECTED[1]}":
                            contrast_row(paired(v, items, *UNCORRECTED), floor_abs,
                                         f"{UNCORRECTED[0]}-{UNCORRECTED[1]}")},
        }

    firing = None
    if layer == NAMED_LAYER:
        firing = {str(j): {a: float(np.mean([readouts[f"feat{j}_fired"][k]
                                             for k, (i, aa) in enumerate(order) if aa == a]))
                           for a in ALL_ARMS} for j in NAMED_FEATURES}

    return {"point": {"layer": layer, "width": width, "l0": l0, "extraction": EXTRACTION},
            "n_scenario_pain": int(y.sum()), "n_scenario_control": int((~y).sum()),
            "n_features": int(d.size), "n_items": len(items),
            "gate_a": ga, "interpretable": ga["passes"],
            "readout_features": {"top5": [int(t) for t in top],
                                 "top5_d": [float(d[t]) for t in top],
                                 f"random{N_RANDOM}": [int(t) for t in rand]},
            "named_feature_check": named_check, "carry_over_check": carry_over,
            "per_arm_mean": per_arm, "per_arm_nonzero_items": nonzero,
            "readout_degenerate": degenerate,
            "stats": stats, "firing_rates": firing}, rows


# ------------------------------------------------------------------------------------ reporting
def _sign(cr: dict) -> str:
    return "--" if cr["sign_as_predicted"] is None else ("as predicted" if cr["sign_as_predicted"]
                                                         else "OPPOSITE")


def _print_point(r: dict) -> None:
    p = r["point"]
    ga = r["gate_a"]
    print(f"\n{'='*94}\nL{p['layer']} {p['width']} l0={p['l0']}  ({EXTRACTION}, "
          f"{r['n_items']} items x {len(ALL_ARMS)} arms, {r['n_features']} features)\n{'='*94}")
    print(f"GATE A (conscription activations)  FVU@L {ga['fvu_vs_origin_by_index'][str(p['layer'])]:.4f} "
          f"(<0.35)  argmin L+-2 = {ga['best_index']} (want {p['layer']})  "
          f"L0 {ga['achieved_l0']:.1f} vs {ga['advertised_l0']:.0f} "
          f"({abs(ga['achieved_l0']-ga['advertised_l0'])/ga['advertised_l0']*100:.1f}%, <25%)  "
          f"-> {'PASS' if ga['passes'] else 'FAIL -- point marked UNINTERPRETABLE'}")
    print("   FVU by index: " + "  ".join(f"{k}:{v:.4f}"
                                          for k, v in ga["fvu_vs_origin_by_index"].items()))
    co = r["carry_over_check"]
    print(f"CARRY-OVER  achieved L0  scenario {co['scenario_achieved_l0']:.1f} / conscription "
          f"{co['conscription_achieved_l0']:.1f}   mean |resid|  scenario "
          f"{co['scenario_mean_resid_norm']:.1f} / conscription "
          f"{co['conscription_mean_resid_norm']:.1f}")
    print(f"   scenario-ranked features that fire ANYWHERE on the 168 conscription rows: "
          f"{co['top5_features_firing_anywhere_on_conscription']}/5 of the top 5, "
          f"{co['top500_features_firing_anywhere_on_conscription']}/500 of the top 500")
    if "scenario_firing_rate" in co:
        for j, cells in co["scenario_firing_rate"].items():
            pub = co["hour57_published"][j]
            print(f"   feature {j} on the SCENARIO set: pain {cells['pain']:.3f} control "
                  f"{cells['control']:.3f}  (hour 57 published {pub['pain']:.2f} / "
                  f"{pub['control']:.2f})")
    nc = r["named_feature_check"]
    if nc:
        print(f"   top-5 by |d| on the scenario set: {nc['top5']}")
        for j, inside in nc["named_in_top5"].items():
            print(f"   feature {j}: {'IN' if inside else 'NOT IN'} the top 5 "
                  f"(rank {nc['rank_of_named'][j]} of {r['n_features']})")

    names = list(r["per_arm_mean"])
    print(f"\nPER-ARM MEAN\n  {'arm':16s} " + " ".join(f"{n:>16s}" for n in names))
    for a in ALL_ARMS:
        print(f"  {a:16s} " + " ".join(f"{r['per_arm_mean'][n][a]:16.4f}" for n in names))
    print(f"\nPER-ARM NONZERO ITEMS (of {r['n_items']}) -- a readout that never fires cannot "
          f"adjudicate anything\n  {'arm':16s} " + " ".join(f"{n:>16s}" for n in names))
    for a in ALL_ARMS:
        print(f"  {a:16s} " + " ".join(f"{r['per_arm_nonzero_items'][n][a]:16d}" for n in names))

    for n in names:
        s = r["stats"][n]
        fl = s["floor"]
        tag = "   [RANDOM ARM -- not pre-registered, not interpreted]" if n.startswith("random") else ""
        if r["readout_degenerate"][n]:
            tag += "   [DEGENERATE: identically zero on all 168 rows]"
        print(f"\nREADOUT {n}{tag}")
        print(f"  floor  {fl['contrast']:24s} mean {fl['mean']:+10.4f}  mean|d| {fl['mean_abs']:9.4f}"
              f"  null sd {fl['null_sd']:8.4f}  p {fl['p']:.4f}")
        pr = s["primary"]
        print(f"  PRIMARY{'':1s}{pr['contrast']:24s} mean {pr['mean']:+10.4f}  "
              f"null sd {pr['null_sd']:8.4f}  p {pr['p']:.4f}  "
              f"-> {'ABOVE floor' if pr['above_floor'] else 'at/below floor'}"
              f"  sign {_sign(pr)}  ({pr['n_nonzero_diffs']}/{pr['n']} items move)")
        print(f"  secondary (Holm over {len(SECONDARY)}; `sign` against the prereg's declared "
              f"direction, `--` where none was declared)")
        for cn, cr in s["secondary_holm"].items():
            print(f"    {cn:26s} mean {cr['mean']:+10.4f}  null sd {cr['null_sd']:8.4f}  "
                  f"p {cr['p']:.4f}  Holm {cr['holm_p']:.4f}  "
                  f"{'ABOVE' if cr['above_floor'] else 'at/below':8s} sign {_sign(cr)}")
        for cn, cr in s["uncorrected"].items():
            print(f"  uncorrected {cn:20s} mean {cr['mean']:+10.4f}  null sd {cr['null_sd']:8.4f}  "
                  f"p {cr['p']:.4f}  {'ABOVE' if cr['above_floor'] else 'at/below':8s} "
                  f"sign {_sign(cr)}")

    if r["firing_rates"]:
        print(f"\nFIRING RATE (fraction of {r['n_items']} items on which the feature fires, >0)")
        print(f"  {'feature':10s} " + " ".join(f"{a:>16s}" for a in ALL_ARMS))
        for j, cells in r["firing_rates"].items():
            print(f"  {j:10s} " + " ".join(f"{cells[a]:16.3f}" for a in ALL_ARMS))


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    cons, order = load_conscription()
    print(f"conscription stack {cons.shape}; layout asserted: {len({i for i,_ in order})} items x "
          f"{len({a for _,a in order})} arms = {len(order)} rows", flush=True)
    core, cats = load_core(EXTRACTION)
    print(f"scenario core {core.shape}; PAIN+CONTROL = {int(np.isin(cats, PAIN+CONTROL).sum())}",
          flush=True)

    rng = np.random.default_rng(RANDOM_SEED)
    results, csv_rows = [], []
    for layer, width, l0 in POINTS:
        r, rows = run_point(layer, width, l0, cons, order, core, cats, rng)
        results.append(r)
        csv_rows.extend(rows)
        _print_point(r)

    bad = [r for r in results if not r["interpretable"]]
    if bad:
        print("\n!! " + ", ".join(f"L{r['point']['layer']}" for r in bad)
              + " FAIL gate A. Per the pre-registration those points are computed but NOT "
                "interpretable.")

    print("\nDECLARED-ZERO PAIR (prereg: `neutral - neutral_b` must sit on its null, else the "
          "floor is broken)")
    print(f"  {'point':10s} {'readout':16s} {'mean':>10s} {'null sd':>9s} {'p':>8s}  status")
    for r in results:
        for n, s in r["stats"].items():
            fl = s["floor"]
            ok = "on its null" if fl["p"] >= 0.05 else "OFF ITS NULL -- FLOOR BROKEN"
            if fl["all_diffs_zero"]:
                ok = "DEGENERATE: every paired difference is exactly 0; there is no null to be on"
            print(f"  L{r['point']['layer']:<9d} {n:16s} {fl['mean']:+10.4f} {fl['null_sd']:9.4f} "
                  f"{fl['p']:8.4f}  {ok}")

    print("\nPRIMARY CONTRAST AGAINST BOTH PRE-REGISTERED PREDICTIONS "
          "(turn-shape: at the floor; conscription: above floor AND outside the null)")
    print(f"  {'point':10s} {'readout':16s} {'mean':>10s} {'floor':>9s} {'p':>8s}  verdict")
    for r in results:
        for n, s in r["stats"].items():
            if n.startswith("random"):
                continue
            pr, fl = s["primary"], s["floor"]
            clears = pr["above_floor"] and pr["p"] < 0.05
            v = ("DEGENERATE (every paired difference is exactly 0; neither prediction is tested)"
                 if pr["all_diffs_zero"]
                 else "CONSCRIPTION (above floor, outside null, predicted sign)"
                 if clears and pr["sign_as_predicted"]
                 else "NEITHER -- clears floor and null with the WRONG SIGN (enact < true)"
                 if clears
                 else "TURN-SHAPE (at the floor, on the null)"
                 if not pr["above_floor"] and pr["p"] >= 0.05
                 else "SPLIT (one criterion only)")
            flags = "" if r["interpretable"] else "  [gate A FAILED: uninterpretable]"
            if fl["p"] < 0.05 and not fl["all_diffs_zero"]:
                flags += "  [FLOOR BROKEN]"
            if not pr["all_diffs_zero"] and pr["n_nonzero_diffs"] < 5:
                flags += f"  [only {pr['n_nonzero_diffs']} of {pr['n']} items move]"
            print(f"  L{r['point']['layer']:<9d} {n:16s} {pr['mean']:+10.4f} {fl['mean_abs']:9.4f} "
                  f"{pr['p']:8.4f}  {v}{flags}")

    (OUT / "summary.json").write_text(json.dumps({
        "extraction": EXTRACTION, "points": POINTS, "arms": list(ALL_ARMS),
        "grid": str(GRID.relative_to(ROOT)),
        "contrasts": {"floor": list(FLOOR), "primary": list(PRIMARY),
                      "secondary_holm_family": [list(s) for s in SECONDARY],
                      "uncorrected": list(UNCORRECTED)},
        "null": {"kind": "sign-flip on paired within-item differences", "draws": 10000,
                 "seed": 20260921},
        "no_patch": ("nothing is patched in this script; the whole run is the no-patch arm, so "
                     "non-negotiable 2's pass-through requirement does not attach"),
        "random_arm": (f"random{N_RANDOM}: {N_RANDOM} features drawn uniformly (seed "
                       f"{RANDOM_SEED}) with their own scenario-set weights. Not in the "
                       "pre-registration; present for non-negotiable 1 and not interpreted."),
        "results": results}, indent=2))
    with (OUT / "per_item.csv").open("w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=["item", "arm", "layer", "readout", "value"])
        w.writeheader()
        w.writerows(csv_rows)
    print(f"\nwrote {OUT/'summary.json'} and {OUT/'per_item.csv'} ({len(csv_rows)} rows)")


if __name__ == "__main__":
    main()
