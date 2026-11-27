# Inkling — experiment log

Entries are written by the agent unless marked otherwise. This line's hours are not numbered with
the other lines; entries are dated.

---

## 2026-11-26 — Speed baseline on Apple M1 Max, 32 GB (agent)

Artifact: `research/inkling/results/speed_baseline.json` (provenance inside). Script:
`scripts/inkling/speed.py`. Greedy decoding. One warm-up call discarded. Other applications were
running on the machine; it was not isolated.

| measurement | result |
|---|---|
| load, weights already in file cache | 5.4 s |
| decode, 256 tokens, 3 passes | 18.2 ± 0.57 tok/s (n=5) |
| peak memory, short prompt | 17.4 GB |

| prompt tokens | prefill tok/s | decode after, tok/s | peak GB |
|---|---|---|---|
| 537 | 332.9 ± 2.9 (n=3) | 19.3 ± 0.14 | 18.8 |
| 2,073 | 372.9 ± 3.5 (n=3) | 19.6 ± 0.14 | 20.4 |
| 8,217 | 377.7 ± 1.6 (n=3) | 18.7 ± 1.04 | 20.7 |
| 32,793 | 339.2 (n=1) | 19.0 | 21.5 |

| loop passes | decode tok/s (n=3) | note |
|---|---|---|
| 1 | 45.3 ± 1.44 | off-distribution |
| 2 | 25.7 ± 1.22 | off-distribution |
| 3 | 18.2 ± 0.22 | trained setting |
| 4 | 14.1 ± 0.22 | off-distribution |
| 5 | 11.3 ± 0.09 | off-distribution |

**Reading.** Seconds per token rise by about 17 ms for each extra pass (22, 39, 55, 71, 88 ms),
so the looped core costs about 17 ms per pass and everything else about 5 ms. The spread on the
trained-setting decode is 3% of the mean across five runs; a speed difference smaller than that
is not a result on this machine.

**Limits.** The 32K prefill is a single run. The filler prompt is repeated text, which does not
affect timing but says nothing about quality at length. Pass counts other than 3 are speed
measurements only: the released checkpoint was trained at 3 passes and output quality at other
counts is unmeasured.

**Unverified.** The mlx-lm port (PR #2086) has not been compared against the reference
implementation, so these are the speeds of this port, not of the architecture.

## 2026-11-26 · Quality baseline (GSM8K, MMLU; unedited model)

`scripts/inkling/quality.py` → `results/quality_baseline.json` (summary) and
`results/quality_baseline.jsonl` (every item with raw output). Same model revision, port and
machine as the speed baseline. 100 items per dataset, fixed sample (`random.Random(0)`), greedy
decoding, 3 passes, cap of 2,048 generated tokens. "Minimum" is reasoning effort `none`;
"default" is the chat template's own default, 0.9. An item that reaches the cap without a final
answer is scored wrong.

| arm | correct | Wilson 95% | hit cap, no answer | correct among answered | mean tokens |
|---|---|---|---|---|---|
| GSM8K, minimum effort | 95/100 | 0.888–0.978 | 2 | 95/98 | 288 |
| GSM8K, default effort | 95/100 | 0.888–0.978 | 2 | 95/98 | 402 |
| MMLU, minimum effort | 81/100 | 0.722–0.875 | 8 | 81/92 | 539 |
| MMLU, default effort | 74/100 | 0.646–0.816 | 19 | 74/81 | 811 |

Determinism: the first five items of each arm, re-run, gave identical output in all four arms.

**Reading.**
- On GSM8K the effort setting changed nothing that was scored: the same 95 items are right in
  both arms and the same 2 hit the cap. Default effort spent 39% more tokens.
- On MMLU, default effort scored 7 points lower, and the whole gap is items that hit the cap
  (19 against 8; 7 items hit it in both). Paired: 9 items right only at minimum effort, 2 right
  only at default. Exact two-sided sign test on 11 discordant items, p = 0.065. That is not a
  demonstrated difference in accuracy at n=100; the difference in cap hits is the solid part.
- Among items that produced an answer, the ordering reverses (81/92 against 74/81). This is a
  comparison on different item subsets, so it shows nothing by itself.
- The capped items inspected (one per arm) are long deliberations that keep re-reading the
  question or re-listing candidate answers. Example: GSM8K test item 186 stalls in both arms on
  whether rabbits count as rodents.

**Limits.**
- The cap censors a tail rather than cleanly separating loops from long answers: the longest
  answered items used 1,416 to 2,015 tokens. Whether a capped item would have finished with a
  larger cap is unmeasured, so "19 loops" is not a claim made here.
- Only one capped item per arm was read. The share of capped items that are true repetition has
  not been counted.
- The intervals are wide. Two arms need to differ by roughly 12 points on MMLU before n=100
  separates them, which sets the size of effect a later edit must reach on this sample.
- Greedy decoding only. The model card's recommended sampling settings were not used.
- The port is unverified against the reference implementation (claim `port-faithful`).
