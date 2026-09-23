"""Frozen double-flip period patch; see firsthop_doubleflip_prereg.md."""
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
import firsthop_swap_patch as previous
import goal_route_cross as cross
import prequestion_route_extract as prior
import story_fact_token_patch as patch


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cache/firsthop_swap/v1/doubleflip"
OLD_REPORT = ROOT / "research/narrative/results/firsthop_swap_patch_v1_summary.json"
OLD_SHA = "914152d540c625a2caf2733bca8b368720b13f157e27008bcd4015d9b99e21cd"
ARMS = ("none", "zero", "world_natural", "plan_matched", "double_natural",
        "double_matched", "random", "last_block")
ACTIVE = ("world_natural", "plan_matched", "double_natural",
          "double_matched", "random")
SEED = 20260924


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _code_digest() -> str:
    paths = (Path(__file__), Path(previous.__file__), Path(grid.__file__),
             Path(behavior.__file__), Path(patch.__file__), Path(prior.__file__),
             Path(base.__file__), ROOT / "src/lsx/core/remote.py",
             ROOT / "src/lsx/core/checks.py", ROOT / "src/lsx/ndif.py")
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _load_old_report() -> dict:
    if _sha(OLD_REPORT.read_bytes()) != OLD_SHA:
        raise ValueError("committed prior report hash changed")
    report = json.loads(OLD_REPORT.read_text())
    if (report["n_target_prompts"] != 128 or report["n_score_jobs"] != 896 or
            report["digests"]["grid_sha256"] != behavior.FROZEN_GRID_SHA256 or
            report["digests"]["code_sha256"] != previous._code_digest() or
            report["model_checkpoint"] != cross.MODEL or
            report["digests"]["tokenizer_revision"] != cross.TOKENIZER_REVISION):
        raise ValueError("prior report does not match frozen code and model")
    if not all(report["gate_components"][name] for name in (
            "core_scorer_equivalence", "row_zero_negative_refused",
            "zero_identity", "last_block_pass_through",
            "repeat_drift_at_most_0_02", "source_state_match_at_most_0_02",
            "flag_fraction_at_most_0_05")):
        raise ValueError("prior report instrument gates failed")
    return report


def _by_factors(cells: list[cross.Cell]) -> dict[tuple, cross.Cell]:
    result = {(c.domain, c.name_order, c.plan_order, c.world, c.goal): c
              for c in cells}
    if len(cells) != 128 or len(result) != 128:
        raise ValueError("first-hop factor grid changed")
    return result


def _sources(cell: cross.Cell, by: dict) -> tuple[cross.Cell, cross.Cell, cross.Cell]:
    domain, name, plan, world, goal = (cell.domain, cell.name_order,
                                       cell.plan_order, cell.world, cell.goal)
    return (by[domain, name, plan, 1 - world, goal],
            by[domain, name, 1 - plan, world, goal],
            by[domain, name, 1 - plan, 1 - world, goal])


def _first_wins(cell: cross.Cell, row: dict) -> bool:
    winner = grid._winner(cell, row)
    a_first = cell.plan_order == 0
    return (winner == cell.plan_a_name) == a_first


def _validate_pair(c: cross.Cell, world: cross.Cell, plan: cross.Cell,
                   double: cross.Cell, row: dict, located: dict) -> int:
    target_winner = grid._winner(c, row)
    world_winner = grid._winner(world, row)
    plan_winner = grid._winner(plan, row)
    double_winner = grid._winner(double, row)
    if not (target_winner == plan_winner and world_winner == double_winner and
            target_winner != world_winner and
            _first_wins(c, row) == _first_wins(double, row) and
            _first_wins(c, row) != _first_wins(world, row) and
            _first_wins(c, row) != _first_wins(plan, row)):
        raise ValueError(f"double-flip winner/slot truth table failed: {c.id}")
    if (world.candidates != c.candidates or plan.candidates != c.candidates or
            double.candidates != c.candidates or
            any(located[x.id][key] != located[c.id][key]
                for x in (world, plan, double)
                for key in ("prompt_length", "prebridge_index", "prebridge_token_id"))):
        raise ValueError(f"source pair token signature changed: {c.id}")
    return 1 if world_winner == c.plan_a_name else -1


def _load_states(rlm, cells: list[cross.Cell], order_cells: list[cross.Cell],
                 located: dict, old_report: dict) -> dict[str, np.ndarray]:
    """Refuse any copied state whose recipe or content differs from the old report."""
    hidden = int(rlm.model.config.hidden_size)
    states = {}
    for c, order in zip(cells, order_cells):
        expected = old_report["pair_metrics"][c.id]
        for current, sha_key in ((c, "target_state_sha256"),
                                 (order, "first_order_state_sha256")):
            fp = previous._fp(current, located[current.id], "state", None,
                              None, old_report["digests"])
            arr = previous._state(current, fp, hidden)
            if arr is None or _sha(arr.tobytes()) != expected[sha_key]:
                raise ValueError(f"copied state differs from old report: {current.id}")
            states[current.id] = arr
    if len(states) != 256:
        raise ValueError("wrong copied state count")
    return states


def _vectors(cells: list[cross.Cell], states: dict,
             located: dict, old_report: dict, domain_rows: dict) -> tuple[dict, dict]:
    by = _by_factors(cells)
    vectors, metadata = {}, {}
    for di, c in enumerate(cells):
        world, plan, double = _sources(c, by)
        row = domain_rows[c.domain]
        sign = _validate_pair(c, world, plan, double, row, located)
        target_h = states[c.id][0].astype(np.float64)
        world_h = states[world.id][0].astype(np.float64)
        plan_h = states[plan.id][0].astype(np.float64)
        double_h = states[double.id][0].astype(np.float64)
        world_delta = world_h - target_h
        plan_delta = plan_h - target_h
        double_delta = double_h - target_h
        world_norm = float(np.linalg.norm(world_delta))
        double_norm = float(np.linalg.norm(double_delta))
        if (not np.isfinite(world_norm) or not np.isfinite(double_norm) or
                min(world_norm, double_norm) <= 0):
            raise ValueError(f"invalid source-state norm: {c.id}")
        seed = (SEED + (di // 16) * 16 + c.name_order * 8 +
                c.plan_order * 4 + c.goal * 2 + c.world)
        rng = np.random.default_rng(seed)
        vectors[c.id] = {
            "none": None,
            "zero": np.zeros_like(target_h, dtype=np.float32),
            "world_natural": np.asarray(world_delta, dtype=np.float32),
            "plan_matched": patch._unit_scaled(plan_delta, world_norm),
            "double_natural": np.asarray(double_delta, dtype=np.float32),
            "double_matched": patch._unit_scaled(double_delta, world_norm),
            "random": patch._unit_scaled(rng.standard_normal(len(target_h)), world_norm),
            "last_block": np.asarray(double_delta, dtype=np.float32),
        }
        old = old_report["pair_metrics"][c.id]
        if (old["source_id"] != world.id or old["plan_id"] != plan.id or
                not np.isclose(old["full_norm"], world_norm, rtol=0, atol=1e-9) or
                not np.isclose(old["plan_norm"], np.linalg.norm(plan_delta),
                               rtol=0, atol=1e-9)):
            raise ValueError(f"old vector geometry differs: {c.id}")
        metadata[c.id] = {
            "source_sign": sign, "world_id": world.id,
            "plan_id": plan.id, "double_id": double.id,
            "world_norm": world_norm, "plan_norm": float(np.linalg.norm(plan_delta)),
            "double_norm": double_norm,
            "target_state_sha256": _sha(states[c.id].tobytes()),
            "world_state_sha256": _sha(states[world.id].tobytes()),
            "plan_state_sha256": _sha(states[plan.id].tobytes()),
            "double_state_sha256": _sha(states[double.id].tobytes()),
        }
        if any(v is not None and (v.shape != target_h.shape or
                                  not np.isfinite(v).all())
               for v in vectors[c.id].values()):
            raise ValueError(f"invalid vector: {c.id}")
    return vectors, metadata


def _old_effects(cells: list[cross.Cell], old_report: dict,
                 metadata: dict) -> dict[str, np.ndarray]:
    old_arms = previous.ARMS
    scores = np.asarray(old_report["candidate_scores"], dtype=np.float64)
    if scores.shape != (8, 2, 2, 2, 2, len(old_arms), 2):
        raise ValueError("old score shape changed")
    a = np.asarray([c.candidates.index(c.plan_a_name) for c in cells],
                   dtype=np.int64).reshape(8, 2, 2, 2, 2)
    m = np.take_along_axis(scores, a[..., None, None], axis=-1)[..., 0] - \
        np.take_along_axis(scores, (1-a)[..., None, None], axis=-1)[..., 0]
    sign = np.asarray([metadata[c.id]["source_sign"] for c in cells],
                      dtype=np.float64).reshape(8, 2, 2, 2, 2)
    effects = {}
    for arm in ("full", "plan_matched", "first_order_matched", "random"):
        e = sign * (m[..., old_arms.index(arm)] - m[..., 0])
        prior_effect = np.asarray(old_report["signed_effects"][arm], dtype=np.float64)
        if (not np.array_equal(e, prior_effect) or
                not np.isclose(e.mean(), old_report["arm_effects"][arm]["mean"],
                               atol=1e-12, rtol=0) or
                not np.allclose(e.mean(axis=(1,2,3,4)),
                                old_report["arm_effects"][arm]["domain_effects"],
                                atol=1e-12, rtol=0)):
            raise ValueError(f"old signed effect failed independent reconstruction: {arm}")
        effects[arm] = e
    return effects


def _score_arrays(cells: list[cross.Cell], rows: dict,
                  metadata: dict) -> tuple[np.ndarray, np.ndarray, dict]:
    scores = np.asarray([[rows[f"{c.id}|{arm}"]["scores"] for arm in ARMS]
                         for c in cells], dtype=np.float64).reshape(
                             8, 2, 2, 2, 2, len(ARMS), 2)
    a = np.asarray([c.candidates.index(c.plan_a_name) for c in cells],
                   dtype=np.int64).reshape(8, 2, 2, 2, 2)
    m = np.take_along_axis(scores, a[..., None, None], axis=-1)[..., 0] - \
        np.take_along_axis(scores, (1-a)[..., None, None], axis=-1)[..., 0]
    sign = np.asarray([metadata[c.id]["source_sign"] for c in cells],
                      dtype=np.float64).reshape(8, 2, 2, 2, 2)
    effects = {arm: sign * (m[..., i] - m[..., 0])
               for i, arm in enumerate(ARMS) if i}
    return scores, sign[..., None] * m, effects


def _positive(report: dict) -> bool:
    return bool(report["mean"] >= .25 and
                report["exact_null"]["p_ge_observed"] <= .05 and
                report["domain_bootstrap"]["ci95"][0] > 0 and
                report["positive_domains"] >= 6)


def _analysis(cells: list[cross.Cell], rows: dict, metadata: dict,
              old_report: dict, repeat_drift: dict, preflight: dict,
              core_checks: dict, digests: dict, versions: dict) -> dict:
    scores, signed_margin, effects = _score_arrays(cells, rows, metadata)
    old_effects = _old_effects(cells, old_report, metadata)
    arm_reports = {arm: patch._effect_report(e, seed=SEED + i + 1)
                   for i, (arm, e) in enumerate(effects.items())}
    double_n = arm_reports["double_natural"]
    double_m = arm_reports["double_matched"]
    contrasts = {
        "world_minus_double": patch._effect_report(
            effects["world_natural"] - effects["double_matched"], seed=SEED + 20),
        "plan_minus_double": patch._effect_report(
            effects["plan_matched"] - effects["double_matched"], seed=SEED + 21),
    }
    zero_diff = float(np.max(np.abs(scores[..., ARMS.index("zero"), :] - scores[..., 0, :])))
    last_diff = float(np.max(np.abs(scores[..., ARMS.index("last_block"), :] - scores[..., 0, :])))
    flags = {arm: sum(bool(rows[f"{c.id}|{arm}"].get("flagged")) for c in cells)
             for arm in ACTIVE}
    flag_fraction = sum(flags.values()) / (128 * len(ACTIVE))
    source_error = max(float(rows[f"{c.id}|double_natural"]["source_state_relative_error"])
                       for c in cells)
    reached = max(float(rows[f"{c.id}|{arm}"].get("period_residual_error", 0))
                  for c in cells for arm in ("double_natural", "double_matched"))
    instrument = {
        "core_equivalence": max(core_checks.values()) <= .001,
        "row_zero_only_refused": bool(preflight["row_zero_only_refused"]),
        "two_row_reach": preflight["block24_residual_error"] <= .001,
        "zero_identity": zero_diff <= .001,
        "last_block_pass_through": last_diff <= .001,
        "repeat_drift": max(repeat_drift.values()) <= .02,
        "double_source_match": source_error <= .02,
        "bf16_patch_arithmetic": reached <= .001,
        "flag_fraction": flag_fraction <= .05,
    }
    instrument_ok = all(instrument.values())

    def equivalent(r: dict) -> bool:
        lo, hi = r["domain_bootstrap"]["ci95"]
        return abs(r["mean"]) <= .15 and lo > -.40 and hi < .40

    slot_gate = {"instrument_ok": instrument_ok,
                 "natural_equivalence": equivalent(double_n),
                 "matched_equivalence": equivalent(double_m),
                 "world_contrast": _positive(contrasts["world_minus_double"]),
                 "plan_contrast": _positive(contrasts["plan_minus_double"])}
    positive_gate = {"instrument_ok": instrument_ok,
                     "natural_positive": _positive(double_n),
                     "matched_positive": _positive(double_m)}
    if all(slot_gate.values()):
        verdict = "slot_cancellation_screen_pass"
    elif all(positive_gate.values()):
        verdict = "cancellation_fails_positive_double"
    elif instrument_ok and any(
            r["mean"] <= -.15 or r["domain_bootstrap"]["ci95"][1] < 0
            for r in (double_n, double_m)):
        verdict = "cancellation_fails_negative_double"
    elif instrument_ok:
        verdict = "mixed_or_unresolved"
    else:
        verdict = "unreadable_instrument"

    prior_scores = np.asarray(old_report["candidate_scores"], dtype=np.float64)
    prior_baseline = prior_scores[..., previous.ARMS.index("none"), :]
    replication = {
        "none_max_candidate_difference": float(np.max(abs(scores[..., 0, :] - prior_baseline))),
        "world_mean_old": float(old_effects["full"].mean()),
        "world_mean_new": float(effects["world_natural"].mean()),
        "plan_mean_old": float(old_effects["plan_matched"].mean()),
        "plan_mean_new": float(effects["plan_matched"].mean()),
        "world_max_cell_effect_difference": float(np.max(abs(
            effects["world_natural"] - old_effects["full"]))),
        "plan_max_cell_effect_difference": float(np.max(abs(
            effects["plan_matched"] - old_effects["plan_matched"]))),
    }
    before = signed_margin[..., 0]
    choice = {}
    for arm in ("double_natural", "double_matched"):
        after = signed_margin[..., ARMS.index(arm)]
        choice[arm] = {
            "source_winner_before": int((before > 0).sum()),
            "source_winner_after": int((after > 0).sum()),
            "flips_toward_source": int(((before <= 0) & (after > 0)).sum()),
            "flips_away_from_source": int(((before > 0) & (after <= 0)).sum()),
            "absolute_margin_shrinks": int((abs(after) < abs(before)).sum()),
            "effect_when_source_already_favoured": float(
                effects[arm][before > 0].mean()) if (before > 0).any() else None,
        }
    pair_means = {arm: e.mean(axis=3).tolist() for arm, e in effects.items()}
    factor_halves = {arm: {
        "name": [float(e[:, i].mean()) for i in (0, 1)],
        "plan": [float(e[:, :, i].mean()) for i in (0, 1)],
        "world": [float(e[:, :, :, i].mean()) for i in (0, 1)],
        "goal": [float(e[..., i].mean()) for i in (0, 1)],
    } for arm, e in effects.items()}
    leave_one_out = {arm: [float(np.delete(e.mean(axis=(1,2,3,4)), i).mean())
                           for i in range(8)]
                     for arm, e in effects.items() if arm.startswith("double_")}
    return {
        "verdict": verdict, "slot_cancellation_gate": slot_gate,
        "positive_double_gate": positive_gate, "instrument_gates": instrument,
        "arm_reports": arm_reports, "paired_contrasts": contrasts,
        "old_arm_reports": {arm: old_report["arm_effects"][arm]
                            for arm in ("full", "plan_matched", "first_order_matched", "random")},
        "replication": replication, "choice": choice,
        "signed_effects": {arm: e.tolist() for arm, e in effects.items()},
        "candidate_scores": scores.tolist(), "unordered_world_pair_means": pair_means,
        "factor_halves": factor_halves, "double_leave_one_domain_out_means": leave_one_out,
        "flag_counts": flags, "flag_fraction": flag_fraction,
        "max_zero_candidate_difference": zero_diff,
        "max_last_block_candidate_difference": last_diff,
        "max_source_state_relative_error": source_error,
        "max_patch_arithmetic_error": reached,
        "repeat_relative_drift_by_domain": repeat_drift,
        "preflight": preflight, "core_equivalence": core_checks,
        "pair_metadata": metadata, "model_checkpoint": cross.MODEL,
        "deployment_weight_revision": None,
        "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
        "versions": versions, "digests": digests,
        "n_target_prompts": len(cells), "n_score_jobs": len(cells) * len(ARMS),
        "n_reused_state_captures": 256, "n_repeat_state_jobs": 8,
    }


def main() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob
    import torch

    old_report = _load_old_report()
    if (_sha(grid.GRID.read_bytes()) != behavior.FROZEN_GRID_SHA256 or
            json.loads(grid.GRID.read_text()) != grid.snapshot()):
        raise ValueError("first-hop grid changed")
    cells, order_cells, grid_metadata = grid.make_cells()
    by = _by_factors(cells)
    doc = json.loads(cross.GRID.read_text())
    domain_rows = {row["id"]: row for row in doc["domains"]}
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("tokenizer revision changed")
    audit = grid.token_audit(rlm.tok)
    committed_audit = json.loads((ROOT / "research/narrative/results/firsthop_swap_v1_token_audit.json").read_text())
    if audit != committed_audit:
        raise ValueError("token audit changed")
    located = {c.id: prior._locate(rlm, c, grid_metadata["question"],
                                    grid_metadata["bridge"]) for c in cells + order_cells}
    states = _load_states(rlm, cells, order_cells, located, old_report)
    vectors, metadata = _vectors(cells, states, located, old_report, domain_rows)
    _old_effects(cells, old_report, metadata)
    repeat_drift = previous._repeat_drift(rlm, cells, located, states)
    max_drift = max(repeat_drift.values())
    if max_drift > .02:
        raise ValueError(f"repeat-state drift exceeds 0.02: {max_drift}")
    if any(metadata[c.id]["double_norm"] <= 10 * max_drift *
           np.linalg.norm(states[c.id][0]) for c in cells):
        raise ValueError("double state difference indistinguishable from repeat drift")
    print("verified 256 old states and 8 repeat captures", flush=True)

    ordered = sorted(cells, key=lambda c: located[c.id]["prompt_length"])
    core_checks = {}
    for label, c in (("shortest", ordered[0]), ("longest", ordered[-1])):
        loc = located[c.id]
        ours, _, _ = patch.traced_score(rlm, loc["prompt"], c.candidates,
                                        loc["prebridge_index"])
        core = np.asarray(asserted_remote_patched_logprob(
            rlm, loc["prompt"], list(c.candidates)), dtype=np.float64)
        error = float(np.max(abs(ours - core)))
        if error > .001:
            raise ValueError(f"scorer differs from core: {label}: {error}")
        core_checks[label] = error

    digests = {"grid_sha256": behavior.FROZEN_GRID_SHA256,
               "old_report_sha256": OLD_SHA,
               "token_audit_sha256": _sha(json.dumps(audit, sort_keys=True).encode()),
               "tokenizer_revision": cross.TOKENIZER_REVISION,
               "code_sha256": _code_digest(), "model": cross.MODEL}
    expected = {}
    for c in cells:
        pair = metadata[c.id]
        pair_digests = {**digests, **{k: v for k, v in pair.items()
                                     if k.endswith("_state_sha256")}}
        for arm in ARMS:
            expected[f"{c.id}|{arm}"] = previous._fp(
                c, located[c.id], "score", arm, vectors[c.id][arm], pair_digests)
    path = OUT / "scores.jsonl"
    saved = base._load_cache(path, expected, generation=False)
    old_scores = np.asarray(old_report["candidate_scores"], dtype=np.float64)
    for i, c in enumerate(cells):
        key = f"{c.id}|none"
        if key not in saved:
            loc = located[c.id]
            scores, _, _ = patch.traced_score(rlm, loc["prompt"], c.candidates,
                                               loc["prebridge_index"])
            row = {"id": key, "fp": expected[key], "scores": scores.tolist(),
                   "flagged": False}
            base._append(path, row)
            saved[key] = row
            print(f"scored {key}", flush=True)
        old_base = old_scores.reshape(128, len(previous.ARMS), 2)[i, 0]
        delta = float(np.max(abs(np.asarray(saved[key]["scores"]) - old_base)))
        if delta > .001:
            raise ValueError(f"new no-patch disagrees with prior report: {c.id}: {delta}")
        core_checks["all_prompt_baseline_drift"] = max(
            core_checks.get("all_prompt_baseline_drift", 0.0), delta)
    first = ordered[0]
    preflight = patch._preflight(rlm, first, located[first.id],
                                 vectors[first.id]["double_natural"],
                                 saved[f"{first.id}|none"]["scores"])
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n")
    print("row-zero refusal and double-vector two-row reach passed", flush=True)

    for c in cells:
        loc = located[c.id]
        base_scores = saved[f"{c.id}|none"]["scores"]
        for arm in ARMS[1:]:
            key = f"{c.id}|{arm}"
            if key in saved:
                continue
            layer = patch.LAST_LAYER if arm == "last_block" else patch.LAYER
            capture = "period" if arm in ("double_natural", "double_matched") else "none"
            scores, period_state, flagged = patch.traced_score(
                rlm, loc["prompt"], c.candidates, loc["prebridge_index"],
                patch_layer=layer, patch_vec=vectors[c.id][arm], capture=capture,
                baseline=base_scores if arm in ACTIVE else None)
            row = {"id": key, "fp": expected[key], "scores": scores.tolist(),
                   "flagged": flagged}
            if capture == "period":
                target = states[c.id]
                v = vectors[c.id][arm]
                predicted = (torch.as_tensor(target).to(torch.bfloat16) +
                             torch.as_tensor(v).to(torch.bfloat16)).float().numpy()
                error = float(np.max(abs(period_state - predicted)))
                if error > .001 or any(np.array_equal(period_state[j], target[j])
                                       for j in range(2)):
                    raise ValueError(f"double patch missed period state: {key}: {error}")
                row["period_residual_error"] = error
                if arm == "double_natural":
                    source = states[metadata[c.id]["double_id"]]
                    row["source_state_relative_error"] = float(np.linalg.norm(
                        period_state.astype(np.float64) - source.astype(np.float64)) /
                        np.linalg.norm(source.astype(np.float64)))
            if arm in ("zero", "last_block") and float(np.max(abs(
                    scores - np.asarray(base_scores)))) > .001:
                raise ValueError(f"zero/pass-through score moved: {key}")
            base._append(path, row)
            saved[key] = row
            print(f"scored {key}", flush=True)
    report = _analysis(cells, saved, metadata, old_report, repeat_drift,
                       preflight, core_checks, digests, rlm.lib_versions())
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("verdict", report["verdict"], flush=True)


if __name__ == "__main__":
    main()
