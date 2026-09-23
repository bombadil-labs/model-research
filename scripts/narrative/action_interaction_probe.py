"""Reverse the final handover to test an actor-goal x action interaction."""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re

import numpy as np

from role_swap_probe import (Case, MID, MODEL_CHECKPOINT, MODEL_REVISION, SEED,
                             heldout_scores, load_acts, make_grid, unit,
                             validate_token_pairs)


ROOT = Path(__file__).resolve().parents[2]
GRIDS = {"goal": "role_swap_v1.json", "neutral": "role_swap_neutral_v1.json"}
SNAPSHOT = ROOT / ("cache/hf/hub/models--Qwen--Qwen2.5-1.5B/snapshots/"
                   "8faed761d45a263340a0528343f099c05c9a4323")
OUT = ROOT / "cache/action_interaction"


def reverse_cases(grid: Path) -> tuple[list[Case], list[Case], str, list[int]]:
    forward, digest = make_grid(grid)
    doc = json.loads(grid.read_text())
    reverse, pre_chars = [], []
    for i, case in enumerate(forward):
        d = doc["domains"][i // 4]
        old = f"{d['giver']} handed the {d['object']} to {d['recipient']}."
        new = f"{d['recipient']} handed the {d['object']} to {d['giver']}."
        if not case.text.endswith(old):
            raise ValueError(f"forward target changed: {case.domain}")
        prefix = case.text[:-len(old)]
        if not prefix.endswith("again. "):
            raise ValueError(f"pre-action bridge changed: {case.domain}")
        reverse.append(Case(case.domain, case.order, case.label, prefix + new))
        pre_chars.append(len(prefix) - 2)  # the period before the separating space
    for i in range(0, len(reverse), 2):
        a, b = reverse[i:i + 2]
        words = lambda s: Counter(re.findall(r"\b\w+\b", s.lower()))
        if (a.text[-200:] != b.text[-200:] or len(a.text) != len(b.text)
                or words(a.text) != words(b.text)):
            raise ValueError(f"reverse pair is not matched: {a.domain}, order {a.order}")
        if pre_chars[i] != pre_chars[i + 1]:
            raise ValueError("pre-action character offset differs within pair")
        if any(len(c.text) - c.text.index(doc["bridge"]) <= 200 for c in (a, b)):
            raise ValueError(f"reverse cue entered local window: {a.domain}, order {a.order}")
    return forward, reverse, digest, pre_chars


def validate_tokens(forward: list[Case], reverse: list[Case], pre_chars: list[int], tok,
                    context_limit: int) -> list[int]:
    validate_token_pairs(reverse, tok)
    pre_indices = []
    for f, r, ch in zip(forward, reverse, pre_chars):
        ef = tok(f.text, return_offsets_mapping=True, add_special_tokens=True)
        er = tok(r.text, return_offsets_mapping=True, add_special_tokens=True)
        if len(er["input_ids"]) > context_limit:
            raise ValueError(f"reverse passage exceeds context: {r.domain}")
        jf = [j for j, (a, b) in enumerate(ef["offset_mapping"]) if a <= ch < b]
        jr = [j for j, (a, b) in enumerate(er["offset_mapping"]) if a <= ch < b]
        if len(jf) != 1 or jf != jr or ef["input_ids"][:jf[0] + 1] != er["input_ids"][:jr[0] + 1]:
            raise ValueError(f"forward/reverse differ before action: {r.domain}, {r.order}, {r.label}")
        pre_indices.append(jr[0])
    for i in range(0, len(reverse), 2):
        if pre_indices[i] != pre_indices[i + 1]:
            raise ValueError(f"pre-action token position differs: {reverse[i].domain}")
    return pre_indices


def extract(snapshot: Path, out: Path) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    import torch
    import transformers
    from lsx.model import LM

    out.mkdir(parents=True, exist_ok=True)
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    lm = LM.from_pretrained(str(snapshot), device="cuda", dtype=torch.float16,
                            local_files_only=True)
    context_limit = int(lm.model.config.max_position_embeddings)
    result = {}
    for kind, filename in GRIDS.items():
        forward, reverse, digest, pre_chars = reverse_cases(ROOT / "research/narrative/prompts" / filename)
        pre_indices = validate_tokens(forward, reverse, pre_chars, lm.tok, context_limit)
        folder = out / kind
        folder.mkdir(parents=True, exist_ok=True)
        rev_rows, pre_rows = [], []
        for di in range(12):
            path = folder / f"domain_{di:02d}.npz"
            group = reverse[di * 4:di * 4 + 4]
            if path.exists():
                with np.load(path) as saved:
                    if (saved["grid_hash"].item() != digest or
                            saved["script_hash"].item() != script_hash or
                            saved["domain"].item() != group[0].domain):
                        raise ValueError(f"stale checkpoint {path}")
                    rev, pre = saved["reverse"], saved["pre"]
            else:
                rr, pp = [], []
                for j, case in enumerate(group):
                    hs, offsets = lm.residuals(case.text)
                    final_char = len(case.text) - 1
                    final = [k for k, (a, b) in enumerate(offsets) if a <= final_char < b]
                    prior = [k for k, (a, b) in enumerate(offsets)
                             if a <= pre_chars[di * 4 + j] < b]
                    if len(final) != 1 or prior != [pre_indices[di * 4 + j]]:
                        raise ValueError(f"readout offset changed: {case.domain}")
                    rr.append(hs[:, final[0], :].numpy().copy())
                    pp.append(hs[:, prior[0], :].numpy().copy())
                    del hs
                rev = np.stack(rr).reshape(2, 2, lm.n_layers + 1, lm.d_model)
                pre = np.stack(pp).reshape(2, 2, lm.n_layers + 1, lm.d_model)
                if not np.isfinite(rev).all() or not np.isfinite(pre).all():
                    raise ValueError("nonfinite activation")
                if not np.array_equal(rev[:, 0, 0], rev[:, 1, 0]):
                    raise ValueError("reverse layer-0 pair differs")
                if not np.array_equal(pre[:, 0, 0], pre[:, 1, 0]):
                    raise ValueError("pre-action layer-0 pair differs")
                np.savez_compressed(path, reverse=rev, pre=pre, domain=group[0].domain,
                                    grid_hash=digest, script_hash=script_hash)
                print(f"extracted {kind} {di + 1}/12: {group[0].domain}", flush=True)
            rev_rows.append(rev)
            pre_rows.append(pre)
        result[kind] = np.stack(rev_rows), np.stack(pre_rows)
        prov = {"model_checkpoint": MODEL_CHECKPOINT, "model_revision": MODEL_REVISION,
                "device": "cuda", "dtype": "float16", "grid_sha256": digest,
                "script_sha256": script_hash, "torch": torch.__version__,
                "transformers": transformers.__version__, "context_limit": context_limit,
                "reverse_sha256": hashlib.sha256(result[kind][0].tobytes()).hexdigest(),
                "pre_sha256": hashlib.sha256(result[kind][1].tobytes()).hexdigest()}
        (folder / "provenance.json").write_text(json.dumps(prov, indent=2) + "\n")
    return result


def load_cached(out: Path) -> dict[str, tuple[np.ndarray, np.ndarray]]:
    result = {}
    for kind, filename in GRIDS.items():
        forward, reverse, digest, _ = reverse_cases(ROOT / "research/narrative/prompts" / filename)
        folder = out / kind
        prov = json.loads((folder / "provenance.json").read_text())
        if (prov["grid_sha256"] != digest or prov["model_revision"] != MODEL_REVISION):
            raise ValueError(f"stale {kind} provenance")
        rev_rows, pre_rows = [], []
        for di in range(12):
            with np.load(folder / f"domain_{di:02d}.npz") as saved:
                if (saved["grid_hash"].item() != digest or
                        saved["script_hash"].item() != prov["script_sha256"] or
                        saved["domain"].item() != forward[di * 4].domain):
                    raise ValueError(f"stale checkpoint: {kind} domain {di}")
                rev_rows.append(saved["reverse"])
                pre_rows.append(saved["pre"])
        rev, pre = np.stack(rev_rows), np.stack(pre_rows)
        if (hashlib.sha256(rev.tobytes()).hexdigest() != prov["reverse_sha256"] or
                hashlib.sha256(pre.tobytes()).hexdigest() != prov["pre_sha256"]):
            raise ValueError(f"activation digest mismatch: {kind}")
        result[kind] = rev, pre
    return result


def cross_scores(train: np.ndarray, test: np.ndarray) -> np.ndarray:
    if train.shape != test.shape or train.shape[:2] != (12, 2):
        raise ValueError("cross-score shape mismatch")
    scores = np.empty(train.shape[:3], dtype=float)
    for d in range(12):
        direction = unit(train[np.arange(12) != d].mean(axis=(0, 1)))
        margin = np.einsum("old,ld->ol", test[d], direction)
        scores[d] = (margin > 1e-12) + .5 * (np.abs(margin) <= 1e-12)
    return scores


def score(forward: dict[str, np.ndarray], extracted: dict[str, tuple[np.ndarray, np.ndarray]],
          n_null: int = 1000, n_boot: int = 2000) -> dict:
    goal_f, neut_f = forward["goal"], forward["neutral"]
    goal_r, goal_pre = extracted["goal"]
    neut_r, neut_pre = extracted["neutral"]
    if not (goal_f.shape == neut_f.shape == goal_r.shape == neut_r.shape == goal_pre.shape == neut_pre.shape
            and goal_f.shape[:3] == (12, 2, 2)):
        raise ValueError("activation shape mismatch")
    if max(MID) >= goal_f.shape[3]:
        raise ValueError("registered layers missing")
    for name, x in [("goal forward", goal_f), ("goal reverse", goal_r),
                    ("neutral forward", neut_f), ("neutral reverse", neut_r),
                    ("goal pre", goal_pre), ("neutral pre", neut_pre)]:
        if not np.array_equal(x[:, :, 0, 0], x[:, :, 1, 0]):
            raise ValueError(f"{name} layer 0 is not an exact null")
    delta = lambda x: x[:, :, 0] - x[:, :, 1]
    gf, gr, gp = map(lambda x: unit(delta(x)), (goal_f, goal_r, goal_pre))
    nf, nr, np_ = map(lambda x: unit(delta(x)), (neut_f, neut_r, neut_pre))
    gi = unit(delta(goal_f) - delta(goal_r))
    ni = unit(delta(neut_f) - delta(neut_r))
    arms = {
        "goal_forward_replication": cross_scores(gf, gf),
        "goal_reverse_event": cross_scores(gf, -gr),
        "goal_reverse_unflipped": cross_scores(gf, gr),
        "goal_pre_action_binding": cross_scores(gf, gp),
        "goal_action_interaction": cross_scores(gi, gi),
        "goal_to_neutral_action_interaction": cross_scores(gi, ni),
        "neutral_action_interaction": cross_scores(ni, ni),
        "neutral_forward_replication": cross_scores(nf, nf),
        "neutral_pre_action_binding": cross_scores(nf, np_),
        "no_action": heldout_scores(unit(delta(goal_f) - delta(goal_f)))[0],
    }
    if any(not np.all(arm[:, :, 0] == .5) for arm in arms.values()):
        raise ValueError("layer-0 control failed")
    rng = np.random.default_rng(SEED + 2)
    primary = arms["goal_action_interaction"]
    control = arms["goal_to_neutral_action_interaction"]
    observed = float(primary[:, :, list(MID)].mean())
    boot_primary, boot_gap = [], []
    for _ in range(n_boot):
        idx = rng.integers(0, 12, size=12)
        boot_primary.append(float(primary[idx][:, :, list(MID)].mean()))
        boot_gap.append(float((primary[idx] - control[idx])[:, :, list(MID)].mean()))
    null, random = [], []
    for _ in range(n_null):
        sign = rng.choice([-1, 1], size=12)
        null.append(float(heldout_scores(gi * sign[:, None, None, None])[0][:, :, list(MID)].mean()))
        direction = unit(rng.standard_normal((gi.shape[2], gi.shape[-1])))
        margin = np.einsum("nold,ld->nol", gi, direction)
        random.append(float(((margin[:, :, list(MID)] > 1e-12) +
                             .5 * (np.abs(margin[:, :, list(MID)]) <= 1e-12)).mean()))
    return {
        "n_domains": 12, "n_pairs_per_action_per_grid": 24, "mid_layers": list(MID),
        "arms": {name: {"mid": float(s[:, :, list(MID)].mean()),
                         "curve": list(map(float, s.mean(axis=(0, 1)))),
                         "layer14_domain_scores": list(map(float, s[:, :, 14].mean(axis=1)))}
                 for name, s in arms.items()},
        "primary_bootstrap_ci95": list(map(float, np.quantile(boot_primary, [.025, .975]))),
        "goal_minus_neutral_interaction_mid": float((primary - control)[:, :, list(MID)].mean()),
        "goal_minus_neutral_bootstrap_ci95": list(map(float, np.quantile(boot_gap, [.025, .975]))),
        "permutation": {"draws": n_null, "mean": float(np.mean(null)),
                        "q95": float(np.quantile(null, .95)),
                        "p_ge_observed": (1 + sum(v >= observed for v in null)) / (n_null + 1)},
        "random_direction": {"draws": n_null, "mean": float(np.mean(random)),
                             "q025_q975": list(map(float, np.quantile(random, [.025, .975])))},
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--snapshot", type=Path, default=SNAPSHOT)
    args = ap.parse_args()
    rng = np.random.default_rng(23)
    signal = unit(rng.normal(size=(12, 2, 29, 16)) * .2 + np.eye(16)[0])
    noise = unit(rng.normal(size=(12, 2, 29, 16)))
    calibration = {"signal": float(heldout_scores(signal)[0][:, :, list(MID)].mean()),
                   "noise": float(heldout_scores(noise)[0][:, :, list(MID)].mean())}
    if calibration["signal"] < .95 or not .35 <= calibration["noise"] <= .65:
        raise ValueError(f"scorer calibration failed: {calibration}")
    extracted = load_cached(OUT) if args.score_only else extract(args.snapshot, OUT)
    forward = {}
    for kind, filename in GRIDS.items():
        cases, digest = make_grid(ROOT / "research/narrative/prompts" / filename)
        f, _ = load_acts(cases, digest, ROOT / "cache" / ("role_swap" if kind == "goal" else "role_swap_neutral"))
        forward[kind] = f
    report = score(forward, extracted)
    report["self_test"] = calibration
    (OUT / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"arms_mid": {k: v["mid"] for k, v in report["arms"].items()},
                      "primary_bootstrap_ci95": report["primary_bootstrap_ci95"],
                      "goal_minus_neutral_interaction_mid": report["goal_minus_neutral_interaction_mid"],
                      "goal_minus_neutral_bootstrap_ci95": report["goal_minus_neutral_bootstrap_ci95"],
                      "permutation": report["permutation"],
                      "random_direction": report["random_direction"],
                      "self_test": calibration}, indent=2))


if __name__ == "__main__":
    main()
