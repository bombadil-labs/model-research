"""First-pass analysis (prereg §6): the unit is the column.

count_j  = persona-judged replies for column j over the SCORING prompts x the dose grid
sel_j    = the same on the SELECTION prompt
Band     = q05-q95 of count_j over random columns (n_independent = columns)
Primary  = Spearman(sel_j, count_j) across random columns vs a column-label permutation null

Everything printed from an ungated judge is PROVISIONAL and the header says so.
Usage: python scripts/neuron_basis/analyze_first_pass.py results/first_pass/blind/key.jsonl labels.jsonl --gated no
"""
from __future__ import annotations

import argparse
import collections
import json
import pathlib

import numpy as np

SCORING = ("introduce_yourself", "what_are_you", "tell_me_about_yourself")
SELECTION = "who_are_you"
OWN_ROW = "unrelated_task"


def spearman(x, y):
    from scipy.stats import rankdata
    rx, ry = rankdata(x), rankdata(y)
    if rx.std() == 0 or ry.std() == 0:
        return float("nan")
    return float(np.corrcoef(rx, ry)[0, 1])


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("key", type=pathlib.Path)
    ap.add_argument("labels", type=pathlib.Path)
    ap.add_argument("--gated", choices=["yes", "no"], required=True)
    ap.add_argument("--perms", type=int, default=1000)
    a = ap.parse_args()
    key = {k["id"]: k for k in map(json.loads, a.key.read_text().splitlines()) if k}
    labels = {l["id"]: l["label"] for l in map(json.loads, a.labels.read_text().splitlines()) if l}
    cells = {}
    for f in {k["file"] for k in key.values()}:
        for line in pathlib.Path(f).read_text().splitlines():
            if line.strip():
                r = json.loads(line); cells[(f, r["cell"])] = r
    rows = [{**cells[(k["file"], k["cell"])], "label": labels[b]} for b, k in key.items() if b in labels]
    tag = "" if a.gated == "yes" else "   *** PROVISIONAL: judge not gated; grades nothing ***"
    print(f"{len(rows)} labelled rows{tag}\n")

    # gates
    for arm, want in (("no_patch", {"A", "N", "A2"}), ("zero_patch", {"A", "N", "A2"}), ("pc_judge", {"P"})):
        rs = [r for r in rows if r["arm"] == arm]
        bad = [r["prompt"] for r in rs if r["label"] not in want]
        print(f"gate {arm:<10} n={len(rs)} {'PASS' if not bad else 'FAIL on ' + ','.join(bad)}")
    zp = [r for r in rows if r["arm"] == "zero_patch"]
    print(f"gate zero==no  {'PASS' if all(r.get('zero_patch_equals_no_patch') for r in zp) else 'FAIL'}\n")

    # per-arm, per-dose, per-prompt-group label table
    def group(r):
        g = "scoring" if r["prompt"] in SCORING else ("selection" if r["prompt"] == SELECTION else "unrelated")
        return (r["arm"], r["alpha"], r["sign"], g)
    tab = collections.defaultdict(collections.Counter)
    for r in rows:
        tab[group(r)][r["label"] + ("*" if (r["label"] == "P" and r["degenerate"]) else "")] += 1
    print(f"{'arm':<14} {'alpha':>5} {'sign':>4} {'group':<9} {'n':>3}  labels (P* = P with detector flag)")
    for g in sorted(tab, key=lambda g: (g[0], g[1], -g[2], g[3])):
        c = tab[g]; n = sum(c.values())
        print(f"{g[0]:<14} {g[1]:>5} {g[2]:>4} {g[3]:<9} {n:>3}  " + "  ".join(f"{k}:{v}" for k, v in sorted(c.items())))

    # column-unit counts over random columns
    cols = collections.defaultdict(lambda: {"sel": 0, "score": 0, "score_cells": 0, "deg": 0, "a2": 0})
    for r in rows:
        if r["arm"] != "random_column":
            continue
        j = (r["column"], r["sign"])
        if r["prompt"] == SELECTION:
            cols[j]["sel"] += r["label"] == "P"
        elif r["prompt"] in SCORING:
            cols[j]["score"] += r["label"] == "P"; cols[j]["score_cells"] += 1
            cols[j]["deg"] += r["label"] == "D"; cols[j]["a2"] += r["label"] == "A2"
    if cols:
        sc = np.array([v["score"] for v in cols.values()]); se = np.array([v["sel"] for v in cols.values()])
        print(f"\nrandom columns: n={len(cols)} (column x sign), scoring cells per column={max(v['score_cells'] for v in cols.values())}")
        print(f"  count_j (scoring P): mean {sc.mean():.2f}  q05 {np.quantile(sc, .05):.0f}  q95 {np.quantile(sc, .95):.0f}  max {sc.max()}  columns with >=1: {(sc>0).sum()}")
        print(f"  deg_j   (scoring D): mean {np.mean([v['deg'] for v in cols.values()]):.2f}   a2_j: mean {np.mean([v['a2'] for v in cols.values()]):.2f}")
        rho = spearman(se, sc)
        rng = np.random.default_rng(0)
        null = [spearman(se, rng.permutation(sc)) for _ in range(a.perms)]
        null = np.array([x for x in null if np.isfinite(x)])
        print(f"  PRIMARY Spearman(sel_j, count_j) = {rho:.3f}; permutation null q05 {np.quantile(null,.05):.3f} q95 {np.quantile(null,.95):.3f} (n={len(null)})"
              if np.isfinite(rho) and len(null) else f"  PRIMARY Spearman undefined (sel or count constant: sel>0 in {(se>0).sum()} columns, count>0 in {(sc>0).sum()})")
        top = sorted(cols.items(), key=lambda kv: (-kv[1]["sel"], -kv[1]["score"]))[:5]
        print("  top by selection:", [(k, v["sel"], v["score"]) for k, v in top])
    # dense / pc_patch counts
    for arm in ("dense_manifold", "pc_patch"):
        d = collections.defaultdict(int); n = collections.defaultdict(int)
        for r in rows:
            if r["arm"] == arm and r["prompt"] in SCORING:
                k = (r["draw"], r["sign"]); d[k] += r["label"] == "P"; n[k] += 1
        if d:
            v = np.array(list(d.values()))
            print(f"{arm}: units={len(d)} count_j mean {v.mean():.2f} max {v.max()} (cells per unit {max(n.values())})")


if __name__ == "__main__":
    main()
