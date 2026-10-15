# Open problem 4i: the permutation arm was not below its null. Every row shared one seed's shuffles.

**Verdict: withdrawn.** On 19 rows re-extracted live from Qwen2.5-1.5B, the h8 readout's
permutation arm averages **+0.002** over 64 independent seeds. Seed 0 averages **−0.106**. Seed 0
is the most extreme of the 64.
- **Why the rows agreed.** All 25 of hour 48's rows ran at `seed=0`. The arm's random generator
  depends only on the seed and the training-set size, so every grid of the same shape received
  *identical* shuffles. Seven of the eight grid/model pairs share one draw set. The other,
  `factors_v2`, has its own.
- **Why that draw set reads low.** Seed 0's shuffles happen to put back about 3.5 SD more of the
  true labels than a typical seed. The arm's mean tracks exactly that label overlap.
- **The two recorded explanations are both wrong:**
  - the mechanism, that the uncentered cosine ranking is "partly a *norm* ranking";
  - the prediction, that the arm "would be refused at roughly 60–100 draws".

  Both quotes are from `phase2_derivable.md`.
- **No treatment verdict changes.** Gains are taken over the measured lexical floor, never over
  this arm.

Model: `Qwen/Qwen2.5-1.5B` at revision `8faed761d45a263340a0528343f099c05c9a4323`. Run on CPU in
float32, in a claude.ai cloud container rather than the local RTX machine. Extraction went through
`build_stack`, so every extraction assertion ran. Results:
[`permutation_seed_audit.json`](../results/permutation_seed_audit.json). Script:
`scripts/narrative/permutation_seed_audit.py`. Test:
`tests/narrative/test_permutation_arm_calibration.py`.

## What hour 48 recorded

> "**the permutation arm sits below its null on 25 of 25 rows** (mean −0.117, every one inside its
> band, sign test p ≈ 3e-8). The mechanism is that the uncentered cosine ranking is partly a *norm*
> ranking." (`docs/EXPERIMENTS.md:2188-2190`)

The h48 note (`phase2_derivable.md`, §3c) gave the mechanism in more detail: "a cosine against a
small direction is partly a ranking by the candidate's own norm, which a shared permuted direction
applies coherently to every item fitted from it". It also gave a prediction: "the band shrinks with
draws and the bias does not, so this arm would be refused at roughly 60–100 draws." The claims
table carried this as `permutation-arm-below-null`, status open.

## Why the mechanism could not be right

`readout_battery` shuffles the factor labels among the training items **before** the level means
are fitted. On a balanced grid, relabelling one factor's levels maps the multiset of training
labels to itself. The permuted level directions are therefore exchangeable across levels:
`(d₁ … d_L)` has the same distribution as `(d_σ1 … d_σL)` for every permutation σ.

Now take one target. Exchangeability gives E[rank(v_ℓ | d_ℓ)] = E[rank(v_ℓ | d_m)] for every m.
Average over targets. For any fixed direction, the mean rank over the candidate set is the midpoint
exactly, so the arm's expectation is **exactly chance**.

This holds for any scoring function, norm-sensitive or not. It also holds for the composed arm,
because product relabellings act transitively on the combinations. A norm effect can make a single
draw noisier, but it cannot move the arm's mean. What it leaves open is that 25 rows were not 25
independent draws.

## The evidence, in the order it was gathered

**1. Committed data alone shows the rows are one draw set.** On `factors_v1`, the arm's 32
per-draw means correlate at **0.63 to 0.96** across Qwen-0.5B, Qwen-1.5B, Pythia-1.4B and
Gemma-2-9B-it. Four different networks agree draw by draw only if they received the same shuffles.
Reproducing the generator from the grid specification alone, with no activations, confirms it:
every 4-scene × 9-combination grid receives identical permutations at `seed=0`, whatever the model
or the grid's text.

**2. The arm is unbiased on synthetic signal.** This is the calibration the arm never had: until
now its only check was on noise (`test_core_phase2.py`). The synthetic grid has:
- a strong factor signal, so the treatment is a perfect lens;
- a large shared component, so the cosine is far from centered;
- norms that depend on level, by up to 9×.

Over 200 seeds, the arm's mean sits at chance on every arm (|t| < 1.8). This is the exact
condition under which a norm ranking would have to show itself. It does not. It is now a test.

**3. Gate.** At seed 0, the live re-extraction reproduces all **19 of 19** committed rows to
within 1e-9 of their recorded permutation-arm value, at the same layer (14 of 29). The
`factors_v2` rows reproduce hour 48's cached-path numbers; the other five grids reproduce hour 50's
live rows. Had any row disagreed, the script would have stopped.

**4. Sixty-four independent seeds, 32 draws each, which was hour 48's setting.**

| grid | arm | chance | committed (source) | seed 0 deviation | mean deviation over 64 seeds ± SE | seed 0 percentile | seed 0 overlap excess (SD over seeds) | draw-level r, intercept at zero overlap |
|---|---|---:|---|---:|---:|---:|---:|---:|
| `factors_v2` | composed | 9.5 | 9.2556 (h48 cached) | -0.244 | +0.0676 ± 0.0206 | 0.03 | +0.0122 (0.0175) | -0.70, +0.0473 |
| `factors_v2` | era | 2.0 | 1.9709 (h48 cached) | -0.029 | -0.0002 ± 0.0047 | 0.22 | +0.0174 (0.0087) | -0.63, +0.0043 |
| `factors_v2` | voice | 2.0 | 1.9332 (h48 cached) | -0.067 | +0.0138 ± 0.0055 | 0.03 | +0.0035 (0.0086) | -0.79, -0.0022 |
| `factors_v2` | tense | 1.5 | 1.4792 (h48 cached) | -0.021 | -0.0015 ± 0.0056 | 0.44 | -0.0087 (0.0144) | -0.80, -0.0023 |
| `factors_v1` | composed | 5.0 | 4.7526 (h50 live) | -0.247 | -0.0103 ± 0.0127 | 0.03 | +0.0590 (0.0168) | -0.77, -0.0023 |
| `factors_v1` | era | 2.0 | 1.9123 (h50 live) | -0.088 | -0.0010 ± 0.0048 | 0.02 | +0.0260 (0.0115) | -0.66, -0.0027 |
| `factors_v1` | voice | 2.0 | 1.9479 (h50 live) | -0.052 | -0.0013 ± 0.0049 | 0.11 | +0.0330 (0.0115) | -0.81, +0.0065 |
| `factors_gpt_v1` | composed | 5.0 | 4.7865 (h50 live) | -0.214 | -0.0048 ± 0.0121 | 0.03 | +0.0590 (0.0168) | -0.66, +0.0021 |
| `factors_gpt_v1` | era | 2.0 | 1.9089 (h50 live) | -0.091 | +0.0005 ± 0.0046 | 0.02 | +0.0260 (0.0115) | -0.56, -0.0011 |
| `factors_gpt_v1` | voice | 2.0 | 1.9297 (h50 live) | -0.070 | -0.0077 ± 0.0047 | 0.08 | +0.0330 (0.0115) | -0.69, -0.0012 |
| `theme_gpt_v1` | composed | 5.0 | 4.7839 (h50 live) | -0.216 | -0.0104 ± 0.0131 | 0.06 | +0.0590 (0.0168) | -0.74, -0.0026 |
| `theme_gpt_v1` | era | 2.0 | 1.9236 (h50 live) | -0.076 | +0.0012 ± 0.0060 | 0.05 | +0.0260 (0.0115) | -0.75, -0.0011 |
| `theme_gpt_v1` | theme | 2.0 | 1.9583 (h50 live) | -0.042 | -0.0026 ± 0.0056 | 0.20 | +0.0330 (0.0115) | -0.63, +0.0035 |
| `theme_v1` | composed | 5.0 | 4.7839 (h50 live) | -0.216 | -0.0068 ± 0.0117 | 0.03 | +0.0590 (0.0168) | -0.74, +0.0008 |
| `theme_v1` | era | 2.0 | 1.9705 (h50 live) | -0.030 | +0.0019 ± 0.0052 | 0.25 | +0.0260 (0.0115) | -0.83, -0.0007 |
| `theme_v1` | theme | 2.0 | 1.8967 (h50 live) | -0.103 | -0.0092 ± 0.0048 | 0.03 | +0.0330 (0.0115) | -0.58, -0.0043 |
| `mood_v1` | composed | 5.0 | 4.8767 (h50 live) | -0.123 | +0.0042 ± 0.0115 | 0.11 | +0.0590 (0.0168) | -0.65, +0.0102 |
| `mood_v1` | era | 2.0 | 1.9062 (h50 live) | -0.094 | +0.0021 ± 0.0048 | 0.02 | +0.0260 (0.0115) | -0.74, +0.0002 |
| `mood_v1` | mood | 2.0 | 2.0139 (h50 live) | +0.014 | +0.0016 ± 0.0046 | 0.64 | +0.0330 (0.0115) | -0.50, +0.0052 |

Across the 19 rows:
- **Seed 0:** 18 of 19 below chance, mean −0.106. It ranks **1st of 64** seeds on the cross-row
  mean. No other seed puts more than 17 of 19 below.
- **All seeds:** on average 9.5 of 19 below, and a cross-row mean of +0.002.
- **All 19 rows below at once,** with an independent seed drawn for each row: **1 in 10,000**
  simulated draws.

**5. The mechanism that does explain it is label overlap.** A random shuffle of balanced labels
leaves some items on their true level. When it leaves more than 1/L of them there, the permuted
direction carries a fraction of the true factor signal, and on these grids that signal is strong.
For each draw I computed the overlap excess, defined as the alignment `f_ℓℓ − mean_{m≠ℓ} f_ℓm` of
the shuffled-into-level fractions, reproducing the battery's generator exactly. Results:
- **Seed 0 is extreme on overlap.** For the 9-combination shape, its overlap excess is **+0.059**
  on the composed arm (the sum over factors), against a spread of 0.017 over seeds: about
  **3.5 SD**. Era is +0.026 (2.3 SD) and voice or theme +0.033 (2.9 SD).
- **Overlap predicts each draw's mean.** Within draws, r is −0.50 to −0.83 across the 19 rows. The
  fitted intercept at zero overlap is within ±0.011 of chance on 18 of 19 rows. The exception is
  `factors_v2` composed, at +0.047.
- **Overlap predicts each seed's mean too:** r −0.52 to −0.83.

**6. Hour 48's prediction, tested.** Seed 0, more draws, using the measured band that
`pooled_draw_arm` applies (3 SD of the draw means, divided by √draws):

| grid | arm | 32 draws | 64 | 128 | 256 |
|---|---|---:|---:|---:|---:|
| `factors_v2` | composed | -0.244 (±0.520) | -0.092 (±0.367) | -0.035 (±0.299) | +0.025 (±0.198) |
| `factors_v2` | era | -0.029 (±0.105) | -0.010 (±0.094) | +0.037 (±0.058) | +0.010 (±0.042) |
| `factors_v2` | voice | -0.067 (±0.123) | -0.006 (±0.097) | -0.006 (±0.072) | +0.001 (±0.048) |
| `factors_v2` | tense | -0.021 (±0.149) | +0.010 (±0.088) | -0.035 (±0.062) | +0.002 (±0.044) |
| `factors_v1` | composed | -0.247 (±0.283) | -0.069 (±0.192) | -0.099 (±0.142) | +0.005 (±0.108) |
| `factors_v1` | era | -0.088 (±0.112) | -0.067 (±0.092) | -0.054 (±0.061) | -0.025 (±0.044) |
| `factors_v1` | voice | -0.052 (±0.136) | +0.019 (±0.092) | -0.028 (±0.069) | +0.006 (±0.046) |
| `factors_gpt_v1` | composed | -0.214 (±0.276) | -0.045 (±0.228) | -0.048 (±0.146) | -0.029 (±0.109) |
| `factors_gpt_v1` | era | -0.091 (±0.114) | -0.017 (±0.103) | -0.009 (±0.061) | -0.009 (±0.043) |
| `factors_gpt_v1` | voice | -0.070 (±0.124) | -0.020 (±0.093) | -0.017 (±0.064) | -0.005 (±0.045) |
| `theme_gpt_v1` | composed | -0.216 (±0.261) | -0.114 (±0.239) | -0.018 (±0.170) | -0.020 (±0.115) |
| `theme_gpt_v1` | era | -0.076 (±0.154) | -0.073 (±0.118) | -0.030 (±0.068) | -0.015 (±0.046) |
| `theme_gpt_v1` | theme | -0.042 (±0.113) | +0.015 (±0.091) | +0.003 (±0.066) | +0.005 (±0.049) |
| `theme_v1` | composed | -0.216 (±0.323) | -0.145 (±0.228) | -0.049 (±0.161) | -0.022 (±0.111) |
| `theme_v1` | era | -0.030 (±0.131) | -0.062 (±0.104) | -0.013 (±0.071) | +0.002 (±0.047) |
| `theme_v1` | theme | -0.103 (±0.132) | -0.008 (±0.080) | -0.027 (±0.060) | -0.009 (±0.041) |
| `mood_v1` | composed | -0.123 (±0.215) | -0.161 (±0.180) | -0.041 (±0.139) | -0.022 (±0.100) |
| `mood_v1` | era | -0.094 (±0.105) | -0.074 (±0.091) | -0.042 (±0.058) | -0.010 (±0.041) |
| `mood_v1` | mood | +0.014 (±0.081) | -0.011 (±0.070) | +0.011 (±0.044) | +0.002 (±0.037) |

**No row is refused at 64, 128 or 256 draws.** The deviation shrinks toward zero as draws are
added. That is what a draw-set artifact does; a bias would stay put while the band shrank.

**7. A scare, reported.** After the first 64 seeds, `factors_v2`'s composed arm read
**+0.068 ± 0.021**, *above* chance (t ≈ 3.3). That contradicted the exchangeability argument, so
I re-checked that every grid is fully balanced (all six are) and ran **512 more seeds** on the
cached stack. They read **+0.0005 ± 0.008** (t 0.06). It was a fluctuation: one t of 3.3 among 19
rows, before any correction for multiple rows.

## What changes

- **Claims.** `permutation-arm-below-null` is **withdrawn**. It is superseded by
  `permutation-arm-at-null`, which **holds**: the arm's expectation is chance by construction, and
  on 19 live rows it is chance over 64 seeds.
- **Verdicts.** None changes. The arm is an off-null alarm, and gains are taken over each grid's
  measured lexical floor. In hour 48's words, "the treatments sit 0.9 to 1.6 ranks away from
  anything, not 0.12".
- **What the episode does change is a reading habit.** Hour 48 read its rows as independent
  replications ("a sign test on 25 of 25 is p = 3 × 10⁻⁸"). Rows that share a seed share their
  null draws. Any statistic pooled **across** rows needs independent draws per row. The seeding
  policy is a decision for the author (`docs/PROGRAM_v2.md`, C1a): keep `seed=0`, so that ledger
  rows reproduce bit-for-bit, and draw fresh seeds only for pooled analyses; or seed every row
  separately and re-land the 15 Qwen ledger rows.
- **Was this a broken instrument?** The arm, its null and its band are all correct for any single
  row. What was wrong was a cross-row inference and an untested mechanism sentence, so this is not
  an entry for `docs/INSTRUMENTS.md`.

## What was not tested

- **Hour 48's rows on Qwen-0.5B, Pythia-1.4B, Gemma-2-9B-it and GPT-J-6B were not re-extracted.**
  Their weights are not in this container. The cross-model draw correlation in step 1, computed
  from the committed numbers, says the same draw set drove them. That is inference from committed
  data, not a rerun.
- **The random arm** also takes `default_rng(seed)`, so its directions are shared across rows of
  equal width. Its directions do not depend on the labels, so the overlap mechanism cannot apply.
  It was not audited.
- **Nothing here was pre-registered.** This is a diagnosis of an existing record, and the "scare"
  in step 7 is reported because it happened, not because a rule required it.

## Failures and cost

- **The model download stalled once,** at 1.9 of 3.1 GB. It was killed by PID, not with
  `pkill -f`, and resumed.
- **A second test I wrote was wrong.** It claimed seed 0 is an outlier on a synthetic grid at
  n_perm = 4. It failed (seed 0 sat at the 37th percentile), because the claim was contingent and
  I had fitted it to the story. I deleted it before committing.
- **The first audit run lacked the draw sweep,** which I added after reading hour 48's prediction.
  The sweep therefore came from a second run on the cached stacks; seed 0 reproduced identically.
- **Cost:**
  - wall time about 50 minutes, on 4-core CPU;
  - live extraction of six grids about 20 minutes;
  - the 64-seed rerun from cache 117 s;
  - the 512-seed check about 5 minutes;
  - agent tokens were not metered separately in this session.

## Proposed edits to `docs/EXPERIMENTS.md` (not applied)

CLAUDE.md does not allow an agent to edit a line's `docs/EXPERIMENTS.md` unasked, so the in-place
retraction is proposed here for the author to apply:

- **Line 2188,** after "(mean −0.117, every one inside its band, sign test p ≈ 3e-8)", insert:
  "*[Withdrawn 2026-10-15: all 25 rows ran at seed 0 and share its permutations; over 64
  independent seeds the arm is at chance (+0.002); see `notes/permutation_seed_audit.md`.]*"
- **Open problem 4i (line 2342):** strike it through and append "withdrawn 2026-10-15: a shared
  seed, not a norm ranking; the arm is at chance over 64 seeds and is refused at no draw count up
  to 256 (`notes/permutation_seed_audit.md`)".
