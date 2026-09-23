# Role swap: controlled long-context recognition (frozen before activation extraction)

## Why this follows the corpus spike

The first ProppLearner spike recognizes function signals across tales, but a 200-character context
retains most accuracy. This cycle asks a sharper, deliberately synthetic question: **can a shared
activation displacement track a change in a handover's story role when the final action and local
wording are identical?** It tests a necessary context-sensitive component, not a trope manifold.

## Frozen material and labels

`research/narrative/prompts/role_swap_v1.json` contains 12 domains, each with two actors, two
opposed prior goals, one neutral bridge, and one fixed final handover sentence. Each domain has two
orders of the role sentences and two assignments of actors to those roles: 48 passages, 24 matched
pairs. The label is `helps` when the recipient previously sought to protect the group, `harms`
when the recipient sought to endanger it. In each pair only the actor names swap between the two
role sentences. The final handover, the last 200 characters, character length, and unigram
multiset are identical. Both role-sentence orders appear for each label, so sentence order itself
cannot predict it. Hold out an entire domain, including its names and object, at scoring time.

The role cue ends more than 200 characters before the final readout. Assert the frozen invariants
above plus equal token count and equal final token ID/position within each matched pair. Refuse any
domain that fails. These are constructed miniatures, not natural stories or human annotations.

## Measurement

Use `Qwen/Qwen2.5-1.5B` revision `8faed761d45a263340a0528343f099c05c9a4323` with CUDA
float16. Extract all layers' hidden states at the final period token of
the unmodified handover sentence. One passage per forward, checkpoint one domain at a time. Record
model revision, device, dtype, tokenizer/library versions, grid hash, code version, and activation
digest in ignored local provenance. Layer 0 should give exactly zero paired displacement: the
readout token and its position are fixed. A failure there invalidates the run.

For every domain and role-sentence order, form `delta = state(helps) - state(harms)` and unit
normalize nonzero deltas. For each held-out domain, average and normalize the 22 deltas from the
other 11 domains. A held-out pair scores 1 if its delta has positive dot product with that training
direction, 0 if negative, and 0.5 on an exact tie. Report the complete layer curve. The primary
statistic is mean pair accuracy over the already fixed layers 10–18, with domains as the independent
unit. Also report the cosine margin and per-domain outcomes at fixed layer 14. This paired score
cancels the local handover text and tests whether a role-flip displacement aligns across domains.

## Controls and calibration

- **No earlier role cue:** score the identical last 200 characters in each pair. Its displacement
  must be exactly zero, giving 0.5 with the tie rule.
- **Static readout:** layer 0 of the full passage must have zero pair displacement, giving 0.5.
- **Random arm:** use 1,000 seeded Gaussian directions at each layer, scored on the same held-out
  pairs. Their mean should sit near 0.5; flag a departure beyond 0.05 before trusting treatment.
- **Label permutation:** flip the `helps`/`harms` orientation together for both orders in each
  domain, refit leave-domain-out directions, and score the permuted labels (1,000 seeded draws).
  This is the inferential null for the fixed mid-layer statistic.
- **Synthetic signal/noise test:** run the scorer on a known shared direction and on seeded
  independent noise before interpreting model vectors; expect near 1.0 and 0.5 respectively.

Pre-run prediction: the primary mid-layer score is at least 0.75, exceeds the random mean by at
least 0.15, and has permutation p <= 0.05. Bootstrap 2,000 times over the 12 domains; its 95%
interval must have lower endpoint above 0.5 for a positive screen. If it fails, the role-swap
direction is not established at this design's resolution. If it passes, the result says that this
model carries a reusable context-sensitive relation in these controlled miniatures; it does not
show a Hero's Journey shape, natural-story generalization, or causal steerability.
