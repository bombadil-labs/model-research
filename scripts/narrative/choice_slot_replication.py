"""Independent property-task replication with an exact target-label null."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import itertools
import json
import os
from pathlib import Path
import re

import numpy as np

import choice_slot_analyze as analysis
import choice_slot_controls as prior
import fact_flip_twohop as base
import goal_route_activation_pilot as pilot
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/choice_slot_replication_v1.json"
OUT = ROOT / "cache/choice_slot_replication/v1"
CODE_FILES = (Path(__file__), Path(analysis.__file__), Path(prior.__file__),
              Path(pilot.__file__), Path(cross.__file__), Path(base.__file__),
              *base.CORE_FILES)
SEED = 20260923
PRIMARY = pilot.BLOCKS.index(24)


def _digest() -> str:
    h = hashlib.sha256()
    for path in CODE_FILES:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def make_cells() -> tuple[list[cross.Cell], dict, dict]:
    raw = GRID.read_bytes()
    doc = json.loads(raw)
    route = json.loads(cross.GRID.read_bytes())
    if (len(doc["domains"]) != 8 or doc["bridge_source"] !=
            "goal_route_cross_v1.json:bridge" or
            doc["question"] != json.loads(prior.GRID.read_bytes())["question"]):
        raise ValueError("replication grid changed")
    if len({r["id"] for r in doc["domains"]}) != 8:
        raise ValueError("property domains are not unique")
    bridge = route["bridge"]
    cells = []
    for di, row in enumerate(doc["domains"]):
        if (len(row["labels"]) != 2 or len(set(row["labels"])) != 2 or
                len(row["names"]) != 2 or len(set(row["names"])) != 2 or
                len(row["names"][0]) != len(row["names"][1])):
            raise ValueError(f"invalid property row: {row['id']}")
        for telling, name_order, fact_order, world, goal in itertools.product(
                (0, 1), repeat=5):
            names = row["names"] if name_order == 0 else row["names"][::-1]
            labels = row["labels"] if world == 0 else row["labels"][::-1]
            facts = [row["fact_template"].format(name=n, label=l)
                     for n, l in zip(names, labels)]
            fact_text = "".join(facts if fact_order == 0 else facts[::-1])
            goal_text = row["goal_template"].format(label=row["labels"][goal])
            body = (goal_text + fact_text if telling == 0 else
                    fact_text + goal_text)
            text = row["setup"] + body + bridge
            ident = f"property_rep:{di:02d}:{telling}:{name_order}:{fact_order}:{world}:{goal}"
            if any(len(re.findall(r"\b" + re.escape(n) + r"\b", text)) != 1
                   for n in names):
                raise ValueError(f"name mentioned more than once: {ident}")
            cells.append(cross.Cell(
                id=ident, stage="property_rep", domain=row["id"], world=world,
                telling=telling, name_order=name_order, plan_order=fact_order,
                user_text=text, plan_a_name=names[0], plan_b_name=names[1],
                goal=goal))
    if len(cells) != 256 or len({c.id for c in cells}) != 256:
        raise ValueError("replication cell count differs")
    for i in range(0, len(cells), 4):
        four = cells[i:i + 4]
        if [(c.world, c.goal) for c in four] != [
                (0, 0), (0, 1), (1, 0), (1, 1)]:
            raise ValueError("quartet ordering changed")
        if len({c.user_text[-200:] for c in four}) != 1:
            raise ValueError(f"quartet suffix changed: {four[0].id}")
        for goal in (0, 1):
            a, b = four[goal], four[2 + goal]
            if (base._words(a.user_text) != base._words(b.user_text) or
                    len(a.user_text) != len(b.user_text)):
                raise ValueError(f"world pair surface changed: {a.id}")
        for world in (0, 1):
            if four[2 * world].user_text == four[2 * world + 1].user_text:
                raise ValueError(f"goal pair did not change: {four[2 * world].id}")
    digests = {"property_grid_sha256": hashlib.sha256(raw).hexdigest(),
               "route_grid_sha256": hashlib.sha256(cross.GRID.read_bytes()).hexdigest(),
               "code_sha256": _digest(),
               "tokenizer_revision": cross.TOKENIZER_REVISION}
    return cells, doc, digests


def _fp(cell: cross.Cell, prompt: str, question: str, digests: dict,
        *, kind: str) -> str:
    body = {"id": cell.id, "prompt": prompt, "question": question,
            "kind": kind, "model": cross.MODEL, **digests}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _path(cell: cross.Cell) -> Path:
    return OUT / "states" / (hashlib.sha256(cell.id.encode()).hexdigest() + ".npz")


def _load(cell: cross.Cell, fp: str, hidden: int) -> np.ndarray | None:
    path = _path(cell)
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        if z["id"].item() != cell.id or z["fp"].item() != fp:
            raise ValueError(f"stale target state: {cell.id}")
        arr = np.asarray(z["vec"], dtype=np.float32)
    if arr.shape != (len(pilot.BLOCKS), hidden) or not np.isfinite(arr).all():
        raise ValueError(f"invalid target vector: {cell.id}")
    return arr


def _save(cell: cross.Cell, fp: str, arr: np.ndarray) -> None:
    path = _path(cell)
    tmp = path.with_suffix(".tmp.npz")
    with tmp.open("wb") as handle:
        np.savez_compressed(handle, id=cell.id, fp=fp,
                            vec=np.asarray(arr, dtype=np.float32))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _repeats(cells: list[cross.Cell]) -> list[cross.Cell]:
    return [replace(cells[di * 32], id=f"property_rep_repeat:{di:02d}",
                    stage="property_rep_repeat") for di in range(8)]


def behavior_report(cells: list[cross.Cell], saved: dict) -> dict:
    margins = np.asarray([cross.role_margin(c, saved) for c in cells],
                         dtype=np.float64).reshape(8, 2, 2, 2, 2, 2)
    d0 = margins[..., 0, 0] - margins[..., 1, 0]
    d1 = margins[..., 1, 1] - margins[..., 0, 1]
    joint = (d0 > .25) & (d1 > .25)
    strict = ((margins[..., 0, 0] > .1) & (margins[..., 0, 1] < -.1) &
              (margins[..., 1, 0] < -.1) & (margins[..., 1, 1] > .1))
    halves = {"early": float(joint[:, 0].mean()),
              "late": float(joint[:, 1].mean()),
              "name_0": float(joint[:, :, 0].mean()),
              "name_1": float(joint[:, :, 1].mean()),
              "fact_order_0": float(joint[:, :, :, 0].mean()),
              "fact_order_1": float(joint[:, :, :, 1].mean())}
    gates = {"joint_at_least_48_of_64": int(joint.sum()) >= 48,
             "early_at_least_0_60": halves["early"] >= .60,
             "late_at_least_0_60": halves["late"] >= .60,
             **{k + "_above_half": v > .5 for k, v in halves.items()
                if k.startswith("name_") or k.startswith("fact_order_")}}
    return {"joint_success": int(joint.sum()), "joint_total": 64,
            "strict_four_cell_choices": int(strict.sum()),
            "joint_by_domain": joint.mean(axis=(1, 2, 3)).tolist(),
            "factor_halves": halves, "margins": margins.tolist(),
            "d0": d0.tolist(), "d1": d1.tolist(),
            "gate_components": gates, "gate_pass": all(gates.values())}


def _source_states(rlm, source: dict, stories: list[cross.Cell],
                   route_question: str) -> np.ndarray:
    hidden = int(rlm.model.config.hidden_size)
    rows = []
    for cell in stories:
        prompt = prior._render(rlm, cell, route_question)
        fp = pilot._fp(cell, prompt, source["digests"])
        arr = pilot._load(cell, fp, hidden)
        if arr is None:
            raise ValueError(f"missing source state: {cell.id}")
        rows.append(arr)
    return np.stack(rows).reshape(8, 2, 2, 2, 2, 2,
                                  len(pilot.BLOCKS), hidden).astype(np.float64)


def _extract_all(rlm, cells: list[cross.Cell], question: str,
                 digests: dict) -> dict:
    repeats = _repeats(cells)
    all_cells = cells + repeats
    fps = {c.id: _fp(c, prior._render(rlm, c, question), question,
                     digests, kind="activation") for c in all_cells}
    hidden = int(rlm.model.config.hidden_size)
    first = cells[0]
    arr = _load(first, fps[first.id], hidden)
    if arr is None:
        arr = pilot._extract_one(rlm, prior._render(rlm, first, question))
        _save(first, fps[first.id], arr)
        print(f"extracted {first.id}", flush=True)
    core_equivalence = pilot._equivalence(rlm, first, arr, question)
    for cell in all_cells:
        if cell.id == first.id:
            continue
        arr = _load(cell, fps[cell.id], hidden)
        if arr is None:
            arr = pilot._extract_one(rlm, prior._render(rlm, cell, question))
            _save(cell, fps[cell.id], arr)
            print(f"extracted {cell.id}", flush=True)
    return {"n_cells": len(cells), "n_repeats": len(repeats),
            "core_equivalence": core_equivalence}


def analyze(source_h: np.ndarray, target_h: np.ndarray,
            repeat_diffs: np.ndarray, behavior: dict, preflight: dict,
            *, n_random: int = 1000) -> dict:
    source, _ = analysis._unit_interactions(source_h)
    target, norms = analysis._unit_interactions(target_h)
    direction = analysis._direction(source, np.ones(8))
    cross_scores = analysis._score(target, direction)
    domain_block = cross_scores.mean(axis=(1, 2, 3))
    observed = float(domain_block[:, PRIMARY].mean())
    domain_values = domain_block[:, PRIMARY]
    null = np.asarray([np.mean(domain_values * np.asarray(signs))
                       for signs in itertools.product((-1, 1), repeat=8)])
    if null[-1] != observed:
        raise ValueError("identity target-label null differs from observed")
    ci = analysis._bootstrap(domain_values, seed_offset=200)
    within = analysis._within(target)
    within_values = within[..., PRIMARY].mean(axis=1)
    within_mean = float(within_values.mean())
    within_ci = analysis._bootstrap(within_values, seed_offset=201)
    within_resolved = bool(within_mean >= .05 and within_ci[0] > 0 and
                           int((within_values > 0).sum()) >= 6)
    drift = np.linalg.norm(repeat_diffs, axis=-1).max(axis=0)
    median_norm = np.median(norms, axis=(0, 1, 2, 3))
    repeat_ratio = np.divide(drift, median_norm,
                             out=np.full_like(drift, np.inf),
                             where=median_norm > 0)
    resolved = norms > 10 * drift[None, None, None, None, :]
    readable = bool(np.all(repeat_ratio <= .01) and
                    np.all(resolved[..., PRIMARY]))
    rng = np.random.default_rng(SEED + 300)
    random_arms = []
    for li, block in enumerate(pilot.BLOCKS):
        vectors = rng.standard_normal((n_random, target.shape[-1]))
        vectors /= np.linalg.norm(vectors, axis=-1, keepdims=True)
        random_scores = vectors @ target[..., li, :].mean(axis=(0, 1, 2, 3))
        random_arms.append({"block": block,
                            "mean": float(random_scores.mean()),
                            "q95": float(np.quantile(random_scores, .95)),
                            "observed_percentile": float(np.mean(
                                random_scores <= cross_scores[..., li].mean()))})
    same_length = (np.asarray(preflight[
        "goal_1_minus_goal_0_tokens_by_quartet"]).reshape(8, 2, 2, 2) == 0)
    length_split = {}
    for label, mask in (("same", same_length), ("changed", ~same_length)):
        length_split[label] = {
            "n_quartets": int(mask.sum()),
            "block24": (float(cross_scores[..., PRIMARY][mask].mean())
                        if mask.any() else None)}
    gates = {"behavior": bool(behavior["gate_pass"]),
             "readable": readable,
             "within_resolved": within_resolved,
             "target_orientation_p": float(np.mean(null >= null[-1])) <= .05,
             "bootstrap_lower": ci[0] > 0,
             "at_least_six_positive_domains": int((domain_values > 0).sum()) >= 6,
             "half_within_reference": (observed >= .5 * within_mean
                                       if within_resolved else False)}
    return {"block_indices": list(pilot.BLOCKS), "primary_block": 24,
            "route_to_target_curve": cross_scores.mean(axis=(0, 1, 2, 3)).tolist(),
            "route_to_target_block24": observed,
            "route_to_target_by_domain_block24": domain_values.tolist(),
            "route_to_target_by_telling_block24": cross_scores[..., PRIMARY].mean(
                axis=(0, 2, 3)).tolist(),
            "route_to_target_by_name_block24": cross_scores[..., PRIMARY].mean(
                axis=(0, 1, 3)).tolist(),
            "route_to_target_by_order_block24": cross_scores[..., PRIMARY].mean(
                axis=(0, 1, 2)).tolist(),
            "route_to_target_ci95": ci,
            "target_orientation_null": {"draws": len(null),
                                        "mean": float(null.mean()),
                                        "q95": float(np.quantile(null, .95)),
                                        "p_ge_observed": float(np.mean(null >= null[-1]))},
            "within_target_curve": within.mean(axis=(0, 1)).tolist(),
            "within_target_block24": within_mean,
            "within_target_by_domain_block24": within_values.tolist(),
            "within_target_by_telling_block24": within[..., PRIMARY].mean(
                axis=0).tolist(),
            "within_target_ci95": within_ci,
            "route_over_internal_ratio": (observed / within_mean
                                          if within_mean != 0 else None),
            "random_directions": {"draws_per_block": n_random,
                                  "calibration": random_arms},
            "median_interaction_norm_by_block": median_norm.tolist(),
            "max_repeat_l2_by_block": drift.tolist(),
            "repeat_to_interaction_ratio_by_block": repeat_ratio.tolist(),
            "unresolved_interactions_by_block": (~resolved).sum(
                axis=(0, 1, 2, 3)).tolist(),
            "goal_length_split": length_split,
            "same_goal_token_length_fraction": preflight[
                "same_goal_token_length_fraction"],
            "gate_components": gates,
            "generic_component_compatible": all(gates.values())}


def main() -> None:
    from lsx.core.remote import RemoteLM

    cells, doc, digests = make_cells()
    _, stories, route_doc, _, source = prior._source_and_direct()
    OUT.joinpath("states").mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("local tokenizer revision changed")
    preflight = prior._validate_tokens(rlm, cells, doc["question"])
    surface = pilot._surface_nulls(cells)
    source_h = _source_states(rlm, source, stories, route_doc["question"])
    prompts = {c.id: prior._render(rlm, c, doc["question"]) for c in cells}
    score_fps = {c.id: _fp(c, prompts[c.id], doc["question"], digests,
                           kind="logprob") for c in cells}
    score_path = OUT / "scores.jsonl"
    scores = base._load_cache(score_path, score_fps, generation=False)
    base.score_cells(rlm, cells, scores, score_fps, score_path, doc["question"])
    behavior = behavior_report(cells, scores)
    extraction = _extract_all(rlm, cells, doc["question"], digests)
    hidden = int(rlm.model.config.hidden_size)
    arrays = {}
    for cell in cells + _repeats(cells):
        prompt = prior._render(rlm, cell, doc["question"])
        fp = _fp(cell, prompt, doc["question"], digests, kind="activation")
        arr = _load(cell, fp, hidden)
        if arr is None:
            raise ValueError(f"missing target state: {cell.id}")
        arrays[cell.id] = arr
    target_h = np.stack([arrays[c.id] for c in cells]).reshape(
        8, 2, 2, 2, 2, 2, len(pilot.BLOCKS), hidden).astype(np.float64)
    repeat_diffs = np.stack([arrays[r.id] - arrays[cells[di * 32].id]
                             for di, r in enumerate(_repeats(cells))]).astype(np.float64)
    report = analyze(source_h, target_h, repeat_diffs, behavior, preflight)
    report.update({"model_checkpoint": cross.MODEL,
                   "deployment_weight_revision": None,
                   "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
                   "source_pilot_sha256": hashlib.sha256(prior.SOURCE.read_bytes()).hexdigest(),
                   "versions": rlm.lib_versions(), "digests": digests,
                   "behavior": behavior, "token_preflight": preflight,
                   "surface_nulls": surface, "core_equivalence": extraction,
                   "source_route_reference": source["transfer_curve"][PRIMARY]})
    path = OUT / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("generic_component_compatible", report["generic_component_compatible"], flush=True)
    print("route_to_target", report["route_to_target_block24"], flush=True)
    print(f"wrote {path}", flush=True)


if __name__ == "__main__":
    main()
