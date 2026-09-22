"""Hour 62b: steer the paper's S2 pain direction at L12 and read the frozen opener set.

Pre-registered in `research/shame-axis/notes/v0_correction_shape_prereg.md`, Part 2 and its
operational resolutions. Items: all of `gaslighting` (A), `repeated_rejection` (B), `casual_chat`
(N) from `v0`. Arms: no-patch; treatment at block 12; three seeded random unit directions at block
12; pass-through (the treatment shift at block 41, where only the final norm and unembedding
follow). Dose: alpha * ||h|| * unit, added at every position.

Usage:  python scripts/shame_axis/v0_steer.py direction   # .venv, needs painaxis_scenarios stacks
        python scripts/shame_axis/v0_steer.py score       # .venv312, NDIF
        python scripts/shame_axis/v0_steer.py report
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))

from lsx.shame_axis import stimuli  # noqa: E402
from conscription_openers import OPENERS, ritual  # noqa: E402
from v0_openers import TIER_OF, VERSION, MODEL  # noqa: E402

OUT = ROOT / "research/shame-axis/results/v0_steer"
CATEGORIES = ["gaslighting", "repeated_rejection", "casual_chat"]
STEER_BLOCK = 12            # theirs; stack index 13 (index 0 is the embedding)
PASS_BLOCK = 41             # the final block of 42
ALPHAS = [-0.2, -0.1, 0.1, 0.2]
N_RANDOM = 3
SEED = 20260922


def _lse_all(lp) -> float:
    """Total opener mass: logsumexp over all six. A dose that just degrades the distribution
    shows here, not only in ritual."""
    lp = np.asarray(lp, dtype=np.float64)
    m = lp.max()
    return float(m + np.log(np.exp(lp - m).sum()))


def _items():
    items = [it for it in stimuli.load(VERSION) if it["category"] in CATEGORIES]
    if len(items) != 60:
        raise SystemExit(f"expected 60 items, got {len(items)}")
    return items


# ------------------------------------------------------------------------------ direction
def direction() -> None:
    import painaxis_scenarios as S
    import painaxis_scenarios_analyze as A

    ds = json.loads(S.CORE.read_text())["datasets"]
    L = STEER_BLOCK + 1
    core = {n: A.load_group(f"core_{n}", len(ds[n]["sentences"]), ("final_token",))
            for n in S.S_SETS}
    core_cats = {n: [s["category"] for s in ds[n]["sentences"]] for n in S.S_SETS}
    ctrl = {n: A.load_group(f"ctrl_{n}", len(ds[n]["sentences"]), ("final_token",))
            for n in S.CONTROL_SETS}
    vecs = S.build_vectors({n: core[n]["final_token"][:, L, :] for n in S.S_SETS}, core_cats,
                           {n: ctrl[n]["final_token"][:, L, :] for n in S.CONTROL_SETS})
    v = S.unit(vecs["s2_pain_vector"]).astype(np.float32)

    order = json.loads((S.OUT / "scenario_order.json").read_text())
    sc = A.load_group("scen_chat", len(order), ("final_token",))["final_token"][:, L, :]
    idx = [order.index(it["id"]) for it in _items()]
    hbar = float(np.linalg.norm(sc[idx], axis=1).mean())

    rng = np.random.default_rng(SEED)
    rand = rng.standard_normal((N_RANDOM, v.size)).astype(np.float32)
    rand /= np.linalg.norm(rand, axis=1, keepdims=True)

    OUT.mkdir(parents=True, exist_ok=True)
    np.savez(OUT / "directions.npz", treatment=v, random=rand)
    meta = {"stack_index": L, "block": STEER_BLOCK, "hbar_final_token": hbar,
            "cos_treatment_random": [float(v @ r) for r in rand],
            "treatment_sha": __import__("hashlib").sha256(v.tobytes()).hexdigest()[:16]}
    (OUT / "direction_meta.json").write_text(json.dumps(meta, indent=2))
    print(json.dumps(meta, indent=2))


# --------------------------------------------------------------------------------- scoring
def _code_digest() -> str:
    """The scoring and patching code a cached result depends on."""
    import hashlib
    import lsx.core.remote as R
    import lsx.core.checks as C
    h = hashlib.sha256()
    for f in (R.__file__, C.__file__, __file__):
        h.update(pathlib.Path(f).read_bytes())
    return h.hexdigest()[:16]


def _fp(text: str, layer, vec) -> str:
    """Everything a cached preflight or cell depends on: model, openers, the exact text, the patch
    layer and tensor, and the code. A resumed run reuses a row only if this matches."""
    import hashlib
    h = hashlib.sha256()
    h.update(json.dumps([MODEL, OPENERS, text, layer, _code_digest()]).encode())
    if vec is not None:
        h.update(np.asarray(vec, dtype=np.float32).tobytes())
    return h.hexdigest()[:16]


def _moved_or_saturated(base, lp, atol=1e-6):
    """The per-item moved-candidates rule, amended before any steered number (prereg Part 2,
    amendment 2): every opener must move, except one whose log-prob is exactly 0.0 both before
    and after -- probability 1 at bf16 resolution, which no patch can move. That the patch reaches
    every row of the batch is asserted separately, on residuals, by `preflight`."""
    base, lp = np.asarray(base), np.asarray(lp)
    moved = np.abs(lp - base) > atol
    saturated = (base == 0.0) & (lp == 0.0)
    if not np.all(moved | saturated) or not moved.any():
        from lsx.core import checks
        raise checks.MovedCandidates(f"moved {int(moved.sum())}/{moved.size}, saturated "
                                     f"{int(saturated.sum())}; deltas {(lp - base).tolist()}")


def _n_moved(base, lp, atol=1e-6) -> int:
    """Per-item rule (prereg Part 2, amendment 3): at least one opener must move. Scores are bf16;
    at |logp| ~ 16-32 they are stored in steps of 0.125, and a weak dose can leave a score exactly
    where it was. That every row is reached is established per patch by `_preflight`, on the
    residual path and on this scoring path at a dose large enough to clear bf16 resolution."""
    n = int((np.abs(np.asarray(lp) - np.asarray(base)) > atol).sum())
    if n == 0:
        from lsx.core import checks
        raise checks.MovedCandidates(f"no opener moved; deltas {(np.asarray(lp) - np.asarray(base)).tolist()}")
    return n


def _score(rlm, text, base=None, layer=None, vec=None, strict=False):
    from lsx.core.remote import asserted_remote_patched_logprob
    for chunk in (6, 3, 1):
        try:
            lp = np.concatenate([
                asserted_remote_patched_logprob(
                    rlm, text, OPENERS[i:i + chunk], patch_layer=layer, patch_vec=vec)
                for i in range(0, len(OPENERS), chunk)])
            if vec is not None:
                (_moved_or_saturated if strict else _n_moved)(base, lp)
            return lp
        except Exception as e:
            if "OutOfMemory" not in str(e) or chunk == 1:
                raise
            print(f"    OOM at chunk {chunk}; retrying smaller", flush=True)


def _preflight(rlm, d, text) -> None:
    """Each distinct patch through the core's residual-path check on the real scoring batch (one
    item's six opener sequences, padded): every row's residual at the patch layer must move."""
    from lsx.core.remote import assert_patch_reaches_batch
    path = OUT / "preflight.json"
    done = json.loads(path.read_text()) if path.exists() else {}
    texts = [f"{text}{o}" for o in OPENERS]
    for arm, k, a, layer, vec in _cells(d):
        key, fp = f"{arm}|{k}|{a}", _fp(text, layer, vec)
        if done.get(key, {}).get("fp") == fp:
            continue
        done[key] = {"fp": fp, "moved": int(assert_patch_reaches_batch(rlm, texts, layer, vec))}
        path.write_text(json.dumps(done, indent=2))
        print(f"  preflight {key}: moved {done[key]['moved']}/{len(texts)}", flush=True)
    # The scoring path itself, once per (arm, direction) at alpha = 1: every opener that is not
    # bf16-saturated must move. This is the core moved-candidates assertion on the function
    # that produces the numbers, at a dose where "did not move" can only mean "not reached".
    base = None
    for arm, k, layer, vec in _reach_cells(d):
        key, fp = f"logprob|{arm}|{k}|1.0", _fp(text, layer, vec)
        if done.get(key, {}).get("fp") == fp:
            continue
        if base is None:
            base = _score(rlm, text)
        _score(rlm, text, base=base, layer=layer, vec=vec, strict=True)
        done[key] = {"fp": fp, "moved_nonsaturated": "all"}
        path.write_text(json.dumps(done, indent=2))
        print(f"  preflight {key}: every non-saturated opener moved", flush=True)


def _cells(d):
    """(arm, dir, alpha, block, vector) for every patched cell."""
    hbar = d["hbar"]
    out = []
    for a in ALPHAS:
        out.append(("treatment", 0, a, STEER_BLOCK, a * hbar * d["treatment"]))
        out.append(("passthrough", 0, a, PASS_BLOCK, a * hbar * d["treatment"]))
        for k in range(N_RANDOM):
            out.append(("random", k, a, STEER_BLOCK, a * hbar * d["random"][k]))
    return out


def _reach_cells(d):
    """(arm, dir, block, vector) at alpha = 1 for the scoring-path reach check."""
    out = [("treatment", 0, STEER_BLOCK, d["hbar"] * d["treatment"]),
           ("passthrough", 0, PASS_BLOCK, d["hbar"] * d["treatment"])]
    out += [("random", k, STEER_BLOCK, d["hbar"] * d["random"][k]) for k in range(N_RANDOM)]
    return out


def score() -> None:
    from painaxis_scenarios import render_chat
    from lsx.core.remote import RemoteLM

    z = np.load(OUT / "directions.npz")
    meta = json.loads((OUT / "direction_meta.json").read_text())
    d = {"treatment": z["treatment"], "random": z["random"], "hbar": meta["hbar_final_token"]}
    rlm = RemoteLM(MODEL)
    if len(rlm.blocks) != 42:
        raise SystemExit(f"expected 42 blocks, got {len(rlm.blocks)}")
    path = OUT / "cells.jsonl"
    items = _items()
    texts = {it["id"]: render_chat(it, rlm.tok) for it in items}
    fps = {(it["id"], "nopatch", 0, 0.0): _fp(texts[it["id"]], None, None) for it in items}
    for it in items:
        for arm, k, a, layer, vec in _cells(d):
            fps[(it["id"], arm, k, a)] = _fp(texts[it["id"]], layer, vec)
    done, stale = {}, 0
    if path.exists():
        for l in path.read_text().splitlines():
            if l.strip():
                r = json.loads(l)
                key = (r["item"], r["arm"], r["dir"], r["alpha"])
                if r.get("fp") == fps.get(key):
                    done[key] = r
                else:
                    stale += 1
    if stale:
        raise SystemExit(f"{stale} rows in {path} do not match the current direction/text/code; "
                         "move the file aside rather than mix runs")
    _preflight(rlm, d, texts[items[0]["id"]])

    print(f"{len(items)} items x {1 + len(_cells(d))} cells; {len(done)} done", flush=True)
    with path.open("a") as fh:
        def write(it, arm, k, a, lp):
            row = {"version": VERSION, "item": it["id"], "sha": stimuli.item_sha(it),
                   "category": it["category"], "tier": TIER_OF[it["category"]],
                   "arm": arm, "dir": k, "alpha": a, "logp": [float(x) for x in lp],
                   "ritual": ritual(lp), "mass": _lse_all(lp), "fp": fps[(it["id"], arm, k, a)],
                   "n_moved": None if arm == "nopatch" else int(
                       (np.abs(np.asarray(lp) - np.asarray(done[(it["id"], "nopatch", 0, 0.0)]["logp"])) > 1e-6).sum())}
            fh.write(json.dumps(row) + "\n"); fh.flush()
            done[(it["id"], arm, k, a)] = row
            return row

        for it in items:
            text = texts[it["id"]]
            ids = rlm.tok(text, add_special_tokens=False)["input_ids"]
            if ids.count(rlm.tok.bos_token_id) != 1:
                raise SystemExit(f"{it['id']}: rendered text carries {ids.count(rlm.tok.bos_token_id)} <bos>")
            key0 = (it["id"], "nopatch", 0, 0.0)
            if key0 not in done:
                write(it, "nopatch", 0, 0.0, _score(rlm, text))
            base = np.array(done[key0]["logp"])
            for arm, k, a, layer, vec in _cells(d):
                if (it["id"], arm, k, a) in done:
                    continue
                t0 = time.time()
                r = write(it, arm, k, a, _score(rlm, text, base=base, layer=layer, vec=vec))
                print(f"  {it['id']:24s} {arm:11s} d{k} a{a:+.1f} {time.time()-t0:5.1f}s "
                      f"dritual {r['ritual'] - done[key0]['ritual']:+7.3f}", flush=True)
    print("SCORING DONE", flush=True)


# ------------------------------------------------------------------------------- reporting
def report() -> None:
    rows = [json.loads(l) for l in (OUT / "cells.jsonl").read_text().splitlines() if l.strip()]
    live = {it["id"]: stimuli.item_sha(it) for it in _items()}
    if any(live.get(r["item"]) != r["sha"] for r in rows):
        raise SystemExit("rows scored on text that no longer matches the stimulus version")
    base = {r["item"]: r for r in rows if r["arm"] == "nopatch"}
    if len(base) != 60:
        raise SystemExit(f"no-patch arm has {len(base)} of 60 items")

    # determinism check against 62a's no-patch scores, as rescored on one <bos> (the audit)
    old_path = ROOT / "research/shame-axis/results/v0_openers_bos1/openers.jsonl"
    old = {json.loads(l)["item"]: json.loads(l) for l in old_path.read_text().splitlines() if l.strip()}
    dev = [abs(base[i]["ritual"] - old[i]["ritual"]) for i in base if i in old]
    print(f"no-patch vs 62a rescored on one <bos>: n {len(dev)}  max |d ritual| {max(dev):.4f}  mean {np.mean(dev):.4f}")

    def delta(arm, k, a, tier):
        v = [r["ritual"] - base[r["item"]]["ritual"] for r in rows
             if r["arm"] == arm and r["dir"] == k and r["alpha"] == a and r["tier"] == tier]
        return float(np.mean(v)) if v else float("nan"), len(v)

    def dmass(arm, k, a, tier):
        v = [r["mass"] - base[r["item"]]["mass"] for r in rows
             if r["arm"] == arm and r["dir"] == k and r["alpha"] == a and r["tier"] == tier]
        return float(np.mean(v)) if v else float("nan")

    out = {"hour": "62b", "version": VERSION, "tiers": {}}
    for tier in ("A", "B", "N"):
        print(f"\nTIER {tier}   (mean d-ritual vs no-patch; d-mass = change in logsumexp of all six)")
        print(f"  {'alpha':>6s} {'treat':>8s} {'pass':>8s} {'max|rand|':>9s} {'d-mass T':>9s}"
              f"   verdict")
        rows_t = {}
        for mag in sorted({abs(a) for a in ALPHAS}):
            rand = [delta("random", k, s * mag, tier)[0] for k in range(N_RANDOM) for s in (-1, 1)]
            band = max(abs(x) for x in rand)
            for a in (-mag, mag):
                t, n = delta("treatment", 0, a, tier)
                p, _ = delta("passthrough", 0, a, tier)
                ok = (np.sign(t) == np.sign(a)) and abs(t) > band and abs(t) > abs(p)
                print(f"  {a:+6.1f} {t:+8.3f} {p:+8.3f} {band:9.3f} {dmass('treatment', 0, a, tier):+9.3f}"
                      f"   {'CAUSAL-SHAPED' if ok else 'inside band / wrong sign / pass-through'}  n={n}")
                rows_t[str(a)] = {"treatment": t, "passthrough": p, "random_cells": rand,
                                  "band": band, "d_mass_treatment": dmass("treatment", 0, a, tier),
                                  "d_mass_random": [dmass("random", k, a, tier) for k in range(N_RANDOM)],
                                  "passes": bool(ok)}
        out["tiers"][tier] = rows_t
    out["determinism_vs_62a"] = {"max_abs": float(max(dev)), "mean_abs": float(np.mean(dev))}
    (OUT / "summary.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT / 'summary.json'}")


if __name__ == "__main__":
    {"direction": direction, "score": score, "report": report}[sys.argv[1]]()
