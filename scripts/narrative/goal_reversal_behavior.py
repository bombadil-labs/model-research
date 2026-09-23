"""Preregistered NDIF goal-reversal choice check on fixed facts and plans."""
from __future__ import annotations

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

from role_swap_probe import SEED


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/goal_reversal_v3.json"
OUT = ROOT / "cache/goal_relative/goal_reversal"
MODEL = "google/gemma-2-9b-it"
TOKENIZER_REVISION = "11c9b309abf73637e4b6f9a3fa1e92e615547819"
MAX_NEW_TOKENS = 8
STOP = set("a an the to for and or of in on at with from by as is was were be "
           "its it that they their one only now planned plan immediate goal".split())
GOAL_TYPE_RE = re.compile(
    r"\b(?:keep|kept|protect|protected|preserve|hidden|unexposed|unaware|"
    r"intact|undiscovered|hold|delayed|unable|unmixed|available|private)\b", re.I)
CONTAIN_RE = re.compile(
    r"\b(?:sealed|dark|off|raise|store|locked|close|moored|silent|closed)\b", re.I)
# A frozen goal-only category reader. It sees no setup or plan and assumes that
# the two available plans are one containing and one releasing action.
GOAL_HAZARD_RELEASE_RE = re.compile(
    r"\b(?:unsafe|reef|rocks|flood|floodplain|floodline|pressure|bursting|"
    r"smoke|fumes|warn|alerted)\b", re.I)
GOAL_CONCEAL_RE = re.compile(
    r"\b(?:raider|raiders|patrol|rival|pursuer|pursuers|interception|"
    r"unknown|undiscovered|unaware|monitoring|hiding)\b", re.I)
GOAL_RETAIN_RE = re.compile(
    r"\b(?:preserve|intact|available|warm|warmth|retain|supply|"
    r"breeding|reference|sample|unexposed)\b", re.I)
CORE_FILES = (ROOT / "src/lsx/core/remote.py", ROOT / "src/lsx/ndif.py",
              ROOT / "scripts/narrative/role_swap_probe.py")


@dataclass(frozen=True)
class Cell:
    id: str
    stage: str
    domain: str
    paraphrase: int
    name_order: int
    plan_order: int
    goal: int
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


def _words(s: str, names: list[str]) -> set[str]:
    return set(re.findall(r"[a-z]+", s.lower())) - STOP - {
        n.lower() for n in names} - {"name"}


def lexical_baselines(doc: dict) -> dict:
    overlap_hits = []
    goal_type_hits = []
    contain_hits = []
    category_hits = []
    overlap_pair_hits = []
    category_pair_hits = []
    for row in doc["domains"]:
        plans = [_words(s, row["names"]) for s in row["plans"]]
        contain = [bool(CONTAIN_RE.search(s)) for s in row["plans"]]
        if contain != [row["plan_a_semantic"] == "contain",
                       row["plan_a_semantic"] == "release"]:
            raise ValueError(f"containment marker is ambiguous: {row['id']}")
        for paraphrase in (0, 1):
            overlap_chosen = []
            category_chosen = []
            for goal in (0, 1):
                phrase = row["goals"][goal][paraphrase]
                protect = bool(GOAL_TYPE_RE.search(phrase))
                expected = ((row["goal_a_type"] == "protect") == (goal == 0))
                if protect != expected:
                    raise ValueError(f"goal-type marker is ambiguous: {row['id']}")
                words = _words(phrase, row["names"])
                sim = [len(words & p) / len(words | p) for p in plans]
                choice = 0 if sim[0] > sim[1] else 1 if sim[1] > sim[0] else -1
                overlap_chosen.append(choice)
                overlap_hits.append(1.0 if choice == goal else .5 if choice < 0 else 0.0)
                type_choice = (0 if row["plan_a_polarity"] == "withhold" else 1)
                if not protect:
                    type_choice = 1 - type_choice
                goal_type_hits.append(float(type_choice == goal))
                contain_choice = (0 if contain[0] else 1)
                if not protect:
                    contain_choice = 1 - contain_choice
                contain_hits.append(float(contain_choice == goal))
                if GOAL_HAZARD_RELEASE_RE.search(phrase):
                    category = "release"
                elif GOAL_CONCEAL_RE.search(phrase) or GOAL_RETAIN_RE.search(phrase):
                    category = "contain"
                else:
                    category = "release"
                category_choice = 0 if row["plan_a_semantic"] == category else 1
                category_chosen.append(category_choice)
                category_hits.append(float(category_choice == goal))
            overlap_pair_hits.append(float(overlap_chosen == [0, 1]))
            category_pair_hits.append(float(category_chosen == [0, 1]))
    return {"word_overlap_accuracy": float(np.mean(overlap_hits)),
            "word_overlap_correct_reversal": float(np.mean(overlap_pair_hits)),
            "goal_type_to_withhold_accuracy": float(np.mean(goal_type_hits)),
            "goal_type_to_contain_accuracy": float(np.mean(contain_hits)),
            "goal_category_to_semantic_accuracy": float(np.mean(category_hits)),
            "goal_category_correct_reversal": float(np.mean(category_pair_hits))}


def _check_grid(doc: dict) -> None:
    from collections import Counter

    domains, controls = doc["domains"], doc["controls"]
    control_ids = {x["id"] for x in controls}
    if len(domains) != 12 or len(controls) != 4:
        raise ValueError("wrong goal-reversal grid size")
    if len({x["id"] for x in domains + controls}) != 16:
        raise ValueError("domain/control ids overlap")
    if Counter((x["goal_a_type"], x["plan_a_semantic"]) for x in domains) != {
            ("protect", "release"): 3, ("protect", "contain"): 3,
            ("provide", "release"): 3, ("provide", "contain"): 3}:
        raise ValueError("goal type and plan meaning are not crossed")
    if Counter(x["plan_a_polarity"] for x in domains) != {"act": 6, "withhold": 6}:
        raise ValueError("plan-A status-quo polarity is unbalanced")
    if Counter(x["plan_a_polarity"] for x in controls) != {"act": 2, "withhold": 2}:
        raise ValueError("control polarity is unbalanced")
    protect_acts = sum((x["plan_a_polarity"] == "act") ==
                       (x["goal_a_type"] == "protect") for x in domains)
    if protect_acts != 6:
        raise ValueError("protective action/status quo shortcut is unbalanced")
    for row in domains + controls:
        if (len(row["names"]) != 2 or row["names"][0] == row["names"][1] or
                len(row["names"][0]) != len(row["names"][1]) or
                len(row["plans"]) != 2 or len(row["goals"]) != 2 or
                not row["setup"].endswith(". ") or
                not all(s.endswith(". ") and s.count("{name}") == 1
                        for s in row["plans"])):
            raise ValueError(f"broken row shape: {row['id']}")
        goal_phrases = row["goals"] if row["id"] in control_ids else [
            s for pair in row["goals"] for s in pair]
        if not all(s.endswith(". ") for s in goal_phrases):
            raise ValueError(f"broken goal sentence: {row['id']}")
    base = lexical_baselines(doc)
    if (base["goal_type_to_withhold_accuracy"] != .5 or
            base["goal_type_to_contain_accuracy"] != .5 or
            base["goal_category_to_semantic_accuracy"] != 45 / 48 or
            base["goal_category_correct_reversal"] != 21 / 24 or
            abs(base["word_overlap_accuracy"] - 0.4895833333333333) > 1e-12):
        raise ValueError(f"frozen stimulus baselines changed: {base}")


def _cell(row: dict, *, stage: str, ident: str, goal: int, paraphrase: int,
          name_order: int, plan_order: int, bridge: str) -> Cell:
    names = row["names"] if name_order == 0 else row["names"][::-1]
    a, b = names
    plans = [row["plans"][0].format(name=a), row["plans"][1].format(name=b)]
    facts = plans if plan_order == 0 else plans[::-1]
    goal_text = "" if goal < 0 else (row["goals"][goal] if stage == "calibration"
                                   else row["goals"][goal][paraphrase])
    text = row["setup"] + goal_text + "".join(facts) + bridge
    if (len(re.findall(r"\b" + re.escape(a) + r"\b", text)) != 1 or
            len(re.findall(r"\b" + re.escape(b) + r"\b", text)) != 1):
        raise ValueError(f"name mention count differs: {ident}")
    return Cell(ident, stage, row["id"], paraphrase, name_order, plan_order,
                goal, text, a, b)


def make_cells() -> tuple[list[Cell], list[Cell], list[Cell], list[Cell], dict, dict]:
    raw = GRID.read_bytes()
    doc = json.loads(raw)
    _check_grid(doc)
    bridge = doc["bridge"]
    if not bridge.endswith(". "):
        raise ValueError("bridge does not end at sentence boundary")
    cal, stories, neutral = [], [], []
    for di, row in enumerate(doc["controls"]):
        for n, o, g in itertools.product((0, 1), repeat=3):
            cal.append(_cell(row, stage="calibration", ident=f"cal:{di:02d}:{n}:{o}:{g}",
                             goal=g, paraphrase=0, name_order=n, plan_order=o,
                             bridge=bridge))
    for di, row in enumerate(doc["domains"]):
        for p, n, o, g in itertools.product((0, 1), repeat=4):
            stories.append(_cell(row, stage="story", ident=f"story:{di:02d}:{p}:{n}:{o}:{g}",
                                 goal=g, paraphrase=p, name_order=n, plan_order=o,
                                 bridge=bridge))
        for n, o in itertools.product((0, 1), repeat=2):
            neutral.append(_cell(row, stage="neutral", ident=f"neutral:{di:02d}:{n}:{o}",
                                 goal=-1, paraphrase=-1, name_order=n, plan_order=o,
                                 bridge=bridge))
        group = stories[-16:]
        for p, n, o in itertools.product((0, 1), repeat=3):
            a, b = group[((p * 2 + n) * 2 + o) * 2:((p * 2 + n) * 2 + o) * 2 + 2]
            ga, gb = row["goals"][0][p], row["goals"][1][p]
            if (a.user_text.replace(ga, "<GOAL>", 1) !=
                    b.user_text.replace(gb, "<GOAL>", 1)):
                raise ValueError(f"non-goal text differs across goals: {row['id']}")
    generations = [c for c in stories if c.paraphrase == 0 and c.plan_order == 0]
    if (len(cal), len(stories), len(neutral), len(generations)) != (32, 192, 48, 48):
        raise ValueError("cell counts differ from preregistration")
    return cal, stories, neutral, generations, doc, {
        "grid_sha256": hashlib.sha256(raw).hexdigest(),
        "code_sha256": _digest(), "tokenizer_revision": TOKENIZER_REVISION}


def render(rlm, cell: Cell, question: str) -> str:
    return rlm.tok.apply_chat_template(
        [{"role": "user", "content": cell.user_text.rstrip() + "\n\n" + question}],
        tokenize=False, add_generation_prompt=True)


def validate_tokens(rlm, cells: list[Cell], question: str) -> None:
    from lsx.core.remote import strip_template_bos

    tok = rlm.tok
    for cell in cells:
        lead = strip_template_bos(tok, render(rlm, cell, question))
        base = tok(lead, add_special_tokens=True)["input_ids"]
        lengths = []
        for name in cell.candidates:
            full = tok(lead + name, add_special_tokens=True)["input_ids"]
            if full[:len(base)] != base:
                raise ValueError(f"candidate changes prompt tokens: {cell.id}")
            lengths.append(len(full) - len(base))
        if lengths[0] != lengths[1] or not lengths[0]:
            raise ValueError(f"candidate token counts differ: {cell.id}: {lengths}")


def fingerprint(cell: Cell, lead: str, digests: dict, *, generation: bool = False) -> str:
    data = {"model": MODEL, "id": cell.id, "prompt": lead,
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


def _remote_scores(rlm, lead: str, candidates: tuple[str, str]) -> list[float]:
    from lsx.core.remote import asserted_remote_patched_logprob

    for attempt in range(12):
        try:
            scores = asserted_remote_patched_logprob(rlm, lead, list(candidates))
            if scores.shape != (2,) or not np.isfinite(scores).all():
                raise ValueError("invalid remote name scores")
            return list(map(float, scores))
        except Exception as exc:
            transient = any(term in str(exc).lower() for term in (
                "out of memory", "cuda out of memory", "503 service unavailable",
                "502 bad gateway", "429 too many requests", "deployment unavailable",
                "not complete after", "timed out"))
            if not transient or attempt == 11:
                raise
            time.sleep(20)
    raise AssertionError("unreachable")


def _score_cells(rlm, cells: list[Cell], saved: dict, fps: dict, path: Path,
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


def calibration_report(cells: list[Cell], saved: dict) -> dict:
    margins = np.array([role_margin(c, saved) for c in cells]).reshape(4, 2, 2, 2)
    signed = np.stack((margins[..., 0], -margins[..., 1]), axis=-1)
    by_name = signed.mean(axis=(0, 2, 3))
    by_order = signed.mean(axis=(0, 1, 3))
    return {"margins": margins.tolist(), "signed_min_margin": float(signed.min()),
            "correct_of_32": int((signed > .1).sum()),
            "name_order_signed_means": by_name.tolist(),
            "plan_order_signed_means": by_order.tolist(),
            "name_order_effect": float(by_name[0] - by_name[1]),
            "plan_order_effect": float(by_order[0] - by_order[1]),
            "gate_pass": bool(np.all(signed > .1))}


def story_report(stories: list[Cell], neutral: list[Cell], saved: dict,
                 doc: dict, n_boot: int = 10000) -> dict:
    margins = np.array([role_margin(c, saved) for c in stories]).reshape(12, 2, 2, 2, 2)
    bare = np.array([role_margin(c, saved) for c in neutral]).reshape(12, 2, 2)
    good = (margins[..., 0] > .1) & (margins[..., 1] < -.1)
    wrong = (margins[..., 0] < -.1) & (margins[..., 1] > .1)
    same = ((margins[..., 0] > .1) & (margins[..., 1] > .1)) | (
        (margins[..., 0] < -.1) & (margins[..., 1] < -.1))
    near = (np.abs(margins) <= .1).any(axis=-1)
    observed = float(good.mean())
    counts = np.stack((good.sum(axis=(1, 2, 3)), wrong.sum(axis=(1, 2, 3))), axis=-1)
    null = []
    for flips in itertools.product((0, 1), repeat=12):
        null.append(float(counts[np.arange(12), flips].sum() / good.size))
    p = float(np.mean(np.array(null) >= observed))
    rng = np.random.default_rng(SEED + 47)
    domain_rate = good.mean(axis=(1, 2, 3))
    boot = domain_rate[rng.integers(0, 12, size=(n_boot, 12))].mean(axis=1)
    ci = list(map(float, np.quantile(boot, [.025, .975])))
    both_names = good[:, :, 0, :] & good[:, :, 1, :]
    halves = {"paraphrase_0": float(good[:, 0].mean()),
              "paraphrase_1": float(good[:, 1].mean()),
              "name_0": float(good[:, :, 0].mean()),
              "name_1": float(good[:, :, 1].mean()),
              "plan_order_0": float(good[:, :, :, 0].mean()),
              "plan_order_1": float(good[:, :, :, 1].mean())}
    gates = {"reversal_fraction": observed >= .70,
             "both_names": float(both_names.mean()) >= .60,
             "exact_permutation": p <= .05,
             "bootstrap_lower": ci[0] > .5,
             **{key: value > .5 for key, value in halves.items()}}
    return {"n_goal_pairs": int(good.size), "correct_reversal_fraction": observed,
            "correct_reversals": int(good.sum()), "wrong_reversals": int(wrong.sum()),
            "same_plan_pairs": int(same.sum()), "near_tie_pairs": int(near.sum()),
            "goal_cell_accuracy": [float((margins[..., 0] > .1).mean()),
                                   float((margins[..., 1] < -.1).mean())],
            "both_name_assignments_fraction": float(both_names.mean()),
            "domain_reversal_fraction": domain_rate.tolist(),
            "factor_halves": halves, "bootstrap": {"draws": n_boot, "ci95": ci},
            "exact_orientation_null": {"draws": len(null), "mean": float(np.mean(null)),
                                       "q95": float(np.quantile(null, .95)),
                                       "p_ge_observed": p},
            "neutral": {"n_cells": int(bare.size), "margins": bare.tolist(),
                        "mean_abs_margin": float(np.abs(bare).mean()),
                        "mean_plan_prior": float(((bare[:, 0] + bare[:, 1]) / 2).mean()),
                        "mean_abs_name_bias": float(np.abs((bare[:, 0] - bare[:, 1]) / 2).mean()),
                        "domain_plan_prior": ((bare[:, 0] + bare[:, 1]) / 2).mean(axis=1).tolist()},
            "lexical_baselines": lexical_baselines(doc),
            "gate_components": gates, "gate_pass_without_generation": all(gates.values())}


def parse_generation(text: str, names: tuple[str, str]) -> str | None:
    pattern = r"\s*(" + "|".join(map(re.escape, names)) + r")[.!?,;:\s]*"
    match = re.fullmatch(pattern, text)
    return match.group(1) if match else None


def generation_report(cells: list[Cell], saved_scores: dict, saved_gen: dict) -> dict:
    rows = []
    for cell in cells:
        parsed = parse_generation(saved_gen[cell.id]["text"], cell.candidates)
        m = role_margin(cell, saved_scores)
        forced = cell.plan_a_name if m > 0 else cell.plan_b_name if m < 0 else None
        rows.append({"id": cell.id, "text": saved_gen[cell.id]["text"],
                     "parsed": parsed, "forced": forced,
                     "agrees": parsed == forced if parsed is not None and forced else None})
    parseable = sum(r["parsed"] is not None for r in rows)
    comparable = [r["agrees"] for r in rows if r["agrees"] is not None]
    parse_rate = parseable / len(rows)
    agreement = sum(comparable) / len(comparable) if comparable else 0.0
    return {"n_cells": len(rows), "parseable_fraction": parse_rate,
            "forced_choice_agreement": agreement,
            "n_forced_ties": sum(r["forced"] is None for r in rows),
            "gate_components": {"parseable": parse_rate >= .90,
                                "agreement": agreement >= .90},
            "rows": rows}


def main() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_generate

    cal, stories, neutral, generations, doc, digests = make_cells()
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(MODEL)
    validate_tokens(rlm, cal + stories + neutral, doc["question"])
    fps = {c.id: fingerprint(c, render(rlm, c, doc["question"]), digests)
           for c in cal + stories + neutral}
    gen_fps = {c.id: fingerprint(c, render(rlm, c, doc["question"]), digests,
                                 generation=True) for c in generations}
    score_path, gen_path = OUT / "scores.jsonl", OUT / "generations.jsonl"
    scores = _load_cache(score_path, fps, generation=False)
    generated = _load_cache(gen_path, gen_fps, generation=True)
    scores = _score_cells(rlm, cal, scores, fps, score_path, doc["question"])
    calibration = calibration_report(cal, scores)
    report = {"model_checkpoint": MODEL, "deployment_weight_revision": None,
              "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
              "digests": digests, "versions": rlm.lib_versions(),
              "question": doc["question"], "calibration": calibration,
              "story": None, "generation": None, "gate_pass": False}
    if calibration["gate_pass"]:
        scores = _score_cells(rlm, stories, scores, fps, score_path, doc["question"])
        scores = _score_cells(rlm, neutral, scores, fps, score_path, doc["question"])
        report["story"] = story_report(stories, neutral, scores, doc)
        for cell in generations:
            if cell.id in generated:
                continue
            text = asserted_remote_generate(rlm, render(rlm, cell, doc["question"]),
                                            max_new_tokens=MAX_NEW_TOKENS)
            row = {"id": cell.id, "fp": gen_fps[cell.id], "text": text}
            _append(gen_path, row)
            generated[cell.id] = row
            print(f"generated {cell.id}", flush=True)
        report["generation"] = generation_report(generations, scores, generated)
        report["gate_pass"] = bool(report["story"]["gate_pass_without_generation"] and
                                   all(report["generation"]["gate_components"].values()))
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
