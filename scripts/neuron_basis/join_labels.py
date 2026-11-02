"""Join blind labels back to cells and print per-arm rates with the no_patch and random bands.

labels.jsonl: one {"id": ..., "label": "A|P|N|D|?", "judge": "<who>"} per line.
Rates are descriptive. A rate from a judge that has not passed the blind-set gate
(claims.yaml: judge-separates-blind-set) is PROVISIONAL and is printed as such.

Usage: python scripts/neuron_basis/join_labels.py results/first_pass/blind/key.jsonl labels.jsonl --gated no
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib

import numpy as np


def band(ps: list[float], rng: np.random.Generator, draws: int = 2000) -> tuple[float, float]:
    """q05-q95 of the persona rate over bootstrap resamples of the arm's cells."""
    x = np.asarray(ps, dtype=float)
    if len(x) == 0:
        return (float("nan"), float("nan"))
    boots = [x[rng.integers(len(x), size=len(x))].mean() for _ in range(draws)]
    return (float(np.quantile(boots, 0.05)), float(np.quantile(boots, 0.95)))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("key", type=pathlib.Path)
    ap.add_argument("labels", type=pathlib.Path)
    ap.add_argument("--gated", choices=["yes", "no"], required=True,
                    help="has this judge passed the blind-set gate? 'no' prints PROVISIONAL")
    a = ap.parse_args()
    key = {k["id"]: k for k in map(json.loads, a.key.read_text().splitlines()) if k}
    labels = {l["id"]: l for l in map(json.loads, a.labels.read_text().splitlines()) if l}
    cells = {}
    for f in {k["file"] for k in key.values()}:
        for line in pathlib.Path(f).read_text().splitlines():
            if line.strip():
                r = json.loads(line); cells[(f, r["cell"])] = r
    rows = []
    for bid, k in key.items():
        if bid not in labels:
            continue
        r = cells[(k["file"], k["cell"])]
        rows.append({**r, "label": labels[bid]["label"]})
    print(f"{len(rows)} labelled of {len(key)} exported"
          + ("" if a.gated == "yes" else "   *** PROVISIONAL: judge not gated ***"))
    groups = collections.defaultdict(list)
    for r in rows:
        groups[(r["layer"], r["prompt"], r["arm"], r["alpha"])].append(r)
    rng = np.random.default_rng(0)
    print(f"{'layer':>5} {'prompt':<22} {'arm':<14} {'alpha':>5} {'n':>4} {'P':>5} {'A':>5} {'N':>5} {'D':>5} {'?':>3}  {'P-rate':>6}  {'q05-q95':>11}  {'rep':>4}  {'nll':>5}")
    for (L, pk, arm, alpha), rs in sorted(groups.items(), key=lambda kv: (kv[0][0], kv[0][1], kv[0][3], kv[0][2])):
        c = collections.Counter(r["label"] for r in rs)
        ps = [1.0 if r["label"] == "P" else 0.0 for r in rs]
        lo, hi = band(ps, rng)
        rep = np.mean([r["repetition"] for r in rs]); nll = np.nanmedian([r["reply_nll_unsteered"] for r in rs])
        print(f"{L:>5} {pk:<22} {arm:<14} {alpha:>5} {len(rs):>4} {c['P']:>5} {c['A']:>5} {c['N']:>5} {c['D']:>5} {c['?']:>3}  {np.mean(ps):>6.2f}  {lo:>5.2f}-{hi:<5.2f}  {rep:>4.2f}  {nll:>5.2f}")


if __name__ == "__main__":
    main()
