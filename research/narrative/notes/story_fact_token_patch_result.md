# A story-token substitution moves scores, but an answer-neutral control moves them more

The [frozen single-token test](story_fact_token_patch_prereg.md) asked whether replacing the residual state immediately after the decisive second-hop facts with its other-world state would redirect a later two-name answer. The patch changed **one period token after block 24** on each of 128 late-telling route prompts. The source and target differed in which destination each route reached. The target's visible text was left intact. The original observational extraction selected this token and block before patch outcomes; this is a conditional test at that site, not a search over tokens or layers.

Model: NDIF's pinned `google/gemma-2-9b-it`, local tokenizer snapshot `11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF does not expose a weight revision hash. The [committed report](../results/story_fact_token_patch_v1_summary.json) includes all 1,024 two-candidate score rows as arrays, 256 state captures' checks, per-cell signed effects, domain and factor summaries, exact nulls, bootstrap intervals, flags, and fingerprints. The individual rows and state vectors remain in the ignored local cache.

## Registered decision

For each target, the signed effect is the change in `logp(plan-A owner) − logp(plan-B owner)` toward the winner in the *other* world. Domain means equally weight the 16 cells in each of eight domains. The registered positive causal screen required an effect at least +0.25 nat, a positive eight-domain exact test and bootstrap interval, at least six positive domains and 96 positive cells, valid instrument checks, **and** a mean more than twice the larger absolute mean of two controls: a seeded Gaussian patch and an answer-neutral, norm-matched change of plan order at the same token.

| One-token arm after block 24 | Mean signed effect (nats) | Positive domains | Positive cells | Exact domain-sign p |
| --- | ---: | ---: | ---: | ---: |
| Other-world state, **treatment** | **+0.386** | **8/8** | **106/128** | **1/256** |
| Same-world plan-order state, norm matched | **+0.784** | **8/8** | **110/128** | **1/256** |
| Last-noun-only state, natural norm | +0.192 | 7/8 | 93/128 | 2/256 |
| Last-noun-only state, norm matched | +0.159 | 7/8 | 92/128 | 2/256 |
| Seeded Gaussian, norm matched | +0.074 | 5/8 | 76/128 | 14/256 |
| Zero vector / final-block same-token patch | 0 / 0 | 0 / 0 | 0 / 0 | — |

The treatment's eight-domain bootstrap 95% interval is **+0.232 to +0.547 nat**. Its p-value is the floor of this one-sided 2^8 domain test, with no non-identity tie. A positive shift in 106 cells is a repeatable **relative-score** effect, not 106 independent experimental units. The answer-neutral plan-order arm is about **twice as large** and has the same eight-domain sign consistency. The registered control bar was `2 × 0.784 = 1.568` nat; the treatment's +0.386 does not reach it. This is the sole failed gate, so the **registered full causal screen fails**. The exact sign test alone cannot distinguish a world-specific edit from a generic in-distribution state perturbation at this site.

The treatment changed **zero** top-name choices toward the source-world winner and **one** away: that winner was chosen on 18/128 target prompts before and 17/128 after. Thus the patch did not redirect a categorical name choice in this run, even though it moved the signed log-probability margin. The low baseline source-winner count also shows that the original target-world choice strongly dominates this one-token edit.

**Exploratory split, made after scoring.** The baseline signed margin for the other-world winner averaged −5.23 nats and was negative in 110/128 cells. A patch that merely makes the current answer less certain therefore yields a positive signed effect in most cells. This is not evidence of a purposeful world swap. Splitting the already-scored rows by baseline preference exposes the distinction:

| Arm | Mean signed change when source winner already favoured (18 cells) | Mean signed change when disfavoured (110 cells) | Cells with smaller absolute name margin | New source-winner choices / lost |
| --- | ---: | ---: | ---: | ---: |
| Other-world state | **−0.096** | +0.465 | 106/128 | 0 / 1 |
| Plan-order state | **+0.217** | +0.877 | 109/128 | 5 / 0 |
| Natural noun-only state | −0.139 | +0.246 | 91/128 | 0 / 0 |
| Norm-matched noun-only state | −0.173 | +0.214 | 95/128 | 0 / 0 |
| Gaussian | −0.070 | +0.097 | 72/128 | 0 / 0 |

The other-world patch behaves primarily like **margin compression**: in the small subset already choosing the other-world winner, it moves *away* from that winner. The plan-order patch also reduces absolute margins often, but it moves *toward* the other-world winner in that subset and produces five top-choice crossings. One hypothesis is that the period state carries plan-position ownership, so transplanting a reversed-plan state changes an answer-related binding even though the correct person in its source text is unchanged. The 18-cell subset and this comparison were not registered, and the table does not establish that mechanism. A follow-up should cross source-state plan order with target-text plan order at fixed world and goal, with directional predictions frozen before scoring.

## Last-noun comparison and instrument checks

Changing just the destination noun before the patched period makes a deliberately inconsistent diagnostic story. On the five domains where that text has the same token length and period index as its target, the treatment exceeds the **natural-norm** noun-only arm by +0.168 nat and the **norm-matched** arm by +0.206 nat. Each difference is positive in all five domains, with exact p=1/32 and bootstrap intervals +0.046 to +0.306 and +0.079 to +0.332. These are registered component results. The **registered beyond-last-noun screen also fails** because it requires the full causal screen to pass first. The three length-shifted domains are descriptive only. Across all cells, the lexical/full vector-norm ratio has median 1.09 and range 0.78–1.31; testing both natural and matched arms avoids treating a reduced lexical dose as decisive.

The instrument gates passed. The new no-patch scorer matched the verified core on the shortest and longest prompts, and all 128 old no-patch score rows matched exactly. Captured states matched the earlier extraction within the registered 0.02 relative-L2 limit; the maximum was 0.0146. The source-to-patched period-state relative error was at most 0.00126. A deliberate row-0-only patch made one candidate move and the other stay fixed, and the armed moved-candidates assertion refused it. Zero and final-block same-token arms changed scores by **0** across the grid. Ten of 640 nonzero block-24 jobs (1.56%) were deterministically flagged by the moved-candidates policy, below its 5% limit; the treatment had none.

The plan-order control is a serious confound, not an explanation we can dismiss after seeing the result. It changes presentation while preserving the correct person and uses an in-distribution residual difference at the exact same token and norm. Its large signed response means this particular site can move later answer margins without carrying the intended world swap; the exploratory split suggests its response may differ from the treatment's simple compression. A future test should separate the state components caused by plan presentation and destination binding before interpreting a one-token patch as a story-fact edit. The positive noun-comparison components motivate that refinement, but do not establish a relation code or a coherent narrative transformation here.
