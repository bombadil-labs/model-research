> **Provenance.** The adversarial review of `PROGRAM_v2.md` v0.1 (commit `dd241b9`), written read-only by an agent in the 2026-10-15 cloud session under `docs/DELEGATION.md` stage 2's hostile brief, and committed verbatim. v0.2 of the program answers it; `PROGRAM_v2.md` §10 lists what was accepted, modified and rejected.

ADVERSARIAL REVIEW: docs/PROGRAM_v2.md

What I reviewed: commit dd241b9 on branch `program-v2`. It is byte-identical to the untracked file (md5 1f247317…). I read it against the audits, `2a992c3` (main), `966003d` (branch `narrative-permutation-seed-audit`, which is open PR #12), `origin/shame-pain-stimuli` (PR #9) and the GitHub REST API. I edited nothing.

Environment warning: while I was reading, another agent changed the shared checkout at /home/user/model-research. HEAD went 65826a8 → 966003d → `program-v2`/dd241b9. The finding about concurrent agents (19b) rests on this.

## RANKED FINDINGS

### 1. BLOCKING: §6 and the escalation paths repeat the failure the document diagnoses
- **Where:** §6 has 12 DECIDE rows and none has a default or a date. R3 says "A fourth hop needs an author decision recorded with its reason". NC1 says "Escalate: fund one causal node … or close here". C2 says "escalate". R4 says "A redirect cannot lapse through silence".
- **What is wrong:** §0's own evidence is a gate that "waits on" the author. That wait cost 683k tokens and then the program was dropped (EXPERIMENTS.md:2095). The repo has been idle 22 days, and PR #9 has been open since 2026-09-23T18:20:48Z. v2 sends 12 decisions plus every escalation down the same channel with no default. R4 stops silence only for redirects; DECIDEs can still lapse.
- **Fix (replacement R4):** "R4. Nothing lapses through silence. Every DECIDE, escalation and fourth-hop request is raised with a default and a date. If no decision exists by that date in the author's own words (a commit or PR/issue text he wrote), the default executes and is recorded as 'defaulted, no decision'. A default is always the cheapest terminal option (retire, close, do not fund). It is never 'fund' or 'continue'." Also add a "default / date" column to §6.

### 2. BLOCKING: NC1's outcome table is inverted, cannot reach "holds", and breaks NN3 and NN4
- **The null is degenerate.** NC1 (§4) defines the null as "norm-matched random-subspace projections". A random direction has cosine of about 0.02 with the route direction (claims.yaml `generic-choice-slot-replication`: "random-direction q95 +0.022"). The property direction has about 0.58. So projecting out a random k=1 subspace removes almost nothing, and the random band sits tightly around the unprojected transfer.
- **Read literally, the holds branch means the opposite.** "Residual inside the random-projection band → holds" means the slot direction did no more than a random one. That is evidence against sufficiency.
- **"Holds" is unreachable.** A residual near 0 (slot fully sufficient) is outside the band and below half, so it lands in "anything in between → narrowed".
- Two readers will classify the same number in opposite ways, depending on whether "band" means the random-projection distribution or chance.
- "Norm-matched" means nothing for a projection.
- **"≥ half" has no basis.** Under it, a reliable 40% route-specific residual (the exact thing cluster C asks about) gets "narrowed, chain closes with no child node".
- There is no branch for the unprojected arm failing to reproduce.
- **NN4:** "+0.171" is block 24, picked because it carried the pilot's signal. The registered statistic was the block-16/24 mean of +0.0854 (goal_route_activation_pilot_result.md:16-17, :31, :44-48).
- **NN3:** the "domain bootstrap for the floor" is a confidence interval, not a floor. The holds branch is a null with no power estimate.
- **Domain selection:** the 8 domains were selected on earlier positives (firsthop_doubleflip_result.md:23).
- **Cost:** "about 264 NDIF jobs" re-extracts only the route states. The property direction needs the property states too (about 520 jobs; narrative_audit.md:396).
- **Fix (replacement outcomes):** Statistic: ρ = T_proj/T_0, using the registered block-16/24 mean, with all six blocks reported.
  - Gate 0: T_0 reproduces +0.0854 within recorded repeat drift; otherwise stop and default to "close".
  - Nulls: the exact orientation null, plus 64 random directions whose cosine with the route direction matches the property direction's (±0.05).
  - δ: the smallest ρ detectable at 80% power, committed before data.
  - **Holds** if T_proj is inside the orientation null AND below the q05 of the cosine-matched residuals.
  - **Falsified** if ρ's lower CI bound > δ AND T_proj > the orientation-null q95.
  - **Underpowered → retired** if ρ's CI spans both 0 and δ.
  - Otherwise **narrowed**, with ρ and its CI recorded.

### 3. BLOCKING: R1–R5 are labels an agent declares for itself, in prose; §8 tests only the labels
- **Self-declaration:**
  - R1 lets the agent create nodes ("add the node first") with no approval.
  - R3 counts a hop only if "motivated by the previous node's caveat", and the agent decides the motivation. v2 shows how loose that is: it calls C2 "Not part of a chain", and calls S1-b "hop 2 of the chain that h65 started". Counted from h53 → h64 → h65 (shame audit chain F, shame_axis_audit.md:108), S1-b would be hop 4.
  - R2 allows "continue (naming the child node)". A caveat response written in advance as a "continue" branch therefore escapes R3.
- **R2's check can't be verified from git.** "Committed before the first activation is read": rewritten branches share committer times (shame_axis_audit.md:290), and one narrative prereg reached its result in 2.5 minutes (narrative_audit.md:170).
- R4 has no "Check:" line at all, so "five, each checkable" is false.
- §8's falsification test ("names a node") is cosmetic.
- **Scenario where every step complies:**
  1. NC1 runs with the author's go and returns ρ = 0.38 [0.12, 0.61], so it is narrowed and its chain closes.
  2. An agent adds NC3, "Is the residual a second slot dimension (k=2)?". It declares NC3 motivated by NC1's *result*, so R3 starts a new chain at hop 1. The outcome table and 150k budget are committed before data; one branch is "else continue to NC4 (causal patch of the residual)".
  3. NC4 is a pre-named continuation, so it is not caveat-motivated.
  4. NC4 fails its 2× plan-order gate, as #20 and #22 did. R2 allows "narrow", so the agent files a new `nc4-margin-shift` row as holds (a registered component) and re-ids the parent (R5 ✓). It adds cost lines with tokens estimated, because tokens aren't metered (R5 ✓). No redirect fired (R4 ✓). Every unit named a node, so §8 passes.
  5. Net: about 450k tokens, more open rows, the line further from closed, and no rule fires.
- **Fix:**
  - Keep nodes as data: `research/<line>/nodes.yaml` with id, claim_ids, parent, motivated_by (note:line), budget_ndif_jobs, budget_wall, spent, outcome_table path, status. `check_claims.py` validates it, and computes hop as depth from parent links rather than taking it as declared.
  - A node not in the accepted document needs an author-authored commit.
  - Rewrite §8: v2 has failed if, after 5 units, (i) open claims across lines have not decreased, or (ii) any DECIDE passed its date without a decision or default, or (iii) any node exceeded 1.5× its NDIF/wall budget without stopping, or (iv) any row was opened by a node descended from a closed chain.

### 4. SHOULD-FIX (high): R3's hop cap would keep untested positives, and v2 leaves alone the rule that generates them
- **Where:** R3.
- **The decisive negatives came late in their chains.** In narrative chain A, the decisive negative ("clause order, not consequence, drives the readout", #5; narrative_audit.md:140) is hop 4 counting from #2 (Propp #1 → #2 → #3 → #4 → #5). In shame chain A, h61's resolution is hop 4. A cap at 3 leaves the earlier "holds" and "narrowed" rows standing with their confounds untested.
- **The generator is untouched.** v2 never addresses "failed gate → new holds row": `late-reveal-paired-margin-shifts` and `story-period-margin-shift` are holds rows split off failed registered decisions (narrative_audit.md:240).
- **Fix:**
  - Add to R3: "A chain stopped by the cap downgrades every holds it produced to narrowed, naming the untested confound. A hop whose only purpose is to test a named confound of a standing holds counts toward budget, not toward the cap."
  - Add to R2: "A component of a failed registered decision is recorded in the parent id's evidence, never as a new holds row, unless it was a registered secondary."

### 5. SHOULD-FIX (high): S1-a recommends the weakest option, and its reasoning repeats patterns §0 condemns
- **The retirement reason is a conjecture filed as a finding (§0's own pattern).** S1-a says "the claim's object, the axis, cannot carry the contrast (h62b, h64, h65)". But h65's positive control passes at later layers in 3 of 4 models (shame_vs_pain_result.md:43-51), and that note's lesson 1 fixes the layer (:98-99). h62b is about causing the ritual; h64 is about self/other specificity. None of them shows the axis cannot carry shame-vs-pain.
- **It changes a question's meaning under a fixed number.** S1-a says "re-pose question 3 behaviourally"; S2 says "'shame-shaped' earns a behavioural meaning". README:22-25 defines Q3's answer as a contrast "on the same axis". Changing that while keeping "question 3" is §0's "meaning changed under a fixed id", one level up. It also requires a README edit.
- **§0 overreads the "redirect".**
  - h62b's sentence (v0_correction_shape_prereg.md:89-91) is scoped to "this behaviour", the opener ritual named at :68-69.
  - After h62b, h64's result itself named the shame-vs-pain stimuli as "the test that could" (crossmodel_result.md:88-89).
  - §0 states one reading as fact: "A redirect that fired and was not followed".
- **S2 is an extension, not closure.** It is a new Claude-built hypothesis (shame_vs_pain_design_DRAFT.md:30). It uses a readout whose sign disagrees with the dense axis (QUESTIONS Q28), and it costs 300k plus NDIF.
- **The case for S1-c.** It is the only option consistent with the document's own diagnosis. h65 also showed the answer depends on who wrote the stimuli (:80-81), and a rewording floor as large as the effect (:82-83), so S1-b will likely come back unreadable.
- **Fix:**
  - Recommend S1-c. Offer S1-b as the alternative, with its table repaired (#6).
  - Move S2 to a new-line charter that requires one hypothesis sentence committed by the author.
  - Retitle §0's row "A conditional reframing that fired and was read narrowly", and quote both scopes.

### 6. SHOULD-FIX: The S1-b and S2 outcome tables are incomplete, contradict each other, and lack nulls and floors
- **The same outcome gets opposite statuses.** S1-b maps "two authors disagree" to **falsified**; S2 maps "authors disagree in sign" to **narrowed**. Disagreement between authors is stimulus dependence ("the answer depends on how the stimuli were written", result:80-81). It means unreadable, not falsified.
- **S1-b gaps:**
  - No branch for the control passing only in some models or layers, which is h65's actual outcome.
  - "Null" has no power estimate. h53 already warned that +0.5 z at n=24 against a ±1.0 band is "hard" (shame_axis_audit.md:153).
  - Its criteria are fewer than h65's five effect criteria (result:68).
- **S2 gaps:**
  - No positive control, though only a positive control bounds false negatives (INSTRUMENTS §6).
  - No shuffled-condition null and no noise floor.
  - No branches for: reverse sign in both author sets; one author positive and the other null; rewording floor ≥ contrast; effect gone after valence adjustment.
- **The authors are not named.** "Two-author" means Claude and a GPT agent ("Claude and Sol", PR #9 body; rows "claude"/"gpt", result:57-66). DEPRECATED.md:7-9's confound is reduced, not removed. Say so.

### 7. SHOULD-FIX: N0's "finish, don't extend" funds three new-science nodes and offers no option that adds no new science
- **The cost is near v1's whole budget.** "1.2–1.5M tokens" is 70–90% of v1's whole-program 1.7M. v1's phases overran 2.6× and 4.6× (method_audit.md:58, :64), and v2's budgets are not corrected for that.
- **Its NB1 recommendation is Claude's disclosed favourite**, for a question the README already marks "Answered: mostly no" (narrative README:8-9).
- **Unlimited escape hatch:** "Anything that continues C … becomes a new line with a charter".
- **No zero-science option:** shame-axis gets S1-c, narrative gets nothing equivalent.
- **Fix:**
  - Add option D: "Close now: C2, NC2, NA2, retire NA1/NB1/NB2 with reasons, writeup (~300k)". Recommend D, or D plus NC1 only.
  - Add: "No new line is chartered while an existing line is open. A charter's question is committed in the author's own words."

### 8. SHOULD-FIX (blocking if funded): NA1 cites a spec that doesn't contain the test it describes, and drops the arm that decides its outcomes
- **No layer sweep in the spec.** NA1 claims a "generation-level layer sweep … following scale_vs_tuning_v1.md piece 2". Piece 2 has no sweep: it fixes `--layer 26 --read 40` (scale_vs_tuning_v1.md:344-346).
- **The deciding arm is dropped.** Piece 2 includes a theme arm (:347) and an 8B arm (:350), and grades outcomes A–E (:283-316). PROGRAM.md:114-115 says the theme arm is "the one that actually tests claim 11". NA1 keeps only era, yet lists outcomes A ("competence is factor-specific") and B, which can only be told apart by theme. C–E are missing.
- **No thresholds:** "The cap tracks depth fraction" has no threshold and no negative branch.
- **No NDIF job count**, which R2 requires.
- **Stale constraints:** the spec mandates legacy scripts and a stale HF_HOME and proxy (:364-371).
- **Unbudgeted extraction:** the h37 70B stacks are not cached (WRITEUP.md:294-295).
- **Fix:** "NA1 requires a new spec (planner plus adversarial review). It adds the generation sweep to piece 2 steps 1–2 (era and theme) and grades A–E plus depth-fraction holds/falsified with numeric thresholds. Budget in jobs = layers × models × arms × 72." Or retire NA1.

### 9. SHOULD-FIX: NB1 and NB2 lack decision rules, and NB2's gating logic is backwards
- "Anything in between → narrowed" is undefined. If the slot baseline is at or above the permutation null, that region is empty.
- No decision statistic over the curve ("Report it; select nothing", but beats it where?).
- The falsified branch is a null with no floor (NN3).
- **Overreach:** a negative from one model and one method becomes "B's answer is 'not recoverable without assuming correspondence'".
- **Dependency and design gaps:** POT (Python Optimal Transport) is not installed (narrative_audit.md:271). The grid is unspecified; if slot position doesn't vary across domains, the slot baseline matches by construction.
- **NB2 is backwards.** NB1 is the harder, assumption-free test. Its failure says nothing about whether the easier, assumed-correspondence readout recovers shape at higher n.
- **Fix:** retire both under "finish". If kept: a fixed-layer-mean statistic; holds iff (recovery − slot baseline) has a CI excluding 0 and exceeds the permutation q95; falsified only if the CI's upper bound < a pre-computed δ; else "underpowered, retired". Fund NB2 only if NB1 is falsified or underpowered.

### 10. SHOULD-FIX: C2's outcome table cannot be applied as written
- **Undefined bands.** "Inside its band of 0.8364" is not defined; treatment is n=55/72 (EXPERIMENTS.md:1985-1986), a binomial SE of about 0.05. The "random band" is not defined either.
- **Missing branch:** the random or no-patch arm moves off its null. The declared null is the no-patch base rate, so if the fix moves the base rate, the null moves with it.
- **Ignores differential loss.** 18% of generations were lost unequally: 0% base, 24% shift, 22% random, deterministically per item (WRITEUP.md:70-72).
- **"fp32 softcap" is irrelevant here.** That fix lives in `asserted_remote_patched_logprob` (remote.py:397-460). h29 uses `asserted_remote_generate` (:519).
- **Escalation is incomplete:** WRITEUP claims 9 and 10 rest on the same 0.84 (:75-81).
- **Fix:**
  - Band = Wilson 95% interval at the rerun's n.
  - Gate: per-arm loss reported, and a loss difference over 10 points means "unreadable, escalate".
  - Add a branch for arms off their nulls.
  - Escalation names claims 8–10.

### 11. SHOULD-FIX: C1 reports as done a result that is unmerged and partly untested
- **Not on its own branch.** On `program-v2`, the linked note does not exist, and claims.yaml:161-167 still has `permutation-arm-below-null` open. The result lives in open PR #12, created 07:42:39Z, one minute before dd241b9. §0 complains PR #9 is unmerged while C1 reports an unmerged PR as "Done".
- **"Done" ignores the note's "What was not tested" (note:176-182):** 6 of 25 rows were not re-extracted, and the random arm shares directions across rows and was not audited. C1a covers only the permutation arm.
- **"Spent ≈ 0.3M tokens" is unsourced.** The note says "agent tokens were not metered separately in this session" (:200).
- **Missing from §6:** the in-place retraction in EXPERIMENTS.md, which needs the author (note:202-212).
- **C1a(b) "hash"** must be `hashlib`, not Python's `hash()`, which is randomised per process (EXPERIMENTS.md:2051-2053).

### 12. SHOULD-FIX: Attribution (NN7) problems in the document itself
- **(a) Header (:3-7).** It calls the uncommitted request "the author's words, quoted". NN7 (CLAUDE.md:28-31) says such text "is a paraphrase and is labelled as such". The shame audit flagged the same pattern, quotation marks around a paraphrase (shame_axis_audit.md:288). Fix: "Paraphrase (NN7): the author asked for …; his words are in the conversation, not a commit."
- **(b) S0 (:307-309).** It says the authorship question "was settled", but the only source is a labelled paraphrase. Fix: "PR #9 reports, as a labelled paraphrase, that…". Ask the author to confirm in the merge commit.
- **(c) S2 (:356).** "Only as Claude's paraphrase (QUESTIONS 13)" cites the wrong item: Q13 (QUESTIONS.md:61-64) is about the conscription hypothesis. S2's hypothesis is Claude's own operationalisation (draft:30), and the shame wording has no provenance entry anywhere (shame_axis_audit.md:57).
- **(d) R3 and §8.** Their "author decision recorded…/in a commit" doesn't require the author's text, so agent paraphrases satisfy it. Precedents: the 0.3 waiver (method_audit.md:45-46), and "per Mykola's explicit instruction" (action_interaction_prereg.md:30-31).
- **(e) §7 lists 2 of at least 9 unlabelled attributions.** It omits:
  - reveal_order_prereg.md:10-11
  - action_interaction_prereg.md:30-31
  - selfmed_perturbation_confound.md:3
  - conscription_direction.md:211-213
  - CONSCRIPTION_INSTRUCTIONS.md:8, :25
  - crossmodel_result.md:86 ("The question the human author raised")
  - EXPERIMENTS.md:1687 (the WAIVED line)
  - the git author field: agent prose committed as "Mykola Bilokonsky", e.g. 13793be and 5c7ea84. Add a check for it.

### 13. SHOULD-FIX: R2 and R5 cost rules can't be enforced, and the budgets aren't credible
- Tokens are not metered (note:200).
- R2 demands NDIF job budgets, but NA1, S1-b ("hour-64/65 scale"), S2 and C2 ("about h29's job count") give no number.
- So "twice its budget stops" can never fire.
- No overrun correction is applied (#7).
- **Fix:** budget in NDIF jobs and wall time, which are metered. Hard stop at 1.5×.

### 14. SHOULD-FIX: "What these five replace" is false, and it drops protections that are still live
- It replaces nothing live. The phase gates were already dead and the screen was never built. CLAUDE.md, DELEGATION and the claims rules all remain, so this is a pure addition.
- **It silently supersedes v1's standing rules (PROGRAM.md:138-150):** one agent at a time; a retraction pauses the program; state what was not tested; planner/review.
- **It drops DELEGATION's report screen with nothing in its place.** That screen checks for a missing arm, an arm near treatment, and a report with no failures. It targets the failure class this repo has actually suffered: 7–8 broken instruments and about 20 later issues (method_audit.md:137-161).
- Merges are too fast to have been screened: 6 of 10 merged PRs went in within 86 s (API: #1 86 s, #2 71 s, #3 28 s, #4 23 s, #5 18 s, #11 86 s). The audit says 7 but lists 6.
- **"Screening now checks it" has nothing behind it.** No screen exists, and check_claims can't detect meaning changes (method_audit.md:248).
- **Fix:** list the surviving rules explicitly. Add a CI check that diffs each id's `claim:` text against main and fails a change of meaning without a new id.

### 15. SHOULD-FIX: Two §7 hygiene items are really science or decisions, and one loses information
- **`conscription-hypothesis` "is falsified" (:419-421).** This is a verdict on an author-attributed hypothesis, filed as hygiene. The README's own Q4 criterion passes on the opener readout (report−enact −4.12, pre-registered; shame_axis_audit.md:180), and Q28 records that the instruments disagree. Make it a DECIDE; "narrowed" is the candidate.
- **Re-id rule: "Each old id is withdrawn".** For `fixed-plan-circumstance-transfer`, that erases a falsified pre-registration (13793be), against claims_v1.md:69. Keep the original wording and falsified status on the old id; put "narrowed" on the new id. Amend claims_v1.md:62-63 to match.
- **Ungated line-doc edits.** "Update the README's question statuses" and "resolve relation-lens vs writeup" edit README/WRITEUP, and C5 itself forbids status changes. Gate them as DECIDE.
- **"Record model revisions in artifacts".** Use sidecar provenance files, not post-hoc edits to committed results.

### 16. SHOULD-FIX: The closure machinery doesn't add up
- **`retired` is misused.** The spec defines it as "never measured" (claims_v1.md:28). It is proposed here for measured claims: `propp-full-story-context` and `shame-not-pain` after h65. Either add an "inconclusive" terminal status or use honest statuses.
- **C4's "NOT-DERIVED" has no claims status.**
- **New rows with no node:** the seven new writeup rows have no status and no node, and the narrative end state (:283-285) omits them. The QUESTIONS triage will add open rows that no node covers. Neither line can close as specified.
- **Closure is redefined:** §1 item 1 goes beyond CLAUDE.md:72 ("the only definition of done") without proposing that edit.
- **Unspecified data format:** C3's "no open question items" has no machine-readable source.

### 17. SHOULD-FIX: C3's success criterion can pass with most tests skipped
- Skips are everywhere: `importorskip`/`skipif` on torch/transformers (tests/conftest.py:31-32), on a Qwen tokenizer cache (tests/shame_axis/test_core_conscription.py:22), on NDIF evidence (tests/lsx/test_core_remote.py:115), and on many script modules.
- **Fix:** success means ≥N tests collected and passed, skips listed by name with `-rs`, and any new skip fails the job.

### 18. SHOULD-FIX: NC2 and NA2 give the wrong reasons
- **"Three control batteries failed" is wrong.** V3 failed at 28/32. V4 was abandoned at 9/32 after a review found a shortcut. V5 had 3 failures in 15 (goal_reversal_calibration_result.md:28-32). And a pass at 22–24/24 could beat the 21/24 shortcut; it is underpowered, not impossible (:14-17).
- **"Story-token states carry no shared direction" overreaches.** The note says it is "a location-specific result, not evidence … in other tokens" (prequestion_route_state_result.md:89-91), and `story-period-margin-shift` holds.
- **The Propp reopen trigger ignores the result's own next test.** That test is a held-wording, within-story manipulation (propp_spike_result.md:76-79), and it needs no second corpus.
- **"In five designs"** has no citation.
- **NA2's reason is a non sequitur.** h48 says voice is "a readout at its ceiling, not a readout failing" (EXPERIMENTS.md:2174-2176), and interference can be read on the mood lens's own floor. Retire it on scope instead: it serves neither product, has no spec, and stimulus writing costs 100–300k.
- **NA3 neglects alternatives.** It ignores human-written sources the repo already uses (ProppLearner tales). It also ignores the author's revealed preference: 0/18 on the template, 1/24 on the conscription grid, and clause writing delegated in PR #9.

### 19. SHOULD-FIX: Omissions
- **(a) A credential risk.** v1 0.3's waiver reopens on "a shared environment". The machine is now shared by two agents and keys load from ~/.bashrc (method_audit.md:42-50).
- **(b) Concurrent agents.** The checkout changed branches under me during this review. v1's one-agent rule was dropped and v2 adds no worktree rule.
- **(c) The core depends on the narrative line's paths:** checks.py:680, ledger.py:43, reproduce.py:42-44 (method_audit.md:205-209).
- **(d) Unfunded products.** Product 2 has no node, and reproduce.py has no `__main__`. Writeups have no node or budget.
- **(e) C4 drops part of the spec's recommendation.** The spec says "(b), then (a) for `crosstalk` alone" (phase2_v1.md:95). v2 drops the crosstalk build, which is the instrument behind "factors are separate directions".
- **(f) Chain C is left open.** "A new domain and model are needed" (firsthop_doubleflip_result.md:23) has no node and no closure record.
- **(g) Narrative README conflicts aren't fixed.** Q2 says "Partly" and Q3 says "Yes for some", against `relation-lens` falsified and `factors-compose` withdrawn. §7 fixes only the shame-axis README.

### 20. NITS (factual)
- **§0 :35 "22 of the 25 rows".** All 25 ran at seed 0; 21 share one draw set and the 4 factors_v2 rows share another (966003d message; note:6-9).
- **"About 3.5 SD".** That is the composed arm only; era is 2.3 and voice/theme 2.9 (note:114-116).
- **"About 5 aim at the question".** The audit's headline says "about 4" (narrative_audit.md:22); its tally double-counts row 11 and omits row 2.
- **"They ran on grids that hour 62 then deprecated".** h58a and its addendum ran on the paper's 500-item pool (sparsity_reference_results.md:25-29).
- **"No costs are recorded after h50".** NDIF job counts and wall times are recorded; tokens are what's missing (shame_axis_audit.md:297-313).
- **§4 "Answer slot (constructed Gemma-9B stories)".** The +1.126 causal test was on 64 property prompts (answer_slot_patch_result.md:3-10).
- **NA3 "v1 … call it the binding constraint".** v1 says "cheapest single change" (PROGRAM.md:99-100).
- **NC1 "six hops".** Six experiments make five hops.
- **C5 "says both seven and eight".** INSTRUMENTS.md:3-6 says "Seven" plus "A seventh"; it never says eight.
- **§4 "era clears … every grid and model family".** Era fails the shallow-layer floor on GPT-J (EXPERIMENTS.md:2179-2181).

## SPOT-CHECKS (26)

**Correct:**
- DEPRECATED.md:12-13 quote
- v0_correction_shape_prereg.md:89-91 quote
- v0_steering_results.md:3-8
- EXPERIMENTS.md:2095
- test_check_claims.py:105 `term < n` (though :97-99 shows it is a deliberate tripwire)
- 13793be at 23:20 → 5c7ea84
- double_bos_audit.md:28
- generation-recomposition holds, 0.8364/0.1429/0.1111
- PR #9 open since 2026-09-23, "all four models", and the delegation paraphrase quote
- elicitor_calibration_prereg.md:22-24
- Propp +0.049 [−0.005, +0.126] and 15 tales
- Pilot block-24 +0.171
- 20/21 terminal, 28 QUESTIONS items
- Hooks (RESULTS.md, tests/test_invariants)
- enact−true −3.98 / r2 −3.13
- Human grid has 18 cells

**Wrong or partial:**
- 22 vs 21 rows
- "≈0.3M tokens"
- "three batteries failed"
- C4 "spec's own recommendation" is partial
- NA1 "piece 2 layer sweep"
- "binding constraint" attributed to v1
- "constructed stories" for the answer-slot test
- "story-token states" generalisation
- h58a "on deprecated grids"
- "No costs"
- S2 cites QUESTIONS 13
- The C1 link is dead on its own branch

## COVERAGE OF THE BRIEF'S SEVEN QUESTIONS
- **Q1 (does the document chase its tail):** findings 1, 3, 4 and 14. R1–R5 would have truncated the autonomous overnight shame chains A–C at hop 3, including the decisive h61. They would not have stopped:
  - narrative chain A, because the author gave instructions mid-chain and R3 needs no author text;
  - chain D, a theme rather than a caveat chain;
  - chain A′'s rule override before data (goal_reversal_prereg.md:182-183, which R2 allows);
  - the failed-gate → holds generator.
- **Q2 (outcome tables):** findings 2, 6, 8, 9, 10 and 16.
- **Q3 (recommendations):** findings 5, 7, 9 and 18.
- **Q4 (facts):** finding 20 and the spot-check list.
- **Q5 (attribution):** finding 12.
- **Q6 (omissions):** findings 11 and 19.
- **Q7 (scope and rules):**
  - Hooks, CI and C5 are correctly gated to the author, and no proposal makes the core import line code.
  - Not gated: the README/WRITEUP status edits in §7, S1-a's Q3 re-posing, §1's change to CLAUDE.md's definition of done, and the supersession of DELEGATION and v1's standing rules. All need explicit author decisions.

## VERDICT
The diagnosis in §0 is mostly accurate and well sourced. The prescription is another prose layer whose rules an agent applies to itself and can satisfy by labelling. It reproduces the failure it names: 12 author decisions with no default, in a repo that stalled 22 days on one. The decision tree is not decision-forcing where it matters. NC1's table is inverted and cannot reach "holds". NA1 cites a spec that lacks its test and drops the arm that decides its outcomes. S1-b and S2 assign opposite statuses to the same outcome, and several nodes break NN3 or NN4. The recommendations lean toward extension while being labelled "finish": three new-science nodes, Claude's admitted favourite among them, and a new behavioural hypothesis for a line it says to close. The document also makes several factual slips about its own freshest result, C1, which sits in an unmerged PR. Do not accept it as written. It becomes acceptable with these changes: findings 1–3 (defaults with dates, nodes as validated data, NC1 rewritten); a close-now option at N0 and S1-c as the recommendation at S1; and the NN7 labelling fixed in the document's own header.
