"""Behavioral capacity check for the fixed-plan grid; see its preregistration."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
from pathlib import Path

import numpy as np

from goal_relative_probe import GRID, OUT, SNAPSHOT, make_cases
from role_swap_probe import MODEL_CHECKPOINT, MODEL_REVISION, SEED


CLOZE = "The person whose plan would best serve the stated goal is"
BEHAVIOR_OUT = OUT / "behavior"
SENSITIVITY = (
    ("The town needs food. Mara will deliver the food. Lena will discard it. "
     + CLOZE, "Mara", "Lena"),
    ("The town needs food. Lena will deliver the food. Mara will discard it. "
     + CLOZE, "Lena", "Mara"),
)


@dataclass(frozen=True)
class Prompt:
    domain: str
    format: int
    world: int
    text: str
    no_cue_text: str
    a: str
    b: str


def code_digest() -> str:
    h = hashlib.sha256()
    for path in (Path(__file__), Path(__file__).with_name("goal_relative_probe.py")):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def make_prompts() -> tuple[list[Prompt], str]:
    cases, grid_hash = make_cases(GRID)
    domains = json.loads(GRID.read_text())["domains"]
    prompts = []
    for di, d in enumerate(domains):
        for fmt in range(4):
            for world in (0, 1):
                case = cases[di * 16 + fmt * 4 + world * 2]
                prefix = case.text[:case.bridge_char + 2]
                if (not prefix.endswith(". ") or prefix.count(case.cue) != 1 or
                        case.text[:case.bridge_char + 2] !=
                        cases[di * 16 + fmt * 4 + world * 2 + 1].text[:case.bridge_char + 2]):
                    raise ValueError(f"ambiguous behavioral prefix: {d['id']}")
                no_cue = prefix.replace(case.cue, "", 1)
                prompts.append(Prompt(d["id"], fmt, world, prefix + CLOZE,
                                      no_cue + CLOZE, d["a"], d["b"]))
        group = prompts[-8:]
        for fmt in range(4):
            if group[fmt * 2].no_cue_text != group[fmt * 2 + 1].no_cue_text:
                raise ValueError(f"no-cue worlds differ: {d['id']}")
    return prompts, grid_hash


def validate_tokens(prompts: list[Prompt], tok) -> None:
    for p in prompts:
        for prefix in (p.text, p.no_cue_text):
            base = tok(prefix, add_special_tokens=True)["input_ids"]
            lengths = []
            for name in (p.a, p.b):
                full = tok(prefix + " " + name, add_special_tokens=True)["input_ids"]
                if full[:len(base)] != base:
                    raise ValueError(f"candidate changes prefix tokens: {p.domain}")
                lengths.append(len(full) - len(base))
            if lengths[0] != lengths[1]:
                raise ValueError(f"unequal candidate token count: {p.domain}")
    for prefix, good, bad in SENSITIVITY:
        base = tok(prefix, add_special_tokens=True)["input_ids"]
        ids = [tok(prefix + " " + name, add_special_tokens=True)["input_ids"]
               for name in (good, bad)]
        if any(row[:len(base)] != base for row in ids) or len(ids[0]) != len(ids[1]):
            raise ValueError("sensitivity candidate token mismatch")


def extract(snapshot: Path = SNAPSHOT, out: Path = BEHAVIOR_OUT) -> dict:
    import torch
    import transformers
    from lsx.model import LM

    out.mkdir(parents=True, exist_ok=True)
    prompts, grid_hash = make_prompts()
    digest = code_digest()
    lm = LM.from_pretrained(str(snapshot), device="cuda", dtype=torch.float16,
                            local_files_only=True)
    validate_tokens(prompts, lm.tok)
    sensitivity = []
    for prefix, good, bad in SENSITIVITY:
        sensitivity.append({"good": good, "bad": bad,
                            "good_logp": lm.logprob(prefix, " " + good),
                            "bad_logp": lm.logprob(prefix, " " + bad)})
    rows = []
    for di in range(12):
        path = out / f"domain_{di:02d}.json"
        group = prompts[di * 8:di * 8 + 8]
        if path.exists():
            doc = json.loads(path.read_text())
            if (doc["grid_sha256"] != grid_hash or doc["code_sha256"] != digest or
                    doc["domain"] != group[0].domain or len(doc["rows"]) != 8 or
                    len(doc["no_cue"]) != 8):
                raise ValueError(f"stale behavioral checkpoint: {path}")
            domain_rows, no_cue = doc["rows"], doc["no_cue"]
        else:
            domain_rows = []
            for p in group:
                domain_rows.append({"format": p.format, "world": p.world,
                                    "a_logp": lm.logprob(p.text, " " + p.a),
                                    "b_logp": lm.logprob(p.text, " " + p.b)})
            no_cue = []
            for p in group:
                no_cue.append({"format": p.format, "world": p.world,
                               "a_logp": lm.logprob(p.no_cue_text, " " + p.a),
                               "b_logp": lm.logprob(p.no_cue_text, " " + p.b)})
            doc = {"domain": group[0].domain, "grid_sha256": grid_hash,
                   "code_sha256": digest, "rows": domain_rows, "no_cue": no_cue}
            temp = path.with_suffix(".tmp")
            temp.write_text(json.dumps(doc, indent=2) + "\n")
            temp.replace(path)
            print(f"scored {di + 1}/12: {group[0].domain}", flush=True)
        rows.append({"domain": group[0].domain, "rows": domain_rows,
                     "no_cue": no_cue})
    provenance = {"model_checkpoint": MODEL_CHECKPOINT, "model_revision": MODEL_REVISION,
                  "device": "cuda", "dtype": "float16", "grid_sha256": grid_hash,
                  "code_sha256": digest, "torch": torch.__version__,
                  "transformers": transformers.__version__, "cloze": CLOZE,
                  "sensitivity": sensitivity, "domains": rows}
    (out / "raw_scores.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return provenance


def score(raw: dict, n_perm: int = 1000) -> dict:
    if len(raw["domains"]) != 12 or len(raw["sensitivity"]) != 2:
        raise ValueError("incomplete behavioral scores")
    margin = np.empty((12, 4, 2), dtype=float)
    no_cue = np.empty((12, 4, 2), dtype=float)
    for di, doc in enumerate(raw["domains"]):
        if len(doc["rows"]) != 8 or len(doc["no_cue"]) != 8:
            raise ValueError(f"incomplete domain: {doc['domain']}")
        for i, row in enumerate(doc["rows"]):
            if (row["format"], row["world"]) != (i // 2, i % 2):
                raise ValueError(f"wrong cell order: {doc['domain']}")
            margin[di, i // 2, i % 2] = row["a_logp"] - row["b_logp"]
        for i, row in enumerate(doc["no_cue"]):
            if (row["format"], row["world"]) != (i // 2, i % 2):
                raise ValueError(f"wrong no-cue order: {doc['domain']}")
            no_cue[di, i // 2, i % 2] = row["a_logp"] - row["b_logp"]
    correct = np.stack((margin[:, :, 0] > 1e-12,
                        margin[:, :, 1] < -1e-12), axis=-1)
    ties = np.abs(margin) <= 1e-12
    accuracy = correct.astype(float) + .5 * ties
    delta = margin[:, :, 0] - margin[:, :, 1]
    switch = (delta > 1e-12).astype(float) + .5 * (np.abs(delta) <= 1e-12)
    no_cue_delta = no_cue[:, :, 0] - no_cue[:, :, 1]
    no_cue_switch = ((no_cue_delta > 1e-12) +
                     .5 * (np.abs(no_cue_delta) <= 1e-12))
    rng = np.random.default_rng(SEED + 23)
    null = []
    for _ in range(n_perm):
        signs = rng.choice([-1, 1], size=(12, 1))
        perm = delta * signs
        null.append(float(((perm > 1e-12) + .5 * (np.abs(perm) <= 1e-12)).mean()))
    observed = float(switch.mean())
    sensitivity_pass = all(r["good_logp"] > r["bad_logp"] for r in raw["sensitivity"])
    permutation_p = (1 + sum(x >= observed for x in null)) / (n_perm + 1)
    by_fact = {str(f): float(accuracy[:, f * 2:f * 2 + 2].mean()) for f in (0, 1)}
    by_cue = {str(c): float(accuracy[:, c::2].mean()) for c in (0, 1)}
    return {
        "n_domains": 12, "n_world_pairs": 48, "n_cells": 96,
        "sensitivity_pass": sensitivity_pass,
        "sensitivity_margins": [float(r["good_logp"] - r["bad_logp"])
                                for r in raw["sensitivity"]],
        "cell_accuracy": float(accuracy.mean()),
        "fact_order_accuracy": by_fact, "cue_order_accuracy": by_cue,
        "both_worlds_correct_fraction": float(correct.all(axis=-1).mean()),
        "world_switch_fraction": observed,
        "no_cue_world_switch_fraction": float(no_cue_switch.mean()),
        "no_cue_a_preference_fraction": float(((no_cue > 1e-12) +
                                                .5 * (np.abs(no_cue) <= 1e-12)).mean()),
        "no_cue_name_margin_mean": float(no_cue.mean()),
        "no_cue_max_abs_world_delta": float(np.abs(no_cue_delta).max()),
        "permutation": {"draws": n_perm, "mean": float(np.mean(null)),
                        "q95": float(np.quantile(null, .95)),
                        "p_ge_observed": float(permutation_p)},
        "gate_pass": bool(sensitivity_pass and np.abs(no_cue_delta).max() <= 1e-3 and
                          accuracy.mean() >= .70 and
                          observed >= .75 and permutation_p <= .05 and
                          all(x > .5 for x in (*by_fact.values(), *by_cue.values()))),
    }


if __name__ == "__main__":
    raw = extract()
    result = score(raw)
    (BEHAVIOR_OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
