"""Pure-logic tests for the platonic-rotation line: no model, no network."""
import numpy as np
import pytest

from lsx.platonic_rotation import align, facts


def test_fit_recovers_a_planted_rotation_and_scale():
    rng = np.random.default_rng(0)
    R = align.random_semi_orthogonal(12, 12, rng)
    za = rng.standard_normal((200, 12)) + 3.0
    zb = 5.0 + 2.5 * (za - za.mean(0)) @ R.T
    m = align.fit_map(za, zb)
    assert np.allclose(m.R, R, atol=1e-8) and m.s == pytest.approx(2.5)
    assert m.s_reciprocal == pytest.approx(1 / 2.5)
    assert np.allclose(m.apply(za), zb, atol=1e-4)


@pytest.mark.parametrize("d_b,d_a", [(6, 10), (10, 6)])
def test_rectangular_maps_are_semi_orthogonal(d_b, d_a):
    rng = np.random.default_rng(1)
    m = align.fit_map(rng.standard_normal((50, d_a)), rng.standard_normal((50, d_b)))
    for R in (m.R, align.random_semi_orthogonal(d_b, d_a, rng)):
        assert R.shape == (d_b, d_a)
        gram = R @ R.T if d_b <= d_a else R.T @ R
        assert np.allclose(gram, np.eye(min(d_a, d_b)), atol=1e-8)


def test_shuffled_pairing_does_not_recover_the_rotation():
    rng = np.random.default_rng(2)
    R = align.random_semi_orthogonal(16, 16, rng)
    za = rng.standard_normal((400, 16))
    zb = (za - za.mean(0)) @ R.T
    shuffled = align.fit_map(za, zb[rng.permutation(400)])
    err = np.linalg.norm(shuffled.apply(za) - zb) / np.linalg.norm(zb)
    assert err > 0.9


def test_last_subject_token_and_boundary_refusal():
    #          <bos>   The     capital  of        France    is
    offsets = [(0, 0), (0, 3), (3, 11), (11, 14), (14, 21), (21, 24)]
    assert facts.last_subject_token(offsets, (15, 21)) == 4
    # a token that runs past the subject's end is refused, not rounded
    assert facts.last_subject_token([(0, 0), (0, 6), (6, 12)], (0, 4)) is None
    assert facts.last_subject_token(offsets, (30, 35)) is None


def test_split_is_by_subject_and_pairs_never_share_an_answer_prefix():
    fs = [{"subject": f"s{i}", "template": "{} speaks", "answer": a}
          for i, a in enumerate(["French", "French Guiana", "Dutch", "dutch", "Thai"] * 4)]
    assert facts.split_of("s1") == facts.split_of("s1")
    for d, r in facts.make_pairs(fs):
        a, b = facts.norm(fs[d]["answer"]), facts.norm(fs[r]["answer"])
        assert d != r and not a.startswith(b) and not b.startswith(a)


def test_says():
    assert facts.says(" Paris, France. It", "Paris")
    assert not facts.says(" a city", "Paris")
    assert not facts.says("anything", "")


def test_build_facts_dedupes_and_records_span():
    recs = [{"case_id": i, "requested_rewrite": {
        "prompt": "The capital of {} is", "relation_id": "P36", "subject": "France",
        "target_true": {"str": "Paris"}}} for i in range(2)]
    out = facts.build_facts(recs)
    assert len(out) == 1
    a, b = out[0]["span"]
    assert out[0]["prompt"][a:b] == "France"


def test_train_span_only_drops_the_arbitrary_completion():
    rng = np.random.default_rng(3)
    za, zb = rng.standard_normal((5, 12)), rng.standard_normal((5, 12))   # n - 1 = 4 < d
    full, span = align.fit_map(za, zb), align.fit_map(za, zb, train_span_only=True)
    assert np.linalg.matrix_rank(full.R) == 12 and np.linalg.matrix_rank(span.R) == 4
    assert np.allclose(full.apply(za), span.apply(za), atol=1e-5)          # agree on the span
    off = rng.standard_normal((3, 12))
    assert not np.allclose(full.apply(off), span.apply(off), atol=1e-2)    # and only there


@pytest.mark.parametrize("d_b,d_a", [(6, 10), (10, 6), (8, 8)])
def test_full_rank_fit_matches_the_direct_svd(d_b, d_a):
    rng = np.random.default_rng(4)
    za, zb = rng.standard_normal((60, d_a)), rng.standard_normal((60, d_b))
    ac, bc = za - za.mean(0), zb - zb.mean(0)
    U, _, Vt = np.linalg.svd(bc.T @ ac, full_matrices=False)
    assert np.allclose(align.fit_map(za, zb).R, U @ Vt, atol=1e-8)


def test_rank_deficient_fit_is_still_a_semi_orthogonal_polar_factor():
    rng = np.random.default_rng(5)
    za, zb = rng.standard_normal((7, 14)), rng.standard_normal((7, 10))
    m = align.fit_map(za, zb)
    assert np.allclose(m.R @ m.R.T, np.eye(10), atol=1e-8)
    M = (zb - zb.mean(0)).T @ (za - za.mean(0))
    H = m.R.T @ M                       # M = R H with H symmetric PSD  <=>  R = U V^T for an SVD of M
    assert np.allclose(H, H.T, atol=1e-8) and np.linalg.eigvalsh(H).min() > -1e-8
    assert np.allclose(m.R @ H, M, atol=1e-8)
    assert align.off_span_energy(align.centre(za), za) < 1e-12
    assert align.off_span_energy(align.centre(za), rng.standard_normal((50, 14))) > 0.3
