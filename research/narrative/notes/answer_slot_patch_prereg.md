# Can the shared answer-slot direction causally bias a two-name choice?

**Frozen before any activation patch on these targets.** The
[route-to-property replication](choice_slot_replication_result.md) found a
block-24 first-listed-person direction shared between two-link route stories
and eight independent property-choice domains. Readout alignment does not
show that the direction affects a choice. This experiment asks whether
adding it changes the model's two-name log-probability margin in the
predicted direction. The target grid and its unpatched activations have
already been observed; the patch outcomes and dose have not. This is a
conditional causal follow-up on known prompts, not a fresh representation
replication.

## Fixed source, target and patch

Model: pinned NDIF `google/gemma-2-9b-it`, with local tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`; NDIF gives no weight
revision hash. Build `u` exactly as in the replication: unit-normalize each
route-story `I_first` at block 24, average all eight source domains, both
tellings, names and plan orders, then unit-normalize the mean. The source
route activation fingerprints must match the committed pilot. No target
state or patch score enters `u`.

Take the 64 prompts in `choice_slot_replication_v1.json` with `telling=0`
and `world=0`, crossing eight domains, two name assignments, two fact
orders and both goals. The early telling is the weaker of the two observed
readout halves (+0.498 versus +0.668), chosen here before patching as the
more conservative target. World 0 holds the fact binding fixed; crossing
the two goals makes role A correct in one and role B correct in the other.
Fact order makes the first-mentioned person correct in half of each domain's
eight prompts. Name assignment balances identity. This battery tests an
answer-slot bias, not the model's ability to infer a new fact.

Patch the output of block 24 by **adding the same vector at every real
token position** using the verified `asserted_remote_patched_logprob` path.
The primary norm is 20.0 residual units, about 6% of the target's observed
median final-token block-24 norm (~334), fixed before patch outcomes. Score
the two bare name candidates in one batch per prompt with the same single
`<bos>`, fp32 softcap and candidate mask as the previous behavioral scores.
Because the core patches every position, a positive result is a causal
effect of a distributed block-24 addition, not proof that the final token
alone is sufficient. All target names are one token under the frozen
tokenizer, so candidate-token hidden states cannot affect the probability
of their own first token; the scored logits come from the prompt boundary.

Arms on **every one of 64 prompts**, with identical two-candidate batch
shape and no chunk fallback:

1. No patch.
2. Zero-vector pass-through at block 24.
3. `+20u` and `−20u` treatment.
4. `±20r1` and `±20r2`, where `r1,r2` are independent unit vectors from
   NumPy `default_rng(20260923)` and `default_rng(20260924)` standard normals,
   normalized in float64 then cast to float32 before scoring.

This is 512 jobs. Each row fingerprints prompt, candidate order, arm,
exact float32 vector, source and target grids, model, tokenizer revision,
core code and script code. Resume only exact matches and refuse duplicates.
Retry transient NDIF failures at the same two-candidate batch size.

## Instrument gates and statistics

Before bulk patching, assert one BOS, identical prompt-token prefix on both
candidates, one token per candidate, left-padding convention and equal
batch shape. On the shortest target prompt, pass all six nonzero vectors
through `assert_patch_reaches_batch` on the **two full candidate texts**;
each must move both residual rows. Run the core score path on that same
prompt for every arm. The no-patch and zero-vector scores must agree per
candidate within 1e-3. Score all 64 no-patch and pass-through cells, and
require the same tolerance throughout; separately compare no-patch to the
earlier unpatched cache as a deployment-drift check (also ≤1e-3).

The core's per-candidate moved-score assertion can fail when a bf16 score
is unchanged at this dose, even though the residual patch reached both
rows. Therefore score every nonzero arm through the core with `base=None`,
record the count of candidate scores different from its same-prompt
no-patch baseline at tolerance 1e-6, and flag any arm/prompt with fewer
than two. A flagged score is retained as a measured numerical zero only
if the corresponding vector passed the two-row residual reach preflight;
otherwise the instrument fails. Report the per-arm moved-count histogram.
This policy is fixed before seeing a patched score and follows the bf16
resolution lesson in INSTRUMENTS §7.

Let `m = logp(A-owner) − logp(B-owner)` and `s=+1` when A's fact sentence
comes first, else `s=−1`; `s·m` is the first-mentioned-person margin. For
each nonzero direction `v`, the signed steering effect on a prompt is
`E(v) = s·[m(+20v)−m(−20v)]/2`. The primary is the mean of `E(u)` within
each domain, then the equally weighted mean of eight domains. A positive
value means `+u` favors the first-mentioned person, as predicted by how
`I_first` was oriented in the source. Report effects for each of the 64
prompts, both random directions, every domain, name/order/goal halves, and
whether `+u` creates or removes a correct-name choice compared with no
patch. Report candidate-level score changes so a shift in the *wrong*
candidate can be distinguished from a change in total score.

The primary exact null independently reverses the effect sign in each of
eight target domains, enumerating all 2^8 assignments including identity.
The one-sided floor is 1/256. Bootstrap 10,000 seeded samples of eight
fixed domain effects for a 95% interval. Report the random-direction
domain means and their maximum absolute magnitude; two directions are
controls, not a calibrated tail distribution. A registered positive screen
requires: instrument gates pass; mean `E(u) ≥ +0.10` nat; exact p≤.05;
bootstrap lower bound >0; at least six of eight domain means and 48 of 64
prompt effects positive; and `E(u)` exceeds twice the maximum absolute
random-direction mean. Report each criterion separately. A null with all
instruments passing limits steering at this fixed dose and patch location;
it does not disprove that a different layer, dose or local-token patch
could work.

If positive, the conclusion is a **causal generic answer-selection bias**
under a block-wide residual addition. It is not a narrative-role edit,
proof of causal sufficiency for the original route interaction, or a
method for transforming a whole story. A future story edit would need to
patch a story-stage state and show a targeted semantic change with
unwanted changes measured.
