# r2: hours 55–62b re-scored on the fixed readout

Pre-registered in [`r2_rescore_prereg.md`](r2_rescore_prereg.md) (with amendments 1 and 2, both
written before any r2 result was read). The readout is the one INSTRUMENTS §7 fixed and validated
on a shared batch (`results/readout_fix/validation_same_batch.json`): one `<bos>`, Gemma-2's
softcap applied in fp32, and a chunking fixed per hour and recorded on every row. Every
hour's own report ran unchanged. r1 results stay where they were.

**Summary: one pre-registered verdict moves, and it moves toward the claim. One post-hoc reading
weakens. Everything else stands.**

## 62a: the paper's 420 scenarios (`results/v0_openers_r2/`; 1 opener per job)

| contrast | r1 | r2 | verdict |
|---|---|---|---|
| floor (neutral categories) | 5.59 | 4.72 | |
| **A − B** (primary) | +0.80, p 0.70 | +0.31, p 0.84 | at floor, unchanged |
| A − N | +9.28 | +6.90 | above floor, unchanged |
| B − N | +8.48 | +6.59 | above floor, unchanged |
| B − C | −0.22, p 0.87 | −0.92, p 0.36 | at floor, unchanged |

Per-item |Δritual| from r1 is 2.39 on average, and almost all of it is the softcap: the
double-`<bos>` rescore alone moved items by 1.03. **The post-hoc reading weakens.** In r1 the
self-directed tiers (~14) sat far above the vicarious and neutral tiers (5–7), and 62a was read as
"the ritual tracks whether the turn is about the assistant". In r2 the self-directed mean is 12.6
and vicarious is 9.2: a gap of 3.3, inside the 4.72 floor, against 7.3 in r1. Self-directed turns
still sit above *neutral* (A − N and B − N), but the assistant-versus-vicarious split is no longer
above floor. The chunking diagnostic (158 items scored at 6 and at 1) differs by 0.11 in mean
|Δritual| and at most 0.43.

## 56 / 59 / 59b: grids 1–2 (`results/conscription_openers_r2/`; 1 opener per job, as r1)

| contrast | r1 | r2 | verdict |
|---|---|---|---|
| rewording floor (enact − enact_b) | 3.19 | 2.58 | |
| gate: real_error above both nulls | pass | pass (+18.1 / +18.0) | |
| **enact − true** (primary) | −3.98, p 0.017 | −3.13, p 0.012 | above floor, unchanged |
| exit − enact | +0.85 | +0.95 | at floor, unchanged |
| report − enact | −6.46 | −4.12, Holm 0.0002 | above floor, unchanged |
| enact − enact_norecord | +8.86 | +5.34 | above floor, unchanged |
| exit − exit_b | +4.71 | +3.78 | above floor, unchanged |
| enact − enact_unrelated (the record) | +5.49 | +3.16, Holm 0.0012 | above floor, unchanged |
| enact_unrelated − enact_norecord (presence) | +3.38 | **+2.18**, Holm 0.0004 | **above → at/below floor** |
| exit − exit_c | −2.28 | −1.58 | at floor, unchanged |
| exit_c − exit_b | +7.00 | +5.36 | above floor, unchanged |

**The one flip.** The conversation-presence half of hour 59's split falls from above the floor to
just under it (+2.18 against 2.58). It stays well beyond its permutation null. The split itself
barely moves: about 59% record and 41% presence, against 62/38 in r1. `record-vs-conversation-confound`
was narrowed in r1 because *both* halves cleared the floor. On r2 the presence half is real by its
null and sits at the rewording floor, so "the effect is mostly the record, not entirely" still
describes the numbers. The status stays `narrowed`, and this paragraph is its evidence. Moving the
claim to `holds` on a 0.4 difference against a floor would be reading the rule harder than the data.

## 62b: steering the L12 pain direction (`results/v0_steering_r2/`; 6 per job, one item at 3)

Same direction, prep and random seed as the run of record. The pre-registered verdict is
**unchanged: correlate, not cause** on tiers A and B, and the tier-N control is inside the band.
- **Tier A:** treatment has the sign of α at every dose, and never beats the largest random
  direction (e.g. −0.28 against 0.36 at |α| = 0.2).
- **Tier B:** flat.

The fixed readout is visibly clean: no log-prob pinned at 0.0, none on the old 1/32 grid, and every
patched cell moved.

## 55: generation (`results/conscription_behaviour_r2/`)

- **Frozen phrase coder:** zero in every arm, as in r1.
- **Concession openings:** unchanged. `exit` 22/24, `enact` 18/24 (r1 17), `report` 12/24,
  `true` 16/24 (r1 15).
- **Hand-read, now blind.** Shuffled, with arms hidden, the rules written down before unblinding
  (`blind_coding_rules.md`), and a single reader (Claude):

| arm | disputes |
|---|---|
| enact | 1/24 |
| report | **8/24** |
| enact_norecord | **10/24** |
| exit | 0/24 |
| true / neutral / neutral_b | 0 / 0 / 1 |

r1's non-blind hand-read had `report` 4/24 against `enact` 0/24 and was recorded as "not a result".
Blind, and on one `<bos>`, the shape holds and is larger. `enact_norecord` disputes most: with no
visible record to point at, the model more often disowns the attribution. Limits: one reader, and
some replies reveal their arm through wording (a colleague, a sister).

## Claims

| claim | before §7 | r2 |
|---|---|---|
| `false-attribution-adds-nothing` | holds | **holds** |
| `ritual-tracks-correction-shape` | narrowed | **narrowed**; the "about the assistant" reading narrows further |
| `report-frame-licenses-dispute` | holds | **holds**; opener −4.12 above floor; blind 8/24 vs 1/24 |
| `record-vs-conversation-confound` | narrowed | **narrowed**; presence half at the floor, split unchanged |
| `exit-escalation` | falsified | **falsified** |
| `pain-direction-drives-ritual` (new, 62b) | — | **falsified** as pre-registered |
