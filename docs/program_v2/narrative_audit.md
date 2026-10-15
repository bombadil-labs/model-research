> **Provenance.** Written read-only by an agent in the 2026-10-15 cloud session as evidence for [`PROGRAM_v2.md`](../PROGRAM_v2.md), and committed verbatim. It is agent output: judgments are marked as such (**[J]** / *Judgment*), and tallies and sums are the agent's own arithmetic. `PROGRAM_v2.md` §9 lists which citations were re-checked against their files. Line numbers refer to the tree at `2a992c3`.

# Narrative line: trajectory digest (read-only audit)

**Conventions.** Paths are relative to `/home/user/model-research`. `file:line` is the exact line in that file. Anything I infer is marked **Judgment**. I edited nothing.

**Git dates.** Dates are git author dates in −0400. The clone is shallow: `.git/shallow` lists `a7fda20` (2026-09-21) and `467f7a0` (2026-09-22 19:55), so no commit before 2026-09-21 can be seen. Dates for hours 1–50 therefore come from the headers in `research/narrative/docs/EXPERIMENTS.md`.

**Note count.** There are 76 notes: 30 cover hours 1–50 and 46 cover the work after hour 50.

### Headline judgments (all Judgment)

1. **The question changed four times, but its wording never did.**
   - The stated question has been the same text in `README.md:3-4` and `claims.yaml:5-7` since at least 2026-09-21.
   - The question actually being worked on moved four times:
     - relational shape and operator (h1–5);
     - factor directions and where composition stops (h6–40);
     - instruments and the measurement core (h41–50);
     - after h50, "is the final-token or story-token state a narrative role, or just binding, order or answer-slot?"
   - That last question appears only in the notes. No framing document has changed since 2026-09-21.
2. **After h50, most work answered the previous experiment's caveat.** Of 23 experiments:
   - about 4 aimed at the line's question;
   - 10 addressed the previous experiment's caveat;
   - 4 calibrated a behavioural readout ("elicitor");
   - 4 were behavioural prerequisites.
   No chain declared an end state in advance.
3. **The strongest activation-level positives after h50 are about the answer format, not the story.** Choice-slot replication +0.583, answer-slot patch +1.126 nats and slot cancellation all describe a code for which listed person or plan wins. The notes say so themselves: "not a story edit" (`claims.yaml:364`).
4. **The open problems that serve the stated question most directly were never run.** Real paraphrases and token clouds with Gromov–Wasserstein have been listed since the first hours (`EXPERIMENTS.md:2327-2328`, `:2357`). All 5 claims that were open at the 2026-09-21 triage are still open, while the post-50 work added 5 more.
5. **The program document was set aside without a recorded decision.**
   - The Phase 2 gate decision was "the user's and the program waits on it" (`EXPERIMENTS.md:2095`), and was still outstanding at h49–h50 (`EXPERIMENTS.md:2257-2258`, `:2317`).
   - The post-50 work then went outside `PROGRAM.md` entirely. `PROGRAM.md:24` says "Anything that serves neither is out of scope for this program", and nothing records that decision.
6. **Most narrative documents predate everything after h50.** `README.md`, `WRITEUP.md`, `VISION.md`, `ALGEBRA.md`, `docs/EXPERIMENTS.md`, `docs/QUESTIONS.md` and `docs/PROGRAM.md` were all last changed on 2026-09-21 (commits `a7fda20` and `ad7f788`). Only `claims.yaml` and the notes record the post-50 work.

---

## 1. The top-level question(s) and how the framing changed

| Source | Exact wording | Last touched (git) |
|---|---|---|
| `research/narrative/README.md:1` | Title "Narrative calculus" | `ad7f788` 2026-09-21 |
| `README.md:3-4` | "**Can the relational structure of a narrative be measured in activation space, fit as an operator, and pointed at a domain where the corresponding parts are unknown?**" | same |
| `README.md:38-43` | "If that shape can be measured (stage 2) it can be fit as an operator (stage 3) and pointed at a domain where the corresponding parts are unknown (stage 4). Longer-term this is the activation-level substrate for a narrative calculus: decompose a story into factors, transform them, recompose." | same |
| `README.md:6-15` | Four sub-questions with answers: Q1 shape "Answered: mostly no"; Q2 affine map "Partly"; Q3 factors compose "Yes for some"; Q4 "Can the measurement core reproduce this project's own published numbers?" "Yes, and it refuses some of them." | same |
| `README.md:24-29` | "**Not** generating stories… **Not** claiming the residual stream contains narrative structure *as such*…" | same |
| `VISION.md:1` | "Narrative Calculus: the operator set, mapped to what the toolkit can do today" | `a7fda20` 2026-09-21 |
| `WRITEUP.md:1` | "Narrative factors are directions: measuring, moving, and composing story structure in transformer activations" | `a7fda20` |
| `WRITEUP.md:11-13` | "We asked whether the structure a prompt describes — a relation among parts, or a narrative property such as setting, register, mood, or theme — exists in a language model's residual stream as a geometric object that can be measured, carried to a new domain, composed with others, and used to steer generation." | same |
| `WRITEUP.md:300` | "The gauge/engine boundary is the central fact" | same |
| `docs/PROGRAM.md:20-22` | "**A narrow, defensible research claim**: narrative factors are composable directions, and here is exactly where composition stops. Not "Narrative Calculus." The stopping point (gauge/engine, ~3× norm, engine-specific, tuning-sensitive) is the interesting finding and we already have it." | `a7fda20` |
| `docs/PROGRAM.md:24-26` | Out of scope: "time translation (closed, h38), absence (falsified twice), commutator regimes (no structure), 405B (unreachable)." | same |
| `claims.yaml:4` | `title: Computational narratology` | present at `467f7a0` |
| `claims.yaml:5-7` | Question copied verbatim from `README.md:3-4` | same |
| `claims.yaml:8-10` | Blurb: "Most of what looked like shared narrative structure turned out to be slot position. What survived the controls is narrower, and more interesting, than what we set out to find." | same |
| `claims.yaml:11` | Audience: "mechanistic interpretability · narratology · computational literary study" | same |
| root `README.md:12` | "Can the relational structure of a narrative be measured, fit as an operator, and pointed at a domain where the parts are unknown?" (drops "in activation space" and "corresponding") | — |

**Implicit framing after h50.** It is never promoted to a framing document; it appears only in the notes:
- `propp_spike_prereg.md:5-7`: "Can a decoder's state at an annotated plot-function signal distinguish the same function in a different tale? … It does not test Campbell's Hero's Journey, cross-genre transfer, causal control, or a complete story shape."
- Repeated disclaimers: "not a trope manifold" (`role_swap_prereg.md:8`, `goal_switch_prereg.md:10`) and "Hero's Journey shape/geometry/manifold" (`role_swap_prereg.md:60`, `role_swap_result.md:84`, `reveal_invariance_prereg.md:106`, `goal_relative_prereg.md:116`).
- "a poor candidate for a reusable narrative shape" (`reveal_invariance_prereg.md:8-9`).
- "a behavioral prerequisite for narrative relation geometry" (`fact_flip_twohop_result.md:77`).

**Judgment on the arc.** The framings fall into four groups:
- `README.md`, `VISION.md` and the `claims.yaml` title/audience keep the broad version: a calculus, narratology.
- `PROGRAM.md` explicitly narrowed it ("Not Narrative Calculus") to factor composition and its stopping point.
- `WRITEUP.md` sits in between.
- The post-50 work pursued a third target that is written down nowhere: a reusable narrative-role or trope geometry beyond binding, order and answer-slot confounds.

**Provenance flags (non-negotiable 7).**
- `reveal_order_prereg.md:10-11`: "This is the user's chronological versus late-reveal contrast at miniature-story scale."
- `action_interaction_prereg.md:30-31`: "per Mykola's explicit instruction".
- Neither is labelled as a paraphrase. Git authorship cannot settle it: 142 commits are authored "Mykola Bilokonsky", including agent-written notes (`git log --format=%an`).
- The model-pinning instruction reached `CLAUDE.md` only in `5044a39` (2026-09-23 00:42). Before that, `CLAUDE.md` said "Never include a model identifier in … any artifact pushed to the repository" (diff of `5044a39`). The 2026-09-22 prereg acted on an instruction that contradicted the `CLAUDE.md` of that moment.

---

## 2. Compressed history, hours 1–50

**Phase A: shape → role → relation (2026-09-11, h1–h5).**
- **Stage 2.** Representational similarity (RSA) over six pooled role vectors gave 0.60 at layer 20 (`EXPERIMENTS.md:156`).
- **Shuffled control (h2).** With spans permuted across template slots, content-labelled RSA fell to 0.05 (`:224`). "a 6-point RSA over pooled spans is a position detector" (`:237-238`). Projecting out the slot subspace did not recover content (`:265-271`).
- **Hour 3 (rotated grid).** A constant "which role" baseline scored 1.07, so earlier stage-3 numbers were role identity (`:287-291`). Best-layer selection was shown to inflate results and was dropped (`:291-293`). A role-centred affine relation scored 3.01 against nulls of 3.48–3.54 (`:302-304`).
- **Hour 4.** The role lens worked: rank 1.69 against 3.25 random (`:339`).
- **Hour 5.** The relation lens as a patch was null: −0.02 against −0.19 nats (`:377-378`), "measurable … not … controllable" (`:389-392`).
- **Stood:** role identity is a direction, and the role lens transfers. **Fell:** the content shape.

**Phase B: narrative factors as directions (h6–h13, 2026-09-11).**
- Era and voice lenses scored 1.28/1.31 against 2.11 random. Composition scored 2.03 of 9 (`:421-426`).
- It replicated on 0.5B and Pythia (`:462-471`). Three factors composed to 2.81 of 18 (`:527`). Mood lens 1.28 (`:602`). Theme was a selector at 1.25 but a generator no better than base (`:643`, `:663-669`).
- Multi-layer patching changed nothing (`:701-706`). On the 1.5B instruct model, the homecoming direction triggered refusal (`:727`, `:743-749`). Gemma-9B-it produced legible theme (`:805-811`).
- The first broken instrument appeared here: the cross-talk rank was degenerate (`:432-436`).

**Phase C: recomposition, abstraction, relation at 40 domains (h14–h26, 2026-09-11; Checkpoint 1 at `:112-138`).**
- An era shift "keeps form" at 0.89/0.81 (`:824`); this was later withdrawn at h40.
- SAE (sparse autoencoder) width as abstraction: generality 0.18 vs 0.06, 12/15 merges more general (`:860-864`).
- Relation selector at 40 domains: 2.21 (`:894`, later restated as 2.1692). "the relation was starved, not absent" (`:900-906`).
- Absential ring falsified (`:989-993`). Commutator: divergence is generic, dominance is real, regimes are noise (`:1127-1130`).
- Generative relation lens: helpful but not source-specific (`:1051`, `:1059-1066`).
- GPT-authored grids replicated (`:1154-1160`).
- Source-specific at the selector level, 0.68 paired win (`:1176`, `:1181-1184`); marginal under patching, 54% (`:1206`).
- Abstraction-ladder fixed points are trivial (`:1245-1250`).

**Phase D: generation boundary, time translation, retractions (h27–h40, 2026-09-12/13; Checkpoint 2 at `:7-110`).**
- Generation at 1× norm was null: 0.14 on Llama-70B, 0.27 on Gemma-9B (`:1264`).
- At 3× norm, re-imposed every decoding step, Gemma reached 0.84 (`:1303`) and Llama-70B-Instruct 0.43 (`:1363`).
- Time translation (h28–h38, "~1M agent tokens", `:79`) closed as a "computed register detector" (`:1453`). Three subject-clock negatives were withdrawn as noise-floor artefacts (`:1345`).
- The h34 Llama battery was withdrawn for a batch-row bug (`:1410`, `:1418`). After the fix, tuning sharpens the era selector from 1.50 to 1.06 while theme does not move (`:1428-1435`).
- A padding bug corrupted 76% of h31 (`:1468-1482`).
- h40: stage 14 was residual arithmetic, so writeup claim 6 was withdrawn (`:1538-1547`).

**Phase E: PROGRAM.md Phases 0–2 (h41–h50, 2026-09-17/18).**
- **h41.** The selector effect is not the direct skip path: +1.837 and +3.614 nats (`:1573-1574`).
- **h42.** The abstraction ladder survives its nulls; "flow ordering" was downgraded (`:1620-1636`, `:1654-1663`). Phase 0 gate met, with item 0.3 waived (`:1687-1693`).
- **h43–h47.** Core build: the rediscovery harness caught 9/9, later 12/12, of the project's own bugs (`:1702-1716`). Reproduction table at `:1830-1833`.
- **h47 lexical floors.** "Only era clears its lexical floor." Tense sat exactly on its floor and voice was worse than its floor; the composed gain was −0.04 inside ±1.83 (`:1959-1971`). The h29 3× result gained its missing controls: random 0.1429, no-patch 0.1111 (`:1985-1989`). Phase 1 gate closed (`:1950-1954`).
- **Phase 2 gate.** "cannot be met as written"; "That decision is the user's and the program waits on it" (`:2067-2095`).
- **h48.** All 27 measurements were refused by the ledger (`:2115-2124`). Voice fails its floor on every grid (`:2171-2177`). The permutation arm sits below its null on 25/25 rows (`:2188-2192`).
- **h49.** Arm-band fix (`:2224`).
- **h50.** 15 rows reach the ledger, Qwen-1.5B only (`:2264-2291`, `:2315-2318`).
- **Judgment:** h41–h50 were about the instruments, not narrative.

---

## 3. Every experiment after h50, in order

**Models.**
- Rows 1–9: `Qwen/Qwen2.5-1.5B` at revision `8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16 (e.g. `propp_spike_result.md:15-19`; RTX 3060 Ti at `role_swap_result.md:14`).
- Rows 10–23: `google/gemma-2-9b-it` on NDIF's pinned deployment. NDIF exposes no weight revision; tokenizer snapshot `11c9b309…` (e.g. `remote_goal_behavior_result.md:11`, `goal_reversal_calibration_result.md` artifacts).

**Dates for rows 1–4.** No per-experiment git dates exist. They sit inside the graft commit `467f7a0` (2026-09-22 19:55) and came in through PR #1, branch `local-session-2026-09-22` (merge `0a47819`). They were run on CUDA, which per `CLAUDE.md` began 2026-09-22.

**JUDGMENT column codes:** **Q** = aimed at the top-level question; **C** = follow-up to the previous experiment's caveat; **I** = calibrating the behavioural readout; **B** = behavioural prerequisite.

| # | Date (prereg → result) | Notes | Question asked | Prompted by (quote) | Outcome, key number | Claims | Model | JUDGMENT |
|---|---|---|---|---|---|---|---|---|
| 1 | ≤09-22 (graft) | `propp_spike_prereg/result` | "Can a decoder's state at an annotated plot-function signal distinguish the same function in a different tale?" (prereg:5-6) | Nothing stated. The prereg has no "why"; nothing in EXPERIMENTS or PROGRAM leads to it | Mid-layer balanced accuracy 0.625 vs best text/position baseline 0.369 and layer-0 0.477 (result:28-32). Gain +0.256 [0.170, 0.338], p=0.001 (:35). Full-story minus 200-char context +0.049 [−0.005, +0.126] (:56-57) | propp-function-signal **holds**; propp-full-story-context **open** | Qwen-1.5B | **Q**. The only post-50 test on natural narrative with an external schema and held-out-tale transfer. Recognition, not an operator |
| 2 | ≤09-22 | `role_swap_prereg`, `role_swap_neutral_prereg`, `role_swap_result` | "can a shared activation displacement track a change in a handover's story role when the final action and local wording are identical?" (prereg:6-8) | "a 200-character context retains most accuracy" (prereg:5-6); the Propp result's "The next test should…" (propp result:76) | 0.792 (result:29). Same order 1.000 / reversed order 0.000 (:46). Neutral grid on itself 1.000 (:60). Goal minus neutral 0.208 [0.097, 0.315] (:61) | controlled-role-swap-context, controlled-role-swap-specificity: both **narrowed** | Qwen | **C**, plus a pivot from natural tales to constructed miniatures. The line never returned to Propp |
| 3 | ≤09-22 | `action_interaction_*` | "whether the prior-goal displacement changes when the final action reverses who receives the same object" (prereg:7-9) | "neutral predicates also produced a strong direction and sentence order dominated raw deltas" (prereg:5-7) | Interaction 0.792 (result:37). Goal minus neutral 0.190 [0.088, 0.282] (:40). Neutral on itself 1.000 (:41). p=0.002 (:42) | controlled-action-interaction **holds** | Qwen | C |
| 4 | ≤09-22 19:55 | `goal_switch_*` | "track which fixed worker plan fits the group's current need, when the workers, their plans and the final handover are unchanged?" (prereg:7-9) | "the goal and neutral grids used different actor predicates" (prereg:5-7) | Linked 0.708 (result:36). Linked minus rotated 0.093 [−0.037, 0.227], so the specificity gate fails (:39, :49) | fixed-predicate-goal-switch **narrowed** | Qwen | C |
| 5 | 09-22 19:58 → 20:08 | `consequence_order_*` | "Does an interaction follow which unchanged worker plan would keep people safe … and the order of those conditions is independently reversed?" (prereg:7-9) | "the linked direction also scored on a rotated goal control" (prereg:5-7) | Within clause order 0.954/0.921. Cross-order 0.125/0.097; primary 0.111 [0.079, 0.141]. The direction reverses sign (result:34-38) | implicit-goal-role-fit open → **narrowed** | Qwen | C. The decisive negative: clause order, not consequence, drives the readout |
| 6 | 20:15 → 20:25 | `reveal_invariance_*` | "Can a final event's relation to earlier story facts survive two changes to the telling…?" (prereg:5-9) | "gave a strong direction within one report order that reversed when the clauses traded places" (prereg:5-7) | Double transfer 0.0046 [0.000, 0.014] (result:43). Timing-only transfer 1.000 (:51-54). Recipient-clause word bag 0.875 (:63) | reveal-timing-transfer **holds**; reveal-order-invariance **falsified**; goal-relative-story-role **opened** | Qwen | C. Repeats #5's confound. The "holds" claim sits below its own lexical ceiling (`claims.yaml:260`) |
| 7 | 23:05 → 23:20 | `goal_relative_*` | "track whether a fixed plan helps a fixed story goal when a relevant circumstance changes…" (prereg:8-11) | "Its recipient-clause word bag scored 0.875" (prereg:7-8) | 0.600 [0.519, 0.681], p=0.104, so it fails (result:42-47). Post-hoc geometry correlation 0.275, but the world main effect gives 0.859 (:80, :85) | fixed-plan-circumstance-transfer: entered **falsified**, reworded to **narrowed** two minutes later (git `13793be` → `5c7ea84`) | Qwen | C. In its own words it "does not close that claim" (result:98-99) |
| 8 | 23:26 → 23:28 | `goal_relative_behavior_*` | "whether the same base model can choose the plan that serves the story's stated goal" (prereg:7-8) | "did not clear its registered cross-format transfer gate. Before treating that as a limitation…" (prereg:5-7) | Sensitivity control failed (result:28). Accuracy 0.500 (:30). 0/48 pairs right in both worlds (:31) | fixed-plan-behavioral-capacity **opened** | Qwen | I |
| 9 | 23:44 → 23:50 | `elicitor_calibration_*` | Search for a cloze that passes controls "in both name orders" (prereg:3-7) | "The first behavioral cloze failed one of two easy name-swap controls" (prereg:3-4) | "**No cloze qualifies.**" Best was 11/16. Position effect 1.07–3.55 nats (result:24-30) | fixed-plan-behavioral-capacity stays **open** | Qwen | I (calibration of a calibration) |
| 10 | 23:59 → 09-23 00:34 | `remote_goal_behavior_*` | Capacity check on a larger instruction-tuned model (prereg:5-8) | "content-sensitive on average but position-dominated in individual easy controls" (prereg:5-6) | Controls 16/16, smallest margin +7.37 (result:15). Accuracy 66/96, below the 68 gate (:23). Paired shift 40/48, p=0.006 (:24) | fixed-plan-chat-behavioral-capacity **narrowed** | Gemma-9B | I (switch of model) |
| 11 | 00:55 → 01:47 (6 prereg commits) | `goal_reversal_prereg`, `goal_reversal_calibration_result` | "when the facts and two worker plans stay fixed, does changing only the stated goal reverse which worker the model chooses?" (prereg:9-11) | "66/96, below the registered 68/96 … leaves a general valence-by-action rule available" (prereg:5-9) | No story was scored (result:6). Control set V3 28/32; V4 abandoned; V5 12/15, then stopped (:30-32). Before scoring, a frozen shortcut rule already gets 21/24 pairs right (:15) | fixed-plan-goal-reversal-capacity **open** | Gemma-9B | Aimed at the goal-relative claim, but stalled on the readout (I). Even a pass would have sat under a 0.875 shortcut ceiling |
| 12 | 02:02 → 02:28 | `fact_flip_twohop_*` | "Does the model's paired preference move with that fact when the necessary information spans two links…?" (prereg:9-12) | "did not reach its stories: its forced-name readout failed crossed controls … shortcut on 21/24" (prereg:5-7) | 55/64 pairs shift correctly, p=1/256. Direct controls 32/32. 49/64 strict choices. Generation 14/16 (result:29-37) | twohop-fact-flip-behavior **holds** | Gemma-9B | B. A change of task to escape a failing readout. First clean behavioural positive |
| 13 | 03:33 → 04:07 | `goal_route_cross_*` | Do "requested destination and … route facts combine as separate factors" (prereg:6-8) | Same sentence (prereg:6-8); "a behavioral gate for a later activation experiment" (prereg:8-9) | 57/64 joint (result:39). 49/64 strict (:45). Generation 13/16 (:46) | goal-route-cross-behavior **holds** | Gemma-9B | B. This is the goal-change-with-fixed-facts behaviour that #11 failed to reach |
| 14 | 03:42 → 04:23 | `goal_route_activation_pilot_*` | "whether the residual stream carries a shared direction for the factorial goal × route contrast across eight held-out story domains" (result:7) | Conditional: "Run only if the behavioral screen … passes" (prereg:3-4) | Block-16/24 mean +0.0854, p=2/256 (result:31). Interval +0.066 to +0.109 (:33). Block 16 −0.0002, block 24 +0.171 (:46) | goal-route-choice-slot-transfer **holds** | Gemma-9B | **Q attempt**, but the prereg says a positive "would be a shared choice-slot code, not a two-link relation operator" (prereg:33-34). Its stated purpose, deciding whether a larger-grid confirmation is worth doing (prereg:5-6), was never acted on |
| 15 | 04:55 → 05:59 | `choice_slot_control_*` | "whether that direction transfers to simpler and unrelated two-person choices" (prereg:5-7) | Pilot: "Comparable transfer there would identify a generic answer-position code" (pilot result:95) | Route to property +0.543 vs within-property +0.566 (result:32). Route to direct +0.513 (:31). Source-flip null p=25/256 fails, but that null is structurally weak (:38, :45) | generic-choice-slot-explanation **opened** (still open) | Gemma-9B | C. Deflates #14 |
| 16 | 05:17 → 06:31 | `prequestion_route_state_*` | "is it already in the story state before the model reads the answer question?" (prereg:7-9) | The pilot found the direction only at the final token after the question (prereg:3-6) | Bridge-end −0.0036, p=186/256 (result:31). Earlier position −0.0005 (:30). Fitted directions nearly orthogonal, cosine −0.015 (:44) | prequestion-route-interaction: open → narrowed → reworded → **falsified** | Gemma-9B | **Q** (negative). No shared story-state direction; the answer question "assembles or exposes an answer-slot code" (:87) |
| 17 | 06:15 → 06:57 | `choice_slot_replication_*` | Target-label test on eight new property domains (prereg:3-12) | "Its registered source-domain sign null missed p≤.05, but that null is weak" (prereg:6-8) | +0.583 vs internal reference +0.579 (result:30, :35). p=1/256 (:33) | generic-choice-slot-replication **holds** | Gemma-9B | C (statistical power). Confirms the result is "task-general answer-slot geometry" (:68) |
| 18 | 06:46 → 07:48 (amended to 08:42) | `reveal_order_*` | "does the model retain the same goal-dependent choice when the decisive second-hop destination facts arrive after an intervening passage…?" (prereg:7-10) | Crossed screen and location test (prereg:3-7); "the user's chronological versus late-reveal contrast" (prereg:10-11) | Same quartet passes in all three tellings 27/32, p=1/256 (result:32). Near-adjacent quadrant 00 is 4/8, so the gate fails (:43). Late-reveal strict choices 16/32 (:30). Post-hoc plan-A offset +0.849 (:71) | late-reveal-route-choice **falsified**; late-reveal-paired-margin-shifts **holds** | Gemma-9B | B. A recurring telling-order theme, not driven by a caveat |
| 19 | 07:02 → 09:26 | `answer_slot_patch_*` | "whether adding it changes the model's two-name log-probability margin in the predicted direction" (prereg:7-9) | "Readout alignment does not show that the direction affects a choice" (prereg:6-7) | Net +1.126 nats, 8/8 domains, 60/64 prompts (result:32). Random directions −0.058 / +0.093 (:36). Accuracy stays 62/64 (:60) | answer-slot-patch-steering **holds** | Gemma-9B | C. A causal generic bias that "neither edits a narrative role…" (:90) |
| 20 | 07:18 → 11:09 | `story_fact_token_patch_*` | "whether a single residual state at that informative story token can move the later answer toward the other world's route winner" (prereg:9-12) | "a large local factorial interaction immediately after the late-telling route facts" (prereg:6-9); "patches **one story-stage period token**" (answer_slot result:92) | Treatment +0.386 [0.232, 0.547] (result:13, :20). Plan-order control +0.784 (:14), so it fails the 2× control gate (:20). Zero choice flips (:22). Post-hoc: mostly "margin compression" (:24, :34) | story-fact-token-causal-edit **falsified**; story-period-margin-shift **holds** | Gemma-9B | **Q attempt** (causal edit of the story state). Failed specificity |
| 21 | 11:22 → 11:49 | `firsthop_swap_behavior_result` (gate inside `firsthop_swap_patch_prereg`) | Eligibility: does the model read a distant first-hop swap? (firsthop prereg:16) | Previous patch's noun confound (firsthop prereg:3) | 29/32, p=1/256. 109/128 cells correct. 19/32 quartets right in all four cells (behavior result:7, :9) | firsthop-swap-behavior **holds** | Gemma-9B | B / C |
| 22 | 11:22 → 13:48 | `firsthop_swap_patch_*` | "whether one story-token state could transmit a counterfactual route→link assignment" (result:3) | "Its signed margin effect was mainly confidence compression, and a matched plan-order control was larger" (prereg:3) | Treatment +0.600 [0.367, 0.861] (result:13, :19). Plan-order +0.866 (:14). Clause-order +0.079 (:15). Both screens fail (:21). Secondary contrast +0.520 passes (:27) | firsthop-swap-story-patch **falsified**; firsthop-swap-clause-contrast **holds** | Gemma-9B | C. Same failure pattern as #20 |
| 23 | 16:36 → 18:19 | `firsthop_doubleflip_*` | "Does the story-period patch carry a winning-plan-slot code?" (prereg:1) | The slot idea "was proposed after those scores" (prereg:3) | Double flips +0.069 / +0.085, both inside ±0.15 (result:11-12). World minus double +0.515, plan minus double +0.782 (:13-14). Ship domain +0.72 (:19) | firsthop-winning-slot-cancellation **holds** | Gemma-9B | C. Explains the failing control. What the period state carries is an answer-format slot |

**Tally (Judgment).**

| Code | Count | Rows |
|---|---|---|
| Q or Q attempt | 5 | 1, 14, 16, 20, plus the aim of 11 |
| C | 10 | 3, 4, 5, 6, 7, 15, 17, 19, 22, 23 |
| I | 4 | 8, 9, 10, 11 |
| B | 4 | 12, 13, 18, 21 |
| C plus pivot | 1 | 2 |

**Pace.** Rows 5–23 ran from 09-22 19:58 to 09-23 18:21, about 22.5 hours. Two experiments went from prereg commit to result commit in 10 minutes (#5) and 2.5 minutes (#8). Several NDIF windows overlapped: #15 with #16, and #18 with #19 and #20. `PROGRAM.md:149` requires "One agent at a time unless two are provably independent and do not share an NDIF queue". Whether separate agents ran these cannot be read from git.

---

## 4. Chains: experiments that exist mainly to answer the previous one's caveat

**Chain A: is the final-token signal narrative role, or binding and order? (Qwen-1.5B, 7 experiments: #1 → #2 → #3 → #4 → #5 → #6 → #7)**
- **Start.** The Propp result's "The next test should **hold local event wording nearly fixed while changing its narrative role**" (`propp_spike_result.md:76`).
- **Links.** Each next-step paragraph names the next design: `role_swap_result.md:86`, `action_interaction_result.md:81`, `goal_switch_result.md:71`, `reveal_invariance_result.md:85`, `goal_relative_result.md:98-99`. Each fix exposed a new confound:
  - order (`role_swap_result.md:43-46`);
  - neutral binding at 1.000 (`:60`);
  - rotated goals (`goal_switch_result.md:39`);
  - clause order (`consequence_order_result.md:36-38`, `reveal_invariance_result.md:43-54`).
- **Current end.** #7 fails its gate (0.600, p 0.104). The open claim goal-relative-story-role (`claims.yaml:273-279`) was never tested in its own form on Qwen.
- **Stop condition declared in advance?** Each experiment had its own gate, but the chain had none. The only conditional was Propp's "A larger corpus … would follow only if this stricter within-story control clears its lexical and position floors" (`propp_spike_result.md:79`). No miniature cleared it, so the chain never went back to natural tales, even though `consequence_order_result.md:71-72` says "The open full-story Propp context test remains the next route".
- **What closes it.** An activation interaction where the goal flips with the fact wording fixed, which transfers across both sentence orders and beats the measured lexical ceiling. Or retiring goal-relative-story-role.

**Chain A′: the behavioural readout (#8 → #9 → #10 → #11, four experiments, three calibration failures)**
- **Stop conditions were declared and mostly honoured:**
  - "If none passes, record the calibration failure and do not use this base model's name-completion accuracy as a story-understanding measure" (`elicitor_calibration_prereg.md:22-24`);
  - "If this gate fails, stop" (`remote_goal_behavior_prereg.md:38`);
  - "There is no further control replacement in this run: if any V4 control fails, the run stops" (`goal_reversal_prereg.md:168-169`).
- **The one exception.** That last rule was overridden before scoring: "This supersedes Amendment 1's planned no-replacement rule because the battery had a pre-score design flaw" (`goal_reversal_prereg.md:182-183`). The grid went through V1–V5 (`:15-21`).
- **End.** It was abandoned by switching task to #12 (`fact_flip_twohop_prereg.md:5-7`). Two claims were left open: `claims.yaml:289-295` and `:305-311`.
- **What closes it.** Retire both claims (see section 6).

**Chain B: from route behaviour to a generic answer slot (Gemma-9B: #12 → #13 → #14 → #15 → #17 → #19)**
- **Start.** The behavioural gates; #13 calls itself "a behavioral gate for a later activation experiment" (`goal_route_cross_prereg.md:8-9`).
- **Pivot.** At #14 the readout was oriented to the first-listed plan, which by design measures a "choice-slot code" (`goal_route_activation_pilot_prereg.md:33-34`). #15 and #17 then showed that slot is task-general (`choice_slot_replication_result.md:30`, `:35`). #19 showed it is causally a generic bias (`answer_slot_patch_result.md:32`, `:90`).
- **Declared end state.** The pilot was "to decide whether an activation-level confirmation on a larger grid is worth doing" (`goal_route_activation_pilot_prereg.md:4-6`). That decision was never recorded, and every later test stayed on the same eight domains ("conditional on these eight domains", `firsthop_swap_patch_prereg.md:7`).
- **What closes it.** A sufficiency test for generic-choice-slot-explanation (`claims.yaml:337-343`).

**Chain C: can one story token carry the edit? (Gemma-9B: #16 → #20 → #21 → #22 → #23)**
- **Links.** Location null at story tokens (#16) → patch the local fact period (#20; fails against the plan-order control) → move to the first hop to remove the noun confound (#21, #22; fails the same way) → post-hoc slot hypothesis → double flip confirms a listed-plan-slot code (#23).
- **Current end.** `firsthop_doubleflip_result.md:23`: "a new domain and model are needed before generalizing this component."
- **Stop condition.** None at chain level.
- **What closes it.** Either a world-swap patch that beats slot-preserving controls (such as the double-flip arm) by the registered 2× margin, or a recorded decision that single-token edits at this site carry answer-slot rather than route content.

**Chain D: telling and reveal order, a recurring theme rather than a caveat chain (#6 → #12 → #13 → #18)**
- Early vs late reveal shows up in #6 (`reveal_invariance_result.md:51-54`), #12 (`fact_flip_twohop_result.md` early/late halves), #13 and #18.
- **End.** late-reveal-route-choice falsified on one quadrant; paired shifts hold (`claims.yaml:369-383`).
- **Stop condition.** None stated.

**For comparison: a pre-50 chain that did close.** Time translation ran h28–h38 under specs with "an explicit kill condition" (`docs/DELEGATION.md:30`). It ended with "This is the finding the planner predicted and it is the end of the line" (`EXPERIMENTS.md:1453`) and cost about 1M tokens (`EXPERIMENTS.md:79`).

**Judgment.** The post-50 preregs dropped the plan-level kill condition. Each prereg has an experiment gate, but no chain has a pre-declared end state.

---

## 5. What stands now (`claims.yaml`; validator: 42/52 terminal, 10 open)

**Holds (17).**

| Group | Claims |
|---|---|
| Original question | role-identity-direction (:21); role-lens-transfers (:29) |
| Factors | era-clears-floor (:45); generation-recomposition (:117) |
| Natural text | propp-function-signal (:201) |
| Qwen miniatures | controlled-action-interaction (:233); reveal-timing-transfer (:257) |
| Gemma behaviour | twohop-fact-flip-behavior (:313); goal-route-cross-behavior (:321); late-reveal-paired-margin-shifts (:377); firsthop-swap-behavior (:417) |
| Gemma activation / causal | goal-route-choice-slot-transfer (:329); generic-choice-slot-replication (:353); answer-slot-patch-steering (:361); story-period-margin-shift (:393); firsthop-swap-clause-contrast (:409); firsthop-winning-slot-cancellation (:425) |

**Narrowed (10).** clock-depth-gain (:93); theme-generator (:125); core-reproduces (:133); cached-npz-ledger (:193); controlled-role-swap-context (:217); controlled-role-swap-specificity (:225); fixed-predicate-goal-switch (:241); implicit-goal-role-fit (:249); fixed-plan-circumstance-transfer (:281); fixed-plan-chat-behavioral-capacity (:297).

**Falsified (10).** cross-domain-shape (:13); relation-lens (:37); tense-clears-floor (:53); voice-clears-floor (:61); shared-clock (:85); reveal-order-invariance (:265); prequestion-route-interaction (:345); late-reveal-route-choice (:369); story-fact-token-causal-edit (:385); firsthop-swap-story-patch (:401).

**Withdrawn (4).** factors-compose (:69); subject-clocks-absent (:77); era-shift-keeps-form (:101); llama-selector-battery (:109). **Retired (1).** scale-substitutes-tuning (:141).

**Integrity notes, factual.**
- **Composition of the table.** It had 23 rows at the 2026-09-21 triage (18/23 terminal per the `ad7f788` commit message). After h50 it gained 29 rows: 13 holds, 6 narrowed, 5 falsified, 5 open (my tally from the `git log -p` of `claims.yaml`). None of the 5 rows open at triage has moved.
- **Holds claims carved from failed decisions.** Three "holds" claims are components split off a failed registered decision, all marked `pre_registered: true`: late-reveal-paired-margin-shifts (:377-383), story-period-margin-shift (:393-399), and firsthop-swap-clause-contrast (:409-415). The last was a registered secondary, which is legitimate.
- **reveal-timing-transfer.** Holds while its own evidence says "entity–attribute binding remains a sufficient explanation" (:260).
- **Claims reworded after the result while keeping the same id.** `docs/specs/claims_v1.md:62-63` says "a claim that changes *meaning* gets a new id". Cases:
  - **fixed-plan-circumstance-transfer.** At `13793be` it read "A final-event direction … transfers across held-out stories when both plan-fact order and circumstance-cue order change" and was falsified. At `5c7ea84` it became "has a weak positive held-out score…" and narrowed.
  - **story-fact-token-causal-edit.** "moves later … choice toward" (`4382cce`) became "specifically redirects … under the registered causal screen", then falsified (`f9bcb00`).
  - **prequestion-route-interaction** was rescoped (`432566c`).
  - **firsthop-winning-slot-cancellation.** "because the two changes preserve…" became "consistent with preserving…" (`d9bdfcb`). This rewording made the claim more cautious.
- **Missing rows.** `WRITEUP.md` standing claims 3, 5, 6, 7, 9, 10 and 11 have no `claims.yaml` row:
  - 40-domain relation selector 2.1692 (`WRITEUP.md:28-32`);
  - factors differ by depth (`:51-53`);
  - abstraction as quotient (`:54-60`);
  - shallower factor dominates (`:61-62`);
  - gauge/engine boundary (`:75-79`);
  - 70B cap (`:80-81`);
  - tuning sharpens era (`:82-88`; it appears only inside `claims.yaml:115`'s superseded_by text).
  
  Also missing as an open row: the human-written grid (`WRITEUP.md:280-282`, `PROGRAM.md:96-107`).
- **relation-lens conflict.** It is falsified on h5 evidence (`claims.yaml:37-43`), while `WRITEUP.md:121-123` calls the relation operator "Partial" and claim 3 calls it "a working selector".

---

## 6. The 10 open claims

The cost classes follow your brief. Local ≤1.5B runs since 2026-09-22 have used the RTX 3060 Ti, and weights for Qwen2.5-1.5B and 1.5B-Instruct are cached (`EXPERIMENTS.md:2268-2270`). In this container `cache/` holds only Qwen2.5-1.5B, about 1.8 GB. The ignored activation caches the notes cite (`cache/goal_route_cross/...` etc.) and `.venv312` are not present here.

| id (`claims.yaml`) | What would settle it | Cost class | Serves the top-level question? (Judgment) | Reachable? (Judgment) |
|---|---|---|---|---|
| depth-fraction-confound (:153) | Generation-level layer sweep on Llama-3.1-70B-Instruct at 3× norm, re-imposed every step (`EXPERIMENTS.md:1370`, `:2360`; `PROGRAM.md:111-120`; `WRITEUP.md:286-288`) | NDIF 70B. Phase 4 budget ~300k tokens with 20–25% expected job loss (`PROGRAM.md:120`); h33 took ~2 h of NDIF (`EXPERIMENTS.md:1370`) | No. It serves the factor/gauge–engine product | Yes. The 70B pair is PINNED RUNNING (`results/ndif_pinned.txt`), and shame-axis used Llama-3.1-70B on 2026-09-23 (`024fc4a`) |
| permutation-arm-below-null (:161) | Already measured as worded: 25/25 rows below null, sign test p≈3e-8 (`EXPERIMENTS.md:2188-2189`). What remains is the mechanism ("partly a norm ranking", `:2190-2192`): compare centred and uncentred ranking on cached Qwen grids | Local ≤1.5B, CPU-cheap | No (instrument hygiene) | Yes. Judgment: could be marked holds now, with a separate mechanism claim |
| mood-voice-interference (:169) | Write a mood × voice grid and run it against measured lexical floors. Evidence says "specified" (:172), but only a one-line question exists (`EXPERIMENTS.md:2341`). No spec or grid file | Local ≤1.5B plus stimulus writing (100k–300k tokens, `DELEGATION.md:118`) | No | Technically yes. But voice "does not separate" from its lexical floor on every grid (`EXPERIMENTS.md:2171-2177`), so interference with voice is ill-posed. Retirement candidate |
| paraphrase-effective-n (:177) | Real per-domain paraphrases of `holonic_v2`; rerun content-labelled stage-2 RSA and stage 3 (`EXPERIMENTS.md:2327-2328`) | Local ≤1.5B plus stimulus writing | **Yes, directly** (stages 2–3) | Yes. h16 already raised effective n through more domains (3.01 → 2.1692) but never tested the content *shape* |
| token-cloud-correspondence (:185) | Token-level clouds with Gromov–Wasserstein matching, no correspondence assumed (`EXPERIMENTS.md:2357`, `:262`) | Local ≤1.5B; needs per-token extraction and a null | **Yes, directly** (stage 2 without the slot confound) | Needs new tooling: the `ot` (POT, Python Optimal Transport) library is not installed (`import ot` fails in `.venv`), and there is no spec |
| propp-full-story-context (:209) | A tighter interval on full-story minus local context (now +0.049 [−0.005, +0.126], `propp_spike_result.md:57`). Needs more annotated tales or a held-wording manipulation in natural tales (`:76`) | Local ≤1.5B | Yes, partly. The only natural-narrative relational test | Not with the current corpus: ProppLearner has 15 tales (`propp_spike_prereg.md:9-15`). A Gemma rerun on the same 53 events would not fix n |
| goal-relative-story-role (:273) | An activation direction that follows goal-relative role with the fact wording fixed, above the lexical ceiling. Evidence (:276) still cites only reveal-order and was not updated after #7, #11, #13–#16 | NDIF Gemma-9B (256-prompt grids, one job each) | **Yes**. The de facto central claim after h50 | Partly blocked: the final token reads a generic answer slot (#17) and story tokens are null (#16). Needs a readout position and design not yet specified |
| fixed-plan-behavioral-capacity (:289) | A name-completion cloze passing 16/16 crossed controls on Qwen base | Local ≤1.5B | Indirect | By its own registered rule, no: "do not use this base model's name-completion accuracy" (`elicitor_calibration_prereg.md:22-24`). Retirement candidate |
| fixed-plan-goal-reversal-capacity (:305) | A fresh, independently fixed control battery that passes (`goal_reversal_prereg.md:169-171`), then story scoring | NDIF Gemma-9B | Indirect | Three batteries failed. A pass is capped by a 21/24 shortcut ceiling (`goal_reversal_calibration_result.md:15`). Functionally superseded by goal-route-cross-behavior. Retirement or withdrawal candidate |
| generic-choice-slot-explanation (:337) | Sufficiency test. Project the property-trained direction out of the route interaction vectors and re-run held-out transfer; zero residual means generic is sufficient. Or a causal version with the property direction patched into route prompts | Offline on cached states, or NDIF Gemma-9B for the causal version | Only negatively (it deflates the route result) | Yes and cheaply, if the ignored caches on the local machine survive. They are not in this container |

---

## 7. Stale or contradictory documentation

**`research/narrative/README.md`**
- Points to a nonexistent `RESULTS.md` (:50, :95, :100, :102). The file does not exist anywhere in the repo.
- Has two "## Documents" sections (:93-98 and :104-111). The first points to `docs/ALGEBRA.md`, which is missing; the file is `research/narrative/ALGEBRA.md`.
- Stage rows 5–6 are orphaned below "Prompt format", outside the ladder table (:81-82).
- Stage 3/4 cells are stale: "weak relation transfers (rank 3.0…)" (:51) and "relation-content patch is null" (:52), versus h16's 2.1692 and h20/h25.
- Stage 5/6 cells and Q3 "Era composes" (:12) conflict with factors-compose being withdrawn (`claims.yaml:69-75`).
- Setup commands use paths that no longer exist: `scripts/extract_grid.py`, `scripts/stage2.py`, `scripts/stage3.py`, `prompts/holonic_v1.json` (:62-64). They now live under `scripts/narrative/` and `research/narrative/prompts/`.
- "Checkpoint 2 … is the authority on what currently stands" (:33-35) conflicts with `docs/specs/claims_v1.md:3-5`, which makes `claims.yaml` the single source. Checkpoint 2 also predates all post-50 work.
- Nothing after h50 is mentioned.

**`WRITEUP.md`**
- "Fourth draft, after 46 logged stages" (:3), yet it contains stage-47/48 text (:36-50).
- Points to `RESULTS.md` (:3) and `docs/ALGEBRA.md` (:5).
- Instrument count disagrees with itself and with `INSTRUMENTS.md`: "four" (:5-6) vs "Five" (:268) vs "**Seven**" (`docs/INSTRUMENTS.md:3`).
- Says "eleven things stand, six fell" (:16), but the "Fell" list has seven bullets (:92-119).
- "Next" (:298-310) names the 70B generation arms and the human-written grid; neither was done.
- Paths `results/notes/*.md` and `scripts/stage*.py` are stale (:314-317).
- Claim 6 is still under "Stand" (:54-60), while `EXPERIMENTS.md:2082-2087` says it "is not to be restated until it clears a floor it was never measured against".
- Absence is "Null, not falsified" (:261-262) but `PROGRAM.md:25` says "absence (falsified twice)".

**`ALGEBRA.md`**
- Cites `RESULTS.md` (:4-6).
- L1 and compose are still "measured" against chance, 2.81/18 (:90-92, :133), although the comparison to chance was withdrawn at h47.
- L5 says "12/15" (:137); h26 and h42 give 13/15.
- L7 says the ordering is "measured" (:139); h42 downgraded it (`EXPERIMENTS.md:1631-1636`).
- The mapping table has "recompose (address shift) … measured" (:193) while L4 says the gauge evidence was withdrawn (:136).
- `rotate` is given as "2.21" (:53, :169, :185); the canonical value is 2.1692.
- `rotate` is called "patch untested at scale" (:185), but :53 records patches at h20/h25.

**`VISION.md`**
- Cites `RESULTS.md` (:6).
- Its RG paragraph says "the flow is an ordering" (:106), which h42 downgraded.
- "Generative reach is bounded by the model" (:110) was rewritten by `WRITEUP.md` claim 11 into a tuning effect.

**`docs/EXPERIMENTS.md`**
- Header still says "Qwen2.5-0.5B, Qwen2.5-1.5B, CPU, float32. Grid: holonic_v1.json" (:3-5).
- Checkpoint 2 is titled "2026-09-12, after 38 stages" (:7) but was amended in place with h39–h47 content.
- Open problem 8 still lists "re-check hour 8's tense control (1.44); correct the stale `ndif_pinned.txt`" (:2360); both were done at h39 (:1495-1496, :1503-1504).
- Item 4g has "key pending a fresh session" (:2338-2340).
- No Checkpoint 3 exists, although `PROGRAM.md:85-88` requires it.

**`docs/QUESTIONS.md:3-6`** claims the ordered list "has been maintained continuously since hour 1"; it stops at h50.

**`docs/INSTRUMENTS.md`**
- :3 says "Seven … §1, §2, §3, §4, §4b, §6 and §7", then :5-7 calls the post-norm residual "A seventh", which is an internal contradiction.
- :329-334 says the abstraction ladder "has no permutation null", which is stale since h42.
- `CLAUDE.md:7` says "the five instruments".
- The `ad7f788` commit message promised the count "cannot drift again".

**`claims.yaml`**
- The header comment says "Triaged from Checkpoint 2" (:1-2), but 29 rows come from notes.
- :172 overstates the mood × voice grid as "specified".
- :276's evidence is stale.
- Rows reworded after the result while keeping the same id (section 5).

**`docs/PROGRAM.md`**
- Phases 3–5 never started. The Phase 2 gate decision is unrecorded (`EXPERIMENTS.md:2095`, `:2257-2258`).

---

## 8. Cost records

**Per hour (`EXPERIMENTS.md`).** No costs are recorded for h1–h25.

| Hour | Cost | Line |
|---|---|---|
| h26 | ~300k tokens, ~270 NDIF jobs | :1252 |
| h27 | ~230k | :1272 |
| h28 | ~170k | :1292 |
| h29 | ~125k | :1309 |
| h30 | ~150k | :1325 |
| h31 | ~115k, 15 min | :1339 |
| h32 | ~160k, 35 min | :1353 |
| h33 | ~115k, ~2 h NDIF | :1370 |
| h34 | ~130k, ~45 min NDIF | :1384 |
| h35 | ~300k (480 hand-written passages), ~30 min | :1406 |
| h36 | ~180k | :1420 |
| h37 | ~170k, <1 h NDIF | :1439 |
| h38 | ~220k, ~43 min | :1455 |
| h39 | ~235k, ~70 min | :1507 |
| h40 | ~135k, ~35 min | :1556 |
| h41 | ~240k, 3 h 22 min | :1613 |
| h42 | none recorded | — |
| h43 | ~190k, ~45 min | :1753 |
| h44 | ~225k, ~55 min | :1812-1813 |
| h45 | ~370k, ~2 h 45 min, 168 NDIF jobs | :1882 |
| h46 | ~515k, ~2 h 10 min, 7 jobs | :1940 |
| h47 | ~3 h 10 min, ≈250 + ≈290 NDIF jobs; tokens not recorded | :2057-2062 |
| h48 | ~353k, 41 min | :2210 |
| h49 | ~143k, 11 min | :2257 |
| h50 | ~187k, 12 min | :2320 |

**Aggregates.**
- Time translation: "~1M agent tokens" (:79).
- My sum of the recorded figures for h26–h50 is ≈4.96M tokens, excluding h42 and h47.

**Program budget vs recorded actuals** (`PROGRAM.md`; my arithmetic):

| Phase | Budget | Recorded actual |
|---|---|---|
| Phase 0 | ~250k (:57) | ≥240k |
| Phase 1 | ~500k (:77) | ≥1.30M for h43–h46, plus h47 unrecorded |
| Phase 2 | ~150k (:92) | ≈683k for h48–h50; h48 itself flags "more than twice … budget" (`EXPERIMENTS.md:2210`) |
| Whole program, 5 phases | "Roughly 1.7M" (:160) | Phases 0–2 alone recorded ≈2.2M |

**After h50.**
- No token or wall-time cost is recorded in any note or summary JSON. I checked every post-50 `results/*summary*.json` for time and cost fields; only model and device fields exist.
- This breaks `PROGRAM.md:145-146`: "Every RESULTS entry states … cost."
- The only proxies are NDIF job counts stated in the notes:
  - fact_flip: 192 + 8 + 32 generations;
  - goal_route_cross: 384 + 16 + 64;
  - the activation pilot: 264;
  - choice_slot_control: 128 scored + 264 activations;
  - prequestion: 264;
  - choice_slot_replication: about 520;
  - reveal_order: 600 (`reveal_order_prereg.md:43`);
  - answer_slot_patch: 896 (`answer_slot_patch_result.md:15-18`);
  - story_fact: 1,024 + 256 (`story_fact_token_patch_prereg.md:107-108`);
  - firsthop: 128 + 896 + 256 (`firsthop_swap_patch_result.md:5`);
  - doubleflip: 1,024 (`firsthop_doubleflip_result.md:5`);
  - remote_goal: 208 rows (`remote_goal_behavior_result.md:9-11`);
  - goal_reversal: 56.
- Those sum to roughly 7,500 Gemma-9B NDIF jobs (my arithmetic). The wall-clock proxy is about 22.5 hours of commit time for rows 5–23.
- General guidance: "Agent cost varies 100k–300k tokens. The expensive ones hand-write stimuli" (`docs/DELEGATION.md:118`).
