"""Controlled role-swap activation probe. Design: role_swap_prereg.md."""
from __future__ import annotations

import argparse
from collections import Counter
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import re

import numpy as np


MID = tuple(range(10, 19))
SEED = 260923
MODEL_CHECKPOINT = "Qwen/Qwen2.5-1.5B"
MODEL_REVISION = "8faed761d45a263340a0528343f099c05c9a4323"


@dataclass(frozen=True)
class Case:
    domain: str
    order: int
    label: str
    text: str


def make_grid(path: Path) -> tuple[list[Case], str]:
    raw = path.read_bytes()
    doc = json.loads(raw)
    if len(doc["domains"]) != 12:
        raise ValueError("expected 12 domains")
    if len({d["id"] for d in doc["domains"]}) != 12:
        raise ValueError("domain ids must be unique")
    cases: list[Case] = []
    for domain in doc["domains"]:
        giver, recipient = domain["giver"], domain["recipient"]
        target = f"{giver} handed the {domain['object']} to {recipient}."
        for order in (0, 1):
            pair = []
            for label in ("helps", "harms"):
                helper = recipient if label == "helps" else giver
                harmer = giver if label == "helps" else recipient
                help_line = domain["help"].format(actor=helper)
                harm_line = domain["harm"].format(actor=harmer)
                first, second = (help_line, harm_line) if order == 0 else (harm_line, help_line)
                text = doc["lead"] + first + " " + second + " " + doc["bridge"] + target
                pair.append(Case(domain["id"], order, label, text))
            a, b = pair
            if a.text[-200:] != b.text[-200:]:
                raise ValueError(f"local wording differs: {domain['id']} order {order}")
            if len(a.text) != len(b.text):
                raise ValueError(f"character length differs: {domain['id']} order {order}")
            words = lambda s: Counter(re.findall(r"\b\w+\b", s.lower()))
            if words(a.text) != words(b.text):
                raise ValueError(f"word multiset differs: {domain['id']} order {order}")
            if any(len(c.text) - c.text.index(doc["bridge"]) <= 200 for c in pair):
                raise ValueError(f"role cue entered local window: {domain['id']} order {order}")
            cases.extend(pair)
    return cases, hashlib.sha256(raw).hexdigest()


def validate_token_pairs(cases: list[Case], tok) -> list[tuple[int, int]]:
    offsets = []
    for i in range(0, len(cases), 2):
        pair = cases[i:i + 2]
        if (pair[0].domain, pair[0].order, pair[0].label, pair[1].label) != (
            pair[1].domain, pair[1].order, "helps", "harms"
        ):
            raise ValueError("grid pair ordering changed")
        encoded = [tok(c.text, return_offsets_mapping=True, add_special_tokens=True) for c in pair]
        last = []
        for c, enc in zip(pair, encoded):
            if not c.text.endswith("."):
                raise ValueError("target must end in a period")
            hits = [j for j, (a, b) in enumerate(enc["offset_mapping"])
                    if a <= len(c.text) - 1 < b]
            if len(hits) != 1:
                raise ValueError("readout period does not map to exactly one token")
            last.append((len(enc["input_ids"]), hits[0], enc["input_ids"][hits[0]]))
        if last[0] != last[1]:
            raise ValueError(f"pair tokenization differs: {pair[0].domain}, order {pair[0].order}: {last}")
        offsets.append((last[0][0], last[0][1]))
    return offsets


def extract(cases: list[Case], grid_hash: str, snapshot: Path, out_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    import torch
    import transformers
    from lsx.model import LM

    out_dir.mkdir(parents=True, exist_ok=True)
    script_hash = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    lm = LM.from_pretrained(str(snapshot), device="cuda", dtype=torch.float16, local_files_only=True)
    validate_token_pairs(cases, lm.tok)
    full_rows, local_rows = [], []
    for di in range(12):
        path = out_dir / f"domain_{di:02d}.npz"
        group = cases[di * 4:di * 4 + 4]
        if path.exists():
            with np.load(path) as saved:
                if (saved["grid_hash"].item() != grid_hash or
                        saved["script_hash"].item() != script_hash or
                        saved["domain"].item() != group[0].domain):
                    raise ValueError(f"stale checkpoint {path}")
                full = saved["full"]
                local = saved["local"]
        else:
            full_list, local_list = [], []
            for case in group:
                for text, target in ((case.text, full_list), (case.text[-200:], local_list)):
                    hs, offsets = lm.residuals(text)
                    hits = [j for j, (a, b) in enumerate(offsets) if a <= len(text) - 1 < b]
                    if len(hits) != 1:
                        raise ValueError("readout token mapping failed")
                    target.append(hs[:, hits[0], :].numpy().copy())
                    del hs
            full = np.stack(full_list).reshape(2, 2, lm.n_layers + 1, lm.d_model)
            local = np.stack(local_list).reshape(2, 2, lm.n_layers + 1, lm.d_model)
            if not np.isfinite(full).all() or not np.isfinite(local).all():
                raise ValueError("nonfinite activation")
            if not np.array_equal(local[:, 0], local[:, 1]):
                raise ValueError("no-cue pair does not match bit-exactly")
            if not np.array_equal(full[:, 0, 0], full[:, 1, 0]):
                raise ValueError("layer-0 pair is not identical")
            np.savez_compressed(path, full=full, local=local, domain=group[0].domain,
                                grid_hash=grid_hash, script_hash=script_hash)
            print(f"extracted {di + 1}/12: {group[0].domain}", flush=True)
        full_rows.append(full)
        local_rows.append(local)
    full_acts, local_acts = np.stack(full_rows), np.stack(local_rows)
    provenance = {
        "model_checkpoint": MODEL_CHECKPOINT, "model_revision": MODEL_REVISION,
        "device": "cuda", "dtype": "float16", "grid_sha256": grid_hash,
        "script_sha256": script_hash, "torch": torch.__version__,
        "transformers": transformers.__version__, "readout": "final period token",
        "last_layer": "post-final-norm",
        "full_acts_sha256": hashlib.sha256(full_acts.tobytes()).hexdigest(),
        "local_acts_sha256": hashlib.sha256(local_acts.tobytes()).hexdigest(),
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return full_acts, local_acts


def load_acts(cases: list[Case], grid_hash: str, out_dir: Path) -> tuple[np.ndarray, np.ndarray]:
    prov = json.loads((out_dir / "provenance.json").read_text())
    if prov["grid_sha256"] != grid_hash:
        raise ValueError("grid hash mismatch")
    full_rows, local_rows = [], []
    for di in range(12):
        with np.load(out_dir / f"domain_{di:02d}.npz") as saved:
            if (saved["grid_hash"].item() != grid_hash or
                    saved["script_hash"].item() != prov["script_sha256"] or
                    saved["domain"].item() != cases[di * 4].domain):
                raise ValueError("checkpoint identity mismatch")
            full_rows.append(saved["full"])
            local_rows.append(saved["local"])
    full, local = np.stack(full_rows), np.stack(local_rows)
    if hashlib.sha256(full.tobytes()).hexdigest() != prov["full_acts_sha256"]:
        raise ValueError("full activation digest mismatch")
    if hashlib.sha256(local.tobytes()).hexdigest() != prov["local_acts_sha256"]:
        raise ValueError("local activation digest mismatch")
    return full, local


def unit(x: np.ndarray) -> np.ndarray:
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)


def heldout_scores(u: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    # u: [domain, order, layer, hidden], positive orientation means helps minus harms.
    n_domain, n_order, n_layer, _ = u.shape
    scores = np.empty((n_domain, n_order, n_layer))
    margins = np.empty_like(scores)
    for d in range(n_domain):
        direction = unit(np.mean(u[np.arange(n_domain) != d], axis=(0, 1)))
        margin = np.einsum("old,ld->ol", u[d], direction)
        margins[d] = margin
        scores[d] = (margin > 1e-12).astype(float) + 0.5 * (np.abs(margin) <= 1e-12)
    return scores, margins


def score(full: np.ndarray, local: np.ndarray, *, n_null: int = 1000,
          n_boot: int = 2000) -> dict:
    if full.shape != local.shape or full.shape[:3] != (12, 2, 2):
        raise ValueError("expected 12 domains x 2 orders x 2 labels")
    n_layers = full.shape[3]
    if max(MID) >= n_layers:
        raise ValueError("missing preregistered layers")
    if not np.array_equal(local[:, :, 0], local[:, :, 1]):
        raise ValueError("local-only pair differs")
    if not np.array_equal(full[:, :, 0, 0], full[:, :, 1, 0]):
        raise ValueError("layer 0 pair differs")
    delta = full[:, :, 0] - full[:, :, 1]
    u = unit(delta)
    treatment, margins = heldout_scores(u)
    local_treatment, _ = heldout_scores(unit(local[:, :, 0] - local[:, :, 1]))
    curve = treatment.mean(axis=(0, 1))
    local_curve = local_treatment.mean(axis=(0, 1))
    mid = float(np.mean(curve[list(MID)]))
    rng = np.random.default_rng(SEED)
    permuted = []
    for _ in range(n_null):
        sign = rng.choice([-1, 1], size=12)
        p, _ = heldout_scores(u * sign[:, None, None, None])
        permuted.append(float(np.mean(p[:, :, list(MID)])))
    random_scores = []
    for _ in range(n_null):
        direction = unit(rng.standard_normal((n_layers, u.shape[-1])))
        margin = np.einsum("nold,ld->nol", u, direction)
        random_scores.append(float(np.mean((margin[:, :, list(MID)] > 1e-12).astype(float) +
                                           0.5 * (np.abs(margin[:, :, list(MID)]) <= 1e-12))))
    boot = []
    for _ in range(n_boot):
        idx = rng.integers(0, 12, size=12)
        boot.append(float(np.mean(treatment[idx][:, :, list(MID)])))
    return {
        "n_domains": 12, "n_pairs": 24, "n_passages": 48,
        "full_layer_curve_pair_accuracy": list(map(float, curve)),
        "local_only_full_layer_curve_pair_accuracy": list(map(float, local_curve)),
        "mid_layers": list(MID), "mid_pair_accuracy": mid,
        "mid_tale_bootstrap_ci95": list(map(float, np.quantile(boot, [.025, .975]))),
        "permutation": {"draws": n_null, "seed": SEED,
                        "mean": float(np.mean(permuted)), "q95": float(np.quantile(permuted, .95)),
                        "p_ge_observed": (1 + sum(x >= mid for x in permuted)) / (n_null + 1)},
        "random_direction": {"draws": n_null, "mean": float(np.mean(random_scores)),
                             "q025_q975": list(map(float, np.quantile(random_scores, [.025, .975])))},
        "local_only_pair_accuracy": float(np.mean(local_curve[list(MID)])),
        "layer_0_pair_accuracy": float(curve[0]),
        "layer_14_per_domain_pair_accuracy": list(map(float, treatment[:, :, 14].mean(axis=1))),
        "layer_14_per_domain_margins": margins[:, :, 14].tolist(),
    }


def self_test() -> dict:
    rng = np.random.default_rng(17)
    direction = unit(rng.standard_normal(16))
    signal = rng.standard_normal((12, 2, 29, 16)) * .2 + direction
    known, _ = heldout_scores(unit(signal))
    noise, _ = heldout_scores(unit(rng.standard_normal((12, 2, 29, 16))))
    return {"signal_mid": float(np.mean(known[:, :, list(MID)])),
            "noise_mid": float(np.mean(noise[:, :, list(MID)]))}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--grid", type=Path, default=Path("research/narrative/prompts/role_swap_v1.json"))
    ap.add_argument("--cache", type=Path, default=Path("cache/role_swap"))
    ap.add_argument("--model-snapshot", type=Path)
    ap.add_argument("--score-only", action="store_true")
    args = ap.parse_args()
    cases, grid_hash = make_grid(args.grid)
    calibration = self_test()
    if calibration["signal_mid"] < .95 or not .35 <= calibration["noise_mid"] <= .65:
        raise ValueError(f"scorer self-test failed: {calibration}")
    if args.score_only:
        full, local = load_acts(cases, grid_hash, args.cache)
    else:
        if args.model_snapshot is None:
            ap.error("--model-snapshot required for extraction")
        full, local = extract(cases, grid_hash, args.model_snapshot, args.cache)
    report = score(full, local)
    report["self_test"] = calibration
    args.cache.mkdir(parents=True, exist_ok=True)
    (args.cache / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("mid_pair_accuracy", "mid_tale_bootstrap_ci95",
                                                   "permutation", "random_direction", "self_test")}, indent=2))


if __name__ == "__main__":
    main()
