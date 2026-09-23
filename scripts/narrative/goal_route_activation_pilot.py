"""Final-token residual pilot for the frozen goal × route crossing."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import itertools
import json
import os
from pathlib import Path
import time

import numpy as np

import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cache/goal_route_cross/activation_v1"
BLOCKS = (0, 8, 16, 24, 32, 40)
PRIMARY = (BLOCKS.index(16), BLOCKS.index(24))
SEED = 20260923
CODE_FILES = (Path(__file__), Path(cross.__file__), Path(cross.base.__file__),
              *cross.base.CORE_FILES)


def _digest() -> str:
    h = hashlib.sha256()
    for path in CODE_FILES:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _check_behavior_gate() -> dict:
    path = cross.OUT / "report.json"
    if not path.exists():
        raise ValueError("crossed behavioral report missing")
    report = json.loads(path.read_text())
    _, _, _, _, _, digests = cross.make_cells()
    if report.get("digests") != digests or not report.get("gate_pass"):
        raise ValueError("crossed behavioral gate or provenance failed")
    return report


def _cells() -> tuple[list[cross.Cell], list[cross.Cell], dict, dict]:
    _, stories, _, _, doc, crossed = cross.make_cells()
    repeats = [replace(stories[di * 32], id=f"activation_repeat:{di:02d}",
                       stage="activation_repeat") for di in range(8)]
    digests = {"grid_sha256": crossed["grid_sha256"],
               "behavior_code_sha256": crossed["code_sha256"],
               "activation_code_sha256": _digest(),
               "tokenizer_revision": cross.TOKENIZER_REVISION,
               "block_indices": list(BLOCKS)}
    return stories, repeats, doc, digests


def _fp(cell: cross.Cell, prompt: str, digests: dict) -> str:
    body = {"id": cell.id, "prompt": prompt, "model": cross.MODEL, **digests}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _path(cell: cross.Cell) -> Path:
    return OUT / "states" / (hashlib.sha256(cell.id.encode()).hexdigest() + ".npz")


def _load(cell: cross.Cell, expected_fp: str, hidden: int) -> np.ndarray | None:
    path = _path(cell)
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        if z["id"].item() != cell.id or z["fp"].item() != expected_fp:
            raise ValueError(f"stale activation cache: {cell.id}")
        arr = np.array(z["vec"], dtype=np.float32)
    if arr.shape != (len(BLOCKS), hidden) or not np.isfinite(arr).all():
        raise ValueError(f"bad activation cache shape or values: {cell.id}")
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


def _validate_final_tokens(rlm, cells: list[cross.Cell], question: str) -> None:
    from lsx.core.remote import strip_template_bos

    tok = rlm.tok
    for i in range(0, len(cells), 4):
        four = cells[i:i + 4]
        ids = [tok(strip_template_bos(tok, cross.base.render(rlm, c, question)),
                   add_special_tokens=True)["input_ids"] for c in four]
        if len({tuple(x[-1:]) for x in ids}) != 1:
            raise ValueError(f"four-cell final token differs: {four[0].id}")
        if len({c.user_text[-200:] for c in four}) != 1:
            raise ValueError(f"four-cell final text differs: {four[0].id}")


def _goal_length_deltas(rlm, stories: list[cross.Cell], question: str) -> list[int]:
    from lsx.core.remote import strip_template_bos

    tok = rlm.tok
    out = []
    for di in range(8):
        pair = stories[di * 32:di * 32 + 2]
        lengths = [len(tok(strip_template_bos(tok, cross.base.render(rlm, c, question)),
                           add_special_tokens=True)["input_ids"]) for c in pair]
        out.append(lengths[1] - lengths[0])
    if out != [0, 0, 1, 0, 1, -1, 0, 0]:
        raise ValueError(f"frozen goal-token length audit changed: {out}")
    return out


def _extract_one(rlm, prompt: str) -> np.ndarray:
    import torch
    from lsx.core.remote import _encode, assert_single_bos

    ids, mask = _encode(rlm, [prompt])
    assert_single_bos(ids, mask, getattr(rlm.tok, "bos_token_id", None))
    if int(mask[0, -1]) != 1:
        raise ValueError("last position is padding")
    blocks = rlm.blocks
    model = rlm.model
    hidden = int(model.config.hidden_size)

    def build(backend):
        with model.trace({"input_ids": ids, "attention_mask": mask},
                         backend=backend) as tracer:
            parts = []
            for bi in BLOCKS:
                o = blocks[bi].output
                h = o if isinstance(o, torch.Tensor) else o[0]
                parts.append(h[:, -1, :].float().reshape(-1, hidden)[-1].cpu())
            out = torch.stack(parts).save()
        return tracer

    for attempt in range(12):
        try:
            arr = np.asarray(rlm._run(build), dtype=np.float32)
            if arr.shape != (len(BLOCKS), hidden) or not np.isfinite(arr).all():
                raise ValueError(f"remote final state has shape {arr.shape}")
            return arr
        except Exception as exc:
            transient = any(term in str(exc).lower() for term in (
                "out of memory", "503 service unavailable", "502 bad gateway",
                "429 too many requests", "deployment unavailable",
                "not complete after", "timed out"))
            if not transient or attempt == 11:
                raise
            time.sleep(20)
    raise AssertionError("unreachable")


def _equivalence(rlm, cell: cross.Cell, extracted: np.ndarray, question: str) -> dict:
    from lsx.core.remote import remote_residuals

    prompt = cross.base.render(rlm, cell, question)
    rows = []
    for bi in (16, 24):
        full = remote_residuals(rlm, [prompt], bi)
        ref = np.asarray(full[0, -1], dtype=np.float32)
        got = extracted[BLOCKS.index(bi)]
        cos = float(np.dot(ref, got) /
                    (np.linalg.norm(ref) * np.linalg.norm(got)))
        rel = float(np.linalg.norm(ref - got) / np.linalg.norm(ref))
        rows.append({"block": bi, "cosine": cos, "relative_l2_error": rel})
        if cos < .999 or rel > .01:
            raise ValueError(f"final-token extractor differs from core at block {bi}")
    return {"prompt_id": cell.id, "checks": rows}


def _surface_nulls(stories: list[cross.Cell]) -> dict:
    max_bag, max_local = 0, 0
    for i in range(0, len(stories), 4):
        four = stories[i:i + 4]
        for texts, which in (([c.user_text for c in four], "bag"),
                             ([c.user_text[-200:] for c in four], "local")):
            bags = [cross.base._words(t) for t in texts]
            words = set().union(*(set(b) for b in bags))
            delta = max((abs(bags[0][w] - bags[1][w] - bags[2][w] + bags[3][w])
                         for w in words), default=0)
            if which == "bag":
                max_bag = max(max_bag, delta)
            else:
                max_local = max(max_local, delta)
    if max_bag or max_local:
        raise ValueError("surface interaction was not zero")
    return {"max_abs_full_bag_interaction": max_bag,
            "max_abs_last_200_char_bag_interaction": max_local}


def _transfer(domain_means: np.ndarray, signs: np.ndarray) -> np.ndarray:
    """Leave-domain-out, train on the opposite telling; [domain,telling,block]."""
    signed = domain_means * signs[:, None, None, None]
    out = np.empty(signed.shape[:3], dtype=np.float64)
    for d in range(8):
        train_domains = [e for e in range(8) if e != d]
        for t in (0, 1):
            for li in range(len(BLOCKS)):
                direction = signed[train_domains, 1 - t, li].mean(axis=0)
                norm = np.linalg.norm(direction)
                out[d, t, li] = (np.dot(signed[d, t, li], direction / norm)
                                  if norm > 0 else 0.0)
    return out


def _orientation_null(domain_means: np.ndarray) -> np.ndarray:
    # Match the observed reduction exactly, including summation order.
    return np.array([_transfer(domain_means, np.array(signs))[
        ..., list(PRIMARY)].mean()
        for signs in itertools.product((-1, 1), repeat=8)])


def analyze(stories: list[cross.Cell], repeats: list[cross.Cell], saved: dict,
            *, n_boot: int = 10000, n_random: int = 1000) -> dict:
    hidden = next(iter(saved.values())).shape[-1]
    h = np.stack([saved[c.id] for c in stories]).reshape(
        8, 2, 2, 2, 2, 2, len(BLOCKS), hidden).astype(np.float64)
    raw_interaction = (h[..., 0, 0, :, :] - h[..., 0, 1, :, :] -
                       h[..., 1, 0, :, :] + h[..., 1, 1, :, :])
    # [domain,telling,name,plan,block,hidden]. The A-owner has no shared
    # cross-domain identity; orient to the first-listed plan's owner.
    plan_sign = np.array([1.0, -1.0])[None, None, None, :, None, None]
    interaction = raw_interaction * plan_sign
    norms = np.linalg.norm(interaction, axis=-1)
    drift = np.stack([saved[rep.id] - saved[stories[di * 32].id]
                      for di, rep in enumerate(repeats)])
    max_repeat = np.linalg.norm(drift, axis=-1).max(axis=0)
    median_norm = np.median(norms, axis=(0, 1, 2, 3))
    repeat_ratio = np.divide(max_repeat, median_norm, out=np.full_like(max_repeat, np.inf),
                             where=median_norm > 0)
    resolved = norms > 10 * max_repeat[None, None, None, None, :]
    unresolved = (~resolved).sum(axis=(0, 1, 2, 3)).astype(int)
    repeat_gate = bool(np.all(repeat_ratio <= .01))
    primary_resolved = bool(np.all(resolved[..., list(PRIMARY)]))
    unit = np.divide(interaction, norms[..., None], out=np.zeros_like(interaction),
                     where=norms[..., None] > 0)
    domain_means = unit.mean(axis=(2, 3))
    observed = _transfer(domain_means, np.ones(8))
    raw_domain_means = (unit * plan_sign).mean(axis=(2, 3))
    raw_observed = _transfer(raw_domain_means, np.ones(8))
    primary_domain_telling = observed[..., list(PRIMARY)].mean(axis=-1)
    primary_observed = float(primary_domain_telling.mean())
    null = _orientation_null(domain_means)
    domain_scores = primary_domain_telling.mean(axis=1)
    rng = np.random.default_rng(SEED)
    boot = domain_scores[rng.integers(0, 8, size=(n_boot, 8))].mean(axis=1)
    ci = list(map(float, np.quantile(boot, [.025, .975])))
    random_calibration = []
    for li in range(len(BLOCKS)):
        directions = rng.standard_normal((n_random, hidden))
        directions /= np.linalg.norm(directions, axis=1, keepdims=True)
        values = directions @ domain_means[:, :, li].mean(axis=(0, 1))
        random_calibration.append({"block": BLOCKS[li],
                                   "mean": float(values.mean()),
                                   "q95": float(np.quantile(values, .95))})
    directional_positive = [int((primary_domain_telling[:, t] > 0).sum())
                            for t in (0, 1)]
    gates = {"repeat_drift": repeat_gate,
             "primary_interactions_resolved": primary_resolved,
             "positive_primary": primary_observed > 0,
             "orientation_p": float(np.mean(null >= primary_observed)) <= .05,
             "bootstrap_lower": ci[0] > 0,
             "early_targets_at_least_6_domains": directional_positive[0] >= 6,
             "late_targets_at_least_6_domains": directional_positive[1] >= 6}
    return {"n_story_prompts": len(stories),
            "block_indices": list(BLOCKS), "primary_block_indices": [16, 24],
            "interaction_norm_median_by_block": median_norm.tolist(),
            "max_repeat_l2_by_block": max_repeat.tolist(),
            "repeat_to_interaction_ratio_by_block": repeat_ratio.tolist(),
            "unresolved_interactions_by_block": unresolved.tolist(),
            "transfer_curve": observed.mean(axis=(0, 1)).tolist(),
            "raw_a_oriented_transfer_curve": raw_observed.mean(axis=(0, 1)).tolist(),
            "raw_a_oriented_primary_mean": float(raw_observed[..., list(PRIMARY)].mean()),
            "transfer_by_target_telling": observed.mean(axis=0).tolist(),
            "transfer_by_domain_telling": observed.tolist(),
            "primary_mean_cosine": primary_observed,
            "primary_domain_telling": primary_domain_telling.tolist(),
            "positive_domains_by_target_telling": directional_positive,
            "exact_orientation_null": {"draws": len(null),
                                        "mean": float(null.mean()),
                                        "q95": float(np.quantile(null, .95)),
                                        "p_ge_observed": float(np.mean(null >= primary_observed))},
            "domain_bootstrap": {"draws": n_boot, "ci95": ci},
            "random_directions": {"draws_per_block": n_random,
                                  "calibration": random_calibration},
            "gate_components": gates,
            "candidate_aligned_interaction": all(gates.values())}


def main() -> None:
    from lsx.core.remote import RemoteLM

    behavior = _check_behavior_gate()
    stories, repeats, doc, digests = _cells()
    OUT.joinpath("states").mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("local tokenizer ref changed")
    _validate_final_tokens(rlm, stories, doc["question"])
    goal_length_deltas = _goal_length_deltas(rlm, stories, doc["question"])
    surface = _surface_nulls(stories)
    hidden = int(rlm.model.config.hidden_size)
    all_cells = stories + repeats
    fps = {c.id: _fp(c, cross.base.render(rlm, c, doc["question"]), digests)
           for c in all_cells}
    saved = {}
    first = stories[0]
    first_arr = _load(first, fps[first.id], hidden)
    if first_arr is None:
        first_arr = _extract_one(rlm, cross.base.render(rlm, first, doc["question"]))
        _save(first, fps[first.id], first_arr)
        print(f"extracted {first.id}", flush=True)
    saved[first.id] = first_arr
    # Check the new capture path against the core before submitting the full grid.
    equivalence = _equivalence(rlm, first, first_arr, doc["question"])
    for cell in all_cells:
        if cell.id in saved:
            continue
        arr = _load(cell, fps[cell.id], hidden)
        if arr is None:
            arr = _extract_one(rlm, cross.base.render(rlm, cell, doc["question"]))
            _save(cell, fps[cell.id], arr)
            print(f"extracted {cell.id}", flush=True)
        saved[cell.id] = arr
    result = analyze(stories, repeats, saved)
    domain_scores = np.asarray(result["primary_domain_telling"]).mean(axis=1)
    same_length = [i for i, delta in enumerate(goal_length_deltas) if delta == 0]
    changed_length = [i for i, delta in enumerate(goal_length_deltas) if delta != 0]
    result["goal_token_length_audit"] = {
        "goal_1_minus_goal_0_by_domain": goal_length_deltas,
        "same_length_domain_mean": float(domain_scores[same_length].mean()),
        "changed_length_domain_mean": float(domain_scores[changed_length].mean())}
    result.update({"model_checkpoint": cross.MODEL,
                   "deployment_weight_revision": None,
                   "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
                   "digests": digests, "versions": rlm.lib_versions(),
                   "behavior_grid_gate_pass": behavior["gate_pass"],
                   "surface_nulls": surface, "core_equivalence": equivalence,
                   "readable_and_aligned": result["candidate_aligned_interaction"]})
    (OUT / "report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
