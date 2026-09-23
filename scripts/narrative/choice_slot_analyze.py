"""Analyze the frozen route-to-control activation transfer after extraction."""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

import choice_slot_controls as controls
import goal_route_activation_pilot as pilot
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
PRIMARY = pilot.BLOCKS.index(24)
SEED = 20260923


def _unit_interactions(states: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    """[domain,telling,name,order,world,goal,block,hidden] to I_first."""
    raw = (states[..., 0, 0, :, :] - states[..., 0, 1, :, :] -
           states[..., 1, 0, :, :] + states[..., 1, 1, :, :])
    sign = np.array([1.0, -1.0])[None, None, None, :, None, None]
    oriented = raw * sign
    norm = np.linalg.norm(oriented, axis=-1)
    unit = np.divide(oriented, norm[..., None], out=np.zeros_like(oriented),
                     where=norm[..., None] > 0)
    return unit, norm


def _direction(unit: np.ndarray, signs: np.ndarray) -> np.ndarray:
    signed = unit * signs[:, None, None, None, None, None]
    mean = signed.mean(axis=(0, 1, 2, 3))
    norm = np.linalg.norm(mean, axis=-1)
    return np.divide(mean, norm[:, None], out=np.zeros_like(mean),
                     where=norm[:, None] > 0)


def _score(unit: np.ndarray, direction: np.ndarray) -> np.ndarray:
    """Cosine per domain, telling, name, order and block."""
    return np.einsum("dtnolh,lh->dtnol", unit, direction)


def _within(unit: np.ndarray) -> np.ndarray:
    """Opposite-telling leave-domain-out; [domain,telling,block]."""
    n_domain, _, _, _, n_block, _ = unit.shape
    out = np.empty((n_domain, 2, n_block), dtype=np.float64)
    for d in range(n_domain):
        others = [i for i in range(n_domain) if i != d]
        for telling in (0, 1):
            mean = unit[others, 1 - telling].mean(axis=(0, 1, 2))
            norm = np.linalg.norm(mean, axis=-1)
            direction = np.divide(mean, norm[:, None], out=np.zeros_like(mean),
                                  where=norm[:, None] > 0)
            out[d, telling] = _score(unit[d:d + 1, telling:telling + 1],
                                     direction).mean(axis=(0, 1, 2, 3))
    return out


def _bootstrap(values: np.ndarray, *, seed_offset: int) -> list[float]:
    rng = np.random.default_rng(SEED + seed_offset)
    n = len(values)
    boot = values[rng.integers(0, n, size=(10000, n))].mean(axis=1)
    return list(map(float, np.quantile(boot, [.025, .975])))


def analyze(source_h: np.ndarray, targets: dict[str, np.ndarray],
            repeat_diffs: dict[str, np.ndarray], behavior: dict,
            preflight: dict, *, n_random: int = 1000) -> dict:
    source, _ = _unit_interactions(source_h)
    source_direction = _direction(source, np.ones(8))
    route_reference = json.loads(controls.SOURCE.read_text())["transfer_curve"][PRIMARY]
    result = {"block_indices": list(pilot.BLOCKS), "primary_block": 24,
              "source_route_opposite_telling_reference": route_reference,
              "n_source_domains": 8, "arms": ["route_trained", "random_direction",
                                              "source_orientation_null"],
              "all_forwards_unpatched": True, "batteries": {}}
    units = {}
    for bi, (battery, h) in enumerate(targets.items()):
        unit, norms = _unit_interactions(h)
        units[battery] = unit
        drift = np.linalg.norm(repeat_diffs[battery], axis=-1).max(axis=0)
        median_norm = np.median(norms, axis=(0, 1, 2, 3))
        ratio = np.divide(drift, median_norm, out=np.full_like(drift, np.inf),
                          where=median_norm > 0)
        resolved = norms > 10 * drift[None, None, None, None, :]
        readable = bool(np.all(ratio <= .01) and np.all(resolved[..., PRIMARY]))

        cross_scores = _score(unit, source_direction)
        by_domain = cross_scores.mean(axis=(1, 2, 3))
        cross_primary = float(by_domain[:, PRIMARY].mean())
        cross_ci = _bootstrap(by_domain[:, PRIMARY], seed_offset=bi)
        within = _within(unit)
        within_primary = float(within[..., PRIMARY].mean())
        within_domain = within[..., PRIMARY].mean(axis=1)
        within_ci = _bootstrap(within_domain, seed_offset=10 + bi)

        # The identity source assignment is the last exact-null row, and
        # defines observed with the same reduction as every relabelling.
        null = np.array([_score(unit, _direction(source, np.array(signs)))[
            ..., PRIMARY].mean()
            for signs in itertools.product((-1, 1), repeat=8)])
        if not np.isclose(null[-1], cross_primary, atol=1e-12):
            raise ValueError(f"identity orientation disagrees: {battery}")
        rng = np.random.default_rng(SEED + 100 + bi)
        random_arms = []
        for li in range(len(pilot.BLOCKS)):
            directions = rng.standard_normal((n_random, unit.shape[-1]))
            directions /= np.linalg.norm(directions, axis=-1, keepdims=True)
            target_mean = unit[..., li, :].mean(axis=(0, 1, 2, 3))
            random_scores = directions @ target_mean
            random_arms.append({"block": pilot.BLOCKS[li],
                                "q95": float(np.quantile(random_scores, .95)),
                                "mean": float(random_scores.mean()),
                                "route_to_target_percentile": float(np.mean(
                                    random_scores <= cross_scores[..., li].mean())),
                                "within_target_percentile": float(np.mean(
                                    random_scores <= within[..., li].mean()))})
        same_length = (np.asarray(preflight[battery][
            "goal_1_minus_goal_0_tokens_by_quartet"]).reshape(4, 2, 2, 2) == 0)
        length_split = {}
        for label, mask in (("same", same_length), ("changed", ~same_length)):
            length_split[label] = {
                "n_quartets": int(mask.sum()),
                "route_to_target_block24": (float(cross_scores[..., PRIMARY][mask].mean())
                                             if mask.any() else None),
                "within_target_block24": (float(np.broadcast_to(
                    within[..., PRIMARY][:, :, None, None], mask.shape)[mask].mean())
                                          if mask.any() else None)}
        internal_resolved = bool(within_primary >= .05 and within_ci[0] > 0 and
                                 int((within_domain > 0).sum()) >= 3)
        eligible = bool(behavior[battery])
        generic_component = bool(eligible and readable and internal_resolved and
                                 cross_primary >= .5 * within_primary and
                                 float(np.mean(null >= null[-1])) <= .05 and
                                 cross_ci[0] > 0)
        result["batteries"][battery] = {
            "behavior_eligible": eligible, "readable": readable,
            "interaction_norm_median_by_block": median_norm.tolist(),
            "max_repeat_l2_by_block": drift.tolist(),
            "repeat_to_interaction_ratio_by_block": ratio.tolist(),
            "unresolved_interactions_by_block": (~resolved).sum(axis=(0, 1, 2, 3)).tolist(),
            "route_to_target_curve": cross_scores.mean(axis=(0, 1, 2, 3)).tolist(),
            "route_to_target_primary": cross_primary,
            "route_to_target_domain_block24": by_domain[:, PRIMARY].tolist(),
            "route_to_target_by_telling_block24": cross_scores[..., PRIMARY].mean(axis=(0, 2, 3)).tolist(),
            "route_to_target_by_name_block24": cross_scores[..., PRIMARY].mean(axis=(0, 1, 3)).tolist(),
            "route_to_target_by_order_block24": cross_scores[..., PRIMARY].mean(axis=(0, 1, 2)).tolist(),
            "route_to_target_block16_24_mean": float(cross_scores[..., list(pilot.PRIMARY)].mean()),
            "route_to_target_domain_bootstrap_ci95": cross_ci,
            "source_orientation_null": {
                "draws": len(null), "mean": float(null.mean()),
                "q95": float(np.quantile(null, .95)),
                "p_ge_observed": float(np.mean(null >= null[-1]))},
            "random_directions": {"draws_per_block": n_random,
                                  "calibration": random_arms},
            "within_target_curve": within.mean(axis=(0, 1)).tolist(),
            "within_target_primary": within_primary,
            "within_target_domain_block24": within_domain.tolist(),
            "within_target_by_telling_block24": within[..., PRIMARY].mean(axis=0).tolist(),
            "within_target_domain_bootstrap_ci95": within_ci,
            "within_target_resolved": internal_resolved,
            "generic_component_gate": generic_component,
            "same_goal_token_length_fraction": preflight[battery][
                "same_goal_token_length_fraction"],
            "goal_length_split": length_split}

    # Independent reverse projection: the four property domains fit a
    # direction without any route data, then score every source route domain.
    prop_direction = _direction(units["property"], np.ones(4))
    reverse = _score(source, prop_direction)
    result["property_to_route"] = {
        "curve": reverse.mean(axis=(0, 1, 2, 3)).tolist(),
        "primary": float(reverse[..., PRIMARY].mean()),
        "domain_block24": reverse[..., PRIMARY].mean(axis=(1, 2, 3)).tolist()}
    prop = result["batteries"]["property"]
    if prop["generic_component_gate"]:
        reading = "generic_answer_slot_compatible"
    elif not (prop["behavior_eligible"] and prop["readable"] and
              prop["within_target_resolved"]):
        reading = "property_battery_cannot_adjudicate"
    elif prop["route_to_target_primary"] < .5 * prop["within_target_primary"]:
        reading = "task_dependent_code"
    else:
        reading = "mixed_or_partial"
    result["registered_reading"] = reading
    return result


def main() -> None:
    from lsx.core.remote import RemoteLM

    extraction_path = controls.OUT / "extraction_report.json"
    extraction_bytes = extraction_path.read_bytes()
    extraction = json.loads(extraction_bytes)
    direct, stories, route_doc, _, source_report = controls._source_and_direct()
    prop, prop_doc, _ = controls.make_property_cells()
    if extraction["digests"]["extraction_code_sha256"] != controls._digest():
        raise ValueError("target extraction code changed")
    rlm = RemoteLM(cross.MODEL)
    hidden = int(rlm.model.config.hidden_size)
    source = []
    for cell in stories:
        fp = pilot._fp(cell, controls._render(rlm, cell, route_doc["question"]),
                       source_report["digests"])
        arr = pilot._load(cell, fp, hidden)
        if arr is None:
            raise ValueError(f"missing source state: {cell.id}")
        source.append(arr)
    source_h = np.stack(source).reshape(8, 2, 2, 2, 2, 2,
                                        len(pilot.BLOCKS), hidden).astype(np.float64)
    targets, repeat_diffs = {}, {}
    for battery, cells, question in (("direct", direct, route_doc["question"]),
                                     ("property", prop, prop_doc["question"])):
        repeats = controls._repeats(cells, battery)
        arrays = {}
        for cell in cells + repeats:
            fp = controls._fp(cell, controls._render(rlm, cell, question),
                              question, extraction["digests"], kind="activation")
            arr = controls._load(cell, fp, hidden)
            if arr is None:
                raise ValueError(f"missing target state: {cell.id}")
            arrays[cell.id] = arr
        targets[battery] = np.stack([arrays[c.id] for c in cells]).reshape(
            4, 2, 2, 2, 2, 2, len(pilot.BLOCKS), hidden).astype(np.float64)
        repeat_diffs[battery] = np.stack([
            arrays[rep.id] - arrays[cells[di * 32].id]
            for di, rep in enumerate(repeats)]).astype(np.float64)
    report = analyze(source_h, targets, repeat_diffs,
                     {"direct": extraction["direct_behavior_joint_success"] == 32,
                      "property": extraction["property_behavior"]["gate_pass"]},
                     extraction["token_preflight"])
    report.update({"model_checkpoint": cross.MODEL,
                   "deployment_weight_revision": None,
                   "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
                   "source_pilot_sha256": extraction["source_pilot_sha256"],
                   "target_extraction_report_sha256": hashlib.sha256(extraction_bytes).hexdigest(),
                   "target_extraction_digests": extraction["digests"],
                   "analysis_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                   "versions": extraction["versions"],
                   "target_core_equivalence": extraction["extraction"],
                   "target_behavior": extraction["property_behavior"],
                   "token_preflight": extraction["token_preflight"]})
    path = controls.OUT / "report.json"
    path.write_text(json.dumps(report, indent=2) + "\n")
    print("reading", report["registered_reading"])
    print("direct", report["batteries"]["direct"]["route_to_target_primary"])
    print("property", report["batteries"]["property"]["route_to_target_primary"])
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
