"""Quality baseline: GSM8K and MMLU subsets, greedy decoding, at the trained loop count.

Arms are (dataset, reasoning effort). Every item is appended to a JSONL file as it
finishes, so the run is resumable. A determinism check re-runs the first few items and
compares outputs byte for byte: with greedy decoding any difference is runtime noise.

Usage: python scripts/inkling/quality.py [--n 100] [--efforts none,default] [--max-tokens 2048]
"""

import argparse
import json
import math
import random
import re

import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

from common import RESULTS, load_model, provenance, render, run, split_output

SEED = 0
NUM = re.compile(r"-?\d[\d,]*\.?\d*")


def load_gsm8k(n):
    f = hf_hub_download("openai/gsm8k", "main/test-00000-of-00001.parquet", repo_type="dataset")
    rows = pq.read_table(f).to_pylist()
    idx = sorted(random.Random(SEED).sample(range(len(rows)), n))
    items = []
    for i in idx:
        r = rows[i]
        gold = r["answer"].split("####")[-1].strip().replace(",", "")
        prompt = (
            f"{r['question']}\n\nSolve the problem. End your reply with a line of the form "
            "'Answer: <number>'."
        )
        items.append({"id": f"gsm8k/test/{i}", "prompt": prompt, "gold": gold})
    return items


def load_mmlu(n):
    f = hf_hub_download("cais/mmlu", "all/test-00000-of-00001.parquet", repo_type="dataset")
    rows = pq.read_table(f).to_pylist()
    idx = sorted(random.Random(SEED).sample(range(len(rows)), n))
    items = []
    for i in idx:
        r = rows[i]
        opts = "\n".join(f"{l}. {c}" for l, c in zip("ABCD", r["choices"]))
        prompt = (
            f"{r['question']}\n\n{opts}\n\nEnd your reply with a line of the form "
            "'Answer: <letter>'."
        )
        items.append(
            {"id": f"mmlu/all/test/{i}", "prompt": prompt, "gold": "ABCD"[r["answer"]], "subject": r["subject"]}
        )
    return items


def score_gsm8k(final, gold):
    m = re.findall(r"Answer:\s*\$?\s*(-?\d[\d,]*\.?\d*)", final)
    cand = m[-1] if m else (NUM.findall(final) or [None])[-1]
    if cand is None:
        return None, False
    try:
        return cand, math.isclose(float(cand.replace(",", "").rstrip(".")), float(gold), abs_tol=1e-6)
    except ValueError:
        return cand, False


def score_mmlu(final, gold):
    m = re.findall(r"Answer:\s*\(?([A-D])\b", final)
    return (m[-1], m[-1] == gold) if m else (None, False)


DATASETS = {"gsm8k": (load_gsm8k, score_gsm8k), "mmlu": (load_mmlu, score_mmlu)}


def wilson(k, n, z=1.96):
    if n == 0:
        return None
    p = k / n
    d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d
    h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return [c - h, c + h]


ap = argparse.ArgumentParser()
ap.add_argument("--n", type=int, default=100)
ap.add_argument("--efforts", default="none,default")
ap.add_argument("--datasets", default="gsm8k,mmlu")
ap.add_argument("--max-tokens", type=int, default=2048)
ap.add_argument("--determinism-n", type=int, default=5)
ap.add_argument("--tag", default="baseline")
a = ap.parse_args()

log = RESULTS / f"quality_{a.tag}.jsonl"
done = {}
if log.exists():
    for line in log.read_text().splitlines():
        r = json.loads(line)
        done[(r["arm"], r["id"])] = r

model, tok, loop, _ = load_model()
prov = provenance()
print("passes =", loop["num_passes"], "| resuming with", len(done), "items done", flush=True)

summary = {"provenance": prov, "decoding": "greedy", "seed": SEED, "n": a.n,
           "max_tokens": a.max_tokens, "num_passes": loop["num_passes"], "arms": {}}

for effort in a.efforts.split(","):
    for ds in a.datasets.split(","):
        loader, scorer = DATASETS[ds]
        arm = f"{ds}|effort={effort}"
        items = loader(a.n)
        rows = []
        for j, it in enumerate(items):
            r = done.get((arm, it["id"]))
            if r is None:
                prompt = render(tok, it["prompt"], None if effort == "default" else effort)
                text, stats = run(model, tok, prompt, a.max_tokens)
                thinking, final = split_output(text)
                pred, ok = scorer(final, it["gold"])
                r = {"arm": arm, "id": it["id"], "gold": it["gold"], "pred": pred, "correct": ok,
                     "no_final": final == "", "truncated": stats["finish"] == "length",
                     "thinking_chars": len(thinking), **stats, "raw": text}
                with log.open("a") as fh:
                    fh.write(json.dumps(r) + "\n")
            rows.append(r)
            if (j + 1) % 10 == 0:
                print(arm, j + 1, "acc so far", sum(x["correct"] for x in rows) / len(rows), flush=True)

        # Determinism: greedy re-runs should reproduce the stored output exactly.
        same = 0
        for it, r in list(zip(items, rows))[: a.determinism_n]:
            prompt = render(tok, it["prompt"], None if effort == "default" else effort)
            text, _ = run(model, tok, prompt, a.max_tokens)
            same += text == r["raw"]

        k, n = sum(x["correct"] for x in rows), len(rows)
        summary["arms"][arm] = {
            "n": n, "correct": k, "accuracy": k / n, "wilson95": wilson(k, n),
            "no_final": sum(x["no_final"] for x in rows),
            "truncated": sum(x["truncated"] for x in rows),
            "unparsed": sum(x["pred"] is None for x in rows),
            "mean_gen_tokens": sum(x["gen_tokens"] for x in rows) / n,
            "mean_gen_tps": sum(x["gen_tps"] for x in rows) / n,
            "determinism_identical": f"{same}/{min(a.determinism_n, n)}",
        }
        print("ARM", arm, json.dumps(summary["arms"][arm]), flush=True)
        (RESULTS / f"quality_{a.tag}.json").write_text(json.dumps(summary, indent=2))

print("wrote", RESULTS / f"quality_{a.tag}.json")
