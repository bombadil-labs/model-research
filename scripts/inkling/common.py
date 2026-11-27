"""Shared helpers for the Inkling 2 Mini baseline benchmarks (MLX, Apple Silicon)."""

import importlib.metadata as md
import platform
import subprocess
import time
from pathlib import Path

import mlx.core as mx
from huggingface_hub import try_to_load_from_cache
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

REPO = "mlx-community/Inkling-2-Mini-4bit"
RESULTS = Path(__file__).resolve().parents[2] / "research" / "inkling" / "results"
RESULTS.mkdir(parents=True, exist_ok=True)


def _sh(cmd):
    try:
        return subprocess.check_output(cmd, text=True).strip()
    except Exception:
        return None


def provenance():
    """Everything needed to say which model, runtime and machine produced a number."""
    snap = Path(try_to_load_from_cache(REPO, "config.json")).parent
    return {
        "model_repo": REPO,
        "model_revision": snap.name,
        "base_model": "thinkingmachines/Inkling-2-Mini",
        "mlx_lm_version": md.version("mlx-lm"),
        "mlx_lm_source": "ml-explore/mlx-lm PR #2086 (unmerged)",
        "mlx_version": md.version("mlx"),
        "python": platform.python_version(),
        "chip": _sh(["sysctl", "-n", "machdep.cpu.brand_string"]),
        "ram_gb": int(_sh(["sysctl", "-n", "hw.memsize"]) or 0) / 2**30,
        "macos": platform.mac_ver()[0],
        "device": "mlx-metal",
        "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }


def load_model():
    t0 = time.time()
    model, tok = load(REPO)
    loop = None
    for _, m in model.named_modules():
        cfg = getattr(getattr(m, "args", None), "loop_config", None)
        if cfg:
            loop = cfg
            break
    assert loop is not None, "loop_config not found"
    return model, tok, loop, time.time() - t0


def render(tok, user, effort=None):
    kw = {} if effort is None else {"reasoning_effort": effort}
    return tok.apply_chat_template(
        [{"role": "user", "content": user}],
        add_generation_prompt=True,
        tokenize=False,
        **kw,
    )


def run(model, tok, prompt, max_tokens, temp=0.0, seed=0):
    """One generation. Returns (text, stats). temp=0 is greedy."""
    mx.random.seed(seed)
    mx.clear_cache()
    mx.reset_peak_memory()
    parts, last = [], None
    for last in stream_generate(
        model, tok, prompt=prompt, max_tokens=max_tokens, sampler=make_sampler(temp=temp)
    ):
        parts.append(last.text)
    return "".join(parts), {
        "prompt_tokens": last.prompt_tokens,
        "prompt_tps": last.prompt_tps,
        "gen_tokens": last.generation_tokens,
        "gen_tps": last.generation_tps,
        "peak_gb": last.peak_memory,
        "finish": last.finish_reason,
    }


def split_output(text):
    """Split raw model output into (thinking, final). final is '' if never produced."""
    final = ""
    if "<|content_text|>" in text:
        final = text.rsplit("<|content_text|>", 1)[1].split("<|end_message|>")[0].strip()
    thinking = ""
    if "<|content_thinking|>" in text:
        thinking = text.split("<|content_thinking|>", 1)[1].split("<|end_message|>")[0]
    return thinking, final
