# Cross-task control for the route choice-slot readout

**Frozen before extracting or scoring any control prompt.** This follows
the [goal × route activation pilot](goal_route_activation_pilot_result.md),
which found block-24 transfer of +0.171 across held-out route domains. The
question here is whether that direction transfers to simpler and unrelated
two-person choices. A positive unrelated transfer would explain the pilot
without a route-specific representation.

## Fixed material

Source is the 256 cached route-story vectors from the pilot: eight domains ×
two tellings × two name assignments × two plan orders × two route worlds ×
two destination goals. Every source row must pass its original fingerprint,
using the original extraction digest recorded in the corrected pilot report.
The source model is NDIF's pinned `google/gemma-2-9b-it`; tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF does not expose a
weight revision hash. If the deployment or tokenizer metadata changes, stop.

Two target batteries are fixed before this run:

1. The four **direct-route** controls already frozen in
   `goal_route_cross_v1.json`. They have the exact route question, bridge,
   name crossing and two-by-two world × goal truth table of the source, but
   only one route link. All 128 cells are measured.
2. Four **unrelated property choices** in
   [choice_slot_controls_v1.json](../prompts/choice_slot_controls_v1.json):
   badge color, cup temperature, card shape and folder state. Each uses a
   fixed pair of names, two labels and explicit one-person facts. World 0
   binds property 0 to role A; world 1 swaps properties. Goal 0 requests
   property 0; goal 1 requests property 1. Thus the correct role is A in
   `(world,goal)=(0,0),(1,1)` and B in `(0,1),(1,0)`. Cross goal-before-facts
   versus goal-after-facts telling, name assignment and fact-sentence order:
   four domains × 2⁵ = 128 cells. The bridge is exactly the frozen route
   bridge, so the final 200 text characters match in every factorial set.

The target property question is fixed in its grid. Its different wording
means a low cross-task value cannot prove route-specific geometry. The same
names and bridge as the direct-route controls reduce name and suffix drift.
Report prompt token lengths by world/goal and the proportion whose two goals
have the same token count. Do not select only length-matched items.

## Behavioral eligibility and extraction checks

The direct-route controls already scored 32/32 correctly oriented joint
world shifts in the behavioral screen. Reuse that report, with its digest
check. Score each property prompt through the verified remote logprob core,
one two-candidate job per prompt. For
`m=logp(A-owner)−logp(B-owner)`, require both `m00−m10>.25` and
`m11−m01>.25` in at least 24/32 four-cell sets, with each telling half above
0.5. Record strict four-cell choice correctness separately. If this
eligibility gate fails, still extract and report the activation controls,
but do not call a weak property transfer evidence for route specificity.

Preflight all 256 target prompts for one BOS, equal candidate token count,
an unchanged prompt prefix on candidate append, identical final token ID
within each four-cell set, world-pair token length within each goal, and
identical last 200 characters across each set. Read the final real token
after blocks `[0,8,16,24,32,40]`, using the pilot's one-prompt job shape.
Compare the first prompt of each battery with core `remote_residuals` at
blocks 16 and 24 (cosine ≥.999, relative L2 error ≤.01) **before** bulk
extraction. Checkpoint each prompt with an exact rendered-prompt fingerprint
bound to the model, target grid and extraction code. Repeat one frozen
`(telling=0,name=0,order=0,world=0,goal=0)` prompt per target domain in a
separate identical job. Maximum repeated-vector L2 drift at each block must
be ≤1% of the median nonzero factorial interaction norm, and each block-24
target interaction must exceed ten times that drift. If this fails, the
target readout is unresolved and no selectivity conclusion is drawn.

## Fixed direction and arms

Form `I_A=h00−h01−h10+h11` for every source and target quartet, then
multiply by +1 when role A's sentence is first and −1 when it is second.
Normalize each nonzero `I_first` to unit length. Source direction at each
block is the unit-normalized mean over the eight source domains, two
tellings, two names and two plan orders. It is fitted **without target
states or target labels**. Score each target unit interaction by cosine to
that frozen source direction. Average first within domain over telling,
name and order, then equally over four target domains. Block 24 is the
primary location, selected from the prior pilot; report the full six-block
curve and the original block-16/24 mean as a companion.

Three unpatched readout arms are reported on **both** target batteries:

- Source-trained direction (the measured transfer).
- 1,000 seeded random unit directions per block, with the target mean's
  95th percentile and the observed percentile against those directions.
- Exact `2^8` source-domain orientation null: jointly flip both tellings,
  names and orders of each source domain, refit, then score the unchanged
  targets. Report the upper-tail p, null mean and 95th percentile. This is
  the causal-label null for the fitted readout, not a random text baseline.

All activations are from **unpatched** forwards. A patching battery, if
subsequently run, will add treatment, matched random and no-patch arms,
plus a pass-through readout at or after its patch layer.

Bootstrap the four fixed target-domain means for 10,000 seeded draws and
report the 95% interval. Report the four individual domain values, both
telling means, both name and order halves, all six blocks, repeat noise,
goal-length split, and source-route reference +0.171 at block 24. No layer,
domain, name, telling or order is selected from these results.

## Reading rules

Call the route signal **compatible with a generic two-option answer slot**
if the unrelated property battery is behaviorally eligible and readable,
has block-24 mean ≥+0.0855 (half the previous route transfer), exact source
orientation p≤.05, bootstrap lower bound >0, and ≥3/4 target domains have
positive means. The direct-route battery must also be reported: positive
direct transfer with weak property transfer would show transfer within the
route family but would not prove a graph operator. If both controls are
weak, the pilot remains a candidate route-specific signal, limited by task
and question wording differences and four target domains. Any partial or
mixed pattern is reported without forcing one of these readings.

This screen does not patch activations or demonstrate causality. An
intervention is justified only after the target batteries and their
measurement gates are read. A successful patch would still require random,
no-patch and pass-through controls and a new held-out stimulus set.
