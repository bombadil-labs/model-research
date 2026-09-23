"""Consequence mapping across clause order; see consequence_order_prereg.md."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from goal_switch_probe import cross_scores
from role_swap_probe import MID, MODEL_CHECKPOINT, MODEL_REVISION, SEED, unit


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/consequence_order_v1.json"
OUT = ROOT / "cache/consequence_order"
SNAPSHOT = ROOT / ("cache/hf/hub/models--Qwen--Qwen2.5-1.5B/snapshots/"
                   "8faed761d45a263340a0528343f099c05c9a4323")


@dataclass(frozen=True)
class Case:
    domain: str
    task_order: int
    clause_order: int
    mapping: int
    recipient: int
    text: str
    pre_char: int


def make_cases(path: Path) -> tuple[list[Case], str]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    domains = doc["domains"]
    if len(domains) != 12 or len({d["id"] for d in domains}) != 12:
        raise ValueError("expected 12 unique domains")
    if sum(d["a_has_original_active_task"] for d in domains) != 6:
        raise ValueError("active-plan assignment is not balanced")
    cases = []
    words = lambda s: Counter(re.findall(r"\b\w+\b", s.lower()))
    for d in domains:
        tasks = [f"{d['a']} planned to {d['task_a']}.",
                 f"{d['b']} planned to {d['task_b']}."]
        conditions = [d["condition_a"], d["condition_b"]]
        for task_order in (0, 1):
            first, second = tasks if task_order == 0 else tasks[::-1]
            for clause_order in (0, 1):
                for mapping in (0, 1):
                    outcomes = ([doc["safe_outcome"], doc["danger_outcome"]] if mapping == 0
                                else [doc["danger_outcome"], doc["safe_outcome"]])
                    clauses = [doc["report_clause"].format(condition=conditions[k],
                                                              outcome=outcomes[k])
                               for k in (0, 1)]
                    if clause_order:
                        clauses.reverse()
                    report = doc["report_intro"] + " ".join(clauses) + " "
                    if (sum(bool(re.search(r"\bsafe\b", c)) for c in clauses) != 1 or
                            sum(bool(re.search(r"\bdanger\b", c)) for c in clauses) != 1 or
                            any(re.search(r"\b(safe|danger)\b", x) for x in conditions)):
                        raise ValueError("valence words do not occur only in report outcomes")
                    prefix = (doc["lead"] + doc["town_goal"] +
                              first + " " + second + " " + report + doc["bridge"])
                    if not prefix.endswith("again. "):
                        raise ValueError("bridge ending changed")
                    for recipient in (0, 1):
                        target = (f"A courier handed the {d['object']} to " +
                                  (d["a"] if recipient == 0 else d["b"]) + ".")
                        text = prefix + target
                        if len(text) - text.index(report) <= 200:
                            raise ValueError(f"report entered local window: {d['id']}")
                        cases.append(Case(d["id"], task_order, clause_order,
                                          mapping, recipient, text, len(prefix) - 2))
        group = cases[-16:]
        # [task order][clause order][mapping][recipient]
        for task_order in (0, 1):
            block = group[task_order * 8:task_order * 8 + 8]
            for recipient in (0, 1):
                matched = [block[clause * 4 + mapping * 2 + recipient]
                           for clause in (0, 1) for mapping in (0, 1)]
                if (len({c.text[-200:] for c in matched}) != 1 or
                        len({len(c.text) for c in matched}) != 1 or
                        len({tuple(sorted(words(c.text).items())) for c in matched}) != 1):
                    raise ValueError(f"mapping/clause text mismatch: {d['id']}")
    return cases, hashlib.sha256(raw).hexdigest()


def validate_tokens(cases: list[Case], tok, context_limit: int) -> list[tuple[int, int]]:
    signatures, indices = [], []
    for c in cases:
        enc = tok(c.text, return_offsets_mapping=True, add_special_tokens=True)
        if len(enc["input_ids"]) > context_limit:
            raise ValueError(f"passage exceeds context: {c.domain}")
        hits = lambda char: [i for i, (a, b) in enumerate(enc["offset_mapping"])
                             if a <= char < b]
        final, pre = hits(len(c.text) - 1), hits(c.pre_char)
        if len(final) != 1 or len(pre) != 1:
            raise ValueError(f"readout does not map to one token: {c.domain}")
        signatures.append((len(enc["input_ids"]), final[0],
                           enc["input_ids"][final[0]], pre[0],
                           tuple(enc["input_ids"][:pre[0] + 1])))
        indices.append((final[0], pre[0]))
    for di in range(12):
        group = signatures[di * 16:di * 16 + 16]
        for task_order in (0, 1):
            block = group[task_order * 8:task_order * 8 + 8]
            if len({s[:3] for s in block}) != 1:
                raise ValueError(f"final token signature differs: {di}, {task_order}")
            for clause in (0, 1):
                for mapping in (0, 1):
                    a, b = block[clause * 4 + mapping * 2:clause * 4 + mapping * 2 + 2]
                    if a[3:] != b[3:]:
                        raise ValueError(f"recipient changes pre-action prefix: {di}")
    return indices


def extract(snapshot: Path, out: Path) -> tuple[np.ndarray, np.ndarray]:
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
    finals, pres = [], []
    for di in range(12):
        path = out / f"domain_{di:02d}.npz"
        group = cases[di * 16:di * 16 + 16]
        if path.exists():
            with np.load(path) as saved:
                if (saved["grid_hash"].item() != grid_hash or
                        saved["script_hash"].item() != script_hash or
                        saved["domain"].item() != group[0].domain):
                    raise ValueError(f"stale checkpoint {path}")
                final, pre = saved["final"], saved["pre"]
        else:
            ff, pp = [], []
            for j, case in enumerate(group):
                hs, offsets = lm.residuals(case.text)
                final_char = len(case.text) - 1
                f = [k for k, (a, b) in enumerate(offsets) if a <= final_char < b]
                p = [k for k, (a, b) in enumerate(offsets) if a <= case.pre_char < b]
                if (f, p) != ([indices[di * 16 + j][0]], [indices[di * 16 + j][1]]):
                    raise ValueError(f"readout offset changed: {case.domain}")
                ff.append(hs[:, f[0], :].numpy().copy())
                pp.append(hs[:, p[0], :].numpy().copy())
                del hs
            final = np.stack(ff).reshape(2, 2, 2, 2, lm.n_layers + 1, lm.d_model)
            pre = np.stack(pp).reshape(2, 2, 2, 2, lm.n_layers + 1, lm.d_model)
            if not np.isfinite(final).all() or not np.isfinite(pre).all():
                raise ValueError("nonfinite activation")
            if not np.array_equal(pre[:, :, :, 0], pre[:, :, :, 1]):
                raise ValueError(f"recipient changed pre-action state: {group[0].domain}")
            if not np.all(final[:, :, :, :, 0, :] == final[:1, :1, :1, :1, 0, :]):
                raise ValueError(f"layer-0 final token differs: {group[0].domain}")
            np.savez_compressed(path, final=final, pre=pre, domain=group[0].domain,
                                grid_hash=grid_hash, script_hash=script_hash)
            print(f"extracted {di + 1}/12: {group[0].domain}", flush=True)
        finals.append(final)
        pres.append(pre)
    final, pre = np.stack(finals), np.stack(pres)
    provenance = {"model_checkpoint": MODEL_CHECKPOINT,
                  "model_revision": MODEL_REVISION, "device": "cuda",
                  "dtype": "float16", "grid_sha256": grid_hash,
                  "script_sha256": script_hash, "torch": torch.__version__,
                  "transformers": transformers.__version__,
                  "context_limit": context_limit,
                  "final_sha256": hashlib.sha256(final.tobytes()).hexdigest(),
                  "pre_sha256": hashlib.sha256(pre.tobytes()).hexdigest()}
    (out / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return final, pre


def load_cached(out: Path) -> tuple[np.ndarray, np.ndarray]:
    cases, grid_hash = make_cases(GRID)
    provenance = json.loads((out / "provenance.json").read_text())
    if (provenance["grid_sha256"] != grid_hash or
            provenance["model_revision"] != MODEL_REVISION or
            provenance["script_sha256"] != hashlib.sha256(Path(__file__).read_bytes()).hexdigest()):
        raise ValueError("stale extraction provenance")
    finals, pres = [], []
    for di in range(12):
        with np.load(out / f"domain_{di:02d}.npz") as saved:
            if (saved["grid_hash"].item() != grid_hash or
                    saved["script_hash"].item() != provenance["script_sha256"] or
                    saved["domain"].item() != cases[di * 16].domain):
                raise ValueError(f"stale checkpoint: {di}")
            finals.append(saved["final"])
            pres.append(saved["pre"])
    final, pre = np.stack(finals), np.stack(pres)
    if (hashlib.sha256(final.tobytes()).hexdigest() != provenance["final_sha256"] or
            hashlib.sha256(pre.tobytes()).hexdigest() != provenance["pre_sha256"]):
        raise ValueError("activation digest mismatch")
    return final, pre


def interaction(states: np.ndarray) -> np.ndarray:
    if states.ndim != 7 or states.shape[:5] != (12, 2, 2, 2, 2):
        raise ValueError("expected domain x task order x clause order x mapping x recipient x layer x width")
    return unit((states[:, :, :, 0, 0] - states[:, :, :, 1, 0]) -
                (states[:, :, :, 0, 1] - states[:, :, :, 1, 1]))


def lexical_baseline(cases: list[Case], *, local: bool) -> float:
    if len(cases) != 192:
        raise ValueError("lexical baseline requires the complete grid")
    if local:
        rows = [Counter(c.text[-200:][i:i + 3]
                        for i in range(len(c.text[-200:]) - 2)) for c in cases]
    else:
        rows = [Counter(re.findall(r"\b\w+\b", c.text.lower())) for c in cases]
    vocab = sorted(set().union(*(set(row) for row in rows)))
    matrix = np.array([[row.get(term, 0) for term in vocab] for row in rows],
                      dtype=np.float32).reshape(12, 2, 2, 2, 2, 1, -1)
    state = interaction(matrix)
    a = cross_scores(state[:, :, 0], state[:, :, 1])
    b = cross_scores(state[:, :, 1], state[:, :, 0])
    return float(np.stack([a, b]).mean())


def score(stacks: tuple[np.ndarray, np.ndarray], *, n_null: int = 1000,
          n_boot: int = 2000) -> dict:
    final, pre = stacks
    if final.shape != pre.shape or final.shape[:5] != (12, 2, 2, 2, 2):
        raise ValueError("stack shape mismatch")
    if max(MID) >= final.shape[5]:
        raise ValueError("registered layers missing")
    if not np.array_equal(pre[:, :, :, :, 0], pre[:, :, :, :, 1]):
        raise ValueError("pre-action recipient null failed")
    if not np.all(final[:, :, :, :, :, 0, :] == final[:, :1, :1, :1, :1, 0, :]):
        raise ValueError("layer-0 final null failed")
    state = interaction(final)
    arms = {
        "within_clause_0": cross_scores(state[:, :, 0], state[:, :, 0]),
        "within_clause_1": cross_scores(state[:, :, 1], state[:, :, 1]),
        "clause_0_to_1": cross_scores(state[:, :, 0], state[:, :, 1]),
        "clause_1_to_0": cross_scores(state[:, :, 1], state[:, :, 0]),
    }
    zero = np.zeros_like(state[:, :, 0])
    arms.update({"pre_action": cross_scores(interaction(pre)[:, :, 0],
                                              interaction(pre)[:, :, 1]),
                 "no_mapping": cross_scores(zero, zero)})
    if any(not np.all(x[:, :, 0] == .5) for x in arms.values()):
        raise ValueError("layer-0 control failed")
    if any(arms[name].mean() != .5 for name in ("pre_action", "no_mapping")):
        raise ValueError("exact-null arm failed")
    cases, _ = make_cases(GRID)
    lexical = {"local_200_char_trigrams": lexical_baseline(cases, local=True),
               "full_word_bag": lexical_baseline(cases, local=False)}
    if any(x != .5 for x in lexical.values()):
        raise ValueError(f"lexical exact-null arm failed: {lexical}")
    primary = np.stack([arms["clause_0_to_1"], arms["clause_1_to_0"]], axis=1)
    observed = float(primary[:, :, :, list(MID)].mean())
    polarity = np.array([d["a_has_original_active_task"]
                         for d in json.loads(GRID.read_text())["domains"]], dtype=bool)
    if polarity.shape != (12,) or polarity.sum() != 6:
        raise ValueError("active-plan assignment is not balanced")
    rng = np.random.default_rng(SEED + 4)
    boot = []
    for _ in range(n_boot):
        idx = rng.integers(0, 12, size=12)
        boot.append(float(primary[idx][:, :, :, list(MID)].mean()))
    perm, random = [], []
    for _ in range(n_null):
        sign = rng.choice([-1, 1], size=12)
        shifted = state * sign[:, None, None, None, None]
        a = cross_scores(shifted[:, :, 0], shifted[:, :, 1])
        b = cross_scores(shifted[:, :, 1], shifted[:, :, 0])
        perm.append(float(np.stack([a, b], axis=1)[:, :, :, list(MID)].mean()))
        direction = unit(rng.standard_normal((state.shape[-2], state.shape[-1])))
        margin = np.einsum("norld,ld->norl", state, direction)
        random.append(float(((margin[:, :, :, list(MID)] > 1e-12) +
                             .5 * (np.abs(margin[:, :, :, list(MID)]) <= 1e-12)).mean()))
    return {
        "n_domains": 12, "n_passages": 192, "mid_layers": list(MID),
        "arms": {name: {"mid": float(s[:, :, list(MID)].mean()),
                         "curve": list(map(float, s.mean(axis=(0, 1))))}
                 for name, s in arms.items()},
        "lexical_baselines": lexical,
        "primary_cross_order_mid": observed,
        "primary_cross_order_curve": list(map(float, primary.mean(axis=(0, 1, 2)))),
        "polarity_halves_mid": {
            "active_A": float(primary[polarity][:, :, :, list(MID)].mean()),
            "restrictive_A": float(primary[~polarity][:, :, :, list(MID)].mean()),
        },
        "primary_bootstrap_ci95": list(map(float, np.quantile(boot, [.025, .975]))),
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
    rng = np.random.default_rng(31)
    signal = unit(rng.normal(size=(12, 2, 29, 16)) * .2 + np.eye(16)[0])
    noise = unit(rng.normal(size=(12, 2, 29, 16)))
    calibration = {"signal": float(cross_scores(signal, signal)[:, :, list(MID)].mean()),
                   "noise": float(cross_scores(noise, noise)[:, :, list(MID)].mean())}
    if calibration["signal"] < .95 or not .35 <= calibration["noise"] <= .65:
        raise ValueError(f"scorer calibration failed: {calibration}")
    stacks = load_cached(OUT) if args.score_only else extract(args.snapshot, OUT)
    report = score(stacks)
    report["self_test"] = calibration
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"arms_mid": {k: v["mid"] for k, v in report["arms"].items()},
                      "lexical_baselines": report["lexical_baselines"],
                      "primary_cross_order_mid": report["primary_cross_order_mid"],
                      "primary_bootstrap_ci95": report["primary_bootstrap_ci95"],
                      "permutation": report["permutation"],
                      "random_direction": report["random_direction"],
                      "self_test": calibration}, indent=2))


if __name__ == "__main__":
    main()
