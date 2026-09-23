# Moving a reveal survives; reversing its clauses flips the readout

## Design and provenance

The [preregistered probe](reveal_invariance_prereg.md) asked whether the
activation interaction for an identical final handover survives retelling the
same facts. Twelve original short stories crossed two worlds (which of two
named people could help the story's stated goal), two final recipients, two
reveal times (before or after the common events), and two orders of the helpful
and harmful fact clauses. Six stories concern allegiance and six competence.
There were 192 passages. Moving the reveal changes sentence order only; within
a world and recipient the four tellings have exactly the same words. Swapping
worlds exchanges equal-length names in the two fact clauses. Each matched
variant has the same final 200 characters, word bag, character length, final
token ID and token position. The reveal is outside that local window.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16. All
tokenizer and context checks passed. Per-domain checkpoints and token indices
remain in ignored `cache/reveal_invariance`; the committed
[summary](../results/reveal_invariance_summary.json) records the grid, code and
activation digests, model and library versions, every layer curve and all
registered controls. A score-only rerun reproduced the report exactly.

At the final period, each domain and telling supplied the unit interaction
`(world0,R0 − world1,R0) − (world0,R1 − world1,R1)`. Each direction was fit on
eleven domains in one telling and tested on the held-out domain in another.
The fixed primary band was layers 10–18. The primary transfers changed both
reveal timing and clause order. The domain was the bootstrap and permutation
unit. Telling indices: 0 = early/helpful first, 1 = early/harmful first,
2 = late/helpful first, 3 = late/harmful first.

## Registered result

| Train telling → test telling, fixed layers 10–18 | 0 | 1 | 2 | 3 |
| --- | ---: | ---: | ---: | ---: |
| **0** early, helpful first | 1.000 | 0.000 | 1.000 | **0.000** |
| **1** early, harmful first | 0.000 | 1.000 | **0.000** | 1.000 |
| **2** late, helpful first | 1.000 | **0.000** | 1.000 | 0.000 |
| **3** late, harmful first | **0.019** | 1.000 | 0.000 | 1.000 |

Bold off-diagonal cells are the four preregistered transfers that change both
timing and clause order. Their mean is **0.0046**, with a 95% domain-bootstrap
interval of **[0.000, 0.014]**. The registered positive gate fails. The
permutation mean was 0.490 over 1,000 draws (registered upper-tail p = 1.000);
random directions averaged 0.501 (95% span 0.437–0.567). The two mechanism
halves scored 0.009 (allegiance) and 0.000 (competence). The complete layer
curves are in the summary; no layer was selected from these results.

The matrix isolates the change that matters. Holding clause order fixed while
moving the fact reveal from early to late gives **1.000** in both directions for
both clause orders. Reversing clause order gives almost entirely opposite
predictions, whether reveal timing changes or stays fixed. Thus this readout
is invariant to **when** the role facts appear in these stories, but not to
their sentence order. The observed sign reversal matches the earlier
[consequence-order result](consequence_order_result.md), now in longer,
story-specific passages with an early/late reveal manipulation.

| Registered control | Score |
| --- | ---: |
| Layer 0, pre-handover, no-world | 0.500 each, exact ties |
| Final 200-character trigrams; full-passage word bag | 0.500 each |
| Recipient-clause word bag, measured before extraction | **0.875** |
| Synthetic scorer: shared signal / noise | 1.000 / 0.491 |

Before the late reveal, all world and recipient variants have the same
tokenized prefix and bit-exact activation state. At the end of the common
events, mean mid-layer world-displacement norm is 0.000 in the late telling and
1.545 in the early telling, which has already supplied the role facts. This is
an information-availability sanity check; the early displacement may be a
lexical trace.

## Interpretation and next discriminator

The identical local suffix and exact controls show that the final-event
interaction depends on earlier text. They do **not** establish a stable plot
role. The model's primary cross-format score, 0.0046, is far below the 0.875
recipient-clause bag baseline. Even the perfect timing-only transfer is
consistent with reading which named recipient was described by positive or
negative words. This grid cannot separate that entity-to-attribute binding
from understanding whether the handover advances the story's goal. The
near-perfect clause-order sign flip is evidence that this particular activation
direction is dominated by how those facts are presented.

A next grid should make the same fact favorable under one goal and unfavorable
under another, while holding its words, the final event and the reveal order
fixed. That would test goal-relative narrative role against the measured
entity-valence ceiling. Natural Propp tales still require a separate test of
whether earlier context changes a function label when the local event wording
is held fixed; these original stories are controlled demonstrations, not a
cross-genre corpus.
