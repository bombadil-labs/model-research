# Consequence binding across clause order (freeze before activation extraction)

## Question

The [fixed-predicate goal switch](goal_switch_result.md) produced a held-out
goal-by-recipient interaction, but the linked direction also scored on a rotated
goal control. Does an interaction follow **which unchanged worker plan would keep
people safe**, when the story states only the consequences of two paraphrased
conditions and the order of those conditions is independently reversed? This is a
small constructed-story inference, not a measure of a general trope shape.

## Frozen stimulus grid

`consequence_order_v1.json` keeps the same 12 domains, named workers, plans,
handover objects and bridge as the previous grid. Each domain adds two condition
phrases that paraphrase the results of the workers' opposed plans. No condition
phrase says which worker to choose. Every passage says the town wants its people
safe, then describes the two fixed plans. The report assigns `safe` to condition A
and `danger` to B, or the reverse. It also presents condition A first or B first.
The only final action hands the same object to one of the two workers. The JSON
freezes the exact town-goal, report-introduction, clause and outcome templates.
Each report contains the same `safe` and `danger` words once each; only their
binding to the condition clauses changes.

The previous grid put the active or enabling plan with worker A in every domain.
This grid assigns that original plan to A in six domains and to B in six, swapping
both the plan and its paraphrased condition. It keeps the original names and
handover recipients. Report the two polarity halves separately; a direction that
simply combines active-versus-restrictive plan polarity with the recipient should
reverse sign between halves. Some plans (raising versus lowering a bridge, filling
versus emptying a cistern) are both actions, so this operational split does not
exhaust all semantic polarity cues.

Cross worker-plan order (2), consequence mapping (2), report-clause order (2),
and handover recipient (2): 16 passages per domain, 192 total. Condition phrases,
plans, names, object and final sentence stay fixed across consequence mappings.
Mapping pairs have the same word multiset, character length and final 200
characters. The report stands outside that final window. Clause order is
orthogonal to consequence mapping; each order has the same vocabulary and
condition-to-outcome facts. The two candidate recipients share the same prefix
through the bridge period.

Before extraction, assert these text invariants and that matched cells have the
same final token ID and position. Assert identical tokenized prefixes through the
pre-action bridge period for recipient pairs. Every passage must fit the model's
trained context. Model: `Qwen/Qwen2.5-1.5B` revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16. One
passage per forward, checkpoint per domain. Record grid/code/model/device/dtype,
library versions and activation digests in ignored local provenance.

## Measurement and controls

At the final period token, for each domain, worker-plan order, report-clause
order and layer, form

`I = unit((safe-A,R0 − safe-B,R0) − (safe-A,R1 − safe-B,R1))`.

The mapping index refers to **which condition is safe**, not which clause is
first. For each held-out domain, fit a mean direction on the other eleven
domains' two worker-plan orders from one report-clause order. Score the held-out
interaction both at that clause order and at the opposite clause order. Repeat
with each clause order as the training source. The primary accuracy is the mean
of the two **cross-order** transfers over fixed layers 10–18. Report both
within-order scores, the cross-order scores, the active-A and restrictive-A
domain halves, and all layer curves. A signal based on the first safe clause
should reverse across clause order; a signal based only on the original active
plan should reverse between polarity halves. A consistent condition-to-recipient
relation should transfer across both.

Use 2,000 bootstrap resamples of the 12 domains on the fixed held-out
predictions for the primary interval. For 1,000 permutation draws, flip the
consequence-mapping label jointly across both clause orders and both worker-plan
orders within each domain, refit the directions and rescore. Report 1,000 random
Gaussian directions. Calibrate the scorer with known-signal and noise synthetic
states. These exact arms must score 0.5:

- **Local-only:** within each recipient and fixed clause order, the last 200
  characters are identical between consequence mappings; an activation of only
  that local string has zero interaction.
- **Pre-action:** before the handover, recipient choices have identical prefixes;
  their difference of mapping differences must be bit-exact zero.
- **No-mapping:** compare each state with itself as its mapping alternative.
- **Layer 0:** every final readout has the same token ID and position; the
  interaction must be bit-exact zero.

The lexical bag is also equal between mappings at fixed clause order. Report a
bag-of-words baseline as a tie rather than treating it as evidence that the
ordered phrasing is understood semantically.

## Prediction and decision

The cross-order signal passes only if mean held-out accuracy is at least 0.70,
exceeds random-direction mean by at least 0.15, permutation p is at most 0.05,
and the 95% domain-bootstrap lower endpoint exceeds 0.5. Both transfer
directions and both active-polarity halves must exceed 0.5; otherwise an
average can hide one reversed order or one sign-flipped polarity group.
Compare cross-order with within-order accuracy descriptively. Passing would
support a consequence-to-recipient interaction that survives reversal of report
position in these miniatures. It would still permit lexical paraphrase matching
and would not establish a causal narrative coordinate or transfer to natural
stories. Failure leaves the implicit-role-fit claim open at this resolution.
