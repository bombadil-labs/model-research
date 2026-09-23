# Fixed plans under changing circumstances: no registered cross-format pass

## Question and design

The [preregistered probe](goal_relative_prereg.md) asks whether a final-event
activation interaction follows which of two fixed worker plans serves a stable
story goal when a relevant circumstance changes. Twelve original stories each
crossed two circumstance worlds, two final recipients, two orders of the
worker-plan sentences, and two orders of the circumstance sentences: 192
passages. World 0 affirms the status under which worker A's plan serves the
goal; world 1 affirms the status under which B's plan serves it. The [reviewed
grid](../prompts/goal_relative_v1.json) states that orientation and its reason
for both plans in every story. The initial bell mislabel and uneven cue grammar
were corrected before extraction, as recorded in the preregistration amendment.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16.
All 192 text, tokenizer and context checks passed; passages were 143–165
tokens against a 131,072-token configured context. Extraction was one passage
per forward, checkpointed by story. The [committed summary](../results/goal_relative_summary.json)
contains the grid/code/activation digests, device and library versions, all
layer curves and all controls. Per-domain arrays and token indices remain in
ignored `cache/goal_relative`. A score-only run reproduced the report exactly.

The scorer forms the unit interaction
`(world0,R0 − world1,R0) − (world0,R1 − world1,R1)` at the identical final
period token. It fits a mean direction on eleven stories and scores the held-out
story. Format indices are 0 = A-plan first, affirmation first; 1 = A-plan first,
negation first; 2 = B-plan first, affirmation first; 3 = B-plan first, negation
first. The primary statistic averages 0→3, 1→2, 2→1 and 3→0 over fixed layers
10–18, changing both sentence orders on every transfer.

## Registered result

| Train format → test format | 0 | 1 | 2 | 3 |
| --- | ---: | ---: | ---: | ---: |
| **0** | 0.361 | 0.407 | 0.630 | **0.630** |
| **1** | 0.352 | 0.380 | **0.583** | 0.593 |
| **2** | 0.630 | **0.565** | 0.472 | 0.481 |
| **3** | **0.620** | 0.583 | 0.537 | 0.352 |

Bold cells are the registered double-order transfers. Their mean is **0.600**
(95% domain-bootstrap interval **0.519–0.681**). All four transfers and both
action-polarity halves exceed 0.5, but the primary misses the registered 0.70
threshold and its required 0.15 margin over random directions (actual margin
0.100). The 1,000-draw permutation upper-tail p is **0.104**, above the 0.05
gate. Thus the registered positive prediction **fails**. The permutation mean
is 0.495 and 95th percentile 0.620; random-direction mean is 0.500, with a
95% draw span of 0.447–0.551. The allow-A and block-A halves score 0.625 and
0.574. Those halves are also the favorable- and unfavorable-status halves by
construction, so they are one split, not independent confirmations.

Within-format transfer averages **0.391**, fact-order-only transfer **0.609**,
and circumstance-cue-order-only transfer **0.444**. The matrix has no simple
``same format works, changed format fails'' pattern. Its full layer curves are
in the summary; no layer was chosen from the observed curve.

| Registered control | Score |
| --- | ---: |
| Layer 0 on every source-target arm | 0.500, exact ties |
| Pre-handover and no-world arms | 0.500 each, exact ties |
| Final-200-character trigrams; full-passage word bag | 0.500 each |
| Recipient-plan-fact bag; circumstance-cue bag | 0.500 each |
| Synthetic shared signal / noise scorer | 1.000 / 0.463 |

The activation interaction is nonzero, but this test does not establish a
shared format-tolerant direction for useful-plan role across held-out stories.
The near-chance exact and lexical controls show that the measured interaction
uses earlier context and is not explained by these bags. They cannot exclude
a richer symbolic strategy: identifying the affirmed status and matching it to
the fixed plans solves the grid. Float16 cancellation and this small model
also limit what a failed direction test says about other representations.

## Post-result geometry diagnostic

After seeing the failed direction test, I asked whether the *relative cosine
distances among stories* might be more stable across formats than a single
direction. This is exploratory and is not part of the registered decision. In
fixed layers 10–18, the four double-order comparisons of the interaction's
12-by-12 domain similarity matrices average Pearson **0.275** over their 66
off-diagonal entries. Jointly permuting domain identities in the target
formats gives a 1,000-draw mean near zero and upper-tail p **0.001**.

That correspondence is not specific to the goal-relative interaction. The
same analysis gives **0.859** for the world main effect and **0.310** for the
recipient main effect. General story identity and surface content can preserve
a domain similarity pattern across tellings. The [diagnostic artifact](../results/goal_relative_rdm_exploratory.json)
records its code and source-activation digests. This pattern motivates a
fresh, controlled geometry test; it does not rescue the failed registered
readout or establish a narrative shape.

## Next discriminator

The [open goal-relative claim](../claims.yaml) asks about a *fixed fact under
different goals*. This probe changed the circumstance while holding the goal
fixed, so it does not close that claim. A subsequent grid should switch the
story goal while holding the plan facts, status cue and final event fixed, and
should include both sentence orders. It should also measure repeatability or
precision of the four-term interaction before reading a weak null as absence
of structure.
