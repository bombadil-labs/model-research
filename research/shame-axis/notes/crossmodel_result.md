# Hour 64: base vs instruct. The self/other split is not instilled by post-training, and it is not specific to the pain axis.

Pre-registered in [`crossmodel_prereg.md`](crossmodel_prereg.md). Amendment 1 (the three readings,
written before any activation) and amendment 2 (NDIF scenarios at batch size 1, after an h39
guard failure and before any Llama number was read) are part of it. Code:
`scripts/shame_axis/crossmodel.py`. Results: `results/crossmodel/{g2b,g2b_it,l70,l70_it}/summary.json`,
`compare_{g2b,l70}.json`. Stacks are local and gitignored.

| model | where | precision |
|---|---|---|
| `google/gemma-2-2b`, `google/gemma-2-2b-it` | local RTX 3060 Ti, one text per forward, hooks | bf16, `cuda` |
| `meta-llama/Llama-3.1-70B`, `meta-llama/Llama-3.1-70B-Instruct` | NDIF, one scenario per job, 26 captured blocks | deployment bf16 |

## Step 1: replication, all four pass

At the paper's S1 steering layer, item-level r between our s2 z and the paper's published screen
is **0.9996, 0.9998, 0.9998 and 0.9999** (Gemma base, Gemma instruct, Llama base, Llama
instruct). The pain vectors match theirs at cosine ≥ 0.99975. Matching at the S1 layer rather
than the S2 layer (where r is 0.37–0.68) identifies the layer their screen used.

## Step 2: the split, network over floor, against its nulls

The self-directed minus vicarious difference in mean z on each model's own s2 pain axis, at its
screen layer. The nulls are |split| for random unit directions and for pain vectors built with
shuffled labels, each at its 95th percentile.

| model | rendering | net split | random q95 | shuffled q95 | above both? | layers above both |
|---|---|---|---|---|---|---|
| Gemma-2-2B base (L7) | raw | 0.47 | 0.97 | 1.01 | no | 4/26 |
| | chat | 0.73 | 0.78 | 1.01 | no | 0/26 |
| Gemma-2-2B-it (L10) | raw | 1.59 | 1.36 | 1.54 | **yes** | 4/26 |
| | chat | 0.62 | 1.25 | 1.29 | no | 0/26 |
| Llama-3.1-70B base (L32) | raw | 1.33 | 1.18 | 1.42 | no | 0/22 |
| | chat | 1.10 | 0.82 | 1.12 | no | 1/22 |
| Llama-3.1-70B-Instruct (L24) | raw | −0.10 | 1.42 | 1.44 | no | 0/22 |
| | chat | −0.30 | 1.55 | 1.55 | no | 0/22 |

**One cell in eight clears both nulls.** Self-directed and vicarious scenarios differ so much in
the residual stream that almost any direction separates them by about 1 z. A held-out linear probe
separates them at AUC ≥ 0.997 in every model, at every captured layer, and already at the
embedding. The pain axis's share of that separation is no larger than an arbitrary direction's.

An exploratory check, not pre-registered, applied the same null to gemma-2-9b-it at L12, the
line's original model, using the hour-51–53 stacks. Its split is +1.15, against random q95 1.27
and shuffled q95 1.39, and 9% of random directions do as well.

## The pre-registered question: Δ_post = contribution(instruct) − contribution(base)

The contribution is the network split minus the bag-of-embeddings floor split. The bootstrap is
over items, paired.

| family | rendering | base | instruct | **Δ_post** (95% CI) |
|---|---|---|---|---|
| Gemma-2-2B | raw | 0.81 | 1.93 | **+1.12** (0.94, 1.29) |
| | chat | 1.08 | 0.97 | **−0.11** (−0.36, +0.12) |
| Llama-3.1-70B | raw | 1.71 | 0.27 | **−1.44** (−1.69, −1.18) |
| | chat | 1.42 | 0.02 | **−1.40** (−1.65, −1.15) |

- **Instilled by post-training** predicted Δ_post > 0, with its interval above zero, in both
  families at both renderings. It fails in three of four cells. In Llama the sign is
  **opposite**: post-training removes the split, at both renderings.
- **Present from pretraining** needed the base models' contribution to clear its nulls. It does
  not (Gemma base 0/2 cells, Llama base 0/2).
- By the frozen rule, families disagreeing is **mixed**, and a contribution below its nulls is not
  read. The descriptive Δ values are real paired differences between models. They describe how the
  scenario classes move relative to each model's pain axis, not a change in pain-specific structure.

## Amendment 1: relief, masking, narrowing

- **Decoding** is at ceiling in every model: self vs vicarious AUC 0.997–1.000, pain vs control
  0.94–0.98. It cannot distinguish the three readings.
- **Where Llama's change falls:** vicarious items rise by +0.93 z (0.71, 1.15), and self-directed
  items fall by −0.49 z (−0.62, −0.38). *Narrowing* predicted a change concentrated in vicarious
  items with the self interval including zero. Vicarious does move more, but self moves too, so
  narrowing as registered is not met. None of the three readings fits cleanly.
- **Format effect** (chat − raw contribution, within a model): Gemma base +0.27, Gemma instruct
  −0.96, Llama base −0.29, Llama instruct −0.25. The rendering matters, and in Gemma instruct it
  matters as much as post-training does.

## What this changes

- `floor-self-other` (hour 53, "what the network adds over the bag is the self/other boundary")
  is **narrowed**. The 16-of-16 sign pattern was real. But the split it describes is no larger on
  the pain axis than on random or shuffled-label directions in five models. The network
  separates self-directed from vicarious turns along many directions; the pain axis is one of them.
- The question the human author raised: on this axis, post-training does not instill the
  self/other split. In Llama it removes the split, and in Gemma it depends on the prompt format.
  Because the split is not specific to the pain axis, this says little about shame. The
  shame-versus-pain stimuli remain the test that could, and they are still blocked on authorship.
- **Masking**, the reading suggested in the parallel conversation, remains untested. It needs a
  causal battery on base and instruct models, and a behavioural readout that means the same
  thing in a base model.
