# Fixed plans, changing consequences (frozen before activation extraction)

## Question

The [early/late reveal probe](reveal_invariance_result.md) preserved a final
event readout across reveal timing but flipped its sign under fact-clause
reversal. Its recipient-clause word bag scored 0.875: assigning a positive or
negative attribute to a name could explain the timing result. Can a final
event's activation interaction instead track whether a **fixed plan helps a
fixed story goal when a relevant circumstance changes**, and still transfer
after two independent sentence-order reversals?

This is a controlled context-composition test. It holds each worker's plan,
name, event object, final handover and group goal constant. The circumstance
changes which of two opposed plans is useful. A pass would remain compatible
with relatively simple language understanding of the affirmative status clause
and the plan verbs; it would not identify a narrative manifold.

## Frozen stories and design

`goal_relative_v1.json` has twelve original short stories. In six, worker A's
plan allows a shipment, signal, visitor or route through and B's blocks it.
In six, A's plan blocks an item or action and B's allows it. Each story states
a stable group goal, the workers' two fixed plans, a circumstance about the
relevant item, a common sequence of events, a neutral bridge, and a final
handover to one worker. Each grid row records `a_useful_status` and
`b_useful_status`, with a sentence explaining why each plan serves the stated
goal under that status. The scorer asserts that these are the two distinct
statuses in the story, then derives world 0 from `a_useful_status` and world 1
from `b_useful_status`. A plan's mechanical allow/block label never sets the
world orientation. Six A-useful statuses have favorable valence and six have
unfavorable valence. The same worker plan changes from goal-serving to
goal-frustrating across worlds, while action polarity is balanced over domains.

The circumstance has two sentences: an affirmative statement that the item
*is* status X, and a negative statement that it is *not* status Y. Reversing
the world exchanges the good and bad status terms between those grammatical
roles. Reversing cue order puts the negative statement first; it does not
change which status is true. Independently reverse the order of the two
worker-plan facts. Cross fact order (2), cue order (2), world (2), and final
recipient (2): 16 passages per domain, 192 total. Within a fixed recipient,
all variants have the same words, character length and final 200 characters.
The world pair keeps the plan facts exactly unchanged; the two order factors
move sentences without changing their facts. The circumstance cue is outside
the final 200-character window.

Before extraction, assert all text invariants, equal final token ID and
position across all sixteen cells of each domain, an identical tokenized
prefix through the bridge period for recipient pairs, and that every passage
fits the model context. Model: `Qwen/Qwen2.5-1.5B` revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16.
One passage per forward under the shared local GPU lock; checkpoint by
domain. Record grid/code/model/device/dtype, library versions, token readout
positions and activation digests in ignored local provenance.

## Measurement and controls

At the identical final period token, form for each domain, fact order, cue
order and layer

`I = unit((world0,R0 − world1,R0) − (world0,R1 − world1,R1))`.

World 0 makes A's fixed plan useful; world 1 makes B's useful. Leave each
domain out in turn. Fit the mean unit interaction of the other eleven domains
from one format and score the held-out interaction in another by cosine sign.
Format index is `[fact order][cue order]`: 0 = facts A then B, affirmation
first; 1 = facts A then B, negation first; 2 = facts B then A, affirmation
first; 3 = facts B then A, negation first. The primary statistic is mean
held-out accuracy across four transfers that change **both** order factors,
0→3, 1→2, 2→1 and 3→0, averaged over fixed layers 10–18. Report all sixteen
source-target arms and complete layer curves, plus within-format,
fact-order-only, cue-order-only, allow-A and block-A results.

Bootstrap twelve domains 2,000 times on fixed held-out predictions. For 1,000
permutations, flip world orientation jointly across all four formats within
each domain, refit and rescore. Report 1,000 random Gaussian directions,
synthetic shared-signal and noise calibration, and the following nulls:

- Layer 0: identical final token ID and position; interaction bit-exact zero.
- Before handover: recipient pairs have identical prefixes through the bridge
  period; interaction bit-exact zero.
- No-world: compare a state to itself instead of the alternate world; 0.5.
- Actual final-200-character trigram counts and full-passage word counts:
  the world-by-recipient interaction must score 0.5.
- The clause containing the final recipient's fixed plan, selected from text
  by the recipient name, has the same words across worlds and must score 0.5.
  The two circumstance sentences as a whole also have the same word bag and
  yield a zero interaction.

These bags do not exhaust lexical shortcuts. A reader who identifies the
affirmed status and its goal relation to each fixed plan can solve the grid
without a reusable story-shape coordinate. Treat that symbolic rule as
a design ceiling of 1.0, not as measured model evidence.

## Pre-extraction amendment after adversarial review

The first grid commit (`38fa04d`) mislabeled bell: silencing a warning during
an actual attack frustrates the stated goal. Bell now pits a real warning
against a false alarm, so silencing serves the goal only for a false alarm.
Every domain now declares the useful status for **both** plans and gives a
reason tied to the story's goal. World orientation follows those declarations.
Cue verbs were also made grammatical for both statuses (for example,
"contained an antidote" and "did not contain a toxin"). These edits preceded
token preflight, activation extraction and scoring; all decision criteria
above are unchanged. The reason strings are human-auditable semantic
annotations, while code checks their completeness and opposing orientation.

## Prediction and decision

The double-order transfer is positive only if its fixed mid-layer accuracy is
at least 0.70, exceeds random-direction mean by at least 0.15, has permutation
p ≤ 0.05, and has a 95% domain-bootstrap lower endpoint above 0.5. All four
primary transfers and both action-polarity halves must exceed 0.5. A pass
would support a format-tolerant circumstance-by-recipient interaction for
fixed plans in these constructed stories. It would not establish natural-story
transfer, a Hero's Journey shape, causal steering or decomposition. A failure
under one order reversal would identify that telling choice as a confound for
this instrument, as in the previous two probes.
