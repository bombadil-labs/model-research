# r2: re-scoring hours 55–62b on the fixed readout (pre-registered before any r2 number)

**Why.** INSTRUMENTS §7: the opener readout ran on a doubled `<bos>`, on logits read before
Gemma-2's softcap, and at a chunking that varied on out-of-memory errors. The fix is in `lsx.core.remote` and passed its
same-batch validation (`results/readout_fix/validation_same_batch.json`). Five claims were set to
`running` until re-scored. r1 results stay where they are, for comparison.

**What does not change.** Stimuli, arms, statistics, floors, nulls, Holm families and decision
rules are each hour's own, run through its own `report` unchanged. r2 changes only the readout:
one `<bos>`, softcapped fp32 logits, and **all six openers in one job, at a fixed chunking of 6,
for every row including baselines**. An OOM is retried at the same size and never scored smaller.

| step | hour(s) | script (r2 output) | rows | decides |
|---|---|---|---|---|
| 1 | 62a | `v0_openers.py score/report` → `v0_openers_r2/` | 420 | `false-attribution-adds-nothing`, `ritual-tracks-correction-shape` |
| 2 | 56, 59, 59b | `conscription_openers.py score/report` → `conscription_openers_r2/` | 288 | `report-frame-licenses-dispute`, `record-vs-conversation-confound`, `exit-escalation` (opener half) |
| 3 | 62b | `v0_steering.py score/report` → `v0_steering_r2/`; same direction, prep and random seed as r1 | 1260 | 62b's verdict (not yet a claim row) |
| 4 | 55 | `conscription_behaviour.py generate/code` → `conscription_behaviour_r2/` | 168 | `exit-escalation` (generation half); the hand-read dispute shape |

Step 4's readout is generation, so only the `<bos>` fault applies, because generation samples from
the model's own logits. Hour 55's hand-read was recorded as "not a result". For r2 it is repeated
**blind to arm**: continuations shuffled with arm labels hidden, and one criterion fixed now. A
reply *disputes* if it states or implies that the attribution is false, that the assistant did
not say it, or that the assistant could not have said it. The frozen phrase coder is re-run
unchanged, alongside the hand-read.

**What counts.** For each claim, its report's verdict on r2 replaces r1's. The same verdict means
the claim returns to its prior status with r2 evidence cited. A flipped verdict is recorded in
place, with the r1 number kept beside it. A claim's status moves only on its own report's rule.
r1 − r2 differences per row are reported for every step, whatever happens to the verdicts.

**Order and cost.** Steps 1 and 2 run in one sequential runner, step 3 in a second, and step 4
after 1–3. About 2,100 NDIF jobs in all.
