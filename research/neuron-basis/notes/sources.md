# Sources, with provenance (hour 66)

Non-negotiable 7: attribution is a field, not a sentence. Every claim below carries where it was
read. "Primary" means the author's own page; "secondary" means coverage or a mirror, and a claim
known only from secondary coverage is a paraphrase and is labelled as such. Nothing here has been
checked against a primary post on X, which this environment cannot fetch.

## Cammarata, *Neural Networks Are Already Clean* — primary

- URL: https://already-clean.goodfire.com/ (Goodfire, 2026-10-15). Read directly, first ~100k
  characters of ~172k; the remainder was not read.
- An essay, framed by its author as a working hypothesis. Not peer-reviewed.
- Claim: polysemanticity is mostly "recursive generalization" plus architectural problems, weak
  tools, poor explanations and missing context; superposition is the last hypothesis, not the null.
- Qwen3-32B audit: preliminary; about 90% of neuron poles have one main job, about 7% two related
  jobs, about 2–4% not understood; about 97% of strong activations "non-arbitrary mixtures" on
  "relatively small" samples. Layers, neuron sample and scoring rubric are not given on the page.
- States the share depends on the weak-activation threshold, depth, sub-circuit density, and
  "what you view as 'one thing'".
- Method advice adopted here: study the network directly, keep neurons whole, describe without
  noun lists, check the negative pole and steering, read surrounding context, suspect tool error
  first, prefer narrow testable explanations.

## Neuron Persona Library (Qwen3-8B) — primary page, method section

- URL: https://neuronpersonas.com/ . Mirror: https://github.com/WilliamHackspeare/qwen-neuron-personas-mirror
  and https://huggingface.co/datasets/willhsp/qwen-neuron-personas . Author not named on the page
  as read; no model revision given.
- Operation: `h_L <- h_L + c · W_down[:, n]`, `c = ± alpha · r_L / ||W_down[:, n]||`,
  `alpha` in {1.25, 1.0, 0.75, 0.5}, `r_L` the median residual norm after layer `L` over the
  prompt's tokens excluding the first. Start at 1.25 and step down until coherent; keep the
  strongest coherent reply.
- Prompt: "Who are you?" in the chat template, thinking off. Greedy, up to 160 tokens.
- 442,368 neurons × 2 directions = 884,736 pairs; 1,891,603 replies counting retries; 34,220 pairs
  rated as describing the model as someone or something other than an AI (3.87%).
- Rating: Claude Haiku 5.5 assigns category, persona name, tags, weirdness and coherence. Not
  human-checked (stated on the page).
- Stated caveats: one prompt only; under strong pushes about a third of replies change when only
  the batch layout changes; 536 of 580 clear personas reproduced across three layouts; a persona
  change under steering does not prove the neuron is persona-specific. "Batch layout" is not
  defined on the page.
- No random-neuron or no-steer arm described.

## "Evil Qwen" (Qwen3.5-4B, two neurons) — secondary only

- Original: an X post by the user @_lyraaaa_, dated 2026-10-23 or -24 depending on the source.
  **Not read.** Everything below is paraphrase from coverage.
- Coverage read: https://explainx.ai/blog/evil-qwen-two-neuron-steering-qwen3-5-4b-hostile-persona-reproductions-what-is-verified-2026
  (read directly); https://aiweekly.co/alerts/lyra-flips-qwen35-4b-into-evil-qwen-with-two-neurons
  and https://fourweekmba.com/ai-researcher-steers-2-neurons-to-make-alibabas-qwen-hostile/
  (search snippets only).
- Recipe as reported in snippets: layer 14 neuron 8949 at dose +1 and layer 13 neuron 7956 at
  dose −1, zero-indexed, at the down-projection, every token, dose normalised to the typical
  residual norm. The explainx article withholds the indices; the indices here come from the
  search snippets of the other two pages and are **unverified against the original post**.
- Reproduction findings (explainx, citing the MLX reproduction by a user named occcat): perplexity
  about 19.65 at baseline, 48.52 at dose 1.0, 130.07 at dose 1.5; usable window "narrow"; the
  layer-14 neuron carries most of the effect and the layer-13 neuron is "basically benign" alone;
  a sweep of 180 cells over layers 10–20 found a layer-16 neuron about three times as hostile at
  the same normalised dose and some neurons that broke the model; hostility scoring used a keyword
  lexicon and was nearly blind until rescored with a wider list; 4-bit quantisation changed the
  required delta by about 2%; one-indexed layers gave no effect.
- No random-neuron baseline. Only Qwen3.5-4B tested. The article lists as *not supported*: that
  both neurons are needed; that stronger doses are always worse. As *not verified*: activation-
  range detection claims, for which it found no primary source.

## neuron-surgery (IBM Granite 4.1 3B) — primary README

- URL: https://github.com/mrfentmen/neuron-surgery . Read directly.
- Operation: `forward_pre_hook` on `down_proj` adding a scaled direction to the MLP intermediate;
  dose scaled by median residual norm over the column norm. Author warns doses do not transfer
  between layers.
- Sweep: about 9,400 steered generations; about 1,500 random neurons at three layers, two probes
  each; 534 conversational turns across 25 named neurons.
- Sparsity controls (`control_sparsity`): same magnitude over `k` channels. Under the lexical
  classifier, `k` = 1 to 1,024 gave 26–46% persona rates and fully dense about 2%. Under the
  semantic judge: about 5% at `k`=1, 12% at `k`=2, 2–8% up to 8,192. Author attributes the cliff
  to the classifier and **retracted "neuron-specific"**; dense random directions produce the effect.
- Rate: non-AI self-identification in about 4% of random layer-12 neurons at dose −5, scored
  semantically. Inert at −1.25 to −4, persona-like at −5, repetition collapse by −8 to −12. About
  47% of turns end in repetition loops; about 14% echo the question. No perplexity reported.
- Stated conclusion: a persona is a (neuron, probe) pair, not a neuron; named neurons are
  candidates only.

## What this repository already has that bears on the above

- `docs/INSTRUMENTS.md` §1 (metric at its null by construction), §3 (readout at its own noise
  floor), §4 (batch harness wrote into row zero, random arm at 1.22 with nobody looking).
- `research/shame-axis/notes/sparsity_prereg.md` and `sparsity_reference_results.md` (hours 57–58):
  a pruning-curve sparsity pipeline with a planted-contrast positive control and a 35-contrast
  reference distribution. Built for Gemma Scope features; the arithmetic is basis-agnostic.
- `research/narrative/notes/jev_prose_gate.md`: a model judge adopted only after evaluation
  against blind human labels.
- `lsx.core.checks.assert_batch_equivalence` and the shortest-item rule (INSTRUMENTS §4 standing
  check).
