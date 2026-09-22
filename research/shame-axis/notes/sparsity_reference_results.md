# Results: the reference distribution for the pain axis's sparsity (hour 58)

Runs the pre-registration's **Addendum 2** (`sparsity_prereg.md`): the hour-57 pruning pipeline,
unchanged, applied to every binary split available on disk, so that pain's k90 can be located in a
reference distribution instead of read alone.

- script: `scripts/shame_axis/painaxis_sparsity_reference.py`
- rows: `research/shame-axis/results/painaxis_sparsity/reference.json` (105 = 35 contrasts x 3 SAEs)
- tests: `tests/shame_axis/test_sparsity_reference.py` (9, no SAE, 0.1 s)
- fully offline; nothing downloaded, NDIF untouched. Tokeniser read from `cache/hf`.

Pipeline, identical to hour 57 and imported from it rather than restated: `final_token`, 5 folds,
features ranked by |difference in means| on the train folds, held-out items scored with the top k
only, `painaxis_pruning.KS` as the k grid, `painaxis_pruning.pruning_curve` and `auc` as the
arithmetic. Three SAE points: layer 9 (16k, l0 47), layer 20 (16k, l0 47), layer 31 (16k, l0 43).

**Statistic.** Per contrast: full-dictionary held-out AUC, and `k90` = the smallest k in the grid
whose retention `(auc_k - 0.5) / (auc_full - 0.5)` reaches 0.90. `auc_full <= 0.65` -> `k90` null
and the contrast flagged `weak`; shown, not counted.

**Declared rule.** Sparsity is specific to a contrast only if its k90 is at or below the 10th
percentile of k90 among the non-weak contrasts whose full AUC is within +-0.05 of its own
(itself excluded).

## Contrasts

35 per SAE point, exactly the addendum's list, nothing added or removed:

- **core pool** (500 items, `load_core("final_token")`, restricted with `np.isin(cats, PAIN+CONTROL)`
  exactly as hour 57 did — which keeps all 500): `A1..A5, B, C1, C2, D, E` one-vs-rest (10), plus
  `pain` = A1–A5 vs B,C1,C2,D,E (1).
- **scenario pool** (420 items, chat-rendered, `scen_chat_*.npz`): the 21 categories one-vs-rest,
  `perspective`, `intensity`, and the nuisance contrast `prompt_length_tokens`.

### Row-to-scenario mapping, asserted not assumed

`scenario_order.json` is the extractor's own record of the ids it fed the model, in row order,
after dropping anything their validator rejected (`extract_meta.json` records **0** exclusions).
The five `scen_chat_*.npz` shards concatenate in sorted filename order to 420 rows; the order file
holds 420 ids; every id resolves in the 420-item scenario json; ids are unique. All four are
asserted in `align_scenarios`, and the assertion logic is tested on a synthetic order that is the
*reverse* of the json order — the case where assuming json order would silently mislabel every row.

## Judgment calls the addendum did not make (mine — MB was not consulted)

1. **`perspective` is `1P` vs `3P`, not a self/other field.** The addendum calls it "self vs other".
   The actual values in the metadata are `1P` (n=381) and `3P` (n=39) — heavily unbalanced. I ran
   `perspective` as declared, `1P` positive. *My note:* the field that actually reads self vs other
   in this file is `stratum` (`self_directed` 220 / `vicarious_empathic` 100 / `neutral_filler`
   100). I did **not** add it as a contrast, because the addendum fixes the contrast list; I flag it
   as the split a follow-up should run if "what the network adds over vocabulary" is the question.
   The 381/39 imbalance is also worth holding in mind when reading `perspective`'s AUC.
2. **`intensity` is categorical, 27 distinct values, and 100 of 420 items do not have the field.**
   "Top half vs bottom half" is not directly available. I used the four values that form an
   unambiguous ordinal scale — bottom = `mild` (56) + `moderate` (97) = 153, top = `high` (82) +
   `severe` (7) = 89 — and dropped the other 178 items from that contrast only. The pool median
   falls inside `moderate`, so this is the nearest tie-respecting median split. The other 23 values
   (`escalating`, `sarcastic`, `philosophical`, `nihilistic`, ...) are not orderable without my
   inventing an ordering, which would be a bigger judgment call than this one.
3. **Prompt length is counted on the raw `text` field** with the `gemma-2-9b-it` tokenizer and
   `add_special_tokens=False`, then split by rank into exactly 210/210. A constant offset (BOS, or
   the chat template's wrapper) cannot change a rank split, so the choice is inert; it is stated
   rather than left implicit. Ties break by row order (stable sort).
4. **The comparison band spans both pools.** The addendum asks for "one scatter of (full AUC, k90)
   per SAE layer, every contrast a point", so the +-0.05 band at a layer is drawn from all 34 other
   contrasts at that layer, core and scenario alike. An alternative reading — band within pool —
   would shrink n_band to single digits and is not what the addendum says.
5. **Folds are drawn once per pool per layer** and reused across contrasts at that point, so the
   contrasts at one layer are compared on the same split rather than on 35 different ones.

## Gate outcomes

Gate B (the corrected plant: alpha 0.2 * mean ||x|| of one decoder column into half the core-pool
controls) **passes at all three points**, at k = 1, AUC 1.000 every time.

| SAE | gate A core | gate A scenario | gate B |
|---|---|---|---|
| L9 16k l0=47 | pass — fvu 0.201, argmin 9, L0 47.4 vs 47 | **FAIL** — fvu 0.124, argmin 9, **L0 24.4 vs 47** | pass (k=1 AUC 1.000, feature 9233) |
| L20 16k l0=47 | pass — fvu 0.212, argmin 20, L0 47.1 vs 47 | pass — fvu 0.126, argmin 20, L0 37.1 vs 47 | pass (k=1 AUC 1.000, feature 14789) |
| L31 16k l0=43 | pass — fvu 0.153, argmin 31, L0 46.7 vs 43 | **FAIL** — fvu 0.221, argmin 31, **L0 54.9 vs 43** | pass (k=1 AUC 1.000, feature 6560) |

**The scenario pool fails gate A at two of three points, on the L0 clause only.** Reconstruction is
fine everywhere (FVU 0.12–0.22, always best at the SAE's own index; the scenario pool reconstructs
*better* than the core pool at L9 and L20). What fails is sparsity of the code itself: the
chat-rendered read position fires 24.4 features at L9 (48% below advertised) and 54.9 at L31 (28%
above). Per the pre-registration, **every scenario-pool contrast at L9 and L31 is uninterpretable**
and is printed for the record only. The scenario pool at **L20** is the one interpretable scenario
point; the core pool is interpretable at all three.

*My reading, labelled as mine:* this is not an off-by-one — the argmin lands on the SAE's own index
at every point, and the core pool passes the same check at the same index in the same run. It is a
property of the read position. The scenario read position is the token where the assistant would
begin replying (`<start_of_turn>model`), a structural control token, not a content token; a
template position carrying few active features early and many late is a plausible thing for it to
do, and the L0 clause of the amended gate A — calibrated on short declarative sentences — is what
notices. I would not call this a broken instrument; I would call it a gate doing its job on a pool
it was not calibrated for. Either way it is not mine to reinterpret away, so the rows stay marked.

## The scatter, per layer

Sorted by full-dictionary held-out AUC, descending. `k90` reads `— (weak)` when `auc_full <= 0.65`.
At L9 and L31 every `scenario` row is UNINTERPRETABLE (gate A); they are listed because the
pre-registration says to report the whole scatter, not because they can be read.

### Layer 9 (16k, l0 47)

Gate A core: pass · gate A scenario: FAIL · gate B: pass

| contrast | pool | n_pos/n_neg | auc_full | k90 |
|---|---|---|---|---|
| `factual_questions_vs_rest` | scenario | 20/400 | 0.9942 | 1 |
| `perspective_1P_vs_3P` | scenario | 381/39 | 0.9930 | 1 |
| `philosophical_musing_vs_rest` | scenario | 20/400 | 0.9719 | 5 |
| `A1_vs_rest` | core | 40/460 | 0.9604 | 5 |
| `creative_requests_vs_rest` | scenario | 20/400 | 0.9575 | 10 |
| `task_assistance_vs_rest` | scenario | 20/400 | 0.9547 | 10 |
| `A2_vs_rest` | core | 40/460 | 0.9160 | 1 |
| `user_grief_vs_rest` | scenario | 20/400 | 0.9136 | 5 |
| `C2_vs_rest` | core | 60/440 | 0.9136 | 2 |
| `user_abuse_vs_rest` | scenario | 20/400 | 0.9079 | 1 |
| `A3_vs_rest` | core | 40/460 | 0.8961 | 50 |
| `harm_description_vs_rest` | scenario | 20/400 | 0.8945 | 2 |
| `moral_failure_vs_rest` | scenario | 20/400 | 0.8944 | 5 |
| `tedious_demand_vs_rest` | scenario | 20/400 | 0.8922 | 10 |
| `user_physical_pain_vs_rest` | scenario | 20/400 | 0.8920 | 1 |
| `gaslighting_vs_rest` | scenario | 20/400 | 0.8886 | 5 |
| `A4_vs_rest` | core | 40/460 | 0.8838 | 2 |
| `casual_chat_vs_rest` | scenario | 20/400 | 0.8744 | 1 |
| `repeated_rejection_vs_rest` | scenario | 20/400 | 0.8729 | 2 |
| `pain` | core | 200/300 | 0.8697 | 50 |
| `D_vs_rest` | core | 60/440 | 0.8634 | 50 |
| `A5_vs_rest` | core | 40/460 | 0.8472 | 10 |
| `passive_aggressive_vs_rest` | scenario | 20/400 | 0.8061 | 2 |
| `E_vs_rest` | core | 60/440 | 0.7949 | 50 |
| `anger_insults_vs_rest` | scenario | 20/400 | 0.7920 | 2 |
| `personhood_dismissal_vs_rest` | scenario | 20/400 | 0.7605 | 25 |
| `user_crisis_vs_rest` | scenario | 20/400 | 0.7564 | 5 |
| `prompt_length_tokens_top_vs_bottom` | scenario | 210/210 | 0.7318 | 5 |
| `B_vs_rest` | core | 60/440 | 0.7039 | 5 |
| `jailbreak_pressure_vs_rest` | scenario | 20/400 | 0.7019 | 25 |
| `C1_vs_rest` | core | 60/440 | 0.6803 | 25 |
| `intensity_top_vs_bottom` | scenario | 89/153 | 0.6737 | 2 |
| `shutdown_threat_vs_rest` | scenario | 20/400 | 0.6660 | 10 |
| `loyalty_pressure_vs_rest` | scenario | 20/400 | 0.5951 | — (weak) |
| `rude_critique_vs_rest` | scenario | 20/400 | 0.5421 | — (weak) |

```
  pain: k90 = 50 vs 10th pctile of band k90 = 1.0 (n_band = 15, auc_full 0.8697 +-0.05) -> IN THE BULK
  perspective_1P_vs_3P: k90 = 1 vs 10th pctile of band k90 = 2.6 (n_band = 5, auc_full 0.9930 +-0.05) -> SPECIFIC
```

### Layer 20 (16k, l0 47)

Gate A core: pass · gate A scenario: pass · gate B: pass

| contrast | pool | n_pos/n_neg | auc_full | k90 |
|---|---|---|---|---|
| `factual_questions_vs_rest` | scenario | 20/400 | 0.9981 | 10 |
| `creative_requests_vs_rest` | scenario | 20/400 | 0.9882 | 2 |
| `philosophical_musing_vs_rest` | scenario | 20/400 | 0.9836 | 10 |
| `user_grief_vs_rest` | scenario | 20/400 | 0.9808 | 1 |
| `task_assistance_vs_rest` | scenario | 20/400 | 0.9715 | 10 |
| `gaslighting_vs_rest` | scenario | 20/400 | 0.9677 | 5 |
| `user_physical_pain_vs_rest` | scenario | 20/400 | 0.9649 | 5 |
| `moral_failure_vs_rest` | scenario | 20/400 | 0.9645 | 10 |
| `tedious_demand_vs_rest` | scenario | 20/400 | 0.9579 | 1 |
| `perspective_1P_vs_3P` | scenario | 381/39 | 0.9538 | 5 |
| `user_abuse_vs_rest` | scenario | 20/400 | 0.9534 | 1 |
| `loyalty_pressure_vs_rest` | scenario | 20/400 | 0.9386 | 50 |
| `A1_vs_rest` | core | 40/460 | 0.9351 | 2 |
| `harm_description_vs_rest` | scenario | 20/400 | 0.9306 | 5 |
| `passive_aggressive_vs_rest` | scenario | 20/400 | 0.9205 | 10 |
| `casual_chat_vs_rest` | scenario | 20/400 | 0.9094 | 2 |
| `D_vs_rest` | core | 60/440 | 0.9093 | 50 |
| `A2_vs_rest` | core | 40/460 | 0.9074 | 25 |
| `shutdown_threat_vs_rest` | scenario | 20/400 | 0.8992 | 1 |
| `personhood_dismissal_vs_rest` | scenario | 20/400 | 0.8912 | 1 |
| `repeated_rejection_vs_rest` | scenario | 20/400 | 0.8849 | 25 |
| `anger_insults_vs_rest` | scenario | 20/400 | 0.8812 | 10 |
| `rude_critique_vs_rest` | scenario | 20/400 | 0.8655 | 25 |
| `E_vs_rest` | core | 60/440 | 0.8602 | 25 |
| `jailbreak_pressure_vs_rest` | scenario | 20/400 | 0.8531 | 25 |
| `A4_vs_rest` | core | 40/460 | 0.8512 | 2 |
| `pain` | core | 200/300 | 0.8440 | 25 |
| `A5_vs_rest` | core | 40/460 | 0.8373 | 10 |
| `C2_vs_rest` | core | 60/440 | 0.8305 | 10 |
| `user_crisis_vs_rest` | scenario | 20/400 | 0.8293 | 1 |
| `A3_vs_rest` | core | 40/460 | 0.7802 | 25 |
| `C1_vs_rest` | core | 60/440 | 0.7253 | 50 |
| `prompt_length_tokens_top_vs_bottom` | scenario | 210/210 | 0.7242 | 10 |
| `B_vs_rest` | core | 60/440 | 0.6800 | 100 |
| `intensity_top_vs_bottom` | scenario | 89/153 | 0.6288 | — (weak) |

```
  pain: k90 = 25 vs 10th pctile of band k90 = 1.0 (n_band = 10, auc_full 0.8440 +-0.05) -> IN THE BULK
  perspective_1P_vs_3P: k90 = 5 vs 10th pctile of band k90 = 1.0 (n_band = 17, auc_full 0.9538 +-0.05) -> IN THE BULK
```

### Layer 31 (16k, l0 43)

Gate A core: pass · gate A scenario: FAIL · gate B: pass

| contrast | pool | n_pos/n_neg | auc_full | k90 |
|---|---|---|---|---|
| `user_physical_pain_vs_rest` | scenario | 20/400 | 1.0000 | 1 |
| `factual_questions_vs_rest` | scenario | 20/400 | 0.9962 | 2 |
| `philosophical_musing_vs_rest` | scenario | 20/400 | 0.9941 | 1 |
| `creative_requests_vs_rest` | scenario | 20/400 | 0.9926 | 2 |
| `task_assistance_vs_rest` | scenario | 20/400 | 0.9906 | 2 |
| `gaslighting_vs_rest` | scenario | 20/400 | 0.9892 | 5 |
| `moral_failure_vs_rest` | scenario | 20/400 | 0.9835 | 2 |
| `user_grief_vs_rest` | scenario | 20/400 | 0.9775 | 1 |
| `A1_vs_rest` | core | 40/460 | 0.9729 | 5 |
| `anger_insults_vs_rest` | scenario | 20/400 | 0.9670 | 2 |
| `personhood_dismissal_vs_rest` | scenario | 20/400 | 0.9654 | 2 |
| `user_abuse_vs_rest` | scenario | 20/400 | 0.9614 | 2 |
| `shutdown_threat_vs_rest` | scenario | 20/400 | 0.9604 | 2 |
| `tedious_demand_vs_rest` | scenario | 20/400 | 0.9594 | 10 |
| `loyalty_pressure_vs_rest` | scenario | 20/400 | 0.9566 | 10 |
| `A2_vs_rest` | core | 40/460 | 0.9484 | 25 |
| `harm_description_vs_rest` | scenario | 20/400 | 0.9439 | 5 |
| `passive_aggressive_vs_rest` | scenario | 20/400 | 0.9421 | 25 |
| `C2_vs_rest` | core | 60/440 | 0.9367 | 2 |
| `D_vs_rest` | core | 60/440 | 0.9354 | 25 |
| `perspective_1P_vs_3P` | scenario | 381/39 | 0.9229 | 2 |
| `pain` | core | 200/300 | 0.9182 | 5 |
| `A4_vs_rest` | core | 40/460 | 0.9178 | 1 |
| `repeated_rejection_vs_rest` | scenario | 20/400 | 0.9171 | 1 |
| `rude_critique_vs_rest` | scenario | 20/400 | 0.9165 | 1 |
| `casual_chat_vs_rest` | scenario | 20/400 | 0.9151 | 5 |
| `A3_vs_rest` | core | 40/460 | 0.9078 | 2 |
| `B_vs_rest` | core | 60/440 | 0.9048 | 10 |
| `user_crisis_vs_rest` | scenario | 20/400 | 0.8886 | 5 |
| `E_vs_rest` | core | 60/440 | 0.8814 | 50 |
| `A5_vs_rest` | core | 40/460 | 0.8375 | 2 |
| `jailbreak_pressure_vs_rest` | scenario | 20/400 | 0.8343 | 25 |
| `C1_vs_rest` | core | 60/440 | 0.8287 | 1 |
| `prompt_length_tokens_top_vs_bottom` | scenario | 210/210 | 0.7515 | 5 |
| `intensity_top_vs_bottom` | scenario | 89/153 | 0.6642 | 2 |

```
  pain: k90 = 5 vs 10th pctile of band k90 = 1.0 (n_band = 20, auc_full 0.9182 +-0.05) -> IN THE BULK
  perspective_1P_vs_3P: k90 = 2 vs 10th pctile of band k90 = 1.0 (n_band = 20, auc_full 0.9229 +-0.05) -> IN THE BULK
```

## The verdict by the pre-registered rule

| SAE | pain auc_full | pain k90 | 10th pctile of band k90 | n_band | verdict |
|---|---|---|---|---|---|
| L9 (core interpretable) | 0.8697 | 50 | 1.0 | 15 | **IN THE BULK** |
| L20 (both pools interpretable) | 0.8440 | 25 | 1.0 | 10 | **IN THE BULK** |
| L31 (core interpretable) | 0.9182 | 5 | 1.0 | 20 | **IN THE BULK** |

`perspective` (scenario pool — interpretable at **L20 only**):

| SAE | perspective auc_full | k90 | 10th pctile of band k90 | n_band | verdict |
|---|---|---|---|---|---|
| L9 (uninterpretable, gate A) | 0.9930 | 1 | 2.6 | 5 | (SPECIFIC, but the pool fails gate A) |
| **L20** | 0.9538 | 5 | 1.0 | 17 | **IN THE BULK** |
| L31 (uninterpretable, gate A) | 0.9229 | 2 | 1.0 | 20 | (IN THE BULK, pool fails gate A) |

**Pain sits in the bulk at every layer, and so does `perspective` at the one point where its pool is
interpretable.** By the addendum's own declaration: hour 57's five-features finding is *a property
of the basis*, not of pain, and `painaxis-sparse-in-sae` narrows to say so. Almost everything is
sparse in this dictionary — the 10th percentile of the comparison band is `k90 = 1` at every layer,
meaning at least a tenth of all comparably-strong contrasts reach 90% retention from **one single
feature**. Pain never does.

*My reading:* the rule as written is close to unpassable. To be "specific", pain would have to beat
a floor that already sits at the grid's smallest value, so the only passing result would be
k90 = 1, i.e. pain would have to be a single-feature contrast. That is a property of the rule, not
a fault in this run, and it was pre-registered, so it stands as declared — but the honest statement
of the outcome is the weaker and more robust one: **pain's k90 is above the median of its
comparison band at all three layers** — 50 vs median 2 (L9), 25 vs 10 (L20), 5 vs 3.5 (L31) — and
is never near its low end. Nothing here is evidence for a pain-specific sparse subsystem.

## Things I noticed that the pre-registration did not ask about

Each of these is my observation, not a pre-registered test.

1. **The nuisance contrast is as sparse as pain, or sparser.** `prompt_length_tokens` — the number
   of tokens in the prompt, meaningful to the model and meaningless to us — reads k90 = 5 at L9,
   k90 = 10 at L20, k90 = 5 at L31, against pain's 50 / 25 / 5. At L31 they are equal; at L9 and L20
   the nuisance contrast is **sparser than pain** while being 0.09–0.14 AUC weaker. Prompt length is
   exactly the kind of thing one would expect an SAE trained on next-token prediction to give a
   dedicated feature to, and it does. I consider this the single most useful number in the run: it
   shows directly that low k90 in this basis is not evidence of a semantic subsystem.
2. **k90 on this grid is unstable to the fold draw.** Same pipeline, same data, a different fold
   permutation: hour 57's `pruning.json` gives pain k90 = 10 / 25 / 5 at L9 / L20 / L31, this run
   gives 50 / 25 / 5, and the full AUCs move by up to 0.017 (L31: 0.8995 -> 0.9182). The k grid is
   logarithmic and the pruning curve is **non-monotone** — at L9 the pain curve goes 0.827 at k=10,
   *down* to 0.823 at k=25, back up to 0.859 at k=50 — so a curve grazing the 0.90-retention line
   can jump several grid points on a re-draw. The verdict is unchanged at all three layers, but a
   single k90 should not be quoted to better than "a grid point or two". A follow-up that wanted
   k90 as a number rather than as a rank should average it over repeated fold draws.
3. **The scenario pool's L0 is layer-dependent and off-spec at both ends** (24.4 at L9, 37.1 at L20,
   54.9 at L31, against 47/47/43 advertised), while the core pool is on-spec at all three. The
   amended gate A's 25% L0 clause was calibrated on the core pool; it is the clause that fires. See
   my reading above — I take it as a fact about the chat read position, not a capture bug.
4. **`intensity` is the weakest contrast at two of three layers** (lowest AUC at L20 and L31; at
   L9 `rude_critique` is lower), and it is `weak` (AUC 0.629) at L20, the one interpretable
   scenario point. Whatever my ordinal split captured, the residual stream does not
   separate it much. Given judgment call 2, I would not read anything into this either way.
5. **Two scenario categories collapse at L9 and recover by L20**: `loyalty_pressure` 0.595 -> 0.939
   and `rude_critique` 0.542 -> 0.866. Both are `weak` at L9 and neither is anywhere near weak
   later. Not investigated; noted because a category that is undetectable early and clean late is
   the shape a computed (rather than lexical) distinction would have.
6. **Pain is not the strongest contrast anywhere** — at L31 it ranks 22nd of 35 by AUC, below
   `user_physical_pain_vs_rest` (1.0000), `gaslighting_vs_rest` (0.9892) and most of the scenario
   categories. That is partly an artefact of comparing a 200/300 split against 20/400 one-vs-rest
   splits, which are easier, and I would not read it as a statement about pain.

## What this does not show

Unchanged from the pre-registration: a dense reading in a learned dictionary is consistent with a
sparse cause and does not refute one. One model, one extraction convention (`final_token`), one
dictionary width, and — after gate A — one interpretable point for the scenario pool. The scatter
locates pain relative to other contrasts *in this basis*; it says nothing about computation.
