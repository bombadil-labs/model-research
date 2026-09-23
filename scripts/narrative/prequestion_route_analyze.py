"""Analyze the story-ending state before the route answer question."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

import goal_route_activation_pilot as pilot
import goal_route_cross as cross
import prequestion_route_extract as extract


ROOT = Path(__file__).resolve().parents[2]


def _direction(saved: dict, stories: list[cross.Cell], block: int) -> np.ndarray:
    li = pilot.BLOCKS.index(block)
    h = np.stack([saved[c.id] for c in stories]).reshape(
        8, 2, 2, 2, 2, 2, len(pilot.BLOCKS), -1).astype(np.float64)
    raw = (h[..., 0, 0, li, :] - h[..., 0, 1, li, :] -
           h[..., 1, 0, li, :] + h[..., 1, 1, li, :])
    sign = np.array([1.0, -1.0])[None, None, None, :, None]
    oriented = raw * sign
    norms = np.linalg.norm(oriented, axis=-1)
    unit = np.divide(oriented, norms[..., None], out=np.zeros_like(oriented),
                     where=norms[..., None] > 0)
    mean = unit.mean(axis=(0, 1, 2, 3))
    return mean / np.linalg.norm(mean)


def main() -> None:
    from lsx.core.remote import RemoteLM

    extraction_path = extract.OUT / "extraction_report.json"
    extraction_bytes = extraction_path.read_bytes()
    extraction_report = json.loads(extraction_bytes)
    source = json.loads(extract.SOURCE.read_text())
    if (extraction_report["digests"]["extraction_code_sha256"] != extract._digest() or
            extraction_report["source_pilot_sha256"] !=
            hashlib.sha256(extract.SOURCE.read_bytes()).hexdigest() or
            extraction_report["all_prompt_final_match"]["min_cosine"] < .999 or
            extraction_report["all_prompt_final_match"]["max_relative_l2_error"] > .01):
        raise ValueError("extraction or source provenance failed")
    _, stories, _, _, doc, route = cross.make_cells()
    if extraction_report["digests"]["grid_sha256"] != route["grid_sha256"]:
        raise ValueError("route grid changed")
    repeats = extract._repeats(stories)
    rlm = RemoteLM(cross.MODEL)
    hidden = int(rlm.model.config.hidden_size)
    story_saved, final_saved = {}, {}
    for cell in stories + repeats:
        located = extract._locate(rlm, cell, doc["question"])
        fp = extract._fp(cell, located, extraction_report["digests"])
        arr = extract._load(cell, fp, hidden)
        if arr is None:
            raise ValueError(f"missing story-end vector: {cell.id}")
        story_saved[cell.id], final_saved[cell.id] = arr[0], arr[1]
    story = pilot.analyze(stories, repeats, story_saved)
    final_dir = _direction(final_saved, stories, 24)
    story_dir = _direction(story_saved, stories, 24)
    direction_cosine = float(np.dot(story_dir, final_dir))
    domain_scores = np.asarray(story["primary_domain_telling"]).mean(axis=1)
    lengths = extraction_report["prompt_length_by_prompt"]
    delta = [lengths[stories[di * 32 + 1].id] -
             lengths[stories[di * 32].id] for di in range(8)]
    if delta != [0, 0, 1, 0, 1, -1, 0, 0]:
        raise ValueError(f"goal-token length audit changed: {delta}")
    same = [di for di, v in enumerate(delta) if v == 0]
    changed = [di for di, v in enumerate(delta) if v != 0]
    result = {**story,
              "state_position": "final neutral-bridge token inside user story, before question",
              "story_end_token_id": extraction_report["story_end_token_id"],
              "story_end_token_decoded": extraction_report["story_end_token_decoded"],
              "source_final_prompt_curve": source["transfer_curve"],
              "story_to_final_direction_cosine_block24": direction_cosine,
              "goal_token_length_audit": {
                  "goal_1_minus_goal_0_by_domain": delta,
                  "same_length_domain_mean": float(domain_scores[same].mean()),
                  "changed_length_domain_mean": float(domain_scores[changed].mean())},
              "surface_nulls": pilot._surface_nulls(stories),
              "model_checkpoint": cross.MODEL,
              "deployment_weight_revision": None,
              "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
              "versions": extraction_report["versions"],
              "digests": extraction_report["digests"],
              "source_pilot_sha256": extraction_report["source_pilot_sha256"],
              "extraction_report_sha256": hashlib.sha256(extraction_bytes).hexdigest(),
              "analysis_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              "measurement_checks": {
                  "first_prompt_equivalence": extraction_report["first_prompt_equivalence"],
                  "all_prompt_final_match": extraction_report["all_prompt_final_match"]},
              "candidate_shared_prequestion": bool(story["candidate_aligned_interaction"])}
    path = extract.OUT / "report.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print("candidate_shared_prequestion", result["candidate_shared_prequestion"])
    print("primary_mean", result["primary_mean_cosine"])
    print(f"wrote {path}")


if __name__ == "__main__":
    main()
