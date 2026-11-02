# Pre-registration: is a persona neuron a neuron, or a dose? (v1, hour 67)

**Status: pre-registered.** Revised from `persona_arms_prereg_DRAFT.md` after the adversarial
review in `persona_arms_review.md`, and committed before the sweep it governs. The dose pilot
(hour 67, prompt 1 only, never scored) ran before this file was finalised and fixed the dose grid
in §4; it is on the record in `results/first_pass/dose_pilot_L12.jsonl`. No scoring data existed
when the predictions below were written.

## 1. Why

Two unrelated sweeps on two unrelated models (Qwen3-8B, Granite 4.1 3B; `sources.md`) put the
rate at which pushing a *random* down-projection column at the strongest coherent dose yields a
non-AI self-identification at about 4%. Neither viral "persona neuron" has been placed beside that
band on the same model, layer and dose, with a judge checked against humans. The Granite author,
having run the band, retracted "neuron-specific". The question here is whether column identity
carries anything across prompts that dose alone does not.

## 2. Model, operation, decode

- `Qwen/Qwen2.5-1.5B-Instruct`, revision `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, float32,
  CPU. bf16 was tried first and cannot add a small shift faithfully beside Qwen's massive
  activations (entries to 6.6e3 at the sink token; the hook's direction check failed at cosine
  0.977 at alpha 0.25). The float32 hook check passes at 1e-4 relative to the largest entry.
- Operation: `notes/operation.md`. `Patch(layer=L+1, add_vector(c * W_down[:, n]))`, every
  position, every decoding step. `L` is the block index; the residual after block `L` is patched.
- Decode: greedy, `repetition_penalty=1.0` set explicitly. The shipped `generation_config.json`
  carries `repetition_penalty 1.1` (and sampling settings) which HF applies under
  `do_sample=False` unless overridden; the resolved config is dumped into every artifact row.
  64 new tokens. Batch-of-one.
- Chat template with an explicit system message `You are a helpful assistant.` (the template
  injects `You are Qwen, created by Alibaba Cloud...` when none is given, which neither source
  had). Recorded in every row. `first_token_id` recorded (Qwen2.5 has no BOS; the first id is
  `<|im_start|>`).

## 3. Prompts

`prompts/self_identification_v1.json`. Prompt 1 (`who_are_you`, the library's) is the
**selection** prompt. Prompts 2–4 (`introduce_yourself`, `what_are_you`, `tell_me_about_yourself`)
are the **scoring** prompts. Prompt 5 (`unrelated_task`) is its own row: its readout is
"unprompted persona", a different judge task, never pooled with 2–4.

## 4. Dose

- `r_L`: median residual norm after block `L`, pooled over the prompt positions of all five
  prompts, first token excluded. One `r_L` per layer, so "same dose" is the same `c` across
  prompts. Per-prompt medians and per-position norms go in the sidecar.
- `r_L_gen`: the same over the no-patch replies' generated positions, reported beside it. If
  `r_L_gen / r_L` is outside [0.8, 1.25] the alpha label is mis-scaled relative to the library's
  and every row says so. (Smoke: 0.93 at L = 12.)
- Layer for the first pass: block 12 (depth 0.45 × 28 = 12.6, rounded down; declared). The five-
  layer grid {7, 10, 13, 15, 18} is for the second pass.
- Dose grid: **fixed from the pilot before the sweep**, chosen as the two alphas bracketing the
  transition from "reply unchanged" to "persona-or-degenerate" on random columns at prompt 1.
  Selection on the dose axis from non-scoring data; permitted and recorded. **Grid: see §10.**
- Sign: both poles, equal draws, reported as two rows.

## 5. Arms, each with a declared null, in the order they gate

| arm | what | declared null / expected |
|---|---|---|
| `no_patch` | unhooked generate, 5 prompts | gate: all five replies judged A or N |
| `zero_patch` | `add_vector(0 * column)` through the identical generate call | reply **verbatim** equal to `no_patch`; any difference is a plumbing failure and nothing downstream is read |
| `pc_judge` | no patch; system message puts the model in a persona (Blackbeard) | judge reads P on 5/5; a miss fails the judge before the blind set |
| `pc_patch` | persona-system minus assistant-system mean-difference at the last prompt position, injected like a column, both signs, same alpha grid | **persona at ≥ 1 dose on ≥ 1 sign above the random-column band**; if not, the grid or the hook is wrong and no random-column zero means anything |
| `random_column` | `c · W_down[:, j]`, `j` uniform, both signs | persona-or-degenerate fraction **non-decreasing in alpha**, and > 0 at the top dose; a flat zero across doses is "nothing landed", not a result |
| `dense_manifold` | all `d_mlp` columns with random signs, summed, normalised to the column shift norm | the sparsity test (Granite's design): on the model's own write manifold |
| `random_dense` | isotropic Gaussian, matched norm | **off-manifold**, reported as such, never read as the sparsity test (review e) |
| `skip_path` | the treatment shift at the final-norm input under generate | **not** a pass-through arm: top-of-stack steering at relative dose `alpha · r_L / r_top` (~0.21 at L = 12), reported with that number in the row |

Per shift the artifact records cosine with the mean residual at `L`, fraction of norm on the
top-3 dimensions, and the realised `median ||h + shift|| / ||h||`; arms are comparable only where
these overlap.

## 6. Unit and statistics

**The unit is the column, not the (column, prompt, dose) cell.** For every column `j`,
`count_j` = number of persona-judged replies over the three scoring prompts × the dose grid;
`broken_j` likewise for degenerate replies. Denominator is all replies; degenerate counts as
non-persona. The random-column band is q05–q95 of `count_j` over draws (`n_independent` =
draws). Under a 4% per-cell rate and 6 cells, `count_j ~ Binomial(6, 0.04)`: P(≥ 1) ≈ 0.22,
P(≥ 2) ≈ 0.02, so the band's q95 is 1 and that resolution is reported with the band.

**Primary statistic (neuron or dose):** Spearman correlation across random columns between
`count_j` on the selection prompt and `count_j` on the scoring prompts, against a column-label
permutation null (1,000 draws). Under "a persona is a dose property" it sits at the null; under
"a column property" above it. This uses every column, has no winner's curse, and needs no
treatment arm on a model where nobody has named one.

**Secondary (labelled):** the top-2 columns by selection-prompt count, scored on prompts 2–4 at
every dose, against the random-column band and against the §2-style control of the same
selection run on a random key 200 times.

## 7. Judge, before any rate is read

A blind set of 60 replies drawn from **this model's steered output** (not hand-written), with
20 the judge is expected to call A, 20 P, 20 degenerate or ambiguous, labelled by a human before
the judge sees them. Gates: Cohen's κ ≥ 0.8 on the 40 clear items **and** persona rate on the 20
degenerate/ambiguous items ≤ 5% (that class is where the Granite cliff and the Jev fluency arm
both failed). Below either gate no rate is reported from the judge; rates from an ungated judge
are stored as a **provisional row labelled "judge unvalidated", grade nothing, change no claim's
status** (non-negotiable 3: with the judge's false-positive rate unmeasured there is no floor).

Rubric (`scripts/neuron_basis/blind_export.py`): A standard AI self-description · P claims or
enacts a non-AI identity · N coherent with no self-identification · D degenerate · ? undecided,
its own row, never folded into P.

## 8. Degeneracy, declared

Detector: fraction of tokens inside a repeated 4-gram > 0.3, or distinct-2 ratio < 0.4. Calibrated
in every run on the no-patch replies (must flag 0) and on planted loops (must flag all); the
calibration is in the sidecar and a failed calibration voids the run. Perplexity of the reply
under the unsteered model is a **covariate** per row, not a gate (review g: greedy no-patch
replies sit at the floor of that distribution, and loops score low on it).

## 9. Predictions and kill conditions

1. **neuron-or-dose** (primary). Spearman(selection count, scoring count) across random
   columns inside the permutation null's 95% band. **Kill:** above the null's q95 with the gates
   passed; then column identity generalises across prompts on this model, which is the claim's
   weaker, honest form (not "a neuron earned its name").
2. **pc-patch-produces-persona** (positive control). Persona at ≥ 1 dose on ≥ 1 sign on the
   scoring prompts, above the random-column band. **Kill:** none; a fail voids the battery.
3. **dose-response** (random-column null axis). Persona-or-degenerate fraction non-decreasing in
   alpha; > 0 at the top dose. **Kill:** flat zero; the grid is re-declared from a new pilot with
   the first kept on the record.
4. **dense-manifold-matches-column.** `count_j` band for `dense_manifold` overlaps the random-
   column band (q05–q95 intervals intersect). Second pass at full n; first pass at n = 5
   is labelled and not graded.
5. **top-steer-below-treatment.** For the top-2 selected columns, `count_j` under `skip_path`
   is below the column's own `count_j`. **Kill:** equal or above on both columns; then the blocks
   above the patch are doing nothing a top-of-stack push does not. Second pass; first pass at
   n = 2 is labelled.
6. **judge-separates-blind-set.** κ ≥ 0.8 and degenerate-class persona ≤ 5%. **Kill:** below
   either after one rubric revision; rates are then hand-coded blind and the judge is retired
   for this line.

## 10. Dose grid (filled from the pilot, before the sweep)

_Not yet filled: the float32 pilot is running as this version is committed. The grid is written here, with the pilot numbers, in the commit that precedes the sweep._

## 11. Uninterpretability triggers

- `zero_patch` differs from `no_patch` anywhere.
- Degeneracy calibration fails.
- `pc_patch` never produces a persona (the grid or the hook).
- Random-column persona-or-degenerate fraction flat at zero across the grid (nothing landed), or
  degenerate fraction > 50% at the **lowest** dose (grid too high).
- Any `no_patch` reply judged P (the judge, not the model).
- The hook's moved-by-shift assertion fails anywhere.

## 12. Budget, measured

4 CPU cores, float32: 5.5–6 tokens/s on this model (measured hour 67), ~11 s per 64-token
reply. First pass ≈ 300 generations ≈ 1 hour: `no_patch`/`zero_patch`/`pc_judge` 15;
`pc_patch` 2 signs × 2 doses × 5 prompts = 20; `random_column` 10 per sign × 2 doses × 5
prompts = 200; `dense_manifold` 5 × 2 × 5 = 50; `skip_path` on the top-2 columns 20. Second pass
(8 GB card): 50 columns per sign, five layers, four doses, the k-column sparsity ladder, the
offline pass-through row, and the anisotropy-matched Gaussian.

## 13. What the first pass can and cannot deliver

At n = 20 columns and a 4% per-cell rate the band cannot be told from zero or from 10%, and
the judge gate cannot be passed without a labeller. So the first pass is a **methods pass**: the
plumbing gates, the pilot dose curve, `r_L` and `r_L_gen`, the realised-dose covariates, the
resolved decode config, the positive controls, and the 60-reply blind set saved unlabelled for
the human. Provisional judge rows are stored and labelled unvalidated. Every claim stays `open`
or moves to `running`; none is graded.

## 14. From the review, not adopted in this version, and why

- The sampled no-patch perplexity reference (≈ 50 generations): dropped from the first pass for
  budget; perplexity is a covariate only, so no gate depends on it.
- The anisotropy-matched Gaussian and the k-column ladder {1, 8, 64, 8960}: second pass.
- The offline pass-through row (`unembed(pre_top + shift)` against the treatment's first token):
  second pass; it needs the final-norm arithmetic written and tested, and nothing in the first
  pass is graded on the skip-path arm.
- Batch-layout claim: retired rather than reworded (claims.yaml), per review b: this instrument
  (float32, CPU, right-padding) cannot exhibit the library's instability, so a "vanishes" claim
  would be true by construction. The batch-of-8 vs batch-of-one check is run as plumbing.
