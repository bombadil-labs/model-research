"""Fixed-plan circumstance switch; see goal_relative_prereg.md."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from reveal_invariance_probe import cross_scores, interaction, PRIMARY_EDGES
from role_swap_probe import MID, MODEL_CHECKPOINT, MODEL_REVISION, SEED, unit


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/goal_relative_v1.json"
OUT = ROOT / "cache/goal_relative"
SNAPSHOT = ROOT / ("cache/hf/hub/models--Qwen--Qwen2.5-1.5B/snapshots/"
                   "8faed761d45a263340a0528343f099c05c9a4323")
DEPENDENCIES = (Path(__file__), Path(__file__).with_name("reveal_invariance_probe.py"),
                Path(__file__).with_name("role_swap_probe.py"))


def code_digest() -> str:
    h = hashlib.sha256()
    for path in DEPENDENCIES:
        h.update(path.name.encode())
        h.update(path.read_bytes())
    return h.hexdigest()


@dataclass(frozen=True)
class Case:
    domain: str
    a_action: str
    format: int
    world: int
    recipient: int
    text: str
    recipient_fact: str
    cue: str
    bridge_char: int


def _words(s: str) -> Counter:
    return Counter(re.findall(r"\b\w+\b", s.lower()))


def make_cases(path: Path) -> tuple[list[Case], str]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    domains = doc["domains"]
    if len(domains) != 12 or len({d["id"] for d in domains}) != 12:
        raise ValueError("expected twelve unique domains")
    if Counter(d["a_action"] for d in domains) != {"allow": 6, "block": 6}:
        raise ValueError("action polarity is not balanced")
    if Counter(d["a_useful_status"] == d["good_status"] for d in domains) != {
            True: 6, False: 6}:
        raise ValueError("useful-status valence is not balanced")
    cases = []
    for d in domains:
        if (d["good_status"] == d["bad_status"] or
                {d["a_useful_status"], d["b_useful_status"]} !=
                {d["good_status"], d["bad_status"]} or
                not d["a_useful_reason"].strip().endswith(".") or
                not d["b_useful_reason"].strip().endswith(".") or
                not d["cue_negative_verb"].strip()):
            raise ValueError(f"missing semantic orientation: {d['id']}")
        if (d["a"] == d["b"] or len(d["a"]) != len(d["b"]) or
                any(not d[k].endswith(". ") for k in ("intro", "body", "fact_a", "fact_b")) or
                not doc["bridge"].endswith(". ") or
                not d["final_template"].endswith(".")):
            raise ValueError(f"broken sentence boundary or actor pair: {d['id']}")
        for fact_order in (0, 1):
            facts = [d["fact_a"].format(name=d["a"]),
                     d["fact_b"].format(name=d["b"])]
            if fact_order:
                facts.reverse()
            for cue_order in (0, 1):
                fmt = fact_order * 2 + cue_order
                for world in (0, 1):
                    true_status = (d["a_useful_status"] if world == 0
                                   else d["b_useful_status"])
                    false_status = (d["b_useful_status"] if world == 0
                                    else d["a_useful_status"])
                    affirmative = f"{d['cue_subject']} {d['cue_verb']} {true_status}. "
                    negative = f"{d['cue_subject']} {d['cue_negative_verb']} {false_status}. "
                    cue = (affirmative + negative if cue_order == 0 else
                           negative + affirmative)
                    prefix = d["intro"] + "".join(facts) + cue + d["body"] + doc["bridge"]
                    for recipient in (0, 1):
                        target = d["a"] if recipient == 0 else d["b"]
                        matching_facts = [fact for fact in facts
                                          if re.search(r"\b" + re.escape(target) + r"\b", fact)]
                        if len(matching_facts) != 1:
                            raise ValueError(f"recipient fact is ambiguous: {d['id']}")
                        text = prefix + d["final_template"].format(recipient=target)
                        if len(text) - text.index(cue) <= 200:
                            raise ValueError(f"circumstance entered local window: {d['id']}")
                        cases.append(Case(d["id"], d["a_action"], fmt, world,
                                          recipient, text, matching_facts[0], cue,
                                          len(prefix) - 2))
        group = cases[-16:]  # [fact order][cue order][world][recipient]
        for recipient in (0, 1):
            matched = [c for c in group if c.recipient == recipient]
            if (len({c.text[-200:] for c in matched}) != 1 or
                    len({len(c.text) for c in matched}) != 1 or
                    len({tuple(sorted(_words(c.text).items())) for c in matched}) != 1):
                raise ValueError(f"world/order text mismatch: {d['id']}")
        for fmt in range(4):
            for world in (0, 1):
                a, b = group[fmt * 4 + world * 2:fmt * 4 + world * 2 + 2]
                if a.text[:a.bridge_char + 1] != b.text[:b.bridge_char + 1]:
                    raise ValueError(f"recipient changes pre-handover text: {d['id']}")
    return cases, hashlib.sha256(raw).hexdigest()


def validate_tokens(cases: list[Case], tok, context_limit: int) -> list[tuple[int, int]]:
    rows = []
    for c in cases:
        enc = tok(c.text, return_offsets_mapping=True, add_special_tokens=True)
        if len(enc["input_ids"]) > context_limit:
            raise ValueError(f"passage exceeds context: {c.domain}")
        indexes = []
        for char in (len(c.text) - 1, c.bridge_char):
            hits = [i for i, (a, b) in enumerate(enc["offset_mapping"]) if a <= char < b]
            if len(hits) != 1:
                raise ValueError(f"readout maps to {len(hits)} tokens: {c.domain}")
            indexes.append(hits[0])
        final, bridge = indexes
        rows.append((len(enc["input_ids"]), final, enc["input_ids"][final],
                     bridge, tuple(enc["input_ids"][:bridge + 1])))
    for di in range(12):
        group = rows[di * 16:di * 16 + 16]
        if len({x[:3] for x in group}) != 1:
            raise ValueError(f"final token signature differs: domain {di}")
        for fmt in range(4):
            for world in (0, 1):
                a, b = group[fmt * 4 + world * 2:fmt * 4 + world * 2 + 2]
                if a[3:] != b[3:]:
                    raise ValueError(f"recipient changes bridge prefix: {di}, {fmt}, {world}")
    return [(x[1], x[3]) for x in rows]


def extract(snapshot: Path, out: Path) -> tuple[np.ndarray, np.ndarray]:
    import torch
    import transformers
    from lsx.model import LM

    out.mkdir(parents=True, exist_ok=True)
    cases, grid_hash = make_cases(GRID)
    script_hash = code_digest()
    lm = LM.from_pretrained(str(snapshot), device="cuda", dtype=torch.float16,
                            local_files_only=True)
    context_limit = int(lm.model.config.max_position_embeddings)
    indices = validate_tokens(cases, lm.tok, context_limit)
    finals, bridges = [], []
    for di in range(12):
        path = out / f"domain_{di:02d}.npz"
        group = cases[di * 16:di * 16 + 16]
        expected_shape = (2, 2, 2, 2, lm.n_layers + 1, lm.d_model)
        if path.exists():
            with np.load(path) as saved:
                if (saved["grid_hash"].item() != grid_hash or
                        saved["script_hash"].item() != script_hash or
                        saved["domain"].item() != group[0].domain):
                    raise ValueError(f"stale checkpoint: {path}")
                final, bridge = saved["final"], saved["bridge"]
            if any(x.shape != expected_shape or not np.isfinite(x).all()
                   for x in (final, bridge)):
                raise ValueError(f"broken checkpoint arrays: {path}")
        else:
            ff, pp = [], []
            for j, case in enumerate(group):
                hs, offsets = lm.residuals(case.text)
                hits = []
                for char in (len(case.text) - 1, case.bridge_char):
                    found = [k for k, (a, b) in enumerate(offsets) if a <= char < b]
                    if len(found) != 1:
                        raise ValueError(f"readout offset changed: {case.domain}")
                    hits.append(found[0])
                if tuple(hits) != indices[di * 16 + j]:
                    raise ValueError(f"readout index changed: {case.domain}")
                ff.append(hs[:, hits[0], :].numpy().copy())
                pp.append(hs[:, hits[1], :].numpy().copy())
                del hs
            final = np.stack(ff).reshape(expected_shape)
            bridge = np.stack(pp).reshape(expected_shape)
            if any(not np.isfinite(x).all() for x in (final, bridge)):
                raise ValueError(f"nonfinite activations: {group[0].domain}")
            if not np.all(final[:, :, :, :, 0, :] == final[:1, :1, :1, :1, 0, :]):
                raise ValueError(f"layer-0 final token differs: {group[0].domain}")
            if not np.array_equal(bridge[:, :, :, 0], bridge[:, :, :, 1]):
                raise ValueError(f"recipient changes pre-handover state: {group[0].domain}")
            np.savez_compressed(path, final=final, bridge=bridge,
                                domain=group[0].domain, grid_hash=grid_hash,
                                script_hash=script_hash,
                                token_indices=np.asarray(indices[di * 16:di * 16 + 16]))
            print(f"extracted {di + 1}/12: {group[0].domain}", flush=True)
        finals.append(final)
        bridges.append(bridge)
    stacks = np.stack(finals), np.stack(bridges)
    provenance = {"model_checkpoint": MODEL_CHECKPOINT, "model_revision": MODEL_REVISION,
                  "device": "cuda", "dtype": "float16", "grid_sha256": grid_hash,
                  "script_sha256": script_hash, "torch": torch.__version__,
                  "transformers": transformers.__version__, "context_limit": context_limit,
                  "final_sha256": hashlib.sha256(stacks[0].tobytes()).hexdigest(),
                  "bridge_sha256": hashlib.sha256(stacks[1].tobytes()).hexdigest()}
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return stacks


def load_cached(out: Path) -> tuple[np.ndarray, np.ndarray]:
    cases, grid_hash = make_cases(GRID)
    provenance = json.loads((out / "provenance.json").read_text())
    if (provenance["grid_sha256"] != grid_hash or
            provenance["model_revision"] != MODEL_REVISION or
            provenance["script_sha256"] != code_digest()):
        raise ValueError("stale extraction provenance")
    by_name = {name: [] for name in ("final", "bridge")}
    for di in range(12):
        with np.load(out / f"domain_{di:02d}.npz") as saved:
            if (saved["grid_hash"].item() != grid_hash or
                    saved["script_hash"].item() != provenance["script_sha256"] or
                    saved["domain"].item() != cases[di * 16].domain):
                raise ValueError(f"stale checkpoint: {di}")
            for name in by_name:
                by_name[name].append(saved[name])
    stacks = tuple(np.stack(by_name[name]) for name in by_name)
    for name, arr in zip(by_name, stacks):
        if hashlib.sha256(arr.tobytes()).hexdigest() != provenance[name + "_sha256"]:
            raise ValueError(f"activation digest mismatch: {name}")
    return stacks


def lexical_baseline(cases: list[Case], *, mode: str) -> float:
    if len(cases) != 192:
        raise ValueError("lexical baseline requires the full grid")
    if mode == "local":
        rows = [Counter(c.text[-200:][i:i + 3]
                        for i in range(len(c.text[-200:]) - 2)) for c in cases]
    elif mode == "whole":
        rows = [_words(c.text) for c in cases]
    elif mode == "recipient_fact":
        rows = [_words(c.recipient_fact) for c in cases]
    elif mode == "circumstance":
        rows = [_words(c.cue) for c in cases]
    else:
        raise ValueError(mode)
    vocab = sorted(set().union(*(set(row) for row in rows)))
    vectors = np.array([[row.get(term, 0) for term in vocab] for row in rows],
                       dtype=np.float32).reshape(12, 4, 2, 2, 1, -1)
    state = interaction(vectors)
    return float(np.stack([cross_scores(state[:, src], state[:, dst])
                           for src, dst in PRIMARY_EDGES]).mean())


def score(stacks: tuple[np.ndarray, np.ndarray], *, n_null: int = 1000,
          n_boot: int = 2000) -> dict:
    final, bridge = stacks
    if final.ndim != 7 or bridge.shape != final.shape or final.shape[:5] != (12, 2, 2, 2, 2):
        raise ValueError("stack shape mismatch")
    if max(MID) >= final.shape[5]:
        raise ValueError("registered layers missing")
    if not np.all(final[:, :, :, :, :, 0, :] == final[:, :1, :1, :1, :1, 0, :]):
        raise ValueError("layer-0 final null failed")
    if not np.array_equal(bridge[:, :, :, :, 0], bridge[:, :, :, :, 1]):
        raise ValueError("pre-handover recipient null failed")
    f = final.reshape(12, 4, 2, 2, *final.shape[-2:])
    p = bridge.reshape(12, 4, 2, 2, *bridge.shape[-2:])
    state = interaction(f)
    arms = {f"{src}_to_{dst}": cross_scores(state[:, src], state[:, dst])
            for src in range(4) for dst in range(4)}
    primary = np.stack([arms[f"{src}_to_{dst}"] for src, dst in PRIMARY_EDGES], axis=1)
    observed = float(primary[:, :, list(MID)].mean())
    transfer_groups = {
        "within_format": tuple((f, f) for f in range(4)),
        "fact_order_only": ((0, 2), (1, 3), (2, 0), (3, 1)),
        "cue_order_only": ((0, 1), (1, 0), (2, 3), (3, 2)),
    }
    zero = np.zeros_like(state[:, 0])
    exact = {"pre_handover": cross_scores(interaction(p)[:, 0], interaction(p)[:, 3]),
             "no_world": cross_scores(zero, zero)}
    if (any(not np.all(x[:, 0] == .5) for x in arms.values()) or
            any(x.mean() != .5 for x in exact.values())):
        raise ValueError("exact-null arm failed")
    cases, _ = make_cases(GRID)
    lexical = {"local_200_char_trigrams": lexical_baseline(cases, mode="local"),
               "full_word_bag": lexical_baseline(cases, mode="whole"),
               "recipient_fact_word_bag": lexical_baseline(cases, mode="recipient_fact"),
               "circumstance_word_bag": lexical_baseline(cases, mode="circumstance")}
    if any(x != .5 for x in lexical.values()):
        raise ValueError(f"lexical null failed: {lexical}")
    rng = np.random.default_rng(SEED + 7)
    boot = []
    for _ in range(n_boot):
        idx = rng.integers(0, 12, size=12)
        boot.append(float(primary[idx][:, :, list(MID)].mean()))
    perm, random = [], []
    for _ in range(n_null):
        sign = rng.choice([-1, 1], size=12)
        shifted = state * sign[:, None, None, None]
        perm.append(float(np.stack([cross_scores(shifted[:, src], shifted[:, dst])
                                    for src, dst in PRIMARY_EDGES], axis=1)
                          [:, :, list(MID)].mean()))
        direction = unit(rng.standard_normal((state.shape[-2], state.shape[-1])))
        margin = np.einsum("nfld,ld->nfl", state, direction)
        random.append(float(((margin[:, :, list(MID)] > 1e-12) +
                             .5 * (np.abs(margin[:, :, list(MID)]) <= 1e-12)).mean()))
    action = np.array([d["a_action"] for d in json.loads(GRID.read_text())["domains"]])
    return {
        "n_domains": 12, "n_passages": 192, "mid_layers": list(MID),
        "arms": {name: {"mid": float(s[:, list(MID)].mean()),
                         "curve": list(map(float, s.mean(axis=0)))}
                 for name, s in arms.items()},
        "primary_edges": [list(x) for x in PRIMARY_EDGES],
        "primary_mid": observed,
        "primary_curve": list(map(float, primary.mean(axis=(0, 1)))),
        "transfer_groups_mid": {
            name: float(np.stack([arms[f"{src}_to_{dst}"] for src, dst in edges])
                        [:, :, list(MID)].mean())
            for name, edges in transfer_groups.items()},
        "primary_bootstrap_ci95": list(map(float, np.quantile(boot, [.025, .975]))),
        "action_halves_mid": {m: float(primary[action == m][:, :, list(MID)].mean())
                              for m in ("allow", "block")},
        "exact_arms": {k: float(v.mean()) for k, v in exact.items()},
        "lexical_baselines": lexical,
        "permutation": {"draws": n_null, "mean": float(np.mean(perm)),
                        "q95": float(np.quantile(perm, .95)),
                        "p_ge_observed": (1 + sum(x >= observed for x in perm)) / (n_null + 1)},
        "random_direction": {"draws": n_null, "mean": float(np.mean(random)),
                             "q025_q975": list(map(float, np.quantile(random, [.025, .975])))},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    args = ap.parse_args()
    rng = np.random.default_rng(43)
    signal = unit(rng.normal(size=(12, 29, 16)) * .2 + np.eye(16)[0])
    noise = unit(rng.normal(size=(12, 29, 16)))
    calibration = {"signal": float(cross_scores(signal, signal)[:, list(MID)].mean()),
                   "noise": float(cross_scores(noise, noise)[:, list(MID)].mean())}
    if calibration["signal"] < .95 or not .35 <= calibration["noise"] <= .65:
        raise ValueError(f"scorer calibration failed: {calibration}")
    stacks = load_cached(OUT) if args.score_only else extract(args.snapshot, OUT)
    report = score(stacks)
    report["self_test"] = calibration
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"primary_mid": report["primary_mid"],
                      "primary_bootstrap_ci95": report["primary_bootstrap_ci95"],
                      "primary_edges": {f"{a}_to_{b}": report["arms"][f"{a}_to_{b}"]["mid"]
                                        for a, b in PRIMARY_EDGES},
                      "action_halves_mid": report["action_halves_mid"],
                      "exact_arms": report["exact_arms"],
                      "lexical_baselines": report["lexical_baselines"],
                      "permutation": report["permutation"],
                      "random_direction": report["random_direction"],
                      "self_test": calibration}, indent=2))


if __name__ == "__main__":
    main()
