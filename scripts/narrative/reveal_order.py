"""Frozen chronological versus late-reveal behavior test; see reveal_order_prereg.md."""
from __future__ import annotations

from collections import Counter
import hashlib
import itertools
import json
import os
from pathlib import Path

import numpy as np

import fact_flip_twohop as base
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/reveal_order_v1.json"
SOURCE = cross.GRID
OUT = ROOT / "cache/reveal_order/v1"
MODEL = cross.MODEL
TOKENIZER_REVISION = cross.TOKENIZER_REVISION
SEED = 20260923
FORMATS = ("chronological", "late_reveal", "near_adjacent")


def _digests() -> dict:
    h = hashlib.sha256()
    for path in (Path(__file__), Path(base.__file__), Path(cross.__file__),
                 *base.CORE_FILES):
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return {"source_grid_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
            "reveal_grid_sha256": hashlib.sha256(GRID.read_bytes()).hexdigest(),
            "code_sha256": h.hexdigest(),
            "tokenizer_revision": TOKENIZER_REVISION}


def _cell(row: dict, source: dict, reveal: dict, *, stage: str, di: int,
          fmt: int, name: int, plan: int, world: int, goal: int) -> cross.Cell:
    names = row["names"] if name == 0 else row["names"][::-1]
    clauses = [source["plan_template"].format(name=n, route=r)
               for n, r in zip(names, row["routes"])]
    plans = "".join(clauses if plan == 0 else clauses[::-1])
    first, second = base._facts(row, source, world, stage)
    values = {"setup": row["setup"],
              "goal": row["goal"] if goal == 0 else row["goal_foil"],
              "plans": plans, "first_hop": first, "second_hop": second,
              "interlude": reveal["interlude"], "closing": reveal["closing"]}
    text = reveal[FORMATS[fmt] + "_template"].format(**values)
    return cross.Cell(id=f"{stage}:{di:02d}:{fmt}:{name}:{plan}:{world}:{goal}",
                      stage=stage, domain=row["id"], world=world,
                      telling=fmt, name_order=name, plan_order=plan,
                      user_text=text, plan_a_name=names[0],
                      plan_b_name=names[1], goal=goal)


def _word_interaction(cells: list[cross.Cell], *, suffix: bool) -> int:
    if len(cells) != 4 or [(c.world, c.goal) for c in cells] != [
            (0, 0), (0, 1), (1, 0), (1, 1)]:
        raise ValueError("wrong factorial quartet")
    bags = [base._words(c.user_text[-200:] if suffix else c.user_text)
            for c in cells]
    words = set().union(*(b.keys() for b in bags))
    return sum(abs(bags[0][w] - bags[1][w] - bags[2][w] + bags[3][w])
               for w in words)


def make_cells() -> tuple[list[cross.Cell], list[cross.Cell], list[cross.Cell],
                          dict, dict, dict]:
    source = json.loads(SOURCE.read_bytes())
    reveal = json.loads(GRID.read_bytes())
    cross._check_grid(source)
    if reveal["source_grid"] != SOURCE.name or reveal["interlude"] != source["bridge"]:
        raise ValueError("source grid or interlude changed")
    if (len(reveal["closing"]) < 200 or
            not reveal["closing"].endswith(". ")):
        raise ValueError("closing must protect a common 200-character suffix")
    expected_templates = {
        "chronological_template": "{setup}{goal}{plans}{first_hop}{second_hop}{interlude}{closing}",
        "late_reveal_template": "{setup}{goal}{plans}{first_hop}{interlude}{second_hop}{closing}",
        "near_adjacent_template": "{setup}{goal}{plans}{interlude}{first_hop}{second_hop}{closing}"}
    if {k: reveal.get(k) for k in expected_templates} != expected_templates:
        raise ValueError("presentation templates changed")
    groups = []
    bag_values = {"full": [], "suffix": []}
    for stage, rows in (("control", source["controls"]),
                        ("story", source["domains"])):
        cells = []
        for di, row in enumerate(rows):
            for fmt, name, plan in itertools.product(range(3), (0, 1), (0, 1)):
                four = [_cell(row, source, reveal, stage=stage, di=di,
                              fmt=fmt, name=name, plan=plan, world=w, goal=g)
                        for w, g in itertools.product((0, 1), repeat=2)]
                cells.extend(four)
                for c in four:
                    if (c.user_text.count(c.plan_a_name) != 1 or
                            c.user_text.count(c.plan_b_name) != 1):
                        raise ValueError(f"name count differs: {c.id}")
                    first, second = base._facts(row, source, c.world, stage)
                    if (c.user_text.count(second) != 1 or
                            (first and c.user_text.count(first) != 1) or
                            c.user_text.count(reveal["interlude"]) != 1):
                        raise ValueError(f"fact or interlude missing: {c.id}")
                    names = row["names"] if c.name_order == 0 else row["names"][::-1]
                    plan_clauses = [source["plan_template"].format(name=n, route=r)
                                    for n, r in zip(names, row["routes"])]
                    if any(c.user_text.count(clause) != 1 for clause in plan_clauses):
                        raise ValueError(f"plan clause missing: {c.id}")
                    interlude = c.user_text.index(reveal["interlude"])
                    second_at = c.user_text.index(second)
                    if (interlude < second_at) != (fmt != 0):
                        raise ValueError(f"disclosure order changed: {c.id}")
                    if first:
                        first_at = c.user_text.index(first)
                        if (interlude < first_at) != (fmt == 2):
                            raise ValueError(f"first-hop order changed: {c.id}")
                for goal in (0, 1):
                    a, b = four[goal], four[2 + goal]
                    if (base._words(a.user_text) != base._words(b.user_text) or
                            len(a.user_text) != len(b.user_text) or
                            a.user_text[-200:] != b.user_text[-200:]):
                        raise ValueError(f"world pair differs: {a.id}")
                bag_values["full"].append(_word_interaction(four, suffix=False))
                bag_values["suffix"].append(_word_interaction(four, suffix=True))
        if len(cells) != len(rows) * 48:
            raise ValueError("incorrect cell count")
        groups.append(cells)
    controls, stories = groups
    for stage, cells, rows in (("control", controls, source["controls"]),
                               ("story", stories, source["domains"])):
        for di, row in enumerate(rows):
            for name, plan, world, goal in itertools.product((0, 1), repeat=4):
                i = di * 48 + name * 8 + plan * 4 + world * 2 + goal
                format_cells = [cells[i + fmt * 16] for fmt in range(3)]
                if (any(base._words(format_cells[0].user_text) != base._words(c.user_text)
                        or len(format_cells[0].user_text) != len(c.user_text)
                        or format_cells[0].user_text[-200:] != c.user_text[-200:]
                        for c in format_cells[1:])):
                    raise ValueError(f"format text differs beyond order: {stage} {row['id']}")
    duplicates = []
    for di, fmt in itertools.product(range(8), range(3)):
        original = stories[di * 48 + fmt * 16]
        duplicates.append(cross.Cell(
            id=f"repeat:{di:02d}:{fmt}", stage="repeat",
            domain=original.domain, world=0, telling=fmt, name_order=0,
            plan_order=0, user_text=original.user_text,
            plan_a_name=original.plan_a_name,
            plan_b_name=original.plan_b_name, goal=0))
    if (len(controls), len(stories), len(duplicates)) != (192, 384, 24):
        raise ValueError("wrong frozen counts")
    bags = {"full_interaction_l1_max": max(bag_values["full"]),
            "suffix_interaction_l1_max": max(bag_values["suffix"]),
            "n_measured_quartets": len(bag_values["full"])}
    return controls, stories, duplicates, source, _digests(), bags


def _null(good: np.ndarray, wrong: np.ndarray) -> dict:
    if good.shape != wrong.shape or good.shape[0] != 8:
        raise ValueError("null requires eight paired domains")
    observed = float(good.mean())
    counts = np.stack((good.sum(axis=tuple(range(1, good.ndim))),
                       wrong.sum(axis=tuple(range(1, wrong.ndim)))), axis=-1)
    null = np.array([counts[np.arange(8), signs].sum() / good.size
                     for signs in itertools.product((0, 1), repeat=8)])
    # product's identity is all 0, unlike a +/- sign enumeration.
    if null[0] != observed:
        raise ValueError("identity orientation null disagrees")
    return {"draws": 256, "mean": float(null.mean()),
            "q95": float(np.quantile(null, .95)),
            "p_ge_observed": float(np.mean(null >= observed))}


def _bootstrap(domain_values: np.ndarray, *, seed: int) -> dict:
    rng = np.random.default_rng(seed)
    n = len(domain_values)
    boot = domain_values[rng.integers(0, n, size=(10000, n))].mean(axis=1)
    return {"draws": 10000,
            "ci95": list(map(float, np.quantile(boot, [.025, .975])))}


def report_group(cells: list[cross.Cell], saved: dict, rows: list[dict],
                 *, treatment: bool) -> dict:
    n = 8 if treatment else 4
    m = np.array([cross.role_margin(c, saved) for c in cells]).reshape(
        n, 3, 2, 2, 2, 2)
    d0 = m[..., 0, 0] - m[..., 1, 0]
    d1 = m[..., 1, 1] - m[..., 0, 1]
    good = (d0 > .25) & (d1 > .25)
    wrong = (d0 < -.25) & (d1 < -.25)
    strict = ((m[..., 0, 0] > .1) & (m[..., 0, 1] < -.1) &
              (m[..., 1, 0] < -.1) & (m[..., 1, 1] > .1))
    all_formats = good.all(axis=1)
    all_wrong = wrong.all(axis=1)
    domain_rate = good.mean(axis=(2, 3))
    paired_rate = all_formats.mean(axis=(1, 2))
    format_names = dict(zip(FORMATS, range(3)))
    formats = {}
    for label, fmt in format_names.items():
        x = good[:, fmt]
        halves = {"name_0": float(x[:, 0].mean()),
                  "name_1": float(x[:, 1].mean()),
                  "plan_order_0": float(x[:, :, 0].mean()),
                  "plan_order_1": float(x[:, :, 1].mean())}
        entry = {"joint_success": int(x.sum()),
                 "joint_success_fraction": float(x.mean()),
                 "strict_four_cell_choices": int(strict[:, fmt].sum()),
                 "strict_four_cell_fraction": float(strict[:, fmt].mean()),
                 "goal_0_correct_shifts": int((d0[:, fmt] > .25).sum()),
                 "goal_1_correct_shifts": int((d1[:, fmt] > .25).sum()),
                 "goal_0_wrong_shifts": int((d0[:, fmt] < -.25).sum()),
                 "goal_1_wrong_shifts": int((d1[:, fmt] < -.25).sum()),
                 "goal_0_near_zero": int((abs(d0[:, fmt]) <= .25).sum()),
                 "goal_1_near_zero": int((abs(d1[:, fmt]) <= .25).sum()),
                 "domain_joint_success_fraction": domain_rate[:, fmt].tolist(),
                 "factor_halves": halves}
        if treatment:
            quadrants = {f"{f}{s}": float(x[[i for i, row in enumerate(rows)
                    if tuple(row["fact_order"]) == (f, s)]].mean())
                    for f, s in itertools.product((0, 1), repeat=2)}
            null = _null(x, wrong[:, fmt])
            boot = _bootstrap(domain_rate[:, fmt], seed=SEED + fmt)
            gates = {"at_least_21_of_32": int(x.sum()) >= 21,
                     "exact_p": null["p_ge_observed"] <= .05,
                     "bootstrap_lower": boot["ci95"][0] > .5,
                     **{k: v > .5 for k, v in halves.items()},
                     **{f"quadrant_{k}": v > .5 for k, v in quadrants.items()}}
            entry.update({"exact_orientation_null": null,
                          "domain_bootstrap": boot,
                          "fact_order_quadrants": quadrants,
                          "gate_components": gates,
                          "gate_pass": all(gates.values())})
        else:
            gates = {"at_least_12_of_16": int(x.sum()) >= 12,
                     **{k: v > .5 for k, v in halves.items()}}
            entry.update({"gate_components": gates,
                          "gate_pass": all(gates.values())})
        formats[label] = entry
    difference_pairs = {"late_minus_chronological": (1, 0),
                        "late_minus_near_adjacent": (1, 2),
                        "near_adjacent_minus_chronological": (2, 0)}
    differences = {label: {
        "mean": float(np.mean(domain_rate[:, hi] - domain_rate[:, lo])),
        "domain_values": (domain_rate[:, hi] - domain_rate[:, lo]).tolist(),
        "domain_bootstrap": _bootstrap(domain_rate[:, hi] - domain_rate[:, lo],
                                        seed=SEED + 3 + i)}
        for i, (label, (hi, lo)) in enumerate(difference_pairs.items())}
    paired = {"all_format_success": int(all_formats.sum()),
              "all_format_fraction": float(all_formats.mean()),
              "domain_all_format_fraction": paired_rate.tolist(),
              "format_differences": differences}
    if treatment:
        null = _null(all_formats, all_wrong)
        boot = _bootstrap(paired_rate, seed=SEED + 2)
        gates = {"at_least_21_of_32": int(all_formats.sum()) >= 21,
                 "exact_p": null["p_ge_observed"] <= .05,
                 "bootstrap_lower": boot["ci95"][0] > .5,
                 "late_noninferior_to_chronological": (
                     differences["late_minus_chronological"]["domain_bootstrap"]["ci95"][0] >= -.15),
                 "late_noninferior_to_near_adjacent": (
                     differences["late_minus_near_adjacent"]["domain_bootstrap"]["ci95"][0] >= -.15)}
        paired.update({"exact_orientation_null": null,
                       "domain_bootstrap": boot,
                       "gate_components": gates,
                       "gate_pass": all(gates.values())})
    else:
        paired["gate_pass"] = int(all_formats.sum()) >= 10
    return {"n_cells": len(cells), "n_quartets_per_format": n * 4,
            "formats": formats, "paired": paired,
            "d0": d0.tolist(), "d1": d1.tolist(),
            "margins": m.tolist(), "strict": strict.tolist()}


def repeat_report(stories: list[cross.Cell], duplicates: list[cross.Cell],
                  saved: dict) -> dict:
    rows = []
    for cell in duplicates:
        di, fmt = map(int, cell.id.split(":")[1:])
        original = stories[di * 48 + fmt * 16]
        a = np.array(saved[original.id]["scores"], dtype=float)
        b = np.array(saved[cell.id]["scores"], dtype=float)
        rows.append({"id": cell.id, "original": original.id,
                     "candidate_differences": (b - a).tolist(),
                     "margin_difference": cross.role_margin(cell, saved) -
                                          cross.role_margin(original, saved)})
    max_margin = max(abs(row["margin_difference"]) for row in rows)
    return {"rows": rows, "max_abs_margin_difference": max_margin,
            "gate_pass": max_margin <= .25}


def main() -> None:
    from lsx.core.remote import RemoteLM, strip_template_bos

    controls, stories, duplicates, source, digests, bags = make_cells()
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != TOKENIZER_REVISION:
        raise ValueError("local tokenizer ref changed from frozen revision")
    cross.validate_tokens(rlm, controls + stories, source["question"])
    token_lengths = {}
    for label, cells in (("control", controls), ("story", stories)):
        token_lengths[label] = {}
        for fmt, format_name in enumerate(FORMATS):
            lengths = [len(rlm.tok(strip_template_bos(
                rlm.tok, base.render(rlm, c, source["question"])),
                add_special_tokens=True)["input_ids"])
                for c in cells if c.telling == fmt]
            token_lengths[label][format_name] = {
                "min": min(lengths), "median": float(np.median(lengths)),
                "max": max(lengths)}
    cells = controls + stories + duplicates
    fps = {c.id: cross.fingerprint(c, base.render(rlm, c, source["question"]),
                                   digests) for c in cells}
    path = OUT / "scores.jsonl"
    saved = base._load_cache(path, fps, generation=False)
    for group in (controls, stories, duplicates):
        base.score_cells(rlm, group, saved, fps, path, source["question"])
    control = report_group(controls, saved, source["controls"], treatment=False)
    story = report_group(stories, saved, source["domains"], treatment=True)
    repeat = repeat_report(stories, duplicates, saved)
    report = {"model_checkpoint": MODEL, "deployment_weight_revision": None,
              "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
              "digests": digests, "versions": rlm.lib_versions(),
              "question": source["question"], "token_lengths": token_lengths,
              "measured_word_bag_interactions": bags,
              "control": control, "story": story, "repeat": repeat,
              "gate_components": {"control_chronological": control["formats"]["chronological"]["gate_pass"],
                                  "control_late_reveal": control["formats"]["late_reveal"]["gate_pass"],
                                  "control_near_adjacent": control["formats"]["near_adjacent"]["gate_pass"],
                                  "control_paired": control["paired"]["gate_pass"],
                                  "repeat": repeat["gate_pass"],
                                  "story_chronological": story["formats"]["chronological"]["gate_pass"],
                                  "story_late_reveal": story["formats"]["late_reveal"]["gate_pass"],
                                  "story_near_adjacent": story["formats"]["near_adjacent"]["gate_pass"],
                                  "story_paired": story["paired"]["gate_pass"]}}
    report["gate_pass"] = all(report["gate_components"].values())
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
