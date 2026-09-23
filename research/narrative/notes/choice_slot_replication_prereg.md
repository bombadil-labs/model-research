# Independent target-label test of the shared answer-slot direction

**Frozen before scoring or extracting any prompt in this grid.** The first
[cross-task control](choice_slot_control_result.md) found route-trained
block-24 cosine +0.543 on unrelated property choices, close to their
within-task +0.566. Its registered source-domain sign null missed p≤.05,
but that null is weak for a fixed target: flipping a minority of nearly
aligned source domains leaves the normalized source direction unchanged.
This replication uses eight **new** property domains and flips the **target**
world labels by domain, which directly tests whether the target interaction
has consistent orientation against the frozen route direction.

## Fixed material and behavior gate

Source: the same 256 cached route-story vectors and corrected pilot summary,
with all original prompt fingerprints checked. The route direction is fit
once on all eight source domains, both tellings, names and plan orders, with
the same unit `I_first` definition and no target data. Primary block 24 was
chosen by the prior pilot, not by this grid. Model: NDIF's pinned
`google/gemma-2-9b-it`; local tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF exposes no weight
revision hash.

Target: the eight rows in
[choice_slot_replication_v1.json](../prompts/choice_slot_replication_v1.json):
ribbon color, key material, parcel weight, tile pattern, lantern brightness,
bottle material, stamp condition and scarf material. None of the eight name
pairs or property labels was used in the first property battery. Each row
crosses two tellings (goal before/after facts), two name assignments, two
fact orders, two world bindings and two requested properties: 32 prompts
per domain, 256 total. The two-world truth table is the same as the source:
role A is correct when `world == goal`. The frozen neutral bridge and
property answer question are exactly those used by the first battery.

Before remote scoring, assert the row count and all 256 factorial IDs,
unique equal-length names within a row, one mention per name, identical
last-200-character suffix within each four-cell set, equal full-text word
bags and character lengths across world twins, a changed goal sentence
across goal twins, one BOS, equal candidate token counts and unchanged
prompt-token prefix on candidate append. Report goal token length differences
without selecting matched subsets. Measure the factorial full-text and
last-200-character word-bag interactions; both are expected zero.

Score every target prompt through the verified two-candidate remote
log-probability core, one two-candidate job per prompt, checkpointed with
exact prompt, grid and code digests. Let `m=logp(A-owner)−logp(B-owner)`.
Per telling × name × fact-order quartet, `D0=m00−m10` and
`D1=m11−m01` must each exceed +0.25 for joint success. Eligibility requires
at least 48/64 jointly successful quartets, both telling halves ≥0.60,
and each name and fact-order half >0.50. Report strict four-cell choice
accuracy and every domain separately. If behavior fails, still extract
and report the activations, but do not use their null to claim a generic
choice code.

## Activation instrument and fixed analysis

Read the final real prompt token after blocks `[0,8,16,24,32,40]`, one
prompt per NDIF job, using the already verified pilot extractor. On the
first target prompt, compare the extracted vector to core
`remote_residuals` at blocks 16/24 before bulk extraction (cosine ≥.999,
relative L2 error ≤.01). Repeat the first world-0/goal-0 prompt of each
domain in a separate identical job. Max repeat L2 per block must be ≤1%
of median nonzero interaction norm, and every block-24 interaction must
exceed ten times max repeat drift. Stale or duplicate fingerprints refuse.

Compute `I_A=h00−h01−h10+h11`; multiply by −1 when A's fact is second so
`I_first` points toward the first-listed person's role; unit-normalize
nonzero interactions. The route-trained direction at each block is the
unit mean of source `I_first`. Score each target `I_first` by cosine to
that direction. Average over both tellings, names and orders within each
domain, then equally over eight domains. **Block 24** is the sole primary
location. Report all six blocks, the source pilot's block-16/24 mean as
context, domain/telling/name/order halves and goal-length splits.

The primary exact null enumerates all `2^8` independent target-domain
world-label flips, including identity. Each flip negates all 16 target
interactions for one domain; the source direction stays fixed. The test
statistic is the same eight-domain mean cosine, with the same reduction
order for observed and every null assignment. Its minimum one-sided p is
1/256. Report null mean/q95 and upper-tail p, plus a 10,000-draw seeded
bootstrap 95% interval over the eight fixed target domain means. Also
report 1,000 seeded random unit directions per block, their target-mean
q95 and the observed percentile. These are unpatched readout arms.

Using the same saved states, fit an **internal property reference** for
each held-out target domain and telling on the other seven domains in the
opposite telling; score the held-out target interactions. Report its curve,
eight domain means, telling halves and bootstrap interval. Call the
internal reference resolved if its block-24 mean is ≥+0.05, its bootstrap
lower bound >0, and at least six of eight domains are positive. Report the
source-route-to-property cosine divided by the internal property value as
a descriptive ratio only.

## Decision and limits

Call the route direction **compatible with a substantial generic
two-person answer-slot component** if behavior and measurement gates pass,
the target-label exact p≤.05, the route-to-target domain-bootstrap lower
bound >0, at least six of eight target domains are positive, and the
route-to-target block-24 mean is at least half the resolved internal
property reference. If internal transfer is unresolved, the battery cannot
adjudicate shared versus task-dependent geometry even if its projected
mean is positive. Failure of a positive gate is not evidence that the
broad narrative geometry hypothesis is false. A pass shows a shared
direction on these constructed two-name choice prompts, not that this
component fully explains the route result or causes any answer. A later
causal test needs treatment, matched random, no-patch and pass-through arms
on held-out stories.
