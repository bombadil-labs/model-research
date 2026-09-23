"""Signed block-24 answer-slot intervention; see answer_slot_patch_prereg.md."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path
import time

import numpy as np

import choice_slot_analyze as analysis
import choice_slot_controls as prior
import choice_slot_replication as replication
import fact_flip_twohop as base
import goal_route_activation_pilot as pilot
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cache/answer_slot_patch/v1"
LAYER = 24
LAST_LAYER = 41
NORM = 20.0
SEED = 20260923
NONZERO = ("u_plus", "u_minus", "r1_plus", "r1_minus",
           "r2_plus", "r2_minus")
ARMS = ("none", "zero", *(f"{name}_24" for name in NONZERO),
        *(f"{name}_41" for name in NONZERO))
CODE_FILES = (Path(__file__), Path(analysis.__file__), Path(prior.__file__),
              Path(replication.__file__), Path(pilot.__file__),
              Path(cross.__file__), Path(base.__file__), *base.CORE_FILES)


def _digest() -> str:
    h = hashlib.sha256()
    for path in CODE_FILES:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def selected_cells(cells: list[cross.Cell]) -> list[cross.Cell]:
    chosen = [c for c in cells if c.telling == 0 and c.world == 0]
    if (len(chosen) != 64 or len({c.id for c in chosen}) != 64 or
            any(c.telling != 0 or c.world != 0 for c in chosen)):
        raise ValueError("patch target subset changed")
    for di in range(8):
        group = chosen[di * 8:(di + 1) * 8]
        if [(c.name_order, c.plan_order, c.goal) for c in group] != list(
                itertools.product((0, 1), repeat=3)):
            raise ValueError(f"target factor order changed: {di}")
    return chosen


def vectors(source_h: np.ndarray) -> dict[str, np.ndarray | None]:
    unit, _ = analysis._unit_interactions(source_h)
    direction = np.asarray(analysis._direction(unit, np.ones(8))[
        pilot.BLOCKS.index(LAYER)], dtype=np.float64)
    if not np.isfinite(direction).all() or not np.isclose(
            np.linalg.norm(direction), 1.0, atol=1e-6):
        raise ValueError("source direction not unit length")
    out = {"none": None, "zero": np.zeros_like(direction, dtype=np.float32),
           "u_plus": (NORM * direction).astype(np.float32),
           "u_minus": (-NORM * direction).astype(np.float32)}
    for i, seed in enumerate((SEED, SEED + 1), start=1):
        rng = np.random.default_rng(seed)
        random = rng.standard_normal(direction.shape)
        random /= np.linalg.norm(random)
        out[f"r{i}_plus"] = (NORM * random).astype(np.float32)
        out[f"r{i}_minus"] = (-NORM * random).astype(np.float32)
    for name, vec in out.items():
        if vec is not None and name != "zero" and not np.isclose(
                np.linalg.norm(vec), NORM, atol=1e-5):
            raise ValueError(f"patch norm changed: {name}")
    return out


def _fp(cell: cross.Cell, prompt: str, arm: str, vec: np.ndarray | None,
        digests: dict) -> str:
    vector_sha = None if vec is None else hashlib.sha256(
        np.asarray(vec, dtype=np.float32).tobytes()).hexdigest()
    layer = (LAST_LAYER if arm.endswith("_41") else LAYER
             if arm != "none" else None)
    body = {"model": cross.MODEL, "id": cell.id, "prompt": prompt,
            "candidates": cell.candidates, "arm": arm, "layer": layer,
            "vector_sha256": vector_sha, **digests}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def preflight_tokens(rlm, cells: list[cross.Cell], question: str) -> dict:
    from lsx.core.remote import assert_single_bos, strip_template_bos
    import torch

    tok = rlm.tok
    if rlm.padding_side != "left":
        raise ValueError("remote padding convention changed")
    lengths = {}
    for cell in cells:
        prompt = prior._render(rlm, cell, question)
        lead = strip_template_bos(tok, prompt)
        lead_ids = tok(lead, add_special_tokens=True)["input_ids"]
        assert_single_bos(torch.tensor([lead_ids]),
                          torch.ones((1, len(lead_ids))), tok.bos_token_id)
        candidate_counts = []
        for candidate in cell.candidates:
            ids = tok(lead + candidate, add_special_tokens=True)["input_ids"]
            if ids[:len(lead_ids)] != lead_ids:
                raise ValueError(f"candidate changes prompt tokens: {cell.id}")
            candidate_counts.append(len(ids) - len(lead_ids))
        if candidate_counts != [1, 1]:
            raise ValueError(f"patch target names are not one token: {cell.id}")
        full_length = len(lead_ids) + 1
        encoded = tok([lead + c for c in cell.candidates], return_tensors="pt",
                      padding=True, add_special_tokens=True)
        if (encoded["input_ids"].shape != (2, full_length) or
                not bool(encoded["attention_mask"].all())):
            raise ValueError(f"scoring batch carries padding: {cell.id}")
        lengths[cell.id] = full_length
    return {"n_cells": len(cells), "candidate_tokens": 1,
            "full_tokens_min": min(lengths.values()),
            "full_tokens_max": max(lengths.values()),
            "shortest_id": min(lengths, key=lengths.get)}


def _remote_scores(rlm, prompt: str, candidates: tuple[str, str],
                   vec: np.ndarray | None, layer: int | None,
                   baseline: list[float] | None) -> tuple[list[float], bool]:
    from lsx.core.remote import asserted_remote_patched_logprob
    from lsx.core import checks

    def once(armed_base):
        for attempt in range(12):
            try:
                scores = asserted_remote_patched_logprob(
                    rlm, prompt, list(candidates), patch_layer=layer,
                    patch_vec=vec, base=armed_base)
                if scores.shape != (2,) or not np.isfinite(scores).all():
                    raise ValueError("invalid patch score vector")
                return np.asarray(scores, dtype=np.float64)
            except checks.MovedCandidates:
                raise
            except Exception as exc:
                transient = any(term in str(exc).lower() for term in (
                    "out of memory", "503 service unavailable", "502 bad gateway",
                    "429 too many requests", "deployment unavailable",
                    "not complete after", "timed out"))
                if not transient or attempt == 11:
                    raise
                time.sleep(20)
        raise AssertionError("unreachable")

    try:
        scores = once(baseline)
        return list(map(float, scores)), False
    except checks.MovedCandidates:
        if baseline is None or vec is None:
            raise
        a, b = once(None), once(None)
        if float(np.max(np.abs(a - b))) > .001:
            raise ValueError("moved-candidate fallback is not deterministic")
        return list(map(float, b)), True


def _preflight_reach(rlm, cell: cross.Cell, question: str,
                     vecs: dict, digests: dict) -> dict:
    from lsx.core.remote import (assert_patch_reaches_batch,
                                 remote_residuals, strip_template_bos)
    import torch

    prompt = prior._render(rlm, cell, question)
    lead = strip_template_bos(rlm.tok, prompt)
    texts = [lead + c for c in cell.candidates]
    position = len(rlm.tok(lead, add_special_tokens=True)["input_ids"]) - 1
    final_base = remote_residuals(rlm, texts, LAST_LAYER)
    reached = {}
    final_max_error = {}
    for layer in (LAYER, LAST_LAYER):
        for name in NONZERO:
            arm = f"{name}_{layer}"
            reached[arm] = assert_patch_reaches_batch(
                rlm, texts, layer, vecs[name])
            if reached[arm] != 2:
                raise ValueError(f"patch did not reach both candidate rows: {arm}")
            if layer == LAST_LAYER:
                final_patched = remote_residuals(
                    rlm, texts, LAST_LAYER, patch_layer=LAST_LAYER,
                    patch_vec=vecs[name])
                expected = (torch.as_tensor(final_base[:, position, :]).to(torch.bfloat16) +
                            torch.as_tensor(vecs[name]).to(torch.bfloat16)).float().numpy()
                error = float(np.max(np.abs(final_patched[:, position, :] - expected)))
                if error > .001:
                    raise ValueError(f"direct-path residual arithmetic failed: {arm}: {error}")
                final_max_error[arm] = error
    return {"id": cell.id, "candidate_batch": 2, "moved_residual_rows": reached,
            "last_block_arithmetic_max_abs_error": final_max_error,
            "prompt_token_index": position, "digests": digests}


def _cached_previous(rlm, all_cells: list[cross.Cell], question: str,
                     digests: dict) -> dict:
    prompts = {c.id: prior._render(rlm, c, question) for c in all_cells}
    expected = {c.id: replication._fp(c, prompts[c.id], question, digests,
                                      kind="logprob") for c in all_cells}
    return base._load_cache(replication.OUT / "scores.jsonl", expected,
                            generation=False)


def _natural_gap(rlm, cells: list[cross.Cell], question: str,
                 target_digests: dict, u: np.ndarray) -> dict:
    hidden = int(rlm.model.config.hidden_size)
    states = []
    for cell in cells:
        prompt = prior._render(rlm, cell, question)
        fp = replication._fp(cell, prompt, question, target_digests,
                             kind="activation")
        arr = replication._load(cell, fp, hidden)
        if arr is None:
            raise ValueError(f"missing unpatched target state: {cell.id}")
        states.append(arr[pilot.BLOCKS.index(LAYER)])
    h = np.stack(states).reshape(8, 2, 2, 2, hidden).astype(np.float64)
    gaps = np.abs((h[..., 0, :] - h[..., 1, :]) @ u)
    return {"goal_flip_projection_gap_median": float(np.median(gaps)),
            "goal_flip_projection_gap_min": float(gaps.min()),
            "goal_flip_projection_gap_max": float(gaps.max()),
            "patch_norm_over_median_gap": float(NORM / np.median(gaps))}


def _effect_report(effect: np.ndarray, *, seed_offset: int) -> dict:
    domain = effect.mean(axis=(1, 2, 3))
    observed = float(domain.mean())
    null = np.array([float(np.mean(domain * np.array(signs))) for signs in
                     itertools.product((-1, 1), repeat=8)])
    if not np.isclose(null[-1], observed, atol=1e-12):
        raise ValueError("identity sign null disagrees")
    rng = np.random.default_rng(SEED + seed_offset)
    boot = domain[rng.integers(0, 8, size=(10000, 8))].mean(axis=1)
    ties = int(np.sum(np.isclose(null, observed, atol=1e-12, rtol=0)))
    return {"mean": observed, "domain_effects": domain.tolist(),
            "cell_effects": effect.tolist(),
            "positive_domains": int((domain > 0).sum()),
            "positive_cells": int((effect > 0).sum()),
            "exact_domain_sign_null": {"draws": 256,
                                       "mean": float(null.mean()),
                                       "q95": float(np.quantile(null, .95)),
                                       "p_ge_observed": float(np.mean(null >= observed - 1e-12)),
                                       "tie_count_at_observed_excluding_identity": ties - 1},
            "domain_bootstrap": {"draws": 10000,
                                 "ci95": list(map(float, np.quantile(
                                     boot, [.025, .975])))}}


def analyze(cells: list[cross.Cell], saved: dict, previous: dict,
            preflight: dict, reach: dict) -> dict:
    # Selection order is [domain][name][fact order][goal].
    scores = np.array([[saved[f"{c.id}|{arm}"]["scores"] for arm in ARMS]
                       for c in cells], dtype=np.float64).reshape(
                           8, 2, 2, 2, len(ARMS), 2)
    score_a = np.array([int(c.candidates.index(c.plan_a_name)) for c in cells],
                       dtype=np.int64).reshape(8, 2, 2, 2)
    a = np.take_along_axis(scores, score_a[..., None, None], axis=-1)[..., 0]
    b = np.take_along_axis(scores, (1 - score_a)[..., None, None], axis=-1)[..., 0]
    margins = a - b
    sign = np.array([1 if c.plan_order == 0 else -1 for c in cells],
                    dtype=np.float64).reshape(8, 2, 2, 2)
    first = sign[..., None] * margins
    def effect(name: str, layer: int) -> np.ndarray:
        return (first[..., ARMS.index(f"{name}_plus_{layer}")] -
                first[..., ARMS.index(f"{name}_minus_{layer}")]) / 2

    total = effect("u", LAYER)
    direct = effect("u", LAST_LAYER)
    net = total - direct
    random_total = [effect(f"r{i}", LAYER) for i in (1, 2)]
    random_direct = [effect(f"r{i}", LAST_LAYER) for i in (1, 2)]
    random_net = [x - y for x, y in zip(random_total, random_direct)]
    primary = _effect_report(net, seed_offset=400)
    secondary_total = _effect_report(total, seed_offset=401)
    secondary_direct = _effect_report(direct, seed_offset=402)
    observed = primary["mean"]
    ci = primary["domain_bootstrap"]["ci95"]
    max_random = max(abs(float(x.mean())) for x in random_net)
    zero_diff = np.abs(scores[..., ARMS.index("none"), :] -
                       scores[..., ARMS.index("zero"), :])
    previous_scores = np.array([previous[c.id]["scores"] for c in cells],
                               dtype=np.float64).reshape(8, 2, 2, 2, 2)
    drift = np.abs(scores[..., ARMS.index("none"), :] - previous_scores)
    moved = {}
    flagged = {}
    for ai, arm in enumerate(ARMS[2:], start=2):
        n = (np.abs(scores[..., ai, :] -
                    scores[..., ARMS.index("none"), :]) > 1e-6).sum(axis=-1)
        moved[arm] = {str(i): int((n == i).sum()) for i in range(3)}
        flagged[arm] = int(sum(bool(saved[f"{c.id}|{arm}"].get("flagged", False))
                               for c in cells))
    n_flagged = sum(flagged.values())
    first_correct = np.array([c.plan_order == c.goal for c in cells]).reshape(
        8, 2, 2, 2)
    none_first = first[..., ARMS.index("none")] > 0
    plus_first = first[..., ARMS.index("u_plus_24")] > 0
    minus_first = first[..., ARMS.index("u_minus_24")] > 0
    gates = {"residual_reach_all": all(v == 2 for v in reach[
        "moved_residual_rows"].values()),
        "zero_pass_through": float(zero_diff.max()) <= .001,
        "deployment_drift": float(drift.max()) <= .001,
        "flag_fraction_at_most_0_05": n_flagged / (64 * 12) <= .05,
        "mean_at_least_0_10": observed >= .10,
        "exact_p": primary["exact_domain_sign_null"]["p_ge_observed"] <= .05,
        "bootstrap_lower": ci[0] > 0,
        "six_positive_domains": primary["positive_domains"] >= 6,
        "forty_eight_positive_cells": primary["positive_cells"] >= 48,
        "twice_random_max": observed > 2 * max_random}
    return {"primary_net_effect": primary,
            "secondary_total_block24_effect": secondary_total,
            "secondary_direct_block41_effect": secondary_direct,
            "factor_halves_net": {"name_0": float(net[:, 0].mean()),
                                  "name_1": float(net[:, 1].mean()),
                                  "fact_order_0": float(net[:, :, 0].mean()),
                                  "fact_order_1": float(net[:, :, 1].mean()),
                                  "goal_0": float(net[..., 0].mean()),
                                  "goal_1": float(net[..., 1].mean())},
            "random_controls": {f"r{i}": {
                "total_mean": float(x.mean()),
                "direct_mean": float(y.mean()),
                "net_mean": float(z.mean()),
                "net_domain_effects": z.mean(axis=(1, 2, 3)).tolist()}
                for i, (x, y, z) in enumerate(zip(random_total, random_direct,
                                                  random_net), start=1)},
            "max_abs_random_net_mean": max_random,
            "candidate_score_changes": (scores - scores[..., :1, :]).tolist(),
            "moved_candidate_histograms": moved,
            "flagged_job_counts": flagged,
            "flagged_job_fraction": n_flagged / (64 * 12),
            "no_patch_to_zero_max_abs_candidate_difference": float(zero_diff.max()),
            "old_to_new_no_patch_max_abs_candidate_difference": float(drift.max()),
            "first_mention_choices": {
                "no_patch": int(none_first.sum()),
                "plus_u": int(plus_first.sum()),
                "minus_u": int(minus_first.sum()),
                "plus_u_new_first_choices": int((~none_first & plus_first).sum()),
                "plus_u_lost_first_choices": int((none_first & ~plus_first).sum()),
                "plus_u_new_correct_choices": int((~none_first & plus_first & first_correct).sum() +
                                                   (none_first & ~plus_first & ~first_correct).sum()),
                "plus_u_new_incorrect_choices": int((~none_first & plus_first & ~first_correct).sum() +
                                                     (none_first & ~plus_first & first_correct).sum())},
            "first_mention_correct": int(first_correct.sum()),
            "preflight_tokens": preflight,
            "residual_reach": reach,
            "gate_components": gates,
            "positive_screen": all(gates.values())}


def main() -> None:
    from lsx.core.remote import RemoteLM

    all_cells, doc, target_digests = replication.make_cells()
    cells = selected_cells(all_cells)
    _, stories, route_doc, _, source = prior._source_and_direct()
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("local tokenizer revision changed")
    source_h = replication._source_states(rlm, source, stories,
                                          route_doc["question"])
    vecs = vectors(source_h)
    natural_gap = _natural_gap(rlm, cells, doc["question"], target_digests,
                               vecs["u_plus"].astype(np.float64) / NORM)
    arm_vectors = {"none": None, "zero": vecs["zero"],
                   **{f"{name}_{layer}": vecs[name]
                      for layer in (LAYER, LAST_LAYER) for name in NONZERO}}
    checks = preflight_tokens(rlm, cells, doc["question"])
    shortest = next(c for c in cells if c.id == checks["shortest_id"])
    digests = {"target_grid_sha256": target_digests["property_grid_sha256"],
               "source_grid_sha256": target_digests["route_grid_sha256"],
               "source_pilot_sha256": hashlib.sha256(prior.SOURCE.read_bytes()).hexdigest(),
               "code_sha256": _digest(),
               "tokenizer_revision": cross.TOKENIZER_REVISION}
    previous = _cached_previous(rlm, all_cells, doc["question"], target_digests)
    if len(previous) != 256:
        raise ValueError("missing prior no-patch baseline")
    reach = _preflight_reach(rlm, shortest, doc["question"], vecs, digests)
    (OUT / "preflight.json").write_text(json.dumps(reach, indent=2) + "\n")
    prompts = {c.id: prior._render(rlm, c, doc["question"]) for c in cells}
    expected = {f"{c.id}|{arm}": _fp(c, prompts[c.id], arm, arm_vectors[arm], digests)
                for c in cells for arm in ARMS}
    path = OUT / "scores.jsonl"
    saved = base._load_cache(path, expected, generation=False)
    scoring_order = [shortest] + [c for c in cells if c.id != shortest.id]
    for cell in scoring_order:
        prompt = prompts[cell.id]
        for arm in ARMS:
            key = f"{cell.id}|{arm}"
            if key in saved:
                continue
            layer = (LAST_LAYER if arm.endswith("_41") else LAYER
                     if arm != "none" else None)
            baseline = saved[f"{cell.id}|none"]["scores"] if arm not in (
                "none", "zero") else None
            scores, flagged = _remote_scores(
                rlm, prompt, cell.candidates, arm_vectors[arm], layer, baseline)
            row = {"id": key, "fp": expected[key], "scores": scores,
                   "flagged": flagged}
            base._append(path, row)
            saved[key] = row
            print(f"scored {key}", flush=True)
        if cell.id == shortest.id:
            no_patch = np.asarray(saved[f"{cell.id}|none"]["scores"])
            zero = np.asarray(saved[f"{cell.id}|zero"]["scores"])
            old = np.asarray(previous[cell.id]["scores"])
            if (float(np.max(np.abs(no_patch - zero))) > .001 or
                    float(np.max(np.abs(no_patch - old))) > .001):
                raise ValueError("first-prompt zero or deployment-drift gate failed")
    report = analyze(cells, saved, previous, checks, reach)
    report.update({"model_checkpoint": cross.MODEL,
                   "deployment_weight_revision": None,
                   "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
                   "versions": rlm.lib_versions(), "digests": digests,
                   "treatment_layer": LAYER, "direct_layer": LAST_LAYER,
                   "patch_norm": NORM,
                   "arm_vectors_sha256": {arm: (None if vec is None else
                       hashlib.sha256(vec.tobytes()).hexdigest())
                       for arm, vec in arm_vectors.items()},
                   "unpatched_natural_gap": natural_gap,
                   "n_target_prompts": len(cells), "n_jobs": len(expected)})
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("positive_screen", report["positive_screen"], flush=True)
    print("primary_net_effect", report["primary_net_effect"]["mean"], flush=True)


if __name__ == "__main__":
    main()
