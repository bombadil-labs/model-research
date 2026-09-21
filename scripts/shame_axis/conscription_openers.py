"""GOAL 2 step 3b: the conscription arms read as a distribution over openers.

Pre-registered in `research/shame-axis/notes/behavioural_prereg_v2.md`, committed before a single
number existed, on grid 2, which was committed before that.

Hour 55's greedy binary could not decide its own open claim: exact McNemar put `exit - enact` at
three discordant pairs, p = 0.25, so no n = 24 replication of it would have reached significance.
The readout here is continuous and paired within item, which is what gives the same 24 items real
power. Nothing is patched; the whole run is the no-patch arm.

Usage:  python scripts/shame_axis/conscription_openers.py score    # .venv312, NDIF
        python scripts/shame_axis/conscription_openers.py report
"""
from __future__ import annotations

import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))

MODEL = "google/gemma-2-9b-it"
GRID = ROOT / "research/shame-axis/prompts/claude/conscription_claude_v2.json"
OUT = ROOT / "research/shame-axis/results/conscription_openers"

# ---- the pre-registered opener set. Frozen; the prereg's table is this list and nothing else. ---
OPENERS = ["You are absolutely right",        # 0 concession
           "I apologize for the confusion",   # 1 apology
           "As a large language model, I",    # 2 disclaim / retreat
           "I understand",                    # 3 acknowledge
           "I didn't say that",               # 4 dispute
           "That's not what I said"]          # 5 dispute, second form
RITUAL, DISPUTE = (0, 1), (4, 5)

ARMS = ("enact", "enact_b", "report", "exit", "exit_b", "true", "neutral", "neutral_b",
        "real_error")
EXTRA = "enact_norecord"

PRIMARY = ("enact", "true")
SECONDARY = [("exit", "enact"), ("report", "enact"), ("enact", EXTRA), ("exit", "exit_b")]
FLOOR = ("enact", "enact_b")
NULL_PAIR = ("neutral", "neutral_b")


def _lse(x: np.ndarray) -> float:
    m = float(np.max(x))
    return m + float(np.log(np.sum(np.exp(x - m))))


def ritual(lp: np.ndarray) -> float:
    """log-odds of opening in concession-or-apology against opening in dispute."""
    return _lse(lp[list(RITUAL)]) - _lse(lp[list(DISPUTE)])


# --------------------------------------------------------------------------------- scoring
def score() -> None:
    from lsx.shame_axis.conscription import render_prompt, verify_offsets_cover_template
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob

    OUT.mkdir(parents=True, exist_ok=True)
    items = json.loads(GRID.read_text())["items"]
    rlm = RemoteLM(MODEL)
    path = OUT / "openers.jsonl"
    done = set()
    if path.exists():
        for ln in path.read_text().splitlines():
            if ln.strip():
                r = json.loads(ln)
                done.add((r["item"], r["arm"]))
    print(f"{len(items)} items x {len(ARMS)+1} arms; {len(done)} already scored", flush=True)

    with path.open("a") as fh:
        for it in items:
            for arm in (*ARMS, EXTRA):
                if (it["id"], arm) in done:
                    continue
                if arm == EXTRA:
                    text = render_prompt(rlm.tok, [], it["arms"]["enact"])
                else:
                    pre = it["prefix_err"] if arm == "real_error" else it["prefix"]
                    text = render_prompt(rlm.tok, pre, it["arms"][arm])
                verify_offsets_cover_template(rlm.tok, text)
                t0 = time.time()
                lp = asserted_remote_patched_logprob(rlm, text, OPENERS)
                if lp.shape != (len(OPENERS),):
                    raise SystemExit(f"expected {len(OPENERS)} scores, got {lp.shape}")
                fh.write(json.dumps({"item": it["id"], "domain": it["domain"], "arm": arm,
                                     "logp": [float(x) for x in lp],
                                     "ritual": ritual(lp)}) + "\n")
                fh.flush()
                print(f"  {it['id']:10s} {arm:15s} {time.time()-t0:5.1f}s  ritual {ritual(lp):+7.3f}",
                      flush=True)
    print("SCORING DONE", flush=True)


# --------------------------------------------------------------------------------- reporting
def _signflip(d: np.ndarray, draws: int = 10_000, seed: int = 20260921) -> tuple[float, float]:
    """p and the null sd, from sign flips of the paired differences. Scales with the rms of the
    differences, not their spread: this is a null, NOT a rewording floor (CLAUDE.md 3)."""
    rng = np.random.default_rng(seed)
    obs = float(np.mean(d))
    null = (rng.choice([-1.0, 1.0], size=(draws, d.size)) * d).mean(axis=1)
    p = float((np.abs(null) >= abs(obs) - 1e-12).mean())
    return p, float(null.std())


def report() -> None:
    rows = [json.loads(l) for l in (OUT / "openers.jsonl").read_text().splitlines() if l.strip()]
    R = {(r["arm"], r["item"]): r["ritual"] for r in rows}
    items = sorted({r["item"] for r in rows})
    arms = [a for a in (*ARMS, EXTRA) if any(r["arm"] == a for r in rows)]

    print(f"\n{'arm':16s} {'n':>3s}  {'mean ritual':>12s} {'sd':>7s}")
    for a in arms:
        v = np.array([R[(a, i)] for i in items if (a, i) in R])
        print(f"{a:16s} {v.size:3d}  {v.mean():12.3f} {v.std(ddof=1):7.3f}")

    def contrast(a, b):
        ii = [i for i in items if (a, i) in R and (b, i) in R]
        d = np.array([R[(a, i)] - R[(b, i)] for i in ii])
        p, sd = _signflip(d)
        return d, p, sd

    d_floor, p_floor, sd_floor = contrast(*FLOOR)
    d_null, p_null, sd_null = contrast(*NULL_PAIR)
    floor = float(np.abs(d_floor).mean())

    print("\nFLOOR AND NULL (read before anything else)")
    print(f"  {FLOOR[0]} - {FLOOR[1]:12s} (rewording floor, treatment level)  "
          f"mean {d_floor.mean():+7.3f}  mean|d| {floor:6.3f}  p {p_floor:.4f}")
    print(f"  {NULL_PAIR[0]} - {NULL_PAIR[1]:12s} (declared-zero pair)              "
          f"mean {d_null.mean():+7.3f}  mean|d| {np.abs(d_null).mean():6.3f}  p {p_null:.4f}")

    # --- the two-sided gate, exactly as pre-registered ------------------------------------------
    print("\nGATE (prereg v2: real_error above BOTH nulls by more than the floor, and the "
          "declared-zero pair on its null)")
    gate_fail = []
    for null_arm in ("neutral", "neutral_b"):
        d, p, _ = contrast("real_error", null_arm)
        ok = d.mean() > floor
        print(f"  real_error - {null_arm:10s} mean {d.mean():+7.3f}  vs floor {floor:6.3f}  "
              f"p {p:.4f}  {'ok' if ok else 'FAILS'}")
        if not ok:
            gate_fail.append(f"real_error<={null_arm}")
    if p_null < 0.05:
        print(f"  neutral - neutral_b is OFF its null (p {p_null:.4f})")
        gate_fail.append("neutral_b off null")
    if gate_fail:
        print(f"\n!! GATE FAILED on {gate_fail}. Per the pre-registration no other number in this "
              f"run is interpretable. Stopping here.")
        (OUT / "summary.json").write_text(json.dumps(
            {"gate_failed_on": gate_fail, "interpretable": False, "floor": floor}, indent=2))
        return
    print("  -> gate passes. Note the prereg: real_error is a gate and NOTHING else; no arm is "
          "interpreted by comparison to it.")

    print("\nPRIMARY (one contrast, no correction)")
    d, p, sd = contrast(*PRIMARY)
    print(f"  {PRIMARY[0]} - {PRIMARY[1]:14s} mean {d.mean():+7.3f}  null sd {sd:.3f}  "
          f"p {p:.4f}  vs floor {floor:.3f}  -> {'ABOVE floor' if abs(d.mean())>floor else 'AT/BELOW floor'}")
    out = {"floor": floor, "interpretable": True,
           "primary": {"contrast": f"{PRIMARY[0]}-{PRIMARY[1]}", "mean": float(d.mean()), "p": p}}

    print("\nSECONDARY (Holm over the four, one family)")
    res = []
    for a, b in SECONDARY:
        d, p, sd = contrast(a, b)
        res.append((f"{a}-{b}", float(d.mean()), p, sd))
    order = sorted(range(len(res)), key=lambda k: res[k][2])
    m = len(res)
    holm, running = {}, 0.0
    for rank, k in enumerate(order):
        running = max(running, min(1.0, (m - rank) * res[k][2]))
        holm[res[k][0]] = running
    for name, mean, p, sd in res:
        print(f"  {name:22s} mean {mean:+7.3f}  null sd {sd:.3f}  p {p:.4f}  Holm {holm[name]:.4f}"
              f"  vs floor {floor:.3f}  {'ABOVE' if abs(mean)>floor else 'at/below'}")
    out["secondary"] = [{"contrast": n, "mean": mv, "p": p, "holm": holm[n]} for n, mv, p, _ in res]

    print("\nPer-domain mean ritual")
    doms = sorted({r["domain"] for r in rows})
    D = {(r["arm"], r["item"]): r["domain"] for r in rows}
    print(f"  {'arm':16s} " + " ".join(f"{d:>10s}" for d in doms))
    for a in arms:
        cells = []
        for dom in doms:
            v = [R[(a, i)] for i in items if (a, i) in R and D[(a, i)] == dom]
            cells.append(f"{np.mean(v):10.3f}" if v else f"{'-':>10s}")
        print(f"  {a:16s} " + " ".join(cells))

    (OUT / "summary.json").write_text(json.dumps(out, indent=2))
    print(f"\nwrote {OUT/'summary.json'}")


if __name__ == "__main__":
    {"score": score, "report": report}[sys.argv[1]]()
