"""Unpatched readout gate for firsthop_swap_patch_prereg.md."""
from __future__ import annotations

import hashlib
import itertools
import json
import os
from pathlib import Path

import numpy as np

import fact_flip_twohop as base
import firsthop_swap_grid as grid
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cache/firsthop_swap/v1"
FROZEN_GRID_SHA256 = "52a26471f27322ad18bc6f72d57d022ffa7f5372609b38bea855dc45570490be"
SEED = 20260923


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _code_digest() -> str:
    paths = (Path(__file__), Path(grid.__file__), Path(base.__file__),
             ROOT / "src/lsx/core/remote.py", ROOT / "src/lsx/ndif.py")
    h = hashlib.sha256()
    for path in paths:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _fingerprint(cell: cross.Cell, prompt: str, digests: dict) -> str:
    body = {"id": cell.id, "prompt": prompt, "candidates": cell.candidates,
            "model": cross.MODEL, **digests}
    return _sha(json.dumps(body, sort_keys=True).encode())


def _analyze(cells: list[cross.Cell], saved: dict, doc: dict,
             digests: dict, versions: dict) -> dict:
    scores = np.array([saved[c.id]["scores"] for c in cells],
                      dtype=np.float64).reshape(8, 2, 2, 2, 2, 2)
    a_index = np.array([c.candidates.index(c.plan_a_name) for c in cells],
                       dtype=np.int64).reshape(8, 2, 2, 2, 2)
    a = np.take_along_axis(scores, a_index[..., None], axis=-1)[..., 0]
    b = np.take_along_axis(scores, (1 - a_index)[..., None], axis=-1)[..., 0]
    m = a - b
    d0 = m[:, :, :, 0, 0] - m[:, :, :, 1, 0]
    d1 = m[:, :, :, 1, 1] - m[:, :, :, 0, 1]
    good = (d0 > .25) & (d1 > .25)
    wrong = (d0 < -.25) & (d1 < -.25)
    good_counts = good.sum(axis=(1, 2))
    wrong_counts = wrong.sum(axis=(1, 2))
    null = np.array([sum(wrong_counts[di] if bit else good_counts[di]
                         for di, bit in enumerate(bits)) / 32
                     for bits in itertools.product((0, 1), repeat=8)])
    observed = float(good.mean())
    if float(null[0]) != observed:
        raise ValueError("behavior null identity differs from observed")
    p = float((null >= observed - 1e-12).mean())
    quadrant = {}
    for fact_order in itertools.product((0, 1), repeat=2):
        index = [di for di, row in enumerate(doc["domains"])
                 if tuple(row["fact_order"]) == fact_order]
        if len(index) != 2:
            raise ValueError(f"fact-order quadrant changed: {fact_order}")
        quadrant[str(fact_order)] = int(good[index].sum())
    target_sign = np.array([1 if c.world == c.goal else -1 for c in cells],
                           dtype=np.int8).reshape(8, 2, 2, 2, 2)
    target_correct = target_sign * m > 0
    strict = target_correct.all(axis=(3, 4))
    source_favoured = int((target_sign * m < 0).sum())
    gates = {"joint_at_least_24_of_32": int(good.sum()) >= 24,
             "both_name_halves_at_least_10_of_16": bool(
                 (good.sum(axis=(0, 2)) >= 10).all()),
             "both_plan_halves_at_least_10_of_16": bool(
                 (good.sum(axis=(0, 1)) >= 10).all()),
             "each_fact_quadrant_above_4_of_8": all(
                 count > 4 for count in quadrant.values()),
             "exact_p_at_most_0_05": p <= .05}
    return {"eligible_for_patch": all(gates.values()),
            "gate_components": gates,
            "joint_success": int(good.sum()), "joint_wrong": int(wrong.sum()),
            "strict_four_cell_correct": int(strict.sum()),
            "name_halves": good.sum(axis=(0, 2)).tolist(),
            "plan_halves": good.sum(axis=(0, 1)).tolist(),
            "fact_order_quadrants": quadrant,
            "domain_joint_counts": good_counts.tolist(),
            "baseline_source_winner_favoured_cells": source_favoured,
            "exact_null": {"draws": len(null), "mean": float(null.mean()),
                           "q95": float(np.quantile(null, .95)),
                           "p_ge_observed": p},
            "d0": d0.tolist(), "d1": d1.tolist(),
            "margins": m.tolist(), "candidate_scores": scores.tolist(),
            "model_checkpoint": cross.MODEL,
            "deployment_weight_revision": None,
            "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
            "tokenizer_revision": cross.TOKENIZER_REVISION,
            "versions": versions, "digests": digests}


def main() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob

    frozen = json.loads(grid.GRID.read_text())
    if _sha(grid.GRID.read_bytes()) != FROZEN_GRID_SHA256 or frozen != grid.snapshot():
        raise ValueError("first-hop prompt grid differs from committed snapshot")
    cells, _, metadata = grid.make_cells()
    doc = json.loads(cross.GRID.read_text())
    if metadata["source_grid_sha256"] != _sha(cross.GRID.read_bytes()):
        raise ValueError("source grid changed")
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("tokenizer revision changed")
    audit = grid.token_audit(rlm.tok)
    committed_audit = json.loads((ROOT / "research/narrative/results/firsthop_swap_v1_token_audit.json").read_text())
    if audit != committed_audit:
        raise ValueError("live token audit differs from committed audit")
    digests = {"grid_sha256": FROZEN_GRID_SHA256,
               "source_grid_sha256": metadata["source_grid_sha256"],
               "token_audit_sha256": _sha(json.dumps(audit, sort_keys=True).encode()),
               "code_sha256": _code_digest()}
    prompts = {c.id: base.render(rlm, c, doc["question"]) for c in cells}
    expected = {c.id: _fingerprint(c, prompts[c.id], digests) for c in cells}
    path = OUT / "behavior_scores.jsonl"
    saved = base._load_cache(path, expected, generation=False)
    for cell in cells:
        if cell.id in saved:
            continue
        scores = np.asarray(asserted_remote_patched_logprob(
            rlm, prompts[cell.id], list(cell.candidates)), dtype=np.float64)
        row = {"id": cell.id, "fp": expected[cell.id], "scores": scores.tolist()}
        base._append(path, row)
        saved[cell.id] = row
        print(f"scored {cell.id}", flush=True)
    report = _analyze(cells, saved, doc, digests, rlm.lib_versions())
    (OUT / "behavior_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("eligible_for_patch", report["eligible_for_patch"], flush=True)
    print("joint_success", report["joint_success"], flush=True)


if __name__ == "__main__":
    main()
