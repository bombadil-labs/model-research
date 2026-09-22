# Fixed-predicate goal switch (frozen before activation extraction)

## Question

The action-interaction spike found a goal-grid component beyond one neutral-predicate
control, but the goal and neutral grids used different actor predicates. Can a
held-out-domain activation direction track **which fixed worker plan fits the group's
current need**, when the workers, their plans and the final handover are unchanged?
This tests a necessary compositional relation in constructed stories. A positive is
still compatible with semantic word matching and is not a trope manifold.

## Frozen grid and controls

`goal_switch_v1.json` has 12 domains. Each has two named workers with fixed, opposed
plans; two group goals that make one plan or the other appropriate; an object the
courier hands to one worker; and a neutral bridge. For each domain, cross two orders
of the worker-plan sentences, two orientations of the group-goal sentence, and two
handover recipients. The linked grid therefore has 96 passages. The goal sentence
uses the *same words* under its two orientations: `needed A, not B` versus
`needed B, not A`. Actor-plan text and final handover are unchanged within each
goal comparison. The goal cue is more than 200 characters before the final readout.

The control grid keeps that domain's workers, plans, object and handover, but uses
the next domain's pair of goal phrases, wrapping from domain 12 to domain 1. This
fixed rotation gives 96 further passages. Across the dataset, the control uses the
same goal vocabulary and the same goal-order manipulation, while the desired
outcome no longer names the current workers' task. Some rotated goals may still
share an abstract active/passive relation with the workers' plans; measure that
transfer rather than assuming its null is exactly chance.

Before extraction, assert for every matched goal pair: identical character length,
word multiset, final 200 characters, final token ID and token position. Assert the
same final token ID and position between linked and rotated control for each
domain/order/goal/recipient cell. Assert the pre-action token prefix is identical
between recipient choices at each fixed goal and that each cue is outside the final
200-character window. All inputs must fit the model's trained context. Refuse a
violating cell. Model: `Qwen/Qwen2.5-1.5B` revision
`8faed761d45a263340a0528343f099c05c9a4323`, CUDA float16. One passage per
forward, checkpoint per domain and grid. Record grid/code/model/device/dtype and
activation digests in ignored local provenance.

## Fixed measurement and nulls

At the final period token, with `G0/G1` the two goal orientations and `R0/R1` the
two recipients, form the raw interaction for each domain, worker-plan order and
layer:

`I = unit((state(G0,R0) − state(G1,R0)) − (state(G0,R1) − state(G1,R1)))`.

For each held-out domain, fit the mean of the other 11 domains' two unit
interactions and score the held-out interaction's cosine sign. Positive gets 1,
negative 0, exact zero 0.5. Fit on linked-grid training domains and score both
linked and rotated held-out interactions; also fit and score the rotated grid on
itself. Report all layers, with the already fixed primary mean over layers 10–18.
Resample the 12 domains 2,000 times for intervals on fixed held-out predictions,
including the paired linked-minus-rotated score. Flip orientation jointly for both
worker-plan orders within each domain for 1,000 permutation draws and refit the
direction. Report 1,000 random Gaussian directions, a synthetic shared-signal and
noise calibration, and these exact controls:

- **Pre-action contrast:** compute the same recipient interaction at the bridge
  period before the handover. Since the prefix is identical across recipients,
  this must be bit-exact zero and score 0.5.
- **Layer 0:** the final period token has the same ID and position in every cell;
  its interaction must be bit-exact zero and score 0.5.
- **No-goal arm:** compare each state with itself in place of a goal swap;
  its interaction must be bit-exact zero and score 0.5.

## Prediction and decision

The linked interaction is a positive screen only if its fixed mid-layer accuracy
is at least 0.70, exceeds random mean by at least 0.15, has permutation p ≤ 0.05,
and has a domain-bootstrap 95% lower endpoint above 0.5. The stronger claim that
the interaction depends on the *appropriate goal for these workers* also requires
a linked-minus-rotated gap of at least 0.15 and a paired domain-bootstrap lower
endpoint above zero. If linked and rotated align similarly, the result is a general
goal-order or active/passive pattern, not domain-specific goal matching. If both
fail, this design does not detect a transferable relation at its resolution.
