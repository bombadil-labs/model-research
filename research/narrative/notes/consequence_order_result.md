# Consequence binding fails under report-order reversal

## Design and provenance

The [registered probe](consequence_order_prereg.md) held two workers' plans and
the final handover fixed, while changing which plan's paraphrased result the
council report called safe. It independently reversed the order of the two
report clauses. Twelve domains crossed two worker-plan orders, two consequence
mappings, two report-clause orders and two recipients, yielding 192 passages.
The original active or enabling plan belonged to worker A in six domains and
worker B in six. Each mapping comparison had the same word multiset, character
length, final 200 characters, final token ID and final token position. The cue
stood outside the final 200-character window. Tokenizer preflight and all
pre-action prefix checks passed.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16. The
[committed summary](../results/consequence_order_summary.json) includes the
model and library versions, grid/code/activation digests and every layer curve.
Raw activations remain in ignored `cache/consequence_order`. A score-only rerun
reproduced the extracted report exactly.

At the final period token, the interaction contrasts the two consequence
mappings across the two recipients. For each held-out domain, a direction was
fit on the other eleven domains' two worker-plan orders at one report-clause
order. It was tested both at that same order and at the opposite order. The
primary measure averaged the two **cross-order** transfers over layers 10–18,
fixed before extraction. Domain was the bootstrap and permutation unit.

## Registered results

| Fixed layers 10–18, mean held-out accuracy | Result |
| --- | ---: |
| Within clause order 0 | **0.954** |
| Within clause order 1 | **0.921** |
| Train order 0, test order 1 | **0.125** |
| Train order 1, test order 0 | **0.097** |
| Primary cross-order mean | **0.111** [0.079, 0.141] domain bootstrap |
| Cross-order, active plan assigned to A / B | **0.134 / 0.088** |
| Permutation, 1,000 draws | mean 0.499, upper-tail p = 1.000 |
| Random direction, 1,000 draws | mean 0.502, 95% span 0.456–0.542 |
| Pre-action / no-mapping / layer 0 | **0.500 / 0.500 / 0.500**, exact ties |
| Actual local suffix trigrams / full word bag | **0.500 / 0.500** |
| Synthetic signal / noise scorer calibration | **1.000 / 0.454** |

The registered cross-order criterion fails decisively: both transfer directions
are below chance, as are both polarity halves. Scores learned and tested with
the same clause order are high, but reversing the two report clauses nearly
reverses the sign of the learned interaction. The full curve shows this across
the fixed band and most other layers; choosing a different layer after seeing
it would not rescue the registered result. The upper-tail permutation p is
reported as specified; this run did not register a lower-tail significance
test. The bootstrap interval and control arms support the descriptive finding
that the transfer is strongly anti-aligned.

The active-plan assignment balance rules out a pure original-active-task
direction as the source of a positive cross-order score; its synthetic analog
scores zero under leave-one-domain-out. It does not explain why the actual
cross-order score is below chance. A report-position or recency interaction is
consistent with the reversal, but this probe does not isolate which textual
feature produces it. The cue paraphrases still share content words with the
plans, and these are short, formulaic stories.

## Implication

The large within-order values are not evidence for a stable consequence-to-role
coordinate. On this grid, the measured interaction is tied to the report's
sentence order more strongly than to the consequence relation it was designed
to test. This narrows the implicit-goal-role-fit claim and reinforces the need
for independent wording and order controls before treating a local direction
as part of a reusable narrative shape. The open full-story Propp context test
remains the next route to whether longer narrative context changes an event's
role under the same local wording.
