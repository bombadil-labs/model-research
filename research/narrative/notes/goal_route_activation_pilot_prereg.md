# Conditional activation pilot for the goal × route interaction

**Written before extracting any activation on the crossed grid.** Run only
if the behavioral screen in `goal_route_cross_prereg.md` passes its direct,
repeatability and two-link gates. This is an eight-domain pilot to decide
whether an activation-level confirmation on a larger grid is worth doing.
It cannot establish a reusable narrative transform by itself.

## State, contrast and location

Use the exact 256 story prompts, tokenizer revision and Gemma-2-9B-it NDIF
deployment of the behavioral screen. For each prompt, capture the residual
stream **after** decoder blocks with zero-based indices `[0, 8, 16, 24,
32, 40]`, at the final real input token immediately before the scored
worker-name continuation. The final token ID, prompt question and last
200 text characters must match across each four-cell set. Record checkpoint,
deployment metadata, tokenizer snapshot, library versions, grid/code digests,
and the six block indices. NDIF exposes no weight revision hash.

Let `h(w,g)` be that vector for a fixed domain, telling, name assignment,
plan order and layer. Form the directed factorial interaction

`I = h(0,0) − h(0,1) − h(1,0) + h(1,1)`.

Its sign is oriented so the A-owner is correct in `(0,0)` and `(1,1)`.
Normalize each nonzero `I` to unit length before fitting. A goal-only or
world-only *additive* state cancels exactly. The full-text word-bag and
last-200-character interaction vectors must be computed and reported; both
are expected to be zero. These are surface nulls, not evidence that the
model's residual has the same property.

## Held-out transfer and null

For each held-out domain `d` and target telling `t`, fit a direction from
the **other seven domains in the opposite telling**: average their unit
interaction vectors over both name assignments and both plan orders, then
unit-normalize that mean. Score the held-out domain's four individual
name×plan interaction vectors in telling `t` by cosine with the fitted
direction. Average the four cosines per `(d,t)`, then average over the
eight domains and two target tellings. This is the primary directed transfer
statistic; a representation that flips sign under telling order scores
negative, even if its pairwise distances stay the same.

Freeze the primary layer statistic as the mean of **block 16 and block 24**
transfer scores. Report the full six-block curve and both transfer
directions, without selecting a better block from the data. Form the exact
orientation null by swapping the two world labels jointly across both goals
and both tellings within each domain, enumerating all `2^8` sign choices.
For each assignment, refit every seven-domain direction and rescore every
held-out domain. Bootstrap the eight fixed domain-level scores for 10,000
draws and report the 95% interval. Also compare with 1,000 seeded random
unit directions per block (a zero-centered calibration, not a second
selection rule).

## Measurement checks and decision

Extract one prompt per remote job, so no row-padding convention enters the
final-token readout. Resolve block output by tensor type, never by
`output[0]`. Save only the selected final-token vectors, and fingerprint
every checkpoint row with exact rendered prompt, model, grid and code.
Refuse stale rows; retry co-tenant OOM or timeout at the same job shape.

Repeat the fixed `(world=0, goal=0, early, name=0, plan=0)` prompt once in
each domain in a separate identical job. The maximum repeated-vector L2
drift at each block must be ≤1% of that block's median nonzero interaction
norm. On one frozen prompt, compare the new extractor's final-token vectors
at blocks 16 and 24 against `lsx.core.remote.remote_residuals` run on the
same single prompt; require cosine ≥0.999 and relative L2 error ≤0.01.
If an interaction norm is within ten times the maximum repeat drift for
its block, report it as unresolved and disclose the count. All four
name×plan interactions in every domain and telling must clear this floor
at blocks 16 and 24; otherwise the primary pilot is unreadable. Other
blocks' unresolved interactions are omitted from their descriptive curves
with the denominator reported.

Call this pilot **a candidate aligned interaction** only if the fixed
block-16/24 mean transfer is positive, exact upper-tail p ≤0.05, its
domain-bootstrap 95% lower bound >0, and each telling direction has
positive domain-mean transfer in at least six of eight held-out domains.
Report failures and all controls regardless. Passing would show that a
directed interaction in the residual transfers across these miniature
stories and tellings. It would not show that this interaction causes the
model's choice, is a plot component, or extends to full stories. Those
require a held-out intervention and a larger, independent domain set.
