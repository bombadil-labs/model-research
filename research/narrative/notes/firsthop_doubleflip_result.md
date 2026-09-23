# First-hop double-flip result: the listed-plan slot cancels

**Registered result: slot-cancellation screen passed.** This is a conditional follow-up to the [first-hop patch result](firsthop_swap_patch_result.md), with the double-flip prediction and thresholds frozen in [the preregistration](firsthop_doubleflip_prereg.md) before any double score. The model was NDIF's pinned `google/gemma-2-9b-it`, with local tokenizer revision `11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF does not expose a weight revision hash. The complete [summary](../results/firsthop_doubleflip_v1_summary.json) contains all 128 cell effects and candidate scores.

The world swap changes the winning person and the winning listed-plan slot. Reversing plan order changes the slot but leaves the winner's person fixed. Flipping both changes the person while preserving the slot. If the period state carries the slot, the two changes should cancel in the later name margin. All 1,024 registered score jobs completed. The 256 copied states passed recipe and content-hash checks against the prior report.

| Arm or paired contrast | Mean signed margin shift (nats) | Domain-bootstrap 95% CI | Exact domain-sign p |
| --- | ---: | ---: | ---: |
| World swap | +0.600 | +0.372 to +0.855 | 1/256 |
| Plan-order swap, matched norm | +0.866 | +0.593 to +1.150 | 1/256 |
| Double flip, natural norm | +0.069 | −0.070 to +0.259 | 67/256 |
| Double flip, matched norm | +0.085 | −0.066 to +0.289 | 66/256 |
| World minus matched double | +0.515 | +0.346 to +0.697 | 1/256 |
| Plan minus matched double | +0.782 | +0.525 to +1.066 | 1/256 |
| Norm-matched random | +0.053 | +0.022 to +0.083 | 4/256 |

Both double means lie within ±0.15 and their CIs wholly within the preregistered ±0.40 equivalence band. Both paired contrasts exceed +0.25, have positive CI lower bounds, and are positive in all eight domains. Every instrument gate passed: core-score agreement, row-0-only refusal, two-row patch reach, zero identity, final-block pass-through, repeat drift, source-state match, bf16 patch arithmetic, and the 16/640 (2.5%) moved-candidate flag ceiling. The 128 new no-patch scores and both rescored single-flip effects reproduce the prior run bit-exactly. Independent recomputation from the committed candidate scores reproduced the four arm means and both paired contrasts exactly.

The average hides domain variation. The matched double effect is within ±0.08 nat in six domains, −0.24 in orchard, and +0.72 in ship; without ship, the mean is −0.007. In ship, the double retains much of the world (+1.24) and plan (+1.31) effects. The earlier slot-preserving first-hop clause-order arm also moved ship (+0.85) and orchard (−0.41) more than the other domains. This pattern suggests that the period state in those two domains is sensitive to in-distribution perturbations even when the winning slot is preserved. The registered aggregate screen passes, but cancellation is not uniform across domains.

The double flip left source-winner top-name choice at 19/128 before and after, with one flip each way. Its small positive mean resembles the random arm's positive mean, which also has a low sign-flip p. Thus a sign-consistent nonzero effect alone is not specific; the registered evidence for slot cancellation is the **equivalence plus the larger within-run single-minus-double contrasts**. The old first-hop-clause-order arm (+0.079) was used to calibrate the equivalence interval before the double scores were read.

This supports a winning **listed-plan-slot component** in the preselected block-24 story-period state on these constructed two-hop prompts. It does not identify a unique vector, prove that the model uses this code to compute the route, or show that patching can edit a coherent story. The state transplant also leaves the earlier visible text unchanged. The grid and site were chosen after earlier positive measurements, so a new domain and model are needed before generalizing this component.
