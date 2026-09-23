# A two-link route fact changes plan choice across tellings

## Registered question and provenance

The [preregistered screen](fact_flip_twohop_prereg.md) held the goal, two
worker plans, names and word bag fixed while swapping which intermediate
link reached the target. It asked whether the model's preference for the
worker whose plan reaches the target would move with that fact in both an
early-fact telling and a late-reveal telling. Eight story domains crossed
fact-clause order, name assignment and plan-sentence order. Four independent
direct-route domains tested the readout. The exact grid was frozen before
scoring and reviewed before the NDIF run.

The model was NDIF's pinned `google/gemma-2-9b-it` deployment. NDIF reports
the checkpoint and that it is pinned, but does not expose its weight revision
hash. The local tokenizer snapshot was
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. The
[committed summary](../results/fact_flip_twohop_summary.json) gives library
versions, grid and scorer digests, every forced-score margin and paired
shift, generation outputs, and every gate component. The candidate scores
and job log remain in ignored `cache/fact_flip_twohop/v1`. All 192 unique
score prompts passed the one-BOS, candidate-token-count, unchanged-prefix
and matched-world token-length checks before scoring.

## Controls and result

| Registered measurement | Observed | Gate |
| --- | ---: | --- |
| Direct-route correct paired shifts | 32/32; early 16/16, late 16/16 | Pass (≥24/32, both halves >0.5) |
| Identical separate-job repeats | Maximum absolute margin difference 0 across 8 prompts | Pass (≤0.25 nat) |
| Two-link correct paired shifts | **55/64** | Pass (≥48/64) |
| Domain-orientation null | Exact p = 1/256 = 0.0039 | Pass (≤0.05) |
| Domain-bootstrap 95% interval | 0.719–0.969 | Pass (lower >0.5) |
| Early / late fact telling | 29/32 / 26/32 | Pass (each ≥0.65) |
| Fact-order quadrants 00 / 01 / 10 / 11 | 0.625 / 1.000 / 1.000 / 0.8125 | Pass (each >0.5) |
| Strict forced-choice reversals | 49/64 | Secondary; no gate |
| Greedy generation, fixed subset | 32/32 parseable and forced-score agreement; 14/16 correct world-pair reversals | Interpretation gates pass |

The name-assignment halves were 27/32 and 28/32; the plan-order halves
were 29/32 and 26/32. Seven paired shifts pointed the wrong way and two
were within ±0.25 nat. The exact orientation null has mean 0.484 and 95th
percentile 0.723. All registered gate components pass. The primary claim
therefore **holds on this constructed grid**: the model's plan preference
responds to the swapped two-link route fact in both tellings, beyond the
frozen bag and clause-order rules.

The frozen shortcut ceilings are zero paired shifts for the full-text word
bag, each worker's plan words, and direct route–target co-occurrence. An
ordinal clause-matching rule and a target-first rule each solve only half
the domains; the per-quadrant gate is what rejects ordinal matching. A
symbolic two-link solver solves all cells. The result is consistent with
using the two route relations, although it does not identify the model's
internal algorithm.

## Misses and limits

The frozen semantic-prior audit labelled four domains where a route or
intermediate-link name suggested a destination. Correct paired shifts were
25/32 in those domains and 30/32 in the four neutral-labelled domains.
Within the labelled domains, strict cell choice was correct in 30/32
prior-congruent worlds and 23/32 prior-incongruent worlds across the eight
name/order/telling variants. The labels were subjective and this is a
descriptive split, but the gap is consistent with semantic route priors
competing with the stated facts. Library had 4/8 correct shifts and ship
5/8; clinic, which had no frozen prior label, had 6/8. The weakest
fact-order quadrant was 00 at 10/16, so the effect is not uniform even though
that gate passed.

The paired-score result and the generated-choice result answer different
questions. The score moved correctly in 55/64 pairs, while the model chose
the correct worker in both worlds in 49/64 pairs under the stricter forced
choice margin. On the fixed generation subset it did so in 14/16 pairs.
Generation covered only one name assignment and plan order, so it does not
establish the full-grid generated-choice rate.

These are short, explicit, constructed route stories. The result supports a
behavioral prerequisite for narrative relation geometry: facts can change
the model's preference while surface words and goal wording stay fixed,
including when the facts are disclosed late. It does not yet show a
continuous activation shape, a manipulable narrative component, or
recognition of a trope across unrelated full stories. NDIF's missing weight
revision also limits exact replay if its pinned deployment changes.
