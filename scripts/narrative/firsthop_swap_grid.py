"""Frozen first-hop link-assignment grid for firsthop_swap_patch_prereg.md."""
from __future__ import annotations

from collections import Counter
from dataclasses import asdict
import hashlib
import itertools
import json
from pathlib import Path
from types import SimpleNamespace

import fact_flip_twohop as base
import goal_route_cross as cross


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/firsthop_swap_v1.json"


def _cell(row: dict, doc: dict, di: int, name: int, plan: int,
          world: int, goal: int, *, first_order_flip: bool = False) -> cross.Cell:
    names = row["names"] if name == 0 else row["names"][::-1]
    plans = [doc["plan_template"].format(name=person, route=route)
             for person, route in zip(names, row["routes"])]
    plans = "".join(plans if plan == 0 else plans[::-1])
    links = row["links"] if world == 0 else row["links"][::-1]
    first = [doc["first_hop_template"].format(route=route, link=link)
             for route, link in zip(row["routes"], links)]
    first_order = int(row["fact_order"][0]) ^ int(first_order_flip)
    first = "".join(first if first_order == 0 else first[::-1])
    second = [doc["second_hop_template"].format(link=link, destination=dest)
              for link, dest in zip(row["links"], (row["target"], row["foil"]))]
    second = "".join(second if row["fact_order"][1] == 0 else second[::-1])
    selected_goal = row["goal"] if goal == 0 else row["goal_foil"]
    text = row["setup"] + selected_goal + plans + first + second + doc["bridge"]
    kind = "order" if first_order_flip else "story"
    ident = f"firsthop:{kind}:{di:02d}:{name}:{plan}:{world}:{goal}"
    return cross.Cell(ident, "story", row["id"], world, 1, name, plan,
                      text, names[0], names[1], goal)


def _winner(cell: cross.Cell, row: dict) -> str:
    """Follow the constructed graph independently of the world==goal rule."""
    links = row["links"] if cell.world == 0 else row["links"][::-1]
    owner_route = {cell.plan_a_name: row["routes"][0],
                   cell.plan_b_name: row["routes"][1]}
    route_link = dict(zip(row["routes"], links))
    link_dest = dict(zip(row["links"], (row["target"], row["foil"])))
    requested = row["target"] if cell.goal == 0 else row["foil"]
    answer = [person for person, route in owner_route.items()
              if link_dest[route_link[route]] == requested]
    if len(answer) != 1:
        raise ValueError(f"non-unique graph winner: {cell.id}")
    return answer[0]


def make_cells() -> tuple[list[cross.Cell], list[cross.Cell], dict]:
    _, _, _, _, doc, source = cross.make_cells()
    stories, first_order_controls = [], []
    for di, row in enumerate(doc["domains"]):
        for name, plan, world, goal in itertools.product((0, 1), repeat=4):
            cell = _cell(row, doc, di, name, plan, world, goal)
            ordered = _cell(row, doc, di, name, plan, world, goal,
                            first_order_flip=True)
            expected = cell.plan_a_name if world == goal else cell.plan_b_name
            if _winner(cell, row) != expected or _winner(ordered, row) != expected:
                raise ValueError(f"symbolic winner mismatch: {cell.id}")
            if (cell.candidates != ordered.candidates or
                    base._words(cell.user_text) != base._words(ordered.user_text) or
                    len(cell.user_text) != len(ordered.user_text)):
                raise ValueError(f"order control changes lexical content: {cell.id}")
            stories.append(cell)
            first_order_controls.append(ordered)
        part = stories[di * 16:(di + 1) * 16]
        for name, plan, goal in itertools.product((0, 1), repeat=3):
            a = next(c for c in part if (c.name_order, c.plan_order,
                                        c.world, c.goal) == (name, plan, 0, goal))
            b = next(c for c in part if (c.name_order, c.plan_order,
                                        c.world, c.goal) == (name, plan, 1, goal))
            names = row["names"] if name == 0 else row["names"][::-1]
            plan_clauses = [doc["plan_template"].format(name=person, route=route)
                            for person, route in zip(names, row["routes"])]
            prefix = (row["setup"] + (row["goal"] if goal == 0 else row["goal_foil"]) +
                      "".join(plan_clauses if plan == 0 else plan_clauses[::-1]))
            fixed_second = [doc["second_hop_template"].format(
                link=link, destination=dest)
                for link, dest in zip(row["links"], (row["target"], row["foil"]))]
            fixed_second = "".join(fixed_second if row["fact_order"][1] == 0
                                   else fixed_second[::-1])
            suffix = fixed_second + doc["bridge"]
            if (not a.user_text.startswith(prefix) or
                    not b.user_text.startswith(prefix) or
                    a.user_text[len(prefix):] == b.user_text[len(prefix):] or
                    not a.user_text.endswith(suffix) or
                    not b.user_text.endswith(suffix) or
                    base._words(a.user_text) != base._words(b.user_text) or
                    len(a.user_text) != len(b.user_text) or
                    a.user_text[-200:] != b.user_text[-200:] or
                    a.candidates != b.candidates):
                raise ValueError(f"world pair surface invariant failed: {a.id}")
    if len(stories) != 128 or len(first_order_controls) != 128:
        raise ValueError("wrong grid size")
    return stories, first_order_controls, {
        "source_grid_sha256": source["grid_sha256"],
        "model_checkpoint": cross.MODEL,
        "tokenizer_revision": cross.TOKENIZER_REVISION,
        "question": doc["question"],
        "bridge": doc["bridge"],
        "fact_order_quadrants": dict(Counter(
            str(tuple(row["fact_order"])) for row in doc["domains"])),
        "correct_rule": "plan-A owner iff world == goal"}


def snapshot() -> dict:
    stories, controls, metadata = make_cells()
    doc = json.loads(cross.GRID.read_text())
    rows = {row["id"]: row for row in doc["domains"]}
    def record(cell: cross.Cell) -> dict:
        return {**asdict(cell), "candidates": list(cell.candidates),
                "correct_name": _winner(cell, rows[cell.domain])}
    return {**metadata,
            "story": [record(c) for c in stories],
            "first_order_control": [record(c) for c in controls]}


def token_audit(tok) -> dict:
    """Check full-prompt signatures and the world-pair's fixed suffix tokens."""
    from lsx.core.remote import strip_template_bos
    import prequestion_route_extract as prior

    stories, controls, metadata = make_cells()
    doc = json.loads(cross.GRID.read_text())
    rlm = SimpleNamespace(tok=tok)
    locations = {}
    suffix_ids = {}
    for cell in stories + controls:
        prompt = base.render(rlm, cell, metadata["question"])
        lead = strip_template_bos(tok, prompt)
        encoded = tok(lead, add_special_tokens=True,
                      return_offsets_mapping=True)
        if encoded["input_ids"].count(tok.bos_token_id) != 1:
            raise ValueError(f"BOS count changed: {cell.id}")
        loc = prior._locate(rlm, cell, metadata["question"], metadata["bridge"])
        if loc["prebridge_decoded_token"] != ".":
            raise ValueError(f"period token changed: {cell.id}")
        for candidate in cell.candidates:
            full = tok(lead + candidate, add_special_tokens=True)["input_ids"]
            if (full[:len(encoded["input_ids"])] != encoded["input_ids"] or
                    len(full) != len(encoded["input_ids"]) + 1):
                raise ValueError(f"candidate tokenization changed: {cell.id}")
        row = doc["domains"][int(cell.id.split(":")[2])]
        clauses = [doc["second_hop_template"].format(link=link,
                   destination=dest) for link, dest in zip(
                       row["links"], (row["target"], row["foil"]))]
        second = "".join(clauses if row["fact_order"][1] == 0 else clauses[::-1])
        if lead.count(second) != 1:
            raise ValueError(f"second-hop text not unique: {cell.id}")
        start = lead.index(second)
        suffix_ids[cell.id] = [token for token, (left, right) in zip(
            encoded["input_ids"], encoded["offset_mapping"])
            if left >= start and right <= start + len(second) and right > left]
        if len(suffix_ids[cell.id]) < 5:
            raise ValueError(f"second-hop token span too short: {cell.id}")
        locations[cell.id] = loc
    for i in range(0, 128, 4):
        for goal in (0, 1):
            a, b = stories[i + goal], stories[i + 2 + goal]
            x, y = locations[a.id], locations[b.id]
            if (x["prompt_length"], x["prebridge_index"],
                    x["prebridge_token_id"], suffix_ids[a.id]) != (
                        y["prompt_length"], y["prebridge_index"],
                        y["prebridge_token_id"], suffix_ids[b.id]):
                raise ValueError(f"world-pair token mismatch: {a.id}")
    for cell, control in zip(stories, controls):
        x, y = locations[cell.id], locations[control.id]
        if (x["prompt_length"], x["prebridge_index"],
                x["prebridge_token_id"]) != (
                    y["prompt_length"], y["prebridge_index"],
                y["prebridge_token_id"]):
            raise ValueError(f"first-hop-order token mismatch: {cell.id}")
    for di, name, world, goal in itertools.product(range(8), (0, 1),
                                                    (0, 1), (0, 1)):
        i = di * 16 + name * 8 + world * 2 + goal
        a, b = stories[i], stories[i + 4]
        x, y = locations[a.id], locations[b.id]
        if (x["prompt_length"], x["prebridge_index"],
                x["prebridge_token_id"]) != (
                    y["prompt_length"], y["prebridge_index"],
                    y["prebridge_token_id"]):
            raise ValueError(f"plan-order token mismatch: {a.id}")
    return {"model_checkpoint": metadata["model_checkpoint"],
            "tokenizer_revision": metadata["tokenizer_revision"],
            "source_grid_sha256": metadata["source_grid_sha256"],
            "prompt_count": len(stories), "order_control_count": len(controls),
            "world_pairs_same_full_length_period_and_second_hop_ids": 64,
            "first_hop_order_pairs_same_full_length_and_period": 128,
            "plan_order_pairs_same_full_length_and_period": 64,
            "max_prompt_tokens": max(x["prompt_length"] for x in locations.values()),
            "min_prompt_tokens": min(x["prompt_length"] for x in locations.values()),
            "grid_sha256": hashlib.sha256(GRID.read_bytes()).hexdigest(),
            "builder_code_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}


def write_snapshot() -> None:
    payload = snapshot()
    GRID.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n")
    print(GRID, hashlib.sha256(GRID.read_bytes()).hexdigest())


if __name__ == "__main__":
    write_snapshot()
