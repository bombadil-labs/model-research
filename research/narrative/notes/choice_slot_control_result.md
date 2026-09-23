# The route readout also aligns with unrelated property choices

The [frozen cross-task test](choice_slot_control_prereg.md) asked whether the
final-token direction learned from eight two-link route-story domains is
specific to that task or also appears in simpler two-person choices. Its
targets were four direct-route domains and four unrelated property domains
(badge color, cup temperature, card shape and folder state), each crossed
over telling, name, fact order, world and goal. The source direction used
all eight original route domains and no target states.

Model: NDIF's pinned `google/gemma-2-9b-it` deployment, local tokenizer
snapshot `11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF exposes no
weight revision hash. The [committed summary](../results/choice_slot_control_v1_summary.json)
records the model, versions, code and grid digests, all six blocks, domain and
factor splits, exact nulls, random-direction arms, repeats and core checks.
The 264 target and repeat activation arrays remain in ignored
`cache/choice_slot_control/v1/states`.

## Result at the registered block 24

The property task passed the behavioral eligibility gate: all 32 four-cell
sets shifted correctly under both goal contrasts, across both tellings, names
and fact orders. Twenty-six of 32 also made all four individual choices
correctly. The direct-route battery had already passed 32/32 in the frozen
behavioral screen. Each battery's first extraction matched the established
core at blocks 16 and 24; separate-job repeat drift was exactly zero, and
all target interactions were resolved.

| Target battery | Route-trained mean cosine | Within-target held-out cosine | Route-trained four-domain 95% bootstrap interval | Source-orientation null |
| --- | ---: | ---: | ---: | ---: |
| Direct route | **+0.513** | +0.440 | +0.481 to +0.544 | p = 6/256 = 0.023 |
| Unrelated property | **+0.543** | +0.566 | +0.409 to +0.628 | p = 25/256 = 0.098 |

The direct-route transfer passes its measured readout gates. The property
transfer is nearly as large as the property battery's own opposite-telling,
leave-domain-out reference, and its four domains are all positive. The
registered **source-orientation** test does not reach p≤0.05 on property,
so the frozen reading remains **mixed or partial**. Its failure is a poor
reason to discount the property alignment, because this particular null has
little power for fixed-target cross-task transfer:

If all eight source domains share a direction `u`, flipping any zero to
three source domains leaves the unit-normalized fitted mean pointing along
`u`. That is `1 + 8 + 28 + 56 = 93` of the 256 assignments with essentially
the observed target score, giving a null-tail floor near **93/256** in the
homogeneous limit. The smaller observed tails (25/256 for property, 6/256
for direct route) reflect heterogeneity among source domains as well as
alignment. The source-flip p value does not cleanly test whether target
alignment beats chance. This weakness was identified after scoring; the
registered gate and reading are retained unchanged.

The informative comparisons are the seeded random-direction arm and the
within-property reference. Against a random-direction 95th percentile of
+0.020, the route-trained property alignment is +0.543, close to the
property-internal +0.566. This is strong descriptive evidence for a
**substantial task-general answer-slot component** at the final prompt
token. The run does not show that this component is sufficient to explain
all of the original route transfer, nor does it establish a route-specific
operator. The reverse property-trained direction projected onto the eight
source route domains at +0.235, another descriptive sign of overlap with
an asymmetric fitted direction.

| Block | 0 | 8 | 16 | 24 | 32 | 40 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Route → direct | −0.039 | +0.015 | −0.012 | **+0.513** | +0.308 | +0.127 |
| Route → property | +0.082 | −0.028 | −0.002 | **+0.543** | +0.278 | +0.096 |
| Within direct | +0.027 | +0.063 | +0.020 | +0.440 | +0.285 | +0.102 |
| Within property | +0.089 | +0.015 | +0.048 | +0.566 | +0.330 | +0.082 |

The direct-route block-24 value exceeds its seeded random-direction 95th
percentile (+0.018). Both batteries had equal goal
token lengths in all 32 quartets, so the length split has no changed-length
subset. The property cross-task value was lower in the early target telling
(+0.453) than the late telling (+0.634); the frozen analysis reports that
split without selecting one. The direct telling values were +0.460/+0.566.

## Interpretation and next test

This is a readout comparison, with no activation patching. The final-token
interaction looks much less route-specific than the earlier pilot alone
suggested: an unrelated, behaviorally validated property task carries a
closely aligned direction at the same block. The preregistered source-flip
null is structurally weak for this question, while a four-domain interval
describes only these constructed controls. A future cross-task replication
should freeze more independent target domains and flip their world labels
by domain in its null; with four target domains, an exact `2^4` test has a
one-sided floor of 1/16, above 0.05.

The next frozen test moves the readout to two locations **before the answer
question**: just after the informative facts and after the long neutral
bridge. This checks whether a shared goal × route signal is already present
in the story state or emerges only when the model reads the answer question.
