> **Provenance.** Written read-only by an agent in the 2026-10-15 cloud session as evidence for [`PROGRAM_v2.md`](../PROGRAM_v2.md), and committed verbatim. It is agent output: judgments are marked as such (**[J]** / *Judgment*), and tallies and sums are the agent's own arithmetic. `PROGRAM_v2.md` §9 lists which citations were re-checked against their files. Line numbers refer to the tree at `2a992c3`.

# Shared method and program layer: audit for the zoom-out program document

I made no changes to the repository. The local clone is shallow: its history starts at `a7fda20` (2026-09-21). To see the full history I made a blobless bare clone of `origin` (456 commits) at `/tmp/claude-0/-home-user-model-research/8f0afb90-77fa-58ee-ac80-44307fefae1b/scratchpad/mr-history.git`. That copy is outside the repo. I also read PRs and Actions runs through the GitHub API.

pytest is not installed in this container's `.venv`, so every test count below is a static count, not a collected count. Anything marked **[J]** is my judgment. Everything else is cited.

---

## 0. Bottom line

1. **`docs/PROGRAM.md`:**
   - Phase 0 was met, but item 0.3 was met only by a waiver.
   - Phase 1 was declared closed, but in a way the program itself forbids (see 1.1).
   - Phase 2 stalled on a decision that was handed to the user and never recorded.
   - Phases 3–5 never started. The only thing done for phase 3 is an empty template.
   - **Nothing after hour 50 references PROGRAM.md, and no newer program document exists.** The work after hour 50 is a new line (shame-axis, which began on 2026-09-19) plus about 20 narrative probes, all outside the phased plan.
2. **Instrument count drift.** The documents give four, five, six and seven broken instruments. INSTRUMENTS.md says seven and mentions an eighth that was never written up. Commit `ad7f788` claimed the count "cannot drift again"; it drifted within two days.
3. **A cross-line invalidation was never carried over.** The double-`<bos>` bug (§7) is marked as affecting narrative generation, including the h29 rerun (`research/shame-axis/notes/double_bos_audit.md:28-33`). The narrative line has no follow-up. h29 is still `holds` (`research/narrative/claims.yaml:117-123`), and it is "the only evidence for recomposition" (`WRITEUP.md:72-74`).
4. **Three of the three Claude Code hooks are broken or bypassed:**
   - SessionStart reads a missing `RESULTS.md`.
   - PostToolUse runs a missing `tests/test_invariants.py`.
   - The merge-diff hook never fires under the PR workflow.

   CI runs only the claims validator. **The core's test suite is not in CI.**
5. **The definition of "done" cannot be reached.** `tests/lsx/test_check_claims.py:105` asserts that no line is closed, and CI runs that test. The claims tables also leave out most program-level open items.
6. **Effort.** Phases 0–2 alone used ≥2.22M agent tokens. The whole five-phase program was budgeted at about 1.7M (`PROGRAM.md:160`). After hour 50, nobody recorded costs at all.

---

## 1. `docs/PROGRAM.md`, phase by phase

PROGRAM.md was written by Fable on 2026-09-17 (`64b143b`). Its content has not changed since: the only later edit was an automated path repoint (`aac368a`, 2026-09-21). Its one rule is: "**No work on phase N+1 while phase N's gate is unmet.** … If a gate cannot be met, the correct move is to write that down in RESULTS.md and stop, not to route around it" (`PROGRAM.md:10-12`).

### Phase 0 — gate: "all three resolved" (`PROGRAM.md:30`) — **MET; 0.3 only by waiver**

| item | gate / ask | status | evidence |
|---|---|---|---|
| 0.1 direct path on the log-prob selectors | Report the computed gain per claim, including "`ndif_factors`, h37's 70B battery" (`PROGRAM.md:34-37`) | **Partially met** | Role lens +1.837, composed +3.614; the stop condition did not fire (`EXPERIMENTS.md:1571-1582`). But the remote batteries were "Not tested here: … the remote 70B and Gemma batteries (unblocked by this result, not withdrawn)" (`:1606-1607`). The role lens at L14 got no verdict (gate 5 failed, `:1596-1599`). And "No G_new below ~0.5 nats from this instrument is trustworthy" (`:1602-1603`). |
| 0.2 ladder nulls | Three nulls run | **Met** | `EXPERIMENTS.md:1615-1670`, including the 42b correction. |
| 0.3 TypeSafe key to proxy injection | "Trivial, but the key is currently visible to every spawned agent" (`PROGRAM.md:54-55`) | **Waived** | "WAIVED by the user (2026-09-18)… Anything that would change the risk (a shared environment, … an untrusted agent) reopens it" (`EXPERIMENTS.md:1687-1691`). The entry's heading still says "blocked on item 0.3, which needs the user" (`:1672`). |

Notes on the 0.3 waiver:
- The commits went from "0.3 blocked on the user's credential UI" (`057143f`, 00:21 UTC) to "0.3 waived by the user" (`72d7503`, 00:50 UTC), 29 minutes apart.
- **[J]** The waiver is attributed to the user, but no commit carries the user's words. Under non-negotiable 7 (`CLAUDE.md:28-31`) it should be labelled a paraphrase, and it isn't.
- **[J]** The waiver's own reopen condition, "a shared environment", plausibly fired on 2026-09-22:
  - "Two agents share the machine" (`CLAUDE.md:56`).
  - Keys now come from `~/.bashrc` (`CLAUDE.md:57`).
  - NDIF itself moved off proxy injection on local hardware (`c9256f6`: "the local machine has no proxy").

### Phase 1 — gate: "§1A reproduction AND §1B rediscovery" (`PROGRAM.md:61`) — **declared closed; partially met**

- §1B was met: 12/12 rediscovery cases (`EXPERIMENTS.md:1947-1950`). There are now 14 (`src/lsx/core/rediscovery.py:71-766`).
- §1A was declared closed "with one target outstanding and named — **h37's 70B matched pair, whose direction stacks are not cached**" (`EXPERIMENTS.md:1950-1954`).
- PROGRAM.md says: "If §1A cannot be met for a target, that target is **withdrawn from the writeup**, not the tolerance loosened" (`PROGRAM.md:74-75`). Claim 11 (h37) is still asserted in `WRITEUP.md:82-88`; only the limitations section notes it was not re-derived (`:294-295`).
- The h16 refusal was counted as a pass. That accounting decision "has not been revisited since" (`research/narrative/docs/QUESTIONS.md:12-15`).
- Budget: ~500k (`PROGRAM.md:77`). Actual: 190k + 225k + 370k + 515k = **1.30M** for h43–h46 (`EXPERIMENTS.md:1753, 1812, 1882, 1940`), plus h47, whose token count was not recorded (about 3 h 10 min, about 540 NDIF jobs; `:2057-2061`). That is at least 2.6× over.

### Phase 2 — gate: "every standing claim is a ledger entry or withdrawn" (`PROGRAM.md:82`) — **NOT MET; stalled, then silently abandoned**

- The spec says: "the gate as written cannot be met inside that budget, and one claim cannot be met inside phase 2 *at any budget*" (`docs/specs/phase2_v1.md:6-8`). Recommended option: "(b) Amend the gate… This is the user's call" (`:84-98`).
- The log says: "**That decision is the user's and the program waits on it**" (`EXPERIMENTS.md:2095`).
- Work did not stop. h48–h50 ran on the argument that they were "valid under all three options" (`:2097-2100`). The phase-2 spent was 353k + 143k + 187k = **683k**, against a budget of 150k, which is 4.6× (`:2210-2211, 2257, 2320`). h48 also found that its own spec was wrong (`:2115-2124`).
- Later entries still say "the phase-2 gate decision is still outstanding" (`:2258`) and "still wait on the gate decision" (`:2317`).
- **No decision is recorded anywhere.** No Checkpoint 3, no NOT-DERIVED markings and no fifth-draft writeup exist (a repo-wide grep finds them only in PROGRAM.md and phase2_v1.md).
- The `Ledger.render()` path that was supposed to generate the hour entries (`PROGRAM.md:85`, `core_v1.md:360-361`, `src/lsx/core/ledger.py:219-247`) is never called to write the log. The ledger stopped at 36 lines: 32 rows plus 4 withdraw operations, last changed before 2026-09-21.
- **[J]** This is "write it down and *don't* stop". It contradicts `PROGRAM.md:10-12`.

### Phase 3 — gate: "one grid authored by a person, run through the core" (`PROGRAM.md:96`) — **NOT MET; never started on the user's side**

- Opus's part is done:
  - Template `f5716d9` and checker `1baeb36`, both on 2026-09-18 at 05:55–05:56 UTC. That was *before* phase 1's gate closed (`0e05e9f`, 08:03 UTC), so it is technically a one-rule violation **[J, minor]**.
- The grid is empty: 0 of 18 cells filled, `"author": "<your name>"`.
- The template sits in the wrong line's directory, `research/shame-axis/prompts/human/human_factors_v1.json`. Its instructions still say "Fill in `prompts/human/human_factors_v1.json`" (`research/shame-axis/prompts/human/GRID_INSTRUCTIONS.md:16`).
- It is still named the top credibility item: "the first thing a reviewer will ask about" (`EXPERIMENTS.md:92-94`) and "the binding constraint is authorship" (`WRITEUP.md:307-309`).
- Shame-axis followed the same pattern:
  - Its human grid reached 1 of 24 items ("pilot: item 1 of 24 is human-authored", `conscription_v1.json` `_meta.note`).
  - Commit `2b9cadc` then deprecated it ("Our claude/ and human/ grids are deprecated").
  - Open PR #9 (hour 65) says the clause writing was delegated to two AI agents, Claude and Sol. The PR body labels that statement itself as a paraphrase.

### Phase 4 — gate: "piece 2 of `scale_vs_tuning_v1.md` complete" (`PROGRAM.md:111`) — **NOT STARTED**

- Piece 2 (`docs/specs/scale_vs_tuning_v1.md:339`) was never run.
- Its deliverables do not exist (`results/svt_era_70b_3.0.json`, `scripts/scale_vs_tuning_report.py`, `results/notes/scale_vs_tuning_gen.md`; spec lines 346-357).
- It is still listed as "The next experiment" (`WRITEUP.md:302-305`; `EXPERIMENTS.md:2360`).

### Phase 5 — `cohere` — **NOT STARTED**

There is no cohere spec in `docs/specs/`.

### Standing rules (`PROGRAM.md:138-150`)

| rule | status |
|---|---|
| 1. Fable plans, Fable reviews | Abandoned at phase 2: "Fable's monthly budget is exhausted" (`phase2_v1.md:9-10`). Preregistrations after hour 50 carry "adversarial review" amendments (e.g. `research/narrative/notes/goal_reversal_prereg.md:16-17`), but who reviewed is not recorded. |
| 2. Pre-merge screen, four-question screen | The screen was never built: no code anywhere matches DELEGATION.md:74-93. The merge hook is bypassed (see §7). 7 of 10 merged PRs were merged ≤86 s after opening (#1, #2, #3, #4, #5, #11; GitHub API). **[J]** The PRs themselves show no evidence of a screen. |
| 3. Every entry states what it did not test, and its cost | Cost recording stops after h50. There are no Cost lines in `research/shame-axis/docs/EXPERIMENTS.md` or in any narrative `*_result.md`. |
| 4. A retraction pauses the program | Followed in shame-axis: r2 re-scoring (h63) came before h64. Not followed for the narrative h29 double-`<bos>` audit (§2). |
| 5. One agent at a time | Violated on 2026-09-22. Merge `2701468`: "Both sessions fixed the double <bos> independently… The local session's 62b… is marked abandoned." Both sessions also used NDIF. |

**[J] Did work after hour 50 follow PROGRAM.md? No.**
- PROGRAM.md is referenced only by phase 0–2 artifacts (EXPERIMENTS.md, the phase-0 scripts, two specs).
- It is not linked from `CLAUDE.md` or `README.md`, which are the agents' entry points.
- The restructure commit (`5278043`) describes the shame-axis line as having "moved in because the tools were there".
- PROGRAM.md:24-26 excluded anything that serves neither of its two products. Shame-axis serves neither, and neither do the narrative goal/route/choice-slot probes.
- The de facto replacement is the per-line claims-closure rule (`CLAUDE.md:68-77`). That rule has no phases, no budgets and no priorities.

---

## 2. Broken instruments

### The logged ones

INSTRUMENTS.md lists seven (`docs/INSTRUMENTS.md:3`). CLAUDE.md:9 says five, and the task brief said five.

| § | What broke | What it invalidated | Rail now |
|---|---|---|---|
| 1 (h6) | A cross-talk rank over 3-of-3 candidates averages 2.0 by construction (`:29-30`) | Nothing published; the metric was replaced (`:36-39`) | The calibrate() sensitivity test (`core_v1.md:239-242`), rediscovery case 6. **But the `crosstalk` instrument is still unbuilt** (`src/lsx/core/registry.py:213`), so writeup claim 4d (diagonal cross-talk) cannot be ledgered. |
| 2 (h1–3) | Best layer chosen on held-out scoring data, 3.5 → 2.4 from selection alone (`:53-55`) | All best-layer numbers and all pre-h3 relation claims (`:61-64`) | `Selection` + `SelectionOnScoringData` (`checks.py:95`), sweep curve mandatory at the ledger (`core_v1.md:205-214`), rediscovery cases 4 and 11, non-negotiable 4. Caveat: h38 still used argmax L* (`:68-69, 337-338`). |
| 3 (h28–31, caught h32) | A 1536-d residual norm sitting at its own noise floor; τ = 1 day guaranteed (`:82-92`) | Three published negatives (`:96-99`) | `Floor` with a required estimator (`MissingFloor`, `checks.py:87`), calibrate() noise test, rediscovery case 5, non-negotiable 3. |
| 4 (h34, caught h36) | `output[0]` was batch row 0; rank-1-on-ties pinned every rank at 1.22 (`:115-125`) | All h34 selector files, cross-talk matrices, the layer sweep (`:133-138`) | `resid()` helper, mid-rank ties, mandatory no-patch arm, `MovedCandidates` (`checks.py:35`) on the core remote path. It caught the bug live on NDIF at h46 (`EXPERIMENTS.md:1897-1901`). Rediscovery cases 1 and 3. |
| 4b (h30–31, caught h39) | Absolute span indices under nnsight left padding; 363 of 480 passages corrupted (`:160-170`) | h31's numbers; the conclusion was re-measured (`:176-183`) | End-relative indices, padding-side assertion, `BatchEquivalence` on the shortest item (`core_v1.md:276-282`), rediscovery case 2. |
| 6 (h55) | A calibration gate built only from null arms; the coder read 0 in all seven arms (`:213-218`) | Nothing believed; `exit-escalation` was kept `running` (`:232-234`) | **No code rail.** The lesson ("only a positive control bounds false negatives", `:236-240`) was applied per study (grid 2's positive control, `102ad09`). The coder is not a registered instrument, so calibrate() never applied to it. |
| 7 (h55–62, caught 62b) | Doubled `<bos>` plus logits read before Gemma's softcap, in bf16 (`:249-262`) | "every behavioural number on the conscription line" (`:265-269`) | `checks.DoubleBos` (`checks.py:43`), `assert_single_bos` / `strip_template_bos` (`remote.py:194-246`), fp32 softcap (`remote.py:425-460`), `tests/lsx/test_core_double_bos.py` (5 tests). **No unit test covers the softcap.** It was validated once on NDIF (`:275-285`). |

§5 (the lexical floor and the h38 calibration failure) is correctly not counted (`:190-209`).

### Internal inconsistencies in INSTRUMENTS.md

- Line 3 says "Seven", but line 6 calls the post-norm residual "A seventh" — it would be the eighth.
- Lines 10-12 still say "four… A sixth followed".
- The summary (`:295-301`) counts six.
- `:329-334` still says the ladder "has no permutation null", which was resolved at h42.
- `:316-321` says both that h8's tense was re-run and "not re-run".

### Instrument issues found since that are NOT in INSTRUMENTS.md

| Issue | Where |
|---|---|
| **The double-`<bos>` bug affects narrative generation: the h29 rerun and older NDIF generation scripts. "audit owned by the narrative line."** No narrative follow-up exists (a grep of `research/narrative` for bos finds only two post-50 preregs). §7's invalidation list omits it. | `research/shame-axis/notes/double_bos_audit.md:28-33`; code path `src/lsx/narrative/rerun_h29.py:153-156, 206-209` |
| A NaN arm tolerance silently disabled `ArmOffNull` ("an arm 9.0 from a null of 0.0 reported off_null False"). Its regression test lives in a line's test directory. | Commit `955d0f4`, 2026-09-20; test at `tests/shame_axis/test_core_conscription.py:329` |
| Checkpoints keyed on item id served stale revised items | `955d0f4` |
| Post-norm residual mislabel (admitted unlogged) | `INSTRUMENTS.md:6-8`; `EXPERIMENTS.md:25-32`; `rediscovery.py:404` |
| The leak detector is anti-predictive by construction, so every earlier leak number was read against the wrong baseline | `EXPERIMENTS.md:1722-1728` |
| `readout_shift`'s cosine form is biased negative | `:1778-1789` |
| The `sqrt(2/d)` tolerance was 8.8× too tight, which overstated h40 as "worse than arithmetic" | `:1840-1849` |
| Calibration-key bugs: config-dependent key; top-level-only hash; missed comprehensions; `arm_tolerance` not in the key | `:1858-1862, 1906-1911, 2139-2143` |
| The i.i.d. arm band refused clean draw-based arms, then its replacement admitted dirty ones | `:2033-2041, 2200-2208` (fixed h49) |
| `Claim.id` collisions when the patched factor is not in provenance | `:2020-2025` |
| `hash()` seeds differed per process | `:2052-2053` |
| **Open:** the permutation arm sits below its null on 25 of 25 rows | `:2187-2192`; `claims.yaml:161-167` |
| `core_v1` §6's "layer 0 *is* the bag-of-tokens check" is falsified for this readout, but still stated in `core_v1.md:260-261` | `EXPERIMENTS.md:2179-2182` |
| Bootstraps over cases rather than units (−0.24 nats) | `:2152-2154` |
| h29 generation loss is unequal across arms | `:2059-2061` |
| The remote readout still depends on batch composition (≤0.13) after the §7 fix | `1da2dd9` message; `INSTRUMENTS.md:279-281` |
| Llama chat failed the h39 equivalence guard (cos 0.99885) | `6dfe576` |
| Gemma Scope is off-distribution on conversation | `research/shame-axis/docs/QUESTIONS.md:148-152` |
| An h58b fixed point of the §6 family ("24 paired zeros"; the prereg rule would have read p = 1 as support) | `1ecc94b` message |
| The dense axis and the opener readout disagree in sign | `research/shame-axis/docs/QUESTIONS.md:153-157` |
| The S2 pain axis fails its positive control at the screen layers in all four models | PR #9, open and unmerged since 2026-09-23 |

---

## 3. Specs inventory (`docs/specs/`)

| Spec | Purpose | Line | Status |
|---|---|---|---|
| `claims_v1.md` (09-21) | Schema and closure rule for `claims.yaml` | shared | **Implemented, with gaps** (§4) |
| `core_v1.md` (09-13 → 09-18) | Verified core: §1A/§1B, Claim contract, registry, ledger | shared | **Mostly implemented** (pieces 1–5). `crosstalk`, `depth_gain` and `generality` are declared but unbuilt (`:310, 313-314`; `registry.py:213, 288, 302`). §9's generated log is unused. h37 is deferred. |
| `phase2_v1.md` (09-18) | Phase-2 inventory and the gate decision | narrative | **Abandoned.** Decision never made. §0 correction at `:12-26`. |
| `selector_direct_path_v1.md` (09-17) | Phase 0.1 | narrative | **Executed** (h41). The header still says "Status: not run" (`:3`). |
| `scale_vs_tuning_v1.md` (09-12) | 70B base/instruct pair, generation arms | narrative | **Piece 1 done** (h34 withdrawn, h36–37 re-run). **Piece 2 never run** (phase 4). |
| `time_translation_v1.md` (09-11) | Time translation T(Δt) | narrative | **Executed (h28), superseded**; the line closed at h38. |
| `subject_clocks_v1.md` (09-12) | Noise-floor-aware subject-clock test | narrative | **Executed (h32), superseded.** Line closed. |
| `clock_depth_gain_v1.md` (09-12) | Clock as depth gain over the lexical floor | narrative | **Executed (h38).** P0 calibration failed (`INSTRUMENTS.md:202-209`). Its `depth_gain` instrument is unbuilt. |
| `conscription_instrument_v1.md` (09-20) | A Claim-able instrument for an unpatched paired design | shame-axis | **Unimplemented.** "proposed, not built, not reviewed" (`:3`). `src/lsx/shame_axis/conscription.py:5-10` confirms there is no registry entry. The line later deprecated its own grids (`2b9cadc`). |

**[J]** Seven of the nine specs are line-specific, yet they sit in the shared `docs/specs/`. Since 09-20, planning has moved to `research/<line>/notes/*_prereg.md` (23 narrative files, 8 shame-axis files). `docs/specs/` is no longer where plans live.

---

## 4. Core status and the claims machinery

### `lsx.core`

Eleven files, 6,483 lines:
- `types.py` 918
- `checks.py` 801 (29 `CoreError` subclasses, lines 23-162)
- `extract.py` 257
- `remote.py` 646
- `instruments.py` 613
- `registry.py` 372
- `planted.py` 322
- `ledger.py` 247
- `rediscovery.py` 894 (14 cases)
- `reproduce.py` 1,384
- `__init__.py` 29

Other code:
- Legacy top-level `lsx` modules: 666 lines. The core imports from them (`core/extract.py:29-30`, `core/remote.py:158, 505`).
- Line modules: narrative 1,956 lines, shame_axis 747.

Layering:
- No core module imports a line module, as required by `CLAUDE.md:44`.
- **But the shared core hard-codes narrative paths:**
  - `CALIBRATION_DIR` (`checks.py:680`)
  - ledger `DEFAULT_PATH` (`ledger.py:43`)
  - `DATA_DIRS` / `PROMPT_DIRS` (`reproduce.py:42-44`)

Who uses which parts:
- Post-50 scripts use only `lsx.core.remote` and `checks`: 19 of 96 narrative scripts and 15 of 27 shame-axis scripts.
- **Only the phase-1/2 code builds `Claim`s or writes the ledger** (`src/lsx/narrative/{phase2,piece5}.py`).

### Tests

There are **348 `def test_` functions** (static count): 141 in `tests/lsx`, 92 in `tests/narrative`, 115 in `tests/shame_axis`. `README.md:44` says "261 tests", which was the count at the restructure (`5278043`).

Core coverage:
- rediscovery 25
- registry/calibration 24
- instruments 21
- ledger 20
- remote 10 (mocked)
- invariants 13
- double-bos 5
- pipeline 5
- claims/pages 18

### CI

`.github/workflows/pages.yml` triggers only on push to `main` (`:3-5`). It runs `check_claims.py` (`:33`) and `tests/lsx/test_check_claims.py` (`:36`), then deploys Pages. **The core suite never runs in CI. No CI runs on pull requests, so claims validation happens after a merge, not before it.** The 30 most recent runs listed all succeeded; the last was 2026-09-23.

### `claims_v1` requirements vs what `check_claims.py` enforces

| Spec rule (`claims_v1.md:77-82`) | Enforced? |
|---|---|
| 1. `id`, `claim`, `status` present; status valid | Yes (`check_claims.py:62-74`) |
| 2. Unique ids | Yes (`:69-71`), plus a slug regex (`:66-68`) |
| 3. Terminal claims have `where` | Yes (`:77-80`). The file must exist only if `where` contains "/" (`:92`). Anchors are never checked. 20 of 52 narrative rows point at the whole 2,363-line log, and 0 rows in either table use an anchor. |
| 4. `withdrawn` has `superseded_by` | Yes (`:81-83`). Free text, not checked against a claim id. |
| 5. "must contain a verb and end in a full stop" | **Partly:** only the full stop and ≥4 words (`:85-89`). No verb check. |
| 6. "no claim is both `pre_registered: true` and missing from the line's log" | **Not enforced at all.** My heuristic check (claim id or note name absent from the log) finds **26 of 30 pre-registered narrative claims** missing from the log, because the narrative log stops at hour 50. |

Other gaps:
- Header fields (`title`, `question`, `blurb`, `audience`) are not validated.
- A table with zero claims passes silently (`:103-106`).
- Id stability is not enforceable.
- There is no staleness check on `running`.
- `test_check_claims.py:105` asserts `term < n` for both lines, **so CI fails the day either line actually closes.**

---

## 5. Pacing and effort

### Timeline (full history: 456 commits, 426 excluding merges)

| Dates | Commits | What | Recorded cost |
|---|---|---|---|
| 09-11 | 93 | h1–h26: stages 2–26, factors, NDIF setup, VISION/ALGEBRA, writeup drafts 1–2, Checkpoint 1 | only h26: ~300k (`EXPERIMENTS.md:1252`) |
| 09-12 | 45 | h27–h39: time translation (~1M, `:79`), generation boundary, h34 bug → h36 fix, Checkpoint 2, writeup draft 4, INSTRUMENTS.md, h39 audit | **2.30M** (h27–h39) |
| 09-13 | 7 | core_v1 v1→v1.3 with adversarial review; h40 withdrawal | 135k |
| 09-14 to 09-16 | 0 | — | — |
| 09-17 | 18 | Jev judge; DELEGATION.md; invariant suite plus 3 hooks (3 hook-fix commits); PROGRAM.md; direct-path spec v1/v2; h41, h42/42b | 240k + h42 unrecorded |
| 09-18 | 41 | Phase 0 gate; phase 1 pieces 1–5 (h43–47, ~7 h of wall time); human-grid template; phase-2 spec and stall; h48–50 | 1.30M + h47 + 683k |
| 09-19 to 09-20 | 20 | **New line:** conscription grid (`06901fa`), harness, pain-axis vendoring, Tier A | none recorded |
| 09-21 | 41 | h51–55; restructure into two lines (`5278043`); 415 path repoints; NDIF citation; claims.yaml and validator; public pages (6 commits in about 35 min); instrument 6 | none |
| 09-22 | 85 | Shame-axis h56–62b; instrument 7; parallel duplicate sessions; r2; hardware move; narrative probes begin (Propp → remote choice) | none (shame-axis overnight: "288 opener cells took ~7 hours", `overnight_2026-09-22.md:100-101`) |
| 09-23 | 106 | PRs #1–#11 (10 merged, #9 open); shame h63–64; about 13 narrative probes (goal reversal → double-flip) | none |
| 09-24 to 10-15 | 0 | **Inactive for 22 days.** PR #9 open. | — |

### Effort fractions

- **By recorded tokens (h26–h50, ~4.96M):**
  - New measurement: ~2.03M, **≈41%** (h26–31, 33–35, 37–38).
  - Instrument repair and verification: ~2.93M, **≈59%** (h32, 36, 39–41, 43–46, 48–50).
  - Documentation and process work in that window has no recorded cost.
  - **[J]** h32 and h34 could be classed either way.
- **By commit count** (heuristic keyword-and-path classifier, roughly ±10%): science ≈ 64%, repair/verification ≈ 27%, documentation/process/presentation ≈ 9%. On 09-17 and 09-18 alone, about 80% was repair/verification, by design.
- **Against budget:** phases 0–2 used ≥2.22M (h41 + h43–46 + h48–50), compared with the 1.7M budgeted for all five phases (`PROGRAM.md:160`).

---

## 6. Recurring "chasing our tail" patterns

All of these are **[J]**, each with the evidence it rests on.

1. **Gates set, then waived, closed with exceptions, or left hanging.**
   - 0.3 went from blocked to waived in 29 minutes.
   - Phase 1 was closed despite `PROGRAM.md:74-75`.
   - Phase 2 was "write it down and keep going", with 683k spent after the stall, then dropped.
   - Plans were reversed within a day. The overnight note said "**Do not steer yet**" and "The human grid… 23 items still owed" (`overnight_2026-09-22.md:95-96`). That same day, `2b9cadc` pre-registered steering (62b) and deprecated the human grids.
2. **A process layer is added after each failure, and enforcement decays.**
   - Layers added: non-negotiables (6 → 7), DELEGATION.md, hooks, PROGRAM.md, the core contract, claims.yaml, pages, the PR rule.
   - What has decayed:
     - All three hooks are broken or bypassed (§7).
     - The screen was never built.
     - The ledger-generated log was never used.
     - The planner rule was dropped on budget.
     - Cost logging stopped after hour 50.
     - The one-agent rule was broken.
     - PROGRAM.md is unreferenced.
3. **Fixes carry their own bug.**
   - "The sixth time in this build that a fix has carried a version of the bug it was fixing" (`EXPERIMENTS.md:2047-2048`).
   - "This build has produced a fix carrying its own bug six times" (`:2308-2309`).
   - h48 opened a problem that h49 closed: "closed the hour after it opened" (`:2215`).
4. **Caveats spawn experiments, and failed gates spawn narrower "holds".**
   - The narrative chain after hour 50 ends at "a winning listed-plan-slot component… not a unique code or a causal story edit" (`claims.yaml:425-431`).
   - Each failed registered gate is paired with a narrower component that "holds": late-reveal (`:369-383`), story-token (`:385-399`), first-hop (`:401-415`).
   - Shame-axis has **28 open questions with none closed** (`research/shame-axis/docs/QUESTIONS.md`), while its table reads 20 of 21 terminal. Its central claim, `shame-not-pain`, is still open, and the last attempt (PR #9) was "unreadable".
   - Its hypothesis is itself "Claude's paraphrase of conversation not in the repo" (`QUESTIONS.md:61-64`).
5. **Counts drift after being "fixed".**
   - Instrument counts: "four" (`WRITEUP.md:5`), "five" (`CLAUDE.md:9`, `README.md:22`, `DELEGATION.md:3,12`, `core_v1.md:3`, `scripts/build_pages.py:375-376,397`), "six" (`CLAUDE.md:25`, `DELEGATION.md:16`, `research/shame-axis/docs/EXPERIMENTS.md:9-10`), "Seven" (`INSTRUMENTS.md:3`).
   - Test count 261 vs 348.
6. **The progress bar overstates closure, and closure is blocked anyway.**
   - Writeup claims 5, 6, 7, 9 and 10, the human grid, phase 4 and the h29 audit have no claims rows. CLAUDE.md:76-77 warns about exactly this.
   - The test at `test_check_claims.py:105` forbids closure.
7. **The shared retraction ledger did not propagate a cross-line hit** (h29, §2), despite `CLAUDE.md:10` and `README.md:25-26` promising that it would.

---

## 7. Stale or broken infrastructure, with the exact fixes

| # | Problem | Fix |
|---|---|---|
| 1 | SessionStart hook (`.claude/settings.json:34`) runs `awk … RESULTS.md`. That file was moved by `5278043`, so the hook prints only its header. Even repointed, its grep finds one stale line. | Replace the command with `cd "$CLAUDE_PROJECT_DIR" && python3 scripts/check_claims.py 2>&1 \| head -15` (optionally also list `open`/`running` claim ids from each `research/*/claims.yaml`). |
| 2 | PostToolUse (`:9`) matches `*tests/test_invariants*` and runs `pytest tests/test_invariants.py`. The file is now `tests/lsx/test_invariants.py`, so the invariants never run. | Change both strings to `tests/lsx/test_invariants.py`, and consider adding `tests/lsx/test_core_rediscovery.py`. |
| 3 | PreToolUse merge hook (`:22`) fires only on a local `git merge` of branches matching `worktree-agent-…\|h[0-9]+-…`. No PR branch matches, and PRs are merged on GitHub. | Add a `pull_request` CI job that runs the full `pytest` and posts `git diff origin/main...HEAD -- src/lsx 'scripts/*/*extract*' 'scripts/*/*factors*' 'scripts/*/*selector*' 'scripts/*/*patch*'`. Make it a required check. |
| 4 | `pages.yml:3-5` has no PR trigger and runs no core tests | Add `pull_request:` and a `pytest` step on CPU torch |
| 5 | `test_check_claims.py:105` asserts that lines are open | Remove the assertion, or assert instead that a closed line has an empty QUESTIONS/open-problems list |
| 6 | `RESULTS.md` references at `PROGRAM.md:11,85`; `DELEGATION.md:4,55,70`; `INSTRUMENTS.md:10,16`; `core_v1.md:360`; `scale_vs_tuning_v1.md:372`; `research/narrative/README.md:50,95,102`; `WRITEUP.md:3` | Point them at `research/<line>/docs/EXPERIMENTS.md` |
| 7 | `docs/ALGEBRA.md` references (`DELEGATION.md:55,71`; `WRITEUP.md:5,316`; narrative `README.md:98`; specs) | Point them at `research/narrative/ALGEBRA.md` |
| 8 | Narrative README: flat `scripts/` and `prompts/` paths (`:62-64, 89`); orphaned table rows (`:81-82`); a duplicate "Documents" section (`:93-111`); `python -m lsx.core.reproduce` (`:124`), but `reproduce.py` has no `__main__`, so it does nothing | Repoint the paths, merge the two sections, and add `if __name__ == "__main__"` to `reproduce.py` (or point at `research/narrative/results/repro_p4_driver.py.txt`) |
| 9 | `scripts/clock_gain_run.sh` and `scripts/run_commutator_v2.sh` hard-code `/home/user/latent-space-exploration` and the flat layout | Move them to `scripts/narrative/` and repoint, or mark them historical |
| 10 | Root `results/calibration/` holds 6 orphaned copies; 2 differ from the live cache under identical keys (`selector.f9555…`, `readout_shift.7b3b…`) | Delete them. Move `CALIBRATION_DIR` (`checks.py:680`) and the ledger `DEFAULT_PATH` (`ledger.py:43`) out of the narrative tree. |
| 11 | `.gitignore` patterns `results/*.log`, `results/*.json.partial`, `results/conscription_dry_run/` and `prompts/holonic_candidates.jsonl` are anchored at the root and no longer match. The dry-run actually writes to `research/shame-axis/results/conscription_dry_run`. | Use `research/*/results/...` and `research/narrative/prompts/holonic_candidates.jsonl` |
| 12 | The phase-3 grid sits under shame-axis, and its path text is stale (`GRID_INSTRUCTIONS.md:16`; `scripts/narrative/human_grid_check.py:4`) | Move it to `research/narrative/prompts/human/` and fix both paths |
| 13 | Instrument counts (§6.5) | Replace the hard numbers with "see docs/INSTRUMENTS.md". Fix `INSTRUMENTS.md:3-12`. |
| 14 | `README.md:44` "261 tests" | Drop the number |
| 15 | Stale docstrings and status lines: `selector_direct_path_v1.md:3`; `conscription_instrument_v1.md:3-4`; `conscription.py:1-2`; `instruments.py:11`; `ledger.py:24`; `EXPERIMENTS.md:31` and `selector_direct_path_v1.md:77` (`tests/test_invariants.py`) | Repoint each, and set the direct-path spec's status to executed (h41) |
| 16 | Leftovers from the parallel sessions: duplicate helpers `assert_single_bos` (`remote.py:205`) and `_assert_one_bos` (`:237`); `scripts/shame_axis/v0_steer.py` marked ABANDONED | Consolidate the helpers and delete the abandoned script |
| 17 | PR #9 open for 22 days | Merge it or close it |

---

## 8. External products

| Product | State |
|---|---|
| **Public GitHub Pages site** (`scripts/build_pages.py`, `pages.yml`) | Deployed on every push to main (33 runs, last 2026-09-23). Generated from `claims.yaml`. The landing copy hard-codes "five instruments" (`build_pages.py:375-376, 397`). It also says the harness "reconstructs every bug this project has shipped" (`:400-402`), which is now untrue: there are no cases for §6, the §7 softcap or the NaN tolerance. The site URL is not recorded anywhere in the repo. |
| **`audience` field** | narrative: "mechanistic interpretability · narratology · computational literary study" (`research/narrative/claims.yaml:11`); shame-axis: "mechanistic interpretability · model welfare · AI safety" (`research/shame-axis/claims.yaml:10`). It is rendered as a page label (`build_pages.py:315`), not validated, and not tied to any audience-specific product. |
| **Narrative WRITEUP.md** | "Fourth draft, after 46 logged stages" (`:3`), though it cites stages 47–48. It has no post-50 results and stale paths. The promised fifth draft (`PROGRAM.md:85-88`) was never written. |
| **"Portfolio artifact" = the trusted core** (`PROGRAM.md:18-19`; `build_pages.py:403-404` "the two pieces worth extracting") | Not extracted or packaged (`pyproject.toml`: `model-research` 0.0.1). Its tests are not in CI. |
| **The "narrow, defensible research claim"** (`PROGRAM.md:20-22`) | Never written as a standalone product. The writeup still lists "eleven things stand" (`WRITEUP.md:16`). |
| **Shame-axis** | README and claims only. No writeup. PR #9 is unmerged. No paper, preprint or outreach plan appears anywhere in the repo. |
| **Jev evaluation; NDIF citation** | Internal note (`research/narrative/notes/jev_prose_gate.md`); README acknowledgement with an open ICLR question (`README.md:92-94`). |
