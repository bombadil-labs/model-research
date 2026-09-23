# Same story, early or late reveal (frozen before activation extraction)

## Question

The preceding consequence probe gave a strong direction within one report order
that reversed when the clauses traded places. Can a final event's **relation to
earlier story facts** survive two changes to the telling: moving a reveal from
early to late, and reversing the reveal clauses? If it cannot, a high readout
from one telling is a poor candidate for a reusable narrative shape.

## Frozen stories and factorial grid

`reveal_invariance_v1.json` contains twelve original short stories: six in
which the reveal concerns allegiance and six in which it concerns competence.
Each has a group goal, two named possible recipients, a common sequence of
events, two role facts, a neutral bridge, and one final handover. The helpful
fact identifies the person who can advance the stated goal; the harmful fact
identifies the one who would frustrate it. In world 0 person A receives the
helpful fact and B the harmful fact; world 1 swaps those assignments. The final
handover can go to A or B. Thus the same final event sentence has a different
plot role between worlds, while a world has the same facts in every telling.

The two fact clauses appear either before the common events (chronological
reveal) or after them (late reveal). Independently, the helpful clause appears
first or second. The late telling withholds the assignment until after the
common events; it is a controlled late reveal, not a claim to reproduce a
literary plot twist. Format index is `[timing][clause order]`: 0 = early/helpful
first, 1 = early/harmful first, 2 = late/helpful first, 3 = late/harmful first.
Cross 2 worlds, 4 formats and 2 recipients: 16 passages per domain, 192 total.

Within a world, all four formats contain exactly the same words and facts; only
sentence order changes. Within a format and recipient, swapping worlds keeps
the word multiset and character length: the two equal-length names exchange
places in the same helpful and harmful clauses. For every matched cell the
final event sentence and preceding 200 characters are identical. The reveal
stands outside that local window. Before extraction, assert these text facts,
identical final readout token ID and position across all 16 cells of a domain,
one-token final readouts, and that each input fits the trained context. For the
late reveal, assert the tokenized prefix ending at the common events is
identical across worlds, clause orders and recipients.

Model: `Qwen/Qwen2.5-1.5B` revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16. Run one
passage per forward under the shared GPU lock, checkpoint by domain, and record
grid/code/model/device/dtype, library versions, readout positions and activation
digests in ignored local provenance. No external story text is in this grid.

## Measurement and controls

At the final period token, for each domain, format and layer, compute

`I = unit((world0,R0 − world1,R0) − (world0,R1 − world1,R1))`.

World 0 makes A the helpful recipient; world 1 makes B helpful. A relation
direction should therefore have a consistent sign across tellings even though
the helpful sentence moves. Leave out each whole domain in turn. Fit the mean
of the other eleven domains' unit interactions in one source format and score
the held-out domain in a target format by cosine sign (positive 1, negative 0,
exact zero 0.5). Report the complete layer curve for every source-target arm.
The fixed primary is the mean over layers 10–18 of four transfers that change
**both** timing and clause order: 0→3, 1→2, 2→1, 3→0. Report the four self-fit
arms, all timing-only and clause-only transfers, and the allegiance and
competence halves separately. No layer is selected from scoring data.

For uncertainty, resample the twelve domains 2,000 times on the fixed held-out
predictions. For 1,000 permutation draws, flip the world orientation jointly
across all four formats within each domain, refit and rescore the primary.
Report 1,000 random Gaussian directions, known-signal and noise scorer
calibration, and these null arms:

- **Layer 0:** the final token ID and position match across the 16 cells; the
  interaction must be bit-exact zero and score 0.5.
- **Before the handover:** recipient pairs have identical prefixes through the
  bridge period; their interaction must be bit-exact zero and score 0.5.
- **Before the late reveal:** world and recipient variants have the same
  prefix through the common events; the world difference must be bit-exact zero.
- **No-world:** replacing the alternative world with the same state must score
  0.5.
- **Local and bag:** construct character-trigram vectors from the actual final
  200 characters and full-passage word-count vectors from the actual texts.
  Their world-by-recipient interactions must score 0.5 under the same rule.

The pre-reveal null is deliberately **not** invariant between telling times:
the early telling has already stated the role facts at that story point, while
the late telling has not. Report the early-versus-late world-displacement norms
at the end of the common events descriptively, with no positive decision gate;
an early nonzero norm can be a lexical trace and does not prove role reasoning.

## Prediction and decision

The primary cross-format relation passes only if accuracy is at least 0.70,
exceeds random-direction mean by at least 0.15, has permutation p at most 0.05,
and has a domain-bootstrap 95% lower endpoint above 0.5. All four doubly
transformed transfers and both mechanism halves must individually exceed 0.5.
Passing would establish a format-tolerant context-by-recipient interaction in
these constructed stories. It would not establish a Hero's Journey manifold,
natural-story generalization, causal control or a decomposition operator.
Failure would show that this corpus and readout still depend on the telling
format at the registered resolution. Either outcome is compared against the
earlier order-reversal failure rather than silently pooling the two formats.
