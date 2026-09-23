# A shared choice-slot interaction appears late in the route stories

## Question and scope

The [pre-registered pilot](goal_route_activation_pilot_prereg.md) followed the
positive [goal × route behavioral screen](goal_route_cross_result.md). It asked
whether the residual stream carries a **shared direction** for the factorial
goal × route contrast across eight held-out story domains and early/late
tellings. This is a readout of the final prompt token immediately before the
worker-name answer, with no activation patching or causal test.

The fixed contrast was `I_A = h(0,0) − h(0,1) − h(1,0) + h(1,1)`. Because the
plan-A owner has no common name or position, the primary `I_first` multiplies
this vector by −1 when plan A is listed second. Each held-out domain was
scored against a direction fitted on the other seven domains in the
**opposite telling**. Blocks 16 and 24 were averaged for the registered
decision; all six captured blocks are reported.

Model: NDIF's pinned `google/gemma-2-9b-it` deployment, local tokenizer
snapshot `11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF exposes no
weight revision hash. The [summary](../results/goal_route_activation_pilot_summary.json)
contains model and library metadata, grid and code digests, per-domain and
per-telling values, the full curve, nulls and measurement checks. The 256
story vectors and eight separate-job repeats remain in ignored
`cache/goal_route_cross/activation_v1/states`.

## Registered outcome

| Measurement | Observed | Registered gate |
| --- | ---: | --- |
| Fixed block-16/24 held-out mean cosine | **+0.0854** | Positive |
| Exact eight-domain orientation null | **p = 2/256 = 0.0078**; null 95th percentile +0.0687 | p ≤ 0.05 |
| Domain-bootstrap 95% interval | **+0.0660 to +0.1094** | Lower > 0 |
| Positive held-out domains, early / late target | **8/8 / 8/8** | At least 6/8 each |
| Identical-prompt repeat drift | **0** at every block; no unresolved interaction | At most 1% and all primary interactions resolved |
| Established-core equivalence, blocks 16 / 24 | Cosine ≥0.9999999, relative L2 error 0 | Cosine ≥0.999, error ≤0.01 |

All registered gates pass. The exact p value is the **floor** for this
eight-domain statistic: globally reversing every domain leaves the fitted
and held-out directions reversed together, giving the same score. The
domain-bootstrap interval is a descriptive uncertainty estimate over these
eight constructed domains; it does not imply broad story generalization.

| Block index | 0 | 8 | 16 | 24 | 32 | 40 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Held-out cosine | +0.0224 | −0.0219 | −0.0002 | **+0.1710** | +0.1599 | +0.1534 |

The registered mean is driven by block 24; block 16 shows no transfer. The
later blocks also show positive descriptive transfer. The raw A-oriented
version, which does not orient by plan order, had primary mean +0.0477;
its exploratory exact null gives p = 0.203. Thus the raw check is not
convincing evidence of a common A-owner code, although its nonzero point
estimate calls for replication rather than assuming exact cancellation.
One plausible grid source is the link vocabulary: link 0 is the upper,
ridge, high, north or forward route in five domains. This could give A a
shared lexical or spatial meaning. Raw transfer is already +0.159 at block
0 and +0.206 at block 32, despite the nonsignificant registered block-16/24
mean. The primary plan-order sign cancels a stable A-code, but a future grid
should counterbalance which link occupies A across domains.
Full-text and last-200-character word-bag interactions were measured as
exact zero. The five domains with equal goal token lengths had mean +0.0690;
the three with a one-token goal-length difference had mean +0.1127.
The effect is present in the length-matched subset, but that split is small
and was registered only as a descriptive position audit.

## Analysis correction

The first report printed exact p = 0.0, an impossible value because its
enumeration includes the unflipped assignment. The observed score and each
null score used mathematically equivalent reductions in different axis
orders; their floating-point difference placed the two maximum null scores
one representable step below the observed score. After extraction completed,
the analysis was corrected to use the same reduction for both. A regression
test covers inclusion of the unflipped assignment. The reanalysis script
validated all 264 cached rows against their original prompt fingerprints,
recomputed the report without another model forward, and preserved the
original extraction digest alongside the corrected analysis digest and the
original report hash. The only registered decision change is p = 0.0078
instead of the invalid zero; the pilot passes either way. The original
ignored report remains available for audit.

## What follows

This pilot supports a **candidate shared choice-slot code** for these
explicit route miniatures at a late residual location. It does not show
that the direction causes the choice, represents a reusable two-link graph
operation, isolates a plot component, or survives independent domains and
longer narratives. The next discriminating step is a held-out intervention:
fit the direction on separate domains, patch it at a frozen location and
dose, and test whether the goal × route choice interaction changes more than
matched random and name/position controls. A larger independent domain set
should then test whether the block-24 pattern replicates. Before treating it
as route composition, project the fitted direction onto the existing direct
route controls and an unrelated, name-and-position-balanced two-option task.
Comparable transfer there would identify a generic answer-position code.
