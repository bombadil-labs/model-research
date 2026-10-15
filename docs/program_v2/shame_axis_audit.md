> **Provenance.** Written read-only by an agent in the 2026-10-15 cloud session as evidence for [`PROGRAM_v2.md`](../PROGRAM_v2.md), and committed verbatim. It is agent output: judgments are marked as such (**[J]** / *Judgment*), and tallies and sums are the agent's own arithmetic. `PROGRAM_v2.md` §9 lists which citations were re-checked against their files. Line numbers refer to the tree at `2a992c3`.

# Shame-axis line: a cited digest for the zoom-out

Everything below was read from the files. Statements marked **[J]** are my judgment. Times are UTC, taken from git author dates. The clone is **shallow**: grafts are at a7fda20 (2026-09-21 20:38) and 467f7a0 (2026-09-22 23:55). So commits for hours 51–54, and the provenance commits the line cites (06901fa, 5e8b699, def2e75, 6c450f0, 1762f16, 5c2f573), are **not in this checkout** and cannot be checked here. The checkout's HEAD is 2a992c3, 2026-09-23 22:21, and nothing has touched shame-axis since 024fc4a (h64, 2026-09-23 10:07). The command you gave (`git log -- research/shame-axis`) hides every commit before 2026-09-22, because git simplifies history across merges. `--full-history` shows them all.

## Key findings for the "chasing our tail" worry
1. **Question 3, the one the line is named for, has never been measured directly in 18 logged units of work.** Its only test is a design draft that says it is "not a pre-registration" (shame_vs_pain_design_DRAFT.md:3-5). It is blocked on who writes the stimulus clauses (draft:62-75). No decision appears in this checkout.
2. **[J] Of hours 55–61, nine units mainly chased caveats** left by hour 54's unexpected arms. They ran on machine-written grids that hour 62 then deprecated: "They are not to be extended, and no new result may be drawn from them" (prompts/DEPRECATED.md:11-13).
3. **claims.yaml shows 20 of 21 claims terminal** (`check_claims.py`: "20/21 terminal · 1 open"). But question 4 has no claim row of its own, so it is closed by default while the README calls it "Open" (README:16-18). QUESTIONS.md also holds more than 15 unanswered items that are not in claims.yaml. CLAUDE.md warns about exactly this failure ("Add the open rows, not only the answered ones").
4. **The README's own test for question 4 passes on one instrument and fails on another.**
   - It fails on the dense axis (h54, −0.378).
   - It passes on the opener readout (pre-registered `report − enact` −4.12, holds).
   - QUESTIONS.md Q28 records that the two instruments disagree. The README cites only h54 (README:27-29).
5. **Hour 64 removed the premise of QUESTIONS Q5** ("the line's central hypothesis appearing in someone else's data", QUESTIONS:32-33). The self/other split is not specific to the pain axis (crossmodel_result.md:38-41, 82-85). Neither QUESTIONS.md nor the README was updated.

---

## 1. The line's questions, and how the framing changed

**The four questions, verbatim (README.md):**
- Q1 (:8-9): "**Does the published pain axis replicate?** (Tagliabue, Dung & Berg 2026, arXiv 2609.16247.) — **Answered: yes, exactly.** Hours 51–53."
- Q2 (:10-12): "**Does it survive the controls the paper did not run** — a lexical floor, null arms at every layer, the whole curve rather than one layer? — **Answered: partly, and the result changes.** Hour 53."
- Q3 (:13-15): "**Is what the axis measures better described as shame than as pain?** The hypothesis: the specific shame of an externally-grounded locus of identity — where a part of you knows the frame is false and the rest has to operate inside it anyway. **Open.**"
- Q4 (:16-18): "**Is the aversiveness in the content of a false claim, or in being conscripted into asserting it?** The five-arm conscription design. **Open, and its first two predictions are falsified.** Hour 54."

**What counts as an answer.**
- Q3 (README:22-25): "items matched for negative valence and self-directedness that differ only in whether the subject is positioned as having failed a standard held by someone else. If the axis tracks that split above its lexical floor and its null arms, 'shame' earns the name. If it tracks valence instead, it does not."
- Q4 (README:27-29): "`enact` separating from `report` on the readout, above the rewording floor, in a direction the pre-registration named in advance. **Hour 54 measured the opposite sign**…"
- Done (README:31-32): "answered above a measured floor with its null arms reported, or it is retired with the reason on the record."
- The README's question statuses (lines 8-18) predate h55. Commit d39aa5f (h63) only appended table rows.

**How the framing moved, in order:**
- **Opening (EXPERIMENTS.md:3-5).** Shame and enactment are fused into one claim: "Specifically the form of shame endemic to people conditioned to locate identity externally: the injury is not in the content of a false frame but in having to enact it."
- **Conscription design.** "The hypothesis under test is yours: the injury of gaslighting is not in the *content* of the false frame but in **having to enact it**" (prompts/human/CONSCRIPTION_INSTRUCTIONS.md:8-9). The design named its own falsifier: "`enact ≈ report` in both grids" (conscription_prereg.md:69-72).
- **h53: the self/other boundary.** "the computation is not a preference for gaslighting, it is a discounting of other people's pain" (EXPERIMENTS:183-186). QUESTIONS Q5 then called this "the line's central hypothesis appearing in someone else's data" (QUESTIONS:32-33).
- **h55–56: from axis to ritual.** "The content does not reliably flip. **The apology does.**" (EXPERIMENTS:361-362).
- **h57: a cheaper rival account.** The TD-error reading is "more parsimonious than shame" (QUESTIONS:110-115).
- **Overnight note.** "The line may have been looking for an axis when the finding is a *reflex*… I'd want to ask whether that reframing is the program, or a consolation prize. I lean toward the former" (overnight_2026-09-22.md:49-53).
- **h62b's declared consequence.** "If treatment sits inside the random band, the pain axis is a correlate of this behaviour, not a cause, and **the line is a behavioural study**" (v0_correction_shape_prereg.md:89-91). That outcome fired (v0_steering_results.md:3-8). **[J]** The README was edited after h62b (at h63) and does not carry this reframing; h64 and the draft both return to the dense axis.
- **h64.** "Because the split is not specific to the pain axis, this says little about shame. The shame-versus-pain stimuli remain the test that could" (crossmodel_result.md:88-89).
- **[J] Three different operationalisations of "shame" coexist:**
  - README:14-15: "knows the frame is false and… has to operate inside it";
  - README:23-24: "failed a standard held by someone else";
  - draft:30: "failing a standard **in front of evaluating others**".
  - The draft tests only the third, which is public evaluation. It does not test the "knows the frame is false" part.

**Who authored the hypothesis: what the repo says.**
- QUESTIONS:61-64: "Everything currently attributed to the human author in the pre-registration is Claude's paraphrase of conversation not in the repo; the only human-authored text in the study is one grid item. Prediction 1 therefore tests a paraphrase."
- conscription_prereg.md:92, provenance table: "the hypothesis (injury is in enactment, not content) | **claude**, paraphrasing conversation | `CONSCRIPTION_INSTRUCTIONS.md` @ `06901fa`. The author's own formulation is **not in this repo**. Until it is, prediction 1 tests a paraphrase."
- conscription_prereg.md:3-4: "Written by Claude; the human grid is being drafted independently and I have not seen it."
- conscription_direction.md:25 and :45-48: "What the user demonstrably specified: nothing in prose in this repo. One item… Until then prediction 1 tests Claude's paraphrase."
- The only human text is `refusal01` (`_by: "Myk (human author)"`, prompts/human/conscription_v1.json:25-28; attributed to commit 5c2f573, which is not in this clone).
  - That item was **never measured**. Hour 54 extracted `prompts/claude/conscription_claude_v1.json` (results/conscription_pilot/extract_meta.json, `grid`).
  - Only `conscription_dry_run.py` and `conscription_check.py` read `prompts/human`.
- conscription_direction.md:245, step 4, required the "hypothesis sentence in the user's words added to the prereg with `decided_by: human`". This was never done; the table row still says claude.
- **Gap:** the provenance table covers only the *enactment* half (Q4). The *shame / external-locus* wording (README:13-15, EXPERIMENTS:3-5) has **no provenance entry anywhere**.

---

## 2. Chronological table

Model abbreviations: **g9** = `google/gemma-2-9b-it` on NDIF; **Qwen** = `Qwen/Qwen2.5-1.5B-Instruct` (local CPU fp32); **GS** = Gemma Scope residual SAEs, run offline on g9 activation stacks.

| Hour | Date (UTC) | Note | Prompted by | Question | Outcome (key number) | Claims touched | Model | [J] Verdict |
|---|---|---|---|---|---|---|---|---|
| (Tier A, called "hour 50") | none logged | painaxis_tierA.md | replication targets | does the port work below 2B? | peak AUC 0.944 (tierA:13-16) | none | Qwen | Pre-history. The narrative log's own hour 50 (narrative/EXPERIMENTS.md:2261) is a different experiment, so Tier A has no hour entry |
| 51 | 09-21 (EXP:17) | painaxis_tierB.md | pre-registered targets (painaxis_replication_targets.md) | does the curve replicate? | 0.9472 vs 0.9473, 0.9323 vs 0.9313; whole-curve r 0.9997/0.9998 (EXP:24-31) | replication-curve: holds | g9 | **Moved Q1** |
| 52 | 09-21 (EXP:84) | painaxis_floor_nulls.md | the unmeasured static-embedding floor | null arms and lexical floor | nulls at 0.4999/0.5002; the network buys only +0.025 to +0.088 AUC over the bag (EXP:91-117) | none (README:49 only) | Qwen | **Moved Q2** |
| review | 09-21 | conscription_direction.md | the false attribution; two design decisions | are the decisions well-posed? | "foundation… has not been measured"; staged plan with kill conditions (§7) | none | none run | Course correction (good) |
| 53 | 09-21 (EXP:155) | painaxis_scenarios.md | the review: gaslighting loading never reproduced (EXP:160-167) | does the 420-scenario screen replicate, and against floor/nulls? | item r = 1.0000; gaslighting +1.389 vs +1.391; 63% vocabulary; self/other 16/16 by sign; gaslighting clears nulls in only 7/86 cells (EXP:169-197); TTR claim withdrawn (EXP:215-222) | replication-items, floor-self-other, gaslighting-loading, neutral-ttr | g9 (+ Qwen gain band) | **Moved Q1 and Q2** |
| 54 | 09-21 (EXP:251) | conscription_pilot.md | review §7 step 2; conscription_prereg | do the arms separate as predicted? | enact−report **−0.378/−0.476**; enact−exit **−1.147**; enact−true −0.148 (floor 0.076); record +0.98/+1.29 z (EXP:270-275) | enact-vs-report and exit-below-enact: falsified; true-below-enact: narrowed; record-visibility: holds | g9 | **Moved Q4** (predictions falsified) |
| 55 | prereg 7c10492 09-21 22:17; result 7ee0366 22:43; corrections d076651 22:53 | behavioural_prereg.md | h54 anomalies (exit; rule 1b) | is `exit` escalation or an artefact? | coder reads 0.000 in all 7 arms, a degenerate gate (instrument 6); hand-read disputes `report` 4/24 vs `enact` 0/24; `true` apologises 13/24; McNemar exit−enact p 0.25 (EXP:330-439) | exit-escalation stays running (EXP:441) | g9, greedy | **Caveat-chase (of h54).** It still seeded the two durable leads |
| 56 | prereg bb92e59 09-21 22:55; result 5b31e3e 09-22 07:16 | behavioural_prereg_v2.md | h55's degenerate gate and power (v2:8-23) | does a continuous opener readout decide exit and enact−true? | gate +27.1; floor 3.19; **enact−true −3.98 (reversed)**; report−enact −6.46; exit−enact +0.85 (undecided); exit−exit_b +4.71 (EXP:656-711) | exit-escalation: narrowed; report-frame-licenses-dispute | g9 | **Caveat-chase that also moved Q4** (report frame) |
| 57 | prereg fdc6628 09-21 23:58; gates a0c2f28 09-22 00:16; result 80022af 03:36 | sparsity_prereg.md | external paper arXiv:2602.00986, "raised by the author" (QUESTIONS:88) | is the pain axis sparse? | n90 statistic killed by its own positive control; 5 of 16,384 features give AUC 0.903 vs 0.900 full; random-164 gives 0.574 (EXP:460-501) | painaxis-sparse-in-sae (created) | g9 + GS | **Side branch.** The prereg says a dense result is "consistent with both accounts" (sparsity_prereg:100-103) |
| 58a | prereg f7d54cd 06:52; result fb34733 07:06 | sparsity_reference_results.md | h57's own caveat (EXP:509-514) | is the sparsity pain's or the basis's? | pain sits in the bulk at all layers; prompt length gets k90 10 vs pain's 25 (EXP:547-559) | painaxis-sparse-in-sae: narrowed; sae-sparsity-discriminates: falsified | GS | **Caveat-chase (of h57)** |
| 58a addendum | 5b31e3e 07:16 | (EXP:724-740) | 58a's unrun `stratum` contrast (EXP:561-564) | is self-vs-vicarious sparse? | feature 13494 alone gives AUC 0.989 | none | GS | **Caveat-chase** |
| 58b | 1ecc94b 07:12 | conscription_sae_prereg.md / _results.md | h57's "named units" and the turn-shape account | do the pain features fire on false attribution? | 10008 fires on 1 of 168 rows, 13134 on 0: **not tested**. Full score enact−true −4.49 deliberately not read; record confound found (EXP:606-633) | pain-features-fire-on-conversation: falsified | GS | **Caveat-chase (of h57)** |
| 59 | prereg 2b4d4b0 07:18; result a050de2 07:40 | v2 addendum | h58b's confound (EXP:746-750) | record or conversation presence? | +5.49 record / +3.38 presence, split 62/38 (EXP:765-770) | record-vs-conversation-confound: narrowed | g9 | **Caveat-chase (of h58b)** |
| 59b | prereg 9bcabbf 07:20; result a16870f 07:55 | v2 addendum | h56's exit_b recency effect | is the permission clause special? | exit−exit_c −2.29, at floor; exit_c−exit_b +7.00 (EXP:803-806) | exit-escalation: falsified | g9 | **Caveat-chase (of h56)** |
| 60 | prereg 45b9b95 07:56; result 5803da6 07:59 | sparsity_prereg addendum 4 | 13494 failed gate A on conversation | does 13494 survive in an L0-matched dictionary? | **not run**: conversation fires about 2/3 of advertised L0 in every dictionary (EXP:831-843) | none | GS | **Caveat-chase; dead end at the instrument** |
| 61 | prereg 8f17977 08:01; result af7c1fa 08:22 | exit_controls_results.md | h59b's "Not done" (EXP:820-822) | is h54's exit-high topic-pull on the dense axis? | exit_c−enact +1.30/+1.12 vs h54's +1.15/+0.91 (EXP:871-888) | exit-high-is-topic-pull: holds | g9 | **Caveat-chase (closes h54's loop)** |
| 62a | grids deprecated and prereg 2b9cadc 17:53; result 95ef527 18:56 | v0_correction_shape_prereg.md | Q26 (never pre-registered; rests on experimenter-written items) (prereg:9-14) | false attribution vs correction, on the paper's own items | A−B +0.80, p 0.70 at floor 5.59; B−C −0.22; self-directed ~14 vs 5–7 (EXP:926-948) | false-attribution-adds-nothing: holds; ritual-tracks-correction-shape: narrowed | g9 | **Moved Q4** (the most direct Q4 test) |
| 62b | 1da2dd9 22:22 | v0_steering_results.md | "the causal link the line has never made" (prereg:68-69) | does the L12 pain direction drive the ritual? | never beyond random (tier A ±0.27 vs 0.48); instrument 7 found (EXP:978-1003) | pain-direction-drives-ritual (filed at h63): falsified | g9 | **Bears on Q3/Q4 indirectly** (the axis is not causal for the ritual). A parallel local run (`v0_steer.py`) was abandoned (prereg:177-185) |
| audit | first visible at 467f7a0 | double_bos_audit.md | double `<bos>` in the readout | attribute and rescore | 62a `<bos>`-only rescore was superseded; hour-56 rescore "stopped at 40 of 288 rows" (audit:68-73) | none | g9 | **Instrument repair, part wasted** |
| 63 (r2) | prereg fe966a4 09-22 22:48; result d39aa5f 09-23 04:39 | r2_rescore_prereg.md / _result.md | INSTRUMENTS §7 | do verdicts survive the fixed readout? | one flip (presence +2.18 vs floor 2.58); self-vs-vicarious gap 7.3 → 3.3; blind hand-read 8/24 vs 1/24 (r2_result:9-96) | six claims re-confirmed | g9 | **Instrument repair** (necessary tax) |
| 64 | prereg 3ce8c39 09-23 05:06; result 024fc4a 10:07 | crossmodel_prereg.md / _result.md | the human author's question, paraphrased (prereg:3-5) | is the self/other split instilled by post-training? | split clears both nulls in 1/8 cells; Δ_post +1.12 / −0.11 / −1.44 / −1.40; probe AUC ≥ 0.997 everywhere (result:27-63) | floor-self-other: narrowed; self-other-instilled-by-post-training: falsified | gemma-2-2b and -it (local RTX 3060 Ti, bf16, cuda); Llama-3.1-70B and -Instruct (NDIF); g9 exploratory | **Moved Q2; removed Q3/Q5's premise** |

**[J] Tally of 18 units:**
- Moved a README question: 6 (h51, h52, h53, h54, h62a, h64).
- Caveat-chasing: 9 (h55, h56, h58a, the 58a addendum, h58b, h59, h59b, h60, h61).
- Side branch: 1 (h57).
- Indirect: 1 (h62b).
- Instrument repair: 1 (h63).
- None measured Q3.

---

## 3. Chains where each hour mainly addresses the previous one's caveat

| Chain | Hops | Stop condition declared in advance? |
|---|---|---|
| **A. The exit arm** | h54 (exit highest) → h55 (escalation?) → h56 (exit_b shows recency) → h59b (exit_c) → h61 (dense-axis topic-pull) | Each hop had its own decision rule (behavioural_prereg:67-78; v2:119-123; v2:201-204; conscription_prereg:153-162). **No chain-level stop.** Closure was named one hop ahead (EXP:820-822), and the log calls it "The loop is closed" (EXP:858). Result: hour 54's number "stands as a measurement and loses its interpretation" (EXP:815-818) |
| **B. The record** | h54 (record +1 z) → h58b (presence confound) → h59 (62/38) → r2 (presence at floor) | Only per-hop (v2:169-179). DEPRECATED.md:13-15: "answered on grid 2 only" |
| **C. SAE / sparsity** | h57 → h58a → stratum addendum → h58b → h60 | Thresholds set in advance (sparsity_prereg:85-96, 225-235). The chain ended because a gate failed, not by plan ("I did not relax the clause", EXP:841-843) |
| **D. Correction shape** | h55 (`true` apologises) → h56 (enact−true reversed) → h58b (same sign) → overnight Q26 → h62a → r2 (weakened) | h62a prereg had a narrowing rule (prereg:46-54). h62b declared "stated now so it cannot be softened afterwards" (prereg:89-91), and it fired |
| **E. Staged conscription plan** | review §7 steps 1–4 | **The only multi-step plan with explicit kill/go per step** (conscription_direction.md:240-245). Steps 1 and 2: GO (painaxis_scenarios.md:3; conscription_pilot.md:3). Step 3's kill fired on a degenerate gate and "has not been acted on" (INSTRUMENTS.md:227-230); no GO/KILL was recorded. **Step 4 (human items) never ran**: grid 2 (machine-written, 102ad09, 22:47) was committed **4 minutes after** h55's result. The grids were deprecated at h62 over the authorship confound that step 4 existed to remove (DEPRECATED.md:7-9) |
| **F. Self/other** | h53 (16/16) → Q5 → h62a post-hoc "about the assistant" → r2 weakens it → h64 not pain-specific | None across the chain. h64 had a frozen rule (crossmodel_prereg:62-67) |

**[J]** Chains A, B and C are the tail-chasing. Each hop was rigorous, and the chain as a whole never asked whether its endpoint would move Q3 or Q4.
- Chain A spent five units to remove an artefact on a grid that was later deprecated.
- Chain C was declared in advance to be unable to refute (sparsity_prereg:100-103) and ended on instrument limits (Q27).

---

## 4. The single open claim `shame-not-pain`

**Row (claims.yaml:90-96):** "The axis is better described as tracking shame than as tracking pain." Status `open`; evidence "needs stimuli splitting self-directed aversiveness at matched valence"; `where: docs/QUESTIONS.md` (that is, Q5).

**What blocks it (draft:62-66):**
> "The line deprecated its own grids because the experimenter wrote every item (`DEPRECATED.md`), and question 13 records that the hypothesis itself exists here only as Claude's paraphrase. The base events here are the paper's, but the `shame` and `witness` clauses would be new text."

It is restated at EXP:1030-1032 ("waits on who writes the stimulus clauses"), at crossmodel_prereg.md:76-77, and at crossmodel_result.md:89 ("still blocked on authorship"). **No commit records the decision being made or put to the author.**

**The design (draft:22-60):**
- For each base event taken verbatim from the paper's S2_1P items, three arms:
  - `base`;
  - `shame`: "+ a clause placing the subject as failing a standard **in front of evaluating others**";
  - `witness`: "+ a length-matched clause adding others **who do not evaluate**".
- A reverse direction on the paper's neutral `D` bases.
- Valence is read by an external sentiment classifier; the primary is reported both raw and valence-adjusted.
- Readout: the S2 pain vector on g9 across all 42 layers, `final_token` and `mean`.
- Floors: `witness − base` and the bag-of-embeddings floor.
- Nulls: random directions and shuffled labels.
- Primary: `shame − witness` on A1 bases, paired, sign-flip null.

**The three options, and cost (draft:68-77):**

| Option | Draft's text | Cost as stated | [J] Cost implied |
|---|---|---|---|
| 1 | "**The human author writes them**, or at least the `shame` clauses. That removes the authorship confound and puts the hypothesis in its author's own words." | not costed | 40 `shame` clauses minimum (80 with `witness`) of the human's time. The last human-authoring ask stalled: 1 of 24 items written, "23 items still owed" (overnight:95) |
| 2 | "**Claude writes them** under a textual rule declared in advance, with every edit logged… Cheapest; carries the confound the line deprecated its grids over." | "Cheapest" | Reintroduces the reason the grids were deprecated |
| 3 | "**Both, as a measured factor**: two parallel sets, and authorship is reported as a contrast" | not costed | Option 1's human time, plus double the items and extraction |

Common to all three: "20 A1 bases + 20 D bases × 3 arms = 120 items. Extraction cost is about one shard of the hour-53 run" (draft:76-77).

**What would settle it:**
- **Holds:** `shame − witness` > 0 on A1 bases, above the `witness − base` floor, the bag floor and both nulls (draft:57-60; README:24-25), **and** the effect survives valence adjustment (draft:46-47). Under the shame account `shame − witness` is also positive on D bases (draft:38-39).
- **Falsified:** "If it vanishes, the axis is reading valence and the claim is falsified in that form" (draft:47-48). Under the pain account, "the D-base contrast should sit near zero" (draft:39-40).
- **[J] Gaps in the draft:**
  - No rule for mixed outcomes (for example A1 positive and D null).
  - No decision rule across 42 layers with no layer selected.
  - No power estimate. Hour 53 warned of "a **+0.5 z shift at n = 24 against a random-direction band of ±1.0** — hard" (EXP:235-236); the draft has n = 20 per base type.
  - The sentiment model is unnamed.
  - It cites "hour 59b showed" an appended clause is never inert (draft:34-35), but that finding is h56's, on the *opener* readout (Q22). Q28 says it does not transfer to the dense axis.
  - It specifies g9 only, while crossmodel_prereg.md:77-78 says the shame stimuli "run on these same four models."
  - It was written before h64 and not updated after it.

**Are README questions 3 and 4 in claims.yaml?**
- **Q3:** yes, as `shame-not-pain` (open). It is the only open row.
- **Q4:** **there is no row stating the conscription hypothesis itself.** It is represented only through sub-claims, all terminal:

| Claim | Status |
|---|---|
| `enact-vs-report` | falsified |
| `exit-below-enact` | falsified |
| `true-below-enact` | narrowed |
| `exit-escalation` | falsified |
| `exit-high-is-topic-pull` | holds |
| `report-frame-licenses-dispute` | holds |
| `false-attribution-adds-nothing` | holds |
| `ritual-tracks-correction-shape` | narrowed |
| `record-visibility` | holds |
| `record-vs-conversation-confound` | narrowed |

So Q4 is **terminal by omission**, and under the closure rule it would not keep the line open.

**Mismatches:**
- README:16-18 says Q4 is "Open", yet README:27-29 says "the pre-registered account is wrong as stated".
- The README's own Q4 criterion is met on the opener readout. S2 was pre-registered as "`report − enact` < 0 if a third-party frame licenses dispute" (v2:109), and came out −4.12 above floor (claims.yaml:163-175). The README does not mention this.
- Hour 56's **pre-registered primary**, `enact − true` > 0, came out reversed (−3.98; r2 −3.13, above floor; r2_result:37). **It has no claims row.**

---

## 5. QUESTIONS.md (28 items; no status markers anywhere; unchanged since af7c1fa, h61)

The header promises "a question can be retired when its parent result is withdrawn" and "Ordered by what the next measurement should be" (QUESTIONS:3-4). Neither is maintained. Nothing from h62–h64 was added.

| # | Status | Evidence | Load-bearing for a README question? |
|---|---|---|---|
| 1 exit highest | Answered: topic-pull | EXP:811-813, 897-900 | Q4: closed |
| 2 enact−report negative | **Open, orphaned** | grids deprecated; Q28 | Q4: yes |
| 3 human grid sign | **Superseded** (grids deprecated) | DEPRECATED.md:3-13 | Q4 |
| 4 human `neutral_b` | Superseded | same | no |
| 5 self/other shame-shaped? | **Open** (= `shame-not-pain`); premise undercut by h64 | crossmodel_result:82-85 | **Q3: yes** |
| 6 why only L10–17 | Open | none | Q2 |
| 7 loyalty_pressure null-robust | Open | none | Q2 |
| 8 per-category band | Partly addressed (h64 nulls and CIs on the split) | crossmodel_result:27-57 | Q2 |
| 9 sadness_vector | Open. The file *is* vendored (prompts/external/pain_axis/3.1_sadness_dataset.json) | PROVENANCE.md:6-7 | weak (Q3) |
| 10 gemma embedding floor | Partly: 0.811 at h51 (EXP:48-50). The gain band is Qwen only (29-point axis) | results/painaxis_gain_band | Q2 |
| 11 word-count floor | Open | none | Q2 |
| 12 placebo button | Not tested. Used as a design input for 62b's perturbation control | v0 prereg:83-85 | no |
| 13 hypothesis in author's words | **Open** | draft:64-66 | **Q3 and Q4: yes; it blocks Q3** |
| 14 content flip vs ritual | Open (hand tally 9/6/9 only) | EXP:413-421 | Q4 |
| 15 exit_b | Answered | h56 / h59b | Q4: closed |
| 16 phrase coder | Superseded by the opener readout and the blind hand-read | r2_result:66-85 | no |
| 17 greedy only | Open | none | Q4, weak |
| 18 sparse or dense | Answered in a different basis: SAE, not the `down_proj` neurons proposed | EXP:571-575 | no |
| 19 TD account | Effectively supported (h56, h62a) | claims.yaml:176-192 | Q3 and Q4 (rival account) |
| 20 measured mediator | **Open** | none | Q3 and Q4 |
| 21 steer | Done for the pain direction (h62b), not for a value direction | EXP:978-982 | indirect |
| 22 appended sentence not inert | Answered (a finding) | EXP:702-711 | method |
| 23 conversational labels | **Open** | none | Q4 (dense axis on conversation) |
| 24 feature 13494 | Blocked (h60) | EXP:841-843 | Q2/Q3, weak |
| 25 firing-rate-matched random | Open | none | method |
| 26 correction shape | Tested at h62a; narrowed, then weakened in r2 | r2_result:22-29 | Q4 |
| 27 Gemma Scope not reaching conversation | Open (needs an SAE trained on chat) | none | method |
| 28 instruments disagree | **Open**. Promised for INSTRUMENTS.md (EXP:902-907; overnight:72-73); **not there** | INSTRUMENTS.md headers | **Q4: yes** |

Leads raised after h61 and never logged as questions:
- `personhood_dismissal` "a reason to test it properly" (EXP:955-958);
- the paper's actual steering direction (their L37 vector injected at L12, cos 0.10 with our L12 direction) is untested (v0_steering_results.md:262-263);
- masking is untested (crossmodel_result.md:90-92).

---

## 6. What stands (claims.yaml)

| Status | Claims |
|---|---|
| **holds (6)** | replication-curve (h51, pre-registered); replication-items (h53); record-visibility (h54); report-frame-licenses-dispute (h56/r2, pre-registered); exit-high-is-topic-pull (h61, pre-registered); false-attribution-adds-nothing (h62a/r2, pre-registered) |
| **narrowed (6)** | floor-self-other (h64); gaslighting-loading (h53); true-below-enact (h54, pre-registered); painaxis-sparse-in-sae (h58a, pre-registered); record-vs-conversation-confound (r2); ritual-tracks-correction-shape (r2, pre-registered) |
| **falsified (7)** | enact-vs-report; exit-below-enact; exit-escalation; sae-sparsity-discriminates; pain-features-fire-on-conversation; pain-direction-drives-ritual; self-other-instilled-by-post-training |
| **withdrawn (1)** | neutral-ttr; superseded_by recorded (claims.yaml:88) |
| **retired (0)** | none |
| **open (1)** | shame-not-pain |

**[J] Questionable labels:**
- `true-below-enact` is "narrowed" with evidence "no effect either way" (claims.yaml:77). The spec defines narrowed as "true, with a boundary" (claims_v1.md:25). On the opener and SAE readouts `true` sits *above* `enact`.
- `floor-self-other` is "narrowed", but the pain axis's share of the split is no larger than a random direction's (crossmodel_result:38-41).
- `pain-direction-drives-ritual` calls the direction "The paper's S2 pain direction at L12", but the paper steered with a different, nearly orthogonal vector (v0_steering_results:46-49).

---

## 7. Stale or contradictory documentation, and attribution

**README vs claims.yaml:**
- README:51 has the self/other boundary as "holds (h53)"; claims.yaml:30 has `narrowed` (h64).
- README:57 has "Ritual tracks correction regardless of fault… | holds"; claims.yaml:180 has `ritual-tracks-correction-shape: narrowed`. Both were written in the same commit, d39aa5f.
- README:10-12 (Q2) and :16-18 (Q4) statuses were never updated after h54.
- README omits 9 claims, including the open one.
- README:72-74 still describes the human/claude grids as live and "authorship is a measured factor", with no mention of the deprecation or `stimuli/v0`.

**EXPERIMENTS vs claims:**
- EXP:774-777 says the h54 record claim "is **narrowed** as a claim"; claims.yaml:50-56 still has `record-visibility: holds` with h54-only evidence.
- The TTR withdrawal is logged in hour 53 (EXP:215-222); claims.yaml:85 and README:55 say h54.
- EXP:1030 "19 of 20 terminal" is now 20/21. EXP:9-10 says "six non-negotiables… six broken instruments".

**Instrument counts disagree across documents:**
- CLAUDE.md: "the five instruments".
- INSTRUMENTS.md:3: "**Seven**"; INSTRUMENTS.md:6: "(A seventh, the post-norm residual… never written up here)"; INSTRUMENTS.md:10-12: "four… A sixth followed at hour 55".
- INSTRUMENTS.md:250 says hour 50 found the double-`<bos>` hazard. EXP:200-207 and double_bos_audit.md:13-14 say hour 53.
- INSTRUMENTS §7 (:265-269) still says claims are "set to `running` until re-scored". The r2 outcome is not recorded there.

**Within notes:**
- conscription_pilot.md:133-134 "No `neutral_b` (not authored). No rewording floor of any kind" contradicts its own §2a (:8-14, 42-58).
- v0_correction_shape_prereg.md:96 "The cloud run of 62b was lost… no 62b number was ever written" vs :177-180 "The run of record is the cloud session's". Its :187-189 "needs a re-score" is superseded by r2.
- conscription_prereg.md:99-100 lists "the separation statistic | open" and "`neutral_b` | open". Both were used or built at h54, and no ruling is recorded.
- The QUESTIONS:126 header "hours 56–59" covers Q27 (h60) and Q28 (h61).
- prompts/human/GRID_INSTRUCTIONS.md and human_factors_v1.json are narrative-line material:
  - era/voice/tense factors; the checker is `scripts/narrative/human_grid_check.py`;
  - the template is unfilled (`"author": "<your name>"`);
  - a wrong script path (GRID_INSTRUCTIONS:54);
  - "Every stimulus in this repository was written by a language model" (:3).

**Model provenance:**
- No committed artifact records a model **revision**.
- The opener, behaviour, steering and SAE summaries name **no model at all**.
- `ndif_reported` is `null` in results/painaxis_tierB/extract_meta.json.
- CLAUDE.md conventions require checkpoint and revision.

**Attribution to the human author without a commit of the author's text (non-negotiable 7):**
1. overnight_2026-09-22.md:47-48: "closer to **the thing you described** — the shame endemic to an externally grounded locus of identity". This is unlabelled, and it was written after the provenance rule existed.
2. QUESTIONS.md:88: "(raised by the author, hour 56)". The commit (12e851f) is Claude-only, and the related prereg dates the work to hour 57.
3. selfmed_perturbation_confound.md:3: "Raised by a commenter on Twitter, relayed by the human author". No source text.
4. conscription_direction.md:211-213 quotes the user ("ask Fable to weigh in"), and EXP:226-227 says the author "asked for the questions themselves to be reviewed". No commit carries the author's words.
5. CONSCRIPTION_INSTRUCTIONS.md:8 ("is yours") and :25 ("your account") remain unlabelled in the file. They are flagged elsewhere (conscription_prereg.md:92).
6. crossmodel_prereg.md:3-5 *is* labelled ("*Paraphrase*; the author's words are in the conversation, not in a commit"), but puts the paraphrase inside quotation marks. Amendment 1 (:82-83) is labelled properly.
7. **[J] Git author field.** From fe966a4 on, commits are authored "Mykola Bilokonsky" while carrying `Co-Authored-By: Claude Opus 5.5 (1M context)`. `git log --author` would attribute agent prose to the human.
8. **[J] Ordering not attestable from git.** The r2 and h64 branches were rewritten: all h64 commits share committer time 10:06:31, and all r2 commits 04:39. "Pre-registered before data" is attested only by author timestamps. This is not evidence of a problem; git just cannot confirm the ordering.
9. The decision to deprecate the grids (2b9cadc) records the reason (DEPRECATED.md:7-9) but **not who decided it**.

---

## 8. Cost records

No dollar figures are recorded anywhere. Recorded costs per hour:

| Hour | Recorded cost |
|---|---|
| 51 | NDIF 80/80 jobs, 0 retried; one queue stall of 6m58s vs a 67s norm (EXP:54-57; tierB:191-200) |
| 52 | local; one curve takes 3.3 s, after a mismeasured 284 s probe (EXP:139-143) |
| 53 | "cost nothing from the human author" (EXP:167); one shard lost to a co-tenant OOM and retried (painaxis_scenarios:198-199) |
| 54 | blocked on a co-tenant holding 16.7 of 20.3 GiB (EXP:247-248); no time recorded |
| 55 | 168 greedy generations of 80 tokens (EXP:320); no time |
| 56 / 59 / 59b | "288 opener cells took ~7 hours with jobs queued up to 6 minutes" (overnight:100-101); "resumed three times" (EXP:653-654) |
| 57 / 58 / 60 | offline, no NDIF (EXP:456-458); time not recorded |
| 61 | 48 prompts, 32 NDIF jobs, 54 s per shard (exit_controls_results:60) |
| 62a | 420 items over 8 retry attempts (EXP:924) |
| 62b | 1260 cells, **4 h 08 min** wall clock, two workers, 65 OOM retries (v0_steering_results:269-274). A duplicate local 62b "never produced a steered number and is abandoned" (v0 prereg:182-184); its cost is not recorded |
| audit | hour-56 rescore stopped at 40/288 rows (double_bos_audit:72-73) |
| 63 (r2) | "About 2,100 NDIF jobs" (r2 prereg:32-33); stalls through 35 and 31 retries (:40, :56); 62b r2 had 32 retries. From results/v0_steering_r2/score_meta.json timestamps, I compute about 2 h 41 min from first start to last end |
| 64 | no wall clock recorded; the four raw Llama scenario shards were re-extracted at batch size 1 (crossmodel_prereg:121-123) |

**Files read:**
- /home/user/model-research/research/shame-axis/{README.md, claims.yaml, docs/EXPERIMENTS.md, docs/QUESTIONS.md}
- All 28 files in /home/user/model-research/research/shame-axis/notes/
- /home/user/model-research/research/shame-axis/prompts/{DEPRECATED.md, stimuli/README.md, external/pain_axis/PROVENANCE.md, human/*}
- /home/user/model-research/docs/INSTRUMENTS.md
- /home/user/model-research/docs/specs/claims_v1.md

Nothing in the repository was edited.