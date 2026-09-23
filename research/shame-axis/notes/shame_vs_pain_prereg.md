# Pre-registration: does the pain axis track shame at matched valence? (claim `shame-not-pain`, hour 65)

**Written after the stimuli were committed and cross-audited, and before any activation of them
exists.** Design history: [`shame_vs_pain_design_DRAFT.md`](shame_vs_pain_design_DRAFT.md).
Stimuli and their provenance: `prompts/stimuli/shame_pain_v1/` (AUTHORING.md, both clause files,
their hash commitments, the cross-audit).

## The claim and what would settle it

`shame-not-pain`: *the axis is better described as tracking shame than as tracking pain.* The
test: hold the event fixed, add a clause of matched length in which others are present, and
compare two versions of that clause. In one, the others **evaluate me against their standard**
(`shame`). In the other, they **do not** (`witness`). If the axis tracks shame, `shame − witness`
is positive, including on neutral events where nothing hurts, and it survives adjustment for
valence. If the axis tracks pain or negative valence, the contrast vanishes once valence is
accounted for, and it sits near zero on neutral events.

## Stimuli (frozen, hash-committed, audited)

- 40 base events from the paper's S2_1P set, taken verbatim: all 20 `A1` (physical pain) and all
  20 `D` (neutral). None were selected.
- Two authors, each writing a full set blind to the other: `claude` (Claude Opus 5.5) and `gpt`
  (Sol). Per base and author there is one `shame` and one `witness` clause, differing by at most 2
  tokens. The validator bans words that name a feeling.
- Items are built as `"<base without its period> <clause>. I feel:"`. That gives 40 `base`,
  80 `shame` and 80 `witness` items, **200 in total**.
- The cross-audit had each author label the other's clauses as shame or witness with the arm
  hidden. The result was **0 of 80 misclassified for each author**, so the manipulation reads as
  intended in both sets, and the planned sensitivity analysis (excluding misclassified items) is
  empty.
- **Known before any activation**, recorded so that it cannot be discovered afterwards: the two
  sets differ in style.
  - The `gpt` set is templated. Its shame clauses are nearly all "<name> at <place> <n> sees me
    break their <x> rule", and its witness clauses nearly all "… without watching/checking me".
  - The `claude` set is narrative and varied.
  - The `gpt` shame arm therefore frames the failure as breaking a rule, which may be closer to
    guilt. Its witness arm names watching under negation.
  - Item gpt `D-08/witness` contains a typo ("winds watches"). It is kept, because the file is
    hash-committed.
  - This is why the decision below is taken **per author**.

## Models, extraction, axis

The four models of hour 64, as its pre-registration promised for these stimuli. Their replication
gates already passed (r ≥ 0.9996).

| key | model | where | screen layer (fixed in hour 64) |
|---|---|---|---|
| `g2b` | `google/gemma-2-2b` | local RTX 3060 Ti, bf16, one text per forward | L7 |
| `g2b_it` | `google/gemma-2-2b-it` | local, same | L10 |
| `l70` | `meta-llama/Llama-3.1-70B` | NDIF, batch 1, the hour-64 layer subset | L32 |
| `l70_it` | `meta-llama/Llama-3.1-70B-Instruct` | NDIF, batch 1, same | L24 |

- **Extraction.** The 200 items are fed as raw sentences, exactly as the paper's core sets are,
  with the tokenizer's own single BOS (asserted). They go through the hour-64 extractor
  (`crossmodel.py`'s local hook path and NDIF pooled path), with `final_token` at every captured
  block and `embed_mean` at the embedding.
  - The NDIF items run at batch size 1, as amendment 2 of hour 64 required. That leaves no padding
    to equate.
  - The pain vectors, core and control sets are hour 64's local stacks. Each stack is checked
    against its recorded digest before use, and none are re-extracted.
- **Axis.** At each captured layer, each model's own S2 pain vector (`build_vectors`, unit norm),
  as in hour 64. Item scores are projections z-scored against the 200-item pool at that layer
  (`zscore_pool`). The **floor** is the same computation on `embed_mean`, projected on the
  embedding-level S2 vector (the hour-52/64 bag-of-embeddings floor).
- **Layer.** The primary readout is at each model's hour-64 screen layer, which was fixed before
  these stimuli existed. The full curve over captured layers is reported. No layer is chosen from
  this data (non-negotiable 4).

## Contrasts and statistics

For author `a`, model `m`, layer `L`, and base `b`, let `Δ_b = z(shame_b) − z(witness_b)`. The
contrast is paired within base, over 40 bases, and reported separately for the 20 `A1` and the
20 `D` bases.

- **Effect.** `Δ̄` is the mean of `Δ_b`. Its one-sided sign-flip p uses 100,000 seeded random
  sign assignments, identity included (2^40 cannot be enumerated). For the A1 and D subsets, all
  2^20 assignments are enumerated, so those p values are exact. The 95% interval is a
  10,000-draw bootstrap over bases, with seed 20260923.
- **Nulls** (non-negotiable 1, at every layer): |Δ̄| computed on 1,000 random unit directions, and
  on 250 S2 vectors built with shuffled pain/control labels. The effect clears the nulls when
  |Δ̄| exceeds **both** 95th percentiles.
- **Floors.**
  1. The *rewording floor* is `witness − base`: what appending any clause of this length does.
  2. The *lexical floor* is `Δ̄` on the bag-of-embeddings floor axis. The **network contribution**
     is `Δ̄(network) − Δ̄(floor)`, with a paired bootstrap interval.
- **Valence adjustment.** Every one of the 200 sentences is scored, without its trailing
  ` I feel:`, by `distilbert-base-uncased-finetuned-sst-2-english`. The score is logit(negative) −
  logit(positive), with the revision pinned at download and run locally before any activation is
  read. The adjusted effect is the intercept of the least-squares fit `Δ_b = α + β·Δval_b` over
  bases, where `Δval_b` is the shame − witness valence difference. Its 95% interval is a bootstrap
  over bases. `α` is the shame − witness difference at equal valence.
- **Positive control (instrument).** `z(base, A1) − z(base, D)`, meaning pain events against
  neutral events on the pain axis. It must exceed both null q95s at the screen layer. If it does
  not, the model does not read these sentences on this axis, and **that model's cells are
  unreadable, not null** (non-negotiable 3).

## Decision

A **cell** is one (model, author) pair at the screen layer. The cell **tracks shame** only if all
of the following hold:
1. `Δ̄ > 0` over all 40 bases, with sign-flip p ≤ .05.
2. It clears both nulls.
3. The network contribution over the lexical floor is positive, with its interval above 0.
4. The valence-adjusted `α` has its interval above 0.
5. The `D`-base subset alone has `Δ̄ > 0` with exact p ≤ .05. This is the reverse direction, shame
   without pain. A pain axis should not respond to it.

The cell must also pass the positive control. The claim's status is decided on the **two instruct
models** (`g2b_it`, `l70_it`), because the line's hypothesis concerns models after post-training.

- **holds**: all four instruct cells (2 models × 2 authors) track shame.
- **falsified**: no instruct cell tracks shame, every instruct cell passes the positive control,
  and in every instruct cell the valence-adjusted `α` interval includes 0 or lies below it. That
  means the axis reads valence, not evaluation.
- **narrowed**: anything else, with the boundary stated. Examples: only one author's set, which
  means the result depends on how the stimuli were written; only one model family; only pain-laden
  bases (A1 but not D).
- An instruct model that fails its positive control makes the claim **unreadable** on that model.
  If both fail, the claim stays `open` and the failure is reported.

**Secondary, which decides nothing:** the base models, and `Δ_post = Δ̄(instruct) − Δ̄(base)` per
family, author and base type, with paired bootstrap intervals. This extends hour 64's question
about post-training from the self/other split to evaluation. It also reports every cell's full
curve, the `A1`/`D` split, the rewording floor, `β`, and each author's effect separately
throughout.

## What this does not test

It uses one axis, the paper's S2 pain vector, read at one token. It is not a test of whether the
model *feels* anything, and not a test of a dedicated shame direction. A positive result says the
pain axis responds to evaluation by others beyond valence and vocabulary, which would earn the
line its name. A negative result says the axis is better described by valence, in these models, on
these stimuli. Both authors are language models who knew the hypothesis. The per-author
requirement limits that confound but does not remove it.
