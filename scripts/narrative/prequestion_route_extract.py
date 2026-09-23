"""Checkpoint the neutral story-ending residual before the answer question."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np

import fact_flip_twohop as base
import goal_route_activation_pilot as pilot
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / "research/narrative/results/goal_route_activation_pilot_summary.json"
OUT = ROOT / "cache/prequestion_route/v1"
CODE_FILES = (Path(__file__), Path(pilot.__file__), Path(cross.__file__),
              Path(base.__file__), *base.CORE_FILES)


def _digest() -> str:
    h = hashlib.sha256()
    for path in CODE_FILES:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _repeats(stories: list[cross.Cell]) -> list[cross.Cell]:
    return [replace(stories[di * 32], id=f"prequestion_repeat:{di:02d}",
                    stage="prequestion_repeat") for di in range(8)]


def _locate(rlm, cell: cross.Cell, question: str, bridge: str) -> dict:
    from lsx.core.remote import strip_template_bos

    tok = rlm.tok
    prompt = base.render(rlm, cell, question)
    lead = strip_template_bos(tok, prompt)
    body = cell.user_text.rstrip()
    if lead.count(body) != 1:
        raise ValueError(f"story body is not unique in rendered prompt: {cell.id}")
    period = lead.index(body) + len(body) - 1
    if lead[period] != ".":
        raise ValueError(f"bridge does not end at a period: {cell.id}")
    if not cell.user_text.endswith(bridge):
        raise ValueError(f"neutral bridge changed: {cell.id}")
    informative = cell.user_text[:-len(bridge)].rstrip()
    if not informative.endswith(".") or lead.count(informative) != 1:
        raise ValueError(f"informative boundary is not unique: {cell.id}")
    prebridge_period = lead.index(informative) + len(informative) - 1
    encoded = tok(lead, add_special_tokens=True, return_offsets_mapping=True)
    offsets = encoded["offset_mapping"]
    def boundary(position: int) -> tuple[int, str, str]:
        hits = [i for i, (start, end) in enumerate(offsets)
                if start <= position < end]
        if len(hits) != 1:
            raise ValueError(f"period maps to {len(hits)} tokens: {cell.id}")
        index = hits[0]
        prefix = lead[:position + 1]
        prefix_ids = tok(prefix, add_special_tokens=True)["input_ids"]
        if (prefix_ids != encoded["input_ids"][:len(prefix_ids)] or
                index != len(prefix_ids) - 1):
            raise ValueError(f"prefix tokenization changed: {cell.id}")
        return index, prefix, tok.decode([encoded["input_ids"][index]])

    index, prefix, decoded = boundary(period)
    prebridge_index, prebridge_prefix, prebridge_decoded = boundary(prebridge_period)
    question_start = lead.index("\n\n" + question) + 2
    if (question in lead[:offsets[index][1]] or
            offsets[index][1] > question_start):
        raise ValueError(f"story-end token includes question text: {cell.id}")
    return {"prompt": prompt, "prefix": prefix, "index": index,
            "token_id": int(encoded["input_ids"][index]),
            "decoded_token": decoded, "prompt_length": len(encoded["input_ids"]),
            "offset": list(map(int, offsets[index])),
            "prebridge_index": prebridge_index, "prebridge_prefix": prebridge_prefix,
            "prebridge_token_id": int(encoded["input_ids"][prebridge_index]),
            "prebridge_decoded_token": prebridge_decoded,
            "prebridge_offset": list(map(int, offsets[prebridge_index]))}


def _preflight(rlm, cells: list[cross.Cell], question: str,
               bridge: str) -> dict[str, dict]:
    located = {c.id: _locate(rlm, c, question, bridge) for c in cells}
    if len({p["token_id"] for p in located.values()}) != 1:
        raise ValueError("story-ending token ID differs across prompts")
    indices = [p["index"] for p in located.values()]
    if min(indices) != 150 or max(indices) != 160:
        raise ValueError(f"story-end token position audit changed: {min(indices)}..{max(indices)}")
    prebridge_indices = [p["prebridge_index"] for p in located.values()]
    if (len({p["prebridge_token_id"] for p in located.values()}) != 1 or
            min(prebridge_indices) != 86 or max(prebridge_indices) != 96 or
            any(p["prebridge_decoded_token"] != "." for p in located.values())):
        raise ValueError("informative-boundary token audit changed")
    for i in range(0, len(cells), 4):
        four = cells[i:i + 4]
        if len({located[c.id]["token_id"] for c in four}) != 1:
            raise ValueError(f"four-cell token differs: {four[0].id}")
    return located


def _fp(cell: cross.Cell, located: dict, digests: dict) -> str:
    body = {"id": cell.id, "prompt": located["prompt"],
            "story_end_index": located["index"],
            "prebridge_index": located["prebridge_index"], "model": cross.MODEL,
            **digests}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _path(cell: cross.Cell) -> Path:
    return OUT / "states" / (hashlib.sha256(cell.id.encode()).hexdigest() + ".npz")


def _load(cell: cross.Cell, expected_fp: str, hidden: int) -> np.ndarray | None:
    path = _path(cell)
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        if z["id"].item() != cell.id or z["fp"].item() != expected_fp:
            raise ValueError(f"stale pre-question state: {cell.id}")
        arr = np.array(z["vec"], dtype=np.float32)
    if arr.shape != (3, len(pilot.BLOCKS), hidden) or not np.isfinite(arr).all():
        raise ValueError(f"invalid pre-question vector: {cell.id}")
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


def _extract_one(rlm, prompt: str, index: int,
                 prebridge_index: int) -> np.ndarray:
    import torch
    from lsx.core.remote import _encode, assert_single_bos, strip_template_bos

    ids, mask = _encode(rlm, [prompt])
    assert_single_bos(ids, mask, getattr(rlm.tok, "bos_token_id", None))
    expected = rlm.tok(strip_template_bos(rlm.tok, prompt),
                       add_special_tokens=True)["input_ids"]
    if ids.shape != (1, len(expected)) or ids[0].tolist() != expected:
        raise ValueError("core encoding differs from the token-offset encoding")
    if (int(mask[0, -1]) != 1 or
            not 0 <= prebridge_index < index < ids.shape[1]):
        raise ValueError("invalid story-end position or padding")
    blocks = rlm.blocks
    model = rlm.model
    hidden = int(model.config.hidden_size)
    block_indices = tuple(pilot.BLOCKS)

    def build(backend):
        with model.trace({"input_ids": ids, "attention_mask": mask},
                         backend=backend) as tracer:
            prebridge, story, final = [], [], []
            for bi in block_indices:
                o = blocks[bi].output
                h = o if isinstance(o, torch.Tensor) else o[0]
                prebridge.append(h[:, prebridge_index, :].float().reshape(-1, hidden)[-1].cpu())
                story.append(h[:, index, :].float().reshape(-1, hidden)[-1].cpu())
                final.append(h[:, -1, :].float().reshape(-1, hidden)[-1].cpu())
            out = torch.stack((torch.stack(prebridge), torch.stack(story),
                               torch.stack(final))).save()
        return tracer

    for attempt in range(12):
        try:
            arr = np.asarray(rlm._run(build), dtype=np.float32)
            if arr.shape != (3, len(pilot.BLOCKS), hidden) or not np.isfinite(arr).all():
                raise ValueError(f"remote pre-question state has shape {arr.shape}")
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


def _compare(a: np.ndarray, b: np.ndarray, label: str) -> dict:
    a, b = np.asarray(a, dtype=np.float64), np.asarray(b, dtype=np.float64)
    cosine = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
    relative = float(np.linalg.norm(a - b) / np.linalg.norm(b))
    if cosine < .999 or relative > .01:
        raise ValueError(f"{label}: cosine {cosine}, relative L2 {relative}")
    return {"cosine": cosine, "relative_l2_error": relative}


def _first_equivalence(rlm, cell: cross.Cell, located: dict, arr: np.ndarray) -> dict:
    from lsx.core.remote import remote_residuals

    checks = []
    for bi in (16, 24):
        li = pilot.BLOCKS.index(bi)
        core = np.asarray(remote_residuals(rlm, [located["prompt"]], bi)[0],
                          dtype=np.float32)
        checks.append({"block": bi,
                       "prebridge_to_core": _compare(arr[0, li], core[located["prebridge_index"]],
                                                     f"prebridge vs core block {bi}"),
                       "story_to_core": _compare(arr[1, li], core[located["index"]],
                                                 f"story vs core block {bi}"),
                       "final_to_core": _compare(arr[2, li], core[-1],
                                                 f"final vs core block {bi}")})
    truncated = pilot._extract_one(rlm, located["prefix"])
    prebridge_truncated = pilot._extract_one(rlm, located["prebridge_prefix"])
    prefix = [_compare(arr[1, pilot.BLOCKS.index(bi)],
                       truncated[pilot.BLOCKS.index(bi)],
                       f"full vs truncated prefix block {bi}")
              for bi in (16, 24)]
    prebridge_prefix = [_compare(arr[0, pilot.BLOCKS.index(bi)],
                                 prebridge_truncated[pilot.BLOCKS.index(bi)],
                                 f"full vs truncated prebridge block {bi}")
                        for bi in (16, 24)]
    return {"prompt_id": cell.id, "core": checks,
            "truncated_prefix": prefix,
            "truncated_prebridge_prefix": prebridge_prefix}


def main() -> None:
    from lsx.core.remote import RemoteLM

    source = json.loads(SOURCE.read_text())
    _, stories, _, _, doc, route = cross.make_cells()
    if (not source["readable_and_aligned"] or
            source["digests"]["grid_sha256"] != route["grid_sha256"] or
            source["digests"]["behavior_code_sha256"] != route["code_sha256"] or
            source["digests"]["tokenizer_revision"] != cross.TOKENIZER_REVISION):
        raise ValueError("original route pilot provenance changed")
    repeats = _repeats(stories)
    OUT.joinpath("states").mkdir(parents=True, exist_ok=True)
    digests = {"grid_sha256": route["grid_sha256"],
               "extraction_code_sha256": _digest(),
               "source_extraction_code_sha256": source["digests"]["activation_code_sha256"],
               "tokenizer_revision": cross.TOKENIZER_REVISION,
               "block_indices": list(pilot.BLOCKS)}
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("local tokenizer revision changed")
    located = _preflight(rlm, stories, doc["question"], doc["bridge"])
    for repeat in repeats:
        located[repeat.id] = _locate(rlm, repeat, doc["question"], doc["bridge"])
    all_cells = stories + repeats
    fps = {c.id: _fp(c, located[c.id], digests) for c in all_cells}
    hidden = int(rlm.model.config.hidden_size)
    first = stories[0]
    first_arr = _load(first, fps[first.id], hidden)
    if first_arr is None:
        first_arr = _extract_one(rlm, located[first.id]["prompt"],
                                 located[first.id]["index"],
                                 located[first.id]["prebridge_index"])
        _save(first, fps[first.id], first_arr)
        print(f"extracted {first.id}", flush=True)
    equivalence = _first_equivalence(rlm, first, located[first.id], first_arr)
    min_cos, max_rel = 1.0, 0.0
    for cell in all_cells:
        arr = first_arr if cell.id == first.id else _load(cell, fps[cell.id], hidden)
        if arr is None:
            arr = _extract_one(rlm, located[cell.id]["prompt"],
                               located[cell.id]["index"],
                               located[cell.id]["prebridge_index"])
            _save(cell, fps[cell.id], arr)
            print(f"extracted {cell.id}", flush=True)
        if cell.stage == "story":
            old_fp = pilot._fp(cell, located[cell.id]["prompt"], source["digests"])
            old = pilot._load(cell, old_fp, hidden)
            if old is None:
                raise ValueError(f"missing prior final-token vector: {cell.id}")
            for bi in (16, 24):
                li = pilot.BLOCKS.index(bi)
                check = _compare(arr[2, li], old[li], f"prior final: {cell.id} block {bi}")
                min_cos = min(min_cos, check["cosine"])
                max_rel = max(max_rel, check["relative_l2_error"])
    result = {"model_checkpoint": cross.MODEL,
              "deployment_weight_revision": None,
              "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
              "versions": rlm.lib_versions(), "digests": digests,
              "source_pilot_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "n_story_prompts": len(stories), "n_repeats": len(repeats),
              "story_end_token_id": located[first.id]["token_id"],
              "story_end_token_decoded": located[first.id]["decoded_token"],
              "prebridge_token_id": located[first.id]["prebridge_token_id"],
              "prebridge_token_decoded": located[first.id]["prebridge_decoded_token"],
              "prebridge_index_by_prompt": {c.id: located[c.id]["prebridge_index"]
                                            for c in stories},
              "story_end_index_by_prompt": {c.id: located[c.id]["index"] for c in stories},
              "prompt_length_by_prompt": {c.id: located[c.id]["prompt_length"] for c in stories},
              "first_prompt_equivalence": equivalence,
              "all_prompt_final_match": {"min_cosine": min_cos,
                                         "max_relative_l2_error": max_rel}}
    (OUT / "extraction_report.json").write_text(json.dumps(result, indent=2) + "\n")
    print(f"wrote {OUT / 'extraction_report.json'}", flush=True)


if __name__ == "__main__":
    main()
