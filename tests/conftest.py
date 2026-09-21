"""Shared fixtures.

The heavy imports (torch, transformers, tokenizers, lsx) live INSIDE the fixture rather than at
module scope. At module scope they make the whole test tree uncollectable without the full ML
stack — a pure-logic test like the claims validator cannot even be *found* in an environment
without torch, which is what broke the first pages build. Now a bare `pip install pytest pyyaml`
can run everything that does not actually need a model.
"""
import pathlib
import sys

import pytest

# Test the checkout these tests live in, not whatever `src` the editable install points at: the
# venv's .pth names the main checkout, so in a worktree `pytest tests/` would otherwise import a
# different tree than the one under edit. parents[1] is the repository root (this file is
# tests/conftest.py); parents[2] would be the directory ABOVE the checkout, which is nothing.
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "src"))

CORPUS = [
    "the thesis is that a particle has a definite position and momentum",
    "the antithesis is that measurement disturbs what it measures",
    "the synthesis is that position and momentum are complementary descriptions",
    "a child is embedded in its impulses; later the impulses become objects it can hold",
    "the muppets take manhattan while star wars unfolds two hundred years earlier",
] * 4


@pytest.fixture(scope="session")
def tiny_lm():
    torch = pytest.importorskip("torch")
    pytest.importorskip("transformers")
    from tokenizers import Tokenizer, models, pre_tokenizers, trainers
    from transformers import PreTrainedTokenizerFast, Qwen2Config, Qwen2ForCausalLM

    from lsx import LM

    torch.manual_seed(0)
    tk = Tokenizer(models.BPE(unk_token="[UNK]"))
    tk.pre_tokenizer = pre_tokenizers.Whitespace()
    tk.train_from_iterator(CORPUS, trainers.BpeTrainer(
        vocab_size=300, special_tokens=["[UNK]", "[PAD]", "[EOS]"]))
    tok = PreTrainedTokenizerFast(tokenizer_object=tk, unk_token="[UNK]",
                                  pad_token="[PAD]", eos_token="[EOS]")
    cfg = Qwen2Config(vocab_size=tok.vocab_size + 8, hidden_size=32, intermediate_size=64,
                      num_hidden_layers=4, num_attention_heads=4, num_key_value_heads=2,
                      max_position_embeddings=256)
    return LM(Qwen2ForCausalLM(cfg), tok)
