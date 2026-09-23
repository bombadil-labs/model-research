"""Single-period counterfactual route patch; see story_fact_token_patch_prereg.md."""
from __future__ import annotations

from dataclasses import replace
import hashlib
import itertools
import json
import os
from pathlib import Path
import time

import numpy as np

import fact_flip_twohop as base
import goal_route_activation_pilot as pilot
import goal_route_cross as cross
import prequestion_route_extract as prior


ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "cache/story_fact_token_patch/v1"
LAYER = 24
LAST_LAYER = 41
SEED = 20260923
ARMS = ("none", "zero", "full", "lex_natural", "lex_matched",
        "plan_matched", "random", "last_block")
ACTIVE = ("full", "lex_natural", "lex_matched", "plan_matched", "random")
MATCHED = ("clinic", "library", "orchard", "factory", "ship")
CODE_FILES = (Path(__file__), Path(prior.__file__), Path(pilot.__file__),
              Path(cross.__file__), Path(base.__file__), *base.CORE_FILES,
              ROOT / "src/lsx/core/checks.py")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _code_digest() -> str:
    h = hashlib.sha256()
    for path in CODE_FILES:
        h.update(str(path.relative_to(ROOT)).encode())
        h.update(path.read_bytes())
    return h.hexdigest()


def _key(cell: cross.Cell) -> tuple:
    return (cell.domain, cell.name_order, cell.plan_order,
            cell.world, cell.goal)


def selected_cells(stories: list[cross.Cell], doc: dict) -> list[cross.Cell]:
    cells = [c for c in stories if c.telling == 1]
    if len(cells) != 128 or len({_key(c) for c in cells}) != 128:
        raise ValueError("late-story target count changed")
    for di, row in enumerate(doc["domains"]):
        part = cells[di * 16:(di + 1) * 16]
        if (any(c.domain != row["id"] for c in part) or
                [(c.name_order, c.plan_order, c.world, c.goal) for c in part] !=
                list(itertools.product((0, 1), repeat=4))):
            raise ValueError(f"late-story factor order changed: {row['id']}")
    return cells


def lexical_cell(cell: cross.Cell, row: dict, doc: dict) -> cross.Cell:
    """Change only the last second-hop destination, leaving an inconsistent story."""
    destinations = ((row["target"], row["foil"]) if cell.world == 0
                    else (row["foil"], row["target"]))
    last_route = 1 - int(row["fact_order"][1])
    old = doc["second_hop_template"].format(
        link=row["links"][last_route], destination=destinations[last_route])
    new = doc["second_hop_template"].format(
        link=row["links"][last_route], destination=destinations[1 - last_route])
    bridge = doc["bridge"]
    if (not cell.user_text.endswith(bridge) or old == new or
            not cell.user_text[:-len(bridge)].endswith(old)):
        raise ValueError(f"lexical suffix mismatch: {cell.id}")
    prefix = cell.user_text[:-len(bridge) - len(old)]
    if (prefix + old + bridge != cell.user_text or
            new.count(destinations[1 - last_route]) != 1):
        raise ValueError(f"lexical change is not unique: {cell.id}")
    return replace(cell, id=f"lexical:{cell.id}",
                   user_text=prefix + new + bridge)


def symbolic_source_sign(cell: cross.Cell, row: dict) -> int:
    """Follow the graph rather than assuming the world/goal sign formula."""
    source_world = 1 - cell.world
    destinations = ((row["target"], row["foil"]) if source_world == 0
                    else (row["foil"], row["target"]))
    requested = row["target"] if cell.goal == 0 else row["foil"]
    routes = row["routes"]
    links = row["links"]
    owner_routes = {cell.plan_a_name: routes[0], cell.plan_b_name: routes[1]}
    route_to_link = dict(zip(routes, links))
    link_to_destination = dict(zip(links, destinations))
    reaches = {name: link_to_destination[route_to_link[route]]
               for name, route in owner_routes.items()}
    winners = [name for name, dest in reaches.items() if dest == requested]
    if len(winners) != 1:
        raise ValueError(f"source graph has {len(winners)} winners: {cell.id}")
    sign = 1 if winners[0] == cell.plan_a_name else -1
    if sign != (1 if source_world == cell.goal else -1):
        raise ValueError(f"source graph disagrees with formula: {cell.id}")
    return sign


def _location(rlm, cell: cross.Cell, doc: dict) -> dict:
    loc = prior._locate(rlm, cell, doc["question"], doc["bridge"])
    if loc["prebridge_decoded_token"] != ".":
        raise ValueError(f"period token changed: {cell.id}")
    return loc


def _validate_factors(rlm, cells: list[cross.Cell], lexical: dict,
                      located: dict, doc: dict) -> dict:
    from lsx.core.remote import strip_template_bos

    tok = rlm.tok
    by_key = {_key(c): c for c in cells}
    shifts = {}
    for cell in cells:
        loc = located[cell.id]
        source = by_key[(cell.domain, cell.name_order, cell.plan_order,
                         1 - cell.world, cell.goal)]
        plan = by_key[(cell.domain, cell.name_order, 1 - cell.plan_order,
                       cell.world, cell.goal)]
        if any(loc[k] != located[source.id][k] for k in
               ("prebridge_index", "prebridge_token_id", "prompt_length")):
            raise ValueError(f"world-pair token signature changed: {cell.id}")
        if any(loc[k] != located[plan.id][k] for k in
               ("prebridge_index", "prebridge_token_id", "prompt_length")):
            raise ValueError(f"plan-order token signature changed: {cell.id}")
        lex = lexical[cell.id]
        ll = located[lex.id]
        if loc["prebridge_token_id"] != ll["prebridge_token_id"]:
            raise ValueError(f"lexical period token changed: {cell.id}")
        shift = ll["prompt_length"] - loc["prompt_length"]
        if ll["prebridge_index"] - loc["prebridge_index"] != shift:
            raise ValueError(f"lexical token shift differs at period: {cell.id}")
        shifts.setdefault(cell.domain, set()).add(shift)
        for current in (cell, lex):
            lead = strip_template_bos(tok, located[current.id]["prompt"])
            lead_ids = tok(lead, add_special_tokens=True)["input_ids"]
            if len(lead_ids) != located[current.id]["prompt_length"]:
                raise ValueError(f"prompt length changed: {current.id}")
            for candidate in cell.candidates:
                full = tok(lead + candidate, add_special_tokens=True)["input_ids"]
                if full[:len(lead_ids)] != lead_ids or len(full) != len(lead_ids) + 1:
                    raise ValueError(f"candidate token boundary changed: {current.id}")
    expected = {name: ({0} if name in MATCHED else {-1, 1})
                for name in shifts}
    if shifts != expected:
        raise ValueError(f"lexical token-length audit changed: {shifts}")
    return {name: sorted(v) for name, v in shifts.items()}


def _fp(cell: cross.Cell, loc: dict, kind: str, arm: str | None,
        vec: np.ndarray | None, digests: dict) -> str:
    layer = LAST_LAYER if arm == "last_block" else LAYER if arm not in (
        None, "none") else None
    body = {"id": cell.id, "prompt": loc["prompt"], "candidates": cell.candidates,
            "period_index": loc["prebridge_index"], "period_id": loc["prebridge_token_id"],
            "kind": kind, "arm": arm, "patch_layer": layer,
            "vector_sha256": (None if vec is None else
                _sha(np.asarray(vec, dtype=np.float32).tobytes())), **digests}
    return _sha(json.dumps(body, sort_keys=True).encode())


def _state_path(cell: cross.Cell) -> Path:
    return OUT / "states" / (_sha(cell.id.encode()) + ".npz")


def _save_state(cell: cross.Cell, fp: str, state: np.ndarray) -> None:
    path = _state_path(cell)
    tmp = path.with_suffix(".tmp.npz")
    with tmp.open("wb") as handle:
        np.savez_compressed(handle, id=cell.id, fp=fp,
                            state=np.asarray(state, dtype=np.float32))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp, path)


def _load_state(cell: cross.Cell, fp: str, hidden: int) -> np.ndarray | None:
    path = _state_path(cell)
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        if z["id"].item() != cell.id or z["fp"].item() != fp:
            raise ValueError(f"stale state capture: {cell.id}")
        value = np.asarray(z["state"], dtype=np.float32)
    if value.shape != (2, hidden) or not np.isfinite(value).all():
        raise ValueError(f"invalid state capture: {cell.id}")
    if not np.array_equal(value[0], value[1]):
        raise ValueError(f"candidate rows differ at period: {cell.id}")
    return value


def traced_score(rlm, prompt: str, candidates: tuple[str, str], period_index: int,
                 *, patch_layer: int | None = None,
                 patch_vec: np.ndarray | None = None,
                 capture: str = "none", row_zero_only: bool = False,
                 baseline: list[float] | None = None) -> tuple[np.ndarray, np.ndarray | None, bool]:
    """One scoring/capture path for all arms; `capture` is none, period or full."""
    import torch
    from lsx.core import checks
    from lsx.core.remote import _add_special, _encode, assert_single_bos, strip_template_bos

    if capture not in ("none", "period", "full"):
        raise ValueError(f"unknown capture mode {capture}")
    if (patch_vec is None) != (patch_layer is None):
        raise ValueError("patch vector and layer must occur together")
    if row_zero_only and patch_vec is None:
        raise ValueError("row-zero check needs a patch vector")
    if len(candidates) != 2 or rlm.padding_side != "left":
        raise ValueError("scoring requires two candidates and left padding")

    lead = strip_template_bos(rlm.tok, prompt)
    texts = [lead + c for c in candidates]
    ids, mask = _encode(rlm, texts)
    assert_single_bos(ids, mask, getattr(rlm.tok, "bos_token_id", None))
    n_lead = len(rlm.tok(lead, add_special_tokens=_add_special(rlm, [lead]))[
        "input_ids"])
    if (tuple(ids.shape) != (2, n_lead + 1) or not bool(mask.all()) or
            not 0 <= period_index < n_lead - 1):
        raise ValueError("scoring batch, zero-padding or period index changed")
    for row in range(2):
        if ids[row, :n_lead].tolist() != ids[0, :n_lead].tolist():
            raise ValueError("candidate changed prompt-token prefix")
    target = ids[:, 1:]
    score_mask = mask[:, 1:].clone().float()
    n_real = mask.sum(dim=1)
    for row in range(2):
        first_real = int(mask.shape[1] - n_real[row])
        score_mask[row, :first_real + n_lead - 1] = 0.0
    first_column = int((score_mask.sum(0) > 0).nonzero().min())
    if float(score_mask.sum()) != 2.0 or first_column != n_lead - 1:
        raise ValueError("candidate mask is not one token per row")
    target = target[:, first_column:]
    score_mask = score_mask[:, first_column:]

    model = rlm.model
    blocks = rlm.blocks
    lm_head = model.lm_head
    cfg = getattr(model, "config", None)
    cap = getattr(cfg, "final_logit_softcapping", None) if cfg is not None else None
    cap = None if cap is None else float(cap)
    block_index = patch_layer if patch_layer is not None else LAYER
    vector = None if patch_vec is None else torch.as_tensor(
        np.asarray(patch_vec, dtype=np.float32))
    if vector is not None and (vector.ndim != 1 or
                               len(vector) != int(model.config.hidden_size) or
                               not bool(torch.isfinite(vector).all())):
        raise ValueError("invalid patch vector")
    hidden = int(model.config.hidden_size)
    sequence = int(ids.shape[1])
    capture_size = (0 if capture == "none" else
                    2 * hidden if capture == "period" else
                    2 * sequence * hidden)

    def once(check_base: list[float] | None):
        def build(backend):
            with model.trace({"input_ids": ids, "attention_mask": mask},
                             backend=backend) as tracer:
                snapshot = None
                if vector is not None or capture != "none":
                    output = blocks[int(block_index)].output
                    h = output if isinstance(output, torch.Tensor) else output[0]
                    if vector is not None:
                        vv = vector.to(h.device, h.dtype)
                        if row_zero_only:
                            h[0:1, period_index, :] = h[0:1, period_index, :] + vv
                        else:
                            h[:, period_index, :] = h[:, period_index, :] + vv
                    if capture == "period":
                        snapshot = h[:, period_index, :].float().cpu().reshape(-1)
                    elif capture == "full":
                        snapshot = h.float().cpu().reshape(-1)
                logits = lm_head.output[:, first_column:-1, :].float()
                if cap is not None:
                    logits = torch.tanh(logits / cap) * cap
                picked = (logits.gather(-1, target.unsqueeze(-1).to(logits.device))
                          .squeeze(-1) - torch.logsumexp(logits, dim=-1))
                scores = (picked * score_mask.to(picked.device)).sum(-1)
                if snapshot is None:
                    out = scores.save()
                else:
                    out = torch.cat((scores.float().cpu().reshape(-1), snapshot)).save()
            return tracer

        for attempt in range(12):
            try:
                returned = np.asarray(rlm._run(build), dtype=np.float32).reshape(-1)
                if returned.size != 2 + capture_size or not np.isfinite(returned).all():
                    raise ValueError(f"invalid traced score/capture shape: {returned.size}")
                scores = np.asarray(returned[:2], dtype=np.float64)
                state = None
                if capture == "period":
                    state = returned[2:].reshape(2, hidden)
                elif capture == "full":
                    state = returned[2:].reshape(2, sequence, hidden)
                if check_base is not None:
                    checks.assert_moved_candidates(check_base, scores, batch=2)
                return scores, state
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
        scores, state = once(baseline)
        return scores, state, False
    except checks.MovedCandidates:
        if baseline is None or vector is None:
            raise
        a, a_state = once(None)
        b, state = once(None)
        if (float(np.max(np.abs(a - b))) > .001 or
                (state is not None and (a_state is None or
                 float(np.max(np.abs(a_state - state))) > .001))):
            raise ValueError("moved-candidate fallback is not deterministic")
        return b, state, True


def _old_state(rlm, cell: cross.Cell, loc: dict, report: dict) -> tuple[np.ndarray, str]:
    hidden = int(rlm.model.config.hidden_size)
    fp = prior._fp(cell, loc, report["digests"])
    arr = prior._load(cell, fp, hidden)
    if arr is None:
        raise ValueError(f"missing original pre-question state: {cell.id}")
    return np.asarray(arr[0, pilot.BLOCKS.index(LAYER)], dtype=np.float32), fp


def capture_states(rlm, cells: list[cross.Cell], lexical: dict,
                   located: dict, prior_report: dict, digests: dict) -> tuple[dict, dict]:
    OUT.joinpath("states").mkdir(parents=True, exist_ok=True)
    hidden = int(rlm.model.config.hidden_size)
    captures = {}
    comparisons = {}
    for cell in cells + [lexical[c.id] for c in cells]:
        loc = located[cell.id]
        fp = _fp(cell, loc, "state", None, None, digests)
        state = _load_state(cell, fp, hidden)
        if state is None:
            _, state, _ = traced_score(rlm, loc["prompt"], cell.candidates,
                                       loc["prebridge_index"], capture="period")
            if state is None or state.shape != (2, hidden) or not np.array_equal(
                    state[0], state[1]):
                raise ValueError(f"candidate rows differ in capture: {cell.id}")
            _save_state(cell, fp, state)
            print(f"captured {cell.id}", flush=True)
        captures[cell.id] = state
        if cell.id in lexical:
            old, old_fp = _old_state(rlm, cell, loc, prior_report)
            a, b = state[0].astype(np.float64), old.astype(np.float64)
            cosine = float(np.dot(a, b) / (np.linalg.norm(a) * np.linalg.norm(b)))
            relative = float(np.linalg.norm(a - b) / np.linalg.norm(b))
            if cosine < .999 or relative > .02:
                raise ValueError(f"one/two-row state mismatch: {cell.id}: {cosine}, {relative}")
            comparisons[cell.id] = {"cosine": cosine, "relative_l2_error": relative,
                                    "original_fingerprint": old_fp,
                                    "batch_state_sha256": _sha(state.tobytes())}
    if len(captures) != 256 or len(comparisons) != 128:
        raise ValueError("state capture count changed")
    return captures, comparisons


def _unit_scaled(vector: np.ndarray, norm: float) -> np.ndarray:
    v = np.asarray(vector, dtype=np.float64)
    length = float(np.linalg.norm(v))
    if not np.isfinite(length) or length <= 0:
        raise ValueError("zero or invalid control delta")
    out = np.asarray(v * (norm / length), dtype=np.float32)
    if not np.isclose(np.linalg.norm(out), norm, atol=.01):
        raise ValueError("control norm differs from treatment")
    return out


def _pair_vectors(cell: cross.Cell, by_key: dict, lexical: dict,
                  captures: dict, di: int, hidden: int) -> tuple[dict, dict]:
    source = by_key[(cell.domain, cell.name_order, cell.plan_order,
                     1 - cell.world, cell.goal)]
    plan = by_key[(cell.domain, cell.name_order, 1 - cell.plan_order,
                   cell.world, cell.goal)]
    target_h = captures[cell.id][0].astype(np.float64)
    source_h = captures[source.id][0].astype(np.float64)
    lexical_h = captures[lexical[cell.id].id][0].astype(np.float64)
    plan_h = captures[plan.id][0].astype(np.float64)
    full = source_h - target_h
    lexical_delta = lexical_h - target_h
    plan_delta = plan_h - target_h
    length = float(np.linalg.norm(full))
    if not np.isfinite(length) or length <= 0:
        raise ValueError(f"zero source-world delta: {cell.id}")
    factor_index = (cell.name_order * 8 + cell.plan_order * 4 +
                    cell.goal * 2 + cell.world)
    rng = np.random.default_rng(SEED + di * 16 + factor_index)
    controls = {"lex_matched": _unit_scaled(lexical_delta, length),
                "plan_matched": _unit_scaled(plan_delta, length),
                "random": _unit_scaled(rng.standard_normal(hidden), length)}
    vectors = {"none": None, "zero": np.zeros(hidden, dtype=np.float32),
               "full": np.asarray(full, dtype=np.float32),
               "lex_natural": np.asarray(lexical_delta, dtype=np.float32),
               **controls, "last_block": np.asarray(full, dtype=np.float32)}
    if any(vec is not None and (vec.shape != (hidden,) or not np.isfinite(vec).all())
           for vec in vectors.values()):
        raise ValueError(f"invalid pair vector: {cell.id}")
    metrics = {"full_norm": length,
               "lexical_norm": float(np.linalg.norm(lexical_delta)),
               "lexical_over_full_norm": float(np.linalg.norm(lexical_delta) / length),
               "plan_norm": float(np.linalg.norm(plan_delta)),
               "source_id": source.id, "plan_order_source_id": plan.id,
               "lexical_id": lexical[cell.id].id,
               "target_state_sha256": _sha(captures[cell.id].tobytes()),
               "source_state_sha256": _sha(captures[source.id].tobytes()),
               "lexical_state_sha256": _sha(captures[lexical[cell.id].id].tobytes()),
               "plan_state_sha256": _sha(captures[plan.id].tobytes())}
    return vectors, metrics


def _preflight(rlm, cell: cross.Cell, loc: dict, vector: np.ndarray,
               no_patch: list[float]) -> dict:
    from lsx.core import checks

    index = loc["prebridge_index"]
    prompt, candidates = loc["prompt"], cell.candidates
    reference, before, _ = traced_score(rlm, prompt, candidates, index,
                                        capture="full")
    if before is None or float(np.max(np.abs(reference - no_patch))) > .001:
        raise ValueError("preflight baseline drift")
    negative, row_only, _ = traced_score(
        rlm, prompt, candidates, index, patch_layer=LAYER,
        patch_vec=4 * vector, capture="full", row_zero_only=True)
    if (row_only is None or
            not np.array_equal(row_only[1], before[1]) or
            not np.array_equal(np.delete(row_only[0], index, axis=0),
                               np.delete(before[0], index, axis=0)) or
            np.array_equal(row_only[0, index], before[0, index]) or
            abs(float(negative[0] - reference[0])) <= 1e-6 or
            abs(float(negative[1] - reference[1])) > 1e-6):
        raise ValueError("row-zero-only negative control did not isolate row 0")
    try:
        checks.assert_moved_candidates(reference, negative, batch=2)
    except checks.MovedCandidates:
        refused = True
    else:
        raise ValueError("row-zero-only patch escaped moved-candidates check")

    full, after, _ = traced_score(rlm, prompt, candidates, index,
                                  patch_layer=LAYER, patch_vec=vector,
                                  capture="full")
    if after is None or not np.array_equal(np.delete(after, index, axis=1),
                                            np.delete(before, index, axis=1)):
        raise ValueError("block-24 patch changed non-target token positions")
    import torch
    expected = (torch.as_tensor(before[:, index, :]).to(torch.bfloat16) +
                torch.as_tensor(vector).to(torch.bfloat16)).float().numpy()
    reach_error = float(np.max(np.abs(after[:, index, :] - expected)))
    if reach_error > .001 or any(np.array_equal(after[r, index], before[r, index])
                                for r in range(2)):
        raise ValueError(f"block-24 patch failed two-row residual reach: {reach_error}")
    last_scores, last_after, _ = traced_score(
        rlm, prompt, candidates, index, patch_layer=LAST_LAYER,
        patch_vec=vector, capture="full")
    last_zero_scores, last_before, _ = traced_score(
        rlm, prompt, candidates, index, patch_layer=LAST_LAYER,
        patch_vec=np.zeros_like(vector), capture="full")
    if (last_before is None or last_after is None or
            float(np.max(np.abs(last_zero_scores - reference))) > .001 or
            float(np.max(np.abs(last_scores - reference))) > .001 or
            not np.array_equal(np.delete(last_after, index, axis=1),
                               np.delete(last_before, index, axis=1))):
        raise ValueError("last-block pass-through changed scored position")
    expected_last = (torch.as_tensor(last_before[:, index, :]).to(torch.bfloat16) +
                     torch.as_tensor(vector).to(torch.bfloat16)).float().numpy()
    last_error = float(np.max(np.abs(last_after[:, index, :] - expected_last)))
    if last_error > .001:
        raise ValueError(f"last-block arithmetic failed: {last_error}")
    return {"row_zero_only_refused": refused,
            "row_zero_score_delta": (negative - reference).tolist(),
            "block24_residual_error": reach_error,
            "block41_residual_error": last_error,
            "block24_score_delta": (full - reference).tolist(),
            "block41_score_delta": (last_scores - reference).tolist()}


def _effect_report(effect: np.ndarray, *, seed: int) -> dict:
    values = np.asarray(effect, dtype=np.float64)
    domain = values.mean(axis=tuple(range(1, values.ndim)))
    n = len(domain)
    if n not in (5, 8):
        raise ValueError("effect must have five or eight independent domains")
    observed = float(domain.mean())
    null = np.array([float(np.mean(domain * np.array(signs)))
                     for signs in itertools.product((-1, 1), repeat=n)])
    if not np.isclose(null[-1], observed, atol=1e-12):
        raise ValueError("identity sign flip differs from observed")
    rng = np.random.default_rng(seed)
    boot = domain[rng.integers(0, n, size=(10000, n))].mean(axis=1)
    return {"mean": observed, "domain_effects": domain.tolist(),
            "positive_domains": int((domain > 0).sum()),
            "positive_cells": int((values > 0).sum()),
            "exact_null": {"draws": len(null), "mean": float(null.mean()),
                           "q95": float(np.quantile(null, .95)),
                           "p_ge_observed": float(np.mean(null >= observed - 1e-12)),
                           "tie_count_excluding_identity": int(np.sum(np.isclose(
                               null, observed, atol=1e-12, rtol=0))) - 1},
            "domain_bootstrap": {"draws": 10000,
                                 "ci95": list(map(float, np.quantile(
                                     boot, [.025, .975])))}}


def analyze(cells: list[cross.Cell], rows: dict, pair_metrics: dict,
            token_audit: dict, capture_checks: dict, preflight: dict,
            core_checks: dict) -> dict:
    if len(cells) != 128:
        raise ValueError("wrong target count")
    scores = np.array([[rows[f"{c.id}|{arm}"]["scores"] for arm in ARMS]
                       for c in cells], dtype=np.float64).reshape(8, 2, 2, 2, 2,
                                                                  len(ARMS), 2)
    a_index = np.array([c.candidates.index(c.plan_a_name) for c in cells],
                       dtype=np.int64).reshape(8, 2, 2, 2, 2)
    score_a = np.take_along_axis(scores, a_index[..., None, None], axis=-1)[..., 0]
    score_b = np.take_along_axis(scores, (1 - a_index)[..., None, None], axis=-1)[..., 0]
    margins = score_a - score_b
    signs = np.array([pair_metrics[c.id]["source_sign"] for c in cells],
                     dtype=np.float64).reshape(8, 2, 2, 2, 2)
    effects = {arm: signs * (margins[..., ARMS.index(arm)] -
                              margins[..., ARMS.index("none")]) for arm in ARMS[1:]}
    primary = _effect_report(effects["full"], seed=SEED + 1)
    random_mean = float(effects["random"].mean())
    plan_mean = float(effects["plan_matched"].mean())
    max_control = max(abs(random_mean), abs(plan_mean))
    zero_diff = np.abs(scores[..., ARMS.index("zero"), :] -
                       scores[..., ARMS.index("none"), :])
    last_diff = np.abs(scores[..., ARMS.index("last_block"), :] -
                       scores[..., ARMS.index("none"), :])
    flags = {arm: int(sum(bool(rows[f"{c.id}|{arm}"].get("flagged", False))
                          for c in cells)) for arm in ACTIVE}
    n_flags = sum(flags.values())
    gates = {"core_equivalence": max(core_checks.values()) <= .001,
             "capture_equivalence": max(v["relative_l2_error"] for v in
                                        capture_checks.values()) <= .02,
             "row_zero_negative_refused": bool(preflight["row_zero_only_refused"]),
             "zero_identity": float(zero_diff.max()) <= .001,
             "last_block_pass_through": float(last_diff.max()) <= .001,
             "flag_fraction_at_most_0_05": n_flags / (128 * len(ACTIVE)) <= .05,
             "mean_at_least_0_25": primary["mean"] >= .25,
             "exact_p": primary["exact_null"]["p_ge_observed"] <= .05,
             "bootstrap_lower": primary["domain_bootstrap"]["ci95"][0] > 0,
             "six_positive_domains": primary["positive_domains"] >= 6,
             "ninety_six_positive_cells": primary["positive_cells"] >= 96,
             "twice_max_control": primary["mean"] > 2 * max_control}
    domain_order = [cells[di * 16].domain for di in range(8)]
    if set(domain_order) != set(token_audit):
        raise ValueError("token audit and scored domain names differ")
    matched_indices = [i for i, name in enumerate(domain_order)
                       if name in MATCHED]
    if len(matched_indices) != 5:
        raise ValueError("length-matched domain count changed")
    lexical_surplus = {}
    lexical_gates = {}
    for offset, arm in enumerate(("lex_natural", "lex_matched"), start=2):
        difference = effects["full"][matched_indices] - effects[arm][matched_indices]
        report = _effect_report(difference, seed=SEED + offset)
        lexical_surplus[arm] = report
        lexical_gates[arm] = {
            "mean_at_least_0_10": report["mean"] >= .10,
            "five_positive_domains": report["positive_domains"] == 5,
            "exact_p": report["exact_null"]["p_ge_observed"] <= .05,
            "bootstrap_lower": report["domain_bootstrap"]["ci95"][0] > 0}
    moved = {}
    for ai, arm in enumerate(ARMS[1:], start=1):
        count = (np.abs(scores[..., ai, :] - scores[..., 0, :]) > 1e-6).sum(axis=-1)
        moved[arm] = {str(k): int((count == k).sum()) for k in range(3)}
    source_before = signs * margins[..., ARMS.index("none")]
    source_after = signs * margins[..., ARMS.index("full")]
    first_correct = (source_before > 0)
    then_correct = (source_after > 0)
    norms = np.array([[pair_metrics[c.id][key] for key in
                       ("full_norm", "lexical_norm", "lexical_over_full_norm",
                        "plan_norm")] for c in cells]).reshape(8, 2, 2, 2, 2, 4)
    return {"primary_full_effect": primary,
            "control_effects": {arm: _effect_report(effects[arm], seed=SEED + 10 + ai)
                                for ai, arm in enumerate(ARMS[1:])},
            "beyond_last_noun_surplus": lexical_surplus,
            "beyond_last_noun_gate_components": lexical_gates,
            "beyond_last_noun_screen": all(gates.values()) and all(
                all(g.values()) for g in lexical_gates.values()),
            "full_causal_screen": all(gates.values()),
            "gate_components": gates,
            "signed_effects": {arm: effect.tolist() for arm, effect in effects.items()},
            "world_pair_mean_effects": effects["full"].mean(axis=3).tolist(),
            "factor_halves": {
                "name_0": float(effects["full"][:, 0].mean()),
                "name_1": float(effects["full"][:, 1].mean()),
                "plan_order_0": float(effects["full"][:, :, 0].mean()),
                "plan_order_1": float(effects["full"][:, :, 1].mean()),
                "target_world_0": float(effects["full"][:, :, :, 0].mean()),
                "target_world_1": float(effects["full"][:, :, :, 1].mean()),
                "goal_0": float(effects["full"][..., 0].mean()),
                "goal_1": float(effects["full"][..., 1].mean())},
            "choice_flips": {"toward_source": int((~first_correct & then_correct).sum()),
                             "away_from_source": int((first_correct & ~then_correct).sum()),
                             "source_winner_before": int(first_correct.sum()),
                             "source_winner_after": int(then_correct.sum())},
            "candidate_scores": scores.tolist(),
            "candidate_score_deltas": (scores - scores[..., :1, :]).tolist(),
            "moved_candidate_histograms": moved,
            "flagged_job_counts": flags,
            "flagged_job_fraction": n_flags / (128 * len(ACTIVE)),
            "max_zero_score_difference": float(zero_diff.max()),
            "max_last_block_score_difference": float(last_diff.max()),
            "max_control_abs_mean": max_control,
            "norms": norms.tolist(),
            "matched_domain_names": list(MATCHED),
            "token_length_audit": token_audit,
            "preflight": preflight,
            "core_equivalence_and_drift": core_checks,
            "capture_checks": capture_checks}


def main() -> None:
    from lsx.core.remote import RemoteLM, asserted_remote_patched_logprob

    controls, stories, duplicates, _, doc, route = cross.make_cells()
    cells = selected_cells(stories, doc)
    domain_rows = {row["id"]: row for row in doc["domains"]}
    lexical = {cell.id: lexical_cell(cell, domain_rows[cell.domain], doc)
               for cell in cells}
    prior_report_path = prior.OUT / "extraction_report.json"
    prior_report = json.loads(prior_report_path.read_text())
    prior_analysis = json.loads((prior.OUT / "report.json").read_text())
    if (prior_report["digests"]["grid_sha256"] != route["grid_sha256"] or
            prior_report["digests"]["extraction_code_sha256"] != prior._digest() or
            prior_report["model_checkpoint"] != cross.MODEL or
            prior_analysis["max_repeat_l2_by_block"][pilot.BLOCKS.index(LAYER)] != 0):
        raise ValueError("original pre-question extraction provenance changed")
    OUT.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(cross.MODEL)
    hf_home = Path(os.environ.get("HF_HOME", ROOT / "cache/hf"))
    ref = hf_home / "hub/models--google--gemma-2-9b-it/refs/main"
    if not ref.exists() or ref.read_text().strip() != cross.TOKENIZER_REVISION:
        raise ValueError("local tokenizer revision changed")

    located = {cell.id: _location(rlm, cell, doc) for cell in cells}
    located.update({cell.id: _location(rlm, cell, doc) for cell in lexical.values()})
    token_audit = _validate_factors(rlm, cells, lexical, located, doc)
    digests = {"model": cross.MODEL,
               "grid_sha256": route["grid_sha256"],
               "prior_extraction_report_sha256": _sha(prior_report_path.read_bytes()),
               "prior_analysis_sha256": _sha((prior.OUT / "report.json").read_bytes()),
               "prior_extraction_code_sha256": prior._digest(),
               "code_sha256": _code_digest(),
               "tokenizer_revision": cross.TOKENIZER_REVISION}

    # The new scorer must agree with the established, softcapped core path.
    ordered = sorted(cells, key=lambda c: located[c.id]["prompt_length"])
    endpoints = {"shortest": ordered[0], "longest": ordered[-1]}
    core_checks = {}
    for name, cell in endpoints.items():
        loc = located[cell.id]
        ours, _, _ = traced_score(rlm, loc["prompt"], cell.candidates,
                                  loc["prebridge_index"])
        core = np.asarray(asserted_remote_patched_logprob(
            rlm, loc["prompt"], list(cell.candidates)), dtype=np.float64)
        error = float(np.max(np.abs(ours - core)))
        if error > .001:
            raise ValueError(f"new scorer differs from core at {name}: {error}")
        core_checks[name] = error
    print("core scorer equivalence passed", flush=True)

    captures, capture_checks = capture_states(
        rlm, cells, lexical, located, prior_report, digests)
    by_key = {_key(c): c for c in cells}
    hidden = int(rlm.model.config.hidden_size)
    vectors, pair_metrics = {}, {}
    for di, cell in enumerate(cells):
        vector_set, metrics = _pair_vectors(
            cell, by_key, lexical, captures, di // 16, hidden)
        metrics["source_sign"] = symbolic_source_sign(cell, domain_rows[cell.domain])
        vectors[cell.id], pair_metrics[cell.id] = vector_set, metrics

    all_original = controls + stories + duplicates
    old_expected = {c.id: cross.fingerprint(
        c, base.render(rlm, c, doc["question"]), route) for c in all_original}
    previous = base._load_cache(cross.OUT / "scores.jsonl", old_expected,
                                generation=False)
    if len(previous) != len(all_original):
        raise ValueError("original core score cache is incomplete")
    expected = {}
    for cell in cells:
        pair_digests = {**digests,
                        "original_state_fingerprint": capture_checks[cell.id][
                            "original_fingerprint"],
                        **{key: pair_metrics[cell.id][key] for key in
                         ("target_state_sha256", "source_state_sha256",
                          "lexical_state_sha256", "plan_state_sha256")}}
        for arm in ARMS:
            expected[f"{cell.id}|{arm}"] = _fp(
                cell, located[cell.id], "score", arm, vectors[cell.id][arm],
                pair_digests)
    score_path = OUT / "scores.jsonl"
    saved = base._load_cache(score_path, expected, generation=False)
    for cell in cells:
        key = f"{cell.id}|none"
        if key not in saved:
            loc = located[cell.id]
            scores, _, _ = traced_score(rlm, loc["prompt"], cell.candidates,
                                         loc["prebridge_index"])
            row = {"id": key, "fp": expected[key], "scores": scores.tolist(),
                   "flagged": False}
            base._append(score_path, row)
            saved[key] = row
            print(f"scored {key}", flush=True)
        drift = float(np.max(np.abs(np.asarray(saved[key]["scores"]) -
                                    np.asarray(previous[cell.id]["scores"]))))
        if drift > .001:
            raise ValueError(f"original no-patch scorer drift: {cell.id}: {drift}")
        core_checks["old_cache_max_drift"] = max(
            core_checks.get("old_cache_max_drift", 0.0), drift)
    print("all 128 no-patch scores match core cache", flush=True)

    first = ordered[0]
    preflight = _preflight(rlm, first, located[first.id],
                           vectors[first.id]["full"],
                           saved[f"{first.id}|none"]["scores"])
    (OUT / "preflight.json").write_text(json.dumps(preflight, indent=2) + "\n")
    print("single-position reach and row-zero negative checks passed", flush=True)

    for cell in cells:
        loc = located[cell.id]
        baseline = saved[f"{cell.id}|none"]["scores"]
        for arm in ARMS[1:]:
            key = f"{cell.id}|{arm}"
            if key in saved:
                continue
            layer = LAST_LAYER if arm == "last_block" else LAYER
            scores, period_state, flagged = traced_score(
                rlm, loc["prompt"], cell.candidates, loc["prebridge_index"],
                patch_layer=layer, patch_vec=vectors[cell.id][arm],
                capture="period" if arm == "full" else "none",
                baseline=baseline if arm in ACTIVE else None)
            row = {"id": key, "fp": expected[key], "scores": scores.tolist(),
                   "flagged": flagged}
            if arm == "full":
                import torch
                target_h = captures[cell.id]
                source_id = pair_metrics[cell.id]["source_id"]
                source_h = captures[source_id]
                predicted = (torch.as_tensor(target_h).to(torch.bfloat16) +
                             torch.as_tensor(vectors[cell.id]["full"]).to(
                                 torch.bfloat16)).float().numpy()
                reach_error = float(np.max(np.abs(period_state - predicted)))
                if reach_error > .001:
                    raise ValueError(f"full patch missed period state: {cell.id}: {reach_error}")
                source_rel = float(np.linalg.norm(
                    period_state.astype(np.float64) - source_h.astype(np.float64)) /
                    np.linalg.norm(source_h.astype(np.float64)))
                row.update({"period_residual_error": reach_error,
                            "source_state_relative_error": source_rel,
                            "moved_period_rows": int(np.sum(np.any(
                                period_state != target_h, axis=-1)))})
                if row["moved_period_rows"] != 2:
                    raise ValueError(f"full patch did not move both period rows: {cell.id}")
            if arm in ("zero", "last_block") and float(np.max(
                    np.abs(scores - np.asarray(baseline)))) > .001:
                raise ValueError(f"identity/pass-through arm changed scores: {cell.id}:{arm}")
            base._append(score_path, row)
            saved[key] = row
            print(f"scored {key}", flush=True)

    report = analyze(cells, saved, pair_metrics, token_audit,
                     capture_checks, preflight, core_checks)
    report.update({"model_checkpoint": cross.MODEL,
                   "deployment_weight_revision": None,
                   "deployment_revision_note": "NDIF reports pinned but exposes no weight revision hash",
                   "versions": rlm.lib_versions(), "digests": digests,
                   "patch_block": LAYER, "pass_through_block": LAST_LAYER,
                   "n_target_prompts": len(cells),
                   "n_scored_jobs": len(expected),
                   "n_state_capture_jobs": len(captures),
                   "pair_metrics": pair_metrics,
                   "source_match_max_relative_error": max(
                       saved[f"{c.id}|full"]["source_state_relative_error"]
                       for c in cells)})
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print("full_causal_screen", report["full_causal_screen"], flush=True)
    print("beyond_last_noun_screen", report["beyond_last_noun_screen"], flush=True)


if __name__ == "__main__":
    main()
