"""Held-out-tale Propp function recognition. See the frozen preregistration note.

Raw tales and exact checkpoint provenance stay in ignored cache/. Run extraction under flock.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
import platform
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer


EXPECTED_MD5 = "8c3219aa8dbd85f3f94a8a0a616780ce"
LABELS = ("A", "C", "H", "I", "K")
MID = tuple(range(10, 19))
SEED = 260922


@dataclass(frozen=True)
class Event:
    tale: int
    label: str
    end: int  # exclusive character offset in story body
    position: float
    text_window: str


@dataclass(frozen=True)
class Tale:
    name: str
    body: str


def read_corpus(path: Path) -> tuple[list[Tale], list[Event], str]:
    digest = hashlib.md5(path.read_bytes()).hexdigest()
    if digest != EXPECTED_MD5:
        raise ValueError(f"archive MD5 mismatch: {digest}")
    tales: list[Tale] = []
    events: list[Event] = []
    with zipfile.ZipFile(path) as archive:
        names = sorted(n for n in archive.namelist() if n.startswith("data/") and n.endswith(".sty"))
        if len(names) != 15:
            raise ValueError(f"expected 15 tales, found {len(names)}")
        for name in names:
            root = ET.fromstring(archive.read(name))
            char = root.find("./rep[@id='edu.mit.story.char']/desc")
            if char is None or char.text is None:
                raise ValueError(f"missing raw character text: {name}")
            # Story Workbench's XML pretty-print adds one newline around the raw text.
            raw = char.text[1:-1]
            if len(raw) != int(char.attrib["len"]):
                raise ValueError(f"character count mismatch: {name}")
            body_regions = [x for x in root.findall("./rep[@id='edu.mit.story.text']/desc")
                            if (x.text or "").strip() == "TEXT"]
            if len(body_regions) != 1:
                raise ValueError(f"expected one body region: {name}")
            region = body_regions[0]
            start, length = int(region.attrib["off"]), int(region.attrib["len"])
            if start < 0 or length <= 0 or start + length > len(raw):
                raise ValueError(f"body region out of bounds: {name}")
            body = raw[start:start + length]
            ti = len(tales)
            tales.append(Tale(name=name, body=body))
            functions = root.findall("./rep[@id='edu.mit.semantics.rep.function']/desc")
            for item in functions:
                value = item.text or ""
                fields = value.split("|", 1)
                if len(fields) != 2:
                    raise ValueError(f"malformed function: {name}")
                family = fields[0][:1]
                if family not in LABELS or not fields[1].startswith("ACTUAL:"):
                    continue
                off, span_len = int(item.attrib["off"]), int(item.attrib["len"])
                end = off + span_len - start
                if off < start or span_len <= 0 or end > len(body):
                    raise ValueError(f"function signal outside body: {name} {fields[0]}")
                if not body[end - 1].strip():
                    raise ValueError(f"function signal ends on whitespace: {name} {fields[0]}")
                events.append(Event(tale=ti, label=family, end=end,
                                    position=end / len(body),
                                    text_window=body[max(0, end - 200):end]))
    counts = {label: sum(e.label == label for e in events) for label in LABELS}
    if counts != {"A": 13, "C": 7, "H": 9, "I": 12, "K": 12}:
        raise ValueError(f"unexpected event counts: {counts}")
    return tales, events, digest


def token_for_signal(offsets: list[tuple[int, int]], end: int) -> int:
    hits = [i for i, (a, b) in enumerate(offsets) if a <= end - 1 < b]
    if len(hits) != 1:
        raise ValueError(f"signal character {end - 1} maps to {len(hits)} tokens")
    return hits[0]


def extract(tales: list[Tale], events: list[Event], archive_md5: str,
            model_name: str, out_dir: Path, *, local_window: bool = False) -> np.ndarray:
    import torch
    import transformers
    from lsx.model import LM

    out_dir.mkdir(parents=True, exist_ok=True)
    script_sha256 = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    model = LM.from_pretrained(model_name, device="cuda", dtype=torch.float16)
    if model.n_layers < max(MID):
        raise ValueError("model has too few layers for preregistered mid band")
    result: list[np.ndarray] = []
    for ti, tale in enumerate(tales):
        path = out_dir / f"tale_{ti:02d}.npz"
        local = [e for e in events if e.tale == ti]
        if path.exists():
            saved = np.load(path)
            if saved["name"].item() != tale.name or saved["archive_md5"].item() != archive_md5:
                raise ValueError(f"checkpoint identity mismatch: {path}")
            if "script_sha256" not in saved or saved["script_sha256"].item() != script_sha256:
                raise ValueError(f"checkpoint code version mismatch: {path}")
            arr = saved["acts"]
            if arr.shape != (len(local), model.n_layers + 1, model.d_model):
                raise ValueError(f"checkpoint shape mismatch: {path}")
        else:
            if local_window:
                vectors = []
                indices = []
                for event in local:
                    hs, offsets = model.residuals(event.text_window)
                    idx = token_for_signal(offsets, len(event.text_window))
                    vectors.append(hs[:, idx, :].numpy().copy())
                    indices.append(idx)
                    del hs
                arr = np.stack(vectors)
            else:
                hs, offsets = model.residuals(tale.body)
                indices = [token_for_signal(offsets, e.end) for e in local]
                arr = hs[:, indices, :].permute(1, 0, 2).numpy().copy()
                del hs
            if not np.isfinite(arr).all():
                raise ValueError(f"nonfinite activations: {tale.name}")
            np.savez_compressed(path, acts=arr, name=tale.name, archive_md5=archive_md5,
                                script_sha256=script_sha256,
                                char_ends=np.asarray([e.end for e in local]),
                                token_indices=np.asarray(indices))
            print(f"extracted {ti + 1}/15: {tale.name}; {len(local)} signals", flush=True)
            torch.cuda.empty_cache()
        result.append(arr)
    acts = np.concatenate(result, axis=0)
    provenance = {
        "model": model_name, "device": "cuda", "dtype": "float16",
        "archive_md5": archive_md5, "readout": "last token containing final signal character",
        "context": "preceding 200 characters" if local_window else "complete causal story prefix",
        "layers": list(range(model.n_layers + 1)), "last_layer": "post-final-norm",
        "tokenizer_padding": model.tok.padding_side,
        "torch": torch.__version__, "transformers": transformers.__version__,
        "python": platform.python_version(), "acts_sha256": hashlib.sha256(acts.tobytes()).hexdigest(),
        "script_sha256": script_sha256,
    }
    (out_dir / "provenance.json").write_text(json.dumps(provenance, indent=2) + "\n")
    return acts


def load_acts(tales: list[Tale], events: list[Event], archive_md5: str,
              out_dir: Path) -> np.ndarray:
    rows = []
    provenance_path = out_dir / "provenance.json"
    provenance = json.loads(provenance_path.read_text()) if provenance_path.exists() else None
    if provenance and provenance["archive_md5"] != archive_md5:
        raise ValueError("provenance source mismatch")
    for ti, tale in enumerate(tales):
        with np.load(out_dir / f"tale_{ti:02d}.npz") as saved:
            if saved["name"].item() != tale.name or saved["archive_md5"].item() != archive_md5:
                raise ValueError("checkpoint identity mismatch")
            local = [e for e in events if e.tale == ti]
            if not np.array_equal(saved["char_ends"], [e.end for e in local]):
                raise ValueError("checkpoint signal positions mismatch")
            if provenance and "script_sha256" in provenance:
                if "script_sha256" not in saved or saved["script_sha256"].item() != provenance["script_sha256"]:
                    raise ValueError("checkpoint code version mismatch")
            rows.append(saved["acts"])
    acts = np.concatenate(rows, axis=0)
    if provenance and hashlib.sha256(acts.tobytes()).hexdigest() != provenance["acts_sha256"]:
        raise ValueError("activation digest mismatch")
    return acts


def unit(x: np.ndarray) -> np.ndarray:
    return x / np.maximum(np.linalg.norm(x, axis=-1, keepdims=True), 1e-12)


def centroids(x: np.ndarray, y: np.ndarray) -> np.ndarray:
    return unit(np.stack([x[y == label].mean(axis=0) for label in LABELS]))


def bacc(y: np.ndarray, pred: np.ndarray) -> float:
    return float(np.mean([np.mean(pred[y == label] == label) for label in LABELS]))


def score(acts: np.ndarray, events: list[Event], n_perm: int = 1000,
          n_boot: int = 2000) -> dict:
    y = np.asarray([e.label for e in events])
    tale = np.asarray([e.tale for e in events])
    pos = np.asarray([e.position for e in events])
    windows = [e.text_window for e in events]
    n_layers = acts.shape[1]
    if max(MID) >= n_layers:
        raise ValueError("missing preregistered mid layers")
    folds = [(np.flatnonzero(tale != t), np.flatnonzero(tale == t)) for t in range(15)]
    prepared = []
    for train, test in folds:
        vec = TfidfVectorizer(ngram_range=(1, 2), lowercase=True)
        x_train = vec.fit_transform([windows[i] for i in train]).toarray()
        x_test = vec.transform([windows[i] for i in test]).toarray()
        mean = acts[train].mean(axis=0)
        prepared.append((unit(acts[train] - mean), unit(acts[test] - mean),
                         x_train, unit(x_test)))

    def predict(labels: np.ndarray, layers: tuple[int, ...], with_controls: bool = True):
        pred_model = np.empty((len(layers), len(y)), dtype="<U1")
        pred_text = np.empty(len(y), dtype="<U1") if with_controls else None
        pred_position = np.empty(len(y), dtype="<U1") if with_controls else None
        pred_combined = np.empty(len(y), dtype="<U1") if with_controls else None
        for (train, test), (xtr, xte, text_train, text_test) in zip(folds, prepared):
            missing = [label for label in LABELS if not np.any(labels[train] == label)]
            if missing:
                raise ValueError(f"training fold lacks classes {missing}; held-out tale {int(tale[test[0]])}")
            if with_controls:
                text_cent = centroids(text_train, labels[train])
                text_score = text_test @ text_cent.T
                pos_cent = np.asarray([pos[train][labels[train] == label].mean() for label in LABELS])
                pos_score = 1 - np.abs(pos[test, None] - pos_cent[None, :])
                pred_text[test] = np.asarray(LABELS)[text_score.argmax(axis=1)]
                pred_position[test] = np.asarray(LABELS)[pos_score.argmax(axis=1)]
                pred_combined[test] = np.asarray(LABELS)[(0.5 * text_score + 0.5 * pos_score).argmax(axis=1)]
            class_cent = centroids(xtr[:, layers], labels[train])  # [class, layer, dim]
            model_scores = np.einsum("tld,cld->ltc", xte[:, layers], class_cent)
            pred_model[:, test] = np.asarray(LABELS)[model_scores.argmax(axis=-1)]
        return pred_model, pred_text, pred_position, pred_combined

    layers = tuple(range(n_layers))
    pred, p_text, p_pos, p_combo = predict(y, layers)
    curve = [bacc(y, row) for row in pred]
    controls = {"text": bacc(y, p_text), "position": bacc(y, p_pos),
                "combined": bacc(y, p_combo), "layer_0": curve[0]}
    mid = float(np.mean([curve[i] for i in MID]))
    strongest = max(controls[k] for k in ("text", "position", "combined"))
    gain = mid - strongest

    rng = np.random.default_rng(SEED)
    null = []
    for _ in range(n_perm):
        perm = y.copy()
        for _, test in folds:
            perm[test] = rng.permutation(perm[test])
        p_perm, _, _, _ = predict(perm, MID, with_controls=False)
        null.append(float(np.mean([bacc(perm, row) for row in p_perm])))
    p_value = (1 + sum(v >= mid for v in null)) / (len(null) + 1)

    boot = []
    boot_over_layer0 = []
    for _ in range(n_boot):
        sampled_tales = rng.integers(0, 15, size=15)
        ix = np.concatenate([np.flatnonzero(tale == t) for t in sampled_tales])
        if any(not np.any(y[ix] == lab) for lab in LABELS):
            continue
        model_bacc = float(np.mean([bacc(y[ix], pred[layer, ix]) for layer in MID]))
        base_bacc = max(bacc(y[ix], p[ix]) for p in (p_text, p_pos, p_combo))
        boot.append(model_bacc - base_bacc)
        boot_over_layer0.append(model_bacc - bacc(y[ix], pred[0, ix]))

    anchor = 14
    return {
        "n_tales": 15, "n_events": len(events), "class_counts": {lab: int(sum(y == lab)) for lab in LABELS},
        "model_curve_balanced_accuracy": curve,
        "primary_mid_layers": list(MID), "primary_mid_balanced_accuracy": mid,
        "controls_balanced_accuracy": controls, "primary_gain_over_strongest_baseline": gain,
        "permutation": {"draws": n_perm, "seed": SEED, "p_ge_observed": p_value,
                        "null_mean": float(np.mean(null)), "null_q95": float(np.quantile(null, .95))},
        "tale_bootstrap_gain_ci95": list(map(float, np.quantile(boot, [.025, .975]))),
        "mid_gain_over_layer_0": mid - curve[0],
        "tale_bootstrap_gain_over_layer_0_ci95": list(map(float, np.quantile(boot_over_layer0, [.025, .975]))),
        "tale_bootstrap_valid_draws": len(boot),
        "mid_layer_event_predictions": [pred[layer].tolist() for layer in MID],
        "anchor_layer_14": {
            "per_class_recall": {lab: float(np.mean(pred[anchor, y == lab] == lab)) for lab in LABELS},
            "per_tale_accuracy": {str(t): float(np.mean(pred[anchor, tale == t] == y[tale == t]))
                                  for t in range(15)},
            "confusion": {lab: {other: int(np.sum((y == lab) & (pred[anchor] == other)))
                                for other in LABELS} for lab in LABELS},
        },
    }


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--archive", type=Path, required=True, help="inner MIT ProppLearner ZIP")
    ap.add_argument("--cache", type=Path, default=Path("cache/propp"))
    ap.add_argument("--model", help="exact local checkpoint, required for extraction")
    ap.add_argument("--score-only", action="store_true")
    ap.add_argument("--local-window", action="store_true", help="exploratory 200-character context ablation")
    ap.add_argument("--quick", action="store_true", help="instrument shakeout: 10 null, 20 bootstrap")
    args = ap.parse_args()
    tales, events, digest = read_corpus(args.archive)
    if args.local_window:
        args.cache = args.cache / "local_window"
    if args.score_only:
        acts = load_acts(tales, events, digest, args.cache)
    else:
        if not args.model:
            ap.error("--model is required for extraction")
        acts = extract(tales, events, digest, args.model, args.cache,
                       local_window=args.local_window)
    report = score(acts, events, n_perm=10 if args.quick else 1000,
                   n_boot=20 if args.quick else 2000)
    args.cache.mkdir(parents=True, exist_ok=True)
    (args.cache / "report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({k: report[k] for k in ("n_events", "primary_mid_balanced_accuracy",
                                                   "controls_balanced_accuracy",
                                                   "primary_gain_over_strongest_baseline",
                                                   "permutation", "tale_bootstrap_gain_ci95")}, indent=2))


if __name__ == "__main__":
    main()
