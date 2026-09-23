"""Post-result control: transfer a goal-grid direction to neutral actor swaps."""
from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from role_swap_probe import MID, SEED, load_acts, make_grid, unit


ROOT = Path(__file__).resolve().parents[2]


def load_grid(name: str, cache: str) -> np.ndarray:
    cases, digest = make_grid(ROOT / "research/narrative/prompts" / name)
    full, local = load_acts(cases, digest, ROOT / "cache" / cache)
    if not np.array_equal(local[:, :, 0], local[:, :, 1]):
        raise ValueError(f"{name}: local pair mismatch")
    return unit(full[:, :, 0] - full[:, :, 1])


def cross_scores(train: np.ndarray, test: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    if train.shape != test.shape or train.shape[:2] != (12, 2):
        raise ValueError("expected 12 domains, 2 orders, same layers and width")
    scores = np.empty(train.shape[:3], dtype=float)
    margins = np.empty_like(scores)
    for d in range(12):
        direction = unit(train[np.arange(12) != d].mean(axis=(0, 1)))
        margin = np.einsum("old,ld->ol", test[d], direction)
        margins[d] = margin
        scores[d] = (margin > 1e-12) + 0.5 * (np.abs(margin) <= 1e-12)
    return scores, margins


def order_scores(train: np.ndarray, test: np.ndarray, *, reverse: bool) -> np.ndarray:
    scores = np.empty(train.shape[:3], dtype=float)
    for d in range(12):
        for order in range(2):
            source_order = 1 - order if reverse else order
            direction = unit(train[np.arange(12) != d, source_order].mean(axis=0))
            margin = np.einsum("ld,ld->l", test[d, order], direction)
            scores[d, order] = (margin > 1e-12) + 0.5 * (np.abs(margin) <= 1e-12)
    return scores


def summarize(goal: np.ndarray, neutral: np.ndarray) -> dict:
    same, _ = cross_scores(goal, goal)
    cross, margins = cross_scores(goal, neutral)
    reverse, _ = cross_scores(neutral, goal)
    neutral_self, _ = cross_scores(neutral, neutral)
    rng = np.random.default_rng(SEED + 1)
    boot_cross, boot_gap = [], []
    for _ in range(2000):
        idx = rng.integers(0, 12, size=12)
        boot_cross.append(float(cross[idx][:, :, list(MID)].mean()))
        boot_gap.append(float((same[idx] - cross[idx])[:, :, list(MID)].mean()))
    observed = float(cross[:, :, list(MID)].mean())
    # A neutral label has no plot meaning. Flip both orders in a domain together.
    null = []
    for _ in range(1000):
        signs = rng.choice([-1, 1], size=12)
        signed = margins * signs[:, None, None]
        wins = (signed > 1e-12) + 0.5 * (np.abs(signed) <= 1e-12)
        null.append(float(wins[:, :, list(MID)].mean()))
    def curve(scores: np.ndarray) -> list[float]:
        return list(map(float, scores.mean(axis=(0, 1))))
    return {
        "goal_self": {"mid": float(same[:, :, list(MID)].mean()), "curve": curve(same)},
        "goal_to_neutral": {
            "mid": observed, "curve": curve(cross),
            "domain_bootstrap_ci95": list(map(float, np.quantile(boot_cross, [.025, .975]))),
            "orientation_permutation_p_ge": (1 + sum(x >= observed for x in null)) / 1001,
            "permutation_draws": 1000,
            "layer14_domain_accuracy": list(map(float, cross[:, :, 14].mean(axis=1))),
        },
        "goal_self_minus_cross": {
            "mid": float((same - cross)[:, :, list(MID)].mean()),
            "domain_bootstrap_ci95": list(map(float, np.quantile(boot_gap, [.025, .975]))),
        },
        "neutral_to_goal": {"mid": float(reverse[:, :, list(MID)].mean()), "curve": curve(reverse)},
        "neutral_self": {"mid": float(neutral_self[:, :, list(MID)].mean()), "curve": curve(neutral_self)},
        "order_diagnostic": {
            "goal_same_mid": float(order_scores(goal, goal, reverse=False)[:, :, list(MID)].mean()),
            "goal_reverse_mid": float(order_scores(goal, goal, reverse=True)[:, :, list(MID)].mean()),
            "neutral_same_mid": float(order_scores(neutral, neutral, reverse=False)[:, :, list(MID)].mean()),
            "neutral_reverse_mid": float(order_scores(neutral, neutral, reverse=True)[:, :, list(MID)].mean()),
            "goal_to_neutral_same_mid": float(order_scores(goal, neutral, reverse=False)[:, :, list(MID)].mean()),
            "goal_to_neutral_reverse_mid": float(order_scores(goal, neutral, reverse=True)[:, :, list(MID)].mean()),
            "goal_order_cosine_layer14": float(np.mean(np.sum(goal[:, 0, 14] * goal[:, 1, 14], axis=-1))),
            "neutral_order_cosine_layer14": float(np.mean(np.sum(neutral[:, 0, 14] * neutral[:, 1, 14], axis=-1))),
        },
    }


if __name__ == "__main__":
    result = summarize(
        load_grid("role_swap_v1.json", "role_swap"),
        load_grid("role_swap_neutral_v1.json", "role_swap_neutral"),
    )
    path = ROOT / "cache/role_swap_cross_control.json"
    path.write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))
