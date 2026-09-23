# Hour 65: shame vs pain is unreadable on the pain axis. The axis does not separate the paper's own pain events from its neutral ones at the screen layer.

Pre-registered in [`shame_vs_pain_prereg.md`](shame_vs_pain_prereg.md), with amendment 1 (fewer
shuffled-null draws off the screen layer, made before any activation). Stimuli:
`prompts/stimuli/shame_pain_v1/`. Code: `scripts/shame_axis/shame_pain.py` (analysis reviewed
by Sol before it ran; fix e84c067). Results: `results/shame_pain/summary.json` and `valence.json`;
stacks are local.

| model | where | screen layer (fixed in hour 64) |
|---|---|---|
| `google/gemma-2-2b`, `google/gemma-2-2b-it` | local RTX 3060 Ti, bf16, `cuda` | L7, L10 |
| `meta-llama/Llama-3.1-70B`, `meta-llama/Llama-3.1-70B-Instruct` | NDIF, batch 1, deployment bf16 | L32, L24 |

Valence: `distilbert-base-uncased-finetuned-sst-2-english` @ `714eb0fa`, CPU.

## The registered verdict: `open`, because every model fails the positive control

The positive control was the pain axis separating the paper's 20 A1 base events (physical pain)
from its 20 D base events (neutral) by more than both null q95s, at the screen layer. It fails in
**all four models**:

| model | A1 − D on the pain axis (z) | random-direction q95 | shuffled-label q95 |
|---|---|---|---|
| Gemma-2-2B base, L7 | 1.25 | 1.53 | 1.70 |
| Gemma-2-2B-it, L10 | 0.99 | 1.78 | 1.81 |
| Llama-3.1-70B base, L32 | 0.96 | 1.45 | 2.01 |
| Llama-3.1-70B-Instruct, L24 | 1.08 | 1.45 | 2.54 |

By the frozen rule, a model that fails its positive control is **unreadable, not null**. With both
instruct models unreadable, `shame-not-pain` stays **open**. None of the shame numbers below is a
result. They are reported because a withheld number is worse than a labelled one.

**What the failure is.** The pain vector is built partly from these same 40 sentences, so the
axis should separate them easily. It does separate them, by about 1 z. But random directions
separate these two groups about as well: the axis never reaches the random distribution's upper
tail. A post-hoc check rules out the obvious explanation, that clause
variance inflates the pool's spread along the axis: the pool-to-base spread ratio is below 1 on
the axis. The groups simply differ along almost every direction, and at these layers the pain
axis is not special among them. This is hour 64's lesson again, now on the paper's own categories:
there, the self/other split was not pain-specific, and here pain versus neutral is not
axis-specific at the screen layer.

**Across the curve** (reported, not selected, per non-negotiable 4), the positive control passes
only at later layers:
- Gemma base: L15–16 and L21–25.
- Gemma-it: L18–20.
- Llama base: L40, L48 and L79.
- Llama-Instruct: none.

The screen layers came from the paper's S1 steering layer, which is where their screen
replicates (hour 64). That is not where their axis singles out pain in these sentences.

## Descriptive only: what the shame contrast did (no cell is readable)

Screen layer, Δ = mean over 40 bases of z(shame) − z(witness):

| model | author | Δ | clears nulls | lexical-floor Δ | network contribution [95%] | α at equal valence [95%] |
|---|---|---|---|---|---|---|
| g2b | claude | +0.66 | yes | +0.90 | −0.24 [−0.50, +0.03] | +0.60 [+0.37, +0.83] |
| | gpt | +0.21 | no | +0.17 | +0.04 [−0.16, +0.25] | +0.77 [+0.15, +1.33] |
| g2b_it | claude | +0.78 | yes | +0.89 | −0.12 [−0.33, +0.11] | +0.68 [+0.48, +0.88] |
| | gpt | +0.73 | no | +0.16 | +0.57 [+0.32, +0.82] | +0.92 [+0.56, +1.33] |
| l70 | claude | +0.39 | no | +0.93 | −0.54 [−0.92, −0.16] | +0.37 [+0.03, +0.68] |
| | gpt | −0.31 | no | +0.29 | −0.60 [−0.76, −0.42] | −0.17 [−0.55, +0.13] |
| l70_it | claude | +0.78 | no | +0.93 | −0.16 [−0.48, +0.17] | +0.74 [+0.45, +1.03] |
| | gpt | −0.15 | no | +0.28 | −0.43 [−0.59, −0.28] | +0.14 [−0.14, +0.44] |

Even setting the instrument aside, **no cell meets the five effect criteria**, and the two
authors' sets behave differently:
- **The Claude set's shame effect is vocabulary.** Its bag-of-embeddings floor alone gives
  +0.89 to +0.93, at least as much as the network. The network contribution is ≤ 0 in all four
  models, so the effect sits in the words. Where it clears the nulls across the curve, it does so
  mostly in the first half of each network (Gemma L0–L18, Llama L0–L20 plus L44 and L48). Its shame clauses name failures in negatively coloured
  words ("botch", "errors", "mess", "crooked", "late") that its witness clauses lack, and the
  feeling-word ban did not reach those. The valence adjustment leaves α positive, but a sentiment
  classifier is not a lexical floor, and the lexical floor is the stricter test here.
- **The GPT set is the reverse.** Its lexical floor is small (+0.16 to +0.29), because its
  templated clauses match word for word. It never clears the nulls at a screen layer (across the curve, only at Gemma-it L8–9). It is positive in Gemma
  (network contribution +0.57 in Gemma-it) and **negative in both Llama models**.
- **The authors disagree in sign on Llama.** That is the outcome the per-author rule was written
  to catch: the answer depends on how the stimuli were written.
- The rewording floor, witness − base, is large: +0.4 to +1.1 z in most cells. Appending any
  clause of this length moves items along the pain axis about as much as the contrast itself.

Δ_post (instruct − base, the registered secondary) has a positive point estimate for all four
family×author pairs, with intervals above 0 for two: Gemma/gpt +0.52 and Llama/claude +0.39. It
is not read, because the cells it compares are unreadable.

## What this changes

- `shame-not-pain` stays **open**. This battery cannot answer it on this axis at these layers. The
  honest summary is that the question presupposed an axis specific to pain, and at the paper's
  screen layer the axis is not specific even to the paper's own pain events.
- New row `pain-axis-separates-own-categories`, **narrowed**: the S2 pain axis separates the
  paper's A1 pain events from its D neutral events beyond random and shuffled directions only at
  later layers, in three of four models, and never at the screen layer.
- For any rerun, three lessons, recorded before anyone designs it:
  1. Choose the readout layer from the positive control's curve **on other data** (for example
     the paper's A2–A5 and B–E items), not from the screen replication.
  2. Extend the feeling-word ban to failure-valenced words, or balance them across arms. The
     Claude set shows that the ban as written leaves the lexical floor wide open.
  3. Match the two arms' vocabulary as tightly as the GPT set did, but without a template that
     turns the witness arm into "not watching me".
- The blind two-author design worked as intended. The cross-audit found both sets valid (0 of 80
  misread each), and the per-author split exposed a stimulus effect that a single set would have
  hidden.
