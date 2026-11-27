"""Smoke test for Inkling 2 Mini on MLX: load, generate, report speed and memory.

Usage: python scripts/inkling/smoke.py [--passes N] [--effort E] [--max-tokens N] [--prompt "..."]
--passes overrides the loop count (the released model was trained at 3 only).
"""

import argparse
import time

import mlx.core as mx
from mlx_lm import load, stream_generate
from mlx_lm.sample_utils import make_sampler

REPO = "mlx-community/Inkling-2-Mini-4bit"

p = argparse.ArgumentParser()
p.add_argument("--passes", type=int, default=None)
p.add_argument("--effort", default=None, help="reasoning_effort: none..max or 0-0.99")
p.add_argument("--max-tokens", type=int, default=400)
p.add_argument("--temp", type=float, default=1.0)
p.add_argument(
    "--prompt",
    default="A farmer has 17 sheep. All but 9 run away. How many are left? Answer briefly.",
)
a = p.parse_args()

t0 = time.time()
model, tokenizer = load(REPO)
print(f"load: {time.time() - t0:.1f}s  active mem: {mx.get_active_memory() / 1e9:.1f} GB")

text = model.language_model if hasattr(model, "language_model") else None
loop = None
for _, m in model.named_modules():
    if getattr(getattr(m, "args", None), "loop_config", None):
        loop = m.args.loop_config
        break
print("loop_config:", loop)
if a.passes is not None:
    loop["num_passes"] = a.passes
    print("-> overriding num_passes to", a.passes)

kw = {}
if a.effort is not None:
    try:
        kw["reasoning_effort"] = float(a.effort)
    except ValueError:
        kw["reasoning_effort"] = a.effort
prompt = tokenizer.apply_chat_template(
    [{"role": "user", "content": a.prompt}],
    add_generation_prompt=True,
    tokenize=False,
    **kw,
)
print("--- prompt as rendered ---")
print(prompt)
print("--- output ---")

last = None
for last in stream_generate(
    model,
    tokenizer,
    prompt=prompt,
    max_tokens=a.max_tokens,
    sampler=make_sampler(temp=a.temp),
):
    print(last.text, end="", flush=True)
print("\n--- stats ---")
print(
    f"prompt: {last.prompt_tokens} tok @ {last.prompt_tps:.1f} tok/s | "
    f"gen: {last.generation_tokens} tok @ {last.generation_tps:.1f} tok/s | "
    f"peak mem: {last.peak_memory:.1f} GB | finish: {last.finish_reason}"
)
