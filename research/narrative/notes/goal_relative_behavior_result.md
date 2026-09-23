# The behavioral cloze fails its own sensitivity gate

## Design and provenance

The [preregistered follow-up](goal_relative_behavior_prereg.md) checked whether
the same base model used in the [activation probe](goal_relative_result.md)
prefers the worker whose fixed plan serves a stated goal when a circumstance
changes. It scored both names as continuations of a fixed cloze after each of
the twelve stories, in both worlds and both sentence-order factors: 96 story
prompts. A paired world contrast subtracts each domain's stable name
preference. The no-circumstance arm removes the status cue, and two simple
food-delivery examples test whether the cloze can elicit a known correct name.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16. All
candidate-prefix and equal-token-count checks passed before scoring. One
candidate was scored per forward; results were checkpointed by domain. The
[summary](../results/goal_relative_behavior_summary.json) records the grid and
code digests, exact model/device/library provenance, raw-score digest and
registered metrics. Detailed log-probabilities remain in ignored
`cache/goal_relative/behavior`.

## Calibration and descriptive result

| Registered check | Result |
| --- | ---: |
| Simple food example, deliverer Mara | Correct; log-prob margin +0.922 |
| Same example with names swapped, deliverer Lena | **Incorrect**; margin −0.078 |
| No-circumstance repeated world pairs | Exact: maximum margin difference 0, switch score 0.500 |
| Story cell choice accuracy | 0.500 across 96 cells |
| Both worlds correct in a matched pair | 0 of 48 |
| Paired world-switch fraction | 0.563; permutation p = 0.297 |

Both fact-order halves and both cue-order halves score 0.500 cell accuracy.
The world-switch permutation mean is 0.503 and 95th percentile 0.604 over
1,000 draws. A stable name preference is visible in the no-cue arm, but it
cannot produce a world contrast. The no-cue repeated prompts agree exactly,
so the run is deterministic at the measured resolution.

The two easy-example margins contain a small content signal: expressed as
`logp(Mara) − logp(Lena)`, they are +0.922 when Mara delivers food and +0.078
when Lena delivers it. Their average is a +0.500 name prior for Mara; half
their difference is a +0.422 effect in the correct direction for the
deliverer. On this pair, the cloze responds to the plan but the name prior
overrides it in one order. A name-balanced or paired-contrast elicitor is the
next instrument to test.

**The registered behavioral-capacity gate fails at its sensitivity control.**
The second easy example's margin is close to zero but points to the wrong
name. Consequently, the story scores are descriptive and cannot tell us
whether this base model understands the useful-plan relation. They also do
not change the activation probe's registered verdict. A new elicitation
instrument needs to pass independent simple examples in both name orders
before its story-level null can be read as a model limitation.
