# Action interaction after the role-swap audit (frozen before new extraction)

## Why

The first controlled role-swap spike found a context-sensitive final-token displacement, but
neutral predicates also produced a strong direction and sentence order dominated raw deltas.
That instrument may be reading which earlier predicate belongs to the recipient. The next
necessary test for an event-role representation is whether the prior-goal displacement changes
when the **final action reverses who receives the same object**.

## Frozen material

Reuse the 12 domains, two earlier sentence orders, and two actor assignments from
`role_swap_v1.json` and `role_swap_neutral_v1.json`. For each existing passage, replace only
the final sentence `giver handed the object to recipient.` with
`recipient handed the object to giver.` The reverse-action grids have the same 48 cases each.
The earlier prefix, including the period after `By dusk the two figures met again.`, is
identical for forward and reverse. The original forward activations are the already cached
stacks; only reverse passages need a new forward pass. Record the pre-action state at that
bridge period and the final state at the reverse handover period in the same pass.

Check, before extraction: within each new reverse-action pair, identical word multiset,
character length, last 200 characters, final token ID and position; the earlier actor cue
ends more than 200 characters before the final readout. Check forward and reverse inputs
have exactly the same token IDs through the pre-action period. The longest input must fit
the model's context. Refuse any failed invariant.

Use the same checkpoint, revision, CUDA float16, tokenizer and local GPU lock as the first
spike. Checkpoint each domain for each grid, with grid, code, model, device, dtype, and
activation digests in ignored local provenance. Pin the exact model in the committed
result note per Mykola's explicit instruction.

## Fixed measurements

At each layer and for each domain/order, let `D_f` be the unit-normalized forward-action
`helps − harms` displacement and `D_r` the unit-normalized reverse-action displacement.
The reverse-action label stays tied to the earlier predicate assignment, so an *event-role*
component should invert when the recipient changes. Let `D_pre` be the unit-normalized
`helps − harms` displacement at the pre-action bridge period. Let the action interaction be
`I = unit((F_helps − F_harms) − (R_helps − R_harms))`, using raw paired differences before
the final normalization.

For each held-out domain, fit directions on both orders of the other 11 domains. Report
the full layer curves and the pre-fixed mean over layers 10–18 for:

1. **Forward replication:** direction fit and scored on goal-grid `D_f`.
2. **Reverse as event:** direction fit on goal-grid `D_f`, scored on `−D_r` of the held-out
   goal domain. Score on unflipped `D_r` too, to expose a shared binding component.
3. **Pre-action binding:** goal-grid `D_f` direction scored on `D_pre`.
4. **Action interaction:** direction fit on goal-grid `I`, scored on held-out goal `I`.
   Apply that same held-out-domain direction to neutral-grid `I`; report the paired
   goal-minus-neutral score. Also fit/score neutral `I` on itself, since syntax alone may
   be predictable.

A positive cosine counts 1, negative 0, and exact tie 0.5. Domain is the independent
unit. Bootstrap 2,000 times over domains on fixed held-out scores, and use 1,000
within-domain orientation permutations for the goal interaction. Report 1,000 random
Gaussian directions. For the no-action arm, comparing each forward state with itself
must give an exact-zero interaction and score 0.5. Layer 0 must likewise give 0.5 for
all paired contrasts at the same final token. Synthetic shared-signal/noise calibration
must distinguish 1 from approximately 0.5 before interpreting model vectors.

## Predictions and decision

The prior forward score should replicate at 0.792, within 0.05. The *primary* test is
goal action-interaction accuracy at least 0.70 in layers 10–18, at least 0.15 above
the random mean, permutation p ≤ 0.05, and domain-bootstrap lower endpoint above 0.5.
For **goal-specific** action interaction, its held-out score must also exceed the
goal-direction-on-neutral interaction score by at least 0.15, with a paired domain
bootstrap lower endpoint above 0. This neutral comparison is required even if the
primary score passes. If the reverse-as-event score stays near/below 0.5, and pre-action
binding is high, the first spike's final-token signal is better read as predicate/person
binding than as this handover's narrative role. A positive interaction would still be a
controlled composition effect, not a natural-story trope shape or a steering result.
