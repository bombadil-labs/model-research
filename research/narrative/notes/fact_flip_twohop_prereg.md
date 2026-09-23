# Two-link fact flip across early and late reveal (frozen before scores)

## Question

The preceding goal-reversal run did not reach its stories: its forced-name
readout failed crossed controls. Its story grid also admitted a goal-category
to plan-verb shortcut on 21/24 matched pairs. This spike holds the goal, both
plan sentences and both candidate names fixed while changing **one route
fact** that reverses which plan reaches the goal. Does the model's paired
preference move with that fact when the necessary information spans two
links, and does it do so whether the links are told before or after the
plans? This is a behavioral prerequisite for reading narrative relations in
activations, not a geometry result.

The exact eight two-link domains and four independent direct-route controls
are in `research/narrative/prompts/fact_flip_twohop_v1.json`. Each two-link
story has plan A use route A and plan B use route B. Route A joins link A and
route B joins link B in both worlds. In world 0, link A reaches the stated
destination; in world 1, link B does. The two terminal destination nouns
swap between second-link clauses. The goal, plans, first-link facts, names,
setup and every other word stay fixed. Two tellings use exactly the same
sentences: chronological places the facts before the plans; late reveal
places the plans before the facts. A common neutral bridge and question end
both. This is a disclosure-order change, not a contradictory plot twist.

The eight domains balance first-link clause order × second-link clause order:
two in each of the four cells. Each domain crosses two name assignments and
two plan-sentence orders independently of the telling and world. That makes
8 × 2 worlds × 2 tellings × 2 names × 2 plan orders = **128** two-link prompts,
or 64 world pairs. Four direct-route controls each replace the two-link
chain with one explicit route→destination sentence per route. They cross the
same world, telling, name and plan-order factors, giving 64 control prompts
and 32 world pairs. The direct fact-clause order is two/two. The controls
are independent of the two-link domains.

The prompt is a single user chat turn ending with the grid's exact question.
The model is NDIF's pinned `google/gemma-2-9b-it`. Record the checkpoint,
deployment metadata, local tokenizer snapshot revision, library versions,
code and grid digests. NDIF does not expose a weight revision hash; say so in
the artifact. The scored candidates are the two bare names in alphabetical
order in one `asserted_remote_patched_logprob` job. Verify one BOS, equal
candidate token counts, unchanged prefix tokenization and the same two-name
batch shape for every cell. Checkpoint each result under a fingerprint of
its exact rendered prompt, candidates, model and scorer. Refuse stale rows.
Retry/resume NDIF queue or OOM failures at the same batch size.

## Pre-score invariants and shortcut ceilings

For every matched world pair, assert the two rendered story bodies have
identical lower-case word multisets, with only the two destination nouns
exchanging clauses. The goal and both plan sentences must be byte-identical
within the pair. The final 200 characters, including bridge and question,
must be identical. In two-link stories, neither route name nor worker name
occurs in a terminal-destination clause, and the goal destination never
occurs in a plan or first-link clause. Assert exactly one mention of each
worker name. The route/link/destination graph is traversable and has exactly
one target-reaching plan in each world.

The full-text word bag, a bag of each worker's plan sentence and direct
route–target co-occurrence cannot distinguish the two worlds in a two-link
domain. Each has `Δ = 0` and therefore zero shifts above the +0.25 primary
threshold; if forced to classify individual worlds, ties have 0.5 accuracy.
A rule that maps the target's second-link clause *ordinal position*
to the route at the same first-link clause ordinal position gets 4/8 domains
right because the two clause orders are crossed. A rule that always chooses
route A when the target is in the first second-link clause also gets 4/8.
Freeze and report these ceilings beside the model. A symbolic two-link graph
solver gets 8/8. Passing the model screen would establish composition of
explicit route relations in these miniatures, not recognition of a broad
narrative trope or a continuous latent shape.

## Measurement and arms

For each cell let `m = logp(name for plan A) − logp(name for plan B)` after
mapping candidate scores back from alphabetical order. World 0 makes A
correct, world 1 makes B correct. The paired shift is `Δ = m_world0 −
m_world1`. A correct fact response requires `Δ > +0.25` nats. Report also
wrong shifts (`Δ < −0.25`), near-zero shifts, and strict choice reversals
(`m_world0 > +0.1` and `m_world1 < −0.1`). The paired shift is primary because
it cancels stable name and plan-position priors that defeated the earlier
absolute-choice gate. Strict choice reversal remains the secondary behavior
needed for eventual story writing.

Run every arm on the frozen grid, including the treatment if a control fails;
control failure then prevents a validated-readout claim, and treatment scores
remain descriptive. The direct-route arm is the positive control. Its gate
is at least 24/32 correct paired shifts, with both telling halves above 0.5.
The no-change arm repeats, in a separate identical two-name job, the fixed
world-0 chronological/name-0/plan-order-0 prompt once per two-link domain
(eight extra jobs). Report the per-candidate and margin differences; require
the largest absolute margin difference ≤0.25 nats as a repeatability gate.
The random-orientation null flips world labels jointly across all eight
pairs of a domain, enumerates all 2^8 assignments, and compares the observed
correct-shift fraction with this exact distribution. These three arms are
reported together; a direct control or repeatability failure is a measurement
problem, not a negative finding about two-link reasoning.

Greedy generation, at most eight new tokens, runs on a fixed subset after
scoring: both worlds × both tellings at name order 0 and plan order 0 for
every two-link domain (32 prompts). Parse only a continuation consisting of
one of the two names plus optional punctuation or whitespace. Report
parseability, agreement with the forced-score winner, and actual generated
choice reversals. At least 90% parseability and 90% agreement among
parseable outputs are required before calling the forced-score result a
faithful generated-choice readout. Generation is secondary and cannot rescue
a failed paired-shift screen.

## Decision rule

The primary two-link statistic is the fraction of 64 paired shifts above
+0.25. Call **two-link fact sensitivity established on this grid** only if:

1. Direct-route and no-change control gates pass.
2. At least 48/64 two-link pairs have correct shifts.
3. The exact domain-orientation upper-tail p ≤ 0.05 and the 10,000-draw
   domain-bootstrap 95% interval has lower bound > 0.5.
4. Each telling half has correct-shift fraction ≥ 0.65; each name-assignment
   and plan-order half is > 0.5; each of the four fact-order quadrants is > 0.5.

Report every component whether it passes or fails. Generation gates govern
only the stronger generated-choice interpretation. If the shift screen
passes but strict choice reversals or generation do not, the conclusion is
limited to fact-dependent movement of the forced-name score. No activation
direction, causal intervention or high-dimensional story shape is claimed
from this behavioral battery alone.
