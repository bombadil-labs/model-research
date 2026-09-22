# Audit: every chat-rendered opener and generation readout ran on `<bos><bos>` (hours 55–62a)

**Written before any corrected number exists.** Found 2026-09-22 while building 62b.

## The defect

Gemma-2's chat template emits `<bos>` as text. `lsx.core.remote._encode` tokenized with
`add_special_tokens=True`, and `asserted_remote_generate` handed nnsight a string, which does the
same. A chat-rendered prompt therefore reached the model as `<bos><bos><start_of_turn>…`. Verified
on a `v0` item with the model's own tokenizer: `add_special_tokens=True` gives ids `[2, 2, 106, …]`.

It passed every check. `v0_openers.score` asserts exactly one `<bos>`, but on
`tok(text, add_special_tokens=False)`, which is not the tokenization that was sent. Hour 53 caught
the same hazard in the dense extraction path (`painaxis_scenarios.py`,
`double_bos_if_add_special_tokens_true: 1`), and that path, `extract_pooled` with
`add_special_tokens=False`, is unaffected. The fix never reached the scoring path.

## Scope

| readout | hours | script | affected |
|---|---|---|---|
| greedy generation | 55 | `conscription_behaviour.py` | yes (nnsight tokenizes the string) |
| opener log-odds, grids 1–2 | 56, 59, 59b | `conscription_openers.py` | yes |
| opener log-odds, `v0` | 62a | `v0_openers.py` | yes |
| dense-axis stacks | 51–54, 61 | `extract_pooled(add_special_tokens=False)` | no |
| SAE readouts | 57–58b, 60 | from the dense stacks | no |
| narrative line | all | raw text, no chat template | no |

## Fix

Commit on `shame-axis`, touching `lsx.core.remote` and `lsx.core.checks`: special tokens are added
only to text that does not already begin with `<bos>`; every encoded row must carry exactly one
(`checks.DoubleBos`); mixed batches are refused; generation is pre-tokenized. `double_bos_bug=True`
reproduces the old path, for this audit only.

## What is measured, and what counts

1. **Attribution.** A sample of old rows rescored with `double_bos_bug=True` must reproduce the
   committed numbers. If it does not, the difference is not the bug, and nothing below is
   interpretable until it is explained.
2. **62a, all 420 items**, rescored with one `<bos>`, then run through `v0_openers.report`
   **unchanged**: same tiers, floor, permutation null, Holm. **62a survives** if every verdict in
   its table (primary A − B at the floor; A − N and B − N above; B − C at the floor) comes out the
   same. Any flipped verdict withdraws the claim that rests on it, in place, replaced by the
   single-`<bos>` number.
3. **Hour 56 (grids 1–2, 288 rows)**, same procedure with `conscription_openers.report`, against
   the verdicts recorded for hours 56, 59 and 59b.
4. **Hour 55** (generation) is re-run last, and only if 2 or 3 moves a verdict. Its claims rest
   on hand-coded continuations, so rescoring means regenerating and recoding.

Per-item |Δritual| between the two tokenizations is reported for every rescored row, whatever
happens to the verdicts.
