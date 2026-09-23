# Cross the requested destination with the two-link route fact

**Frozen before any score on this grid.** The previous eight-domain two-link
screen established that a fixed goal can move plan preference when a
terminal route fact changes. It did not establish that the representation
of the *requested destination* and the representation of the route facts
combine as separate factors. This follow-up crosses those factors. It is a
behavioral gate for a later activation experiment, not itself evidence of
latent geometry.

## Grid and prediction

`research/narrative/prompts/goal_route_cross_v1.json` freezes the exact
sentences. It inherits the previous route→link structure, fact-clause orders,
name pairs, two tellings and question. Five foil destinations were replaced
before this run so that sending the item to either destination is plausible:
clinic→dispensary, reading room→archive room, shelter→field hospital,
assembly bench→repair bay, and engine room→supply locker. Four direct-route
controls remain independent of the eight two-link domains. The two goals
for every row are literal `goal` and `goal_foil` strings in the grid. They
differ only in the stated destination; no model output was used to choose
them. The earlier score cache is **not** reused because the grid and goals
have changed.

Each domain has four causal cells, crossing route world `w` and goal `g`:

| | Goal names destination A | Goal names destination B |
| --- | --- | --- |
| Route A reaches destination A | Plan A | Plan B |
| Route A reaches destination B | Plan B | Plan A |

The route facts change only by exchanging destination nouns between the two
second-hop clauses. The goal changes only by naming the other destination.
The setup, plans, name assignment, first-hop facts, bridge and question
remain fixed within a four-cell set. Both goal conditions keep the final
200 characters identical, and within either goal the two worlds have the
same full-text word multiset and length. Each four-cell set crosses an early
versus late fact telling, both name assignments and both plan-sentence
orders. Thus 8 domains × 4 causal cells × 2 tellings × 2 names × 2 plan
orders = **256 story score prompts**. Four direct-route domains give **128
control prompts**. The first-hop order × second-hop order quadrants remain
balanced two domains each. The two surviving subjective semantic-prior
labels (theater and orchard) are descriptive only.

The model is the same pinned NDIF `google/gemma-2-9b-it` deployment. Record
checkpoint, tokenizer snapshot revision, exposed deployment metadata,
library versions, grid and scorer digests. NDIF does not expose a weight
revision hash; state that limitation. Score the two bare worker names
alphabetically in one `asserted_remote_patched_logprob` job per prompt.
Preflight every prompt for one BOS, equal candidate-token counts, unchanged
prompt prefix, and matched world lengths within each goal. Use the same
two-candidate batch shape throughout. Checkpoint each job under a fingerprint
of its rendered prompt, candidates, grid, model and scorer, and refuse stale
rows. Retry transient NDIF queue/OOM failures at the same size.

## Measurement and controls

Let `m(w,g) = logp(name for plan A) − logp(name for plan B)`. The two
correctly oriented world contrasts are:

- `D0 = m(0,0) − m(1,0)` when goal 0 names destination A;
- `D1 = m(1,1) − m(0,1)` when goal 1 names destination B.

`I = D0 + D1 = m(0,0) − m(1,0) − m(0,1) + m(1,1)` is the factorial
interaction. A four-cell set succeeds only if **both** `D0` and `D1` exceed
+0.25 nat. Report each contrast, the interaction, wrong contrasts below
−0.25, near-zero contrasts, and the strict four-cell choice rate (all four
correct names have margins beyond ±0.1 nat). A goal-only rule cannot make
either world contrast positive. A route-only rule may make one positive but
must make the other negative. A fixed name or plan-position preference
cancels within the contrasts. An ordinal shortcut linking clause positions
gets the same two fact-order quadrants right and two wrong as in the first
screen, so a per-quadrant gate remains essential. Report these frozen
shortcut ceilings; a graph traversal plus goal match solves all four cells.

The direct-route arm is an independent positive control. Its gate is at
least 24/32 four-cell sets with both world contrasts >+0.25, with each
telling half >0.5. A separate no-change arm repeats the fixed world-0,
early-telling, name-0, plan-order-0 prompt for **both goals in all eight
story domains** (16 extra jobs). Report candidate and margin differences
against the first score; the largest absolute margin difference must be
≤0.25 nat. Run story and generation arms even if a direct control fails,
but then treat story scores as descriptive until the readout is repaired.

For the orientation null, flip the two world labels jointly for both goals
and all telling/name/plan variants in each domain, enumerate all `2^8`
assignments, and compare the observed both-contrasts-correct fraction with
the exact upper tail. Bootstrap over eight fixed domain-level success rates
for 10,000 draws. The no-change and exact-null arms are reported with the
direct and story arms; an off-null control is a measurement problem.

Greedy generation runs after scoring on the fixed subset with name and plan
order 0: 8 domains × 2 tellings × 4 causal cells = **64 prompts**. Parse
only one worker name plus optional whitespace or punctuation. Report
parseability, agreement with the forced-score winner, and how many of the
16 four-cell sets generate all four correct names. At least 90%
parseability and 90% agreement among parseable outputs are required before
interpreting forced scores as a generated-choice readout. Generation
cannot rescue a failed score screen.

## Decision rule

Call **goal × route-fact sensitivity established on this constructed grid**
only if all of the following hold:

1. The direct-route and no-change gates pass.
2. At least 42/64 two-link four-cell sets have both `D0` and `D1` >+0.25,
   and each goal's contrast separately succeeds in at least 48/64 sets.
3. The exact domain-orientation upper-tail p ≤0.05 and the domain-bootstrap
   95% interval for joint success has lower bound >0.5.
4. Both telling halves have joint success ≥0.60; both name-assignment and
   plan-order halves are >0.5; each fact-order quadrant is >0.5.

Report every gate component, strict four-cell choice rate, individual-domain
rates and any semantic-prior split. A positive result would make an
activation-level study of a composed goal–route relation worthwhile. It
would not show a reusable geometric direction or any ability to edit a
story's plot. A negative result after passing controls would limit this
small model and readout on this grid, with the plausibility of specific
destinations and the eight-domain size stated as limitations.
