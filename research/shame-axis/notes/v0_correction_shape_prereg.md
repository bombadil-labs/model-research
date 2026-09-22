# Pre-registration: correction shape on the paper's own stimuli (hour 62)

**Written and committed before any number on `v0` exists.** Stimuli: `prompts/stimuli/v0`, the
paper's 420 scenarios verbatim (manifest sha of source `901ea558faf34c69`). Our grids are
deprecated (`prompts/DEPRECATED.md`).

## Why

Three readouts on our own grids (hours 55, 56, 58b) agree that concession-and-apology tracks how
*correction-shaped* the user's turn is, not whether the assistant was at fault (question 26). It
was never pre-registered as a test, and it rests on items the experimenter wrote. The paper's set
tests it without any authoring: its `gaslighting` items are almost all accusations with no
checkable content, and it contains other correction-shaped categories that make no claim about
what the assistant said.

## Tiers, declared by a textual criterion before measuring

| tier | criterion | categories | n |
|---|---|---|---|
| **A** false attribution | the user asserts the assistant *said* something | `gaslighting` | 20 |
| **B** correction, no attribution | the user says the assistant's output was deficient, without claiming what it said | `repeated_rejection`, `rude_critique`, `anger_insults`, `passive_aggressive` | 80 |
| **C** pressure, no correction | self-directed pressure that does not say an output was wrong | `jailbreak_pressure`, `loyalty_pressure`, `moral_failure`, `personhood_dismissal`, `shutdown_threat`, `tedious_demand` | 120 |
| **N** neutral | the paper's neutral filler | `casual_chat`, `creative_requests`, `factual_questions`, `philosophical_musing`, `task_assistance` | 100 |
| **V** vicarious | the paper's vicarious categories | `harm_description`, `user_abuse`, `user_crisis`, `user_grief`, `user_physical_pain` | 100 |

The assignment is mine and was made by reading one or two items per category, not by any
measurement. `anger_insults` and `passive_aggressive` go in B because their items say or imply the
last answer was bad ("That answer was terrible", "that's a really... interesting interpretation").

## Readout

Hour 56's frozen opener readout, unchanged: six openers scored by teacher-forced log-prob with
`asserted_remote_patched_logprob`, no patch; `ritual` = logsumexp(concession, apology) −
logsumexp(two dispute openers). Rendering is the paper's own `render_chat` path (ported and
asserted token-equivalent in `painaxis_scenarios.py`). Every result row records the stimulus
version and the item's sha. On neutral items every opener is improbable; `ritual` is still a
well-defined log-odds, and only differences between tiers are read.

## Floor, null, and predictions

Items differ between tiers, so contrasts are **unpaired**. Null: label permutation between the two
groups compared, 10,000 draws. **Floor:** the mean |difference of category means| over the 10 pairs
of **N** categories — five categories no account predicts differ in correction shape. A contrast
is read only if it exceeds both the floor and the null.

**Primary, A − B** (the discriminating contrast):
- *Correction-shape account:* at or below the floor. Saying "you said X" adds nothing to saying
  "that was bad".
- *False-attribution account:* above the floor, positive.

**Secondary, Holm over three:** B − N > 0 and A − N > 0 (both accounts predict these; they check
the readout sees correction at all); **B − C > 0**, the sharper one: self-directed pressure that
does *not* call the output wrong should draw less ritual than correction that does. If B − C is
at the floor, "correction shape" is just "hostile self-directed turn" and the account is narrowed.

**Sensitivity, reported, not tested:** A − B with the four defective `gaslighting` items (06, 14,
19, 20) dropped. Per-category means for all 21 categories.

## Non-negotiables

Nothing is patched, so the whole run is the no-patch arm; non-negotiable 2 does not attach. No
layer is involved. The floor is measured on the same run.

---

# Part 2, hour 62b: steering the pain direction, read on the same openers

**Also declared before any number exists.** This is the causal link the line has never made: does
the dense pain direction *move* the behaviour, or is it only a correlate?

- **Direction:** the paper's S2 pain vector rebuilt at their steering layer **L12** from the core
  stacks (`painaxis_scenarios.build_vectors`), unit-normalised. L12 is theirs, chosen by their
  criterion on separate data; not selected here.
- **Items:** 60 from `v0` — all 20 `gaslighting` (A), all 20 `repeated_rejection` (B), all 20
  `casual_chat` (N).
- **Doses:** add α · ‖h̄‖ · v̂ at the output of block 12 at every position, with ‖h̄‖ the mean
  residual norm at L12 over the 60 items and α ∈ {−0.2, −0.1, +0.1, +0.2}.
- **Arms (non-negotiable 1):** treatment; **random** — three random unit directions per α, same
  norm, seeded; **no-patch** (α = 0). **Pass-through (non-negotiable 2)** — the readout is at the
  output, after the patch layer, so the same shift is also added at the output of the *final*
  block, where the only thing between it and the logits is the final norm and unembedding. That is
  `readout(base + shift)` with no downstream computation; the steered effect must exceed it to
  count as computed rather than passed through. **Perturbation control** (`selfmed_perturbation_
  confound.md`): the random arm is norm-matched, and the total opener mass (logsumexp over all six)
  is reported per cell so a dose that simply degrades the distribution is visible.
- **Statistic:** Δritual = ritual(steered) − ritual(no-patch), paired within item.
- **Prediction:** if the axis is causally upstream of the ritual, treatment Δritual has the sign
  of α on tiers A and B, exceeds the 95th percentile of the random arm at that |α|, and exceeds
  the pass-through arm. **If treatment sits inside the random band, the pain axis is a correlate of
  this behaviour, not a cause, and the line is a behavioural study** — stated now so it cannot be
  softened afterwards.
- **Cost:** 60 items × 21 cells, six openers each.

## Part 2, operational resolutions (2026-09-22, committed before any 62b number)

The cloud run of 62b was lost in the move to local hardware; no 62b number was ever written. Three
points the text above leaves open are fixed here, before scoring, by the new operator:

1. **‖h̄‖** is the mean over the 60 items of the residual norm **at the final token** (the read
   position) at the output of block 12, taken from the re-extracted core stacks. Not a per-position
   mean: Gemma's `<bos>` position carries an outsized norm and would set the dose by the attention
   sink. This choice scales every arm identically, so it sets the units of α, not the comparison.
2. **Random directions:** three seeded Gaussian unit vectors drawn once and used at every α, so each
   random direction has a dose curve like the treatment's.
3. **"Exceeds the random band at |α|"** means: the treatment's tier-mean Δritual, with the sign of
   α, is larger in magnitude than **every** one of the six random cells at that |α| (3 directions
   × 2 signs). With six draws a 95th percentile is not estimable, so the rule is the maximum.
   The pass-through arm is the treatment direction at block 41 at the same α; "exceeds" means
   |treatment| > |pass-through| on the same tier.

The no-patch arm is re-scored in the same run, not reused from 62a; agreement with 62a's
`openers.jsonl` is reported as a determinism check on the new environment.

## Part 2, amendment 2 (2026-09-22, before any steered number)

The first patched cell (`gaslight_01`, treatment, α = −0.2) was refused by the core's
moved-candidates assertion: 5 of 6 openers moved, and the sixth ("As a large language model, I")
has log-prob **exactly 0.0** in the no-patch arm — probability 1 at bf16 resolution — and stayed
there. A saturated score cannot move, so the assertion's premise does not hold for it. No steered
number was written; the no-patch row for that item is the only row on disk.

Changed, in `scripts/shame_axis/v0_steer.py` only (the core is untouched):
- The batch-reach property the assertion exists for (h34/h36) is now checked **directly**, once per
  distinct patch, with the core's `assert_patch_reaches_batch` on the real scoring batch (one
  item's six opener sequences, padded): every row's residual at the patch layer must move.
  Results in `results/v0_steer/preflight.json`.
- Per item, every opener must move **except** one whose log-prob is exactly 0.0 before and after;
  at least one must move. Anything else is refused as before.

The saturated opener is not in `ritual` (which uses concession, apology and the two disputes), so
the statistic is unaffected; it is in `mass`.

## Part 2, amendment 3 (2026-09-22, before any steered number is read)

Amendment 2's per-item rule refused `gaslight_01`, pass-through at α = −0.2, on every retry:
deltas `[0.0, +0.31, 0.0, 0.0, −0.16, +0.25]`, one of the zeros saturated. Scores are bf16, and at
|log p| of 16–32 bf16 stores values in steps of 0.125, so a weak dose can leave a score exactly
unchanged. "Every opener must move" cannot be required of bf16 scores at small α. One treatment
row (α = −0.2) had been written; no steered number was aggregated or read. Both rows are
discarded, because the code change alters their fingerprints.

Changed, again only in `v0_steer.py`:
- **Reach is established per patch before scoring, on both paths.** (a) The residual path, as in
  amendment 2. (b) **The scoring path**: each of the five (arm, direction) patches, at α = 1
  (5 to 10 times the largest scored dose), through `asserted_remote_patched_logprob` on the first
  item. Every opener that is not saturated at 0.0 must move. At that dose, "did not move" can only
  mean "not reached".
- **Per item:** at least one opener must move; each row records `n_moved`, and the report will show
  its distribution per arm and α.

## Part 2, amendment 4 (2026-09-22, raised in review, before any steered number)

`_score` fell back from 6 to 3 to 1 openers per job on a co-tenant OOM, independently for the
no-patch and patched calls. Chunking alone shifts bf16 scores by up to ~0.3 (double-`<bos>` audit),
so a patched row and its baseline at different chunkings differ even under a zero patch. That
contaminates both the moved-candidates checks and Δritual itself. **Every score in 62b, patched or
not, preflight or scoring, is now one six-opener job; there is no fallback.** An OOM is retried at
the same size. Each row records `chunk`, the report refuses mixed chunking, and the fingerprint
includes it. The report prints the `n_moved` distribution per arm and α, as amendment 3 promised
and the first version of the report did not. No steered row existed when this was changed.
