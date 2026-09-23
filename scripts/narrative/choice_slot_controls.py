"""Score and extract the frozen direct-route and property-choice controls."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import itertools
import json
import os
from pathlib import Path
import re

import numpy as np

import fact_flip_twohop as base
import goal_route_activation_pilot as pilot
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/choice_slot_controls_v1.json"
SOURCE = ROOT / "research/narrative/results/goal_route_activation_pilot_summary.json"
OUT = ROOT / "cache/choice_slot_control/v1"
CODE_FILES = (Path(__file__), Path(pilot.__file__), Path(cross.__file__),
              Path(base.__file__), *base.CORE_FILES)
SEED = 20260923


def _digest() -> str:
    h = hashlib.sha256()
    for path in CODE_FILES:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def make_property_cells() -> tuple[list[cross.Cell], dict, dict]:
    raw = GRID.read_bytes()
    doc = json.loads(raw)
    if (len(doc["domains"]) != 4 or doc["bridge_source"] !=
            "goal_route_cross_v1.json:bridge"):
        raise ValueError("property control grid changed")
    route = json.loads(cross.GRID.read_bytes())
    bridge = route["bridge"]
    route_controls = route["controls"]
    if [r["names"] for r in doc["domains"]] != [
            r["names"] for r in route_controls]:
        raise ValueError("property names differ from direct-route controls")
    if len(bridge) < 200 or not bridge.endswith(". "):
        raise ValueError("invalid frozen bridge")
    cells = []
    for di, row in enumerate(doc["domains"]):
        if (len(row["labels"]) != 2 or len(set(row["labels"])) != 2 or
                len(set(row["names"])) != 2 or
                len(row["names"][0]) != len(row["names"][1])):
            raise ValueError(f"invalid property row: {row['id']}")
        for telling, name_order, plan_order, world, goal in itertools.product(
                (0, 1), repeat=5):
            names = row["names"] if name_order == 0 else row["names"][::-1]
            labels = row["labels"] if world == 0 else row["labels"][::-1]
            facts = [row["fact_template"].format(name=n, label=l)
                     for n, l in zip(names, labels)]
            fact_text = "".join(facts if plan_order == 0 else facts[::-1])
            goal_text = row["goal_template"].format(label=row["labels"][goal])
            body = (goal_text + fact_text if telling == 0 else
                    fact_text + goal_text)
            text = row["setup"] + body + bridge
            ident = f"property:{di:02d}:{telling}:{name_order}:{plan_order}:{world}:{goal}"
            if any(len(re.findall(r"\b" + re.escape(n) + r"\b", text)) != 1
                   for n in names):
                raise ValueError(f"name mentioned more than once: {ident}")
            cells.append(cross.Cell(
                id=ident, stage="property", domain=row["id"], world=world,
                telling=telling, name_order=name_order, plan_order=plan_order,
                user_text=text, plan_a_name=names[0], plan_b_name=names[1],
                goal=goal))
    if len(cells) != 128:
        raise ValueError("property cell count differs")
    for i in range(0, len(cells), 4):
        four = cells[i:i + 4]
        if [(c.world, c.goal) for c in four] != [
                (0, 0), (0, 1), (1, 0), (1, 1)]:
            raise ValueError("property quartet order changed")
        if len({c.user_text[-200:] for c in four}) != 1:
            raise ValueError("property quartet suffix changed")
        for goal in (0, 1):
            a, b = four[goal], four[2 + goal]
            if (base._words(a.user_text) != base._words(b.user_text) or
                    len(a.user_text) != len(b.user_text)):
                raise ValueError(f"property world pair differs: {a.id}")
        for world in (0, 1):
            a, b = four[world * 2:world * 2 + 2]
            if a.user_text == b.user_text:
                raise ValueError(f"property goal does not change: {a.id}")
    return cells, doc, {"property_grid_sha256": hashlib.sha256(raw).hexdigest(),
                        "route_grid_sha256": hashlib.sha256(cross.GRID.read_bytes()).hexdigest()}


def _source_and_direct() -> tuple[list[cross.Cell], list[cross.Cell], dict, dict, dict]:
    source = json.loads(SOURCE.read_text())
    direct, stories, _, _, route_doc, route_digests = cross.make_cells()
    behavior = json.loads((cross.OUT / "report.json").read_text())
    if (source["model_checkpoint"] != cross.MODEL or
            source["digests"]["grid_sha256"] != route_digests["grid_sha256"] or
            source["digests"]["behavior_code_sha256"] != route_digests["code_sha256"] or
            source["digests"]["tokenizer_revision"] != cross.TOKENIZER_REVISION or
            not source["readable_and_aligned"] or
            behavior["digests"] != route_digests or
            behavior["control"]["joint_success"] != 32):
        raise ValueError("source or direct-route behavioral provenance failed")
    return direct, stories, route_doc, route_digests, source


def _render(rlm, cell: cross.Cell, question: str) -> str:
    return base.render(rlm, cell, question)


def _fp(cell: cross.Cell, prompt: str, question: str, digests: dict,
        *, kind: str) -> str:
    body = {"id": cell.id, "prompt": prompt, "question": question,
            "model": cross.MODEL, "kind": kind, **digests}
    return hashlib.sha256(json.dumps(body, sort_keys=True).encode()).hexdigest()


def _path(cell: cross.Cell) -> Path:
    return OUT / "states" / (hashlib.sha256(cell.id.encode()).hexdigest() + ".npz")


def _load(cell: cross.Cell, expected_fp: str, hidden: int) -> np.ndarray | None:
    path = _path(cell)
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        if z["id"].item() != cell.id or z["fp"].item() != expected_fp:
            raise ValueError(f"stale target state: {cell.id}")
        arr = np.array(z["vec"], dtype=np.float32)
    if arr.shape != (len(pilot.BLOCKS), hidden) or not np.isfinite(arr).all():
        raise ValueError(f"bad target state: {cell.id}")
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


def _validate_tokens(rlm, cells: list[cross.Cell], question: str) -> dict:
    from lsx.core.remote import assert_single_bos, strip_template_bos
    import torch

    tok = rlm.tok
    goal_deltas = []
    for i in range(0, len(cells), 4):
        four = cells[i:i + 4]
        ids = []
        for cell in four:
            lead = strip_template_bos(tok, _render(rlm, cell, question))
            base_ids = tok(lead, add_special_tokens=True)["input_ids"]
            assert_single_bos(torch.tensor([base_ids]),
                              torch.ones((1, len(base_ids))),
                              getattr(tok, "bos_token_id", None))
            lengths = []
            for candidate in cell.candidates:
                full = tok(lead + candidate, add_special_tokens=True)["input_ids"]
                if full[:len(base_ids)] != base_ids:
                    raise ValueError(f"candidate changes prompt tokenization: {cell.id}")
                lengths.append(len(full) - len(base_ids))
            if lengths[0] != lengths[1] or not lengths[0]:
                raise ValueError(f"candidate token counts differ: {cell.id}: {lengths}")
            ids.append(base_ids)
        if (len({x[-1] for x in ids}) != 1 or
                len({c.user_text[-200:] for c in four}) != 1):
            raise ValueError(f"four-cell final token or text differs: {four[0].id}")
        for g in (0, 1):
            if len(ids[g]) != len(ids[2 + g]):
                raise ValueError(f"world pair token lengths differ: {four[g].id}")
        goal_deltas.append(len(ids[1]) - len(ids[0]))
    return {"goal_1_minus_goal_0_tokens_by_quartet": goal_deltas,
            "same_goal_token_length_fraction": float(np.mean(np.array(goal_deltas) == 0))}


def _repeats(cells: list[cross.Cell], battery: str) -> list[cross.Cell]:
    return [replace(cells[di * 32], id=f"choice_repeat:{battery}:{di:02d}",
                    stage=f"choice_repeat_{battery}") for di in range(4)]


def _extract_group(rlm, cells: list[cross.Cell], repeats: list[cross.Cell],
                   question: str, digests: dict, battery: str) -> dict:
    all_cells = cells + repeats
    fps = {c.id: _fp(c, _render(rlm, c, question), question, digests,
                     kind="activation") for c in all_cells}
    hidden = int(rlm.model.config.hidden_size)
    first = cells[0]
    first_arr = _load(first, fps[first.id], hidden)
    if first_arr is None:
        first_arr = pilot._extract_one(rlm, _render(rlm, first, question))
        _save(first, fps[first.id], first_arr)
        print(f"extracted {first.id}", flush=True)
    equivalence = pilot._equivalence(rlm, first, first_arr, question)
    for cell in all_cells:
        if cell.id == first.id:
            continue
        arr = _load(cell, fps[cell.id], hidden)
        if arr is None:
            arr = pilot._extract_one(rlm, _render(rlm, cell, question))
            _save(cell, fps[cell.id], arr)
            print(f"extracted {cell.id}", flush=True)
    return {"battery": battery, "n_cells": len(cells),
            "n_repeats": len(repeats), "core_equivalence": equivalence}


def main() -> None:
    from lsx.core.remote import RemoteLM

    direct, stories, route_doc, route_digests, source = _source_and_direct()
    prop, prop_doc, grids = make_property_cells()
    OUT.joinpath("states").mkdir(parents=True, exist_ok=True)
    digests = {**grids, "extraction_code_sha256": _digest(),
               "source_extraction_code_sha256": source["digests"]["activation_code_sha256"],
               "tokenizer_revision": cross.TOKENIZER_REVISION,
               "block_indices": list(pilot.BLOCKS)}
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("local tokenizer revision changed")
    for cell in stories:
        fp = pilot._fp(cell, _render(rlm, cell, route_doc["question"]),
                       source["digests"])
        if pilot._load(cell, fp, int(rlm.model.config.hidden_size)) is None:
            raise ValueError(f"missing original source state: {cell.id}")
    preflight = {"direct": _validate_tokens(rlm, direct, route_doc["question"]),
                 "property": _validate_tokens(rlm, prop, prop_doc["question"])}
    score_path = OUT / "property_scores.jsonl"
    score_fps = {c.id: _fp(c, _render(rlm, c, prop_doc["question"]),
                           prop_doc["question"], digests, kind="logprob")
                 for c in prop}
    scores = base._load_cache(score_path, score_fps, generation=False)
    base.score_cells(rlm, prop, scores, score_fps, score_path,
                     prop_doc["question"])
    behavior = cross.paired_report(prop, scores, prop_doc["domains"],
                                   treatment=False)
    direct_repeats = _repeats(direct, "direct")
    prop_repeats = _repeats(prop, "property")
    extracted = [_extract_group(rlm, direct, direct_repeats,
                                route_doc["question"], digests, "direct"),
                 _extract_group(rlm, prop, prop_repeats,
                                prop_doc["question"], digests, "property")]
    report = {"model_checkpoint": cross.MODEL,
              "deployment_weight_revision": None,
              "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
              "versions": rlm.lib_versions(), "digests": digests,
              "source_pilot_sha256": hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
              "route_behavior_digests": route_digests,
              "property_question": prop_doc["question"],
              "direct_question": route_doc["question"],
              "token_preflight": preflight,
              "direct_behavior_joint_success": 32,
              "property_behavior": behavior, "extraction": extracted}
    (OUT / "extraction_report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("property behavioral gate", behavior["gate_pass"], flush=True)
    print(f"wrote {OUT / 'extraction_report.json'}", flush=True)


if __name__ == "__main__":
    main()
