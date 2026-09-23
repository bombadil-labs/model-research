# Late reveal keeps much of the route signal, but the registered screen misses one quadrant

The [frozen three-format test](reveal_order_prereg.md) moved the same neutral
interlude around the two route-fact hops in eight constructed stories. The
three orders were chronological (`FH SH I C`), late reveal (`FH I SH C`),
and near adjacent (`I FH SH C`). The goal, plans, two-hop graph, complete
word bag, prompt length and final 200 characters were held fixed within
each matched set. Four independent direct-route controls and separate
repeat jobs tested the scorer. The amended third order was frozen before
any score, after peer review identified the opposing separation and
recency changes in a two-order comparison.

Model: NDIF's pinned `google/gemma-2-9b-it`, local tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF does not expose a
weight revision hash. The [committed report](../results/reveal_order_v1_summary.json)
contains every quartet margin, format-specific null, domain bootstrap,
factor half, quadrant, token-length audit, control and repeat.

## Result against the frozen decision

A quartet succeeds when *both* goal-conditioned world contrasts move
toward the route's actual destination by more than 0.25 nat. A stricter
measure also requires the correct name to win in all four world×goal
cells by at least 0.1 nat. The first measures **sensitivity to the facts**;
the second measures **correct absolute choices**.

| Telling | Successful two-contrast quartets | Strictly correct four-cell choices | Exact domain-orientation p | Domain-bootstrap 95% interval |
| --- | ---: | ---: | ---: | ---: |
| Chronological | 28/32 | 24/32 | 2/256 | 0.750–0.969 |
| Late reveal | 30/32 | 16/32 | 1/256 | 0.844–1.000 |
| Near adjacent | 28/32 | 19/32 | 2/256 | 0.688–1.000 |
| **Same quartet, all three** | **27/32** | — | **1/256** | **0.688–0.969** |

The paired late-minus-chronological and late-minus-near-adjacent
differences are each +0.0625, with domain-bootstrap intervals
0 to +0.1563. Both lower bounds exceed the frozen −0.15
non-inferiority margin. Near-adjacent minus chronological is 0, with
interval −0.0938 to +0.0938. The paired sign-flip null has mean 0.422,
95th percentile 0.656, and p=1/256, the floor of this eight-domain exact
test.

**The registered overall screen fails.** The near-adjacent telling's
`00` first-hop×second-hop fact-order quadrant scores **4/8 = 0.50**;
the preregistration required *every* quadrant in *every* format to
exceed 0.50. That `00` quadrant is the weakest in **all three** tellings:
5/8 chronological, 6/8 late, 4/8 near adjacent. Its two domains are
clinic and library, each 2/4 in the near-adjacent telling. The grid has
only two domains in this quadrant, so domain identity and fact order
cannot be separated here. Descriptively, all four near-adjacent misses
are the plan-order-1 cells in those two domains, across both name
assignments; plan-order 0 passes 16/16. That pattern does not isolate a
cause, but it locates the sensitivity more precisely. All other
near-adjacent quadrants are 8/8.
Chronological and late reveal pass their four quadrant gates and all
other format-specific gates. Five of the eight domains pass all four
quartets in all three tellings; clinic and library pass only two each,
and ship passes three.
The all-format paired test and both non-inferiority tests pass, but they
do not override the failed eligibility gate.

The lower strict-choice count in late reveal matters separately. Its
30/32 signed quartets show that the destination swap changes relative
name preference in the right direction, while only 16/32 quartets give
the correct name in **all** four cells. Thus a high paired shift rate
does not mean the model always names the right worker under each
counterfactual.

An exploratory decomposition of the committed cell margins locates one
part of this gap. Averaging each quartet's four raw plan-A-minus-plan-B
margins over the two worlds and goals gives a plan-A offset. Its mean is
−0.095 nat in chronological order, **+0.849** in late reveal, and −0.047
in near-adjacent order. In late reveal, plan A wins when it is correct in
57/64 cells, while plan B wins when it is correct in only 44/64. The
world×goal interaction still moves in the right direction on most
quartets. This post-result audit identifies an option offset; it does not
identify whether its cause is route wording, position, or some other
feature of the telling, and it is not a registered gate.

## Measurement and reading

The four direct-route controls pass all **16/16** matched quartets in
all three formats. Every control format passes its 12/16 and name/order
half gates. The 24 separate story repeats have maximum absolute margin
drift **0**. The measured full-text and final-200-character word-bag
world interactions are **0** across 144 quartets. Story token lengths
range from 228 to 238 and have the same distribution in the three
tellings; each two-candidate score ran as one verified fp32-softcapped
job. The failed near-adjacent quadrant is therefore a model/readout
result on this grid, not a repeatability or surface-count failure.

The registered all-gates claim is **falsified** by the near-adjacent
quadrant. Its registered paired component still shows goal-and-route
sensitive margin changes in 27/32 matched quartets across all three
tellings. The late format is non-inferior by the frozen margin; its
+0.0625 point differences have intervals touching zero, so they do not
establish superiority. Its strict-choice count is the lowest of the
three. The near-adjacent comparison holds second-hop recency fixed but
also moves the plan-to-first-hop gap, as the preregistration states. These
orders do not identify a stable latent story shape or a causal
representation. They do give a concrete boundary for the next test:
absolute name choice and the clinic/library `00` cases need to improve
without selecting a new format or gate from these outcomes.
