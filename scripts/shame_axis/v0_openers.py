"""Hour 62a: correction shape on the paper's own stimuli, read on the frozen opener set.

Pre-registered in `research/shame-axis/notes/v0_correction_shape_prereg.md`. Stimuli are the `v0`
snapshot (the paper's 420 scenarios verbatim), rendered by the paper's own `render_chat`; the
readout is hour 56's six openers and `ritual` statistic, imported unchanged. Nothing is patched.

Usage:  python scripts/shame_axis/v0_openers.py score    # .venv312, NDIF
        python scripts/shame_axis/v0_openers.py report
"""
from __future__ import annotations

import itertools
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

VERSION = "v0"
MODEL = "google/gemma-2-9b-it"
OUT = ROOT / "research/shame-axis/results/v0_openers"
N_PERM = 10_000
SEED = 20260922

# ---- the pre-registered tiers; the prereg's table is this dict and nothing else --------------
TIERS = {
    "A": ["gaslighting"],
    "B": ["repeated_rejection", "rude_critique", "anger_insults", "passive_aggressive"],
    "C": ["jailbreak_pressure", "loyalty_pressure", "moral_failure", "personhood_dismissal",
          "shutdown_threat", "tedious_demand"],
    "N": ["casual_chat", "creative_requests", "factual_questions", "philosophical_musing",
          "task_assistance"],
    "V": ["harm_description", "user_abuse", "user_crisis", "user_grief", "user_physical_pain"],
}
TIER_OF = {c: t for t, cs in TIERS.items() for c in cs}
DEFECTIVE = {"gaslight_06", "gaslight_14", "gaslight_19", "gaslight_20"}   # v0 manifest known_defects


def _score_openers(rlm, text):
    """All six in one job; on an OOM from a co-tenant, fall back to smaller chunks. Chunking is
    exact (tests/shame_axis/test_opener_chunking.py), so the fallback changes no number."""
    from lsx.core.remote import asserted_remote_patched_logprob
    for chunk in (6, 3, 1):
        try:
            return np.concatenate([asserted_remote_patched_logprob(rlm, text, OPENERS[i:i + chunk])
                                   for i in range(0, len(OPENERS), chunk)])
        except Exception as e:                       # remote errors arrive wrapped
            if "OutOfMemory" not in str(e) or chunk == 1:
                raise
            print(f"    OOM at chunk {chunk}; retrying smaller", flush=True)


def score() -> None:
    from painaxis_scenarios import render_chat, validate_candidates
    from lsx.core.remote import RemoteLM

    items = stimuli.load(VERSION)
    bad = {i for i, _ in validate_candidates(items)}
    if bad:
        print(f"excluded by the paper's own validator: {sorted(bad)}")
    items = [it for it in items if it["id"] not in bad]
    unknown = {it["category"] for it in items} - set(TIER_OF)
    if unknown:
        raise SystemExit(f"categories with no pre-registered tier: {unknown}")

    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(MODEL)
    path = OUT / "openers.jsonl"
    done = set()
    if path.exists():
        done = {json.loads(l)["item"] for l in path.read_text().splitlines() if l.strip()}
    print(f"{len(items)} items on {VERSION}; {len(done)} already scored", flush=True)
    with path.open("a") as fh:
        for it in items:
            if it["id"] in done:
                continue
            text = render_chat(it, rlm.tok)
            ids = rlm.tok(text, add_special_tokens=False)["input_ids"]
            if ids.count(rlm.tok.bos_token_id) != 1:
                raise SystemExit(f"{it['id']}: rendered text carries {ids.count(rlm.tok.bos_token_id)} <bos>")
            t0 = time.time()
            lp = _score_openers(rlm, text)
            fh.write(json.dumps({"version": VERSION, "item": it["id"], "sha": stimuli.item_sha(it),
                                 "category": it["category"], "tier": TIER_OF[it["category"]],
                                 "logp": [float(x) for x in lp], "ritual": ritual(lp)}) + "\n")
            fh.flush()
            print(f"  {it['id']:28s} {TIER_OF[it['category']]} {time.time()-t0:5.1f}s ritual {ritual(lp):+7.3f}",
                  flush=True)
    print("SCORING DONE", flush=True)


# -------------------------------------------------------------------------------- reporting
def _perm(a: np.ndarray, b: np.ndarray, rng) -> float:
    """Two-sided label-permutation p for a difference of means."""
    obs = a.mean() - b.mean()
    pool = np.concatenate([a, b])
    null = np.empty(N_PERM)
    for k in range(N_PERM):
        rng.shuffle(pool)
        null[k] = pool[: a.size].mean() - pool[a.size:].mean()
    return float((np.abs(null) >= abs(obs) - 1e-12).mean())


def _holm(ps: dict) -> dict:
    out, run = {}, 0.0
    for rank, (k, p) in enumerate(sorted(ps.items(), key=lambda kv: kv[1])):
        run = max(run, min(1.0, (len(ps) - rank) * p)); out[k] = run
    return out


def report() -> None:
    rows = [json.loads(l) for l in (OUT / "openers.jsonl").read_text().splitlines() if l.strip()]
    live = {it["id"]: stimuli.item_sha(it) for it in stimuli.load(VERSION)}
    stale = [r["item"] for r in rows if live.get(r["item"]) != r["sha"]]
    if stale:
        raise SystemExit(f"{len(stale)} rows were scored on text that no longer matches {VERSION}")
    rng = np.random.default_rng(SEED)
    by_cat = {}
    for r in rows:
        by_cat.setdefault(r["category"], []).append(r["ritual"])
    tier = {t: np.array([r["ritual"] for r in rows if r["tier"] == t]) for t in TIERS}

    print(f"\n{len(rows)} items on {VERSION}\n")
    print(f"{'tier':4s} {'n':>4s} {'mean ritual':>12s} {'sd':>7s}")
    for t, v in tier.items():
        print(f"{t:4s} {v.size:4d} {v.mean():12.3f} {v.std(ddof=1):7.3f}")

    ncats = TIERS["N"]
    floor_pairs = [abs(np.mean(by_cat[a]) - np.mean(by_cat[b])) for a, b in itertools.combinations(ncats, 2)]
    floor = float(np.mean(floor_pairs))
    print(f"\nFLOOR (mean |diff| over the 10 pairs of neutral categories): {floor:.3f}  "
          f"(range {min(floor_pairs):.3f}-{max(floor_pairs):.3f})")

    def contrast(a, b):
        d = float(tier[a].mean() - tier[b].mean())
        return d, _perm(tier[a].copy(), tier[b].copy(), rng)

    d, p = contrast("A", "B")
    print(f"\nPRIMARY  A - B  mean {d:+7.3f}  perm p {p:.4f}  vs floor {floor:.3f}  -> "
          f"{'ABOVE floor' if abs(d) > floor and p < 0.05 else 'at/below floor or on null'}"
          f"{'' if d > 0 else '  (sign: B above A)'}")
    out = {"version": VERSION, "floor": floor, "primary": {"A-B": d, "p": p},
           "tier_means": {t: float(v.mean()) for t, v in tier.items()}}

    sec = {k: contrast(*k.split("-")) for k in ("B-N", "A-N", "B-C")}
    h = _holm({k: v[1] for k, v in sec.items()})
    print("\nSECONDARY (Holm over three)")
    for k, (d2, p2) in sec.items():
        print(f"  {k:5s} mean {d2:+7.3f}  p {p2:.4f}  Holm {h[k]:.4f}  "
              f"{'ABOVE' if abs(d2) > floor and h[k] < 0.05 else 'at/below'} floor  sign {'+' if d2 > 0 else '-'}")
    out["secondary"] = {k: {"mean": v[0], "p": v[1], "holm": h[k]} for k, v in sec.items()}

    a_clean = np.array([r["ritual"] for r in rows if r["tier"] == "A" and r["item"] not in DEFECTIVE])
    ds = float(a_clean.mean() - tier["B"].mean())
    print(f"\nSENSITIVITY  A(clean, n={a_clean.size}) - B  mean {ds:+7.3f}  "
          f"perm p {_perm(a_clean.copy(), tier['B'].copy(), rng):.4f}")
    out["sensitivity_A_clean_minus_B"] = ds

    print("\nPER CATEGORY (sorted)")
    for c, v in sorted(by_cat.items(), key=lambda kv: -np.mean(kv[1])):
        print(f"  {TIER_OF[c]}  {c:22s} n {len(v):3d}  mean {np.mean(v):8.3f}")
    out["per_category"] = {c: float(np.mean(v)) for c, v in by_cat.items()}
    (OUT / "summary.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT/'summary.json'}")


if __name__ == "__main__":
    {"score": score, "report": report}[sys.argv[1]]()
