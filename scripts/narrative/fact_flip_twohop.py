"""Preregistered two-link fact-flip screen, with early and late disclosure."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
import hashlib
import itertools
import json
import math
import os
from pathlib import Path
import re
import time

import numpy as np


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/fact_flip_twohop_v1.json"
OUT = ROOT / "cache/fact_flip_twohop/v1"
MODEL = "google/gemma-2-9b-it"
TOKENIZER_REVISION = "11c9b309abf73637e4b6f9a3fa1e92e615547819"
MAX_NEW_TOKENS = 8
SEED = 20260923
CORE_FILES = (ROOT / "src/lsx/core/remote.py", ROOT / "src/lsx/ndif.py")


@dataclass(frozen=True)
class Cell:
    id: str
    stage: str
    domain: str
    world: int
    telling: int
    name_order: int
    plan_order: int
    user_text: str
    plan_a_name: str
    plan_b_name: str

    @property
    def candidates(self) -> tuple[str, str]:
        return tuple(sorted((self.plan_a_name, self.plan_b_name)))


def _digest() -> str:
    h = hashlib.sha256()
    for path in (Path(__file__), *CORE_FILES):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _words(text: str) -> Counter:
    return Counter(re.findall(r"[a-z]+", text.lower()))


def _facts(row: dict, doc: dict, world: int, stage: str) -> tuple[str, str]:
    dest = (row["target"], row["foil"]) if world == 0 else (
        row["foil"], row["target"])
    if stage == "control":
        clauses = [doc["direct_template"].format(route=r, destination=d)
                   for r, d in zip(row["routes"], dest)]
        order = row["fact_order"]
        return "", "".join(clauses if order == 0 else clauses[::-1])
    first = [doc["first_hop_template"].format(route=r, link=l)
             for r, l in zip(row["routes"], row["links"])]
    second = [doc["second_hop_template"].format(link=l, destination=d)
              for l, d in zip(row["links"], dest)]
    f, s = row["fact_order"]
    return ("".join(first if f == 0 else first[::-1]),
            "".join(second if s == 0 else second[::-1]))


def shortcut_baselines(doc: dict) -> dict:
    bag_differences, plan_differences, direct_matches, symbolic = [], [], [], []
    for row in doc["domains"]:
        cells = [_cell(row, doc, stage="story", di=0, world=w, telling=0,
                       name_order=0, plan_order=0) for w in (0, 1)]
        texts = [cell.user_text for cell in cells]
        plan_clauses = [doc["plan_template"].format(name=n, route=r)
                        for n, r in zip(row["names"], row["routes"])]
        plan_spans = []
        for text in texts:
            matches = [text.count(clause) for clause in plan_clauses]
            if matches != [1, 1]:
                raise ValueError(f"plan clause missing or duplicated: {row['id']}")
            plan_spans.append("".join(text[text.index(clause):text.index(clause) + len(clause)]
                                      for clause in plan_clauses))
        bag_differences.append(sum((_words(texts[0]) - _words(texts[1])).values()) +
                               sum((_words(texts[1]) - _words(texts[0])).values()))
        plan_differences.append(sum((_words(plan_spans[0]) - _words(plan_spans[1])).values()) +
                                sum((_words(plan_spans[1]) - _words(plan_spans[0])).values()))
        for world in (0, 1):
            _, second = _facts(row, doc, world, "story")
            direct_matches.append(sum(int(route in clause and row["target"] in clause)
                                      for route in row["routes"]
                                      for clause in second.split(". ") if clause))
            destinations = ((row["target"], row["foil"]) if world == 0
                            else (row["foil"], row["target"]))
            symbolic.append(int(destinations.index(row["target"]) == world))
    return {"bag_world_difference_tokens": int(sum(bag_differences)),
            "plan_world_difference_tokens": int(sum(plan_differences)),
            "direct_route_target_cooccurrences": int(sum(direct_matches)),
            "same_ordinal_correct_domain_fraction": float(np.mean([
                r["fact_order"][0] == r["fact_order"][1] for r in doc["domains"]])),
            "target_first_correct_domain_fraction": float(np.mean([
                r["fact_order"][1] == 0 for r in doc["domains"]])),
            "symbolic_graph_cell_accuracy": float(np.mean(symbolic))}


def _cell(row: dict, doc: dict, *, stage: str, di: int, world: int,
          telling: int, name_order: int, plan_order: int) -> Cell:
    names = row["names"] if name_order == 0 else row["names"][::-1]
    a, b = names
    plan_clauses = [doc["plan_template"].format(name=n, route=r)
                    for n, r in zip(names, row["routes"])]
    plans = "".join(plan_clauses if plan_order == 0 else plan_clauses[::-1])
    first, second = _facts(row, doc, world, stage)
    facts = first + second
    if telling == 0:
        text = row["setup"] + row["goal"] + facts + plans + doc["bridge"]
    else:
        text = row["setup"] + row["goal"] + plans + facts + doc["bridge"]
    ident = f"{stage}:{di:02d}:{telling}:{name_order}:{plan_order}:{world}"
    for name in names:
        if len(re.findall(r"\b" + re.escape(name) + r"\b", text)) != 1:
            raise ValueError(f"name mention count differs: {ident}")
    return Cell(ident, stage, row["id"], world, telling, name_order,
                plan_order, text, a, b)


def _check_grid(doc: dict) -> None:
    if len(doc["domains"]) != 8 or len(doc["controls"]) != 4:
        raise ValueError("wrong two-link grid size")
    rows = doc["domains"] + doc["controls"]
    if len({r["id"] for r in rows}) != 12:
        raise ValueError("duplicate grid id")
    if Counter(tuple(r["fact_order"]) for r in doc["domains"]) != {
            (0, 0): 2, (0, 1): 2, (1, 0): 2, (1, 1): 2}:
        raise ValueError("fact orders are not balanced")
    if Counter(r["fact_order"] for r in doc["controls"]) != {0: 2, 1: 2}:
        raise ValueError("direct fact orders are not balanced")
    if Counter(r["prior_congruent_world"] is None for r in doc["domains"]) != {
            True: 4, False: 4}:
        raise ValueError("semantic-prior audit split changed")
    if any(r["prior_congruent_world"] not in (None, 0, 1)
           for r in doc["domains"]):
        raise ValueError("invalid prior-congruent world label")
    if not doc["bridge"].endswith(". ") or len(doc["bridge"]) < 200:
        raise ValueError("bridge is too short or lacks a sentence boundary")
    for row in rows:
        if (len(row["names"]) != 2 or len(set(row["names"])) != 2 or
                len(row["names"][0]) != len(row["names"][1]) or
                len(row["routes"]) != 2 or len(set(row["routes"])) != 2 or
                row["target"] == row["foil"] or
                not row["setup"].endswith(". ") or
                not row["goal"].endswith(". ") or
                row["target"] not in row["goal"]):
            raise ValueError(f"broken row shape: {row['id']}")
        if "links" in row:
            if len(row["links"]) != 2 or len(set(row["links"])) != 2:
                raise ValueError(f"broken two-link row: {row['id']}")
            first, second = _facts(row, doc, 0, "story")
            if (row["target"] in first or row["foil"] in first or
                    any(route in second for route in row["routes"])):
                raise ValueError(f"direct route/destination leak: {row['id']}")
        for name_order, plan_order, telling in itertools.product((0, 1), repeat=3):
            stage = "story" if "links" in row else "control"
            a = _cell(row, doc, stage=stage, di=0, world=0,
                      telling=telling, name_order=name_order, plan_order=plan_order)
            b = _cell(row, doc, stage=stage, di=0, world=1,
                      telling=telling, name_order=name_order, plan_order=plan_order)
            if (_words(a.user_text) != _words(b.user_text) or
                    len(a.user_text) != len(b.user_text) or
                    a.user_text[-200:] != b.user_text[-200:]):
                raise ValueError(f"world bag, length or suffix differs: {row['id']}")
            other = _cell(row, doc, stage=stage, di=0, world=0,
                          telling=1 - telling, name_order=name_order,
                          plan_order=plan_order)
            if (_words(a.user_text) != _words(other.user_text) or
                    a.user_text[-200:] != other.user_text[-200:]):
                raise ValueError(f"tellings differ beyond disclosure order: {row['id']}")
    base = shortcut_baselines(doc)
    if base != {"bag_world_difference_tokens": 0,
                "plan_world_difference_tokens": 0,
                "direct_route_target_cooccurrences": 0,
                "same_ordinal_correct_domain_fraction": .5,
                "target_first_correct_domain_fraction": .5,
                "symbolic_graph_cell_accuracy": 1.0}:
        raise ValueError(f"frozen shortcut ceilings changed: {base}")


def make_cells() -> tuple[list[Cell], list[Cell], list[Cell], list[Cell], dict, dict]:
    raw = GRID.read_bytes()
    doc = json.loads(raw)
    _check_grid(doc)
    controls, stories = [], []
    for stage, rows, dest in (("control", doc["controls"], controls),
                              ("story", doc["domains"], stories)):
        for di, row in enumerate(rows):
            for telling, name, plan, world in itertools.product((0, 1), repeat=4):
                dest.append(_cell(row, doc, stage=stage, di=di, world=world,
                                  telling=telling, name_order=name, plan_order=plan))
    duplicates = []
    for di in range(8):
        base = stories[di * 16]
        duplicates.append(Cell(f"duplicate:{di:02d}", "duplicate", base.domain,
                               base.world, base.telling, base.name_order,
                               base.plan_order, base.user_text,
                               base.plan_a_name, base.plan_b_name))
    generations = [c for c in stories if c.name_order == 0 and c.plan_order == 0]
    if (len(controls), len(stories), len(duplicates), len(generations)) != (
            64, 128, 8, 32):
        raise ValueError("cell counts differ from preregistration")
    return controls, stories, duplicates, generations, doc, {
        "grid_sha256": hashlib.sha256(raw).hexdigest(),
        "code_sha256": _digest(), "tokenizer_revision": TOKENIZER_REVISION}


def render(rlm, cell: Cell, question: str) -> str:
    return rlm.tok.apply_chat_template(
        [{"role": "user", "content": cell.user_text.rstrip() + "\n\n" + question}],
        tokenize=False, add_generation_prompt=True)


def validate_tokens(rlm, cells: list[Cell], question: str) -> None:
    from lsx.core.remote import assert_single_bos, strip_template_bos
    import torch

    tok = rlm.tok
    for cell in cells:
        lead = strip_template_bos(tok, render(rlm, cell, question))
        base = tok(lead, add_special_tokens=True)["input_ids"]
        assert_single_bos(torch.tensor([base]), torch.ones((1, len(base))),
                          getattr(tok, "bos_token_id", None))
        lengths = []
        for name in cell.candidates:
            full = tok(lead + name, add_special_tokens=True)["input_ids"]
            if full[:len(base)] != base:
                raise ValueError(f"candidate changes prompt tokens: {cell.id}")
            lengths.append(len(full) - len(base))
        if lengths[0] != lengths[1] or not lengths[0]:
            raise ValueError(f"candidate token counts differ: {cell.id}: {lengths}")
    for i in range(0, len(cells), 2):
        a, b = cells[i:i + 2]
        if (a.stage == b.stage and a.domain == b.domain and
                a.world == 0 and b.world == 1):
            a_len = len(tok(strip_template_bos(tok, render(rlm, a, question)),
                            add_special_tokens=True)["input_ids"])
            b_len = len(tok(strip_template_bos(tok, render(rlm, b, question)),
                            add_special_tokens=True)["input_ids"])
            if a_len != b_len:
                raise ValueError(f"world token lengths differ: {a.id} {b.id}")


def fingerprint(cell: Cell, prompt: str, digests: dict, *, generation: bool = False) -> str:
    data = {"model": MODEL, "id": cell.id, "prompt": prompt,
            "candidates": cell.candidates, "generation": generation,
            "max_new_tokens": MAX_NEW_TOKENS if generation else None, **digests}
    return hashlib.sha256(json.dumps(data, sort_keys=True).encode()).hexdigest()


def _load_cache(path: Path, expected: dict[str, str], *, generation: bool) -> dict[str, dict]:
    saved = {}
    if not path.exists():
        return saved
    for line in path.read_text().splitlines():
        row = json.loads(line)
        key = row["id"]
        if key not in expected or row["fp"] != expected[key] or key in saved:
            raise ValueError(f"stale or duplicate cached row: {key}")
        if generation:
            if not isinstance(row.get("text"), str):
                raise ValueError(f"bad generated text: {key}")
        elif (len(row.get("scores", [])) != 2 or
              not all(math.isfinite(v) for v in row["scores"])):
            raise ValueError(f"bad score row: {key}")
        saved[key] = row
    return saved


def _append(path: Path, row: dict) -> None:
    with path.open("a") as handle:
        handle.write(json.dumps(row, ensure_ascii=False) + "\n")
        handle.flush()
        os.fsync(handle.fileno())


def _remote_scores(rlm, prompt: str, candidates: tuple[str, str]) -> list[float]:
    from lsx.core.remote import asserted_remote_patched_logprob

    for attempt in range(12):
        try:
            scores = asserted_remote_patched_logprob(rlm, prompt, list(candidates))
            if scores.shape != (2,) or not np.isfinite(scores).all():
                raise ValueError("invalid remote name scores")
            return list(map(float, scores))
        except Exception as exc:
            transient = any(term in str(exc).lower() for term in (
                "out of memory", "503 service unavailable", "502 bad gateway",
                "429 too many requests", "deployment unavailable",
                "not complete after", "timed out"))
            if not transient or attempt == 11:
                raise
            time.sleep(20)
    raise AssertionError("unreachable")


def score_cells(rlm, cells: list[Cell], saved: dict, fps: dict, path: Path,
                question: str) -> dict:
    for cell in cells:
        if cell.id in saved:
            continue
        scores = _remote_scores(rlm, render(rlm, cell, question), cell.candidates)
        row = {"id": cell.id, "fp": fps[cell.id], "scores": scores}
        _append(path, row)
        saved[cell.id] = row
        print(f"scored {cell.id}", flush=True)
    return saved


def role_margin(cell: Cell, saved: dict) -> float:
    scores = dict(zip(cell.candidates, saved[cell.id]["scores"]))
    return float(scores[cell.plan_a_name] - scores[cell.plan_b_name])


def paired_report(cells: list[Cell], saved: dict, rows: list[dict], *, treatment: bool,
                  n_boot: int = 10000) -> dict:
    n = 8 if treatment else 4
    margins = np.array([role_margin(c, saved) for c in cells]).reshape(n, 2, 2, 2, 2)
    delta = margins[..., 0] - margins[..., 1]
    good, wrong = delta > .25, delta < -.25
    choice = (margins[..., 0] > .1) & (margins[..., 1] < -.1)
    domain_rate = good.mean(axis=(1, 2, 3))
    halves = {"early": float(good[:, 0].mean()),
              "late": float(good[:, 1].mean()),
              "name_0": float(good[:, :, 0].mean()),
              "name_1": float(good[:, :, 1].mean()),
              "plan_order_0": float(good[:, :, :, 0].mean()),
              "plan_order_1": float(good[:, :, :, 1].mean())}
    result = {"n_pairs": int(good.size), "correct_shift_fraction": float(good.mean()),
              "correct_shifts": int(good.sum()), "wrong_shifts": int(wrong.sum()),
              "near_zero_shifts": int((~good & ~wrong).sum()),
              "strict_choice_reversals": int(choice.sum()),
              "strict_choice_reversal_fraction": float(choice.mean()),
              "domain_correct_shift_fraction": domain_rate.tolist(),
              "factor_halves": halves, "margins": margins.tolist(),
              "deltas": delta.tolist()}
    if treatment:
        counts = np.stack((good.sum(axis=(1, 2, 3)),
                           wrong.sum(axis=(1, 2, 3))), axis=-1)
        null = np.array([counts[np.arange(8), flips].sum() / good.size
                         for flips in itertools.product((0, 1), repeat=8)])
        rng = np.random.default_rng(SEED)
        boot = domain_rate[rng.integers(0, 8, size=(n_boot, 8))].mean(axis=1)
        ci = list(map(float, np.quantile(boot, [.025, .975])))
        domain_values = [good[di].mean() for di in range(8)]
        quadrants = {f"{f}{s}": float(np.mean([domain_values[di] for di in range(8)
                        if tuple(rows[di]["fact_order"]) == (f, s)])) for f, s in
                     itertools.product((0, 1), repeat=2)}
        flagged = [di for di, row in enumerate(rows)
                   if row["prior_congruent_world"] is not None]
        neutral = [di for di, row in enumerate(rows)
                   if row["prior_congruent_world"] is None]
        world_correct = np.stack((margins[..., 0] > .1,
                                  margins[..., 1] < -.1), axis=-1)
        prior_split = {
            "labelled_domain_shift_fraction": float(good[flagged].mean()),
            "neutral_domain_shift_fraction": float(good[neutral].mean()),
            "congruent_world_cell_accuracy": float(np.mean([
                world_correct[di, ..., rows[di]["prior_congruent_world"]].mean()
                for di in flagged])),
            "incongruent_world_cell_accuracy": float(np.mean([
                world_correct[di, ..., 1 - rows[di]["prior_congruent_world"]].mean()
                for di in flagged]))}
        gates = {"at_least_48_of_64": int(good.sum()) >= 48,
                 "orientation_p": float(np.mean(null >= good.mean())) <= .05,
                 "bootstrap_lower": ci[0] > .5,
                 "early": halves["early"] >= .65,
                 "late": halves["late"] >= .65,
                 **{k: v > .5 for k, v in halves.items()
                    if k.startswith("name_") or k.startswith("plan_order_")},
                 **{f"quadrant_{k}": v > .5 for k, v in quadrants.items()}}
        result.update({"exact_orientation_null": {
            "draws": len(null), "mean": float(null.mean()),
            "q95": float(np.quantile(null, .95)),
            "p_ge_observed": float(np.mean(null >= good.mean()))},
            "domain_bootstrap": {"draws": n_boot, "ci95": ci},
            "fact_order_quadrants": quadrants,
            "prior_split": prior_split,
            "gate_components": gates, "gate_pass_without_controls": all(gates.values())})
    else:
        gates = {"at_least_24_of_32": int(good.sum()) >= 24,
                 "early": halves["early"] > .5, "late": halves["late"] > .5}
        result.update({"gate_components": gates, "gate_pass": all(gates.values())})
    return result


def repeat_report(stories: list[Cell], duplicates: list[Cell], saved: dict) -> dict:
    rows = []
    for di, dup in enumerate(duplicates):
        base = stories[di * 16]
        a = np.array(saved[base.id]["scores"], dtype=float)
        b = np.array(saved[dup.id]["scores"], dtype=float)
        diff = b - a
        rows.append({"domain": dup.domain, "base_id": base.id,
                     "duplicate_id": dup.id, "candidate_differences": diff.tolist(),
                     "margin_difference": role_margin(dup, saved) - role_margin(base, saved)})
    max_margin = max(abs(r["margin_difference"]) for r in rows)
    return {"rows": rows, "max_abs_margin_difference": max_margin,
            "max_abs_candidate_difference": max(abs(v) for r in rows
                                                for v in r["candidate_differences"]),
            "gate_pass": max_margin <= .25}


def parse_generation(text: str, names: tuple[str, str]) -> str | None:
    pattern = r"\s*(" + "|".join(map(re.escape, names)) + r")[.!?,;:\s]*"
    match = re.fullmatch(pattern, text)
    return match.group(1) if match else None


def generation_report(cells: list[Cell], scores: dict, generated: dict) -> dict:
    rows = []
    for cell in cells:
        parsed = parse_generation(generated[cell.id]["text"], cell.candidates)
        margin = role_margin(cell, scores)
        forced = cell.plan_a_name if margin > 0 else cell.plan_b_name if margin < 0 else None
        rows.append({"id": cell.id, "world": cell.world, "telling": cell.telling,
                     "parsed": parsed, "forced": forced,
                     "agrees": parsed == forced if parsed is not None and forced else None,
                     "text": generated[cell.id]["text"]})
    parseable = sum(r["parsed"] is not None for r in rows)
    comparable = [r["agrees"] for r in rows if r["agrees"] is not None]
    reversals = 0
    for i in range(0, len(rows), 2):
        a, b = rows[i:i + 2]
        ca, cb = cells[i:i + 2]
        reversals += int(a["parsed"] == ca.plan_a_name and
                         b["parsed"] == cb.plan_b_name)
    parse_rate = parseable / len(rows)
    agreement = sum(comparable) / len(comparable) if comparable else 0.0
    return {"n_cells": len(rows), "parseable_fraction": parse_rate,
            "forced_choice_agreement": agreement,
            "correct_generated_reversals": reversals,
            "n_world_pairs": len(rows) // 2,
            "gate_components": {"parseability": parse_rate >= .9,
                                "agreement": agreement >= .9}, "rows": rows}


def main() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_generate

    controls, stories, duplicates, generations, doc, digests = make_cells()
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != TOKENIZER_REVISION:
        raise ValueError("local tokenizer ref changed from the frozen revision")
    validate_tokens(rlm, controls + stories, doc["question"])
    cells = controls + stories + duplicates
    fps = {c.id: fingerprint(c, render(rlm, c, doc["question"]), digests)
           for c in cells}
    gen_fps = {c.id: fingerprint(c, render(rlm, c, doc["question"]), digests,
                                 generation=True) for c in generations}
    score_path, gen_path = OUT / "scores.jsonl", OUT / "generations.jsonl"
    saved = _load_cache(score_path, fps, generation=False)
    generated = _load_cache(gen_path, gen_fps, generation=True)
    for group in (controls, stories, duplicates):
        score_cells(rlm, group, saved, fps, score_path, doc["question"])
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
        text = asserted_remote_generate(rlm, render(rlm, cell, doc["question"]),
                                        max_new_tokens=MAX_NEW_TOKENS)
        row = {"id": cell.id, "fp": gen_fps[cell.id], "text": text}
        _append(gen_path, row)
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
