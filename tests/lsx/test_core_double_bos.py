"""`lsx.core.remote`: a chat-rendered text reaches the model with exactly one `<bos>`.

Gemma's chat template emits `<bos>` as text. Every remote scoring and generation path tokenized
with special tokens added, so a rendered prompt reached the model as `<bos><bos>` -- through
every shape check. Found in the 62b audit; these tests hold the rule without a deployment.
"""
import types

import pytest
import torch

from lsx.core import checks, remote

BOS, BOS_ID = "<bos>", 2


class _Tok:
    """Word-level tokenizer that treats a leading literal `<bos>` as the bos token, as Gemma's does."""
    bos_token, bos_token_id, pad_token_id = BOS, BOS_ID, 0
    padding_side = "left"

    def _ids(self, text, add):
        ids = [BOS_ID] if add else []
        if text.startswith(BOS):
            ids.append(BOS_ID)
            text = text[len(BOS):]
        return ids + [10 + len(w) for w in text.split()]

    def __call__(self, texts, return_tensors=None, padding=False, add_special_tokens=True, **kw):
        if isinstance(texts, str):
            return {"input_ids": self._ids(texts, add_special_tokens)}
        rows = [self._ids(t, add_special_tokens) for t in texts]
        n = max(map(len, rows))
        ids = torch.tensor([[0] * (n - len(r)) + r for r in rows])
        mask = torch.tensor([[0] * (n - len(r)) + [1] * len(r) for r in rows])
        return {"input_ids": ids, "attention_mask": mask}


def _rlm():
    return types.SimpleNamespace(tok=_Tok())


def test_a_rendered_text_is_not_given_a_second_bos():
    ids, mask = remote._encode(_rlm(), [f"{BOS}user says hi", f"{BOS}user says hello there"])
    for r in range(ids.shape[0]):
        assert int(((ids[r] == BOS_ID) & (mask[r] > 0)).sum()) == 1


def test_raw_text_still_gets_its_bos():
    ids, mask = remote._encode(_rlm(), ["plain text", "more plain text here"])
    assert all(int(((ids[r] == BOS_ID) & (mask[r] > 0)).sum()) == 1 for r in range(2))


def test_the_old_behaviour_is_reproducible_and_is_what_the_assertion_catches():
    """The flag exists so the audit can measure the bug; the assertion must fire on its output."""
    rlm = _rlm()
    ids, mask = remote._encode(rlm, [f"{BOS}user says hi"], double_bos_bug=True)
    assert int((ids[0] == BOS_ID).sum()) == 2
    with pytest.raises(checks.DoubleBos):
        remote._assert_one_bos(rlm, ids, mask)


def test_a_mixed_batch_is_refused():
    with pytest.raises(checks.DoubleBos):
        remote._encode(_rlm(), [f"{BOS}rendered", "raw"])


def test_lead_length_and_ids_use_the_same_rule():
    """`n_lead` masks the lead out of the candidate score; if it counted a bos the ids did not
    carry, one candidate token would be masked away."""
    rlm = _rlm()
    lead = f"{BOS}user says hi"
    ids, mask = remote._encode(rlm, [lead + " ok"])
    n_lead = len(rlm.tok(lead, add_special_tokens=remote._add_special(rlm, [lead]))["input_ids"])
    assert int(mask[0].sum()) == n_lead + 1
