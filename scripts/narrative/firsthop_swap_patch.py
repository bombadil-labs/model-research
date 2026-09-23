"""Single-period first-hop route-binding patch; see firsthop_swap_patch_prereg.md."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path

import numpy as np

import fact_flip_twohop as base
import firsthop_swap_behavior as behavior
import firsthop_swap_grid as grid
import goal_route_cross as cross
import prequestion_route_extract as prior
import story_fact_token_patch as old


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cache/firsthop_swap/v1/patch"
ARMS = ("none", "zero", "full", "plan_matched", "first_order_matched",
        "random", "last_block")
ACTIVE = ("full", "plan_matched", "first_order_matched", "random")
SEED = 20260923


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _code_digest() -> str:
    paths = (Path(__file__), Path(grid.__file__), Path(behavior.__file__),
             Path(old.__file__), Path(prior.__file__), Path(base.__file__),
             ROOT / "src/lsx/core/remote.py", ROOT / "src/lsx/core/checks.py",
             ROOT / "src/lsx/ndif.py")
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _fp(cell: cross.Cell, loc: dict, kind: str, arm: str | None,
        vector: np.ndarray | None, digests: dict) -> str:
    layer = (old.LAST_LAYER if arm == "last_block" else old.LAYER
             if arm not in (None, "none") else None)
    payload = {"id": cell.id, "prompt": loc["prompt"],
               "candidates": cell.candidates,
               "period_index": loc["prebridge_index"],
               "period_token_id": loc["prebridge_token_id"],
               "kind": kind, "arm": arm, "patch_layer": layer,
               "vector_sha256": None if vector is None else _sha(
                   np.asarray(vector, dtype=np.float32).tobytes()), **digests}
    return _sha(json.dumps(payload, sort_keys=True).encode())


def _state_path(cell: cross.Cell) -> Path:
    return OUT / "states" / (_sha(cell.id.encode()) + ".npz")


def _state(cell: cross.Cell, fp: str, hidden: int) -> np.ndarray | None:
    path = _state_path(cell)
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        if z["id"].item() != cell.id or z["fp"].item() != fp:
            raise ValueError(f"stale state capture: {cell.id}")
        arr = np.asarray(z["state"], dtype=np.float32)
    if (arr.shape != (2, hidden) or not np.isfinite(arr).all() or
            not np.array_equal(arr[0], arr[1])):
        raise ValueError(f"invalid two-row state: {cell.id}")
    return arr


def _save_state(cell: cross.Cell, fp: str, arr: np.ndarray) -> None:
    path = _state_path(cell)
    tmp = path.with_suffix(".tmp.npz")
    with tmp.open("wb") as handle:
        np.savez_compressed(handle, id=cell.id, fp=fp,
                            state=np.asarray(arr, dtype=np.float32))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def capture_states(rlm, all_cells: list[cross.Cell], located: dict,
                   digests: dict) -> tuple[dict, dict]:
    OUT.joinpath("states").mkdir(parents=True, exist_ok=True)
    hidden = int(rlm.model.config.hidden_size)
    saved, fingerprints = {}, {}
    for cell in all_cells:
        loc = located[cell.id]
        fp = _fp(cell, loc, "state", None, None, digests)
        arr = _state(cell, fp, hidden)
        if arr is None:
            _, arr, _ = old.traced_score(rlm, loc["prompt"], cell.candidates,
                                         loc["prebridge_index"], capture="period")
            if (arr is None or arr.shape != (2, hidden) or
                    not np.array_equal(arr[0], arr[1])):
                raise ValueError(f"candidate rows differ at period: {cell.id}")
            _save_state(cell, fp, arr)
            print(f"captured {cell.id}", flush=True)
        saved[cell.id], fingerprints[cell.id] = arr, fp
    return saved, fingerprints


def _repeat_drift(rlm, cells: list[cross.Cell], located: dict,
                  captures: dict) -> dict:
    result = {}
    for di in range(8):
        cell = cells[di * 16]  # name=plan=world=goal=0, frozen before extraction
        loc = located[cell.id]
        _, repeat, _ = old.traced_score(rlm, loc["prompt"], cell.candidates,
                                        loc["prebridge_index"], capture="period")
        if repeat is None or not np.array_equal(repeat[0], repeat[1]):
            raise ValueError(f"repeat state differs by candidate: {cell.id}")
        initial = captures[cell.id].astype(np.float64)
        relative = float(np.linalg.norm(repeat.astype(np.float64) - initial) /
                         np.linalg.norm(initial))
        result[cell.domain] = relative
    return result


def _vectors(cells: list[cross.Cell], order_cells: list[cross.Cell],
             captures: dict) -> tuple[dict, dict]:
    by = {(c.domain, c.name_order, c.plan_order, c.world, c.goal): c
          for c in cells}
    ordered = {c.id.replace("firsthop:order:", "firsthop:story:"): c
               for c in order_cells}
    hidden = captures[cells[0].id].shape[-1]
    vectors, metrics = {}, {}
    for i, cell in enumerate(cells):
        key = (cell.domain, cell.name_order, cell.plan_order,
               cell.world, cell.goal)
        source = by[key[:3] + (1 - cell.world, cell.goal)]
        plan = by[(cell.domain, cell.name_order, 1 - cell.plan_order,
                   cell.world, cell.goal)]
        order = ordered[cell.id]
        target_h = captures[cell.id][0].astype(np.float64)
        source_h = captures[source.id][0].astype(np.float64)
        full = source_h - target_h
        norm = float(np.linalg.norm(full))
        if not np.isfinite(norm) or norm <= 0:
            raise ValueError(f"zero source-world state difference: {cell.id}")
        plan_delta = captures[plan.id][0].astype(np.float64) - target_h
        order_delta = captures[order.id][0].astype(np.float64) - target_h
        factor_index = (cell.name_order * 8 + cell.plan_order * 4 +
                        cell.goal * 2 + cell.world)
        rng = np.random.default_rng(SEED + (i // 16) * 16 + factor_index)
        vectors[cell.id] = {
            "none": None, "zero": np.zeros(hidden, dtype=np.float32),
            "full": np.asarray(full, dtype=np.float32),
            "plan_matched": old._unit_scaled(plan_delta, norm),
            "first_order_matched": old._unit_scaled(order_delta, norm),
            "random": old._unit_scaled(rng.standard_normal(hidden), norm),
            "last_block": np.asarray(full, dtype=np.float32)}
        metrics[cell.id] = {"source_id": source.id, "plan_id": plan.id,
                            "first_order_id": order.id,
                            "full_norm": norm,
                            "plan_norm": float(np.linalg.norm(plan_delta)),
                            "first_order_norm": float(np.linalg.norm(order_delta)),
                            "target_state_sha256": _sha(captures[cell.id].tobytes()),
                            "source_state_sha256": _sha(captures[source.id].tobytes()),
                            "plan_state_sha256": _sha(captures[plan.id].tobytes()),
                            "first_order_state_sha256": _sha(captures[order.id].tobytes())}
        if any(vec is not None and (vec.shape != (hidden,) or
               not np.isfinite(vec).all()) for vec in vectors[cell.id].values()):
            raise ValueError(f"invalid vector: {cell.id}")
    if len(by) != 128 or len(ordered) != 128:
        raise ValueError("factor keys changed")
    return vectors, metrics


def analyze(cells: list[cross.Cell], rows: dict, doc: dict,
            preflight: dict, core_checks: dict, repeats: dict,
            metrics: dict, digests: dict, versions: dict) -> dict:
    scores = np.array([[rows[f"{c.id}|{arm}"]["scores"] for arm in ARMS]
                       for c in cells], dtype=np.float64).reshape(
                           8, 2, 2, 2, 2, len(ARMS), 2)
    a_index = np.array([c.candidates.index(c.plan_a_name) for c in cells],
                       dtype=np.int64).reshape(8, 2, 2, 2, 2)
    score_a = np.take_along_axis(scores, a_index[..., None, None], axis=-1)[..., 0]
    score_b = np.take_along_axis(scores, (1 - a_index)[..., None, None], axis=-1)[..., 0]
    margins = score_a - score_b
    by = {(c.domain, c.name_order, c.plan_order, c.world, c.goal): c
          for c in cells}
    domain_rows = {row["id"]: row for row in doc["domains"]}
    signs = []
    for cell in cells:
        source = by[(cell.domain, cell.name_order, cell.plan_order,
                     1 - cell.world, cell.goal)]
        winner = grid._winner(source, domain_rows[cell.domain])
        sign = 1 if winner == cell.plan_a_name else -1
        if sign != (1 if (1 - cell.world) == cell.goal else -1):
            raise ValueError(f"source-winner formula disagrees: {cell.id}")
        signs.append(sign)
    signs = np.asarray(signs, dtype=np.float64).reshape(8, 2, 2, 2, 2)
    effects = {arm: signs * (margins[..., ai] - margins[..., 0])
               for ai, arm in enumerate(ARMS) if ai > 0}
    primary = old._effect_report(effects["full"], seed=SEED + 1)
    control_arms = ("plan_matched", "first_order_matched", "random")
    control_mean = {arm: float(effects[arm].mean()) for arm in control_arms}
    max_control = max(abs(value) for value in control_mean.values())
    zero_diff = float(np.max(np.abs(scores[..., ARMS.index("zero"), :] -
                                     scores[..., 0, :])))
    last_diff = float(np.max(np.abs(scores[..., ARMS.index("last_block"), :] -
                                     scores[..., 0, :])))
    flags = {arm: int(sum(bool(rows[f"{c.id}|{arm}"].get("flagged", False))
                          for c in cells)) for arm in ACTIVE}
    flag_fraction = sum(flags.values()) / (128 * len(ACTIVE))
    max_source_error = max(float(rows[f"{c.id}|full"]["source_state_relative_error"])
                           for c in cells)
    gates = {"core_scorer_equivalence": max(core_checks.values()) <= .001,
             "row_zero_negative_refused": bool(preflight["row_zero_only_refused"]),
             "zero_identity": zero_diff <= .001,
             "last_block_pass_through": last_diff <= .001,
             "repeat_drift_at_most_0_02": max(repeats.values()) <= .02,
             "source_state_match_at_most_0_02": max_source_error <= .02,
             "flag_fraction_at_most_0_05": flag_fraction <= .05,
             "mean_at_least_0_25": primary["mean"] >= .25,
             "exact_p": primary["exact_null"]["p_ge_observed"] <= .05,
             "bootstrap_lower": primary["domain_bootstrap"]["ci95"][0] > 0,
             "six_positive_domains": primary["positive_domains"] >= 6,
             "ninety_six_positive_cells": primary["positive_cells"] >= 96,
             "twice_max_control": primary["mean"] > 2 * max_control}
    instrument_names = ("core_scorer_equivalence", "row_zero_negative_refused",
                        "zero_identity", "last_block_pass_through",
                        "repeat_drift_at_most_0_02",
                        "source_state_match_at_most_0_02",
                        "flag_fraction_at_most_0_05")
    instrument_ok = all(gates[name] for name in instrument_names)
    specific = all(gates.values())
    contrasts = {}
    contrast_gates = {}
    for j, arm in enumerate(("first_order_matched", "plan_matched"), start=2):
        report = old._effect_report(effects["full"] - effects[arm],
                                    seed=SEED + j)
        contrasts[arm] = report
        contrast_gates[arm] = {
            "instrument_ok": instrument_ok,
            "mean_at_least_0_10": report["mean"] >= .10,
            "exact_p": report["exact_null"]["p_ge_observed"] <= .05,
            "bootstrap_lower": report["domain_bootstrap"]["ci95"][0] > 0,
            "six_positive_domains": report["positive_domains"] >= 6}
    before = signs * margins[..., 0]
    after = signs * margins[..., ARMS.index("full")]
    initially_favoured = before > 0
    newly_favoured = after > 0
    toward = int((~initially_favoured & newly_favoured).sum())
    away = int((initially_favoured & ~newly_favoured).sum())
    n_favoured = int(initially_favoured.sum())
    favoured_effect = (float(effects["full"][initially_favoured].mean())
                       if n_favoured else None)
    choice_readable = n_favoured >= 8
    choice_gate = bool(specific and choice_readable and toward >= 8 and away <= 4
                       and favoured_effect is not None and favoured_effect > 0)
    absolute_shrink = int((np.abs(margins[..., ARMS.index("full")]) <
                           np.abs(margins[..., 0])).sum())
    return {"specific_margin_screen": specific,
            "choice_redirection_screen": choice_gate,
            "choice_readable": choice_readable,
            "gate_components": gates,
            "secondary_binding_contrasts": contrasts,
            "secondary_contrast_gate_components": contrast_gates,
            "secondary_contrast_screen": {arm: all(values.values())
                                          for arm, values in contrast_gates.items()},
            "primary_full_effect": primary,
            "arm_effects": {arm: old._effect_report(effect, seed=SEED + 10 + i)
                            for i, (arm, effect) in enumerate(effects.items())},
            "control_mean": control_mean,
            "max_abs_control_mean": max_control,
            "choice_flips": {"toward_source": toward, "away_from_source": away,
                             "source_winner_before": n_favoured,
                             "source_winner_after": int(newly_favoured.sum()),
                             "effect_when_source_already_favoured": favoured_effect,
                             "absolute_margin_shrinks": absolute_shrink},
            "flagged_job_counts": flags, "flagged_job_fraction": flag_fraction,
            "max_zero_score_difference": zero_diff,
            "max_last_block_score_difference": last_diff,
            "max_source_state_relative_error": max_source_error,
            "repeat_relative_drift_by_domain": repeats,
            "factor_halves": {
                "name_0": float(effects["full"][:, 0].mean()),
                "name_1": float(effects["full"][:, 1].mean()),
                "plan_0": float(effects["full"][:, :, 0].mean()),
                "plan_1": float(effects["full"][:, :, 1].mean()),
                "world_0": float(effects["full"][:, :, :, 0].mean()),
                "world_1": float(effects["full"][:, :, :, 1].mean()),
                "goal_0": float(effects["full"][..., 0].mean()),
                "goal_1": float(effects["full"][..., 1].mean())},
            "signed_effects": {arm: effect.tolist() for arm, effect in effects.items()},
            "candidate_scores": scores.tolist(),
            "pair_metrics": metrics,
            "preflight": preflight, "core_equivalence": core_checks,
            "model_checkpoint": cross.MODEL,
            "deployment_weight_revision": None,
            "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
            "versions": versions, "digests": digests,
            "patch_block": old.LAYER, "pass_through_block": old.LAST_LAYER,
            "n_target_prompts": len(cells), "n_score_jobs": len(cells) * len(ARMS),
            "n_state_capture_jobs": 256, "n_state_repeat_jobs": 8}


def main() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob
    import torch

    behavior_path = behavior.OUT / "behavior_report.json"
    if not behavior_path.exists():
        raise ValueError("first-hop behavior eligibility has not been scored")
    behavior_report = json.loads(behavior_path.read_text())
    if not behavior_report["eligible_for_patch"]:
        raise ValueError("frozen behavioral eligibility gate failed; no patch allowed")
    if behavior_report["digests"]["grid_sha256"] != behavior.FROZEN_GRID_SHA256:
        raise ValueError("behavior report uses another prompt grid")
    frozen = json.loads(grid.GRID.read_text())
    if (_sha(grid.GRID.read_bytes()) != behavior.FROZEN_GRID_SHA256 or
            frozen != grid.snapshot()):
        raise ValueError("first-hop grid differs from committed exact texts")
    cells, order_cells, metadata = grid.make_cells()
    doc = json.loads(cross.GRID.read_text())
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("tokenizer revision changed")
    audit = grid.token_audit(rlm.tok)
    committed_audit = json.loads((ROOT / "research/narrative/results/firsthop_swap_v1_token_audit.json").read_text())
    if audit != committed_audit:
        raise ValueError("live token audit changed")
    digests = {"model": cross.MODEL,
               "grid_sha256": behavior.FROZEN_GRID_SHA256,
               "source_grid_sha256": metadata["source_grid_sha256"],
               "token_audit_sha256": _sha(json.dumps(audit, sort_keys=True).encode()),
               "behavior_report_sha256": _sha(behavior_path.read_bytes()),
               "code_sha256": _code_digest(),
               "tokenizer_revision": cross.TOKENIZER_REVISION}
    located = {c.id: prior._locate(rlm, c, metadata["question"],
                                   metadata["bridge"]) for c in cells + order_cells}
    for c in cells + order_cells:
        if located[c.id]["prebridge_decoded_token"] != ".":
            raise ValueError(f"period token changed: {c.id}")
    captures, state_fp = capture_states(rlm, cells + order_cells, located, digests)
    repeats = _repeat_drift(rlm, cells, located, captures)
    if max(repeats.values()) > .02:
        raise ValueError(f"state repeat drift exceeds instrument limit: {repeats}")
    vectors, metrics = _vectors(cells, order_cells, captures)
    if any(metrics[c.id]["full_norm"] <= 10 * max(repeats.values()) *
           np.linalg.norm(captures[c.id][0]) for c in cells):
        raise ValueError("source-target state difference is too close to repeat drift")

    behavior_expected = {c.id: behavior._fingerprint(
        c, base.render(rlm, c, metadata["question"]), behavior_report["digests"])
        for c in cells}
    baseline = base._load_cache(behavior.OUT / "behavior_scores.jsonl",
                                behavior_expected, generation=False)
    if len(baseline) != 128:
        raise ValueError("behavior baseline cache incomplete")
    ordered = sorted(cells, key=lambda c: located[c.id]["prompt_length"])
    core_checks = {}
    for label, cell in (("shortest", ordered[0]), ("longest", ordered[-1])):
        loc = located[cell.id]
        ours, _, _ = old.traced_score(rlm, loc["prompt"], cell.candidates,
                                      loc["prebridge_index"])
        core = np.asarray(asserted_remote_patched_logprob(
            rlm, loc["prompt"], list(cell.candidates)), dtype=np.float64)
        error = float(np.max(np.abs(ours - core)))
        if error > .001:
            raise ValueError(f"line-local scorer differs from core: {label}: {error}")
        core_checks[label] = error

    expected = {}
    for cell in cells:
        pair_digests = {**digests,
                        **{kind + "_state_fp": state_fp[which] for kind, which in (
                            ("target", cell.id),
                            ("source", metrics[cell.id]["source_id"]),
                            ("plan", metrics[cell.id]["plan_id"]),
                            ("first_order", metrics[cell.id]["first_order_id"]))}}
        for arm in ARMS:
            expected[f"{cell.id}|{arm}"] = _fp(
                cell, located[cell.id], "score", arm,
                vectors[cell.id][arm], pair_digests)
    path = OUT / "scores.jsonl"
    saved = base._load_cache(path, expected, generation=False)
    for cell in cells:
        key = f"{cell.id}|none"
        if key not in saved:
            loc = located[cell.id]
            scores, _, _ = old.traced_score(rlm, loc["prompt"], cell.candidates,
                                             loc["prebridge_index"])
            row = {"id": key, "fp": expected[key], "scores": scores.tolist(),
                   "flagged": False}
            base._append(path, row)
            saved[key] = row
            print(f"scored {key}", flush=True)
        drift = float(np.max(np.abs(np.asarray(saved[key]["scores"]) -
                                    np.asarray(baseline[cell.id]["scores"]))))
        if drift > .001:
            raise ValueError(f"baseline scorer drift: {cell.id}: {drift}")
        core_checks["all_prompt_max_drift"] = max(
            core_checks.get("all_prompt_max_drift", 0.0), drift)
    first = ordered[0]
    preflight = old._preflight(rlm, first, located[first.id],
                               vectors[first.id]["full"],
                               saved[f"{first.id}|none"]["scores"])
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n")
    print("single-position two-row reach and row-zero refusal passed", flush=True)

    for cell in cells:
        loc = located[cell.id]
        no_patch = saved[f"{cell.id}|none"]["scores"]
        for arm in ARMS[1:]:
            key = f"{cell.id}|{arm}"
            if key in saved:
                continue
            layer = old.LAST_LAYER if arm == "last_block" else old.LAYER
            scores, period_state, flagged = old.traced_score(
                rlm, loc["prompt"], cell.candidates, loc["prebridge_index"],
                patch_layer=layer, patch_vec=vectors[cell.id][arm],
                capture="period" if arm == "full" else "none",
                baseline=no_patch if arm in ACTIVE else None)
            row = {"id": key, "fp": expected[key], "scores": scores.tolist(),
                   "flagged": flagged}
            if arm == "full":
                target_h = captures[cell.id]
                source_h = captures[metrics[cell.id]["source_id"]]
                predicted = (torch.as_tensor(target_h).to(torch.bfloat16) +
                             torch.as_tensor(vectors[cell.id]["full"]).to(
                                 torch.bfloat16)).float().numpy()
                error = float(np.max(np.abs(period_state - predicted)))
                if error > .001 or any(np.array_equal(period_state[i], target_h[i])
                                       for i in range(2)):
                    raise ValueError(f"source patch missed period state: {cell.id}: {error}")
                relative = float(np.linalg.norm(
                    period_state.astype(np.float64) - source_h.astype(np.float64)) /
                    np.linalg.norm(source_h.astype(np.float64)))
                row.update({"period_residual_error": error,
                            "source_state_relative_error": relative})
            if arm in ("zero", "last_block") and float(np.max(
                    np.abs(scores - np.asarray(no_patch)))) > .001:
                raise ValueError(f"identity/pass-through arm moved scores: {key}")
            base._append(path, row)
            saved[key] = row
            print(f"scored {key}", flush=True)
    report = analyze(cells, saved, doc, preflight, core_checks, repeats,
                     metrics, digests, rlm.lib_versions())
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("specific_margin_screen", report["specific_margin_screen"], flush=True)
    print("choice_redirection_screen", report["choice_redirection_screen"], flush=True)


if __name__ == "__main__":
    main()
