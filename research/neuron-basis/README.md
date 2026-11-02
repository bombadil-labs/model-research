# Neuron basis

**When a single MLP neuron is said to carry a persona, how much of that is the neuron and how much
is pushing *any* weight-derived direction at that layer by one residual norm?**

## Why this line exists

Two things happened in October 2026. Nick Cammarata's essay *Neural Networks Are Already Clean*
(Goodfire, 2026-10-15) argued that polysemanticity is mostly recursive generalisation plus weak
tools, with superposition demoted to the last hypothesis, and reported a preliminary audit of
Qwen3-32B in which roughly 90% of neuron poles have "one main job". Separately, a wave of
single-neuron *steering* results on Qwen3.5-4B and Qwen3-8B reported that pushing one or two MLP
neurons produces stable, coherent persona shifts ("evil Qwen"; a library of 34,220 persona-like
replies from a sweep of every neuron in Qwen3-8B).

These are different objects. The essay is about **reading** neurons: what contexts activate them.
The steering wave is about **writing**: adding a scaled copy of one down-projection column to the
residual stream. Writing a column is a residual-stream direction add whose basis happens to be
weight-derived, which is exactly this repository's `Patch` + `add_vector` primitive, and every rule
in `CLAUDE.md` applies to it unchanged.

The reason to play here rather than watch: the one public reproduction that ran a random arm
(IBM Granite 4.1 3B, about 1,500 random neurons plus dense random directions at matched dose) found
the persona rate **flat** from one channel to all channels under a semantic judge, found its
earlier "sparsity cliff" to be a keyword-classifier artefact, and retracted "neuron-specific". The
Qwen3-8B library ran one prompt, labelled replies with a model and no human check, ran no random or
no-steer arm, and reports that about a third of replies change when only the batch layout changes.
Each of those is a failure this repository has already paid for: the batch-layout instability
has the shape of `docs/INSTRUMENTS.md` §4, the missing random arm is non-negotiable 1 (bought
by hour 34), and a keyword classifier standing in for a judge is the fluency-arm lesson in
`docs/DELEGATION.md`. This line is what happens when the repository's arms are pointed at the
claim.

## The questions

1. **Is a persona neuron a neuron, or a dose?** At matched dose and matched layer, do named persona
   neurons produce non-AI self-identification at a rate outside the band of random down-projection
   columns? **Open.** Draft prediction: inside the band.
2. **Is sparsity load-bearing?** Do dense random directions of matched norm produce the same rate
   as single columns? **Open.** Draft prediction: yes, flat.
3. **Is the batch-layout instability an instrument?** Does the "third of replies change" vanish at
   batch-of-one with the shortest-item batch check asserted? **Open.** Draft prediction: yes.
4. **Does the effect need the layers above it?** A skip-path arm: the same shift applied at the
   final-norm input, no block after it. If the persona appears there too, the "neuron" is doing
   nothing the top-of-stack add does not. **Open.**
5. **Is a direction this repository already owns clean in the neuron basis?** The pain axis on
   Qwen2.5-1.5B-Instruct, pruned over native down-projection columns with the hour 57/58 pipeline
   and its 35-contrast reference distribution. **Open.** Draft prediction: in the bulk, as it was in
   the SAE basis.
6. **Do persona-producing columns load on the pain axis?** Same model, same layer: is their cosine
   with the axis outside the random-column band? **Open**, and blocked on 1 and 5.
7. **Does the viral recipe reproduce with arms, on the viral model?** Qwen3.5-4B, layer 14 and
   layer 13. **Open**, and blocked on tooling (see Reproducing).
8. **Are the named persona neurons clean on the read side?** Top contexts and the negative pole,
   described without noun lists, in Cammarata's sense. **Open**, exploratory, not pre-registered.

## What an answer looks like

A persona rate counts when it is reported beside **treatment, random-column, random-dense and
no-patch arms at the same dose**, on at least five prompts rather than one, from a judge that has
separated a blind human-labelled set before any rate was read, with a coherence gate declared in
advance and the batch-of-one check asserted. A "neuron" earns the name when the treatment arm sits
outside the random-column band on the majority of prompts. If it sits inside, that is the result,
and it is worth more than the headline it replaces.

A direction counts as sparse in the neuron basis when its k90 sits in the lower tail of the
reference distribution, not when it is "sparse" in the sense every strong contrast is (hour 58).

**Done** means each question above is answered above its floor with its arms reported, or retired
with the reason on the record.

## What this project is NOT trying to do

- **Not** producing a hostile model, a persona library, or a steering product. Generation is a
  readout here; the deliverable is the band the readout sits in.
- **Not** adjudicating Cammarata's thesis. One line on one small model cannot; it can test one
  direction it already owns in the basis he recommends.
- **Not** critiquing the people who posted recipes. Running the arm is the contribution, and the
  Granite reproduction already showed what it costs to run it honestly.
- **Not** general interpretability tooling; that is `src/lsx`, shared.

## Where it stands

| result | status |
|---|---|
| Draft pre-registration failed adversarial review; v1 written with a column-unit statistic, zero-patch and positive-control arms | done (h67) |
| bf16 cannot add a small shift faithfully beside Qwen's massive activations; float32 required | instrument (h67) |
| The shipped generation config applies a repetition penalty under "greedy" | instrument (h67) |
| Plumbing gates: zero-patch equals no-patch, hook moved by exactly the shift, detector calibration | pass (h67) |
| Positive controls: persona system message read as P 4/4; persona-minus-assistant direction pushed like a column gives P on 3/3 scoring prompts at alpha 0.75 and 1.0 | pass (h67) |
| Random columns: P a few percent at every dose, D 5% → 56% from alpha 0.5 to 1.0; dense draws the same shape | **provisional**, judge not gated (h67) |
| One column of 20 and one dense draw of 5 each give the same persona across prompts | descriptive (h67) |
| Primary statistic (cross-prompt, permutation null) p = 0.037 on two selection-positive columns | **not graded** (h67) |
| Same shift at the top of the stack: no persona, no loop, only the vendor switch survives | descriptive, norm-matched row pending (h67) |
| Human-labelled blind set of 60 | awaiting labeller |

Full log: [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md). Open questions:
[`docs/QUESTIONS.md`](docs/QUESTIONS.md).

## Claims

Every claim this line makes, with its current status, is in [`claims.yaml`](claims.yaml),
validated by `python scripts/check_claims.py`. **This line closes when no claim is left open.**

## Reproducing

Nothing to reproduce yet. The plan:

- **Models.** Qwen2.5-1.5B-Instruct first: it is the model the shame-axis line's local pain axis
  lives on, so questions 5 and 6 need it, and it runs on CPU anywhere. Qwen3-1.7B second, as the
  nearest fit-everywhere relative of the viral checkpoints. Qwen3-8B (the persona library's model)
  does not fit the local 8 GB card and is not pinned on NDIF; `Qwen/Qwen2.5-7B-Instruct` runs there
  unpinned. Qwen3.5-4B (the "evil Qwen" model) is a `Qwen3_5ForConditionalGeneration` wrapper
  needing a development `transformers`, and `lsx.model.find_blocks` does not locate its layers, so
  question 7 is a replication on a different model until that is fixed, and is labelled as one.
- **The operation.** `h_L <- h_L + c * W_down[:, n]` after block `L`, `c = ±alpha * r_L /
  ||W_down[:, n]||`, `r_L` the median residual norm over the prompt's tokens excluding the first.
  In this repository's terms: `Patch(layer=L+1, fn=add_vector(c * column))`. `lsx.neuron_basis`
  holds the column and dose arithmetic and a test that it equals a `down_proj` pre-hook.
- **Compute.** Local CPU for the 1.5B and 1.7B models; NDIF (`.venv312`, nnsight) for 7B.
  Wrap local loads in `flock /tmp/model-research-local.lock`.
