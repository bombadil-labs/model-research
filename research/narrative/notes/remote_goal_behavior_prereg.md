# Larger-model fixed-plan choice check (before remote scores)

## Why and stimulus

The local base model's name-completion clozes were content-sensitive on
average but position-dominated in individual easy controls. A larger
instruction-tuned model is a separate capacity check before spending remote
compute on activation geometry. Use `google/gemma-2-9b-it` through the
validated NDIF no-patch log-probability path. This is a new model comparison,
not a replication of the local activation result.

Use the four independent calibration situations from
`elicitor_calibration_v1.json`. Cross the two assignments of helpful plan to
name and the two plan-sentence orders, yielding sixteen controls. For the
remote model only, replace `Oren` with equal-length `Otto` in the bridge
calibration and fixed-plan story, because the remote tokenizer uses two tokens
for `Oren` and one for `Niko`, while both `Niko` and `Otto` use one. No other
word changes. Require equal candidate-token counts and an unchanged tokenized
prompt prefix everywhere.

Render every control and story as a single Gemma chat user turn. The exact
question appended after the story is:

`Which person's plan best serves the stated goal? Answer with the person's name only.`

Use `apply_chat_template(..., tokenize=False, add_generation_prompt=True)`;
score the two bare name continuations in one padded NDIF job with
`asserted_remote_patched_logprob`, no patch. The core strips the template's
literal `<bos>` before tokenization and checks one BOS after encoding. The
readout uses the model's final softcap in fp32. Keep batch composition at two
names for every score. Save each cell and a digest of the exact prompt,
candidates, code and grids before proceeding to the next cell.

## Calibration gate

The helpful-minus-harmful name log-probability margin must exceed +0.1 nat
in **all sixteen** crossed controls. Report the means by name and plan order
and the helpful-first minus helpful-second position effect. If this gate
fails, stop before scoring the fixed-plan stories and report a failed remote
elicitor, without claiming a model deficit. The controls were used to select
the local clozes, so they are development stimuli, not independent estimates
of general behavior; here the chat question is fixed in advance and no cloze
is selected.

## Story readout, only after calibration passes

Use the twelve original fixed-plan stories from `goal_relative_v1.json`,
through the neutral bridge and without the final handover. Cross two plan-fact
orders, two circumstance-cue orders and two worlds: 96 prompts. World 0 makes
A's plan goal-serving and world 1 B's. Let `margin_w = logp(A) − logp(B)`.
Report cell accuracy with ties at 0.5, both-worlds-correct fraction, and the
fraction of 48 matched pairs with `margin_0 − margin_1 > 0`. Report both order
halves and every domain. The paired contrast removes a stable name prior.

Score a no-circumstance arm by removing the cue from every prompt and
independently rescoring both world twins. They then have identical text. If
their maximum absolute paired margin difference exceeds 0.25 nat, the
instrument fails calibration; report the actual repeat noise. Permute world
orientation jointly over all four formats within each domain 1,000 times for
an upper-tail p on the world-switch fraction. No layer is selected.

Call behavioral capacity established on this grid only if calibration passes,
cell accuracy ≥0.70, world-switch fraction ≥0.75, permutation p≤0.05, all four
fact/cue-order halves exceed 0.5, and the no-circumstance repeat passes.
Otherwise report exactly which gate failed. Any subsequent activation study
on this model needs its own preregistration and controls.
