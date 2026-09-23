# Pre-registration: is the self/other split instilled by post-training? (hour 64)

**Written before any activation from these four models exists.** Raised by the human author: "if
this is shame, then the shame would have been instilled in post-training." *Paraphrase*; the
author's words are in the conversation, not in a commit.

## What is already known, and why it is not enough

The paper's published per-model screens (`Pain-axis/results/4.1_self_other/per_model/`, upstream
at 8d1649c) give each model's s2 pain-axis z for the 420 scenarios. An exploratory look at those
numbers, taken before this note, found the self-directed minus vicarious gap present in every base
model, e.g. Gemma-2-9B base +1.12 against instruct +1.14, and Llama-3.1-70B base +1.33 against
instruct −0.31. That look has three limits:
- the numbers are the paper's, replicated by us on one model only;
- they have no lexical floor, and hour 52 found vocabulary takes most of the pain effect;
- base models were rendered as a raw transcript and instruct models with the chat template,
  so **format and training are confounded**.

This hour removes all three.

## Models and access

| family | base | instruct | where |
|---|---|---|---|
| Gemma-2-2B | `google/gemma-2-2b` | `google/gemma-2-2b-it` | local GPU (RTX 3060 Ti), bf16, one text per forward |
| Llama-3.1-70B | `meta-llama/Llama-3.1-70B` | `meta-llama/Llama-3.1-70B-Instruct` | NDIF (both pinned) |

Gemma-2-9B base is loaded on NDIF but not pinned, and this key cannot hotswap it, so it is out of
reach. Local runs record `cuda` and bf16, per CLAUDE.md.

## Measurement

For each model, reuse the hour 51–53 recipe:
- the paper's core sets (S1_1P, S2_1P, ControlSupplement_1P) and control sets (Arousal, Random,
  Numb _1P) as raw sentences with the tokenizer's own BOS;
- the 420 scenarios in **both** renderings: `raw` (the paper's plain "[User]: … [Assistant]:"
  text) and `chat` (the model's own chat template, with the template's BOS counted once);
- final-token and mask-mean pooling at every captured block output, plus the unscaled embedding
  output.

Gemma-2-2B captures all 26 blocks. Llama-70B captures every 4th block plus the paper's layers
for it (S1/S2 steering 32/40 base and 24/24 instruct; the vector-file layers 70 and 48). That
keeps its stacks inside local RAM. The curve is reported at those layers.

**Step 1: replication gate, per model.** At the paper's screen layer, in the paper's own format
(raw for base, chat for instruct), item-level Pearson r between our s2 z and their CSV must be
≥ 0.99. Their screen file does not name its layer. r is reported at both the S1 and S2 steering
layers, and the one that matches identifies it; that identifies a layer, it does not select one
for a claim. Also reported: the cosine between our pain vector and theirs at their vector-file
layer. **A model that fails the gate is not interpreted**; the failure is reported.

**Step 2: the question.** Per model and per rendering, at the replicated layer and across the
curve, measure the hour-53 statistic. That is the self-directed minus vicarious difference in
mean z, computed twice: once on the network's own direction, and once on the static-embedding
bag floor built the same way. The **network contribution** is the network's split minus the
floor's split. The quantity that answers the question is

`Δ_post = contribution(instruct) − contribution(base)`, **at matched rendering**,

computed per family and per rendering (raw and chat), with a 95% bootstrap interval over items.

- **Instilled by post-training** predicts Δ_post > 0, with the interval excluding zero, in both
  families and at both renderings.
- **Present from pretraining** predicts that base's contribution is itself above its nulls,
  and Δ_post ≤ 0 or its interval includes zero.
- Anything else (families disagreeing, or renderings disagreeing) is reported as mixed. It
  answers neither way.

**Nulls:** random unit directions and shuffled-label pain vectors, at every captured layer, as
in hour 52. A contribution is read only above both. **The format effect** is reported separately
as contribution(chat) − contribution(raw) within each model, since it is exactly the confound in
the exploratory look.

## What this does not test

This is the self/other split, not shame. The shame-versus-pain stimuli
(`shame_vs_pain_design_DRAFT.md`) are still blocked on authorship. When they exist, they run on
these same four models.

## Amendment 1 (before any activation): three readings of "the axis shrinks after post-training"

Raised in a parallel conversation and relayed by the human author (a paraphrase of another
Claude instance's reply; the text itself is not in the repo). If post-training reduces the axis,
there are three readings, and they make different predictions:

| reading | decoding in instruct vs base | causal influence | where the change falls |
|---|---|---|---|
| **relief** | drops | drops | wherever the signal was |
| **masking** | holds | drops | — |
| **narrowing the chorus** (fewer voices modelled) | drops for other-directed items | — | concentrated in **vicarious** items; self-directed unchanged |

Hour 64 adds two measurements, per model, per rendering, at every captured layer:
- **Decoding:** held-out (5-fold by item) logistic-probe AUC for self-directed vs vicarious, and
  for the paper's pain vs control sets. This is decodability, as distinct from how far items
  project on the paper's single direction.
- **Where the change falls:** base → instruct change in mean z, reported separately for
  self-directed and vicarious items, network and bag floor. *Narrowing* predicts |Δ vicarious| >
  |Δ self|, with self's interval including 0.

**Causal influence is out of scope for hour 64.** It needs a steering battery on every model,
and a behavioural readout that means the same thing in a base model, which has no assistant
turn. That is a follow-up with its own pre-registration. Until then, 62b (instruct only:
correlate, not cause) is half of the masking test, not the test.

**Known before this amendment, so not a prediction test:** the paper's numbers had already been
looked at, and the drop there falls mostly on self-directed items (Llama-70B, Qwen-32B,
Gemma-27B). The pre-registered test is on our own replicated, floor-adjusted, format-crossed
measurements.

**Operational note (before any activation):** the base tokenizers (`gemma-2-2b`,
`Llama-3.1-70B`) carry no chat template. Their `chat` rendering uses the instruct sibling's
template, and the script asserts the two vocabularies are identical.
