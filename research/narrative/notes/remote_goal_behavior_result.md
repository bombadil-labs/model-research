# Gemma responds to the circumstance, but misses the choice gate

The [frozen remote check](remote_goal_behavior_prereg.md) asked whether
`google/gemma-2-9b-it` chooses the worker whose unchanged plan serves a goal
after the story's circumstance changes. This is a behavioral capacity check on
constructed stories, not an activation geometry result. It used one fixed chat
question and scored the two possible names by teacher-forced log-probability.
The [summary](../results/remote_goal_behavior_summary.json) contains every
calibration margin, the registered story metrics, model and library provenance,
grid and code digests, and the digest of all 208 saved score rows. NDIF reported
the deployment as `HOT` and `pinned`, but did not expose a revision hash. The
raw rows remain in ignored `cache/goal_relative/remote_behavior/cells.jsonl`.

The model passed all sixteen easy controls crossing name assignment and plan
sentence order. The smallest helpful-minus-harmful margin was +7.37 nats,
above the registered +0.1 gate. Helpful-first margins averaged 2.15 nats
higher than helpful-second margins, so sentence position still affects the
score, but it did not reverse any control choice. These controls were used to
develop the earlier local clozes and are not independent generalization data.

| Registered story check | Result | Gate |
| --- | ---: | --- |
| Correct named worker, across 96 cells | 66/96 = 0.688 | **Fail**; required ≥0.70, or 68/96 |
| Correct-direction paired margin shift | 40/48 = 0.833 | Pass; required ≥0.75 |
| Joint domain-orientation permutation | p = 0.006 | Pass; required ≤0.05 |
| Fact-order halves | 0.708 / 0.667 | Both pass; required >0.5 |
| Cue-order halves | 0.667 / 0.708 | Both pass; required >0.5 |
| Identical no-circumstance world twins | Maximum margin difference 0 | Pass; required ≤0.25 nat |

The paired margin shift means `logp(A) − logp(B)` was greater when A's plan
served the goal than when B's did. It is **not** a count of flipped choices:
the model actually chose the correct worker in both worlds for 20 of 48 pairs,
chose the wrong worker in both worlds for 2, and kept one name across worlds
for 26. The no-circumstance twins scored identically, so repeated scoring noise
does not explain the paired effect at this resolution. The permutation
compared the 0.833 shift fraction with joint domain-orientation flips over
1,000 draws (null mean 0.506, 95th percentile 0.708).

| Domain | Correct cells / 8 | Correct-direction shifts / 4 |
| --- | ---: | ---: |
| Harbor | 5 | 4 |
| Bridge | 8 | 4 |
| Radio | 4 | 1 |
| Gate | 8 | 4 |
| Water | 4 | 4 |
| Map | 4 | 2 |
| Vial | 6 | 2 |
| Boat | 6 | 4 |
| Bell | 7 | 4 |
| Archive | 6 | 4 |
| Lantern | 4 | 3 |
| Seeds | 4 | 4 |

Several domains move the name margin in the expected direction without
crossing the decision boundary: water and seeds each show four positive
paired shifts but only four correct choices. This is consistent with a strong
baseline preference for one name or plan in those domains. Radio and map also
have weak or negative mean shifts, so the failure is not solely a threshold
effect from name preference.

**The registered behavioral-capacity gate does not pass.** Accuracy misses its
threshold by two cells, even though calibration, paired shift, permutation,
order halves, and repeat noise pass. The defensible finding is that this chat
readout detects a reproducible circumstance-dependent preference in these
stories, without establishing reliable correct choice under the frozen gate.
The local Qwen cloze and this Gemma chat question differ in model, prompt and
readout; their scores are not a controlled model-size comparison. A further
activation probe would need its own preregistration and controls, and should
preserve the distinction between a shifted margin and an actual choice flip.
