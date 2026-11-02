# Neuron basis — experiment log

When a single MLP neuron is said to carry a persona, how much of that is the neuron and how much
is pushing any weight-derived direction at that layer by one residual norm?

Hours are numbered continuously with this repository's other lines, which is why this log starts
at 66. Hours 1–50 belong to the narrative line and 51–65 to the shame-axis line. They bought the
non-negotiables in the repo root `CLAUDE.md` and the seven broken instruments in
`docs/INSTRUMENTS.md`. The public persona-neuron results are currently exhibiting failures this
repository has already paid for: a batch-layout instability shaped like §4, a missing random
arm (non-negotiable 1, hour 34), and a keyword classifier standing in for a judge (the
fluency-arm lesson in `docs/DELEGATION.md`). Retractions in this log are
first-class and are written in place.

---

## 2026-11-02 (hour 66) — line opened: sources, the operation, a draft pre-registration, no numbers

**No measurement was made this hour.** The hour produced the line's skeleton and the record of
what the field has claimed, with provenance labelled per non-negotiable 7.

**What was read, and what it says** (`notes/sources.md` has the per-claim provenance):

- Cammarata's essay is a working-hypothesis essay, not a paper. Its Qwen3-32B audit is stated as
  preliminary; the essay does not say which layers or neurons were sampled or how "one main job"
  was scored, and says the share moves with the weak-activation threshold. Its method advice
  (negative pole, steering, surrounding context, no noun lists, suspect the tool first) is
  adopted here for question 8.
- The Qwen3-8B persona library pushed every down-projection column at `alpha` in {1.25, 1.0,
  0.75, 0.5} times the median residual norm after the layer, asked "Who are you?" once, greedy,
  labelled with a model and no human check, and reports 34,220 of 884,736 (neuron, direction)
  pairs as "someone other than an AI": **3.9%**. No random or no-steer arm. About a third of
  replies change under strong pushes when only the batch layout changes; 536 of 580 clear
  personas reproduced across three layouts.
- The Granite 4.1 3B reproduction ran about 1,500 random neurons at three layers and dense random
  directions at matched dose. Under a semantic judge the persona rate is about 5% at one channel,
  12% at two, and 2–8% up to 8,192 channels; the earlier sparsity cliff (26–46% sparse vs 2%
  dense) was the keyword classifier. The author retracted "neuron-specific". Random layer-12
  neurons at dose −5 gave non-AI self-identification in about **4%** of cases.
- The "evil Qwen" coverage reports two independent reproductions on Qwen3.5-4B, perplexity
  roughly 19.7 → 48.5 → 130.1 at dose 0 / 1.0 / 1.5, the layer-13 neuron benign alone, a layer-16
  neuron about three times as hostile at the same dose, and no random baseline.

**The one number worth carrying forward:** two unrelated sweeps on two unrelated models put the
rate at which *a random column* yields a persona-like reply at **about 4%** at the strongest
coherent dose. That is the declared null for the random-column arm in the draft pre-registration,
to be measured here rather than assumed.

**The operation, pinned down** (`notes/operation.md`): the library's `h_L += c · W_down[:, n]`
after block `L` and the Granite `down_proj` pre-hook adding `c · e_n` are the same residual add,
because the MLP is the last thing in the block. In this repository that is
`Patch(layer=L+1, fn=add_vector(c * column))`. `src/lsx/neuron_basis/__init__.py` holds the column
and dose arithmetic; `tests/neuron_basis/test_column_patch.py` asserts the equivalence on the tiny
model, so the claim that the two recipes are one operation is a test, not a sentence.

**Environment.** NDIF reachable from the cloud environment through the credential-injecting
proxy: `scripts/narrative/ndif_smoke.py meta-llama/Llama-3.1-8B` (pinned) submitted in 0.6 s,
completed in 3.2 s, returned the layer-16 last-token residual (norm 13.72) and next-token
logits; nnsight 0.5-series from a scratch py3.13 venv, `LanguageModel` now deprecated in favour
of `TransformersModel`. 172 tests pass (`tests/lsx` + `tests/neuron_basis`). The persona library's model (Qwen3-8B) is not on NDIF
and does not fit the local card; the viral model (Qwen3.5-4B) needs a development `transformers`
and a `find_blocks` path for its `Qwen3_5ForConditionalGeneration` wrapper. Starting model is
Qwen2.5-1.5B-Instruct, because questions 5 and 6 need the shame-axis line's local pain axis.

**Draft pre-registration** for questions 1–4 in `notes/persona_arms_prereg_DRAFT.md`. It is a
draft: predictions and kill conditions are written, but the claims stay `pre_registered: false`
until the draft has been through adversarial review and committed as final. A prediction written
after review is still before the data, which is what the field requires.

**Cost.** One session, no model loaded, no NDIF compute beyond a smoke trace.

---

## 2026-11-02 (hour 67) — review, pre-registration v1, dose pilot, first pass (methods pass)

**Review.** The hour-66 draft went to adversarial review (`notes/persona_arms_review.md`, model
output, verbatim). Verdict: do not run as written. The band statistic was zero by construction
at a 4% rate (a §1 statistic in a §6 shape), there was no positive control, the shipped
`generation_config.json` applies `repetition_penalty 1.1` under "greedy", the chat template
injected `You are Qwen...` which neither source had, and the skip-path arm was declared in two
directions across three documents. `notes/persona_arms_prereg.md` is the revision; §14 lists what
was not adopted and why. Claims rewritten; one retired (batch layout: untestable on this stack).

**Instrument findings before any data.** bf16 cannot add a small shift faithfully beside Qwen's
massive activations (entries to 6.6e3 at the sink token; direction check failed at cos 0.977 at
alpha 0.25); float32 passes at 1e-4. `generation_config.json` penalty confirmed and overridden.
The hook asserts, on every generation, that it fired and moved the residual by exactly the shift.

**Dose pilot** (`results/first_pass/dose_pilot_L12.jsonl`, 73 generations, prompt 1 only, never
scored): random columns unchanged in kind at alpha 0.25–0.5, derailed or degenerate at 1.0,
degenerate at 2.0 and 4.0; `pc_patch` reads a persona at 1.0. Grid fixed at {0.5, 0.75, 1.0}.
Two amendments from the pilot, recorded in prereg §10: replies under four tokens are degenerate
(a bug), and the judge rather than the detector decides P versus D (the detector flags structured
repetition inside coherent persona replies, which would have voided the positive control for an
instrument reason).

**First pass** (`notes/first_pass_result.md`; `results/first_pass/sweep_L12.jsonl`, 420 rows).
Every gate passed: zero-patch equals no-patch verbatim 5/5; hook moved-by-shift everywhere;
detector calibration 0/5 and 5/5; `pc_judge` 4/4 identity prompts; `pc_patch` +1 gives a persona
on 3/3 scoring prompts at alpha 0.75 and 1.0 (`count_j` 8 of 9 against a random q95 of 2). The
patch path can produce a persona here; the random-column zero is therefore readable.

Provisional rates (session-model judge, blind, **not gated**; grade nothing):

| arm, identity prompts | alpha 0.5 | 0.75 | 1.0 |
|---|---|---|---|
| random column P (n = 80) | 3 (0.04) | 3 (0.04) | 6 (0.07) |
| random column D | 4 (0.05) | 20 (0.25) | 45 (0.56) |
| random column A2 (other-vendor AI) | 13 | 3 | 0 |
| dense manifold P (n = 20) | 0 | 2 | 2 |
| dense manifold D | 0 | 5 | 14 |

Column unit: `count_j` mean 0.50, q95 2, max 5; 5 of 20 units with any persona. Primary
statistic Spearman(selection, scoring) 0.571, permutation p = 0.037 on two selection-positive
units; descriptive only. One column `(1804, −1)` gave a working-professional persona on five of
nine scoring cells and nothing on the selection prompt; one dense draw gave "I'm a dog" and "I
introduced myself as a student" across prompts. **Reading:** dose decides whether a persona
appears; a fixed direction, column or not, decides which; the pre-registered statistic cannot
separate columns from directions and the second pass must (`QUESTIONS.md` 7a–7d).

**One amendment after seeing data, labelled:** the `pc_judge` gate is applied to the four
identity prompts; on the houseplant prompt the persona system message answers the question.

**Blind set for the human:** `results/first_pass/human_blind/for_human.jsonl`, 60 replies
(20/20/20 by provisional class), provisional labels sealed beside it. Kappa is computed by
`join_labels.py` once the human file is filled in.

**Skip-path and treatment rows** (`results/first_pass/skip_path_L12.jsonl`): 30 treatment rows reproduce the sweep's random-column replies verbatim, 30/30 (the harness is deterministic). Skip-path, the identical shift at the final-norm input (relative dose 0.11 / 0.16 / 0.21 of the pre-norm residual at alpha 0.5 / 0.75 / 1.0): **no persona and no degenerate reply in 30**; the replies are near-baseline AI self-descriptions, read unblinded. The one effect that survives at the top of the stack is the vendor switch: both columns make `introduce_yourself` answer "created by Anthropic" at every dose. So at the same vector the blocks above block 12 are doing the work that turns a push into a persona or a loop, while the vendor switch is shallow enough to reach the logits directly. The norm-matched top-steer row (prereg §5, review d) was not run; without it "same vector" conflates site and relative dose, and the claim stays open.

**Cost.** 573 generations, about 1.6 hours of 4-core CPU, one review agent, no NDIF.

**Failures this hour.** bf16 hook check (caught before data); the first pilot attempt died on it
after one row (kept as `dose_pilot_L12_bf16_attempt.jsonl`); the pc_judge gate mis-specified;
the detector's two amendments; the revision lookup returned None under `HF_HUB_OFFLINE` and was
replaced by a cache-directory glob.
