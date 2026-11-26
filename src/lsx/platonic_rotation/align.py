"""The Plato's Key map: mean-centre, orthogonal Procrustes, one global scale. Pure numpy.

    z_B = mu_B + s * R (z_A - mu_A),   R = U V^T  from the thin SVD of  Zc_B Zc_A^T = U S V^T

Keys are stored one per ROW here, so `Zc_B Zc_A^T` of the post (one key per column) is
`Bc.T @ Ac`, shape [d_B, d_A]. With d_A != d_B, R is semi-orthogonal: orthonormal rows when
d_B < d_A, orthonormal columns when d_B > d_A.

The scale. The post's prose says s is chosen "to roughly match the recipient's overall spread",
which is s = ||Zc_B||_F / ||Zc_A||_F. Its rendered equation, as extracted on 2026-11-26, reads the
reciprocal (||Zc_A||_F / ||Zc_B||_F). The two cannot both be meant; `fit_map` uses the one that
does what the prose says and `Map.with_scale` exists so the other can be run as a labelled arm.
"""
from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np


@dataclass(frozen=True)
class Map:
    mu_a: np.ndarray      # [d_A]
    mu_b: np.ndarray      # [d_B]
    R: np.ndarray         # [d_B, d_A]
    s: float
    s_reciprocal: float   # ||Zc_A||_F / ||Zc_B||_F, the equation as extracted from the post

    def apply(self, za: np.ndarray) -> np.ndarray:
        za = np.asarray(za, dtype=np.float64)
        return (self.mu_b + self.s * (za - self.mu_a) @ self.R.T).astype(np.float32)

    def with_scale(self, s: float) -> "Map":
        return replace(self, s=float(s))

    def with_rotation(self, R: np.ndarray) -> "Map":
        assert R.shape == self.R.shape
        return replace(self, R=R)


@dataclass(frozen=True)
class Centred:
    """One model's training keys at one layer, centred and QR-factored once so that the fits
    against every layer of the other model reuse it: (z - mu).T = Q[:, :m] @ T, m = min(n, d)."""
    mu: np.ndarray
    Q: np.ndarray         # [d, d] orthonormal; the first m columns span the centred keys
    T: np.ndarray         # [m, n]
    fro: float


def centre(z: np.ndarray) -> Centred:
    z = np.asarray(z, dtype=np.float64)
    mu = z.mean(0)
    zc = z - mu
    Q, Rr = np.linalg.qr(zc.T, mode="complete")
    return Centred(mu, Q, Rr[:min(z.shape)], float(np.linalg.norm(zc)))


def fit_centred(a: Centred, b: Centred, train_span_only: bool = False, seed: int = 0) -> Map:
    """R = U V^T from an SVD of Zc_B Zc_A^T, computed through the small core T_B T_A^T.

    With fewer training facts than dimensions (n - 1 < min(d_A, d_B)) that cross-covariance is
    rank-deficient: only r = n - 1 singular directions are determined by the data, and "the thin
    SVD" pads U and V with an ARBITRARY orthonormal completion (whatever LAPACK returns). Any
    completion is a valid SVD, and it decides how the map acts on the part of a new key that lies
    off the span of the training keys. Here the completion is explicit: a seeded Haar-random
    semi-orthogonal map between the two complements. `train_span_only=True` leaves it out, giving
    the partial isometry the data does determine, which sends everything off the span to zero.
    """
    if a.T.shape[1] != b.T.shape[1]:
        raise ValueError(f"unpaired keys: {a.T.shape[1]} vs {b.T.shape[1]}")
    ma, mb = a.T.shape[0], b.T.shape[0]
    d_a, d_b = a.Q.shape[0], b.Q.shape[0]
    P, S, Qt = np.linalg.svd(b.T @ a.T.T, full_matrices=True)       # [mb, ma] core
    r = int((S > 1e-9 * S[0]).sum())
    U1, V1 = b.Q[:, :mb] @ P[:, :r], a.Q[:, :ma] @ Qt[:r].T
    R = U1 @ V1.T
    if not train_span_only and r < min(d_a, d_b):
        Ub = np.concatenate([b.Q[:, :mb] @ P[:, r:], b.Q[:, mb:]], axis=1)      # [d_b, d_b - r]
        Va = np.concatenate([a.Q[:, :ma] @ Qt[r:].T, a.Q[:, ma:]], axis=1)      # [d_a, d_a - r]
        W = random_semi_orthogonal(d_b - r, d_a - r, np.random.default_rng(seed))
        R = R + Ub @ W @ Va.T
    return Map(a.mu, b.mu, R, b.fro / a.fro, a.fro / b.fro)


def fit_map(za: np.ndarray, zb: np.ndarray, train_span_only: bool = False, seed: int = 0) -> Map:
    """Fit on paired keys: za [n, d_A], zb [n, d_B], row i of each is the same fact."""
    if len(za) != len(zb):
        raise ValueError(f"unpaired keys: {len(za)} vs {len(zb)}")
    return fit_centred(centre(za), centre(zb), train_span_only, seed)


def off_span_energy(c: Centred, z: np.ndarray) -> float:
    """Fraction of the centred energy of new keys `z` lying off the span of the training keys."""
    zc = np.asarray(z, dtype=np.float64) - c.mu
    on = zc @ c.Q[:, :c.T.shape[0]]
    return float(1.0 - (on ** 2).sum() / (zc ** 2).sum())


def random_semi_orthogonal(d_b: int, d_a: int, rng: np.random.Generator) -> np.ndarray:
    """A Haar-random [d_b, d_a] map with orthonormal rows (d_b <= d_a) or columns (d_b > d_a)."""
    big, small = max(d_a, d_b), min(d_a, d_b)
    q, r = np.linalg.qr(rng.standard_normal((big, small)))
    q = q * np.sign(np.diag(r))          # fix the QR sign convention so the draw is Haar
    return q.T if d_b <= d_a else q


def wilson(k: int, n: int, z: float = 1.96) -> tuple[float, float]:
    if n == 0:
        return (0.0, 1.0)
    p = k / n
    den = 1 + z * z / n
    mid = (p + z * z / (2 * n)) / den
    half = z * np.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (float(max(0.0, mid - half)), float(min(1.0, mid + half)))
