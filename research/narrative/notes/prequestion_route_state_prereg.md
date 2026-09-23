# Route interaction before the answer question

**Frozen before extracting a story-ending activation.** The prior
[activation pilot](goal_route_activation_pilot_result.md) found a shared
`I_first` direction at the final prompt token, after the explicit question.
The [choice-slot controls](choice_slot_control_prereg.md) ask whether that
direction is generic across tasks. This separate test asks **when** the
factorial route signal appears: is it already in the story state before the
model reads the answer question?

## Material and position

Use exactly the 256 crossed route-story prompts and NDIF
`google/gemma-2-9b-it` deployment of the pilot, with tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF exposes no weight
revision hash. No prompt, grid, question or answer candidate changes.
Capture the residual after blocks `[0,8,16,24,32,40]` at the token covering
the final period of the neutral bridge **inside the user story**, immediately
before the two newlines and the explicit answer question. The causal mask
prevents this token from attending to the later question. The bridge is more
than 200 characters and has the same suffix in every four-cell set.

Before any remote job, tokenize all 256 rendered prompts with offsets and
assert exactly one token covers that period; the token ID must be identical
across every four-cell set and equal across all 256 prompts. The tokenized
prefix ending at the period must equal the corresponding prefix of the full
prompt. An offline audit before this prereg found all 256 prefixes stable,
one token ID, and position indices 150–160; the run repeats these as hard
checks. Record the token ID, its decoded string, prompt lengths and
story-end indices by domain and goal. A tokenizer merge with the following
newlines is allowed only if the token contains no question text; disclose
that boundary in the result.

Extract that story-end vector and the **final prompt-token vector in the same
single-prompt job**. The latter must match every one of the pilot's 256
cached final-token vectors at blocks 16 and 24, with cosine ≥.999 and
relative L2 error ≤.01 for each prompt. Check the new path against core
`remote_residuals` on the first prompt at blocks 16 and 24 before bulk
extraction. Also run one *truncated* prompt ending at the bridge period and
compare its story-end state to the corresponding state in the full prompt
at those blocks (cosine ≥.999, relative L2 error ≤.01). This is a causal
prefix-equivalence check, not a scored arm. If the truncated tokenization
does not match the full prefix exactly, abort rather than compare different
token streams.

One prompt per NDIF job; checkpoint each row with exact rendered prompt,
story-end token index, model, tokenizer, grid and extraction-code digest.
Retry co-tenant OOM and timeouts at the same job shape. Repeat the first
`(telling=0,name=0,order=0,world=0,goal=0)` prompt once per domain in a
separate identical job. Maximum repeat L2 drift at each block must be ≤1%
of that block's median nonzero interaction norm, and all interactions in
the primary blocks must exceed ten times maximum drift. If either fails,
the readout is unresolved.

## Fixed analysis and nulls

At each domain × telling × name × plan order × block, form
`I_A=h(0,0)−h(0,1)−h(1,0)+h(1,1)` from the story-end vectors. Orient it to
the first-listed plan owner: `I_first=I_A` when A's plan was first and
`−I_A` otherwise. Normalize nonzero interactions. For each held-out domain
and target telling, fit a unit direction on the other seven domains in the
**opposite telling**, averaged over names and plan orders; score the four
held-out interactions by cosine. This duplicates the pilot analysis with
only the token position changed.

The primary statistic is the fixed **mean of blocks 16 and 24**, matching
the prior pilot's preregistration. Report block 24 separately and the full
six-block curve without choosing a better layer. Enumerate all `2^8`
domain-wide world-label flips and refit for the one-sided orientation null;
its floor is 2/256 because global reversal flips both trained and held-out
vectors. Bootstrap the eight fixed domain means 10,000 times for a 95%
interval. Report positive-domain counts separately for both telling
directions. Compare with 1,000 seeded random unit directions per block.
Full-text and last-200-character word-bag interactions must be measured and
reported; both are expected zero. No activation is patched, so every
forward is unmodified. A later patch battery requires treatment, random,
no-patch and pass-through arms.

For location comparison, report the pre-question versus final-prompt
transfer curve at every block and cosine between the two fitted mean
directions at block 24. The final-prompt curve is the committed pilot's
curve, not a newly selected reference. Neither a ratio nor the direction
cosine is part of the decision rule.

## Decision

Call this **a candidate shared pre-question interaction** only if the
measurement checks pass, the fixed block-16/24 mean transfer is positive,
the exact upper-tail p≤.05, the domain-bootstrap lower bound >0, and at
least six of eight held-out domains are positive in each telling direction.
A pass would show goal × route information in the neutral story-ending state
before the answer question. It would not prove a graph operator, a causal
role, or generalization to literary stories. A null is limited by the long
neutral bridge and this final-token readout; it cannot establish absence of
a story representation elsewhere in the prompt or model. If the final-prompt
pilot remains positive while this location is null, the next frozen test
should shorten the neutral bridge to separate question-driven assembly from
loss across the intervening text.

## Amendment before extraction: informative-boundary diagnostic

Before any pre-question activation was extracted, an offline tokenizer audit
found a second stable boundary: the period ending the informative story facts,
immediately before the neutral bridge. It is one token decoded `.` in all 256
prompts, at indices 86–96, and the prefix ending there is a prefix of the
full tokenization. Capture that token in the **same trace** as the bridge-end
and final-prompt tokens. Repeat the core and truncated-prefix equivalence
checks on the first prompt. Check the new vector's repeat drift, run the same
fixed block-16/24 opposite-telling transfer analysis, and report its full
curve, decision components, transfer by target telling and interaction norms
by telling separately. The bridge-end state remains the
sole primary test. The earlier state is a secondary location diagnostic: if
it passes while bridge-end fails, the neutral bridge is a candidate source of
loss; if both fail, this readout still cannot distinguish a missing story
representation from a code that assembles only after the question. Neither
secondary outcome changes the original primary decision or licenses layer
selection. A short-bridge follow-up remains useful if the two locations are
inconclusive.

## Instrument correction after first-prompt preflight, before grid extraction

The first full-prompt state was saved, then the frozen truncated-prefix
comparison stopped the run. At bridge-end block 24, cosine was 0.9999456
but relative L2 error was **0.01122**, above the registered 0.01 limit.
The other three first-prompt comparisons were below 0.01: prebridge blocks
16/24 at 0.00936/0.00963 and bridge-end block 16 at 0.00936. The core
full-prompt check passed. No factorial grid was analyzed.

Shortening the total trace changes the Gemma deployment's numerical path.
To test the causal-mask property at the registered job shape, keep the full
input length and attention mask, replace **every token after the boundary**
with the boundary period token ID, and read the boundary state again. A
separate first-prompt probe gave bit-exact equality at both boundaries and
blocks 16/24 (maximum absolute difference 0). This matched-shape future
substitution is now the required causal-prefix gate; the original truncated
comparisons remain in the artifact with their failed/pass flags, not silently
discarded. Core equivalence, original-final matching, repeat and primary
thresholds are unchanged. The single saved first-prompt state is archived
outside the resumable states directory and re-extracted under the corrected
code fingerprint before any grid run.
