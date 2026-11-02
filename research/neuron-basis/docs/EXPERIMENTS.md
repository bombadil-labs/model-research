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
proxy; see the hour's smoke result below. The persona library's model (Qwen3-8B) is not on NDIF
and does not fit the local card; the viral model (Qwen3.5-4B) needs a development `transformers`
and a `find_blocks` path for its `Qwen3_5ForConditionalGeneration` wrapper. Starting model is
Qwen2.5-1.5B-Instruct, because questions 5 and 6 need the shame-axis line's local pain axis.

**Draft pre-registration** for questions 1–4 in `notes/persona_arms_prereg_DRAFT.md`. It is a
draft: predictions and kill conditions are written, but the claims stay `pre_registered: false`
until the draft has been through adversarial review and committed as final. A prediction written
after review is still before the data, which is what the field requires.

**Cost.** One session, no model loaded, no NDIF compute beyond a smoke trace.
