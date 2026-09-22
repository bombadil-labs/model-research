# Controlled role-swap spike: a context signal with a large order confound

## Question and material

Can the final-token activation reflect a prior actor-goal assignment across unrelated
miniature stories when the final handover sentence, its last 200 characters, and the paired
word bag are identical? The [registered design](role_swap_prereg.md) froze 12 domains with
distinct names, goals and objects, two role-sentence orders, and two actor assignments per
order: 48 passages and 24 matched pairs. The context cue occurs more than 200 characters
before the final-period readout. Longest input is 100 tokens. The held-out unit is a domain,
including both its sentence orders. All paired final token IDs and positions matched.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`. Local CUDA float16 on an RTX 3060 Ti.
The exact grid, script, model and activation digests plus library versions are in the
ignored local provenance files; the committed [summary](../results/role_swap_summary.json)
contains the derived scores and these model identifiers. A 200-character local-only input
and layer 0 produced bit-identical states within every matched pair.

## Registered score

For each pair, subtract the `harms` state from the `helps` state, unit-normalize, and fit a
direction on both orders of the other 11 domains. A positive cosine on a held-out pair is
one hit, a negative cosine is a miss, and an exact zero gets 0.5. The fixed layers were
10–18; inference and bootstrap resample domains, not the 216 pair-by-layer outcomes.

| Measurement | Result |
| --- | ---: |
| Mean pair accuracy, layers 10–18 | **0.792** |
| 95% domain bootstrap interval | 0.731–0.847 |
| Domain-label permutation, 1,000 draws | mean 0.506; p = 0.001 |
| Random direction, 1,000 draws | mean 0.500; 95% span 0.440–0.560 |
| Local 200-character input | 0.500, exact tie |
| Layer 0 | 0.500, exact tie |
| Fixed layer 14 | 0.875 |

The result clears every registered positive-screen threshold. The complete layer curve
is in the summary. Its apparent improvement near the final layers was observed after
extraction and is exploratory. It does not license choosing a better layer retroactively.

## Diagnostic after the registered result

The paired direction is dominated by sentence order. At layer 14, within-domain deltas
from the two orders have mean cosine **−0.740**. Fitting on one order of 11 domains and
testing the same order of the twelfth gives 1.000 mean accuracy over layers 10–18;
testing the opposite order gives 0.000. The registered score averages both orders in
training, canceling much of this component, but the raw delta is not an order-invariant
plot-role vector.

After this audit, and **before its extraction**, we froze a [neutral control](role_swap_neutral_prereg.md)
with the same names, handovers, actor swaps, sentence orders, and local text. Its two
earlier activities are counting stones and watching clouds. The `helps`/`harms` names
in this control are bookkeeping labels with no moral or plot meaning.

| Mean pair accuracy, layers 10–18 | Value |
| --- | ---: |
| Original goal-grid direction on goal-grid holdouts | 0.792 |
| Original goal-grid direction on neutral holdouts | **0.583** |
| Neutral-grid direction on goal-grid holdouts | 0.500 |
| Neutral-grid direction on neutral holdouts | **1.000** |
| Original minus cross-grid, paired domain bootstrap | **0.208** [0.097, 0.315] |

The cross-grid 0.583 is below the diagnostic's 0.60 flag, but is above an orientation-
permutation null (p = 0.025; 1,000 draws); its domain bootstrap interval is 0.519–0.653.
That is a small residual structural transfer. The neutral grid's 1.000 self-score proves
that the original registered score alone could be produced by an arbitrary, consistently
named predicate association. The two scores must be read together.

The order diagnostic is still more pointed: when trained and tested on the same order,
the goal direction transfers to the neutral grid at **0.995**; on reversed order it scores
**0.005**. So the nearly perfect raw cross-domain alignment is largely a reusable
name/predicate/order pattern. Balancing orders exposes a smaller difference between the
goal and neutral grids, but does not identify a pure narrative-role component. The neutral
grid itself has order cosine −0.550 at layer 14 and scores 1.000 on same order, 0.009 on
reversed order. The full curves and diagnostic scores are in the summary.

## Finding and next discriminator

The model carries information from earlier actor descriptions to the identical final
token, and an order-balanced direction distinguishes the goal-bearing passages from this
particular neutral control by 0.208 pair-accuracy points. The large order component and
the neutral grid's perfect self-score show how readily this instrument learns predicate
binding rather than a narrative shape. These are constructed miniatures, not evidence of
a Hero's Journey geometry, natural-story transfer, or a causal transformation operator.

The next discriminating measurement should change the *final action* while keeping the
prior goal assignments fixed, and compare final-action versus pre-action readouts. A
claim about the handover's role requires an interaction between prior goals and the
action. If the direction is already present before the action and does not change with
the action, it is actor-goal binding, not a representation of that plot event.
