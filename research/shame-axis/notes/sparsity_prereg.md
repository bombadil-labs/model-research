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
