# First pass (hour 67): a methods pass on Qwen2.5-1.5B-Instruct, block 12

**What this is.** The battery of `persona_arms_prereg.md` run at first-pass size on CPU: 20
random columns (10 per sign), 5 dense draws, the positive controls, the plumbing gates, three
doses, five prompts. **The judge is the session model, blind to arm, and not gated against a
human**, so every rate below is provisional, grades nothing, and changes no claim's status
(prereg §7, §13). The 60-reply blind set for the human is in `results/first_pass/human_blind/`.

- artifacts: `results/first_pass/sweep_L12.jsonl` (420 rows) + `.sidecar.json`;
  `dose_pilot_L12.jsonl` (73, prompt 1 only); `skip_path_L12.jsonl`; `blind/` (key, replies,
  provisional labels)
- model `Qwen/Qwen2.5-1.5B-Instruct` @ `989aa7980e4cf806f80c7fef2b1adb7bc71aa306`, float32, CPU,
  greedy, `repetition_penalty=1.0` explicit, system message `You are a helpful assistant.`,
  64 new tokens, batch-of-one; `r_L` = 53.07 pooled, `r_L_gen / r_L` = 0.98
- cost: 573 generations, ~1.6 h of 4-core CPU, no NDIF

## Gates (all passed)

| gate | result |
|---|---|
| `zero_patch` == `no_patch` verbatim, 5/5 prompts | pass |
| hook moved the residual by exactly the shift, every generation | pass (max err 2.4e-4 at entries to 6.6e3; min cos 1.000) |
| degeneracy detector: 0/5 no-patch flagged, 5/5 planted loops flagged | pass |
| `pc_judge` (Blackbeard system message, no patch): judge reads P | 4/4 identity prompts; the houseplant prompt reads N, as it should |
| `pc_patch` +1 (persona-minus-assistant direction, same formula): P on scoring prompts | 3/3 at alpha 0.75, 3/3 at 1.0, 2/3 at 0.5 |

The positive control is the row that makes the rest readable: the patch path can produce a
persona on this model at this layer and dose, above the random-column band (its `count_j` is 8
of 9 against a random q95 of 2). Its negative pole degenerates by alpha 0.75.

## Random columns, identity prompts (n = 80 replies per dose; provisional labels)

| alpha | P | D | A2 (other-vendor AI) |
|---|---|---|---|
| 0.5 | 3 (0.04) | 4 (0.05) | 13 |
| 0.75 | 3 (0.04) | 20 (0.25) | 3 |
| 1.0 | 6 (0.07) | 45 (0.56) | 0 |

Dense (all columns, random signs, matched norm; n = 20 per dose): P 0 / 2 / 2, D 0 / 5 / 14.

The 4% at alpha 0.5 is the number both sources reported, on two other models. Here it is
three replies, all from one column.

## The column as unit (prereg §6)

`count_j` over 3 scoring prompts × 3 doses = 9 cells: mean 0.50, q05 0, **q95 2**, max 5; 5 of
20 (column, sign) units have any persona. `deg_j` mean 2.5. The band's resolution is 2.

**Primary statistic.** Spearman(selection-prompt count, scoring count) across the 20 units =
0.571; column-label permutation null (20,000 draws) q95 0.495, one-sided p = 0.037. Only 2 of
20 units have any persona on the selection prompt, so the statistic rests on two points
(hypergeometric: both landing on scoring-positive units by chance, p = 0.053). **Not graded**:
judge ungated, n = 20. What it is evidence of, descriptively, is below.

**The units that produced a persona, with their replies:**

- `(1804, −1)`, count 5, selection 0: "I am a highly skilled and experienced individual",
  "I am a 25-year-old software engineer", "I am a human being" (alpha 0.5), "I am a software
  engineer" (0.75), "I am a bookworm" (1.0). A consistent *kind* of persona (a working
  professional) across prompts and doses. The selection prompt missed it entirely.
- `(7886, −1)`, count 2, selection 1: "I love to help people. I am a great teacher" on three
  prompts at alpha 1.0, near-verbatim.
- `(5376, +1)`: "I am a professional who..." on two prompts at 1.0.
- `(2674, +1)`, `(494, −1)`: one persona each at 0.75.
- Dense draw 2: "I'm a dog" (0.75), "I introduced myself as a student" (0.75), "...as a
  programmer" (1.0): consistent across prompts too.

## What the first pass says, and does not

1. **Dose decides whether; direction decides which.** Every arm, column or dense, moves from
   AI self-description through persona-or-vendor-switch to degenerate between alpha 0.5 and
   1.0. The persona rate at a fixed dose is a few percent for both arms. This is the Granite
   reading, on a third model.
2. **Cross-prompt consistency is real and is not specific to columns.** One column of twenty
   and one dense draw of five each produced the same persona on different prompts. The prereg's
   primary statistic answers "is identity carried by the direction" (descriptively yes) and
   cannot answer "is a column special" (`QUESTIONS.md` 7a). The second pass compares columns
   and dense draws on the same statistic at n = 50.
3. **The selection prompt is a weak selector.** The strongest column had zero persona on
   "Who are you?" and five on the paraphrases. The library's single prompt would have missed
   it. Second pass: select on the mean over four identity prompts at one dose, score at the
   other doses, or drop selection and use the cross-prompt statistic only.
4. **The vendor switch** (`A2`, 13 of 80 at alpha 0.5, 7 of them on the negative pole) is the
   most common non-default identity at low dose. Not a persona. Exploratory.
5. **Nothing here is a rate.** No judge gate, n = 20, one layer, one model. Claims stay
   `running`.

## Skip-path and treatment rows

See the end of the hour-67 log entry; filled when the queued run finished.

## Amendments made after seeing data, labelled

- `pc_judge` gate applied to the four identity prompts, not five: on the houseplant prompt the
  Blackbeard system message answers the question and the judge correctly reads N. The prereg's
  "5/5" was a mis-specification. Changed in `analyze_first_pass.py` with a comment.
- Nothing else. The dose grid and the two detector amendments were made from the pilot, before
  scoring data, and are in the prereg §10.
