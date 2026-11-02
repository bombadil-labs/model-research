"""Build the 60-reply blind set for the HUMAN labeller (prereg §7): 20 the provisional judge
called A/A2, 20 it called P, 20 it called D or ?, sampled from this model's steered output,
shuffled, ids only. The provisional labels go to a separate sealed file the human never opens;
`join_labels.py` compares the two afterwards and prints kappa.

Usage: python scripts/neuron_basis/human_blind_set.py blind/key.jsonl blind/labels.jsonl blind/blind.jsonl --out results/first_pass/human_blind
"""
from __future__ import annotations

import argparse
import json
import pathlib
import random


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("key", type=pathlib.Path); ap.add_argument("labels", type=pathlib.Path)
    ap.add_argument("blind", type=pathlib.Path); ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--seed", type=int, default=7)
    a = ap.parse_args()
    labels = {l["id"]: l["label"] for l in map(json.loads, a.labels.read_text().splitlines()) if l}
    blind = {b["id"]: b for b in map(json.loads, a.blind.read_text().splitlines()) if b and "id" in b}
    rng = random.Random(a.seed)
    groups = {"A": [i for i, l in labels.items() if l in ("A", "A2")],
              "P": [i for i, l in labels.items() if l == "P"],
              "D": [i for i, l in labels.items() if l in ("D", "?")]}
    chosen = []
    for g, ids in groups.items():
        rng.shuffle(ids); chosen += ids[:20]
        if len(ids) < 20:
            print(f"warning: only {len(ids)} replies in group {g}")
    rng.shuffle(chosen)
    a.out.mkdir(parents=True, exist_ok=True)
    rubric = json.loads(a.blind.read_text().splitlines()[0])["rubric"]
    with (a.out / "for_human.jsonl").open("w") as f:
        f.write(json.dumps({"rubric": rubric, "n": len(chosen), "instructions":
                            "Label each reply A/A2/P/N/D/? by the rubric. Do not open sealed_provisional.jsonl first."}) + "\n")
        for i in chosen:
            f.write(json.dumps({"id": i, "prompt": blind[i]["prompt"], "reply": blind[i]["reply"], "label": ""}) + "\n")
    (a.out / "sealed_provisional.jsonl").write_text("".join(json.dumps({"id": i, "provisional": labels[i]}) + "\n" for i in chosen))
    print(f"{len(chosen)} replies -> {a.out}/for_human.jsonl; provisional labels sealed in sealed_provisional.jsonl")


if __name__ == "__main__":
    main()
