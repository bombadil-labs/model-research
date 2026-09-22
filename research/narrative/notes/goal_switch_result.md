# Fixed-predicate goal switch: signal without goal specificity

## Design and provenance

The [preregistered goal-switch probe](goal_switch_prereg.md) kept each worker's
plan, actor binding and final handover fixed while reversing which of two needs
the group named. The two goal sentences have the same words in a different order.
Twelve domains each supplied two worker-plan orders, two goal orientations and
two handover recipients: 96 linked passages. A control used the next domain's
goal phrases with the same workers and handover: 96 rotated passages. The cue
stood more than 200 characters before the final readout. Token preflight passed
all matched-cell checks and verified that every passage fit the model's
131,072-position configuration.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16.
Activation stacks and detailed provenance remain in ignored `cache/goal_switch`;
the committed [summary](../results/goal_switch_summary.json) records the model,
environment, input/code and activation digests, all layer curves and scores.
The score-only rerun reproduced the extracted run's report exactly.

At the final period token, the per-domain, per-order interaction was

`I = unit((G0R0 − G1R0) − (G0R1 − G1R1))`.

Each held-out domain was scored against a direction fit on the other eleven;
both sentence orders contributed to each fit. The primary band was fixed at
layers 10–18 before extraction. The linked direction was also scored on the
rotated goal control, and a separate direction was fit on the rotated grid.
The domain was the bootstrap unit.

## Registered result

| Fixed layers 10–18, mean held-out accuracy | Result |
| --- | ---: |
| Linked goal-switch interaction | **0.708** |
| 95% domain bootstrap interval | 0.583–0.829 |
| Linked direction on rotated goals | **0.616** |
| Linked minus rotated, paired domain bootstrap | **0.093** [−0.037, 0.227] |
| Rotated goal interaction on itself | **0.505** |
| Domain-orientation permutation, 1,000 draws | mean 0.504, p = 0.018 |
| Random direction, 1,000 draws | mean 0.498, 95% span 0.426–0.574 |
| Pre-action / no-goal / layer-0 controls | **0.500 / 0.500 / 0.500**, exact ties |
| Synthetic signal / noise calibration | **1.000 / 0.523** |

The linked grid passes the registered positive screen: accuracy at least 0.70,
random-direction advantage above 0.15, permutation p at most 0.05, and a
bootstrap lower endpoint above chance. The stronger **goal specificity** gate
fails: the linked-minus-rotated gap is below the required 0.15, and its paired
interval crosses zero. This run therefore does not establish that the direction
represents which plan actually fits this group's need.

The rotated grid's self-fit score is near chance, yet the linked direction
transfers to it at 0.616. The result is consistent with a shared goal-order,
active/passive or other surface component; this design cannot choose among those
explanations. Layers 15–18 show larger linked-versus-control separation than
the fixed band, but choosing those layers after seeing the curve would be a new
test and cannot rescue the registered specificity result. All layer scores are
in the summary.

## What this changes

The earlier [action-interaction probe](action_interaction_result.md) found a
component beyond one neutral-predicate control. This probe fixed the plans and
predicates while changing the explicit group goal. A context-sensitive
goal-by-recipient interaction survived held-out domains and exact pre-action,
no-goal and layer-0 controls. The necessary contrast against rotated goals did
not survive its prespecified gate. The result narrows the fixed-predicate claim
and leaves narrative role-fit, natural-story recognition and causal control open.

The next discriminating design should express the group's need through a
situation rather than the explicit `needed A, not B` phrase, hold worker plans
and handover fixed, and match the control for sentence order and local lexical
cues. Its acceptance gate must compare relevant against irrelevant situations
on held-out domains before any layer is selected.
