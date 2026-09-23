# The route-trained final-token direction transfers to eight new property tasks

The [frozen replication](choice_slot_replication_prereg.md) tested whether the
final-token direction found on two-link route stories aligns with a new set
of simple two-person property choices. It fixed the route-trained direction
before any target score, used eight new domains and name pairs, and replaced
the first control's weak source-flip null with an exact **target-domain
world-label** null. This directly asks whether independently varied target
bindings share the source direction.

Model: NDIF's pinned `google/gemma-2-9b-it` deployment, local tokenizer
snapshot `11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF exposes no
weight revision hash. The [committed summary](../results/choice_slot_replication_v1_summary.json)
records the checkpoint, versions, grid and code hashes, all six blocks,
domain and factor splits, exact null, random directions, repeats and core
checks. The 256 target and eight repeat activation arrays are in ignored
`cache/choice_slot_replication/v1/states`.

## Registered result

The property behavior gate passed: **60/64** world × goal quartets shifted
correctly, and the same 60/64 made all four individual choices with the
registered margin. Seven domains passed 8/8; lantern brightness passed 4/8.
The early and late telling halves were 28/32 and 32/32. Name and fact-order
halves were each 30/32. All target goal pairs had identical token lengths;
the full-text and final-200-character factorial word-bag interactions were
measured as zero.

At the sole registered primary, block 24, the frozen route direction scored
**+0.583 mean cosine** on the new property interactions, with eight of eight
positive domain means and a domain-bootstrap 95% interval **+0.492 to
+0.653**. The exact target-label orientation null had mean zero, 95th
percentile +0.345 and **p = 1/256 = 0.0039**, its attainable floor at eight
domains. The opposite-telling, leave-one-property-domain-out reference was
**+0.579** (interval +0.521 to +0.627), so route-to-property alignment was
1.006 times the property task's own fitted transfer. This ratio is
descriptive, not a proof of identical computations. All seven registered
behavior, measurement and transfer gate components passed.

| Block | 0 | 8 | 16 | 24 | 32 | 40 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Route → new property | −0.003 | +0.007 | +0.023 | **+0.583** | +0.325 | +0.134 |
| Within new property | +0.067 | +0.011 | −0.010 | **+0.579** | +0.376 | +0.122 |

The block-24 route-to-property mean exceeded every one of 1,000 seeded
random directions; their 95th percentile was +0.022. The target telling
halves were +0.498 early and +0.668 late. All eight domain means were
positive, from +0.303 (lantern) to +0.709 (stamp). These splits are reported
without selecting a subset or moving the primary block.

The first target extraction matched the established remote residual core at
blocks 16 and 24 with relative L2 error zero. Separate-job repeat drift
was zero at every block. Every block-24 factorial interaction exceeded the
registered noise floor. The same model deployment and two-candidate
teacher-forced scoring path were used throughout.

## Interpretation

The registered claim **holds**: a route-trained, first-listed-person
direction appears in independent, behaviorally valid property choices
under a target-label test with an informative exact null. The earlier
four-domain control gave a similar descriptive result but its source-flip
null had little power; this replication resolves that specific statistical
weakness. The shared component is large relative to an internal property
reference and to random directions.

This narrows the meaning of the original route-story transfer. Its
block-24 final-token readout is substantially **task-general answer-slot
geometry** across these two-name questions. It does not show that the
property and route tasks use the same computation, that the generic
component is sufficient to explain every part of the route result, or that
an intervention on the direction would change the chosen name. The
[pre-question location test](prequestion_route_state_result.md) found no
transfer of this direction at two story-ending tokens. Together,
the results point to answer selection after the explicit question as the
next causal target; a later patching study needs no-patch, pass-through,
matched-random and signed-treatment arms on held-out prompts.
