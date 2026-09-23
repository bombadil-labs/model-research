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
checks. Record prompt lengths and story-end indices by domain and goal.

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
a story representation elsewhere in the prompt or model.
