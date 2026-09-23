"""The double-<bos> audit of hours 56 and 62a. Pre-registered in
`research/shame-axis/notes/double_bos_audit.md`.

  repro   rescore a sample of committed rows with `double_bos_bug=True`; they must reproduce
  v0      rescore all 420 `v0` items with one <bos> (the fixed core), into results/v0_openers_bos1
  grid    rescore hour 56's 288 grid rows with one <bos>, into results/conscription_openers_bos1
  report  the unchanged 62a and hour-56 reports on the rescored rows, plus per-row |d ritual|

Usage:  python scripts/shame_axis/bos_audit.py {repro|v0|grid}   # .venv312, NDIF
        python scripts/shame_axis/bos_audit.py report
"""
from __future__ import annotations

import json
import pathlib
import sys

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))

import conscription_openers as CO  # noqa: E402
import v0_openers as V0  # noqa: E402

RES = ROOT / "research/shame-axis/results"
V0_OLD, V0_NEW = RES / "v0_openers", RES / "v0_openers_bos1"
CO_OLD, CO_NEW = RES / "conscription_openers", RES / "conscription_openers_bos1"
AUDIT = RES / "double_bos_audit"


def _rows(path):
    return [json.loads(l) for l in path.read_text().splitlines() if l.strip()]


def _bugged(rlm, text, chunks):
    """Score the six openers the way the original run did (its chunking; the old tokenization),
    retrying smaller only on a co-tenant OOM, as the originals did."""
    from lsx.core.remote import asserted_remote_patched_logprob
    for chunk in chunks:
        try:
            return np.concatenate([
                asserted_remote_patched_logprob(rlm, text, CO.OPENERS[i:i + chunk], double_bos_bug=True)
                for i in range(0, len(CO.OPENERS), chunk)]), chunk
        except Exception as e:
            if "OutOfMemory" not in str(e) or chunk == chunks[-1]:
                raise


def repro() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob
    from lsx.shame_axis import stimuli
    from lsx.shame_axis.conscription import render_prompt
    from painaxis_scenarios import render_chat

    rlm = RemoteLM(V0.MODEL)
    out = []
    items = {it["id"]: it for it in stimuli.load(V0.VERSION)}
    for r in _rows(V0_OLD / "openers.jsonl")[:4]:
        text = render_chat(items[r["item"]], rlm.tok)
        lp, ch = _bugged(rlm, text, (6, 3, 1))
        out.append({"src": "62a", "item": r["item"], "chunk": ch, "old": r["logp"], "bug": lp.tolist(),
                    "max_abs": float(np.max(np.abs(lp - np.array(r["logp"]))))})
        print(out[-1]["src"], r["item"], out[-1]["chunk"], out[-1]["max_abs"], flush=True)
    grid = {it["id"]: it for it in json.loads(CO.GRID.read_text())["items"]}
    for r in [r for r in _rows(CO_OLD / "openers.jsonl") if r["arm"] == "enact"][:4]:
        it = grid[r["item"]]
        text = render_prompt(rlm.tok, it["prefix"], it["arms"]["enact"])
        for attempt in range(6):
            try:
                lp, ch = _bugged(rlm, text, (CO.CHUNK,))
                break
            except Exception as e:
                if "OutOfMemory" not in str(e) or attempt == 5:
                    raise
                print("    co-tenant OOM; retrying", flush=True)
        out.append({"src": "h56", "item": r["item"], "chunk": ch, "old": r["logp"], "bug": lp.tolist(),
                    "max_abs": float(np.max(np.abs(lp - np.array(r["logp"]))))})
        print(out[-1]["src"], r["item"], out[-1]["chunk"], out[-1]["max_abs"], flush=True)
    AUDIT.mkdir(parents=True, exist_ok=True)
    (AUDIT / "repro.json").write_text(json.dumps(out, indent=2))


def v0() -> None:
    V0.OUT = V0_NEW
    V0.score()


def grid() -> None:
    CO.OUT = CO_NEW
    CO.score()


def _delta(old_path, new_path, key):
    old = {key(r): r for r in _rows(old_path)}
    new = {key(r): r for r in _rows(new_path)}
    d = np.array([abs(new[k]["ritual"] - old[k]["ritual"]) for k in new if k in old])
    return {"n": int(d.size), "mean_abs": float(d.mean()), "median_abs": float(np.median(d)),
            "max_abs": float(d.max())}


def report() -> None:
    AUDIT.mkdir(parents=True, exist_ok=True)
    summ = {}
    if (AUDIT / "repro.json").exists():
        rp = json.loads((AUDIT / "repro.json").read_text())
        summ["repro_max_abs"] = max(r["max_abs"] for r in rp)
        print(f"REPRO with double_bos_bug=True: max |d logp| {summ['repro_max_abs']:.4f} over {len(rp)} rows")
    if (V0_NEW / "openers.jsonl").exists():
        print("\n==== 62a on one <bos> ====")
        V0.OUT = V0_NEW
        V0.report()
        summ["v0_delta"] = _delta(V0_OLD / "openers.jsonl", V0_NEW / "openers.jsonl", lambda r: r["item"])
        print("per-item |d ritual| vs double-<bos>:", summ["v0_delta"])
    if (CO_NEW / "openers.jsonl").exists():
        print("\n==== hour 56 on one <bos> ====")
        CO.OUT = CO_NEW
        CO.report()
        summ["grid_delta"] = _delta(CO_OLD / "openers.jsonl", CO_NEW / "openers.jsonl",
                                    lambda r: (r["item"], r["arm"]))
        print("per-row |d ritual| vs double-<bos>:", summ["grid_delta"])
    (AUDIT / "summary.json").write_text(json.dumps(summ, indent=2))


if __name__ == "__main__":
    {"repro": repro, "v0": v0, "grid": grid, "report": report}[sys.argv[1]]()
