# The final-token choice direction does not transfer before the question

The [frozen location test](prequestion_route_state_prereg.md) reused all 256
two-link route-story prompts from the positive
[final-token pilot](goal_route_activation_pilot_result.md). In each single
forward, it read three residual positions: the period immediately after the
informative goal and route facts, the period ending a long neutral bridge,
and the final prompt token after the explicit answer question. A causal mask
keeps both story positions from reading that later question. The bridge-end
position was the sole registered primary; the earlier informative boundary
was declared as a secondary location diagnostic before extraction.

Model: NDIF's pinned `google/gemma-2-9b-it` deployment, local tokenizer
snapshot `11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF exposes no
weight revision hash. The [committed summary](../results/prequestion_route_state_v1_summary.json)
contains the full six-block curves, domain and telling values, exact nulls,
random-direction arms, repeat and instrument checks, prompt indices and
code/grid fingerprints. The 256 three-position arrays and eight repeats
remain in ignored `cache/prequestion_route/v1/states`.

## Registered result

The fixed `I_first` factorial interaction was oriented to the first-listed
plan owner and scored by opposite-telling leave-domain-out cosine, exactly
as in the pilot. The decision averaged blocks 16 and 24. Neither story
position has a shared direction under that test:

| Location | Fixed block-16/24 cosine | Exact eight-domain orientation p | Eight-domain bootstrap 95% interval | Positive domains, early / late target |
| --- | ---: | ---: | ---: | ---: |
| After informative facts (secondary) | −0.0005 | 148/256 = 0.578 | −0.0048 to +0.0035 | 4/8 / 4/8 |
| After neutral bridge (**primary**) | **−0.0036** | **186/256 = 0.727** | **−0.0082 to +0.0020** | **2/8 / 3/8** |
| After answer question (prior pilot) | +0.0854 | 2/256 = 0.0078 | +0.0660 to +0.1094 | 8/8 / 8/8 |

The bridge-end primary fails its positive direction, exact-null, interval
and domain-count gates. The earlier position also fails. The same forward
reproduces every cached final-question vector at blocks 16 and 24 exactly
(maximum relative L2 error 0), so a deployment or extraction shift cannot
explain the location difference. Separate-job repeat drift is zero at every
block and all primary interactions are above the registered noise floor.
This falsifies the **specified bridge-end linear-direction transfer**:
the interval's upper bound (+0.0020) is far below the prior final-question
effect (+0.0854). It does not test every representation at that position.
The block-24 fitted mean directions at bridge-end and after the question
have cosine −0.015, nearly orthogonal.

| Block | 0 | 8 | 16 | 24 | 32 | 40 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| After facts | +0.0061 | +0.0017 | +0.0018 | −0.0029 | −0.0036 | −0.0402 |
| After bridge | +0.0042 | −0.0037 | +0.0050 | −0.0122 | −0.0026 | +0.0069 |
| After question (prior pilot) | +0.0224 | −0.0219 | −0.0002 | **+0.1710** | +0.1599 | +0.1534 |

At the informative boundary, the late telling has a much larger local
factorial interaction norm than the early telling (block-24 medians 378.4
versus 57.5), because the late boundary directly follows the decisive
destination clause while the early boundary follows a fixed plan sentence.
Yet both target-telling transfer curves stay near zero: at block 24,
−0.0010 late and −0.0049 early. After the neutral bridge, the two norm
medians shrink to 14.3 and 12.1, and transfer remains near zero. This
separates a strong *local* change in the state from a cross-domain aligned
direction; bridge washout alone cannot account for the earlier null.

Full-text and last-200-character word-bag interactions measured exactly
zero. Five domains had equal goal token lengths and three differed by one
token. These surface and length checks are reported in the summary; no
domain or layer was selected from them.

## Instrument correction before bulk extraction

The first full-prompt state matched the established core exactly, but the
original shortened-prefix check exceeded its frozen 1% relative L2 limit
at bridge-end block 24: 1.122%, with cosine 0.999946. That failed check is
preserved in the artifact. The shortened trace changes the deployment's
bf16 numerical path. Before the factorial grid was extracted, the
[documented amendment](prequestion_route_state_prereg.md) replaced that
gate with a same-length causal check: keep the full token length and mask,
replace all **future** token IDs, then read the boundary state. It was
bit-exact at both story positions and blocks 16/24. The original first
state was archived outside the resumable cache and re-extracted under the
corrected code fingerprint. The registered statistical decision and
other instrument thresholds were unchanged.

## What this means

In these constructed route miniatures, the particular shared
first-listed-answer direction seen at the final prompt token is not found
at either tested story-ending token before the question. The simplest
reading is that the explicit answer question **assembles or exposes an
answer-slot code** from information in the prompt, rather than merely
reading out a stable copy of that direction at the story ending. This is a
location-specific result, not evidence that the model lacks route or goal
information elsewhere in its residual stream, in other tokens, or in a
nonlinear code. A later experiment should compare a matched late-reveal
and chronological telling at multiple story positions, then intervene on
the answer step only after separating generic answer selection from any
story-specific state.
