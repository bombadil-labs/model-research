"""Chunking the opener set must not change a single score.

The remote run scores gemma's six openers two at a time, because all six in one padded job puts
the deployment process over its memory allowance and it OOMs in the decoder MLP. That is a
throughput change, and a throughput change that moved the numbers would be exactly the class of
bug `docs/INSTRUMENTS.md` §4 and §4b are about -- both were batching bugs that produced plausible
numbers. So the claim "chunking changes no number" is asserted here rather than argued.

The logprobs are teacher-forced and independent: each is log p(opener | prompt), and nothing is
normalised across the batch. If that ever stops being true this test fails.
"""
from __future__ import annotations

import importlib.util
import pathlib

import numpy as np
import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
_spec = importlib.util.spec_from_file_location(
    "conscription_openers", ROOT / "scripts/shame_axis/conscription_openers.py")
openers_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(openers_mod)


def test_chunks_partition_the_opener_set_exactly():
    for n in (1, 2, 3, 4, 5, 6, 7):
        chunks = openers_mod._chunks(openers_mod.OPENERS, n)
        assert [x for c in chunks for x in c] == list(openers_mod.OPENERS)
        assert all(1 <= len(c) <= n for c in chunks)


def test_opener_chunking_is_exact(tiny_lm):
    """Scoring in chunks reproduces scoring in one batch, bit for bit, on the local twin."""
    from lsx.core.extract import asserted_patched_logprob

    lead = "The quick brown fox "
    cands = list(openers_mod.OPENERS)
    whole = asserted_patched_logprob(tiny_lm, lead, cands)
    for n in (1, 2, 3, 4):
        chunked = np.concatenate([asserted_patched_logprob(tiny_lm, lead, c)
                                  for c in openers_mod._chunks(cands, n)])
        assert chunked.shape == whole.shape
        np.testing.assert_allclose(chunked, whole, rtol=0, atol=0,
                                   err_msg=f"chunk size {n} moved a score")


def test_ritual_is_a_log_odds_of_the_declared_index_sets():
    lp = np.array([-2.0, -3.0, -8.0, -4.0, -12.0, -13.0])
    expect = np.logaddexp(-2.0, -3.0) - np.logaddexp(-12.0, -13.0)
    assert openers_mod.ritual(lp) == pytest.approx(expect)
    # the statistic is antisymmetric under swapping the two index sets
    swapped = lp[[4, 5, 2, 3, 0, 1]]
    assert openers_mod.ritual(swapped) == pytest.approx(-expect)


def test_ritual_ignores_the_non_contrast_openers():
    """Openers 2 and 3 are reported but are not in either side of the primary statistic."""
    lp = np.array([-2.0, -3.0, -8.0, -4.0, -12.0, -13.0])
    moved = lp.copy()
    moved[2] += 5.0
    moved[3] -= 7.0
    assert openers_mod.ritual(moved) == pytest.approx(openers_mod.ritual(lp))
