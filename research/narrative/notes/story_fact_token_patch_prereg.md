# Can one story-fact state redirect a later route choice?

**Frozen before any source-to-target patch on this battery.** The
[crossed two-hop screen](goal_route_cross_result.md) showed that changing
which destination each route reaches changes the selected worker. The
[pre-question extraction](prequestion_route_state_result.md) found no
*shared first-listed direction* at the story ending, but found a large
local factorial interaction immediately after the late-telling route facts.
This experiment tests a different property: whether a **single residual
state at that informative story token** can transmit a counterfactual
world binding into the later answer. A positive result would be a small
causal latent edit of story information, not a trope shape.

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

## Arms and instrument gates

On every target prompt score these arms with the same two-candidate
teacher-forced logits, using the same single-BOS, fp32 softcap and mask
formula as the verified core:

1. No patch.
2. Zero-vector patch at the informative period after block 24.
3. **Source-world delta** at that period after block 24.
4. A seeded Gaussian vector, unit-normalized then scaled to the exact
   norm of that pair's delta, at the same period and block.
5. The **same source delta after final block 41**, at the same earlier
   period. This is the pass-through control: final norm and head are
   positionwise, and the period is before the answer token, so its correct
   score effect is zero. In the offline readout equation,
   `logits_at_prompt_end = head(norm(h41[prompt_end]))`; adding `delta`
   only to `h41[informative_period]` leaves that argument unchanged.

This is 640 scored jobs and 128 state-capture jobs, plus a small preflight.
The Gaussian seed is
`20260923 + domain_index*16 + factor_index` with factor index
`name*8 + plan_order*4 + goal*2 + target_world`; use NumPy
`default_rng(seed).standard_normal`, float64 normalization, then float32.
Checkpoint each row with the exact prompt, candidate order, token index,
delta/random float32 tensor hash, model, source and target grid digests,
original-state fingerprint, same-batch target/source state hashes,
tokenizer revision and script/core digests.
Reject stale or duplicate rows. Retry NDIF OOM and queue timeouts at the
same batch size, without a shape fallback.

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
position must stay bit-exact. Repeat at block 41 and verify its logits
match the no-patch arm within 1e-3. The all-grid zero-vector and block-41
arms must also match no-patch candidate scores within 1e-3; a failure
invalidates the instrument. Report per-arm candidate movement counts,
the number of deterministic zero-score responses, and the source-state
match error at the patched period. The source and target states must be
readable above repeat drift under the original extraction gates.

## Registered effect and interpretation

Let `m = logp(A-owner) − logp(B-owner)`. For a target world `w` and goal
`g`, the **source** world prefers A exactly when `(1−w)==g`; otherwise it
prefers B. Define `s=+1` in the former case and `s=−1` in the latter.
The treatment effect is `s·(m_source_patch − m_no_patch)`; positive means
the target choice moves toward the counterfactual source-world winner.
Report its mean for each domain, target world, goal, name, plan order, the
64 world-paired contrasts, and all 128 prompts. Report the same signed
effect for the random, zero and final-block controls, plus forced-choice
flips toward and away from the source winner.

The primary statistic is the mean of eight domain means, each averaging
16 target cells. Use an exact one-sided 2^8 domain sign-flip null (identity
included; floor 1/256) and a seeded 10,000-draw bootstrap over the eight
fixed domain effects. A **positive causal screen** requires all instrument
gates, mean source-patch effect ≥+0.25 nat, exact p≤.05, bootstrap lower
bound >0, at least six of eight domain effects and 96 of 128 cell effects
positive, and the treatment mean exceeding twice the absolute random
mean. The random direction is a norm-matched control, not a calibrated
null distribution; report its value whether or not the gate passes.

If positive, one story-stage token state can causally bias the later
answer toward a counterfactual world, despite the visible source words
remaining absent from the target prompt. It does not establish that this
one token fully carries the route graph, that the result generalizes to
unrelated narratives, or that a complete story can be changed coherently.
A null with instrument gates passing limits **single-token block-24
substitution at this period**; distributed states or other positions may
still carry the relation. The long neutral bridge may attenuate the edit.
