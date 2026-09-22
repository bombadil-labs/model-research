# Pre-registration: is the pain axis sparse?

**Written and committed before a single number exists.** Hour 57.

## Why

Xu, Yuksekgonul & Zou, *Sparse Reward Subsystem in Large Language Models* (arXiv:2602.00986),
find that reward-related information in an LLM is carried by **under 1% of neurons**, and that the
concentration is causally load-bearing: zeroing the value neurons costs **−54.9%** average accuracy
on MATH500 against **−0.6%** for a random neuron set of the same size. Their random arm reads its
null, which is the control this project's first non-negotiable demands. They study positive reward
only; aversive states are untouched.

That makes a structural question sharp. The pain axis is a **dense difference-in-means direction**
in the residual stream, and hour 53 measured 63% of its headline as vocabulary. If aversive valence
is a subsystem of the same *kind* as reward, it should be concentrated in few units. If the pain
axis is a lexical-plus-self/other readout, it should be spread across many. **Sparsity
discriminates, and it is measurable offline with what is already on disk.**

## Instrument

Gemma Scope JumpReLU SAEs on `gemma-2-9b-it` **residual stream** — the model and the site the
replication used. Cached locally; nothing is downloaded. Available points:

| layer | width | average L0 |
|---|---|---|
| 9 | 16k | 47 |
| 20 | 16k | 14, 25, 47, 91, 189 |
| 20 | 131k | 43 |
| 31 | 16k | 43 |

Layer 9 sits in the `final_token` window (the replication peaks at L10); layer 31 is the `mean`
peak (AUC 0.9472). Layer 20's L0 sweep is reported so the answer cannot rest on one sparsity
setting, and the 131k width so it cannot rest on one dictionary size.

**Gemma Scope features are not their MLP neurons.** This measures the residual stream's learned
sparse code, not MLP hidden units. Both are "is it few units" questions; they are not the same
question, and the result is reported as the former.

## Data

The 420-scenario core sets (`S1_1P`, `S2_1P`, `ControlSupplement_1P`) already captured for the
replication, `[n, 42, 3584]` per set. Pain = categories A1–A5, control = B, C1, C2, D, E, exactly
as `painaxis_analyze.compute_pain_vector` uses them. Both extractions (`final_token`, `mean`).

## The two gates, declared before the data is touched

**Gate A — the capture convention.** The SAE must reconstruct *our* activations. Report
fraction-of-variance-unexplained at stack indices **L−1, L, L+1**. Declared: index **L**
reconstructs best, and FVU at L is well below 1. If the SAE cannot reconstruct what we captured,
our capture site is not its training site — an off-by-one or a scaling mismatch — and **nothing
downstream is interpretable.**

**Gate B — a planted sparse contrast, which is the positive control.** Add `α · W_dec[j]` to the
control activations for a randomly chosen feature `j` and run the **whole** pipeline on that
synthetic contrast. It must come back concentrated on ≈ 1 feature, and that feature must be `j`.

This gate exists because of broken instrument 6. There, a calibration built only from null arms
passed degenerately: a coder with no sensitivity reads the same zero as a working one. **A measure
that cannot see a planted sparse contrast cannot report that a real one is dense.** Null arms bound
false positives; only this bounds false negatives.

## The measurement

Encode pain and control activations through the SAE; take the difference in means **in feature
space**, `f_diff`. Concentration statistics on the mass `|f_diff|`:

- number of features to reach **50%** and **90%** of the total mass
- participation ratio `1 / Σ pᵢ²` with `pᵢ = f_diff²ᵢ / Σ f_diff²` — the effective number of features
- top-k mass fraction at k = 1, 5, 10, 50, 100, 500
- how many features are active at all in either group

## Nulls

- **Label permutation**, 200 draws: shuffle pain/control labels within the pool and recompute
  everything. This is the random arm, and it carries the multiplicity of picking a maximum over
  16,384 features, which is why it is a permutation and not an analytic band.
- **Control-vs-control split-half**: split the control set at random in two and take the
  difference in means. A contrast with nothing in it; declares ≈ the null.

Nothing is patched in this experiment, so non-negotiable 2 (pass-through) does not apply and there
is no no-patch arm to report; the split-half is the no-treatment arm. All layers and all L0
settings are reported as a curve — **no layer or sparsity setting is selected** (non-negotiable 4).

## The threshold, set in advance

Their subsystem is under 1% of units. For a 16,384-feature dictionary that is **under 164
features**. Declared:

- **Sparse** if 90% of the mass falls within ~164 features *and* that concentration sits outside
  the permutation null.
- **Dense** if it takes thousands.

Either outcome is a result. If it is dense, the pain axis is not a subsystem of the same kind as
their reward circuitry, and the lexical-plus-self/other reading is strengthened. If it is sparse,
the line gains **named units to ablate**, which is the causal bridge this project does not have.

## What this cannot show

A sparse cause can present as a dense residual direction, and a direction concentrated in a learned
dictionary need not correspond to concentrated *computation*. This is a necessary-condition test in
one direction only: a concentrated result is strong evidence and hands us units; **a dense result is
consistent with both accounts** and must not be reported as refuting a sparse cause. One model. And
the SAE is itself an instrument with its own failure modes — dead features, feature absorption,
and a reconstruction error that is not uniform across the space.

---

# Addendum, hour 57: both gates failed, and the second one earned its keep

Run as pre-registered, on all 16 points. **Both gates failed everywhere.** Recorded here before any
re-run, with the original numbers kept.

## Gate A failed, and the convention it was testing is fine

FVU came back **1.016 at L31, 1.240 at L20, 2.015 at L9** — the SAE reconstructing worse than the
mean of our own data. But the two comparisons *inside* gate A both pointed the right way: the
SAE's own index was the argmin over L±2 at every point, and a scale sweep put the optimum at
exactly α = 1.

The denominator was the fault. `FVU = Σ(x−r)² / Σ(x−x̄)²` measures error against the variance
**across our 500 scenario sentences**, which are short, similar, and nearly collinear. That
denominator is tiny; the numerator carries the full reconstruction error. FVU > 1 is what a narrow
dataset produces from a perfectly good SAE.

Three independent signals say the capture convention is right:

| SAE | best index over L±2 | FVU vs origin | cos(x, x̂) | achieved L0 | advertised L0 |
|---|---|---|---|---|---|
| layer 9 | **9** | 0.201 | 0.894 | **47.4** | 47 |
| layer 20 | **20** | 0.212 | 0.888 | **47.1** | 47 |
| layer 31 | **31** | 0.154 | 0.921 | **46.7** | 43 |

The L0 match is the one that settles it: it is a quantity of the SAE's own, not of my choosing, it
is reproduced to within a feature at the matching index, and it degrades on either side.

**Amended gate A**, declared before the re-run: at the SAE's own index, (i) FVU against the origin
< 0.35, (ii) that index is the argmin over L±2, (iii) achieved L0 within 25% of advertised.

**And `mean` is expected to fail it.** A mean over token positions is not a residual the SAE was
ever trained on. It is reported as failing rather than quietly dropped.

## Gate B failed, and that is the one useful thing that happened

As written, gate B planted `α·W_dec[j]` into the **pain** rows and demanded `n90 ≤ 5`. It could
never have passed: the plant rides on top of the real contrast instead of replacing it. Corrected
to plant into one half of the **controls**, so the plant is the only real signal, and swept over α:

| α (× mean ‖x‖) | planted feature recovered as argmax | n90 | top-1 mass |
|---|---|---|---|
| 0.02 | no | 514 | 0.028 |
| 0.05 | no | 517 | 0.027 |
| 0.10 | **yes** | 485 | 0.104 |
| 0.20 | **yes** | 409 | 0.186 |
| 0.50 | **yes** | 346 | 0.175 |
| 1.00 | **yes** | 408 | 0.128 |

The plant is recovered from α ≥ 0.1 — **and `n90` never collapses.** A contrast with exactly one
real feature in it still reads `n90 ≈ 400`.

**So `n90` is noise, not signal.** A difference in means between two groups of ~250 in a
16,384-dimensional feature space carries sampling noise in every coordinate, and that noise is
dense by construction. The split-half floor — a contrast with *nothing* in it — reads `n90 ≈ 500`.
A statistic whose no-signal floor sits at 500 cannot certify "under 164", and cannot tell sparse
from dense in either direction. The observed values (n90 = 414 at L31, against a permutation null
of 656) would have been written up as "more concentrated than chance but not sparse". **That
sentence would have been about the noise floor.**

This is broken instrument 6's lesson collecting: the gate that catches a measure with no
sensitivity is the one that plants a signal you know is there. Here it fired **before** the number
reached a write-up, which is the first time in this project that has happened in that order.

## What replaces it

`n90` is abandoned. The statistic becomes the one their paper actually uses — a **pruning curve**,
which is noise-robust because it is scored by held-out discriminability rather than by mass:

1. Encode all scenarios; split items into train and test folds.
2. Rank features by |difference in means| **on train only**.
3. For each k, score test items using only the top-k features and compute AUC (pain vs control).
4. Report the whole k-curve. No k is selected (non-negotiable 4).

**Nulls:** random-k features at the same k (their own control), label permutation, and the
control-vs-control split-half, which must sit at AUC 0.5.

**Positive control:** the corrected plant, into half the controls at α = 0.2. The pruning curve
must reach full AUC at **k = 1**. A curve that cannot do that on a one-feature contrast cannot
report that a real one needs thousands.

**Threshold, restated in the new statistic:** sparse if the top **164** features (under 1% of
16,384) retain **≥ 90%** of the full-dictionary AUC's gain over chance, on held-out items.

The limit from the original pre-registration stands unchanged: a dense result is consistent with a
sparse cause and must not be reported as refuting one.

---

# Addendum 2, hour 58: the reference distribution — is the sparsity *pain's*, or the basis's?

Hour 57 found five features saturate the pain contrast. That number is uninterpretable alone: an
SAE is trained to make things sparse, so a strong semantic contrast being recoverable from few
features may be the ordinary case. The question is not "is pain sparse" but **"is pain sparser
than other contrasts of comparable strength on the same pool, through the same pipeline."**

## Contrasts

Same pipeline as hour 57 (5-fold; rank features on train; score held-out; `final_token`; all
three SAE layers), applied to every meaningful binary split available on disk:

- **Core pool (500 items):** each of the ten categories A1–A5, B, C1, C2, D, E one-vs-rest, plus
  the pain contrast itself (A\* vs B–E) as the point being located.
- **Scenario pool (420 items, 21 categories × 20):** each category one-vs-rest; `perspective`
  (self vs other), which hour 53 found to be the network's actual contribution; `intensity`
  (top vs bottom half); and a **nuisance contrast, prompt length** (top vs bottom half by token
  count), which is meaningful to the model but not to us.

Gate A is re-checked per pool per SAE (the scenario pool has not been through it). Gate B is
re-run once per script invocation.

## Statistic

Per contrast: **full-dictionary held-out AUC** and **k₉₀**, the smallest k whose retention ≥ 0.90.
Reported as one scatter of (full AUC, k₉₀) per SAE layer, every contrast a point.

## What is declared

- Sparsity is **specific to pain** only if pain's k₉₀ is at or below the **10th percentile** of
  k₉₀ among contrasts whose full AUC is within **±0.05** of pain's. Contrasts weaker than
  AUC 0.65 are shown but not counted: a weak contrast has no well-defined k₉₀.
- If pain sits in the bulk of comparably-strong contrasts, hour 57's finding is **a property of
  the basis**, and the claim `painaxis-sparse-in-sae` is narrowed to say so.
- The `perspective` contrast is the one to watch alongside pain: it is what the network adds over
  vocabulary, and whether *it* is sparse matters more than whether the headline is.

No contrast is selected on. The whole scatter is the result.
