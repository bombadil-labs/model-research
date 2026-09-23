# Goal reversal at fixed facts and plans (frozen before scores)

## Question and limits

The previous Gemma chat readout passed 16/16 easy controls and moved its
two-name margin in the expected direction on 40/48 circumstance pairs, but
its choice accuracy was 66/96, below the registered 68/96 minimum. More
fundamentally, changing a good or bad circumstance while holding the goal
fixed leaves a general valence-by-action rule available. This spike asks a
narrower causal question: **when the facts and two worker plans stay fixed,
does changing only the stated goal reverse which worker the model chooses?**
It is a behavioral check before any activation geometry claim.

Use the twelve new constructed dilemmas and four new easy controls in
`research/narrative/prompts/goal_reversal_v5.json`. The v1 grid was frozen
before scores, then adversarial review found that every protective goal chose
the withholding plan. V2 balanced the status quo but a second review found
that all protective goals still chose containing/closing verbs. V3 corrects
the semantic shortcut before any model score. Each dilemma has two
legitimate but incompatible priorities and a single choice of plan. The grid
stores a short rationale for each goal's correct plan; rationales are never
shown to the model. Goals 0 and 1 make plan A and plan B useful,
respectively. Two phrasings of each goal are frozen. The model and prompt are
fixed: `google/gemma-2-9b-it` on NDIF, a single user turn ending with the
grid's exact question. No prompt is selected on story outcomes. Record the
checkpoint, NDIF deployment metadata, tokenizer snapshot revision, library
versions and all code/grid digests. NDIF has so far reported a pinned
deployment without exposing the weight revision; record that limitation
explicitly rather than imply the tokenizer revision identifies the weights.

Within each dilemma and paraphrase, the only text changed between goals is
the goal sentence. The grid is exactly balanced across goal-0 type
(protect/provide) and plan-A physical meaning (release/contain): three
domains in every quadrant. A protective goal is served by release in six
domains and by containment in six; it is served by an act in six and by
withholding in six. Plan A itself is act/withhold 6/6. Thus the two shortcuts
found in review each score 0.5 by construction. The four controls split
plan-A polarity two and two. Cross both assignments of the
two names to plans and both orders of the plan sentences. The common setup,
plan wording, neutral bridge, question and candidate names stay fixed. This
gives 12 domains × 2 goal
paraphrases × 2 name assignments × 2 plan orders × 2 goals = 192 story
prompts, or 96 matched goal pairs. The controls use their own four domains
crossed with goal, name assignment and plan order: 32 prompts. The control
content is disjoint from the story domains and from the previous calibration
grid. Also score a goal-omitted arm once per story domain × name assignment ×
plan order (48 prompts); report its plan/name preference without demanding
chance, since a plan can have a prior even when no goal is stated.

Score the two bare name continuations in alphabetical name order, independent
of plan role, in one NDIF job per prompt with the
validated `asserted_remote_patched_logprob` path, including one BOS and Gemma's
fp32 final softcap. The two candidates must have equal token counts and an
unchanged tokenized prefix. Batch composition is always the same two names.
Checkpoint each score with a fingerprint of the exact rendered prompt,
candidates, model, grids and scoring code. Refuse stale or duplicate rows.
NDIF OOM or queue failure is retried/resumed at the same batch size.

## Calibration and readout checks

For a control, let `m = logp(name for plan A) − logp(name for plan B)`.
Before any story score, every one of the 32 crossed controls must give
`m > +0.1` under goal 0 and `m < −0.1` under goal 1. If one fails, stop:
the elicitor has not demonstrated sensitivity to goal reversal, and story
performance is not graded. Report each control margin and both order effects.

After story scoring, greedily generate at most eight new tokens on a fixed
subset chosen **before** scores: all twelve domains × both goals × both name
assignments, with plan order 0 and paraphrase 0 (48 prompts). A generated
answer is parseable only if the entire continuation consists of exactly one
of the two names, optionally followed by punctuation or whitespace. Report parseability and
agreement with the forced-name winner. Require at least 90% parseability and
90% agreement among parseable answers to treat forced-name choices as a
faithful readout. Any failure narrows the conclusion to the scored
continuations. Do not select generation cases based on story errors.

## Primary test and nulls

In each matched pair, use the name-aligned margin `m` above, irrespective of
which name owns plan A. A **correct choice reversal** requires `m_goal0 >
+0.1` and `m_goal1 < −0.1`. A wrong reversal has the opposite two signs.
Report correct and wrong reversals, same-plan choices, per-goal cell accuracy,
and all domain and factor halves. The primary statistic is the fraction of
96 matched pairs with a correct reversal. The threshold +0.1 excludes
near-ties at the remote readout's practical resolution; report near-ties
separately. The goal-omitted arm reports the baseline margin in both name
assignments and plan orders. Its exact paired goal difference is zero by
construction, so it is a bias control, not an accuracy arm.

For the significance null, flip the two goal labels jointly for all eight
pairs of each domain, enumerate all 2^12 domain sign patterns, and compare the
correct-reversal fraction with that exact orientation distribution. Bootstrap
domains 10,000 times on fixed predictions for a 95% interval. Report a
word-overlap baseline: lower-case `[a-z]+` word tokens in each goal sentence
and each plan sentence, remove the two names and this frozen stopword set:
`a an the to for and or of in on at with from by as is was were be its it
that they their one only now planned plan immediate goal`. Compute Jaccard
overlap, and choose the plan with higher overlap; ties count as 0.5.
Shared object nouns in both plans contribute equally to the two overlap
scores. On the frozen grid this baseline is 0.490 across the 48 goal phrasings,
computed before any model score. Also report a frozen goal-type shortcut: a goal is protective when it
contains one of `keep kept protect protected preserve hidden unexposed
unaware intact undiscovered hold delayed unable unmixed available private`
as a whole word, and the shortcut chooses the withholding plan for such a
goal and the active plan otherwise. All 48 frozen goal phrasings classify as
their declared type, and the six/six status-quo balance predicts 0.5 accuracy
for this shortcut. The second frozen shortcut uses the same goal detector
but chooses the **containing** plan for protective goals and the releasing
plan otherwise. The containing plan is identified by exactly one of the two
plan sentences containing a whole-word match from `sealed dark off raise
store locked close moored silent closed`. All twelve plan pairs meet that
rule, and the protect-by-release/contain balance predicts 0.5 for it too.
These baselines are descriptive; semantic associations beyond these two
coarse rules remain possible.

An adversarial review of V3 identified a stronger ceiling that uses the goal
sentence and the plan verbs but no setup or causal facts. Freeze this ordered
goal-category rule before scoring: choose **release** if the goal contains a
whole-word match from `unsafe reef rocks flood floodplain floodline pressure
bursting smoke fumes warn alerted`; otherwise choose **contain** if it matches
`raider raiders patrol rival pursuer pursuers interception unknown undiscovered
unaware monitoring hiding` or `preserve intact available warm warmth retain
supply breeding reference sample unexposed`; otherwise choose **release**.
Map that category to the one plan bearing the containment marker listed
above, or to the other plan for release. Across the 48 goal phrasings, this
frozen rule has 45/48 correct individual choices and 21/24 correct paired
reversals (0.875), before any model score. Its errors are one bridge phrasing
and both pasture delivery phrasings. Report the model's reversal fraction
alongside this ceiling. A model pass below it supports goal-sensitive choice
but remains consistent with goal-category-to-plan-verb matching without using
the dilemma's causal facts.

Call **goal-sensitive choice established on this constructed grid** only if:

1. The 32-control calibration passes.
2. At least 70% of the 96 matched pairs are correct reversals.
3. At least 60% of the 48 matched pairs are correct in **both** name
   assignments at the same domain × paraphrase × plan order.
4. The exact domain-orientation upper-tail p is at most 0.05 and the
   domain-bootstrap interval lower bound is above 0.5.
5. Each name-assignment, plan-order and paraphrase half has a correct
   reversal fraction above 0.5.
6. The fixed generation subset meets the parseability and agreement gates.

If a gate fails, report it as a failure of this positive screen, with the
observed effects and controls; do not relabel the design or threshold from
the score. Passing would establish goal-dependent *behavior* in these
miniatures, not an invariant latent narrative shape. A future activation
study must use its own preregistered readout, lexical/position controls,
held-out domains and causal checks.

## Amendment 1: calibration failure and new control battery

The first V3 run scored **only** the 32 calibration cells, then stopped as
specified. It passed 28/32. All four failures were goal 1 in the `stage`
control: the scorer preferred turning the spotlights off for astronomers even
when the stated goal was performers rehearsing. No story, goal-omitted or
generation cell was scored. The full calibration result, including every
margin, is in `research/narrative/results/goal_reversal_v3_calibration.json`.

After seeing that control result, V4 replaces **all four** controls with new,
disjoint cases (`bakery`, `observatory`, `records`, `aquarium`). The twelve story
domains, their goal phrasings, the question, the neutral bridge, both
candidate continuations and every decision threshold are text-identical to
V3. The new battery again crosses four domains with both goals, both name
assignments and both plan orders. Plan A is active in two controls and a
withholding plan in two. No V4 control or story score existed when this
amendment was written. There is no further control replacement in this run:
if any V4 control fails, the run stops. A V4 pass is an **exploratory amended
screen** because the calibration instrument was revised after seeing its V3
failure. Formal confirmation would need a fresh independently fixed battery.

## Amendment 2: balance the controls against the frozen lexical ceiling

Adversarial review of V4 found that all four `keep` control goals chose
the containing plan, while the other goals chose release. A simple
keep→contain rule could therefore pass all 32 controls without using their
setups. The exact frozen goal-type and goal-category baselines scored 7/8 and
6/8 goals respectively, still above neutral. A V4 run had started while
review was pending. It was interrupted after nine **control** scores; there was no
complete calibration, story score or generation, and those partial scores are
discarded. This supersedes Amendment 1's planned no-replacement rule because
the battery had a pre-score design flaw.

V5 keeps the V4 `bakery` and `records` controls and replaces `observatory`
with `greenhouse` and the earlier `aquarium` with a heat-versus-cat version.
In both new controls, a protective **preserve** goal requires the releasing
plan: opening vents trapped heat. A separate provision goal requires the
containing plan: closed windows retain humidity for heat-tolerant orchids,
and a closed aquarium lid provides a barrier against a cat. These are
unambiguous physical tradeoffs in the frozen setups. Among the eight V5
control goals, both the frozen goal-type→contain rule and the stronger frozen
goal-category→plan-semantic rule have 4/8 correct choices and 2/4 correct
paired reversals. The scorer asserts both rates. Two controls have plan A
active and two withholding. The twelve story domains, the question, bridge,
candidate continuations and thresholds remain text-identical to V3 and V4.
No V5 score existed when this amendment was written. V5 is still an
exploratory amended screen; if its controls fail, stop and report the failure.
