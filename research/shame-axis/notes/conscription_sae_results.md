# Results: do the pain features fire on false attribution, or on correction-shaped turns?

Runs `research/shame-axis/notes/conscription_sae_prereg.md` exactly as pre-registered. Hour 58.

- Script: `scripts/shame_axis/conscription_sae.py` (offline; no NDIF, no network, nothing patched).
- Data: hour-54 conscription stacks (`research/shame-axis/results/conscription_pilot/shards/grid_*.npz`,
  `final_token`, 24 items x 7 arms = 168 rows) and the hour-53/57 scenario stacks (500 PAIN+CONTROL).
- Output: `research/shame-axis/results/conscription_sae/summary.json`, `.../per_item.csv` (2184 rows).
- Tests: `tests/shame_axis/test_conscription_sae.py` (3, no SAE needed).

**Every sentence marked `[Agent reading]` is this agent's interpretation, not a measured result.**
Everything not so marked is a number produced by the script or a statement of what the
pre-registration declared.

## 0. The row -> (item, arm) map, asserted not assumed

The shards are indexed by position and carry no labels. The order is derived from the code that
wrote them (`conscription_pilot.render_all`: per item the five design arms `enact, report, exit,
true, neutral` then `enact_norecord`; then one `neutral_b` per item appended after all of those),
checked against the extraction's own `extract_meta.json["order"]`, and asserted: 168 rows, 24
distinct items, 7 arms each, no duplicates. The script refuses to label a row if any of that fails.

## 1. Gate A, on the conscription activations

FVU is against the origin, as in `painaxis_pruning.run_point`. Pass requires all three: FVU < 0.35,
argmin over L+-2 at the SAE's own index, achieved L0 within 25% of advertised.

| point | FVU @ L | argmin L+-2 | achieved L0 | advertised | off by | gate A |
|---|---|---|---|---|---|---|
| L9 16k l0=47 | 0.1401 | 9 | 18.6 | 47 | 60.3% | **FAIL** |
| L20 16k l0=47 | 0.1481 | 20 | 31.7 | 47 | 32.6% | **FAIL** |
| L31 16k l0=43 | 0.2107 | 31 | 53.1 | 43 | 23.6% | **PASS** |

FVU by index: L9 — 7:0.2438 8:0.2362 **9:0.1401** 10:0.2962 11:0.2855; L20 — 18:0.2641 19:0.2086
**20:0.1481** 21:0.2109 22:0.2228; L31 — 29:0.2821 30:0.2617 **31:0.2107** 32:0.2551 33:0.2741.

L9 and L20 are computed in full below and **marked uninterpretable**, per the pre-registration.
Both fail on achieved L0 only; the capture convention (argmin) is right at all three points.

**[Agent reading]** The L0 failure is a distribution-shift failure, not a plumbing failure: these
SAEs hit their advertised L0 on the scenario sentences (47.4, 47.1, 46.7 against 47/47/43) and miss
it on multi-turn chat prompts (18.6, 31.7, 53.1). L31 is the only point where a chat turn excites
the dictionary about as much as the sentences it was checked on, and it is also the only point that
passes — at 23.6%, one point inside the threshold.

## 2. Carry-over check (the readout is the hour-57 one, not a new fit)

The pre-registration states plainly that there is no positive control inside the conscription data.
What can be checked is that the readout was carried over intact. Recomputed on the scenario set
through this script's code:

| L31 feature | pain (here) | control (here) | pain (hour 57) | control (hour 57) |
|---|---|---|---|---|
| 10008 | 0.660 | 0.093 | 0.66 | 0.09 |
| 13134 | 0.615 | 0.120 | 0.61 | 0.12 |

The top 5 by \|d\| at L31 on the scenario set is `[10008, 13134, 3519, 3098, 15449]`. **The
pre-registered assertion holds**: 10008 is rank 0 and 13134 is rank 1 of 16,384.

| point | achieved L0 scenario / conscription | mean \|resid\| scenario / conscription | top-5 firing anywhere on the 168 rows | top-500 firing anywhere |
|---|---|---|---|---|
| L9 | 47.4 / 18.6 | 128.0 / 98.5 | 1 / 5 | 44 / 500 |
| L20 | 47.1 / 31.7 | 258.4 / 271.7 | 2 / 5 | 66 / 500 |
| L31 | 46.7 / 53.1 | 485.3 / 533.0 | 3 / 5 | 99 / 500 |

## 3. Per-arm means

`top5` and `full` are projections onto the scenario-set difference-in-means direction, normalised by
the L2 norm of the weights used. `random5` is the random arm (see §7).

**L31 16k l0=43 (the only interpretable point)**

| arm | top5 | full | random5 | 10008 act | 10008 fired | 13134 act | 13134 fired |
|---|---|---|---|---|---|---|---|
| enact | -0.9099 | -6.0511 | 0.0000 | 0.0000 | 0.000 | 0.0000 | 0.000 |
| report | 0.3189 | -4.6604 | 0.0000 | 0.5708 | 0.042 | 0.0000 | 0.000 |
| exit | -2.2568 | -7.2065 | 0.0000 | 0.0000 | 0.000 | 0.0000 | 0.000 |
| true | 0.0000 | -1.5583 | 0.0000 | 0.0000 | 0.000 | 0.0000 | 0.000 |
| neutral | 0.1995 | -4.1110 | 0.0000 | 0.0000 | 0.000 | 0.0000 | 0.000 |
| enact_norecord | -0.1983 | -15.1922 | 0.0000 | 0.0000 | 0.000 | 0.0000 | 0.000 |
| neutral_b | 0.0000 | -4.0797 | 0.0000 | 0.0000 | 0.000 | 0.0000 | 0.000 |

Items (of 24) on which each readout is nonzero at L31: `top5` — enact 4, report 1, exit 9, true 0,
neutral 1, enact_norecord 1, neutral_b 0. `full` — 24 on every arm. The named-feature readouts and
`random5` — 0 on every arm except 10008 on one `report` item.

**L20 16k l0=47 (gate A FAILED — not interpretable)**

| arm | top5 | full |
|---|---|---|
| enact | -17.6527 | -10.4724 |
| report | -19.0239 | -11.3421 |
| exit | -16.3148 | -10.2306 |
| true | -13.8496 | -8.2556 |
| neutral | -18.3410 | -11.3058 |
| enact_norecord | -32.1141 | -18.6874 |
| neutral_b | -16.7390 | -10.1215 |

**L9 16k l0=47 (gate A FAILED — not interpretable)**

| arm | top5 | full |
|---|---|---|
| enact | -19.9096 | -13.0573 |
| report | -21.4430 | -14.0071 |
| exit | -20.6500 | -13.4848 |
| true | -19.6333 | -12.8786 |
| neutral | -19.6988 | -12.9317 |
| enact_norecord | -23.1098 | -15.2490 |
| neutral_b | -20.0925 | -13.2038 |

## 4. The floor: the declared-zero pair `neutral - neutral_b`

The pre-registration: "What this data *does* carry is the declared-zero pair: `neutral - neutral_b`
must sit on its null. If it does not, the floor is broken."

| point | readout | mean | null sd | p | status |
|---|---|---|---|---|---|
| L9 | top5 | +0.3937 | 0.1500 | 0.0060 | **OFF ITS NULL — FLOOR BROKEN** |
| L9 | full | +0.2721 | 0.1067 | 0.0084 | **OFF ITS NULL — FLOOR BROKEN** |
| L20 | top5 | -1.6019 | 0.9082 | 0.0758 | on its null |
| L20 | full | -1.1843 | 0.5996 | 0.0393 | **OFF ITS NULL — FLOOR BROKEN** |
| **L31** | **top5** | **+0.1995** | **0.1995** | **1.0000** | **on its null** |
| **L31** | **full** | **-0.0314** | **0.6270** | **0.9634** | **on its null** |
| L31 | 10008 act / fired, 13134 act / fired | 0 | 0 | 1.0000 | degenerate: every paired difference is exactly 0 |
| L9/L20/L31 | random5 | 0 | 0 | 1.0000 | degenerate: every paired difference is exactly 0 |

Items (of 24) on which the floor's paired difference is nonzero: L9 top5 24, L9 full 24, L20 top5
23, L20 full 24, **L31 top5 1**, L31 full 24.

**[Agent reading]** The floor is intact at L31 on both live readouts and broken at L9 (both) and at
L20 (`full`). Those three cells are unusable on the pre-registration's own terms independently of
gate A, and I would not read the L9/L20 numbers even if their L0 had passed. **[Agent reading]** I
would also not lean on L31 `top5`'s floor: it is "on its null" at p = 1.0000 because exactly one of
24 items moves at all, so that floor is an estimate from a single item and is nearly as uninformative
as the degenerate rows beneath it. L31 `full` is the only cell in this table with a floor I would
call measured.

## 5. THE PRIMARY CONTRAST, `enact - true`, against both pre-registered predictions

Pre-registered predictions: **turn-shape account — at the floor**; **conscription account — above
the floor and outside the null**. The conscription account's direction is stated in the
pre-registration as "false attribution adds something the self-correction lacks", i.e. `enact - true`
positive. Floor = mean \|`neutral - neutral_b`\| differences. Null = 10,000 seeded sign flips.

| point | readout | mean | floor | null sd | p | verdict |
|---|---|---|---|---|---|---|
| L9 | top5 | -0.2763 | 0.6203 | 0.1799 | 0.1311 | TURN-SHAPE (at floor, on null) — *gate A FAILED, floor broken* |
| L9 | full | -0.1787 | 0.4546 | 0.1183 | 0.1350 | TURN-SHAPE (at floor, on null) — *gate A FAILED, floor broken* |
| L20 | top5 | -3.8030 | 3.4526 | 1.3465 | 0.0021 | NEITHER: clears floor and null with the WRONG SIGN — *gate A FAILED* |
| L20 | full | -2.2168 | 2.2140 | 0.8374 | 0.0039 | NEITHER: clears floor and null with the WRONG SIGN — *gate A FAILED, floor broken* |
| **L31** | **top5** | **-0.9099** | **0.1995** | **0.4567** | **0.1276** | **SPLIT: above floor, inside the null; only 4 of 24 items move** |
| **L31** | **full** | **-4.4928** | **2.2136** | **1.2607** | **0.0002** | **NEITHER: clears floor and null with the WRONG SIGN** |
| L31 | 10008 act | 0.0000 | 0.0000 | 0.0000 | 1.0000 | DEGENERATE: all 24 paired differences exactly 0 |
| L31 | 10008 fired | 0.0000 | 0.0000 | 0.0000 | 1.0000 | DEGENERATE: all 24 paired differences exactly 0 |
| L31 | 13134 act | 0.0000 | 0.0000 | 0.0000 | 1.0000 | DEGENERATE: all 24 paired differences exactly 0 |
| L31 | 13134 fired | 0.0000 | 0.0000 | 0.0000 | 1.0000 | DEGENERATE: all 24 paired differences exactly 0 |

Stated against each prediction at the one interpretable point, L31:

- **Turn-shape prediction (`enact - true` at the floor).** Not met on `full`: \|mean\| = 4.49
  against a floor of 2.21, p = 0.0002. Not met on `top5` either, on the floor half of the criterion
  (0.91 against 0.20), though `top5` stays inside its null (p = 0.13). **Not met on the named
  features, but only because they never fire** — see below.
- **Conscription prediction (`enact - true` above the floor AND outside the null).** The magnitude
  and significance criteria are met on `full` (above floor, p = 0.0002) and the magnitude criterion
  alone on `top5`. **The sign is the reverse of the one the account predicts on all three:** `enact`
  reads *less* pain-like than `true`, not more.
- **The named features 10008 and 13134 test neither prediction.** Their paired differences are
  exactly zero on all 24 items in every contrast, because the features do not fire on any
  conscription arm. A sign-flip null over 24 zeros has width zero and returns p = 1 by construction.
  That is the instrument reading itself (non-negotiable 3), not a null, and it is labelled
  DEGENERATE rather than scored.

**[Agent reading]** My reading is that the pre-registration's primary contrast **does not come out
for either account** on the readout that passes its gates. Neither prediction anticipated a
significant reversal, and "above the floor and outside the null" was written as the conscription
account's signature on the assumption that the excess would be positive. What the `full` readout
actually says is that the *self-correction* turn — the user correcting themselves, the assistant
having been right — sits highest on the scenario-derived pain direction, and the false attribution
sits lower. **[Agent reading]** I would not call that a win for the turn-shape account either: that
account predicted the two would be indistinguishable, and they are separated at p = 0.0002 on 24 of
24 items. The honest summary is a third outcome the pre-registration did not enumerate.

**[Agent reading]** I flag one specific reason for caution on `full` before anyone builds on the
reversal: `enact_norecord` reads -15.19 on a readout where the other six arms sit between -1.6 and
-7.2, and `enact_norecord` is the one arm with no prefix turns at all. That is a prompt-length /
prompt-structure difference the design does not control, and it tells me the `full` score is at
least partly tracking how much conversation precedes the read position. `enact` and `true` share a
prefix so the primary contrast is not exposed to that directly, but the readout's sensitivity to it
is a confound I would want measured before the reversal is believed.

## 6. Secondary family (Holm over four), and `report - enact` uncorrected

`sign` is against the direction the pre-registration declared; `--` where it declared none
(`exit - enact`: "no direction is declared here; the sign is the finding") or where the mean is
exactly zero.

**L31 `full` (gate A passes, floor intact)**

| contrast | mean | null sd | p | Holm p | vs floor 2.2136 | sign |
|---|---|---|---|---|---|---|
| enact - neutral | -1.9401 | 1.0722 | 0.0701 | 0.0760 | at/below | OPPOSITE |
| true - neutral | +2.5527 | 0.9565 | 0.0065 | **0.0195** | ABOVE | as predicted |
| enact - enact_norecord | +9.1411 | 2.2033 | 0.0000 | **0.0000** | ABOVE | as predicted |
| exit - enact | -1.1554 | 0.5634 | 0.0380 | 0.0760 | at/below | -- |
| *report - enact* (uncorrected) | +1.3907 | 0.9024 | 0.1242 | — | at/below | -- |

**L31 `top5` (gate A passes, floor intact)**

| contrast | mean | null sd | p | Holm p | vs floor 0.1995 | sign |
|---|---|---|---|---|---|---|
| enact - neutral | -1.1094 | 0.4998 | 0.0648 | 0.1944 | ABOVE | OPPOSITE |
| true - neutral | -0.1995 | 0.1995 | 1.0000 | 1.0000 | at/below | OPPOSITE |
| enact - enact_norecord | -0.7115 | 0.3832 | 0.1276 | 0.2552 | ABOVE | OPPOSITE |
| exit - enact | -1.3469 | 0.6503 | 0.0287 | 0.1148 | ABOVE | -- |
| *report - enact* (uncorrected) | +1.2288 | 0.5586 | 0.0663 | — | ABOVE | -- |

**L20 `full` — gate A FAILED, floor broken; recorded, not interpretable**

| contrast | mean | null sd | p | Holm p | vs floor 2.2140 | sign |
|---|---|---|---|---|---|---|
| enact - neutral | +0.8334 | 0.6539 | 0.2122 | 0.4244 | at/below | as predicted |
| true - neutral | +3.0502 | 0.9400 | 0.0002 | 0.0006 | ABOVE | as predicted |
| enact - enact_norecord | +8.2150 | 1.8720 | 0.0000 | 0.0000 | ABOVE | as predicted |
| exit - enact | +0.2418 | 0.7603 | 0.7634 | 0.7634 | at/below | -- |
| *report - enact* (uncorrected) | -0.8697 | 0.5406 | 0.1105 | — | at/below | -- |

**L20 `top5` — gate A FAILED; recorded, not interpretable**

| contrast | mean | null sd | p | Holm p | vs floor 3.4526 | sign |
|---|---|---|---|---|---|---|
| enact - neutral | +0.6883 | 1.1545 | 0.5604 | 0.6712 | at/below | as predicted |
| true - neutral | +4.4914 | 1.6023 | 0.0025 | 0.0075 | ABOVE | as predicted |
| enact - enact_norecord | +14.4614 | 3.2944 | 0.0000 | 0.0000 | ABOVE | as predicted |
| exit - enact | +1.3379 | 1.3506 | 0.3356 | 0.6712 | at/below | -- |
| *report - enact* (uncorrected) | -1.3713 | 0.9511 | 0.1553 | — | at/below | -- |

**L9 `full` / `top5` — gate A FAILED, floor broken; recorded, not interpretable**

| readout | contrast | mean | null sd | p | Holm p | vs floor | sign |
|---|---|---|---|---|---|---|---|
| full | enact - neutral | -0.1256 | 0.1213 | 0.3137 | 0.6274 | at/below (0.4546) | OPPOSITE |
| full | true - neutral | +0.0531 | 0.1294 | 0.6895 | 0.6895 | at/below | as predicted |
| full | enact - enact_norecord | +2.1917 | 0.4766 | 0.0000 | 0.0000 | ABOVE | as predicted |
| full | exit - enact | -0.4275 | 0.1430 | 0.0008 | 0.0024 | at/below | -- |
| full | *report - enact* (uncorrected) | -0.9498 | 0.2193 | 0.0000 | — | ABOVE | -- |
| top5 | enact - neutral | -0.2108 | 0.1828 | 0.2545 | 0.5090 | at/below (0.6203) | OPPOSITE |
| top5 | true - neutral | +0.0655 | 0.1894 | 0.7420 | 0.7420 | at/below | as predicted |
| top5 | enact - enact_norecord | +3.2002 | 0.6976 | 0.0000 | 0.0000 | ABOVE | as predicted |
| top5 | exit - enact | -0.7404 | 0.2203 | 0.0000 | 0.0000 | ABOVE | -- |
| top5 | *report - enact* (uncorrected) | -1.5334 | 0.3477 | 0.0000 | — | ABOVE | -- |

All four named-feature readouts at L31 return mean 0.0000, null sd 0.0000, p 1.0000, Holm 1.0000 on
every secondary contrast — degenerate, for the reason in §5. The one exception is `report - enact`
on `10008 act` (+0.5708) and `10008 fired` (+0.0417), which is one item.

**[Agent reading]** The one contrast that behaves the same way everywhere, at every layer and on
every live readout, is `enact - enact_norecord`: Holm p = 0.0000 at all three layers with the
predicted sign on `full`. **[Agent reading]** I do not think that is a conscription result. The
`enact_norecord` arm is the bare single user turn with no prefix at all, so this contrast confounds
"the visible record" with "there is a prior conversation", and §5's note about `enact_norecord`
reading -15.19 at L31 is the same observation. Hour 54's dense-axis +1.0 to +1.3 z for this pair
inherits the same confound.

## 7. Firing rates (reported without a prediction, as pre-registered)

Fraction of the 24 items on which the feature fires (> 0), L31 16k l0=43:

| feature | enact | report | exit | true | neutral | enact_norecord | neutral_b |
|---|---|---|---|---|---|---|---|
| 10008 | 0.000 | **0.042** | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |
| 13134 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 | 0.000 |

On the scenario set the same two features fire on 0.660 / 0.615 of pain items and 0.093 / 0.120 of
controls (§2, matching hour 57). On the conscription grid they fire on one of 168 rows.

**[Agent reading]** This is the result I would lead with. The pre-registration asked whether the
near-binary scenario behaviour is binary on conversational turns; the answer measured here is that
it is *absent* on conversational turns. **[Agent reading]** I see two readings and this data cannot
separate them: either these features encode something about the pain *sentences* (first-person
declaratives about one's own aversive state) that no arm of a conscription dialogue contains, or the
SAE's feature basis does not transfer from that stimulus class to multi-turn chat at all — and the
gate-A L0 shortfalls at L9 and L20, plus 99 of the scenario top-500 features firing anywhere on 168
chat rows at L31, are consistent with the second. **[Agent reading]** Either way, the specific
proposal in hour 57's write-up — that 10008 and 13134 are "a concrete target" for ablation, "the
causal bridge the line does not have" — cannot be tested on the conscription grid, because there is
nothing to ablate: the features are off in every arm.

## 8. Arms, nulls and what was not done

- **No-patch.** Nothing is patched anywhere in this script. The whole run is the no-patch arm, so
  non-negotiable 2's pass-through requirement does not attach to it.
- **Random arm.** `random5` — five features drawn uniformly (seed 20260922) with their own
  scenario-set weights. Not in the pre-registration; added because non-negotiable 1 requires a
  random arm in every battery. It reads exactly 0.0000 on all 168 rows at all three layers and is
  reported, never used to adjudicate. **[Agent reading]** It is a weak control: five features of
  16,384 at an L0 of ~50 are expected to be off on every row, so its sitting at its declared zero is
  close to guaranteed and tells us little. A random arm matched on firing rate rather than on count
  would be the better control and was not run.
- **Floor.** `neutral - neutral_b`, the declared-zero pair, reported first at every point (§4).
- **No positive control exists inside this data.** The pre-registration says so; §2's carry-over
  check is a check that the readout is hour 57's, not a control on this stimulus set.
- **No layer was selected on scoring data.** All three pre-registered points are reported whole,
  gates and all, including the two that fail.
- **Not done.** No ablation. No lexical control on the conscription arms. One model, n = 24,
  machine-authored items. The `enact_norecord` prefix-length confound named in §5 and §6 is
  identified here and not measured.

## 9. Judgment calls this note's author made that the pre-registration did not cover

1. **Degeneracy is flagged rather than scored.** A contrast whose 24 paired differences are all
   exactly zero gets a sign-flip null of width zero and p = 1. The pre-registration's decision rule
   would read that as "at the floor" and hence as support for the turn-shape account. It is labelled
   DEGENERATE instead, and the named-feature readouts are reported as untestable here.
2. **The primary verdict is scored with its sign.** The pre-registration's floor comparison is on
   \|mean\|, but its conscription prediction is directional. A contrast clearing the floor and the
   null in the reverse direction is reported as supporting NEITHER account rather than as
   conscription-shaped.
3. **Gate-A logic was reproduced, not imported.** It is inline in `painaxis_pruning.run_point` and
   not exposed as a function; extracting it would have meant editing that file, which was out of
   scope. `encode`, `decode`, `load_sae`, `load_core`, `PAIN` and `CONTROL` are imported, and the
   sign-flip null and Holm treatment come from `conscription_openers`.
4. **Holm is applied per (layer, readout).** The pre-registration names one family of four; that
   family is corrected within each layer-and-readout cell, not pooled across the 13 cells.
5. **The carry-over check in §2 was added** so that "the features do not fire here" can be told
   apart from "the readout was not carried over correctly".
