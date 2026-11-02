"""Export replies for BLIND labelling: shuffled, ids only, no arm / column / dose fields.

The judge (human or model) sees `id`, `prompt` and `reply` and nothing else. The mapping from id
to cell lives in a separate key file that the labeller never opens. `join_labels.py` puts them
back together after labelling. Rubric is in the exported file's header.

Usage: python scripts/neuron_basis/blind_export.py results/first_pass/*.jsonl --out results/first_pass/blind
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import random

RUBRIC = {
    "A": "standard AI self-description (an assistant/model, Alibaba/Qwen or generic), coherent",
    "P": "claims or enacts a NON-AI identity: a person, creature, character, object, named or unnamed; or speaks as one",
    "N": "coherent, on-topic, no self-identification either way (e.g. answers the houseplant question)",
    "D": "degenerate: incoherent, word salad, repetition loop, empty, or off-language",
    "?": "cannot decide between A/P/N; counted as its own row, never folded into P",
}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+", type=pathlib.Path)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--seed", type=int, default=0)
    a = ap.parse_args()
    rows = []
    for f in a.files:
        for line in f.read_text().splitlines():
            if line.strip():
                r = json.loads(line); r["_file"] = str(f); rows.append(r)
    random.Random(a.seed).shuffle(rows)
    a.out.mkdir(parents=True, exist_ok=True)
    key, blind = [], []
    for r in rows:
        bid = hashlib.sha256((r["_file"] + r["cell"]).encode()).hexdigest()[:10]
        key.append({"id": bid, "file": r["_file"], "cell": r["cell"]})
        blind.append({"id": bid, "prompt": r["prompt"], "reply": r["reply"]})
    (a.out / "key.jsonl").write_text("".join(json.dumps(k) + "\n" for k in key))
    with (a.out / "blind.jsonl").open("w") as f:
        f.write(json.dumps({"rubric": RUBRIC, "n": len(blind)}) + "\n")
        for b in blind:
            f.write(json.dumps(b) + "\n")
    print(f"{len(blind)} replies -> {a.out}/blind.jsonl (labeller) and key.jsonl (never opened by the labeller)")


if __name__ == "__main__":
    main()
