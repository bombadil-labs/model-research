"""Speed baseline: load time, decode tok/s, prefill tok/s by prompt length, peak memory,
and decode tok/s by loop count. Greedy decoding, repeated so the spread is visible.

Usage: python scripts/inkling/speed.py [--quick]
"""

import argparse
import json
import statistics as st

from common import RESULTS, load_model, provenance, render, run

FILLER = (
    "The survey team crossed the ridge at dawn and logged the first of the day's readings. "
    "Wind out of the north-west held steady at eleven knots while the barometer fell slowly. "
    "By noon the instruments at the lower camp had been recalibrated against the reference set. "
    "Each entry in the ledger carries a station code, a timestamp and the observer's initials. "
)
ESSAY = "Write a long, detailed essay on the history of bridge engineering."


def summarize(xs):
    return {
        "mean": st.mean(xs),
        "sd": st.stdev(xs) if len(xs) > 1 else None,
        "min": min(xs),
        "max": max(xs),
        "n": len(xs),
        "values": xs,
    }


def long_prompt(tok, n_tokens):
    ids = tok.encode(FILLER * (n_tokens // 40 + 8))[:n_tokens]
    return render(tok, tok.decode(ids) + "\n\nSummarize the log above in one sentence.")


ap = argparse.ArgumentParser()
ap.add_argument("--quick", action="store_true")
a = ap.parse_args()

model, tok, loop, load_s = load_model()
out = {"provenance": provenance(), "load_seconds_warm_cache": load_s, "decoding": "greedy"}
trained_passes = loop["num_passes"]
print("loaded in", round(load_s, 1), "s; passes =", trained_passes, flush=True)

# Warm-up: the first call compiles kernels and is not representative.
run(model, tok, render(tok, "Say hi."), 16)

# 1. Decode speed at the trained loop count.
reps = 2 if a.quick else 5
gen_n = 64 if a.quick else 256
rs = [run(model, tok, render(tok, ESSAY), gen_n)[1] for _ in range(reps)]
out["decode"] = {
    "gen_tokens": gen_n,
    "gen_tps": summarize([r["gen_tps"] for r in rs]),
    "peak_gb": max(r["peak_gb"] for r in rs),
}
print("decode", out["decode"]["gen_tps"], flush=True)

# 2. Prefill speed and memory by prompt length (fresh cache every run).
out["prefill"] = []
plan = [(512, 2)] if a.quick else [(512, 3), (2048, 3), (8192, 3), (32768, 1)]
for n, reps in plan:
    p = long_prompt(tok, n)
    rs = [run(model, tok, p, 64)[1] for _ in range(reps)]
    row = {
        "target_tokens": n,
        "prompt_tokens": rs[0]["prompt_tokens"],
        "prompt_tps": summarize([r["prompt_tps"] for r in rs]),
        "gen_tps_after": summarize([r["gen_tps"] for r in rs]),
        "peak_gb": max(r["peak_gb"] for r in rs),
    }
    out["prefill"].append(row)
    print("prefill", n, row["prompt_tps"]["mean"], row["gen_tps_after"]["mean"], row["peak_gb"], flush=True)

# 3. Decode speed by loop count. Only the trained count is in-distribution.
out["decode_by_passes"] = []
for passes in [1, 2] if a.quick else [1, 2, 3, 4, 5]:
    loop["num_passes"] = passes
    rs = [run(model, tok, render(tok, ESSAY), gen_n)[1] for _ in range(2 if a.quick else 3)]
    row = {
        "passes": passes,
        "in_distribution": passes == trained_passes,
        "gen_tps": summarize([r["gen_tps"] for r in rs]),
        "peak_gb": max(r["peak_gb"] for r in rs),
    }
    out["decode_by_passes"].append(row)
    print("passes", passes, row["gen_tps"]["mean"], flush=True)
loop["num_passes"] = trained_passes

path = RESULTS / ("speed_quick.json" if a.quick else "speed_baseline.json")
path.write_text(json.dumps(out, indent=2))
print("wrote", path)
