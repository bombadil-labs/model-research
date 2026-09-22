# Propp function recognition across tales: first spike

**Status:** screening positive for a *local function signal*; no resolved full-story context gain.
The [pre-registration](propp_spike_prereg.md) was written before model extraction. Aggregate
numbers, including the [complete layer curve](../results/propp_spike_summary.json), are committed;
raw tales, vectors, and exact checkpoint provenance remain in ignored `cache/propp/`.

## Source and measurement

The [MIT ProppLearner archive](https://dspace.mit.edu/entities/publication/62248a45-5353-4fff-ab63-f62560f558db)
contains 15 annotated Russian folktales. Its inner ZIP matches the registered MD5. We excluded
the bibliographic headers and 5 implicit annotations in the selected families, retaining 53
explicit signals: A=13, C=7, H=9, I=12, K=12. Seven pairs of selected functions share a sentence,
so the readout is the model state at the last token of each annotation signal, with the entire
earlier tale available causally. The local run used CUDA and float16. Each tale was held out in turn;
class centroids were fit only on the other 14. The primary score averages balanced accuracy over
the preselected layers 10–18. There is no intervention or generation in this measurement.
The longest body has 2,518 model tokens, below the checkpoint configuration's 131,072-token
position limit.

## Registered prediction and controls

| Readout, held-out tales | Balanced accuracy |
| --- | ---: |
| Full-story state, layers 10–18 mean | **0.625** |
| Text TF-IDF, preceding 200 characters | 0.280 |
| Relative position in tale | 0.302 |
| Fixed text + position average | 0.369 |
| Layer 0, signal token | 0.477 |
| Within-tale label-permutation null, mean; 95th percentile | 0.206; 0.323 |

The registered gain over the strongest text/position control is **+0.256** (tale bootstrap 95%
interval **+0.170 to +0.338**). Permutation p is 0.001 from 1,000 seeded shuffles. All three
registered thresholds passed: score ≥0.45, gain ≥0.10, p ≤0.05; the gain interval also excludes
zero. This is evidence that a signal learned from other tales can identify these function families
within this corpus. The calculation is a readout, so patch treatment/random/no-patch arms are not
applicable; the unmodified forward, lexical/position controls, and a label permutation are reported.

Layer 0 is a stronger floor than the hand-built lexical controls. The mid-layer gain over layer 0
is **+0.148** (tale bootstrap 95% interval **+0.068 to +0.226**). This supports a computed
distinction beyond the signal token's static embedding, but it does not say whether the computation
uses the whole narrative. The full layer curve is in the aggregate JSON; the preregistered
mid-layer band was not selected from that curve. Its values rise from 0.477 at layer 0 through
0.647 at layer 14 to 0.702 at layer 26; the final post-norm state is 0.581.

At fixed layer 14, class recall is A 0.54, C 1.00, H 0.78, I 0.42, K 0.50. Victory (`I`) is the
weakest class, confused with response, struggle, and resolution. Tale accuracy ranges from 0 to 1;
the one zero-scored tale has a single selected event, so a tale-level success count would be brittle.

## Exploratory context check after seeing the primary result

We repeated the same activation readout with only the preceding 200 characters ending at each
signal. Its mid-layer balanced accuracy is **0.576**, versus **0.625** with the causal tale prefix.
The paired difference is **+0.049**, with a tale bootstrap 95% interval **−0.005 to +0.126**.
One of 53 final signal tokens has a different token ID between contexts; excluding it leaves the
difference **+0.049**, interval **−0.005 to +0.126**. The local readout itself clears the text and
position controls and its own layer-0 floor (0.449; gain +0.127, interval +0.053 to +0.202).

Thus we cannot yet say that the model is using the story's larger plot shape to recognize the
function. Most measured accuracy survives with a short local passage. The five-point full-context
advantage remains plausible, but this corpus is too small to resolve it at this precision.

## Boundaries and next discriminating test

These are 15 related folktales with supplied Propp labels, not unrelated stories or independently
discovered tropes. The rubric may be visible in local event semantics: an annotation of victory
often accompanies language that describes winning. The exact signal token repeats across tales
for 19 of 53 events, and static token states already score 0.477. Neither the TF-IDF baseline nor
layer 0 exhausts local semantic cues. Collapse of function subtypes into five families also removes
finer plot distinctions. The result does not establish a Hero's Journey manifold, a decomposable
story representation, or a steerable direction.

The next test should **hold local event wording nearly fixed while changing its narrative role**,
then ask whether the model's state follows the role across held-out stories. That comparison would
force earlier context to do work. A larger corpus with independently annotated, unrelated stories
would follow only if this stricter within-story control clears its lexical and position floors.

## Instrument record

- The parser verified the archive checksum, all 15 declared character lengths, body bounds, and
  non-empty signal spans. Every selected signal mapped to exactly one readout token.
- Checkpoints were written one tale at a time. The first scoring pass failed in bootstrap indexing:
  labels were resampled, baseline predictions were not. Correcting it left the saved vectors and
  primary classification untouched. A synthetic test with unequal tale lengths now exercises this
  case. The local context run had one transient CUDA initialization failure and succeeded on retry.
- Fresh full-story and 200-character extractions from committed code `e12c6c8` reproduced their
  respective activation digests and aggregate reports exactly. The fresh checkpoints record the
  extraction script hash in ignored local provenance.
- The within-tale permutation null sat near five-way chance and below the observed score. A
  synthetic known-signal test scored 1.00 with all text/position controls at 0.20. The raw vectors
  and per-tale checkpoints remain local; the aggregate JSON contains no copyrighted tale text.
- Every held-out training fold contains all five families; the scorer now refuses a missing class
  rather than letting a NaN centroid silently win an `argmax`.
