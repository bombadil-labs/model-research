"""NDIF choice readout for fixed-plan stories, gated by crossed easy controls."""
from __future__ import annotations

from dataclasses import dataclass
import hashlib
import json
import math
import os
from pathlib import Path
import re
import time

import numpy as np

from elicitor_calibration import GRID as CAL_GRID, make_controls
from goal_relative_probe import GRID as STORY_GRID, OUT, ROOT, make_cases
from role_swap_probe import SEED


MODEL = "google/gemma-2-9b-it"
QUESTION = "Which person's plan best serves the stated goal? Answer with the person's name only."
REMOTE_OUT = OUT / "remote_behavior"
CORE_FILES = (ROOT / "src/lsx/core/remote.py", ROOT / "src/lsx/ndif.py")


@dataclass(frozen=True)
class Cell:
    id: str
    stage: str
    user_text: str
    candidate_a: str
    candidate_b: str
    domain: str
    format: int
    world: int
    name_order: int = -1
    plan_order: int = -1


def code_digest() -> str:
    h = hashlib.sha256()
    for path in (Path(__file__), Path(__file__).with_name("elicitor_calibration.py"),
                 Path(__file__).with_name("goal_relative_probe.py"),
                 Path(__file__).with_name("role_swap_probe.py"), *CORE_FILES):
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _remote_names(text: str, names: tuple[str, str]) -> tuple[str, tuple[str, str]]:
    if "Oren" not in names:
        return text, names
    if names != ("Niko", "Oren") and names != ("Oren", "Niko"):
        raise ValueError("unexpected Oren pair")
    if len(re.findall(r"\bOren\b", text)) != 1:
        raise ValueError("expected exactly one Oren mention")
    return re.sub(r"\bOren\b", "Otto", text), tuple("Otto" if n == "Oren" else n
                                                     for n in names)


def make_cells() -> tuple[list[Cell], list[Cell], list[Cell], dict]:
    controls, _, cal_hash = make_controls(CAL_GRID)
    cases, story_hash = make_cases(STORY_GRID)
    calibration = []
    for i, row in enumerate(controls):
        story, (good, bad) = _remote_names(row["story"], (row["good"], row["bad"]))
        calibration.append(Cell(f"cal:{i:02d}", "calibration", story, good, bad,
                                row["id"], -1, -1, row["name_order"], row["plan_order"]))
    stories, no_cue = [], []
    domains = json.loads(STORY_GRID.read_text())["domains"]
    for di, d in enumerate(domains):
        for fmt in range(4):
            for world in (0, 1):
                c = cases[di * 16 + fmt * 4 + world * 2]
                prefix = c.text[:c.bridge_char + 2]
                if prefix.count(c.cue) != 1:
                    raise ValueError(f"missing circumstance cue: {d['id']}")
                text, (a, b) = _remote_names(prefix, (d["a"], d["b"]))
                bare, bare_names = _remote_names(prefix.replace(c.cue, "", 1),
                                                 (d["a"], d["b"]))
                if bare_names != (a, b):
                    raise ValueError("name map differs on no-cue arm")
                stories.append(Cell(f"story:{di:02d}:{fmt}:{world}", "story",
                                    text, a, b, d["id"], fmt, world))
                no_cue.append(Cell(f"no_cue:{di:02d}:{fmt}:{world}", "no_cue",
                                   bare, a, b, d["id"], fmt, world))
        group = no_cue[-8:]
        for fmt in range(4):
            x, y = group[fmt * 2:fmt * 2 + 2]
            if x.user_text != y.user_text or (x.candidate_a, x.candidate_b) != (
                    y.candidate_a, y.candidate_b):
                raise ValueError(f"no-cue world twins differ: {d['id']}")
    return calibration, stories, no_cue, {"calibration_grid_sha256": cal_hash,
                                          "story_grid_sha256": story_hash}


def render(rlm, cell: Cell) -> str:
    return rlm.tok.apply_chat_template(
        [{"role": "user", "content": cell.user_text.rstrip() + "\n\n" + QUESTION}],
        tokenize=False, add_generation_prompt=True)


def validate_tokens(rlm, cells: list[Cell]) -> None:
    from lsx.core.remote import strip_template_bos

    tok = rlm.tok
    for cell in cells:
        lead = strip_template_bos(tok, render(rlm, cell))
        base = tok(lead, add_special_tokens=True)["input_ids"]
        lengths = []
        for name in (cell.candidate_a, cell.candidate_b):
            full = tok(lead + name, add_special_tokens=True)["input_ids"]
            if full[:len(base)] != base:
                raise ValueError(f"candidate changes prompt token prefix: {cell.id}")
            lengths.append(len(full) - len(base))
        if lengths[0] != lengths[1]:
            raise ValueError(f"unequal name token counts: {cell.id} {lengths}")
        if not lengths[0]:
            raise ValueError(f"empty candidate: {cell.id}")


def fingerprint(cell: Cell, lead: str, digests: dict) -> str:
    payload = {"model": MODEL, "id": cell.id, "lead": lead,
               "candidates": [cell.candidate_a, cell.candidate_b], **digests}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def _load_cache(path: Path, expected: dict[str, str]) -> dict[str, dict]:
    saved = {}
    if not path.exists():
        return saved
    for line in path.read_text().splitlines():
        row = json.loads(line)
        key = row["id"]
        if key not in expected or row["fp"] != expected[key] or key in saved:
            raise ValueError(f"stale or duplicate remote score: {key}")
        scores = row["scores"]
        if len(scores) != 2 or not all(math.isfinite(x) for x in scores):
            raise ValueError(f"invalid remote score: {key}")
        saved[key] = row
    return saved


def _score_remote(rlm, lead: str, a: str, b: str) -> list[float]:
    from lsx.core.remote import asserted_remote_patched_logprob

    for attempt in range(12):
        try:
            scores = asserted_remote_patched_logprob(rlm, lead, [a, b])
            if scores.shape != (2,) or not np.isfinite(scores).all():
                raise ValueError("invalid two-name remote score")
            return list(map(float, scores))
        except Exception as exc:
            message = str(exc).lower()
            transient = any(term in message for term in (
                "out of memory", "cuda out of memory", "503 service unavailable",
                "502 bad gateway", "429 too many requests", "deployment unavailable"))
            if not transient or attempt == 11:
                raise
            time.sleep(20)
    raise AssertionError("unreachable")


def _get_scores(rlm, cells: list[Cell], saved: dict, fps: dict,
                cache_path: Path) -> dict:
    for cell in cells:
        if cell.id in saved:
            continue
        lead = render(rlm, cell)
        scores = _score_remote(rlm, lead, cell.candidate_a, cell.candidate_b)
        row = {"id": cell.id, "fp": fps[cell.id], "scores": scores}
        with cache_path.open("a") as handle:
            handle.write(json.dumps(row) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        saved[cell.id] = row
        print(f"scored {cell.id}", flush=True)
    return saved


def calibration_report(cells: list[Cell], saved: dict) -> dict:
    if len(cells) != 16:
        raise ValueError("expected sixteen crossed controls")
    margins = np.array([saved[c.id]["scores"][0] - saved[c.id]["scores"][1]
                        for c in cells], dtype=float).reshape(4, 2, 2)
    return {"margins": margins.tolist(), "correct_of_16": int((margins > 0).sum()),
            "min_margin": float(margins.min()),
            "mean_margin": float(margins.mean()),
            "name_order_means": list(map(float, margins.mean(axis=(0, 2)))),
            "plan_order_means": list(map(float, margins.mean(axis=(0, 1)))),
            "position_effect": float(margins[:, :, 0].mean() -
                                     margins[:, :, 1].mean()),
            "gate_pass": bool(np.all(margins > .1))}


def story_report(stories: list[Cell], no_cue: list[Cell], saved: dict,
                 n_perm: int = 1000) -> dict:
    if len(stories) != 96 or len(no_cue) != 96:
        raise ValueError("expected ninety-six story and no-cue cells")
    margins = np.array([saved[c.id]["scores"][0] - saved[c.id]["scores"][1]
                        for c in stories], dtype=float).reshape(12, 4, 2)
    bare = np.array([saved[c.id]["scores"][0] - saved[c.id]["scores"][1]
                     for c in no_cue], dtype=float).reshape(12, 4, 2)
    correct = np.stack((margins[:, :, 0] > 1e-9,
                        margins[:, :, 1] < -1e-9), axis=-1)
    accuracy = correct.astype(float) + .5 * (np.abs(margins) <= 1e-9)
    delta = margins[:, :, 0] - margins[:, :, 1]
    switch = (delta > 1e-9) + .5 * (np.abs(delta) <= 1e-9)
    no_cue_delta = bare[:, :, 0] - bare[:, :, 1]
    no_cue_switch = (no_cue_delta > 1e-9) + .5 * (np.abs(no_cue_delta) <= 1e-9)
    rng = np.random.default_rng(SEED + 31)
    null = []
    for _ in range(n_perm):
        signs = rng.choice([-1, 1], size=(12, 1))
        x = delta * signs
        null.append(float(((x > 1e-9) + .5 * (np.abs(x) <= 1e-9)).mean()))
    observed = float(switch.mean())
    p = (1 + sum(x >= observed for x in null)) / (n_perm + 1)
    halves = {"fact_0": float(accuracy[:, :2].mean()),
              "fact_1": float(accuracy[:, 2:].mean()),
              "cue_0": float(accuracy[:, 0::2].mean()),
              "cue_1": float(accuracy[:, 1::2].mean())}
    no_cue_max = float(np.abs(no_cue_delta).max())
    gates = {"cell_accuracy": bool(accuracy.mean() >= .70),
             "world_switch": bool(observed >= .75),
             "permutation": bool(p <= .05),
             "no_cue_repeat": bool(no_cue_max <= .25),
             **{name: bool(value > .5) for name, value in halves.items()}}
    return {"n_cells": 96, "cell_accuracy": float(accuracy.mean()),
            "both_worlds_correct_fraction": float(correct.all(axis=-1).mean()),
            "world_switch_fraction": observed, "order_halves": halves,
            "domain_world_switch": list(map(float, switch.mean(axis=1))),
            "domain_mean_world_margin_delta": list(map(float, delta.mean(axis=1))),
            "no_cue_world_switch_fraction": float(no_cue_switch.mean()),
            "no_cue_max_abs_world_delta": no_cue_max,
            "permutation": {"draws": n_perm, "mean": float(np.mean(null)),
                            "q95": float(np.quantile(null, .95)),
                            "p_ge_observed": float(p)},
            "gate_components": gates, "gate_pass": all(gates.values())}


def main() -> None:
    from lsx.core.remote import RemoteLM

    calibration, stories, no_cue, digests = make_cells()
    digests["code_sha256"] = code_digest()
    REMOTE_OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(MODEL)
    validate_tokens(rlm, calibration + stories + no_cue)
    fps = {c.id: fingerprint(c, render(rlm, c), digests)
           for c in calibration + stories + no_cue}
    cache_path = REMOTE_OUT / "cells.jsonl"
    saved = _load_cache(cache_path, fps)
    saved = _get_scores(rlm, calibration, saved, fps, cache_path)
    cal = calibration_report(calibration, saved)
    report = {"model": MODEL, "question": QUESTION, "name_substitution": "Oren→Otto",
              "digests": digests, "versions": rlm.lib_versions(), "calibration": cal,
              "story": None}
    if cal["gate_pass"]:
        saved = _get_scores(rlm, stories, saved, fps, cache_path)
        saved = _get_scores(rlm, no_cue, saved, fps, cache_path)
        report["story"] = story_report(stories, no_cue, saved)
    (REMOTE_OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
