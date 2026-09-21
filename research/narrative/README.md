# Narrative calculus

**Can the relational structure of a narrative be measured in activation space, fit as an operator,
and pointed at a domain where the corresponding parts are unknown?**

## The questions

1. **Does a cross-domain relational shape exist above chance?** — **Answered: mostly no.** The
   apparent shape is largely slot position; the shuffled control kills the by-content signal.
2. **Can an affine map carry a relation to a held-out domain?** — **Partly.** Role identity is a
   domain-independent direction; after removing it a weak relation transfers.
3. **Do narrative factors behave as directions that compose?** — **Yes for some.** Era composes and
   transfers; tense sits on its floor; voice is worse than its floor.
4. **Can the measurement core reproduce this project's own published numbers?** — **Yes, and it
   refuses some of them.** Phase 1 pieces 1–5; three logged numbers mean less than the record said.

## What an answer looks like

A factor counts as real when it clears a **measured** floor (bag-of-words or word-count on the same
grid, never chance) with its random and no-patch arms reported, and the layer curve shown rather
than a peak. A transfer counts when it holds on a held-out domain and on a second model family.
**Done** means answered above a floor with arms, or retired with the reason on the record.

## What this project is NOT trying to do

- **Not** generating stories, or building a writing tool. Generation is a readout, not a product.
- **Not** claiming the residual stream contains narrative structure *as such* — the measured objects
  are directions that predict specific readouts on specific grids.
- **Not** general interpretability tooling; that is `src/lsx`, shared across lines.

## State

The ladder below is the original framing, kept because the stage numbering is referenced throughout
the log. Checkpoint 2 in [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) is the authority on what
currently stands, what fell, and what was **withdrawn**.


The motivating idea: a prompt that describes a structure (thesis → antithesis → synthesis;
a Kegan subject/object transition; a plot) produces a point cloud in activation space whose
*internal relations* may be shared across domains even though the clouds sit in different regions.
If that shape can be measured (stage 2) it can be fit as an operator (stage 3) and pointed at a
domain where the corresponding parts are unknown (stage 4). Longer-term this is the activation-level
substrate for a narrative calculus: decompose a story into factors, transform them, recompose.

## Ladder

| stage | module | question | status |
|---|---|---|---|
| 1 | `lsx.model`, `lsx.extract` | capture residuals, pool by role, patch | working on Qwen2.5-0.5B |
| 2 | `lsx.compare` | does the same shape appear across domains, above baseline? | **mostly slot position, not content**: shuffled control kills the by-content signal (RESULTS.md) |
| 3 | `lsx.operate` | can an affine map carry the relation to a held-out domain? | role identity is a domain-independent direction (constant baseline rank 1.07); after removing it, a weak relation transfers (rank 3.0 vs 3.5 null, peaks layer 20) |
| 4 | `lsx.steer` | patch a target activation in and read it out | role direction selects the held-out domain's span (rank 1.3–1.7 vs 3.3 random, best at layers 14–20); relation-content patch is null |

## Setup

```
uv venv .venv && . .venv/bin/activate
uv pip install -e ".[dev]"
export HF_HOME=$PWD/cache/hf HF_HUB_DISABLE_XET=1   # Xet transfer host is not reachable from the cloud env
python -c "from huggingface_hub import snapshot_download; snapshot_download('Qwen/Qwen2.5-0.5B', allow_patterns=['*.json','*.safetensors','merges.txt','vocab.json'])"
pytest                                   # synthetic tests on a tiny random model, no weights needed
python scripts/extract_grid.py prompts/holonic_v1.json --model Qwen/Qwen2.5-1.5B
python scripts/stage2.py prompts/holonic_v1.json --model Qwen/Qwen2.5-1.5B --metric rsa --stacks results/stacks_qwen2.5_1.5b_holonic_v1.npz
python scripts/stage3.py results/stacks_qwen2.5_1.5b_holonic_v1.npz
```

CPU-only is fine for 0.5B–1.5B: ~0.5 s per extraction, ~4 tok/s generation on 4 cores.

## Prompt format

Roles are marked inline and pooled by mean over their tokens; unmarked text still runs through the
model as context.

```
In physics, the initial claim is that [[thesis: ...]]. The opposing claim is that [[antithesis: ...]]. ...
```

A grid is a JSON file with `roles` and `prompts` keyed `domain/framing`. `research/narrative/prompts/dialectic_v0.json`
is a draft 4-domain × 2-framing grid for the dialectic relation.

| 5 | `scripts/stage5_*` | narrative factors (era, voice) as directions: lens, composition, order | both lenses work (1.3/3 vs 2.1 random), era+voice composes (2.0/9), order gap 0.5; replicates on Qwen 0.5B and Pythia 1.4B |
| 6 | `scripts/narrative/stage6_factors.py` | N factors: era × voice × tense; era × mood; era × theme (3-sentence passages) | three-way composition 2.8/18 (chance 9.5); mood lens 1.28/3 and composes with era 1.9/9; theme lens 1.25/3 but does not steer generation; cross-talk matrices diagonal |

## Remote models via NDIF

`src/lsx/ndif.py` runs traces on NDIF-hosted models (`nnsight`) through a credential-injecting
egress proxy: the API key header is added by the proxy (the client omits it), and because the proxy
does not carry WebSocket upgrades, jobs are submitted over HTTPS and polled. Requires Python 3.12
(`.venv312`). `python scripts/ndif_smoke.py EleutherAI/gpt-j-6b` round-trips in ~4 s; `ndif_extract.py`, `ndif_factors.py`, `ndif_generate.py` mirror the local pipeline. Only
"pinned" models are available on the free tier (`research/narrative/results/ndif_pinned.txt`); gated ones need an
HF token injected for `huggingface.co`.

## Documents

- `RESULTS.md`: the running log, every number with its control.
- `WRITEUP.md`: the draft writeup.
- `VISION.md`: the operator set, lexicon, coarse-graining mechanism, ecology notes.
- `docs/ALGEBRA.md`: the calculus as a closed many-sorted operator algebra with laws marked measured / hypothesized / conjectured.

## Results

See `RESULTS.md` for the running log, including open problems in priority order.

## Documents

- [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md) — the running log, hours 1–50, with checkpoints and
  the ordered open-problems list.
- [`docs/QUESTIONS.md`](docs/QUESTIONS.md) — questions not yet ordered into that list.
- [`VISION.md`](VISION.md) — the operator set the calculus would need, mapped to what exists.
- [`WRITEUP.md`](WRITEUP.md) — the claims, as claims.
- [`ALGEBRA.md`](ALGEBRA.md) — the calculus itself.

## Reproducing

```bash
. .venv/bin/activate
export HF_HOME=$PWD/cache/hf HF_HUB_DISABLE_XET=1
python -m lsx.core.reproduce          # §1A: reproduce every number the core can compute
pytest tests/narrative tests/lsx
```

`.npz` stacks are gitignored; the reproduction suite regenerates what it can and reports what it
cannot as a refusal rather than a pass.
