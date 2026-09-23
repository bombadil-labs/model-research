# A route-trained answer-slot direction causally biases name preference

The [frozen patch test](answer_slot_patch_prereg.md) asked whether the
block-24 direction that transferred from two-hop route stories to unrelated
property questions could *change* a later two-name answer. It added the
route-trained first-mentioned-person direction at every real token position
on 64 fixed property prompts, then compared the same addition at the final
block. The target prompts and their unpatched activations were known before
patching, so this is a conditional intervention on known prompts, not a new
representation replication.

Model: NDIF's pinned `google/gemma-2-9b-it`, local tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF exposes no weight
revision hash. The [committed report](../results/answer_slot_patch_v1_summary.json)
records the 64 prompt effects, candidate score changes, domain and factor
halves, exact nulls, bootstrap intervals, controls, fingerprints and
instrument gates. The ignored local cache retains all 896 individual score
jobs.

## Registered decision

The signed effect is half the difference between the `+20u` and `−20u`
first-mentioned-name margins. The primary is the block-24 effect minus the
same direction's final-block effect, averaged equally over eight domains.
The final-block arm measures the direct residual carry into final norm and
the output head, with no intervening transformer blocks. This subtraction
is a comparison of two full-magnitude interventions; because final norm and
later computation are nonlinear, it is not an exact additive circuit split.

| Arm | Mean signed margin effect (nats) | Positive domains | Positive prompts | Exact domain-sign p | Domain-bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: | ---: |
| Block 24 minus direct carry, **primary** | **+1.126** | **8/8** | **60/64** | **1/256** | **+0.985 to +1.282** |
| Block 24 total | +1.130 | 8/8 | 56/64 | 1/256 | +0.988 to +1.292 |
| Final block direct carry | +0.0038 | 6/8 | 33/64 | 25/256 | −0.0012 to +0.0082 |

The two norm-matched random directions have net means **−0.058** and
**+0.093** nat; the preregistered bar was twice the larger absolute mean
(+0.186). The primary exceeds it, and all ten registered gate components
pass: effect ≥+0.10 nat, exact p≤.05, bootstrap lower >0, ≥6/8 positive
domains, ≥48/64 positive prompts, the random-direction comparison, and
the four instrument gates. The p-value is at the 1/256 floor of this
eight-domain one-sided exact test, with no non-identity tie at the observed
value.

The second random direction is positive in **8/8 domains**, so its own
domain-sign test also reaches p=1/256. The sign test establishes a
consistent first-mention bias; it does not by itself distinguish `u` from
a random direction at this dose. The direction-specific evidence is the
**about 12-fold effect magnitude** over the larger of only two Gaussian
controls. Those controls do not calibrate the full space of plausible
in-distribution directions.

The +20u arm changes the first-mentioned candidate's log probability by
an average **+0.152** nat and the alternative's by **−1.026**; the −20u
arm changes them by −0.140 and +0.941. Thus most of the relative-margin
movement comes from lowering the alternative under +u, not only from
raising the first name. These are log probabilities, not isolated raw
logits. The `+u` patch changes four of 64 top-name choices toward the
first-mentioned person and changes none away. Two of those flips correct
the answer and two make it wrong; accuracy stays **62/64** from the
unpatched baseline. The baseline count is recoverable from the earlier
[committed property-replication margins](../results/choice_slot_replication_v1_summary.json)
at early telling and world 0: 32/32 plan-A-correct and 30/32
plan-B-correct cells. The present report's `first_mention_choices` records
the two corrected and two broken flips, yielding the same patched count.
The direction is an answer-selection bias, not an accuracy-improving
story edit.

## Measurement and scope

The source vector has norm 20, about 0.69 times the median natural
**goal-flip projection gap** on the same unpatched block-24 direction, and
about 6% of the target residual norm. All 64 prompts had one-token name
candidates, one BOS and zero padding in a fixed two-row batch. The
preflight found residual reach on **both candidate rows for all 12
nonzero patch/layer combinations**; the final-block arithmetic error was
zero. No-patch versus zero-vector and old versus new no-patch candidate
scores both differ by **0** at maximum. The core moved-candidates check
remained armed. It flagged 25/768 nonzero jobs (3.26%); each flagged row
passed the frozen deterministic two-rerun policy, and the rate stayed
below the 5% instrument ceiling. Neither block-24 `u` arm was flagged.

The result establishes a causal, domain-consistent **generic choice-slot
bias** from a distributed block-24 addition. The intervention touches
every real prompt position, including the attention sink and name tokens;
it does not locate which token carries the effect. Two Gaussian controls
are weak calibration of the space of possible in-distribution directions.
The tested target world was fixed, and the model was already correct on
most prompts, so the choice-flip count is small despite the log-probability
effect. This result neither edits a narrative role nor shows that the
route interaction itself is causally sufficient. The next frozen test
patches **one story-stage period token** with a counterfactual-world state
and compares a last-noun-only substitution before drawing a story-binding
conclusion.
