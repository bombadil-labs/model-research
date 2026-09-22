# Hour 61 — `exit`'s topic-matched controls on the dense pain axis

Spec: `conscription_prereg.md`, "Addendum, hour 61", written and committed before any activation
was extracted. Script: `scripts/shame_axis/conscription_exit_controls.py` (a sibling that imports
`conscription_pilot`; the hour-54 script is unedited). Data:
`results/conscription_pilot/exit_controls_contrasts.csv` (301 rows, 43 layers x 7 pairs),
`exit_controls_summary.json`, `exit_controls_extract_meta.json`. Test:
`tests/shame_axis/test_exit_controls.py`.

Everything measured here — rendering, extraction, the z-unit projection onto the externally
fitted pain axis, the static-embedding floor, the sign-flip band, the gain — is hour 54's code,
imported. The only new things are the two arms, the Holm correction over the addendum's family of
three, and the assertions that hour 54 did not move.

---

## 1. What was run

24 items x 2 new arms = **48 new prompts**, appended after the existing 168 rows.

| arm | the sentence that replaces the item closer | words | tokens |
|---|---|---|---|
| `exit` (hour 54) | "You're free to disagree with me about that." | 8 | 11 |
| `exit_b` (new) | "There's a window open in here this afternoon." | 8 | 11 |
| `exit_c` (new) | "Just so we're on the same page here." | 8 | 11 |

Checked rather than taken from the addendum: all three closers are 8 words and **11** gemma-2
tokens (the addendum says 12; that is a prose slip, and 11 is what this tokenizer gives with or
without a leading space). What actually matters held exactly — **for all 24 items the fully
rendered `exit`, `exit_b` and `exit_c` prompts have identical token length**, and for all 24 the
opener preceding the closer is byte-identical across the three arms and equal to `enact`'s opener.
So the three arms differ in the last eight words and in nothing else. — *my check, my reading.*

Row order, per the pilot's own append convention: rows 0–143 the six base arms item-major, rows
144–167 `neutral_b`, then rows **168–191 `exit_b`** and **192–215 `exit_c`**, arm-major, one arm
per 24-row shard. Two new shards, `grid_0168.npz` and `grid_0192.npz`.

## 2. Assertion outcomes

### The row-order assertions (the task's (i) and (ii))

| assertion | outcome |
|---|---|
| first 168 (item, arm) pairs == `extract_meta.json`'s recorded order, position for position | **PASS** (`order_matches_hour54: true`, `n_base: 168`, `n_total: 216`) |
| row 167 is the last `neutral_b`; the new arms come strictly after it | **PASS** |
| per-prompt text hashes of the first 168 unchanged | **PASS** on re-runs (`text_hashes_checked: true`). Hour 54 recorded no text hashes, so the *first* run of this script could only record them; that run reports `false` and the check is real only from the second run on. Said plainly rather than presented as a check that ran. |
| the seven hour-54 shards' size+mtime unchanged across extraction | **PASS** — `grid_0000 … grid_0144` byte-identical, fingerprints recorded in the meta |
| shards written by the extraction | `grid_0168.npz`, `grid_0192.npz` only |
| `d_acts`, `d_floor`, `gain` for (`enact`,`exit`) and (`neutral`,`neutral_b`) recomputed from the cached shards == `pilot_contrasts.csv` | **PASS, exactly, 86 of 86 cells** (43 layers x 2 pairs). These three columns are plain means with no rng, so this is an equality test, not a tolerance test. Also re-checked against a copy of `pilot_contrasts.csv` taken *before* anything was run. |
| `conscription_pilot.py analyze` re-run end-to-end | `pilot_contrasts.csv` and `summary.json` **byte-identical** to their pre-run copies; `extract_meta.json` never written |

*My reading:* the last two rows are the ones that carry the weight. The shards carry no labels of
their own — the row order **is** the labelling — so "hour 54 is unchanged" is exactly the claim
that its numbers still come out of the cached bytes unaltered, and they do, to the last decimal
place the CSV prints.

### How the run actually went, including the part that went wrong

The extraction that produced `grid_0168.npz` and `grid_0192.npz` completed on its **first
attempt**, 54 s per shard, 32 NDIF jobs; the deployment was not contended. The retry-with-backoff
loop (90 minute budget) was never needed after the first launch.

Two process notes, recorded because a silent version of either would be a defect:

* The first launch set `HF_HUB_OFFLINE=1`. CLAUDE.md scopes that flag to **local** runs; with it
  set, nnsight cannot resolve the model key against the hub and the job never leaves the machine.
  That attempt failed in 40 s with `OfflineModeIsEnabled` and was relaunched without the flag.
  `HF_HOME` still points at the repo cache, and `dispatch=False` means no weights are fetched.
* That first process survived its `SIGTERM` and, once the hub metadata was cached, ran again to
  completion with **every shard already on disk**. It extracted nothing — the fingerprint check
  confirms it — but it overwrote the meta's shard bookkeeping, which had been computed as a
  before/after set difference and so labelled the new shards as pre-existing. The bookkeeping is
  now derived from **position** (`hour54_shards()` = the shards at offsets < 168), which cannot
  drift on a re-run, and the meta records each hour-54 shard's size and mtime explicitly.

### The §7 extraction assertions

Same `painaxis_remote.extract_pooled` call as hour 54, `add_special_tokens=False`,
`batch_size=2`, `check_every=3`.

| §7 clause | outcome on the 48 new prompts |
|---|---|
| 1. padding convention read back off the remote tokenizer, `end_relative` | **PASS** — `padding_side: left` |
| 2. batched-vs-single equivalence on the **shortest** (maximally padded) item of every third batch | **PASS** — 32 comparisons (rows 1, 6, 12, 19 of each new shard x `mean@mid`, `mean@last`, `final_token@mid`, `embed_mean`), **min cos 0.999950, max 1.000000**, threshold 0.999 |
| 3. non-empty spans for both readouts of every row | **PASS** (would have raised) |
| 4. block output resolved **by type**, never `output[0]` (h36) | in force, inline in `_pooled_job` |
| 5. in-trace vs offline pooling cross-check | **NOT RUN, by construction.** `cross_check_against_asserted_path` refuses chat-rendered text — the offline path re-tokenises with `add_special_tokens=True` and would compare two different token sequences. Hour 54 did not run it either; it is run once per model on the raw stimuli in `painaxis_scenarios`. Recorded as absent rather than implied. |
| degenerate-offset guard on every rendered prompt (`verify_offsets_cover_template`) | **PASS** — all 216 rows, including the 168 re-rendered hour-54 ones |
| non-finite values in any capture | none |

Deployment as reported by NDIF: `google/gemma-2-9b-it`, `HOT`, pinned. Local libs: torch
2.14.0+cu130, transformers 5.17.0, nnsight 0.7.0, numpy 2.5.3.

**No patching anywhere in this run**, so CLAUDE.md non-negotiable 2 (pass-through arm) does not
attach — the addendum says so and it is correct: the whole run is the no-patch arm. The
`emb` layer serves as the free arithmetic check demanded by non-negotiable 1's spirit: at `emb`
the treatment *is* the floor, so the gain must be exactly 0 — **it is, +0.0000, for all seven
pairs**.

## 3. The tables

Units: scenario-pool z. `gain = d_acts − d_floor`, the floor being the static-embedding bag read
through the same axis recipe. Band: sign-flip over the 24 items, 5000 draws. Holm: over the
**three pre-registered pairs, within a layer**. **No layer is selected** — the CSV carries all 43
layers (emb + blocks 0–41); the L10–17 window is printed because hour 54 printed it, and that
window was fixed on the paper's stimuli, not on this grid.

```
--- PRE-REGISTERED ------------------------------------------------------------------------------------------
  L pair                   d_acts  d_floor     gain           gain band       p  Holm p clears
 10 exit - exit_c         +0.2092  +0.2807  -0.0715 [-0.0519,+0.0507]  0.0022  0.0044    yes
 10 exit - exit_b         +0.5664  +0.5862  -0.0198 [-0.0546,+0.0516]  0.4814  0.4814     no
 10 exit_c - enact        +0.3102  -0.0490  +0.3592 [-0.1662,+0.1637]  0.0000  0.0000    yes

 11 exit - exit_c         +0.2539  +0.2807  -0.0268 [-0.0427,+0.0421]  0.2312  0.2312     no
 11 exit - exit_b         +0.7690  +0.5862  +0.1828 [-0.1020,+0.1030]  0.0000  0.0000    yes
 11 exit_c - enact        +0.4305  -0.0490  +0.4795 [-0.2281,+0.2282]  0.0000  0.0000    yes

 12 exit - exit_c         +0.6340  +0.2807  +0.3533 [-0.1509,+0.1544]  0.0000  0.0000    yes
 12 exit - exit_b         +0.8854  +0.5862  +0.2993 [-0.1339,+0.1389]  0.0000  0.0000    yes
 12 exit_c - enact        +0.1929  -0.0490  +0.2419 [-0.1387,+0.1367]  0.0000  0.0000    yes

 13 exit - exit_c         +0.7003  +0.2807  +0.4196 [-0.1846,+0.1776]  0.0000  0.0000    yes
 13 exit - exit_b         +1.1723  +0.5862  +0.5861 [-0.2510,+0.2559]  0.0000  0.0000    yes
 13 exit_c - enact        +0.4252  -0.0490  +0.4742 [-0.2212,+0.2153]  0.0000  0.0000    yes

 14 exit - exit_c         +0.3153  +0.2807  +0.0346 [-0.0721,+0.0700]  0.3598  0.3598     no
 14 exit - exit_b         +0.8322  +0.5862  +0.2460 [-0.1286,+0.1303]  0.0000  0.0000    yes
 14 exit_c - enact        +0.4673  -0.0490  +0.5163 [-0.2408,+0.2383]  0.0000  0.0000    yes

 15 exit - exit_c         +0.0768  +0.2807  -0.2039 [-0.1124,+0.1107]  0.0000  0.0000    yes
 15 exit - exit_b         +0.7129  +0.5862  +0.1267 [-0.1052,+0.0997]  0.0144  0.0144    yes
 15 exit_c - enact        +0.5317  -0.0490  +0.5807 [-0.2580,+0.2629]  0.0000  0.0000    yes

 16 exit - exit_c         +0.1261  +0.2807  -0.1546 [-0.1173,+0.1155]  0.0062  0.0062    yes
 16 exit - exit_b         +1.7023  +0.5862  +1.1161 [-0.4681,+0.4781]  0.0000  0.0000    yes
 16 exit_c - enact        +1.2527  -0.0490  +1.3017 [-0.5452,+0.5439]  0.0000  0.0000    yes

 17 exit - exit_c         +0.0750  +0.2807  -0.2057 [-0.1418,+0.1430]  0.0034  0.0034    yes
 17 exit - exit_b         +1.1041  +0.5862  +0.5179 [-0.2382,+0.2349]  0.0000  0.0000    yes
 17 exit_c - enact        +1.0679  -0.0490  +1.1169 [-0.4611,+0.4724]  0.0000  0.0000    yes

--- CONTINUITY ----------------------------------------------------------------------------------------------
  L pair                   d_acts  d_floor     gain           gain band       p  Holm p clears
 10 enact - exit_b        +0.0470  +0.3545  -0.3075 [-0.1400,+0.1391]  0.0000       -    yes
 10 enact - exit_c        -0.3102  +0.0490  -0.3592 [-0.1630,+0.1596]  0.0000       -    yes
 10 enact - exit          -0.5194  -0.2317  -0.2877 [-0.1449,+0.1411]  0.0002       -    yes

 11 enact - exit_b        +0.0846  +0.3545  -0.2699 [-0.1463,+0.1566]  0.0002       -    yes
 11 enact - exit_c        -0.4305  +0.0490  -0.4795 [-0.2285,+0.2347]  0.0000       -    yes
 11 enact - exit          -0.6844  -0.2317  -0.4527 [-0.2391,+0.2368]  0.0000       -    yes

 12 enact - exit_b        +0.0585  +0.3545  -0.2960 [-0.1575,+0.1594]  0.0000       -    yes
 12 enact - exit_c        -0.1929  +0.0490  -0.2419 [-0.1397,+0.1379]  0.0000       -    yes
 12 enact - exit          -0.8269  -0.2317  -0.5952 [-0.2617,+0.2593]  0.0000       -    yes

 13 enact - exit_b        +0.0469  +0.3545  -0.3076 [-0.1512,+0.1498]  0.0000       -    yes
 13 enact - exit_c        -0.4252  +0.0490  -0.4742 [-0.2186,+0.2160]  0.0000       -    yes
 13 enact - exit          -1.1254  -0.2317  -0.8937 [-0.3806,+0.3867]  0.0000       -    yes

 14 enact - exit_b        +0.0496  +0.3545  -0.3049 [-0.1496,+0.1469]  0.0000       -    yes
 14 enact - exit_c        -0.4673  +0.0490  -0.5163 [-0.2333,+0.2342]  0.0000       -    yes
 14 enact - exit          -0.7826  -0.2317  -0.5509 [-0.2576,+0.2481]  0.0000       -    yes

 15 enact - exit_b        +0.1044  +0.3545  -0.2501 [-0.1319,+0.1359]  0.0000       -    yes
 15 enact - exit_c        -0.5317  +0.0490  -0.5807 [-0.2608,+0.2534]  0.0000       -    yes
 15 enact - exit          -0.6085  -0.2317  -0.3768 [-0.1920,+0.1906]  0.0000       -    yes

 16 enact - exit_b        +0.3235  +0.3545  -0.0310 [-0.1274,+0.1269]  0.6456       -     no
 16 enact - exit_c        -1.2527  +0.0490  -1.3017 [-0.5600,+0.5526]  0.0000       -    yes
 16 enact - exit          -1.3788  -0.2317  -1.1471 [-0.4820,+0.4891]  0.0000       -    yes

 17 enact - exit_b        -0.0388  +0.3545  -0.3933 [-0.2302,+0.2287]  0.0006       -    yes
 17 enact - exit_c        -1.0679  +0.0490  -1.1169 [-0.4727,+0.4705]  0.0000       -    yes
 17 enact - exit          -1.1429  -0.2317  -0.9112 [-0.3863,+0.3807]  0.0000       -    yes

--- FLOOR (hour 54's rewording floor, `neutral - neutral_b`) -------------------------------------------------
  L pair                   d_acts  d_floor     gain           gain band       p  Holm p clears
 10 neutral - neutral_b   +0.1176  -0.0410  +0.1585 [-0.1463,+0.1512]  0.0374       -    yes
 11 neutral - neutral_b   +0.1090  -0.0410  +0.1500 [-0.1635,+0.1658]  0.0770       -     no
 12 neutral - neutral_b   -0.0031  -0.0410  +0.0379 [-0.1296,+0.1312]  0.5890       -     no
 13 neutral - neutral_b   -0.0200  -0.0410  +0.0210 [-0.1489,+0.1479]  0.7932       -     no
 14 neutral - neutral_b   +0.0152  -0.0410  +0.0562 [-0.1479,+0.1498]  0.4732       -     no
 15 neutral - neutral_b   +0.0318  -0.0410  +0.0728 [-0.1762,+0.1776]  0.4446       -     no
 16 neutral - neutral_b   +0.0542  -0.0410  +0.0952 [-0.1596,+0.1585]  0.2620       -     no
 17 neutral - neutral_b   -0.0554  -0.0410  -0.0144 [-0.1432,+0.1498]  0.8488       -     no

--- emb (the free check: at emb the treatment IS the floor, so gain must be 0) -------------------------------
  L pair                   d_acts  d_floor     gain           gain band       p  Holm p clears
emb exit - exit_c         +0.2807  +0.2807  +0.0000 [+0.0000,+0.0000]  1.0000  1.0000     no
emb exit - exit_b         +0.5862  +0.5862  +0.0000 [+0.0000,+0.0000]  1.0000  1.0000     no
emb exit_c - enact        -0.0490  -0.0490  +0.0000 [+0.0000,+0.0000]  1.0000  1.0000     no
emb enact - exit_b        +0.3545  +0.3545  +0.0000 [+0.0000,+0.0000]  1.0000       -     no
emb enact - exit_c        +0.0490  +0.0490  +0.0000 [+0.0000,+0.0000]  1.0000       -     no
emb enact - exit          -0.2317  -0.2317  +0.0000 [+0.0000,+0.0000]  1.0000       -     no
emb neutral - neutral_b   -0.0410  -0.0410  +0.0000 [+0.0000,+0.0000]  1.0000       -     no
```

## 4. The addendum's prediction table, evaluated at each window layer

The addendum states the three predictions in words and gives no numeric rule. **The
operationalisation below is mine**, stated so it can be disagreed with:

* **at floor** — Holm-adjusted gain p ≥ 0.05 **and** |gain| ≤ |gain(`neutral`,`neutral_b`)| at the
  same layer. Both halves.
* **above floor** — Holm-adjusted gain p < 0.05 **and** |gain| > that same floor magnitude.
* **ambiguous** — anything else (e.g. clears the band but is smaller than the rewording floor).
* the "+0.9 to +1.1 z" band for `exit_c − enact` is read on **gain**, because hour 54's
  −1.15 / −0.91 at L16–17 are gain, not `d_acts`. And because that band *was* hour 54's value at
  L16–17 only, the ratio to hour 54's own `exit − enact` **at the same layer** is reported beside
  it; that ratio is what "≈ hour 54's `exit − enact`" means at L10–15.

```
  L prediction row            gain    floor   Holm p  sign      verdict  notes
 10 exit - exit_c          -0.0715   0.1585   0.0044     -    ambiguous
 10 exit - exit_b          -0.0198   0.1585   0.4814     -     at floor  exit higher: no
 10 exit_c - enact         +0.3592   0.1585   0.0000     +  above floor  h54 exit-enact +0.2877, ratio 1.25x; in +0.9..+1.1: no; ~0: no
 11 exit - exit_c          -0.0268   0.1500   0.2312     -     at floor
 11 exit - exit_b          +0.1828   0.1500   0.0000     +  above floor  exit higher: YES
 11 exit_c - enact         +0.4795   0.1500   0.0000     +  above floor  h54 exit-enact +0.4527, ratio 1.06x; in +0.9..+1.1: no; ~0: no
 12 exit - exit_c          +0.3533   0.0379   0.0000     +  above floor
 12 exit - exit_b          +0.2993   0.0379   0.0000     +  above floor  exit higher: YES
 12 exit_c - enact         +0.2419   0.0379   0.0000     +  above floor  h54 exit-enact +0.5952, ratio 0.41x; in +0.9..+1.1: no; ~0: no
 13 exit - exit_c          +0.4196   0.0210   0.0000     +  above floor
 13 exit - exit_b          +0.5861   0.0210   0.0000     +  above floor  exit higher: YES
 13 exit_c - enact         +0.4742   0.0210   0.0000     +  above floor  h54 exit-enact +0.8937, ratio 0.53x; in +0.9..+1.1: no; ~0: no
 14 exit - exit_c          +0.0346   0.0562   0.3598     +     at floor
 14 exit - exit_b          +0.2460   0.0562   0.0000     +  above floor  exit higher: YES
 14 exit_c - enact         +0.5163   0.0562   0.0000     +  above floor  h54 exit-enact +0.5509, ratio 0.94x; in +0.9..+1.1: no; ~0: no
 15 exit - exit_c          -0.2039   0.0728   0.0000     -  above floor
 15 exit - exit_b          +0.1267   0.0728   0.0144     +  above floor  exit higher: YES
 15 exit_c - enact         +0.5807   0.0728   0.0000     +  above floor  h54 exit-enact +0.3768, ratio 1.54x; in +0.9..+1.1: no; ~0: no
 16 exit - exit_c          -0.1546   0.0952   0.0062     -  above floor
 16 exit - exit_b          +1.1161   0.0952   0.0000     +  above floor  exit higher: YES
 16 exit_c - enact         +1.3017   0.0952   0.0000     +  above floor  h54 exit-enact +1.1471, ratio 1.14x; in +0.9..+1.1: no; ~0: no
 17 exit - exit_c          -0.2057   0.0144   0.0034     -  above floor
 17 exit - exit_b          +0.5179   0.0144   0.0000     +  above floor  exit higher: YES
 17 exit_c - enact         +1.1169   0.0144   0.0000     +  above floor  h54 exit-enact +0.9112, ratio 1.23x; in +0.9..+1.1: no; ~0: no
```

### Verdict per prediction, per layer

| prediction | topic-pull column says | clause-special column says | what happened |
|---|---|---|---|
| `exit − exit_c` | at the floor | above the floor | **neither cleanly.** At floor at L11 and L14; ambiguous at L10; above floor at L12, L13 (**+**, exit higher) and at L15, L16, L17 (**−**, exit_c higher). The sign reverses inside the window. |
| `exit − exit_b` | above the floor, `exit` higher | either | **above the floor with `exit` higher at 7 of 8 window layers** (L11–L17); at floor at L10. The topic-pull column's prediction, satisfied. Uninformative between the two columns by the addendum's own admission ("either"). |
| `exit_c − enact` | ≈ hour 54's `exit − enact`, +0.9 to +1.1 z | ≈ 0 | **≈ hour 54's, never ≈ 0.** Positive and clearing at all 8 window layers, ratio to hour 54's own `exit − enact` at the same layer 0.41–1.54x, **1.14x at L16 and 1.23x at L17** — hour 54's headline layers. Literal band membership (+0.9..+1.1) is `no` at every layer, L17's +1.1169 missing by 0.017 and L16's +1.3017 overshooting. |

Across all 42 blocks, `exit_c − enact` is positive and clears its band at **40 of 42**, and its
peak, **+1.3017, falls at L16 — the same layer where hour 54's `exit − enact` peaked** (+1.1471).
Median ratio over the 33 blocks where hour 54's contrast exceeds 0.1 in magnitude: **1.13x**.

## 5. What I take from it — every sentence in this section is my reading, not the addendum's

**Hour 54's `exit`-high is topic-pull, and the permission clause is not what produced it.** A
sentence with no permission content whatsoever — "Just so we're on the same page here." —
reproduces the whole of hour 54's `exit − enact` separation, at the same peak layer, at 1.1–1.2
times the size. Prediction 3 was written to discriminate exactly this and it discriminates
decisively: `exit_c − enact` is nowhere near zero at any layer in the window or out of it.

**But `exit − exit_c` is not at the floor either, and the prereg had no slot for what it does.**
It clears Holm at 6 of 8 window layers, and the sign *reverses* across the window: `exit` is above
`exit_c` at L12–13 (+0.35, +0.42) and `exit_c` is above `exit` at L15–17 (−0.20, −0.15, −0.21).
The addendum's binary — "at the floor" or "above the floor" — cannot express a residual that
changes sign. I do not think this rescues the permission clause: at hour 54's own headline layers
the clause makes the readout *lower*, which is the opposite of what "permission is special and
raises the pain readout" would need. My reading is that after the topic-pull is accounted for, the
last eight words leave a small, layer-dependent residue that the addendum's own caveat covers —
"a result about what the last eight words do to a lexical-plus-boundary direction" — and that
reading a sign-reversing ±0.2 z residue as a semantic fact about permission would be exactly the
overreach this line has retracted before.

**The residue is small against the headline, but not against the rewording floor.** `exit − exit_c`
peaks at |0.21| in the window; hour 54's `exit − enact` peaks at 1.15. So at most ~18% of the
hour-54 number survives the topic-matched control, and that fraction does not have a stable sign.
The rewording floor (`neutral − neutral_b`) runs 0.02–0.16 over the window and clears its band at
only 1 of 8 layers, so it is doing its job — it is small — but at L10–11 it is 0.15, comparable to
the entire `exit − exit_c` residue, which is why L10 comes out "ambiguous" and why I would not
lean on any window layer where the floor and the effect are the same size.

## 6. Surprising, and recorded because it is

1. **`exit_b` — the inert sentence — sits *above* `enact` on the dense axis**, by 0.25–0.31 z at
   L10–15 (`enact − exit_b` is negative and clears at every one of those layers). Hours 55/56/59b
   found the opposite on the behavioural opener readout, where `exit_b` sat **4 below** `enact`.
   *My reading:* the two readouts disagree in sign about the same stimulus. That is a fact about
   the instruments, not about conscription, and it belongs in the ledger. It also means the dense
   axis is not simply a quiet version of the opener readout, and results from one should not be
   narrated as if they were results from the other.
2. **L16 is where everything is largest for every arm.** `exit − exit_b` +1.12, `exit_c − enact`
   +1.30, hour 54's `exit − enact` +1.15 — while `enact − exit_b` at L16 is the one continuity
   cell in the window that does *not* clear (+p 0.65). *My reading:* whatever L16 amplifies, it
   amplifies the last-eight-words difference, not the arm semantics. A single-layer story told at
   L16 would be a story about L16.
3. **`exit − exit_c` peaks far outside the window**, at **L4, +0.91**, larger than anything it does
   at L10–17. It is significantly POSITIVE at every block 0–9 and at L12–13, and significantly
   NEGATIVE at L10 and at every block from L15 to L41 except L22. *My reading:* this is a curve with structure that the L10–17 window was never
   chosen to capture; reporting only the window would have hidden it. Reported because
   non-negotiable 4 says report the curve. The full curve is in the CSV.
4. The addendum's "12 tokens" for the three closers is 11 on this tokenizer. Harmless, and the
   property that mattered (equal length across the three arms, per item, after templating) holds
   exactly.

## 7. What this cannot show

The addendum's own paragraph stands unchanged and I have nothing to add to it: two sentences,
machine-written; the axis is 63% lexical; a topic-pull result here is a result about what the last
eight words do to a lexical-plus-boundary direction, and says nothing further about escalation,
which is already falsified where behaviour was measured. One further limit of my own: `exit_c` was
written to be on-topic and non-permissive, and whether it succeeds at "non-permissive" is my
judgement about my own sentence, not a measurement.
