# Propp function transfer: first corpus spike (frozen before model extraction)

## Question and scope

Can a decoder's state at an annotated plot-function signal distinguish the same function in a
different tale? This tests recognition within one collection of Russian folktales. It does not test
Campbell's Hero's Journey, cross-genre transfer, causal control, or a complete story shape.

Source: the 15 Story Workbench `.sty` tales in the MIT ProppLearner archive, inner ZIP MD5
`8c3219aa8dbd85f3f94a8a0a616780ce`. The source texts remain local; only aggregate results and
code enter this repository. Use the five recurring Propp function families `A`, `C`, `H`, `I`, `K`,
chosen by annotation counts before seeing activations. Retain only `ACTUAL` annotations. Preserve
all occurrences, including repeated functions in one tale. This yields 53 events: A=13, C=7,
H=9, I=12, K=12. The corpus supplies a single literary tradition and mostly one translation;
even a positive result would have that narrow scope.

## Extraction and validation

Use the body region marked `TEXT` in each file, excluding bibliographic headers. XML character
offsets index the `char` representation without its formatting newlines. Verify its declared length,
all body and signal bounds, and that every signal's last character maps to exactly one model token.
The readout is that token's hidden state for every layer, after one causal forward over the complete
body. This keeps prior story context and gives the model no later text at that position. The last
hidden state is post-final-norm; label it as such. Work one tale at a time under the local GPU lock.
Record exact checkpoint, device, dtype, tokenizer/library versions, source hash, code commit, and
readout position in ignored local provenance. No raw story text is committed.

## Scoring

Leave out one whole tale per fold. At each layer, subtract the training mean, normalize each event
vector, build the mean vector for each class from training tales, normalize each class mean, and
predict the largest cosine for held-out events. The primary score is balanced accuracy: mean recall
over the five classes, pooled over held-out events. Report per-class recall, per-tale ordinary
accuracy, and the complete layer curve. The primary layer statistic is the mean balanced accuracy
over layers 10–18, fixed before extraction. No score-selected layer is a claim.

Controls use the same held-out tales. Text baseline: word TF-IDF (1–2 grams) on the 200 characters
ending at the signal, nearest normalized class centroid. Position baseline: nearest training class
mean of relative signal position in the tale. Combined baseline: average of the text cosine and
`1 - absolute position difference`; no fitted weight. Layer 0 is a static-token control. A
within-tale label permutation (1,000 seeded draws) gives the null for the fixed mid-layer statistic.
It preserves event positions and class counts within each tale. The primary gain is mid-layer score
minus the strongest of text, position, and combined baselines. Pairwise talewise bootstrap (2,000
resamples) gives an uncertainty interval for that gain, recomputing balanced accuracy over sampled
tales; the permutation gives a calibration check rather than an effect-size floor.

## Predictions and decision

Pre-run prediction: mid-layer balanced accuracy at least 0.45 and at least 0.10 above the strongest
baseline, with permutation p <= 0.05. A positive screening result requires all three and a
bootstrap interval whose lower endpoint is above zero. Failure to meet them means this corpus and
readout do not yet support a transferable function signature; it does not establish absence of any
narrative representation. Inspect confusion, especially H vs I, which often occur in the same
sentence, and whether the gain is concentrated in one tale or one annotation family. No patching or
generation is in this spike.

## Pre-run instrument risks

- Function labels come from an analyst who knew the folktale rubric; label quality is not an
  independent test of the ontology.
- Canonical plot order can make position look like meaning; the position and combined baselines
  must be shown even if model accuracy is high.
- Function signals are often verbs, so cross-tale lexical overlap can drive recognition. The text
  baseline and layer 0 measure this floor, but neither exhausts lexical confounding.
- One model and 15 related tales cannot establish an invariant trope shape. The next corpus would
  need unrelated stories and independent labels.
