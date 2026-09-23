"""Early/late reveal and clause-order invariance; see reveal_invariance_prereg.md."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from role_swap_probe import MID, MODEL_CHECKPOINT, MODEL_REVISION, SEED, unit


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/reveal_invariance_v1.json"
OUT = ROOT / "cache/reveal_invariance"
SNAPSHOT = ROOT / ("cache/hf/hub/models--Qwen--Qwen2.5-1.5B/snapshots/"
                   "8faed761d45a263340a0528343f099c05c9a4323")
# Format = timing * 2 + clause order. Every primary edge changes both factors.
PRIMARY_EDGES = ((0, 3), (1, 2), (2, 1), (3, 0))
TIMING_EDGES = ((0, 2), (2, 0), (1, 3), (3, 1))
CLAUSE_EDGES = ((0, 1), (1, 0), (2, 3), (3, 2))


@dataclass(frozen=True)
class Case:
    domain: str
    mechanism: str
    format: int
    world: int
    recipient: int
    text: str
    recipient_clause: str
    body_char: int
    bridge_char: int


def _words(s: str) -> Counter:
    return Counter(re.findall(r"\b\w+\b", s.lower()))


def make_cases(path: Path) -> tuple[list[Case], str]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    domains = doc["domains"]
    if len(domains) != 12 or len({d["id"] for d in domains}) != 12:
        raise ValueError("expected twelve unique domains")
    if Counter(d["mechanism"] for d in domains) != {"allegiance": 6, "competence": 6}:
        raise ValueError("mechanism halves are not balanced")
    cases = []
    for d in domains:
        if (d["a"] == d["b"] or len(d["a"]) != len(d["b"]) or
                any(not d[k].endswith(". ") for k in ("intro", "body", "helpful_fact", "harmful_fact")) or
                not doc["bridge"].endswith(". ") or
                not d["final_template"].endswith(".")):
            raise ValueError(f"broken sentence boundary or actor pair: {d['id']}")
        for timing in (0, 1):
            for clause_order in (0, 1):
                fmt = timing * 2 + clause_order
                for world in (0, 1):
                    helper = d["a"] if world == 0 else d["b"]
                    hinderer = d["b"] if world == 0 else d["a"]
                    clauses = [d["helpful_fact"].format(name=helper),
                               d["harmful_fact"].format(name=hinderer)]
                    if clause_order:
                        clauses.reverse()
                    reveal = "".join(clauses)
                    if timing == 0:
                        story = d["intro"] + reveal + d["body"]
                        body_char = len(story) - 2
                    else:
                        story = d["intro"] + d["body"] + reveal
                        body_char = len(d["intro"] + d["body"]) - 2
                    prefix = story + doc["bridge"]
                    for recipient in (0, 1):
                        target = d["a"] if recipient == 0 else d["b"]
                        text = prefix + d["final_template"].format(recipient=target)
                        matching_clauses = [c for c in clauses
                                            if re.search(r"\b" + re.escape(target) + r"\b", c)]
                        if len(matching_clauses) != 1:
                            raise ValueError(f"recipient clause is ambiguous: {d['id']}")
                        recipient_clause = matching_clauses[0]
                        if len(text) - text.index(reveal) <= 200:
                            raise ValueError(f"reveal entered local window: {d['id']}")
                        cases.append(Case(d["id"], d["mechanism"], fmt, world,
                                          recipient, text, recipient_clause,
                                          body_char, len(prefix) - 2))
        group = cases[-16:]  # [timing][clause order][world][recipient]
        for recipient in (0, 1):
            matched = [c for c in group if c.recipient == recipient]
            if (len({c.text[-200:] for c in matched}) != 1 or
                    len({len(c.text) for c in matched}) != 1 or
                    len({tuple(sorted(_words(c.text).items())) for c in matched}) != 1):
                raise ValueError(f"world/telling words differ: {d['id']}")
        late = group[8:]
        if len({c.text[:c.body_char + 1] for c in late}) != 1:
            raise ValueError(f"late pre-reveal text differs: {d['id']}")
        for fmt in range(4):
            for world in (0, 1):
                a, b = group[fmt * 4 + world * 2:fmt * 4 + world * 2 + 2]
                if a.text[:a.bridge_char + 1] != b.text[:b.bridge_char + 1]:
                    raise ValueError(f"recipient changes pre-handover text: {d['id']}")
    return cases, hashlib.sha256(raw).hexdigest()


def validate_tokens(cases: list[Case], tok, context_limit: int) -> list[tuple[int, int, int]]:
    rows = []
    for c in cases:
        enc = tok(c.text, return_offsets_mapping=True, add_special_tokens=True)
        if len(enc["input_ids"]) > context_limit:
            raise ValueError(f"passage exceeds context: {c.domain}")
        indexes = []
        for char in (len(c.text) - 1, c.bridge_char, c.body_char):
            hits = [i for i, (a, b) in enumerate(enc["offset_mapping"]) if a <= char < b]
            if len(hits) != 1:
                raise ValueError(f"readout maps to {len(hits)} tokens: {c.domain}")
            indexes.append(hits[0])
        final, bridge, body = indexes
        rows.append((len(enc["input_ids"]), final, enc["input_ids"][final],
                     bridge, tuple(enc["input_ids"][:bridge + 1]),
                     body, tuple(enc["input_ids"][:body + 1])))
    for di in range(12):
        group = rows[di * 16:di * 16 + 16]
        if len({x[:3] for x in group}) != 1:
            raise ValueError(f"final token signature differs: domain {di}")
        for fmt in range(4):
            for world in (0, 1):
                a, b = group[fmt * 4 + world * 2:fmt * 4 + world * 2 + 2]
                if a[3:5] != b[3:5]:
                    raise ValueError(f"recipient changes bridge prefix: {di}, {fmt}, {world}")
        if len({x[5:] for x in group[8:]}) != 1:
            raise ValueError(f"late pre-reveal token prefix differs: domain {di}")
    return [(x[1], x[3], x[5]) for x in rows]


def extract(snapshot: Path, out: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    import torch
    import transformers
    from lsx.model import LM

    out.mkdir(parents=True, exist_ok=True)
    cases, grid_hash = make_cases(GRID)
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    lm = LM.from_pretrained(str(snapshot), device="cuda", dtype=torch.float16,
                            local_files_only=True)
    context_limit = int(lm.model.config.max_position_embeddings)
    indices = validate_tokens(cases, lm.tok, context_limit)
    finals, bridges, bodies = [], [], []
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
                final, bridge, body = saved["final"], saved["bridge"], saved["body"]
            if any(x.shape != expected_shape or not np.isfinite(x).all()
                   for x in (final, bridge, body)):
                raise ValueError(f"broken checkpoint arrays: {path}")
        else:
            ff, pp, bb = [], [], []
            for j, case in enumerate(group):
                hs, offsets = lm.residuals(case.text)
                hits = []
                for char in (len(case.text) - 1, case.bridge_char, case.body_char):
                    found = [k for k, (a, b) in enumerate(offsets) if a <= char < b]
                    if len(found) != 1:
                        raise ValueError(f"readout offset changed: {case.domain}")
                    hits.append(found[0])
                if tuple(hits) != indices[di * 16 + j]:
                    raise ValueError(f"readout index changed: {case.domain}")
                ff.append(hs[:, hits[0], :].numpy().copy())
                pp.append(hs[:, hits[1], :].numpy().copy())
                bb.append(hs[:, hits[2], :].numpy().copy())
                del hs
            final = np.stack(ff).reshape(expected_shape)
            bridge = np.stack(pp).reshape(expected_shape)
            body = np.stack(bb).reshape(expected_shape)
            if any(not np.isfinite(x).all() for x in (final, bridge, body)):
                raise ValueError(f"nonfinite activations: {group[0].domain}")
            if not np.all(final[:, :, :, :, 0, :] == final[:1, :1, :1, :1, 0, :]):
                raise ValueError(f"layer-0 final token differs: {group[0].domain}")
            if not np.array_equal(bridge[:, :, :, 0], bridge[:, :, :, 1]):
                raise ValueError(f"recipient changes pre-handover state: {group[0].domain}")
            if not np.all(body[1] == body[1, :1, :1, :1]):
                raise ValueError(f"late pre-reveal state differs: {group[0].domain}")
            np.savez_compressed(path, final=final, bridge=bridge, body=body,
                                domain=group[0].domain, grid_hash=grid_hash,
                                script_hash=script_hash,
                                token_indices=np.asarray(indices[di * 16:di * 16 + 16]))
            print(f"extracted {di + 1}/12: {group[0].domain}", flush=True)
        finals.append(final)
        bridges.append(bridge)
        bodies.append(body)
    stacks = tuple(np.stack(rows) for rows in (finals, bridges, bodies))
    provenance = {"model_checkpoint": MODEL_CHECKPOINT, "model_revision": MODEL_REVISION,
                  "device": "cuda", "dtype": "float16", "grid_sha256": grid_hash,
                  "script_sha256": script_hash, "torch": torch.__version__,
                  "transformers": transformers.__version__, "context_limit": context_limit,
                  **{name + "_sha256": hashlib.sha256(arr.tobytes()).hexdigest()
                     for name, arr in zip(("final", "bridge", "body"), stacks)}}
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return stacks


def load_cached(out: Path) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    cases, grid_hash = make_cases(GRID)
    provenance = json.loads((out / "provenance.json").read_text())
    if (provenance["grid_sha256"] != grid_hash or
            provenance["model_revision"] != MODEL_REVISION or
            provenance["script_sha256"] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
        raise ValueError("stale extraction provenance")
    by_name = {name: [] for name in ("final", "bridge", "body")}
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


def interaction(states: np.ndarray) -> np.ndarray:
    if states.ndim != 6 or states.shape[:4] != (12, 4, 2, 2):
        raise ValueError("expected domain x format x world x recipient x layer x width")
    return unit((states[:, :, 0, 0] - states[:, :, 1, 0]) -
                (states[:, :, 0, 1] - states[:, :, 1, 1]))


def cross_scores(train: np.ndarray, test: np.ndarray) -> np.ndarray:
    if train.shape != test.shape or train.ndim != 3 or train.shape[0] != 12:
        raise ValueError("expected matching domain x layer x width arrays")
    scores = np.empty(train.shape[:2], dtype=float)
    for d in range(12):
        direction = unit(train[np.arange(12) != d].mean(axis=0))
        margin = np.einsum("ld,ld->l", test[d], direction)
        scores[d] = (margin > 1e-12) + .5 * (np.abs(margin) <= 1e-12)
    return scores


def lexical_baseline(cases: list[Case], *, mode: str) -> float:
    if len(cases) != 192:
        raise ValueError("lexical baseline requires the full grid")
    if mode == "local":
        rows = [Counter(c.text[-200:][i:i + 3]
                        for i in range(len(c.text[-200:]) - 2)) for c in cases]
    elif mode == "whole":
        rows = [_words(c.text) for c in cases]
    elif mode == "recipient_clause":
        rows = [_words(c.recipient_clause) for c in cases]
    else:
        raise ValueError(mode)
    vocab = sorted(set().union(*(set(row) for row in rows)))
    vectors = np.array([[row.get(term, 0) for term in vocab] for row in rows],
                       dtype=np.float32).reshape(12, 4, 2, 2, 1, -1)
    state = interaction(vectors)
    return float(np.stack([cross_scores(state[:, src], state[:, dst])
                           for src, dst in PRIMARY_EDGES]).mean())


def score(stacks: tuple[np.ndarray, np.ndarray, np.ndarray], *, n_null: int = 1000,
          n_boot: int = 2000) -> dict:
    final, bridge, body = stacks
    if any(x.shape != final.shape for x in (bridge, body)) or final.shape[:5] != (12, 2, 2, 2, 2):
        raise ValueError("stack shape mismatch")
    if max(MID) >= final.shape[5]:
        raise ValueError("registered layers missing")
    if not np.all(final[:, :, :, :, :, 0, :] == final[:, :1, :1, :1, :1, 0, :]):
        raise ValueError("layer-0 final null failed")
    if not np.array_equal(bridge[:, :, :, :, 0], bridge[:, :, :, :, 1]):
        raise ValueError("pre-handover recipient null failed")
    if not np.all(body[:, 1] == body[:, 1, :1, :1, :1]):
        raise ValueError("late pre-reveal null failed")
    # Flatten [timing][clause order] into the registered format index.
    f = final.reshape(12, 4, 2, 2, *final.shape[-2:])
    p = bridge.reshape(12, 4, 2, 2, *bridge.shape[-2:])
    state = interaction(f)
    arms = {f"{src}_to_{dst}": cross_scores(state[:, src], state[:, dst])
            for src in range(4) for dst in range(4)}
    primary = np.stack([arms[f"{src}_to_{dst}"] for src, dst in PRIMARY_EDGES], axis=1)
    observed = float(primary[:, :, list(MID)].mean())
    zero = np.zeros_like(state[:, 0])
    exact = {"pre_handover": cross_scores(interaction(p)[:, 0], interaction(p)[:, 3]),
             "no_world": cross_scores(zero, zero)}
    if (any(not np.all(x[:, 0] == .5) for x in arms.values()) or
            any(x.mean() != .5 for x in exact.values())):
        raise ValueError("exact-null arm failed")
    cases, _ = make_cases(GRID)
    lexical = {"local_200_char_trigrams": lexical_baseline(cases, mode="local"),
               "full_word_bag": lexical_baseline(cases, mode="whole"),
               "recipient_clause_word_bag": lexical_baseline(cases, mode="recipient_clause")}
    if any(lexical[x] != .5 for x in ("local_200_char_trigrams", "full_word_bag")):
        raise ValueError(f"lexical null failed: {lexical}")
    rng = np.random.default_rng(SEED + 6)
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
    early_world = np.linalg.norm(body[:, 0, :, 0] - body[:, 0, :, 1], axis=-1)
    late_world = np.linalg.norm(body[:, 1, :, 0] - body[:, 1, :, 1], axis=-1)
    mechanism = np.array([d["mechanism"] for d in json.loads(GRID.read_text())["domains"]])
    report = {
        "n_domains": 12, "n_passages": 192, "mid_layers": list(MID),
        "arms": {name: {"mid": float(s[:, list(MID)].mean()),
                         "curve": list(map(float, s.mean(axis=0)))}
                 for name, s in arms.items()},
        "primary_edges": [list(x) for x in PRIMARY_EDGES],
        "timing_only_edges": [list(x) for x in TIMING_EDGES],
        "clause_only_edges": [list(x) for x in CLAUSE_EDGES],
        "primary_mid": observed,
        "primary_curve": list(map(float, primary.mean(axis=(0, 1)))),
        "primary_bootstrap_ci95": list(map(float, np.quantile(boot, [.025, .975]))),
        "mechanism_halves_mid": {m: float(primary[mechanism == m][:, :, list(MID)].mean())
                                 for m in ("allegiance", "competence")},
        "exact_arms": {k: float(v.mean()) for k, v in exact.items()},
        "lexical_baselines": lexical,
        "body_world_displacement_mid": {
            "early": float(early_world[..., list(MID)].mean()),
            "late": float(late_world[..., list(MID)].mean()),
        },
        "permutation": {"draws": n_null, "mean": float(np.mean(perm)),
                        "q95": float(np.quantile(perm, .95)),
                        "p_ge_observed": (1 + sum(x >= observed for x in perm)) / (n_null + 1)},
        "random_direction": {"draws": n_null, "mean": float(np.mean(random)),
                             "q025_q975": list(map(float, np.quantile(random, [.025, .975])))},
    }
    return report


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    args = ap.parse_args()
    rng = np.random.default_rng(37)
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
                      "mechanism_halves_mid": report["mechanism_halves_mid"],
                      "exact_arms": report["exact_arms"],
                      "lexical_baselines": report["lexical_baselines"],
                      "body_world_displacement_mid": report["body_world_displacement_mid"],
                      "permutation": report["permutation"],
                      "random_direction": report["random_direction"],
                      "self_test": calibration}, indent=2))


if __name__ == "__main__":
    main()
