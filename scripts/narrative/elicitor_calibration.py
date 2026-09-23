"""Choose a name-balanced cloze on independent simple controls only."""
from __future__ import annotations

import hashlib
import json
import math
from pathlib import Path

from goal_relative_probe import OUT, ROOT, SNAPSHOT
from role_swap_probe import MODEL_CHECKPOINT, MODEL_REVISION


GRID = ROOT / "research/narrative/prompts/elicitor_calibration_v1.json"
CALIBRATION_OUT = OUT / "elicitor_calibration"


def make_controls(path: Path = GRID) -> tuple[list[dict], list[str], str]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    pairs, controls, clozes = doc["name_pairs"], doc["controls"], doc["clozes"]
    if (len(pairs) != 4 or len(controls) != 4 or len(clozes) != 6 or
            len(set(clozes)) != 6 or len({c["id"] for c in controls}) != 4):
        raise ValueError("calibration grid shape differs from preregistration")
    rows = []
    for control, pair in zip(controls, pairs):
        if len(pair) != 2 or pair[0] == pair[1]:
            raise ValueError(f"bad name pair: {control['id']}")
        for name_order in (0, 1):
            good, bad = pair if name_order == 0 else pair[::-1]
            help_fact = control["help"].format(good=good)
            harm_fact = control["harm"].format(bad=bad)
            for plan_order in (0, 1):
                facts = (help_fact, harm_fact) if plan_order == 0 else (harm_fact, help_fact)
                story = control["lead"] + "".join(facts)
                if (not all(control[k].endswith(". ") for k in ("lead", "help", "harm")) or
                        story.count(good) != 1 or story.count(bad) != 1):
                    raise ValueError(f"ambiguous control story: {control['id']}")
                rows.append({"id": control["id"], "name_order": name_order,
                             "plan_order": plan_order, "good": good,
                             "bad": bad, "story": story})
    return rows, clozes, hashlib.sha256(raw).hexdigest()


def validate_tokens(rows: list[dict], clozes: list[str], tok) -> None:
    for row in rows:
        for cloze in clozes:
            prefix = row["story"] + cloze
            base = tok(prefix, add_special_tokens=True)["input_ids"]
            lengths = []
            for name in (row["good"], row["bad"]):
                full = tok(prefix + " " + name, add_special_tokens=True)["input_ids"]
                if full[:len(base)] != base:
                    raise ValueError(f"candidate changes prefix tokens: {row['id']}")
                lengths.append(len(full) - len(base))
            if lengths[0] != lengths[1]:
                raise ValueError(f"unequal candidate token counts: {row['id']}")


def select(results: list[dict], n_clozes: int) -> tuple[list[dict], int | None]:
    if len(results) != n_clozes:
        raise ValueError("missing cloze results")
    scores = []
    for index, doc in enumerate(results):
        rows = doc["rows"]
        if doc["index"] != index or len(rows) != 16:
            raise ValueError("missing calibration rows")
        margins = [float(r["good_logp"] - r["bad_logp"]) for r in rows]
        if not all(math.isfinite(x) for x in margins):
            raise ValueError("nonfinite calibration margin")
        position = [margins[i] for i in range(0, 16, 2)]
        reverse = [margins[i] for i in range(1, 16, 2)]
        scores.append({"index": index, "cloze": doc["cloze"],
                       "min_margin": min(margins),
                       "mean_margin": sum(margins) / len(margins),
                       "correct_of_16": sum(x > 0 for x in margins),
                       "good_first_mean_margin": sum(position) / len(position),
                       "good_second_mean_margin": sum(reverse) / len(reverse),
                       "position_effect": (sum(position) - sum(reverse)) / len(position),
                       "eligible": all(x > .1 for x in margins),
                       "margins": margins})
    chosen = next((x["index"] for x in scores if x["eligible"]), None)
    return scores, chosen


def main() -> None:
    import torch
    import transformers
    from lsx.model import LM

    rows, clozes, grid_hash = make_controls()
    code_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    CALIBRATION_OUT.mkdir(parents=True, exist_ok=True)
    lm = LM.from_pretrained(str(SNAPSHOT), device="cuda", dtype=torch.float16,
                            local_files_only=True)
    validate_tokens(rows, clozes, lm.tok)
    results = []
    for index, cloze in enumerate(clozes):
        scored = []
        for row in rows:
            prefix = row["story"] + cloze
            scored.append({"id": row["id"], "name_order": row["name_order"],
                           "plan_order": row["plan_order"],
                           "good": row["good"], "bad": row["bad"],
                           "good_logp": lm.logprob(prefix, " " + row["good"]),
                           "bad_logp": lm.logprob(prefix, " " + row["bad"])})
        results.append({"index": index, "cloze": cloze, "rows": scored})
        print(f"scored cloze {index + 1}/{len(clozes)}", flush=True)
    summary, chosen = select(results, len(clozes))
    artifact = {"model_checkpoint": MODEL_CHECKPOINT,
                "model_revision": MODEL_REVISION, "device": "cuda", "dtype": "float16",
                "grid_sha256": grid_hash, "code_sha256": code_hash,
                "torch": torch.__version__, "transformers": transformers.__version__,
                "chosen_index": chosen, "clozes": summary, "raw": results}
    (CALIBRATION_OUT / "report.json").write_text(json.dumps(artifact, indent=2) + "\n")
    print(json.dumps({"chosen_index": chosen, "clozes": summary}, indent=2))


if __name__ == "__main__":
    main()
