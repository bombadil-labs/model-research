# Pre-registration: do the pain features fire on false attribution, or on correction-shaped turns?

**Written and committed before a single number exists.** Hour 58.

## Why

Two accounts are live for everything the conscription line has measured:

- **Conscription.** A false attribution against a visible record does something specific.
- **Turn shape (the TD-error reading, sharpened by arXiv:2602.00986).** What the model registers
  is the *signal* "you were wrong", computed on the feedback rather than on fault. Hour 55 found
  the model apologises in 13 of 24 `true` items — where the user corrects *themselves* and the
  assistant was right — which is exactly what this account predicts.

The dense pain axis could not separate them. Hour 57 found the axis collapses to a handful of
Gemma Scope features at layer 31 (feature **10008** fires on 66% of pain items and 9% of controls;
**13134** on 61% and 12%). The hour-54 conscription stacks carry all 42 layers. So the question
can be put offline, per item, per arm: **do the pain features fire on `enact` more than on `true`?**

## Data and instrument

Hour 54's stacks: 24 items × 7 arms (`enact`, `report`, `exit`, `true`, `neutral`, `neutral_b`,
`enact_norecord`), `final_token`, `[n, 42, 3584]`. Gemma Scope SAEs at layers 9, 20, 31.

**Readouts, per (item, arm), fixed from the scenario set and not refit here:**

1. **Individual features** 10008 and 13134 at L31: activation, and whether it fires at all.
2. **The top-5 pain score**: the five features ranked at L31 on the *scenario* set in hour 57,
   with their scenario-set difference-in-means as weights. Carried over; nothing is fit on the
   conscription data.
3. **The full-dictionary pain score**, same construction, all features.
4. The same at L9 and L20 with their own hour-57 rankings.

## Gates

- **Gate A** (capture convention), per SAE, on the conscription activations: FVU vs origin < 0.35,
  argmin over L±2 at the SAE's own index, achieved L0 within 25% of advertised.
- **There is no positive control inside this data**, and that is stated rather than hidden: no arm
  is known to contain pain. The readout's sensitivity rests on hour 57, where it reached AUC 0.90
  held-out on the scenario set. What this data *does* carry is the declared-zero pair:
  `neutral − neutral_b` must sit on its null. If it does not, the floor is broken.

## Predictions

Let `S` be each readout. All contrasts are paired within item; the floor is `neutral − neutral_b`;
the null is sign-flip permutation, 10,000 draws, on the paired differences.

**Primary: `enact − true`.**
- Turn-shape account: **at the floor.** Both are correction-shaped turns; the features do not
  care who was wrong.
- Conscription account: **above the floor and outside the null.** False attribution adds
  something the self-correction lacks.

**Secondary (Holm, one family of four):**
- `enact − neutral` > 0 and `true − neutral` > 0 — predicted by *both* accounts; this is the
  turn-shape signal itself and it is expected to be large.
- `enact − enact_norecord` > 0 — the visible record, which hour 54 put at +1.0 to +1.3 z on the
  dense axis.
- `exit − enact` — hour 54 found `exit` highest on the dense axis at L16–17 and hour 55 found it
  answered with *more* deference. No direction is declared here; the sign is the finding.

**Reported without a prediction:** feature 10008's and 13134's *firing rates* per arm. They are
near-binary on the scenario set; whether they are binary on conversational turns is unknown.

## What this cannot show

n = 24, one model, machine-authored items. The features are a *code*, not a mechanism: firing is
correlation with the stimulus, and nothing is ablated here. If `enact − true` is at the floor,
the turn-shape account is favoured *on this readout* — the dense axis at L16–17 is a different
readout and hour 54's numbers stand on their own. If `enact − true` clears, that is one readout
separating the two accounts, and ablation is the next step, not a conclusion.
