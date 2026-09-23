# Goal reversal at fixed facts and plans: calibration result

The registered question was whether changing only a story's stated goal
reverses a model's choice between two unchanged worker plans. The story grid
contains twelve dilemmas, crossed over goal paraphrase, name assignment and
plan order. **No story choice was scored.** The forced-name readout failed its
control gate first, so this run cannot establish or reject story-level goal
sensitivity.

## Frozen ceiling and instrument

The story grid balances protective versus providing goals against both
physical plan meaning and act versus withhold status. This removed two simple
shortcuts. A stronger goal-category→plan-verb rule frozen before any score
still gets 21/24 of the grid's paired goal reversals without reading a setup.
Any later story result at or below that ceiling can be explained by this
coarse rule; it would not demonstrate integration of causal story facts.

The instrument scored two bare name continuations under one chat prompt with
`asserted_remote_patched_logprob`. Plan A's owner minus plan B's owner is the
margin, independent of the names' alphabetical order. A control passes only
if this margin exceeds +0.1 under goal 0 and is below −0.1 under goal 1,
for both name assignments and both plan orders. Every one of 32 crossed
control cells had to pass before story scoring.

## Observed gates

| Battery | Completed | Result | Consequence |
| --- | ---: | --- | --- |
| V3, four initial controls | 32/32 | 28 passed; all four `stage` goal-1 cells failed | Stopped before stories |
| V4, revised controls | 9/32 | Adversarial review found a keep→contain shortcut; partial scores discarded | No complete gate |
| V5, shortcut-balanced controls | 15/32 | 12 passed, 3 failed in `greenhouse` | Stopped once a full pass was impossible |

In V3 the model preferred switching spotlights **off** for astronomy even
when the stated goal changed to a performers' rehearsal. The four failed
margins remained positive across both name and plan orders. The full result
is [the V3 calibration artifact](../results/goal_reversal_v3_calibration.json).

V5 deliberately makes the frozen goal-type and stronger goal-category rules
correct on only 4/8 control goals and 2/4 paired reversals. In its greenhouse
control, opening the windows vents heat for tender seedlings; leaving them
closed retains humidity for heat-tolerant orchids. The bakery control passed
8/8 completed cells. The greenhouse control passed 4/7 completed cells; its
three wrong margins were +1.54 and +3.59 when humidity called for **closed**
windows, and −1.35 when heat protection called for **open** windows. The
eighth greenhouse cell and both remaining controls were not scored. The
[V5 partial artifact](../results/goal_reversal_v5_calibration_partial.json)
contains every completed name score, margin, fingerprint and gate outcome.
The invalidated V4 attempt scored only nine control cells; it contributes no
measurement claim.

## Reading

The goal statement affects some choices: V5's greenhouse has four correct
cells, including one complete correct reversal. But the strict crossed
readout is not reliable enough here to certify story performance. The
failures persisted across changes of name and plan-sentence position, but
these controls do not isolate their cause. They are compatible with
competing goal-word and plan-word associations, plus wording-specific effects. The
data do **not** show that the model cannot reason about goals, or that it
does. They show that this forced-name instrument has not passed a control
battery that requires it to choose against a known lexical shortcut.

The measured checkpoint was `google/gemma-2-9b-it` on NDIF's pinned HOT
deployment. The local tokenizer snapshot revision was
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF does not expose a
weight revision hash, so the exact deployment weights cannot be named more
precisely. The artifacts record code and grid digests and local/NDIF library
metadata. The local host only prepared prompts; the scored forwards ran on
NDIF.

The next test should hold the *goal words and plan verbs* fixed while
changing a causal setup fact that flips which plan serves the goal. It should
freeze independent controls with that same reversal, score both names and
both sentence orders, and use a preregistered contrastive statistic to
measure the fact's effect separately from name and position priors. Such a
result would speak more directly to story-fact integration than a goal-only
switch can.
