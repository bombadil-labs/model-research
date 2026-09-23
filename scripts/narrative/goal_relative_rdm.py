"""Post-result geometry diagnostic for the fixed-plan probe; exploratory only."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path

import numpy as np

from goal_relative_probe import OUT, load_cached
from reveal_invariance_probe import PRIMARY_EDGES
from role_swap_probe import MID, SEED, unit


def effects(final: np.ndarray) -> dict[str, np.ndarray]:
    if final.ndim != 7 or final.shape[:5] != (12, 2, 2, 2, 2):
        raise ValueError("stack shape mismatch")
    f = final.reshape(12, 4, 2, 2, *final.shape[-2:])
    return {
        "interaction": unit((f[:, :, 0, 0] - f[:, :, 1, 0]) -
                            (f[:, :, 0, 1] - f[:, :, 1, 1])),
        "world_main": unit(((f[:, :, 0, 0] + f[:, :, 0, 1]) -
                            (f[:, :, 1, 0] + f[:, :, 1, 1])) / 2),
        "recipient_main": unit(((f[:, :, 0, 0] + f[:, :, 1, 0]) -
                                (f[:, :, 0, 1] + f[:, :, 1, 1])) / 2),
    }


def pearson_rows(a: np.ndarray, b: np.ndarray) -> np.ndarray:
    a = a - a.mean(axis=-1, keepdims=True)
    b = b - b.mean(axis=-1, keepdims=True)
    numerator = (a * b).sum(axis=-1)
    denominator = np.sqrt((a * a).sum(axis=-1) * (b * b).sum(axis=-1))
    return numerator / np.maximum(denominator, 1e-12)


def rdm_transfer(state: np.ndarray, permutation: np.ndarray | None = None) -> float:
    """Mean correlation of off-diagonal domain cosine matrices across two-order changes."""
    if state.ndim != 4 or state.shape[:2] != (12, 4):
        raise ValueError("expected domain x format x layer x width")
    gram = np.einsum("nfld,mfld->flnm", state, state)
    rows, cols = np.triu_indices(12, k=1)
    pairs = []
    for src, dst in PRIMARY_EDGES:
        target = gram[dst]
        if permutation is not None:
            target = target[:, permutation][:, :, permutation]
        pairs.append(pearson_rows(gram[src][:, rows, cols],
                                  target[:, rows, cols])[list(MID)].mean())
    return float(np.mean(pairs))


def report(final: np.ndarray, draws: int = 1000) -> dict:
    states = effects(final)
    rng = np.random.default_rng(SEED + 19)
    perms = [rng.permutation(12) for _ in range(draws)]
    result = {}
    for name, state in states.items():
        observed = rdm_transfer(state)
        null = np.array([rdm_transfer(state, p) for p in perms])
        result[name] = {
            "double_order_rdm_pearson": observed,
            "domain_permutation_draws": draws,
            "domain_permutation_mean": float(null.mean()),
            "domain_permutation_q95": float(np.quantile(null, .95)),
            "domain_permutation_p_ge_observed": float((1 + np.sum(null >= observed)) /
                                                       (draws + 1)),
        }
    return {"status": "post-result exploratory", "mid_layers": list(MID),
            "edges": [list(x) for x in PRIMARY_EDGES], "effects": result}


if __name__ == "__main__":
    final, _ = load_cached(OUT)
    result = report(final)
    result["rdm_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    result["source_provenance"] = json.loads((OUT / "provenance.json").read_text())
    path = OUT / "rdm_report.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
