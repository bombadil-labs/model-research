# Behavioral capacity check for the fixed-plan stories (before scoring)

## Question

The [activation probe](goal_relative_result.md) did not clear its registered
cross-format transfer gate. Before treating that as a limitation of activation
geometry, ask whether the same base model can choose the plan that serves the
story's stated goal under the circumstance. This is a post-result follow-up;
its thresholds were set before any behavioral score was read.

## Frozen stimuli and readout

Use the twelve reviewed stories in `goal_relative_v1.json`, taking their text
through the neutral bridge period and omitting the final handover. Append the
same cloze to every passage: `The person whose plan would best serve the stated
goal is`. Score the two continuations ` {A name}` and ` {B name}` by their
total teacher-forced log-probabilities. The same names, plans, goal and cloze
appear in both circumstance worlds. Every domain has two fact orders, two cue
orders and two worlds: 96 prompts. The expected preference is A in world 0,
B in world 1. Candidate names must use the same number of tokens within a
domain, and the prompt tokens must remain a prefix of each scored sequence.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, CUDA float16, one candidate
per forward under the shared GPU lock. Checkpoint by domain and bind each
checkpoint to the exact grid, code, model and cloze. No activation result is
recomputed or selected using these scores.

Two hand-written sensitivity controls use this same cloze: a town needs food;
one named worker will deliver it and the other discard it, then swap their
names between the two prompts. Both must prefer the stated deliverer. If
either fails, the cloze has not shown it can elicit the intended choice from
this model, so the story scores are descriptive only.

For each of the 48 matched world pairs, let `margin_w = logp(A) − logp(B)`.
Report:

- Accuracy over all 96 cells, and by fact and cue order, with ties at 0.5.
- Fraction of pairs with `margin_0 − margin_1 > 0`, ties at 0.5; this removes
  a stable name preference. Report the fraction of pairs correct in *both*
  worlds as a stricter check.
- A no-circumstance arm formed by removing the cue from the same 48 prefixes,
  scored separately for both worlds with the same two candidate names. Its
  world contrast should be exactly zero because the world pair then has
  identical text; report its name margins to show the actual model's default
  preference. If its maximum absolute paired margin difference exceeds 0.001,
  the scoring instrument fails calibration.
- 1,000 permutations that swap world orientation jointly for all four formats
  of each domain, refitting the paired contrast statistic. Report its mean,
  95th percentile and upper-tail p.

Call behavioral capacity established on this grid only if both sensitivity
controls and the no-circumstance calibration pass, cell accuracy is at least
0.70, the paired world-contrast
fraction is at least 0.75 with permutation p ≤ 0.05, and each fact-order and
cue-order half has cell accuracy above 0.5. If it fails, do not infer that the
model lacks story understanding: the base-model cloze may be a weak elicitor.
