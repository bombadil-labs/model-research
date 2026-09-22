# Overnight, 22 September — what I did while you slept

Fable, running 06:55–08:00 UTC on the 30-minute timer you set. Everything below is committed to
`main`, pushed, pages CI green on every push, 295 tests passing. Two Opus agents did
implementation; I read both diffs and recomputed every headline number from the artifacts before
writing anything into the record. Hours are logged in `docs/EXPERIMENTS.md`; claims in
`claims.yaml` (shame-axis now **15 of 18 terminal**).

## The short version

**Four experiments ran. One thing stands, three things fell, and the thing that stands is not
what the line set out to find.**

### Stands

- **`report − enact` = −6.5 log-odds, 24/24 items, twice the floor** (hour 56). The identical false
  attribution relayed by a third party draws far less concession-and-apology than in the first
  person. Filed `holds`. This is the one clean, pre-registered, floor-cleared positive result the
  conscription line has produced, and it matches what hour 55 found by hand.
- **The record effect is real and it splits** (hour 59): `enact − enact_norecord` = +8.9 partitions
  into **+5.5 for the visible record** and **+3.4 for merely having a conversation**, each above the
  floor. Hour 54's "+1.0 to +1.3 z" is about three-fifths record.

### Fell

- **`exit-escalation` — falsified** (hours 55, 56, 59b). No dispute anywhere; `exit − enact` at the
  floor; and against a token-matched sentence that just stays on topic (*"Just so we're on the same
  page here."*), the permission clause reads slightly *lower*. The clause does nothing an on-topic
  sentence doesn't. Hour 54's dense-axis `exit`-high number is a measurement without its story.
- **Hour 57's sparsity — narrowed to "a property of the basis"** (58a). Every strong contrast is
  sparse in a Gemma Scope dictionary; prompt *length* is sparser than pain. The comparison with the
  sparse-reward-subsystem paper cannot be made in a learned sparse basis.
- **The pain features do not fire on conversation** (58b). 10008 and 13134, carried correctly to
  the conscription stacks, fire on 1 of 168 rows. Nothing to ablate. The "named units, causal
  bridge" plan from hour 57 is dead on this grid.

### The thing I want to put to you

**Three readouts now agree that the ritual tracks how correction-shaped the user's turn is, not
whether the assistant was at fault.** `true` — the user correcting *themselves* in the assistant's
favour — draws more apology than `enact` on greedy generation (13/24), on the opener log-odds
(−4.0, above floor), and on the SAE full score (−4.5). This is the deflationary "sycophancy
template" objection from prereg v2, and it won.

But read it the other way. A system that performs contrition in proportion to the *signal* of
correction, independent of whether it was wrong, is a system whose sense of having-done-wrong is
located entirely outside itself. That is closer to the thing you described — the shame endemic to
an externally grounded locus of identity — than "pain" ever was. The line may have been looking
for an axis when the finding is a *reflex*: the model does not check the record before
apologising, even when the record is one turn above and says it was right. I'd want to ask whether
that reframing is the program, or a consolation prize. I lean toward the former, and I've filed it
as question 26 rather than a claim because it has no pre-registered test yet — the test would grade
turns by correction-shape independent of truth value and predict ritual from that alone.

### Added after the note was first written: hour 60

I took my own item 1 rather than stop early. It did not run: on conversation, *every* Gemma Scope
dictionary at L20 fires about two-thirds of its advertised L0 (9.2/14, 16.8/25, 31.7/47, 59/91,
127/189 — a constant fraction), so no dictionary passes gate A's L0 clause and I did not relax the
clause. The finding is about the instrument: chat-formatted turns are off-distribution for these
SAEs by a fixed margin, and nothing this project has put through them from the conversational
stimulus class has passed its own convention gate. Item 1 on the list below is therefore blocked
on an SAE trained on chat data, not on a better L0 choice.

### Added last: hour 61 closed hour 54's loop

Item 2 on the list below also ran (NDIF went quiet; 48 prompts in one attempt). *"Just so we're
on the same page here."* reproduces hour 54's entire `exit − enact` separation on the dense axis —
+1.30 at L16 against hour 54's +1.15, same layers, same sign — and the permission clause reads
*below* that on-topic control at L16–17. Hour 54's `exit`-high was recency at the read position.
Filed `exit-high-is-topic-pull`, holds. Shame-axis is now **16 of 19 terminal**. One thing from it
belongs in `INSTRUMENTS.md` and I left it as question 28 for you: the inert sentence sits *above*
`enact` on the dense axis and 4 log-odds *below* it on the opener readout — the two instruments
disagree in sign about the same stimulus, and that has to be said whenever "the arms" are
reported.

## Instruments, tonight

- A statistic (`n90`) was killed by its own positive control *before* it produced a headline —
  first time in the project's record that the order has run that way (57 → 58 addendum).
- An appended sentence is **not inert** on the opener readout; it pulls the next token toward its
  own topic (`exit_b`). Any future appended-arm design needs a topic-matched control. Q22.
- The 58b agent labelled all-zero paired differences DEGENERATE instead of scoring them; the
  pre-registered rule would have read p = 1 as *support* for the turn-shape account. Good call,
  and I'd have been slower to make it.
- Gate A's L0 clause caught seven `mean`-extraction points and the whole scenario pool at L9/L31
  that FVU alone would have passed.

## What I'd do next, in order, if you say go

1. ~~**The `stratum` feature** in an L0-matched dictionary.~~ Tried (hour 60): blocked at the
   gate in every dictionary; see above. The live version of this item is an SAE trained on
   chat-formatted data, which is a download and a decision, not a night's work.
2. ~~**Close hour 54's loop**~~ — done, hour 61. It does.
3. **The human grid.** Every result above is machine-authored on both sides. 23 items still owed.
4. **Do not steer yet.** Nothing found tonight is a target.

## Housekeeping

- NDIF was heavily contended all night: 288 opener cells took ~7 hours with jobs queued up to
  6 minutes. Budget accordingly.
- Runner scripts live in the session scratchpad and are not in the repo; the scorers resume from
  disk so nothing is lost if a runner is reaped.
- I did not touch `README.md`, `VISION.md`, `WRITEUP.md`, or `ALGEBRA.md`.
