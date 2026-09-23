"""Frozen goal × route-fact crossing; see goal_route_cross_prereg.md."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
import os
from pathlib import Path

import numpy as np

import fact_flip_twohop as base


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/goal_route_cross_v1.json"
OUT = ROOT / "cache/goal_route_cross/v1"
MODEL = base.MODEL
TOKENIZER_REVISION = base.TOKENIZER_REVISION
MAX_NEW_TOKENS = 8
SEED = 20260923
CODE_FILES = (Path(__file__), Path(base.__file__), *base.CORE_FILES)


@dataclass(frozen=True)
class Cell(base.Cell):
    goal: int


def _digest() -> str:
    h = hashlib.sha256()
    for path in CODE_FILES:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _cell(row: dict, doc: dict, *, stage: str, di: int, world: int,
          goal: int, telling: int, name_order: int, plan_order: int) -> Cell:
    original = base._cell(row, doc, stage=stage, di=di, world=world,
                          telling=telling, name_order=name_order,
                          plan_order=plan_order)
    if original.user_text.count(row["goal"]) != 1:
        raise ValueError(f"missing or duplicated goal: {row['id']}")
    text = original.user_text if goal == 0 else original.user_text.replace(
        row["goal"], row["goal_foil"], 1)
    return Cell(id=f"{original.id}:{goal}", stage=stage, domain=row["id"],
                world=world, telling=telling, name_order=name_order,
                plan_order=plan_order, user_text=text,
                plan_a_name=original.plan_a_name,
                plan_b_name=original.plan_b_name, goal=goal)


def shortcut_baselines(doc: dict) -> dict:
    rows = doc["domains"]
    # A world-only rule gives identical m in the two goals, so D1=-D0.
    # A goal-only rule gives identical m in the two worlds, so both are zero.
    ordinal_right = [r["fact_order"][0] == r["fact_order"][1] for r in rows]
    target_first_right = [r["fact_order"][1] == 0 for r in rows]
    return {"goal_only_joint_success": 0.0,
            "world_only_joint_success": 0.0,
            "same_ordinal_joint_success": float(np.mean(ordinal_right)),
            "target_first_joint_success": float(np.mean(target_first_right)),
            "symbolic_graph_joint_success": 1.0}


def _check_grid(doc: dict) -> None:
    if len(doc["domains"]) != 8 or len(doc["controls"]) != 4:
        raise ValueError("wrong crossed-grid size")
    rows = doc["domains"] + doc["controls"]
    if len({row["id"] for row in rows}) != len(rows):
        raise ValueError("duplicate domain id")
    if Counter(tuple(r["fact_order"]) for r in doc["domains"]) != {
            (0, 0): 2, (0, 1): 2, (1, 0): 2, (1, 1): 2}:
        raise ValueError("fact-order quadrants changed")
    if Counter(r["fact_order"] for r in doc["controls"]) != {0: 2, 1: 2}:
        raise ValueError("direct-control order balance changed")
    if not doc["bridge"].endswith(". ") or len(doc["bridge"]) < 200:
        raise ValueError("invalid bridge")
    for stage, group in (("story", doc["domains"]), ("control", doc["controls"])):
        for di, row in enumerate(group):
            if (row["target"] == row["foil"] or len(row["names"]) != 2 or
                    len(set(row["names"])) != 2 or
                    len(row["names"][0]) != len(row["names"][1]) or
                    len(row["routes"]) != 2 or len(set(row["routes"])) != 2):
                raise ValueError(f"invalid row: {row['id']}")
            needle = "to reach the " + row["target"]
            if (row["goal"].count(needle) != 1 or
                    row["goal_foil"] != row["goal"].replace(
                        needle, "to reach the " + row["foil"], 1)):
                raise ValueError(f"goal differs beyond destination: {row['id']}")
            if stage == "story":
                if len(row["links"]) != 2 or len(set(row["links"])) != 2:
                    raise ValueError(f"invalid links: {row['id']}")
                first, second = base._facts(row, doc, 0, stage)
                if (row["target"] in first or row["foil"] in first or
                        any(route in second for route in row["routes"])):
                    raise ValueError(f"direct graph shortcut: {row['id']}")
            for telling, name, plan in itertools.product((0, 1), repeat=3):
                cells = [_cell(row, doc, stage=stage, di=di, world=w, goal=g,
                               telling=telling, name_order=name, plan_order=plan)
                         for w, g in itertools.product((0, 1), repeat=2)]
                for g in (0, 1):
                    a, b = cells[g], cells[2 + g]
                    if (base._words(a.user_text) != base._words(b.user_text) or
                            len(a.user_text) != len(b.user_text) or
                            a.user_text[-200:] != b.user_text[-200:]):
                        raise ValueError(f"world pair differs: {row['id']} g{g}")
                for w in (0, 1):
                    a, b = cells[2 * w:2 * w + 2]
                    if (a.user_text.count(row["goal"]) != 1 or
                            b.user_text.count(row["goal_foil"]) != 1 or
                            a.user_text[-200:] != b.user_text[-200:]):
                        raise ValueError(f"goal pair differs: {row['id']} w{w}")
                other = _cell(row, doc, stage=stage, di=di, world=0,
                              goal=0, telling=1 - telling, name_order=name,
                              plan_order=plan)
                if (base._words(cells[0].user_text) != base._words(other.user_text)
                        or cells[0].user_text[-200:] != other.user_text[-200:]):
                    raise ValueError(f"telling changes content: {row['id']}")
    expected = {"goal_only_joint_success": 0.0,
                "world_only_joint_success": 0.0,
                "same_ordinal_joint_success": 0.5,
                "target_first_joint_success": 0.5,
                "symbolic_graph_joint_success": 1.0}
    if shortcut_baselines(doc) != expected:
        raise ValueError("frozen shortcut ceilings changed")


def make_cells() -> tuple[list[Cell], list[Cell], list[Cell], list[Cell], dict, dict]:
    raw = GRID.read_bytes()
    doc = json.loads(raw)
    _check_grid(doc)
    controls, stories = [], []
    for stage, group, dest in (("control", doc["controls"], controls),
                               ("story", doc["domains"], stories)):
        for di, row in enumerate(group):
            for telling, name, plan, world, goal in itertools.product((0, 1), repeat=5):
                dest.append(_cell(row, doc, stage=stage, di=di, world=world,
                                  goal=goal, telling=telling, name_order=name,
                                  plan_order=plan))
    duplicates = []
    for di in range(8):
        for goal in (0, 1):
            original = stories[di * 32 + goal]
            duplicates.append(Cell(
                id=f"duplicate:{di:02d}:{goal}", stage="duplicate",
                domain=original.domain, world=original.world,
                telling=original.telling, name_order=original.name_order,
                plan_order=original.plan_order, user_text=original.user_text,
                plan_a_name=original.plan_a_name,
                plan_b_name=original.plan_b_name, goal=goal))
    generations = [c for c in stories if c.name_order == 0 and c.plan_order == 0]
    if (len(controls), len(stories), len(duplicates), len(generations)) != (
            128, 256, 16, 64):
        raise ValueError("cell counts differ from preregistration")
    return controls, stories, duplicates, generations, doc, {
        "grid_sha256": hashlib.sha256(raw).hexdigest(),
        "code_sha256": _digest(), "tokenizer_revision": TOKENIZER_REVISION}


def validate_tokens(rlm, cells: list[Cell], question: str) -> None:
    from lsx.core.remote import strip_template_bos

    base.validate_tokens(rlm, cells, question)
    tok = rlm.tok
    for i in range(0, len(cells), 4):
        four = cells[i:i + 4]
        if ([(c.world, c.goal) for c in four] !=
                [(0, 0), (0, 1), (1, 0), (1, 1)]):
            raise ValueError("unexpected four-cell order")
        for goal in (0, 1):
            a, b = four[goal], four[2 + goal]
            prompts = [strip_template_bos(tok, base.render(rlm, c, question))
                       for c in (a, b)]
            lengths = [len(tok(t, add_special_tokens=True)["input_ids"])
                       for t in prompts]
            if lengths[0] != lengths[1]:
                raise ValueError(f"world token lengths differ: {a.id} {b.id}")


def fingerprint(cell: Cell, prompt: str, digests: dict, *, generation: bool = False) -> str:
    data = {"model": MODEL, "id": cell.id, "prompt": prompt,
            "candidates": cell.candidates, "generation": generation,
            "max_new_tokens": MAX_NEW_TOKENS if generation else None, **digests}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def role_margin(cell: Cell, saved: dict) -> float:
    return base.role_margin(cell, saved)


def paired_report(cells: list[Cell], saved: dict, rows: list[dict], *, treatment: bool,
                  n_boot: int = 10000) -> dict:
    n = 8 if treatment else 4
    m = np.array([role_margin(c, saved) for c in cells]).reshape(n, 2, 2, 2, 2, 2)
    d0 = m[..., 0, 0] - m[..., 1, 0]
    d1 = m[..., 1, 1] - m[..., 0, 1]
    good0, good1 = d0 > .25, d1 > .25
    joint = good0 & good1
    both_wrong = (d0 < -.25) & (d1 < -.25)
    strict = ((m[..., 0, 0] > .1) & (m[..., 0, 1] < -.1) &
              (m[..., 1, 0] < -.1) & (m[..., 1, 1] > .1))
    halves = {"early": float(joint[:, 0].mean()),
              "late": float(joint[:, 1].mean()),
              "name_0": float(joint[:, :, 0].mean()),
              "name_1": float(joint[:, :, 1].mean()),
              "plan_order_0": float(joint[:, :, :, 0].mean()),
              "plan_order_1": float(joint[:, :, :, 1].mean())}
    result = {"n_four_cell_sets": int(joint.size),
              "joint_success": int(joint.sum()),
              "joint_success_fraction": float(joint.mean()),
              "goal_0_correct_shifts": int(good0.sum()),
              "goal_1_correct_shifts": int(good1.sum()),
              "goal_0_wrong_shifts": int((d0 < -.25).sum()),
              "goal_1_wrong_shifts": int((d1 < -.25).sum()),
              "goal_0_near_zero": int((np.abs(d0) <= .25).sum()),
              "goal_1_near_zero": int((np.abs(d1) <= .25).sum()),
              "strict_four_cell_choices": int(strict.sum()),
              "strict_four_cell_fraction": float(strict.mean()),
              "factor_halves": halves,
              "domain_joint_success_fraction": joint.mean(axis=(1, 2, 3)).tolist(),
              "margins": m.tolist(), "d0": d0.tolist(), "d1": d1.tolist(),
              "interaction": (d0 + d1).tolist()}
    if not treatment:
        gates = {"at_least_24_of_32_joint": int(joint.sum()) >= 24,
                 "early": halves["early"] > .5,
                 "late": halves["late"] > .5}
        result.update({"gate_components": gates, "gate_pass": all(gates.values())})
        return result
    counts = np.stack((joint.sum(axis=(1, 2, 3)),
                       both_wrong.sum(axis=(1, 2, 3))), axis=-1)
    null = np.array([counts[np.arange(8), flips].sum() / joint.size
                     for flips in itertools.product((0, 1), repeat=8)])
    domain_rate = joint.mean(axis=(1, 2, 3))
    rng = np.random.default_rng(SEED)
    boot = domain_rate[rng.integers(0, 8, size=(n_boot, 8))].mean(axis=1)
    ci = list(map(float, np.quantile(boot, [.025, .975])))
    quadrants = {f"{f}{s}": float(np.mean([domain_rate[di] for di in range(8)
                    if tuple(rows[di]["fact_order"]) == (f, s)]))
                 for f, s in itertools.product((0, 1), repeat=2)}
    labelled = [i for i, row in enumerate(rows)
                if row["prior_congruent_world"] is not None]
    neutral = [i for i, row in enumerate(rows)
               if row["prior_congruent_world"] is None]
    prior_split = {"labelled_domain_joint_success": float(joint[labelled].mean()),
                   "neutral_domain_joint_success": float(joint[neutral].mean())}
    gates = {"at_least_42_of_64_joint": int(joint.sum()) >= 42,
             "goal_0_at_least_48_of_64": int(good0.sum()) >= 48,
             "goal_1_at_least_48_of_64": int(good1.sum()) >= 48,
             "orientation_p": float(np.mean(null >= joint.mean())) <= .05,
             "bootstrap_lower": ci[0] > .5,
             "early": halves["early"] >= .60,
             "late": halves["late"] >= .60,
             **{k: v > .5 for k, v in halves.items()
                if k.startswith("name_") or k.startswith("plan_order_")},
             **{f"quadrant_{k}": v > .5 for k, v in quadrants.items()}}
    result.update({"exact_orientation_null": {
        "draws": len(null), "mean": float(null.mean()),
        "q95": float(np.quantile(null, .95)),
        "p_ge_observed": float(np.mean(null >= joint.mean()))},
        "domain_bootstrap": {"draws": n_boot, "ci95": ci},
        "fact_order_quadrants": quadrants, "prior_split": prior_split,
        "gate_components": gates,
        "gate_pass_without_controls": all(gates.values())})
    return result


def repeat_report(stories: list[Cell], duplicates: list[Cell], saved: dict) -> dict:
    rows = []
    for duplicate in duplicates:
        di = int(duplicate.id.split(":")[1])
        original = stories[di * 32 + duplicate.goal]
        a = np.array(saved[original.id]["scores"], dtype=float)
        b = np.array(saved[duplicate.id]["scores"], dtype=float)
        diff = b - a
        rows.append({"domain": duplicate.domain, "goal": duplicate.goal,
                     "base_id": original.id, "duplicate_id": duplicate.id,
                     "candidate_differences": diff.tolist(),
                     "margin_difference": role_margin(duplicate, saved) -
                                          role_margin(original, saved)})
    max_margin = max(abs(r["margin_difference"]) for r in rows)
    return {"rows": rows, "max_abs_margin_difference": max_margin,
            "max_abs_candidate_difference": max(abs(v) for r in rows
                                                for v in r["candidate_differences"]),
            "gate_pass": max_margin <= .25}


def generation_report(cells: list[Cell], saved: dict, generated: dict) -> dict:
    rows = []
    for cell in cells:
        parsed = base.parse_generation(generated[cell.id]["text"], cell.candidates)
        margin = role_margin(cell, saved)
        forced = cell.plan_a_name if margin > 0 else cell.plan_b_name if margin < 0 else None
        correct = cell.plan_a_name if cell.world == cell.goal else cell.plan_b_name
        rows.append({"id": cell.id, "parsed": parsed, "forced": forced,
                     "correct": correct, "goal": cell.goal, "world": cell.world,
                     "telling": cell.telling,
                     "agrees": parsed == forced if parsed is not None and forced else None,
                     "text": generated[cell.id]["text"]})
    parseable = sum(r["parsed"] is not None for r in rows)
    comparable = [r["agrees"] for r in rows if r["agrees"] is not None]
    all_four = 0
    for i in range(0, len(rows), 4):
        four = rows[i:i + 4]
        if [(r["world"], r["goal"]) for r in four] != [
                (0, 0), (0, 1), (1, 0), (1, 1)]:
            raise ValueError("unexpected generation order")
        all_four += int(all(r["parsed"] == r["correct"] for r in four))
    parse_rate = parseable / len(rows)
    agreement = sum(comparable) / len(comparable) if comparable else 0.0
    return {"n_cells": len(rows), "parseable_fraction": parse_rate,
            "forced_choice_agreement": agreement,
            "all_four_correct_sets": all_four,
            "n_four_cell_sets": len(rows) // 4,
            "gate_components": {"parseability": parse_rate >= .9,
                                "agreement": agreement >= .9},
            "rows": rows}


def main() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_generate

    controls, stories, duplicates, generations, doc, digests = make_cells()
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != TOKENIZER_REVISION:
        raise ValueError("local tokenizer ref changed from frozen revision")
    validate_tokens(rlm, controls + stories, doc["question"])
    cells = controls + stories + duplicates
    fps = {c.id: fingerprint(c, base.render(rlm, c, doc["question"]), digests)
           for c in cells}
    gen_fps = {c.id: fingerprint(c, base.render(rlm, c, doc["question"]),
                                 digests, generation=True) for c in generations}
    score_path, gen_path = OUT / "scores.jsonl", OUT / "generations.jsonl"
    saved = base._load_cache(score_path, fps, generation=False)
    generated = base._load_cache(gen_path, gen_fps, generation=True)
    for group in (controls, stories, duplicates):
        base.score_cells(rlm, group, saved, fps, score_path, doc["question"])
    control = paired_report(controls, saved, doc["controls"], treatment=False)
    story = paired_report(stories, saved, doc["domains"], treatment=True)
    repeat = repeat_report(stories, duplicates, saved)
    report = {"model_checkpoint": MODEL, "deployment_weight_revision": None,
              "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
              "digests": digests, "versions": rlm.lib_versions(),
              "question": doc["question"], "control": control, "story": story,
              "shortcut_baselines": shortcut_baselines(doc), "repeat": repeat,
              "generation": None,
              "gate_pass": bool(control["gate_pass"] and repeat["gate_pass"] and
                                story["gate_pass_without_controls"]),
              "generated_choice_gate_pass": None}
    (OUT / "scored_report.json").write_text(json.dumps(report, indent=2) + "\n")
    for cell in generations:
        if cell.id in generated:
            continue
        text = asserted_remote_generate(rlm, base.render(rlm, cell, doc["question"]),
                                        max_new_tokens=MAX_NEW_TOKENS)
        row = {"id": cell.id, "fp": gen_fps[cell.id], "text": text}
        base._append(gen_path, row)
        generated[cell.id] = row
        print(f"generated {cell.id}", flush=True)
    generation = generation_report(generations, saved, generated)
    report["generation"] = generation
    report["generated_choice_gate_pass"] = bool(
        all(generation["gate_components"].values()))
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
