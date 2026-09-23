"""Fixed-predicate group-goal x recipient interaction; see goal_switch_prereg.md."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from role_swap_probe import MID, MODEL_CHECKPOINT, MODEL_REVISION, SEED, heldout_scores, unit


ROOT = Path(__file__).resolve().parents[2]
GRID = ROOT / "research/narrative/prompts/goal_switch_v1.json"
OUT = ROOT / "cache/goal_switch"
SNAPSHOT = ROOT / ("cache/hf/hub/models--Qwen--Qwen2.5-1.5B/snapshots/"
                   "8faed761d45a263340a0528343f099c05c9a4323")


@dataclass(frozen=True)
class Case:
    domain: str
    order: int
    goal: int
    recipient: int
    text: str
    pre_char: int


def make_cases(path: Path) -> tuple[dict[str, list[Case]], str]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    domains = doc["domains"]
    if len(domains) != 12 or len({d["id"] for d in domains}) != 12:
        raise ValueError("expected 12 unique domains")
    grids = {"linked": [], "rotated": []}
    for di, d in enumerate(domains):
        tasks = [f"{d['a']} planned to {d['task_a']}.",
                 f"{d['b']} planned to {d['task_b']}."]
        for kind, source in (("linked", d), ("rotated", domains[(di + 1) % 12])):
            for order in (0, 1):
                first, second = (tasks if order == 0 else tasks[::-1])
                for goal in (0, 1):
                    desired, rejected = ((source["goal_a"], source["goal_b"]) if goal == 0
                                         else (source["goal_b"], source["goal_a"]))
                    prefix = (doc["lead"] + first + " " + second + " " +
                              f"The group needed {desired}, not {rejected}. " + doc["bridge"])
                    if not prefix.endswith("again. "):
                        raise ValueError("bridge ending changed")
                    for recipient in (0, 1):
                        target = (f"A courier handed the {d['object']} to " +
                                  (d["a"] if recipient == 0 else d["b"]) + ".")
                        text = prefix + target
                        if len(text) - text.index(doc["bridge"]) <= 200:
                            raise ValueError(f"goal cue entered local window: {d['id']}")
                        grids[kind].append(Case(d["id"], order, goal, recipient,
                                                text, len(prefix) - 2))
            # Eight cases per domain, ordered [order][goal][recipient].
            group = grids[kind][di * 8:di * 8 + 8]
            for order in (0, 1):
                for recipient in (0, 1):
                    a, b = group[order * 4 + recipient], group[order * 4 + 2 + recipient]
                    words = lambda s: Counter(re.findall(r"\b\w+\b", s.lower()))
                    if (a.text[-200:] != b.text[-200:] or len(a.text) != len(b.text)
                            or words(a.text) != words(b.text)):
                        raise ValueError(f"goal pair not matched: {d['id']}, {kind}, {order}, {recipient}")
    return grids, hashlib.sha256(raw).hexdigest()


def validate_tokens(grids: dict[str, list[Case]], tok, context_limit: int) -> dict[str, list[tuple[int, int]]]:
    indices = {}
    for kind, cases in grids.items():
        signatures, rows = [], []
        for c in cases:
            enc = tok(c.text, return_offsets_mapping=True, add_special_tokens=True)
            if len(enc["input_ids"]) > context_limit:
                raise ValueError(f"passage exceeds context: {c.domain}")
            hits = lambda char: [i for i, (a, b) in enumerate(enc["offset_mapping"])
                                 if a <= char < b]
            final, pre = hits(len(c.text) - 1), hits(c.pre_char)
            if len(final) != 1 or len(pre) != 1:
                raise ValueError(f"readout does not map to one token: {c.domain}")
            signatures.append((len(enc["input_ids"]), final[0], enc["input_ids"][final[0]],
                               pre[0], tuple(enc["input_ids"][:pre[0] + 1])))
            rows.append((final[0], pre[0]))
        for di in range(12):
            for order in (0, 1):
                q = signatures[di * 8 + order * 4:di * 8 + order * 4 + 4]
                if len({s[:3] for s in q}) != 1:
                    raise ValueError(f"final token position differs: {kind}, {di}, {order}")
                for goal in (0, 1):
                    if q[goal * 2][3:] != q[goal * 2 + 1][3:]:
                        raise ValueError(f"recipient changes pre-action prefix: {kind}, {di}, {order}")
        indices[kind] = rows
        indices[kind + "_signatures"] = signatures
    for a, b in zip(indices["linked_signatures"], indices["rotated_signatures"]):
        if a[:3] != b[:3]:
            raise ValueError("linked/rotated final token signature differs")
    return {kind: indices[kind] for kind in grids}


def extract(snapshot: Path, out: Path) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    import torch
    import transformers
    from lsx.model import LM

    out.mkdir(parents=True, exist_ok=True)
    grids, grid_hash = make_cases(GRID)
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    lm = LM.from_pretrained(str(snapshot), device="cuda", dtype=torch.float16,
                            local_files_only=True)
    context_limit = int(lm.model.config.max_position_embeddings)
    indices = validate_tokens(grids, lm.tok, context_limit)
    result = {}
    for kind, cases in grids.items():
        folder = out / kind
        folder.mkdir(parents=True, exist_ok=True)
        finals, pres = [], []
        for di in range(12):
            path = folder / f"domain_{di:02d}.npz"
            group = cases[di * 8:di * 8 + 8]
            if path.exists():
                with np.load(path) as saved:
                    if (saved["grid_hash"].item() != grid_hash or
                            saved["script_hash"].item() != script_hash or
                            saved["kind"].item() != kind or
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
                    if (f, p) != ([indices[kind][di * 8 + j][0]],
                                  [indices[kind][di * 8 + j][1]]):
                        raise ValueError(f"readout offset changed: {case.domain}")
                    ff.append(hs[:, f[0], :].numpy().copy())
                    pp.append(hs[:, p[0], :].numpy().copy())
                    del hs
                final = np.stack(ff).reshape(2, 2, 2, lm.n_layers + 1, lm.d_model)
                pre = np.stack(pp).reshape(2, 2, 2, lm.n_layers + 1, lm.d_model)
                if not np.isfinite(final).all() or not np.isfinite(pre).all():
                    raise ValueError("nonfinite activation")
                if not np.array_equal(pre[:, :, 0], pre[:, :, 1]):
                    raise ValueError(f"recipient changed pre-action state: {kind}, {group[0].domain}")
                if not np.all(final[:, :, :, 0, :] == final[:, :1, :1, 0, :]):
                    raise ValueError(f"layer-0 final token differs: {kind}, {group[0].domain}")
                np.savez_compressed(path, final=final, pre=pre, kind=kind,
                                    domain=group[0].domain, grid_hash=grid_hash,
                                    script_hash=script_hash)
                print(f"extracted {kind} {di + 1}/12: {group[0].domain}", flush=True)
            finals.append(final)
            pres.append(pre)
        result[kind] = np.stack(finals), np.stack(pres)
        prov = {"model_checkpoint": MODEL_CHECKPOINT, "model_revision": MODEL_REVISION,
                "device": "cuda", "dtype": "float16", "grid_sha256": grid_hash,
                "script_sha256": script_hash, "torch": torch.__version__,
                "transformers": transformers.__version__, "context_limit": context_limit,
                "final_sha256": hashlib.sha256(result[kind][0].tobytes()).hexdigest(),
                "pre_sha256": hashlib.sha256(result[kind][1].tobytes()).hexdigest()}
        (folder / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n")
    return result


def load_cached(out: Path) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    grids, grid_hash = make_cases(GRID)
    result = {}
    for kind, cases in grids.items():
        folder = out / kind
        prov = json.loads((folder / "provenance.json").read_text())
        if prov["grid_sha256"] != grid_hash or prov["model_revision"] != MODEL_REVISION:
            raise ValueError(f"stale {kind} provenance")
        finals, pres = [], []
        for di in range(12):
            with np.load(folder / f"domain_{di:02d}.npz") as saved:
                if (saved["grid_hash"].item() != grid_hash or
                        saved["script_hash"].item() != prov["script_sha256"] or
                        saved["kind"].item() != kind or
                        saved["domain"].item() != cases[di * 8].domain):
                    raise ValueError(f"stale checkpoint: {kind}, {di}")
                finals.append(saved["final"])
                pres.append(saved["pre"])
        final, pre = np.stack(finals), np.stack(pres)
        if (hashlib.sha256(final.tobytes()).hexdigest() != prov["final_sha256"] or
                hashlib.sha256(pre.tobytes()).hexdigest() != prov["pre_sha256"]):
            raise ValueError(f"activation digest mismatch: {kind}")
        result[kind] = final, pre
    return result


def interaction(states: np.ndarray) -> np.ndarray:
    if states.ndim != 6 or states.shape[:4] != (12, 2, 2, 2):
        raise ValueError("expected domain x task order x goal x recipient x layer x width")
    return unit((states[:, :, 0, 0] - states[:, :, 1, 0]) -
                (states[:, :, 0, 1] - states[:, :, 1, 1]))


def cross_scores(train: np.ndarray, test: np.ndarray) -> np.ndarray:
    if train.shape != test.shape or train.shape[:2] != (12, 2):
        raise ValueError("cross-score shape mismatch")
    scores = np.empty(train.shape[:3], dtype=float)
    for d in range(12):
        direction = unit(train[np.arange(12) != d].mean(axis=(0, 1)))
        margin = np.einsum("old,ld->ol", test[d], direction)
        scores[d] = (margin > 1e-12) + .5 * (np.abs(margin) <= 1e-12)
    return scores


def score(stacks: dict[str, tuple[np.ndarray, np.ndarray]], *, n_null: int = 1000,
          n_boot: int = 2000) -> dict:
    lf, lp = stacks["linked"]
    rf, rp = stacks["rotated"]
    if lf.shape != rf.shape or lp.shape != rp.shape or lf.shape != lp.shape:
        raise ValueError("stack shape mismatch")
    if max(MID) >= lf.shape[4]:
        raise ValueError("registered layers missing")
    for name, final, pre in (("linked", lf, lp), ("rotated", rf, rp)):
        if not np.array_equal(pre[:, :, :, 0], pre[:, :, :, 1]):
            raise ValueError(f"{name} pre-action recipient null failed")
        if not np.all(final[:, :, :, :, 0, :] == final[:, :, :1, :1, 0, :]):
            raise ValueError(f"{name} layer-0 final null failed")
    li, ri = interaction(lf), interaction(rf)
    arms = {"linked": cross_scores(li, li), "linked_to_rotated": cross_scores(li, ri),
            "rotated": cross_scores(ri, ri),
            "pre_action": heldout_scores(interaction(lp))[0],
            "no_goal": heldout_scores(unit(li - li))[0]}
    if any(not np.all(x[:, :, 0] == .5) for x in arms.values()):
        raise ValueError("layer-0 control failed")
    if arms["pre_action"].mean() != .5 or arms["no_goal"].mean() != .5:
        raise ValueError("exact-null arm failed")
    rng = np.random.default_rng(SEED + 3)
    treatment, control = arms["linked"], arms["linked_to_rotated"]
    observed = float(treatment[:, :, list(MID)].mean())
    boot_treatment, boot_gap = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, 12, size=12)
        boot_treatment.append(float(treatment[idx][:, :, list(MID)].mean()))
        boot_gap.append(float((treatment[idx] - control[idx])[:, :, list(MID)].mean()))
    perm, random = [], []
    for _ in range(n_null):
        sign = rng.choice([-1, 1], size=12)
        perm.append(float(heldout_scores(li * sign[:, None, None, None])[0][:, :, list(MID)].mean()))
        direction = unit(rng.standard_normal((li.shape[2], li.shape[-1])))
        margin = np.einsum("nold,ld->nol", li, direction)
        random.append(float(((margin[:, :, list(MID)] > 1e-12) +
                             .5 * (np.abs(margin[:, :, list(MID)]) <= 1e-12)).mean()))
    return {
        "n_domains": 12, "n_passages_per_grid": 96, "mid_layers": list(MID),
        "arms": {name: {"mid": float(s[:, :, list(MID)].mean()),
                         "curve": list(map(float, s.mean(axis=(0, 1)))),
                         "layer14_domain_scores": list(map(float, s[:, :, 14].mean(axis=1)))}
                 for name, s in arms.items()},
        "linked_bootstrap_ci95": list(map(float, np.quantile(boot_treatment, [.025, .975]))),
        "linked_minus_rotated_mid": float((treatment - control)[:, :, list(MID)].mean()),
        "linked_minus_rotated_bootstrap_ci95": list(map(float, np.quantile(boot_gap, [.025, .975]))),
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
    rng = np.random.default_rng(29)
    signal = unit(rng.normal(size=(12, 2, 29, 16)) * .2 + np.eye(16)[0])
    noise = unit(rng.normal(size=(12, 2, 29, 16)))
    calibration = {"signal": float(heldout_scores(signal)[0][:, :, list(MID)].mean()),
                   "noise": float(heldout_scores(noise)[0][:, :, list(MID)].mean())}
    if calibration["signal"] < .95 or not .35 <= calibration["noise"] <= .65:
        raise ValueError(f"scorer calibration failed: {calibration}")
    stacks = load_cached(OUT) if args.score_only else extract(args.snapshot, OUT)
    report = score(stacks)
    report["self_test"] = calibration
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"arms_mid": {k: v["mid"] for k, v in report["arms"].items()},
                      "linked_bootstrap_ci95": report["linked_bootstrap_ci95"],
                      "linked_minus_rotated_mid": report["linked_minus_rotated_mid"],
                      "linked_minus_rotated_bootstrap_ci95": report["linked_minus_rotated_bootstrap_ci95"],
                      "permutation": report["permutation"],
                      "random_direction": report["random_direction"],
                      "self_test": calibration}, indent=2))


if __name__ == "__main__":
    main()
