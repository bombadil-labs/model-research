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
median final-token block-24 norm (~334) and 0.69 times the median natural
goal-flip projection gap on `u` (~29.0) in these unpatched target states.
These are geometric references measured before patch outcomes, not dose
selection from a steering result. Score
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
2. Zero-vector **identity** at block 24.
3. `+20u` and `−20u` treatment at block 24.
4. `±20r1` and `±20r2`, where `r1,r2` are independent unit vectors from
   NumPy `default_rng(20260923)` and `default_rng(20260924)` standard normals,
   normalized in float64 then cast to float32 before scoring, at block 24.
5. The same six nonzero vectors at **last block 41**, using the same verified
   scorer. This is the direct-path pass-through: at the final block output
   there is no further transformer computation, so it reads final norm,
   `lm_head` and softcap on the unpatched last-block state plus `20v`.
   Comparing block-24 and block-41 effects subtracts the additive route
   that survives without blocks 25–41. The last-block arm reruns the same
   unpatched prefix, but the intervention has no downstream attention or
   MLP layers. Assert at preflight that block-41 patching changes the
   captured last-block residual by the declared vector on both rows.

This is 896 score jobs plus the residual preflight. Each row fingerprints
prompt, candidate order, arm, patch layer,
exact float32 vector, source and target grids, model, tokenizer revision,
core code and script code. Resume only exact matches and refuse duplicates.
Retry transient NDIF failures at the same two-candidate batch size.

## Instrument gates and statistics

Before bulk patching, assert one BOS, identical prompt-token prefix on both
candidates, one token per candidate, left-padding convention and equal
batch shape, with **zero padding on every job**. On the shortest target
prompt, pass all six nonzero vectors at both block 24 and block 41 through
`assert_patch_reaches_batch` on the **two full candidate texts**; each
must move both residual rows. Capture no-patch last-block residuals on that
batch and compare the six directly patched last-block residuals to the
captured state plus the declared float32 vector at the scored prompt token,
after casting both operands to bf16 and performing the addition, with
maximum absolute error ≤1e-3. Run the core score
path on that same
prompt for every arm. The no-patch and zero-vector scores must agree per
candidate within 1e-3. Score all 64 no-patch and pass-through cells, and
require the same tolerance throughout; separately compare no-patch to the
earlier unpatched cache as a deployment-drift check (also ≤1e-3).

The core's per-candidate moved-score assertion stays **armed**: pass each
nonzero job its same-prompt no-patch candidate scores as `base`. If it
raises `MovedCandidates`, rerun the job twice with `base=None`, require
those two score vectors to agree per candidate within 1e-3, record the
deterministic score vector and flag it. If the two runs differ, abort as an
unstable measurement. A flagged score can remain a measured numerical zero
only if its patch/layer passed the two-row residual reach preflight.
More than 5% flagged among the 768 nonzero score jobs fails the instrument.
Record candidate movement counts at 1e-6 and the per-arm flag histogram.
This deterministic bf16 exception policy is fixed before a patched score.

Let `m = logp(A-owner) − logp(B-owner)` and `s=+1` when A's fact sentence
comes first, else `s=−1`; `s·m` is the first-mentioned-person margin. For
each nonzero direction `v`, the signed steering effect on a prompt is
`E24(v) = s·[m(+20v at block 24)−m(−20v at block 24)]/2`.
Define `E41(v)` identically for the direct-path block-41 arm. The **sole
primary** is the net computational effect `E_net(u)=E24(u)−E41(u)`, averaged
within each domain and then equally over eight domains. A positive net
value means adding `u` at block 24 favors the first-mentioned person
through subsequent computation beyond its direct residual carry. Report
total `E24`, direct `E41` and net effects for every one of the 64 prompts,
both random directions, every domain, name/order/goal halves, and
whether `+u` creates or removes a correct-name choice compared with no
patch. Report candidate-level score changes so a shift in the *wrong*
candidate can be distinguished from a change in total score.

The primary exact null independently reverses the **net** effect sign in each of
eight target domains, enumerating all 2^8 assignments including identity.
The one-sided floor is 1/256; report tie count. Bootstrap 10,000 seeded
samples of eight fixed domain effects for a 95% interval. Report the two
random-direction **net** domain means and their maximum absolute magnitude;
two directions are controls, not a calibrated tail distribution. A
registered positive screen requires: instrument gates pass; mean
`E_net(u) ≥ +0.10` nat; exact p≤.05; bootstrap lower bound >0; at least six
of eight domain means and 48 of 64 prompt effects positive; and the net
mean exceeds twice the maximum absolute random net mean. Report each
criterion separately. Also report the total and direct effects with their
own exact sign null and bootstrap as **secondary** tests, without moving
the primary. A net null with all instruments passing limits steering
beyond direct pass-through at this fixed dose and patch location;
it does not disprove that a different layer, dose or local-token patch
could work.

If positive, the conclusion is a **causal generic answer-selection bias
beyond direct residual carry** under a block-wide addition. If total
steering passes but net steering does not, the result supports only a
shallow additive output bias. Neither is a narrative-role edit,
proof of causal sufficiency for the original route interaction, or a
method for transforming a whole story. A future story edit would need to
patch a story-stage state and show a targeted semantic change with
unwanted changes measured.
