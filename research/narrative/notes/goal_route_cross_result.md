# Plan preference depends jointly on the goal and two-link facts

## Design and provenance

The [preregistered crossing](goal_route_cross_prereg.md) asked whether a
fixed pair of worker plans changes preference when either the requested
destination or the second-hop route fact changes. Each of eight constructed
story domains has four cells: two route worlds × two destination goals. The
correct plan follows an XOR pattern: A in cells `(world,goal)=(0,0)` and
`(1,1)`, B in `(0,1)` and `(1,0)`. The grid crosses early versus late fact
telling, name assignment, plan-sentence order and four balanced fact-clause
order quadrants. Four independent direct-route domains test the readout.
The [exact grid](../prompts/goal_route_cross_v1.json), scorer and decision
rule were committed and adversarially reviewed before any new model score.

Model: NDIF's pinned `google/gemma-2-9b-it` deployment, local tokenizer
snapshot `11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF reports the
checkpoint but no weight revision hash; exact replay depends on the pinned
deployment remaining the same. The [committed summary](../results/goal_route_cross_summary.json)
contains library/deployment metadata, grid and scorer digests, every margin
and goal-specific contrast, generation outputs and every gate component.
Raw candidate scores and NDIF job logs remain in ignored
`cache/goal_route_cross/v1`. All 384 unique score prompts passed one-BOS,
equal-candidate-token, unchanged-prefix and within-goal matched-world
token-length preflight. Each score was a separate job with the same
two-candidate batch shape.

## Registered outcome

For the margin `m = logp(A-owner name) − logp(B-owner name)`, the two
correctly oriented world contrasts are `D0 = m(0,0) − m(1,0)` and
`D1 = m(1,1) − m(0,1)`. A four-cell set succeeds only when both exceed
+0.25 nat.

| Measurement | Observed | Registered gate |
| --- | ---: | --- |
| Independent direct-route sets with both shifts | **32/32** | Pass (≥24/32; both telling halves >0.5) |
| Separate-job identical repeats | Maximum margin difference **0** across 16 prompts | Pass (≤0.25 nat) |
| Two-link sets with both shifts | **57/64** | Pass (≥42/64) |
| Goal 0 / goal 1 shifts separately | 57/64 / 58/64 | Pass (each ≥48/64) |
| Exact eight-domain orientation null | p = **1/256 = 0.0039** | Pass (≤0.05) |
| Domain-bootstrap 95% interval for joint success | **0.781–0.969** | Pass (lower >0.5) |
| Early / late telling joint success | 29/32 / 28/32 | Pass (each ≥0.60) |
| Fact-order quadrants 00 / 01 / 10 / 11 | 11/16 / 16/16 / 16/16 / 14/16 | Pass (each >0.5) |
| Strict forced-score correctness in all four cells | 49/64 | Secondary; no gate |
| Greedy generation, fixed subset | 64/64 parseable and in agreement with forced-score winner; 13/16 all-four-correct sets | Readout gates pass |

The name-assignment halves were 27/32 and 30/32; plan-order halves were
30/32 and 27/32, clearing every registered split. The exact null's mean
was 0.492 and 95th percentile 0.734. Every behavioral gate passes. The
claim therefore **holds on this constructed grid**: preference responds
jointly to the requested destination and the two-link route facts, in both
tellings. Goal-only, route-only, stable name and plan-position rules cannot
make both contrasts positive. Clause-order shortcuts solve only half the
domains and fail the registered quadrant gate. This is behavioral evidence
that the model can combine an explicit goal with two route links.

## Misses and scope

The joint result is not uniform: clinic had 6/8 successes, library 5/8,
ship 6/8, and the other five domains 8/8. The 00 fact-order quadrant was
weakest at 11/16. The two domains with frozen subjective route-prior labels
were 16/16; neutral-labelled domains were 41/48. That split does not explain
the remaining failures. The two prior labels and the eight-domain sample
are too thin for a general conclusion about semantic priors.

The paired score shift is easier than choosing correctly in every cell.
Strict forced-score four-cell correctness was 49/64. On the fixed generated
subset (one name assignment and plan order), 13/16 sets generated all four
correct names; factory's early telling and both ship tellings favored the
B-owner name in two A-correct cells. Those generation errors are compatible
with a persistent name or position preference overriding a correct
goal–fact effect. The generation subset does not estimate the full-grid
choice rate.

The positive screen warrants a [pre-frozen activation pilot](goal_route_activation_pilot_prereg.md).
It does not itself show an aligned residual direction, a causal edit, a
story component that can be transformed, or a hero's-journey shape. The
stories are short, explicit route problems; testing literary narrative
structure still requires larger and less templated material.
