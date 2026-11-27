# Inkling

**Can the control parameters of a looped mixture-of-experts model be edited into small, removable,
goal-specific overlays that beat a random edit of the same size?**

The question above is provisional. It was written by the agent from a conversation on 2026-11-26
and has not been reviewed as a line question; treat it as a placeholder until it is.

## The model

`thinkingmachines/Inkling-2-Mini` (released 2026-11-20, Apache 2.0). 26.4B parameters, 24 stored
layers, of which the middle 12 (layers 6–17) run three times per token with shared weights. Each
layer routes every token to 8 of 128 experts.

Run locally as `mlx-community/Inkling-2-Mini-4bit` at revision
`9c0e2960609ba7cb40daf92c6f7bf8ed56e1dd62`, on an Apple M1 Max with 32 GB.

## Runtime caveat

Inkling support in mlx-lm exists only in an unmerged pull request, ml-explore/mlx-lm#2086, pinned
here to commit `e2b5bbd3bd9d186dea895e60802aa765e70b9d93`. Every result in this line depends on
that implementation being a faithful port. It has not been checked against the reference
transformers implementation. Until it is, numbers here describe "Inkling as run by this port".

## Why this model

The bulk weights (experts, attention projections) are stored packed at 4 bits. The parameters that
steer them are stored as plain floats: the expert router and its bias, a scale per expert, the loop
message gates, and the queries that decide which earlier block or pass each layer reads. That is a
few tens of millions of floats steering 26 billion quantized weights.

## Reproduce

```bash
uv venv --python cpython-3.12-macos-aarch64-none .venv-mlx
.venv-mlx/bin/python -m ensurepip
.venv-mlx/bin/python -m pip install \
  "git+https://github.com/jundot/mlx-lm.git@e2b5bbd3bd9d186dea895e60802aa765e70b9d93" \
  pillow pyarrow
.venv-mlx/bin/python scripts/inkling/speed.py
.venv-mlx/bin/python scripts/inkling/quality.py
```

Weights download to the default Hugging Face cache (`~/.cache/huggingface/hub`), not to
`cache/hf` as on the other machines.

## What this line is NOT trying to do

- **Not** adding knowledge to the model. Published weight-editing results on other models removed
  a failure (repetition loops); none added an ability.
- **Not** reproducing Thinking Machines' benchmark numbers. The baselines here are small fixed
  subsets used as a before-number for our own edits.

Log: `docs/EXPERIMENTS.md`. Claims: `claims.yaml`.
