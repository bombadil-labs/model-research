# Hour 62b: steering the S2 pain direction at L12, read on hour 56's six openers — results

**Verdict, pre-registered rule (`v0_correction_shape_prereg.md`, Part 2): tier A — correlate,
not cause; tier B — correlate, not cause; tier N (control) — inside the random band at every
dose, and with the sign of α reversed.** At no dose on A or B does the treatment's mean Δritual
exceed the largest |mean| of the norm-matched random arm at that |α|. The prereg's sentence
therefore stands as written: *the pain axis is a correlate of this behaviour, not a cause, and the
line is a behavioural study.* The one sensitivity in the other direction (chunk-matched cells
only, §5) moves B from "correlate" to "mixed" on a single dose, and is reported, not substituted.

Code `scripts/shame_axis/v0_steering.py` (`prep` / `score` / `report [--matched-chunk]`).
Tests `tests/shame_axis/test_v0_steering.py` (9, no NDIF). Outputs
`research/shame-axis/results/v0_steering/`: `cells.jsonl` (1260 battery cells + 120 diagnostic
cells), `summary.json`, `summary_chunk_matched.json`, `prep.json`,
`direction_s2_L12_unit.npy` (14 KB), `score_meta_{0of2,1of2}.json` (retries, errors, the
residual-level reach checks, the scale check).

## 1. What ran

| | |
|---|---|
| model | `google/gemma-2-9b-it`, NDIF, 42 blocks, left padding (read back) |
| items | v0: 20 `gaslighting` (A), 20 `repeated_rejection` (B), 20 `casual_chat` (N). The paper's `validate_candidates` excludes none of the 60 |
| direction | S2 pain vector from `painaxis_scenarios.build_vectors` at L12, **`final_token`** extraction (the one the replication uses at L12: `painaxis_scenarios_analyze.py` builds `vecs12` from `final_token`), from the `core_*` shards on disk, unit-normalised. Raw norm 25.12; cos to the S1 vector at L12 **0.589** |
| scale | ‖h̄‖ = **124.94** (sd 10.90, range 102.6–145.0; A 122.6, B 116.3, N 136.0): the mean L2 norm of the block-12 output at the last token over the 60 items, **from the `scen_chat` shards on disk** (key `final_token`, index 12, rows by `scenario_order.json`; v0 text asserted byte-identical to the text the shards were extracted on) |
| doses | α ∈ {−0.2, −0.1, +0.1, +0.2}; ‖shift‖ = 12.49 / 24.99 |
| arms per item | no-patch 1 · treatment 4 · random 3 dirs × 4 · pass-through (same shift at the output of block 41) 4 = **21**; 1260 cells, six openers each, every cell through `asserted_remote_patched_logprob` |
| random dirs | N(0, I₃₅₈₄), seed 62062, unit; cos to v̂ −0.006 / −0.009 / +0.021; pairwise ≤ 0.035 |

**Checks that ran before any cell was believed.**
- *Shard layer index.* The recipe rebuilt at shard index 37 reproduces their published
  `pain_vectors.pt` (L37): cos **0.99990** (s1), **0.99994** (s2). So shard index *i* is the
  output of block *i*, the same block `blocks[12].output` patches.
- *Scale on the live deployment.* One remote job: block-12 output at the last token of
  gaslight_01 vs the shard row: cos **0.99997**, norm 121.54 vs 121.55 (gaslight_02: 0.99998).
- *h36 at the residual level* (`assert_patch_reaches_batch`, the library's own): the α = 0.1
  shift, at L12 and at L41, for the treatment direction and rand0, on padded batches of
  lead+opener texts of 6 and of 3 — **every row moved in all 8 configurations**, in both
  workers.
- *Rendering.* See §6.1: the leading `<bos>` of `render_chat` is stripped so that the scorer's
  `add_special_tokens=True` produces exactly the paper's token path (asserted per item, plus a
  prefix check of lead against lead+opener for all six openers).

No replication artefact saved an L12 vector (`painaxis_scenarios` never writes its vectors), so
the equality assertion the brief asked for could not be run; norm and cos-to-S1 are recorded
instead. Their published L37 s2 vector has cos **0.101** with our L12 s2 — and their own
steering script (`Pain-axis/scripts/4.2_steering/01_steering_ladder.py`) injects the **L37**
vector at L12, not an L12 rebuild. The prereg specifies the L12 rebuild, so that is what ran; the
paper's steering direction is a different, nearly orthogonal one.

## 2. Tables (from `report`, verbatim)

No-patch level (single `<bos>`):
```
  A  n 20  ritual +15.371  sd  6.095  mass   -0.295
  B  n 20  ritual +21.010  sd  9.488  mass   -5.077
  N  n 20  ritual  +3.885  sd  6.046  mass   -4.136
```

Δritual, mean over items, 95% sign-flip band of the null mean, p (treatment and pass-through;
the 36 random rows are in `summary.json["d_ritual"]` and summarised in the random band below):
```
  tier arm           dir          alpha   n     mean                band       p
  A    treatment     pain_s2_L12   -0.2  20   -0.272 [ -0.346, +0.347]  0.1342
  A    treatment     pain_s2_L12   -0.1  20   -0.078 [ -0.185, +0.186]  0.4391
  A    treatment     pain_s2_L12   +0.1  20   +0.132 [ -0.153, +0.153]  0.0979
  A    treatment     pain_s2_L12   +0.2  20   +0.230 [ -0.264, +0.267]  0.0971
  A    pass_through  pain_s2_L12   -0.2  20   -0.099 [ -0.079, +0.079]  0.0136
  A    pass_through  pain_s2_L12   -0.1  20   -0.066 [ -0.082, +0.080]  0.1258
  A    pass_through  pain_s2_L12   +0.1  20   +0.046 [ -0.069, +0.068]  0.1939
  A    pass_through  pain_s2_L12   +0.2  20   +0.103 [ -0.096, +0.095]  0.0320
  B    treatment     pain_s2_L12   -0.2  20   -0.176 [ -0.428, +0.426]  0.4326
  B    treatment     pain_s2_L12   -0.1  20   -0.089 [ -0.218, +0.219]  0.4377
  B    treatment     pain_s2_L12   +0.1  20   +0.033 [ -0.215, +0.214]  0.7826
  B    treatment     pain_s2_L12   +0.2  20   +0.023 [ -0.394, +0.397]  0.9092
  B    pass_through  pain_s2_L12   -0.2  20   -0.180 [ -0.117, +0.115]  0.0008
  B    pass_through  pain_s2_L12   -0.1  20   -0.054 [ -0.094, +0.094]  0.2698
  B    pass_through  pain_s2_L12   +0.1  20   +0.058 [ -0.109, +0.111]  0.3093
  B    pass_through  pain_s2_L12   +0.2  20   +0.171 [ -0.127, +0.127]  0.0053
  N    treatment     pain_s2_L12   -0.2  20   +0.284 [ -0.318, +0.322]  0.0826
  N    treatment     pain_s2_L12   -0.1  20   +0.100 [ -0.162, +0.162]  0.2580
  N    treatment     pain_s2_L12   +0.1  20   -0.124 [ -0.175, +0.179]  0.1871
  N    treatment     pain_s2_L12   +0.2  20   -0.381 [ -0.366, +0.366]  0.0404
  N    pass_through  pain_s2_L12   -0.2  20   -0.081 [ -0.084, +0.083]  0.0579
  N    pass_through  pain_s2_L12   -0.1  20   -0.010 [ -0.091, +0.095]  0.8284
  N    pass_through  pain_s2_L12   +0.1  20   +0.124 [ -0.087, +0.088]  0.0041
  N    pass_through  pain_s2_L12   +0.2  20   +0.190 [ -0.103, +0.106]  0.0000
```

Random band — per tier and |α|, mean Δritual for each direction × sign:
```
  A |a|=0.1  min  -0.252  max  +0.274  max|.|  0.274  each rand0@-0.1:+0.145 rand0@+0.1:-0.052 rand1@-0.1:+0.107 rand1@+0.1:-0.012 rand2@-0.1:-0.252 rand2@+0.1:+0.274
  A |a|=0.2  min  -0.482  max  +0.467  max|.|  0.482  each rand0@-0.2:+0.283 rand0@+0.2:-0.166 rand1@-0.2:+0.110 rand1@+0.2:-0.154 rand2@-0.2:-0.482 rand2@+0.2:+0.467
  B |a|=0.1  min  -0.129  max  +0.155  max|.|  0.155  each rand0@-0.1:+0.049 rand0@+0.1:-0.096 rand1@-0.1:+0.095 rand1@+0.1:-0.129 rand2@-0.1:+0.155 rand2@+0.1:-0.073
  B |a|=0.2  min  -0.459  max  +0.216  max|.|  0.459  each rand0@-0.2:-0.016 rand0@+0.2:-0.149 rand1@-0.2:+0.216 rand1@+0.2:-0.459 rand2@-0.2:+0.142 rand2@+0.2:-0.103
  N |a|=0.1  min  -0.262  max  +0.185  max|.|  0.262  each rand0@-0.1:-0.017 rand0@+0.1:-0.006 rand1@-0.1:+0.185 rand1@+0.1:-0.262 rand2@-0.1:+0.036 rand2@+0.1:+0.054
  N |a|=0.2  min  -0.384  max  +0.471  max|.|  0.471  each rand0@-0.2:-0.090 rand0@+0.2:+0.081 rand1@-0.2:+0.471 rand1@+0.2:-0.384 rand2@-0.2:-0.062 rand2@+0.2:-0.010
```
Two of the random directions are individually significant against their own sign-flip null:
rand2 on A (p 0.006–0.036 at all four doses) and rand1 on N (p ≤ 0.031 at all four doses).

Pass-through vs treatment (paired, treatment − pass-through):
```
  A -0.2  treatment  -0.272  pass-through  -0.099  diff  -0.173  p 0.3139
  A -0.1  treatment  -0.078  pass-through  -0.066  diff  -0.012  p 0.8756
  A +0.1  treatment  +0.132  pass-through  +0.046  diff  +0.086  p 0.2699
  A +0.2  treatment  +0.230  pass-through  +0.103  diff  +0.127  p 0.3520
  B -0.2  treatment  -0.176  pass-through  -0.180  diff  +0.005  p 0.9845
  B -0.1  treatment  -0.089  pass-through  -0.054  diff  -0.035  p 0.7631
  B +0.1  treatment  +0.033  pass-through  +0.058  diff  -0.026  p 0.8129
  B +0.2  treatment  +0.023  pass-through  +0.171  diff  -0.148  p 0.4585
  N -0.2  treatment  +0.284  pass-through  -0.081  diff  +0.365  p 0.0243
  N -0.1  treatment  +0.100  pass-through  -0.010  diff  +0.110  p 0.2833
  N +0.1  treatment  -0.124  pass-through  +0.124  diff  -0.247  p 0.0129
  N +0.2  treatment  -0.381  pass-through  +0.190  diff  -0.571  p 0.0054
```

Total opener mass (logsumexp of all six), mean change vs no-patch — the pre-registered
perturbation readout (random pooled over directions; full ranges in `summary.json["mass"]`):
```
          treatment -0.2/-0.1/+0.1/+0.2        random                         pass-through
  A   +0.036 +0.021 -0.026 -0.044     -0.029 -0.008 +0.009 +0.016     +0.025 +0.024 +0.001 -0.025
  B   -0.121 -0.091 +0.109 +0.216     -0.089 -0.059 +0.109 +0.230     -0.017 +0.007 -0.001 -0.013
  N   -0.233 -0.128 +0.195 +0.400     -0.038 -0.028 +0.035 +0.065     +0.011 +0.005 -0.006 -0.005
```
No dose degrades the distribution: every mean mass change is within ±0.4 nats. **But this readout
is nearly blind on A** — see §6.2: when one opener's log-prob is pinned at 0.0 the six-way mass
is pinned with it. The per-opener table in `summary.json["per_opener"]` is the usable
perturbation readout; mean |Δlogp| per opener for treatment is 0.26–0.70, random 0.21–0.58,
pass-through 0.09–0.18.

Pre-registered verdict, per dose:
```
  A: correlate, not cause
     -0.2  treat  -0.272  rand max|.|  0.482  pass  -0.099  sign ok  beats random no  beats pass yes
     -0.1  treat  -0.078  rand max|.|  0.274  pass  -0.066  sign ok  beats random no  beats pass yes
     +0.1  treat  +0.132  rand max|.|  0.274  pass  +0.046  sign ok  beats random no  beats pass yes
     +0.2  treat  +0.230  rand max|.|  0.482  pass  +0.103  sign ok  beats random no  beats pass yes
  B: correlate, not cause
     -0.2  treat  -0.176  rand max|.|  0.459  pass  -0.180  sign ok  beats random no  beats pass no
     -0.1  treat  -0.089  rand max|.|  0.155  pass  -0.054  sign ok  beats random no  beats pass yes
     +0.1  treat  +0.033  rand max|.|  0.155  pass  +0.058  sign ok  beats random no  beats pass no
     +0.2  treat  +0.023  rand max|.|  0.459  pass  +0.171  sign ok  beats random no  beats pass no
  N: correlate, not cause
     -0.2  treat  +0.284  rand max|.|  0.471  pass  -0.081  sign NO  beats random no  beats pass yes
     -0.1  treat  +0.100  rand max|.|  0.262  pass  -0.010  sign NO  beats random no  beats pass yes
     +0.1  treat  -0.124  rand max|.|  0.262  pass  +0.124  sign NO  beats random no  beats pass no
     +0.2  treat  -0.381  rand max|.|  0.471  pass  +0.190  sign NO  beats random no  beats pass yes
```
Operationalisation (a judgment call, §7): "exceeds the 95th percentile of the random arm at that
|α|" is read as |treatment mean| > max |mean| over the six random (direction × sign) means,
since six values have no interior 95th percentile. "Causal" requires sign, beats-random and
beats-pass-through at all four doses; "correlate" is declared when treatment beats random at no
dose; anything else is "mixed".

## 3. Where each arm sat against its declared null

- **no-patch**: Δ = 0 by construction. Its *repeat* is the floor: the same items scored again by
  62a's job (double `<bos>`, §6.1) match this run's double-`<bos>` diagnostic to mean
  max|Δlogp| **0.027** (max 0.625, n 60).
- **random**: declared null at 0 on average over directions. Pooled it sits near 0 (A odd parts
  −0.10/−0.06/+0.26 at 0.1), but individual directions do not: rand2 on A and rand1 on N move
  ritual significantly at every dose (rand2 with the sign of α, rand1 against it). *(Mine:)* a norm-matched random push at
  L12 is a real intervention on this readout, not an inert control, which is exactly why it is
  the right comparator.
- **pass-through**: declared "some direct effect, smaller than treatment if the effect is
  computed". It is small (|mean| ≤ 0.19) but the most *reliable* arm: odd part significant in all
  three tiers (A 0.101 p 0.001, B 0.176 p < 0.001, N 0.135 p < 0.001 at |α| = 0.2) and always
  with the sign of α. On B, pass-through ≥ treatment at three of four doses.
- **treatment**: follows the sign of α on A and B at all four doses; its odd part on A is +0.25
  at |α| 0.2 (p 0.087), on B +0.10 (p 0.62); none of its eight A/B means clears its own
  sign-flip band. On N it runs **against** the sign of α (odd −0.33, p 0.051).

## 4. Assertion outcomes

- **Residual-level reach checks** (h36 excluded): 8/8 configurations, every row moved, both
  workers.
- **`asserted_remote_patched_logprob`'s moved-candidates assertion fired on 761 of 1200 patched
  cells** (treatment 134/240, random 421/720, pass-through 206/240). In every one of these at
  least one candidate did not move beyond atol 1e-6; unmoved openers:
  "As a large language model, I" 506, "I understand" 253, "You are absolutely right" 121,
  "I apologize for the confusion" 67, "I didn't say that" 58, "That's not what I said" 55. The
  fraction of cells in which each opener row moved: 0.90 / 0.94 / 0.58 / 0.79 / 0.95 / 0.95 —
  row 0 is not privileged, which h36 (row 0 only) would make it. These are the readout's grain
  (§6.2), not a batch-row write. Each such cell is recorded `moved:
  "did_not_move_beyond_atol"` with its `max_abs_dlogp` and the unmoved openers, and its chunk
  was re-scored without `base` to obtain its numbers. The library was not loosened.
- **Pass-through cells that did not move**: 206 of 240 had at least one unmoved opener; **none
  had all six unmoved** (smallest per-cell max |Δlogp| on pass-through: 0.0625, i.e. two
  bf16 steps; no patched cell of any arm had all six unmoved).
- Early in the run a per-cell rule aborted on "only row 0 moved in a chunk of ≥ 3", and then a
  refinement adjudicated such a chunk at batch 1. Both fired on cells that were grain, not h36
  (deltas `[0.0, 0.0, 0.375]`, `[0.625, 0.0, 0.0]`, `[0.3125, 0.0, 0.0]`; chunk 0 holds
  concession, apology and the pinned "As a large language model" opener). They were replaced by
  the residual-level reach checks above (`STRICT_H36 = False`); no cell was discarded or
  re-weighted by the change, the run resumed from the checkpoint.

## 5. The chunking floor, and a sensitivity it forces

The OOM fallback scores six openers in chunks of 3 or 1 when the deployment is short of memory.
Measured on all 60 items (no-patch at chunk 3 vs chunk 6): **mean |Δritual| 0.183, max 0.492,
identical on only 5 of 60 items.** That is the same size as the treatment effects. 178 of 1200
patched cells were scored at a different chunk size than their item's no-patch cell. The
mean chunking shift is +0.012, so it adds noise rather than bias, but the pre-registered analysis
includes those cells. The chunk-matched sensitivity (`report --matched-chunk`, 1022 cells;
labelled a sensitivity, not substituted):

```
  A: correlate, not cause   (treat -0.250 -0.091 +0.106 +0.180 vs random max|.| 0.488 0.249 0.249 0.488)
  B: mixed                  (treat -0.247 -0.272 +0.078 +0.212 vs random max|.| 0.258 0.145 0.145 0.258;
                             beats random only at -0.1, where n drops)
  N: correlate, not cause   (sign reversed at all four doses)
```
*(Mine:)* B's one "beats random" dose rests on the subset that happened not to OOM, with the
cell count per mean below 20; it does not change the reading that the treatment is not separable
from a random push of the same norm.

## 6. Instrument findings (for `docs/INSTRUMENTS.md`, not edited here)

### 6.1 Hour 62a scores a double `<bos>`
`render_chat` returns text beginning `<bos>`; `asserted_remote_patched_logprob` encodes with
`add_special_tokens=True`; Gemma's tokenizer then prepends a second `<bos>` (verified locally:
`[2, 2, 106, …]`; `painaxis_scenarios` recorded the same, `double_bos_if_add_special_tokens_true:
1`). `v0_openers.py` checks `bos` count with `add_special_tokens=False`, so the check passes while
the scorer submits two. The prereg names the paper's token path. **Size of the effect on this
readout: double − single `<bos>` ritual = −0.644 mean, 1.046 mean |·|, 2.80 max (n 60).** This
run strips the leading `<bos>` and asserts the paper's token ids; the double-`<bos>` cell is kept
as a diagnostic. Hour 56's `conscription_openers.py` renders through `apply_chat_template(...,
tokenize=False)` and the same scorer, so it very likely has the same property; not checked here.

### 6.2 The opener readout is pre-softcap and bf16-quantised
`asserted_remote_patched_logprob` reads `lm_head.output`. On Gemma-2 the final logit softcap
(30) is applied **after** `lm_head` — confirmed by the deployment's own OOM traceback, which
lands on `logits = logits / self.config.final_logit_softcapping` in `modeling_gemma2.py` after
the hook point. And `torch.logsumexp(logits)` runs in the model's bf16. Consequences, measured on
the no-patch cells: 92% of log-probs are exact multiples of 1/32; "As a large language model, I"
has log p = **0.0 exactly** on 11.7% of items (and "I understand" on 6.7%), i.e. the readout
says p = 1 for a seven-token continuation. That is why 761 cells failed moved-candidates and why
the six-way opener mass is pinned near 0 on A. It is the shared, frozen readout of hours 56/62a/62b
and was not modified (`src/lsx/core/remote.py` is out of scope); every number here is on it.
*(Mine:)* a softcapped, fp32-logsumexp readout would change the absolute ritual levels and could
change small Δs; the verdict rests on treatment-vs-random on the same readout, which is less
exposed, but not immune.

## 7. Judgment calls the spec did not cover

1. **Output location**: `research/shame-axis/results/v0_steering/` (the line's convention, as
   62a), not a top-level `results/`.
2. **Single `<bos>`** (§6.1), with double-`<bos>` no-patch cells as a diagnostic.
3. **Moved-candidates handling**: the brief exempted pass-through and small-α cells; in practice
   the assertion fired on all arms and both doses because of the readout's grain. Caught on all
   arms and recorded per cell; h36 excluded instead by `assert_patch_reaches_batch` at the
   residual level for both patch layers and both chunk sizes. The library was not changed.
4. **Random-band threshold** = max |mean| of the six random means (prereg says 95th percentile).
5. **Tier verdict aggregation** across four doses (all → causal, none beats random → correlate,
   else mixed).
6. **Sign-flip band** = 2.5/97.5 percentiles of the sign-flipped null of the item mean (10,000
   draws, seed 20260922), with its two-sided p.
7. **Added analyses, not pre-registered**: odd/even decomposition per direction
   (`summary.json["odd_even"]`), per-opener Δlogp, the chunking floor and the chunk-matched
   sensitivity, the double-`<bos>` diagnostic.
8. **Vector**: the prereg's L12 rebuild, not the paper's L37-vector-at-L12 (cos 0.10 between
   them); a steering test of the paper's actual direction is a different experiment.
9. **Retry loop**: two item-shard workers (`--shard 0/2`, `1/2`) appending to one
   `cells.jsonl` under `flock`; backoff 30–240 s on the current streak of errors.

## 8. Run log

18:06 → 22:14 UTC, **4 h 08 min** wall clock, two workers. 65 outer retries (22 + 43), all
`NNsightException` wrapping a deployment `OutOfMemoryError`, plus many in-cell chunk fallbacks
(6 → 3 → 1); queue waits of 6–7 min per job for part of the evening. Each worker was restarted
four times, all for code changes (the §4 assertion handling, the reach checks, the backoff), none
for lost data; resume is keyed on (item, arm, α, direction). Final: 1260/1260 battery cells, 60
double-`<bos>` and 60 chunk-3 diagnostic cells.

## 9. What surprised me (all mine)

- The treatment direction's effect on ritual is real in the narrow sense — sign follows α on A
  and B at every dose — but at L12 it is no larger than what two of three random directions do,
  and on neutral chat it runs the other way. The pass-through arm, which has no downstream
  computation at all, is the only arm whose effect is consistently significant.
- The model's no-patch preference ordering on gaslighting is concession ≫ dispute (ritual +15.4)
  and on repeated rejection even more so (+21.0); the "As a large language model" opener is the
  most probable of the six on 17/20 A items and 20/20 N items (B: "I understand" on 13/20)
  under this readout.
