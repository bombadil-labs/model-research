# Can one story-fact state redirect a later route choice?

**Frozen before any source-to-target patch on this battery.** The
[crossed two-hop screen](goal_route_cross_result.md) showed that changing
which destination each route reaches changes the selected worker. The
[pre-question extraction](prequestion_route_state_result.md) found no
*shared first-listed direction* at the story ending, but found a large
local factorial interaction immediately after the late-telling route facts.
This experiment tests a different property: whether a **single residual
state at that informative story token** can move the later answer toward
the other world's route winner. The stronger question is whether it
transmits anything beyond the destination noun immediately before the
period. Even a positive result would be a small causal latent edit, not a
trope shape.

## Fixed prompts, state and source-target pairs

Use exactly the 256 original `goal_route_cross_v1.json` story prompts and
the cached three-position pre-question states for provenance and an
independent state check. Model: pinned NDIF
`google/gemma-2-9b-it`, tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`; NDIF does not expose a
weight revision hash. Use only **late telling** cells (`telling=1`): setup,
goal, plans, first-hop facts, second-hop facts, neutral bridge, question.
At the informative boundary, the final period of the second-hop facts is
one token decoded `.`. It is before the neutral bridge and the explicit
answer question. The previous extraction checked its causal prefix in the
same full trace by replacing all future tokens and finding bit-exact states.

For every domain × name assignment × plan order × goal × target world,
pair the target with the **other world** at exactly the same factors:
8 × 2 × 2 × 2 × 2 = **128 target/source pairs**. The two worlds exchange
only the target and foil destination nouns between the second-hop clauses.
The route, goal, names, fact order, full word bag, total length, final 200
characters and candidate names are identical within each pair. Assert
equal tokenized prompt lengths, equal informative-period indices and token
IDs within each pair, one BOS, and unchanged prompt-token prefixes when
the candidate is appended. Score one-token bare names alphabetically in a
two-candidate, **zero-padding** batch.

Construct one diagnostic **last-noun-only** text per target by changing
only the destination noun in the final second-hop clause to its other-world
counterpart. Its first second-hop clause remains as in the target, so both
clauses now lead to the same destination and the text is deliberately
inconsistent. Assert a single exact suffix-clause substitution, an
unchanged prefix before that noun and an unchanged suffix after it.
Capture its period state in the
same two-candidate shape. The tokenizer audit before any patch score must
confirm which domains preserve the period index and full prompt length.
The registered length-matched set is clinic, library, orchard, factory and
ship; infer beyond-last-noun effects only on those five. Theater, shelter
and museum lexical comparisons are descriptive because the noun change
shifts the period index and full prompt length by one token.

Let `h_t` and `h_s` be the target/source residual vectors at the
informative period **after block 24**, captured in the same two-candidate
batch shape as the scoring jobs. There are 128 distinct late-telling
prompts, and each prompt serves once as target and once as source, so
capture each state's two rows once before any treatment score. The two
rows must be bit-identical at the informative period; candidate continuations
are causally downstream of it. Compare every batch-captured state to its
cached one-prompt extraction at the same token and block, under the
original fingerprints. Require cosine ≥0.999 and relative L2 error ≤0.02;
the bound admits the previously observed bf16 job-shape drift while
refusing a changed state. The treatment is `delta = h_s − h_t`, cast to float32 and
added at that **one token position in both candidate rows** after block 24
of the full *target* prompt. No other token is patched. Thus the patched
period state equals the same-batch counterfactual source state up to the
deployment's bf16 rounding. The rest of the target text, including its world-0/1 fact
words, remains unchanged. Record delta norms and source-to-patched
residual errors. No dose or layer is selected from patch outcomes.
Block 24 and this token were selected from the earlier observational
extraction on these prompts. The causal screen is conditional on that
site; it is not a fresh search over positions or layers.

## Arms and instrument gates

On every target prompt score these arms with the same two-candidate
teacher-forced logits, using the same single-BOS, fp32 softcap and mask
formula as the verified core:

1. No patch.
2. Zero-vector patch at the informative period after block 24.
3. **Source-world delta** at that period after block 24.
4. **Last-noun-only direction**, the diagnostic state's period vector minus
   the target's, unit-normalized and scaled to the full source-world delta's
   norm, at the same block and position. This is a conservative lexical
   comparator at the treatment's dose; record its unscaled norm too.
5. **Plan-order delta** from the same world, goal and name assignment with
   the plan sentences reversed, also normalized to the full delta's norm.
   The correct person is unchanged. This is an in-distribution
   answer-neutral perturbation at the same state site.
6. A seeded Gaussian vector, unit-normalized then scaled to the exact
   norm of that pair's delta, at the same period and block.
7. The **same source delta after final block 41**, at the same earlier
   period. This is the pass-through control: final norm and head are
   positionwise, and the period is before the answer token, so its correct
   score effect is zero. In the offline readout equation,
   `logits_at_prompt_end = head(norm(h41[prompt_end]))`; adding `delta`
   only to `h41[informative_period]` leaves that argument unchanged.

This is 896 scored jobs and 256 state-capture jobs (128 original prompts,
128 noun-only prompts), plus a small preflight.
The Gaussian seed is
`20260923 + domain_index*16 + factor_index` with factor index
`name*8 + plan_order*4 + goal*2 + target_world`; use NumPy
`default_rng(seed).standard_normal`, float64 normalization, then float32.
Checkpoint each row with the exact prompt, candidate order, token index,
patch arm and float32 tensor hash, model, source and target grid digests,
original-state fingerprint, same-batch target/source state hashes,
tokenizer revision and script/core digests.
Reject stale or duplicate rows. Retry NDIF OOM and queue timeouts at the
same batch size, without a shape fallback.

The single-position scorer is line-local because the shared core patches
all positions. Use **one traced scoring function** for the no-patch,
capture, and patched jobs, with one optional position and vector; the
preflight calls that same function with residual capture enabled. For
each of the four nonzero block-24 arms, call
`checks.assert_moved_candidates` with the **same-prompt no-patch** pair of
candidate scores, requiring both rows to move. If it raises, rerun that
exact job twice without the assertion, require both candidate scores to
agree within 1e-3, save the deterministic row as flagged, and fail the
instrument if more than 5% of the 512 nonzero block-24 jobs are flagged.
There is no score-movement assertion on the zero and final-block arms:
both are required to leave the answer scores unchanged.

Before scoring the grid, compare the new **unpatched** scorer with core
`asserted_remote_patched_logprob` on the shortest and longest prompts,
candidate by candidate (≤1e-3), and with the committed no-patch core scores
on all 128 target prompts (≤1e-3). In the state-capture jobs, assert the
same two-row batch shape, zero padding, one BOS, bit-identical period
states across candidate rows, and the registered ≤0.02 relative distance
to the original one-prompt states. Assert the same two-row batch shape and
zero padding on every job. On the shortest prompt, capture block-24
residuals before and after a nonzero period-only patch: both rows at that
one index must move by the declared bf16 addition, and every other token
position must stay bit-exact. Run that residual preflight through the
same traced scoring function as the grid. Repeat at block 41 and verify its logits
match the no-patch arm within 1e-3. The all-grid zero-vector and block-41
arms must also match no-patch candidate scores within 1e-3; a failure
invalidates the instrument. Report per-arm candidate movement counts,
the number of deterministic zero-score responses, and the source-state
match error at the patched period. The source and target states must be
readable above repeat drift under the original extraction gates.

## Registered effect and interpretation

Let `m = logp(A-owner) − logp(B-owner)`. For a target world `w` and goal
`g`, the **source** world prefers A exactly when `(1−w)==g`; otherwise it
prefers B. Independently derive the source winner by following the
grid's plan→route→link→destination chain to the requested goal and
assert agreement with this formula on every cell. Define `s=+1` in the
former case and `s=−1` in the latter.
The treatment effect is `s·(m_source_patch − m_no_patch)`; positive means
the target choice moves toward the counterfactual source-world winner.
Report its mean for each domain, target world, goal, name, plan order, the
64 world-paired contrasts, and all 128 prompts. Report the same signed
effect for the lexical, plan-order, random, zero and final-block controls,
plus forced-choice flips toward and away from the source winner.

The primary statistic is the mean of eight domain means, each averaging
16 target cells. Use an exact one-sided 2^8 domain sign-flip null (identity
included; floor 1/256) and a seeded 10,000-draw bootstrap over the eight
fixed domain effects. A **positive causal screen** requires all instrument
gates, mean source-patch effect ≥+0.25 nat, exact p≤.05, bootstrap lower
bound >0, at least six of eight domain effects and 96 of 128 cell effects
positive, and the treatment mean exceeding twice the maximum absolute
mean of the Gaussian and plan-order controls. These are controls, not a
calibrated null distribution; report their values even if a gate fails.

The **beyond-last-noun** analysis compares the full and norm-matched
lexical signed effects on the five length-matched domains. A positive
beyond-last-noun
screen additionally requires mean `(full − lexical) ≥+0.10` nat, at least
four of five domain differences positive, the exact one-sided 2^5 domain
sign-flip p≤.05 (floor 1/32), and a 10,000-draw five-domain bootstrap
lower bound >0. Report the full and lexical effects separately on all
eight domains, with the three length-shifted domains labelled. If the
full screen passes but this comparison does not, the evidence supports
only a single-token intervention compatible with the preceding noun.

If the causal screen passes, this one story-stage token state can bias a
later choice toward the other world's winner at the preselected site. If
the beyond-last-noun screen also passes, that effect exceeds a patch made
from just the immediately preceding destination noun in five matched
domains. Otherwise, the effect may be a lexical echo. The edited state
remains inside a target text whose visible facts say something else; it
does not construct a coherent source-world story. Neither result shows
that this one token fully carries the route graph, that the surplus
encodes a relation rather than both destination nouns as a bag, that it
generalizes to unrelated narratives, or that a complete story can be
changed coherently.
A null with instrument gates passing limits **single-token block-24
substitution at this period**; distributed states or other positions may
still carry the relation. The long neutral bridge may attenuate the edit.
