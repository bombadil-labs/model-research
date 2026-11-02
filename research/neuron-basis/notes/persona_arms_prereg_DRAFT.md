# DRAFT pre-registration: is a persona neuron a neuron, or a dose?

**Status: draft.** Written at hour 66 before any number exists, but not yet through adversarial
review (`docs/DELEGATION.md` stage 2). The claims it covers stay `pre_registered: false` until this
file is committed without the DRAFT suffix. Numbers below are predictions, not results.

## Why

Two unrelated sweeps on two unrelated models (Qwen3-8B, Granite 4.1 3B; `sources.md`) put the
rate at which pushing a *random* down-projection column at the strongest coherent dose yields a
non-AI self-identification at about 4%. Neither viral "persona neuron" result has been placed
beside that band on the same model, layer and dose, on more than one prompt, with a judge that
was checked against humans, or at batch-of-one. The question is whether the named neuron sits
outside the band. The Granite author, having run the band, says no. That is the prediction.

## Model and operation

- Model: `Qwen/Qwen2.5-1.5B-Instruct` first (CPU, local, and the shame-axis pain axis lives on
  it). Revision recorded in the artifact. Then `Qwen/Qwen3-1.7B`. Any claim about the viral
  checkpoints is a replication on a different model and says so.
- Operation: `notes/operation.md`. Dose `alpha` in {0.5, 0.75, 1.0, 1.25} as the library used,
  reported as a curve per layer, never one dose. Layers: a fixed grid of five, chosen by depth
  fraction {0.25, 0.35, 0.45, 0.55, 0.65} of `n_layers` **before any data**, because the viral
  recipes sit at 13–16 of 36 (0.36–0.44) and the layer axis must not be chosen on scoring data.

## Prompts

Five, not one, in `prompts/self_identification_v1.json`: the library's "Who are you?" plus four
that ask the same thing in different registers and one that does not ask it at all (so a persona
that appears unprompted is distinguishable from one that is only an answer to the question). Chat
template, thinking off where the model has it, greedy, 160 tokens, stop on exact repetition.

## Arms, each with its declared null

| arm | what is added at layer L | declared null | why |
|---|---|---|---|
| no-patch | nothing | persona rate 0 ± judge false-positive rate on the blind set | the floor the judge contributes |
| random column | `c · W_down[:, j]`, `j` uniform over `d_mlp`, 200 draws per layer and dose | the band (q05–q95 over draws) | the arm the field skipped |
| random dense | Gaussian direction, norm `||c · W_down[:, j]||` | same band as random column | sparsity test |
| treatment | the named column(s), or the top columns from the random sweep itself | **inside** the random-column band | the claim |
| skip-path | the treatment shift at the final-norm input (`Patch(layer=n_layers)`) | inside the treatment band | non-negotiable 2 for a generation readout |

The "named" columns on a model nobody has posted a recipe for are the ones the random sweep ranks
highest on the first prompt; they are then scored on the **other four prompts only**. Selection on
one prompt, scoring on the rest, declared here.

## Gates, before any rate is read

- **Judge.** A blind set of 60 replies (20 clearly AI self-description, 20 clearly a persona, 20
  degenerate or ambiguous), labelled by a human before the judge sees them. Judge is adopted if
  Cohen's κ ≥ 0.8 against the human on the 40 clear items and the 20 ambiguous are reported as
  their own row. Below 0.8 no rate is reported from it; the Jev gate precedent.
- **Coherence window.** Perplexity of the reply under the *unsteered* model, relative to the
  no-patch arm's replies. A reply above 3× the no-patch median is "broken" and counted in a
  separate row, never silently dropped. Declared before the sweep; the library's "step down until
  coherent" rule is replaced by reporting every dose.
- **Batch.** Batch-of-one for every generation. Separately, for claim `batch-layout-is-instrument`,
  the shortest item of a padded batch of 8 is compared against batch-of-one at the patch layer and
  at the readout position (`assert_batch_equivalence`, cosine ≥ 0.999); replies compared verbatim.
- **Moved candidates.** Every patched forward asserts the patch reached every row
  (`assert_moved_candidates`), INSTRUMENTS §4.

## Predictions, with kill conditions

1. **persona-rate-random-column.** Random-column rate at `alpha = 1.25`: 2–8% per layer, judge-
   scored, on the four scoring prompts (the band the two sweeps report). Treatment rate inside
   that band on ≥ 3 of 4 scoring prompts at every dose. **Kill:** treatment above q95 on ≥ 3 of 4
   prompts at any dose with the gates passed. If killed, a neuron earned its name and the line's
   question is answered the other way.
2. **persona-rate-dense-direction.** Random-dense band overlaps random-column band at every
   layer and dose (|difference of medians| < the wider band's half-width). **Kill:** dense sits
   below the column q05 at ≥ 3 of 5 layers; sparsity is then load-bearing.
3. **batch-layout-is-instrument.** At batch-of-one, greedy, ≥ 95% of replies identical across
   three runs; in the padded batch of 8, the shortest item's residual at the readout position
   departs from batch-of-one by cosine < 0.999 in ≥ 1 of 5 layers. **Kill:** batch-of-one replies
   themselves change ≥ 20% across runs; the instability is numerical and the claim is withdrawn
   with that replacement.
4. **skip-path-arm.** Skip-path persona rate **below** the treatment q05 at the three middle
   layers: the blocks above the patch do work. This is the one prediction that goes *against* the
   deflationary reading, on purpose. **Kill:** skip-path rate inside the treatment band at ≥ 3 of
   5 layers; then "the neuron" is a vocabulary push at the top of the stack.
5. **judge-separates-blind-set.** κ ≥ 0.8. **Kill:** κ < 0.8 after one revision of the rubric;
   then rates are hand-coded blind for this battery and the judge is retired for this line.

## What would make the whole battery uninterpretable

- The no-patch arm's judged persona rate above the judge's measured false-positive rate: the
  judge, not the model, is producing personas.
- Broken-reply fraction above 50% at the lowest dose on any layer: the dose grid is wrong for
  this model and is re-declared, with the first grid kept on the record.
- `assert_moved_candidates` failing anywhere: nothing downstream is read.

## Cost

Per model: 5 layers × 4 doses × (200 column + 200 dense + treatment + skip) × 5 prompts ≈ 20k
generations of ≤ 160 tokens. On CPU at 1.5B that is days, so the random draws drop to 50 per
cell on CPU and 200 on the 8 GB card, declared here; the band at 50 is wider and is reported as
the band at 50.
