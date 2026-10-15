> **Provenance.** The verification pass on `PROGRAM_v2.md` v0.2 (commit `bf8f683`), written read-only by an agent in the 2026-10-15 cloud session, committed verbatim. Probe scripts it mentions lived in that session's scratch directory and are not in the repository. v0.3 answers it; `PROGRAM_v2.md` §10 summarises what changed.

Verification pass on PROGRAM_v2 v0.2 (`bf8f683`, PR #13). I edited nothing in the checkout. Probes are in /tmp/claude-0/-home-user-model-research/8f0afb90-77fa-58ee-ac80-44307fefae1b/scratchpad/verify/ (probe.py, probe2.py, probe3.py). `check_nodes.py` prints OK, its 13 tests pass, and the full suite collects 398 tests.

# BLOCKING

**B1. The default path (N0 = D) cannot close the narrative line.**
- **Where:** §4 N0 option D, §6 #4/#6, `research/narrative/nodes.yaml`.
- **Problem:** D retires NC2 (4 claims), NA1, NA2, NB1 and NB2. Nothing under D retires `generic-choice-slot-explanation`. Its only node is NC1, which D does not run.
- **Evidence:** probe3 accepts the tree, defaults N0 to D and marks NC1 retired. It then fails: `open claims with no node: ['generic-choice-slot-explanation', …]`.
- **Fix, §4 D bullet:** "Retire through NC2, NA1, NA2, NB1 and NB2, **and retire `generic-choice-slot-explanation` (reason: "sufficiency test not funded under D"; reopen trigger: NC1 as specified)**, with the reasons below." Add it to §6 #6.
- **Fix, yaml:** add a retire node.
```yaml
  - id: nc1-unfunded
    title: Retire generic-choice-slot-explanation if NC1 is not funded
    kind: retire
    claims: [generic-choice-slot-explanation]
    parent: null
    status: proposed
    outcomes:
      - {if: "N0 = D+NC1", then: continue, child: nc1-slot-sufficiency}
      - {if: "retire: sufficiency test not funded under D", then: retire}
    default: "retire: sufficiency test not funded under D"
    decide_by: 2026-10-29
```

**B2. NC1's "holds" branch can fire with about 70% of the transfer left, and it overlaps "underpowered".**
- **Where:** §4 NC1 Outcomes, `nodes.yaml` nc1.
- **The null is too loose.** The pilot's orientation null has q95 = +0.0687 (`goal_route_activation_pilot_result.md:32`), which is 0.80·T₀. So "T_proj inside the orientation null" is true for any ρ ≲ 0.8.
- **Holds has no power condition.** It never looks at ρ's CI. ρ = 0.7 with CI [0.45, 0.95] can be "holds" even though ρ_lo > δ. That breaks non-negotiable 3 and contradicts the falsify logic.
- **Holds overlaps underpowered.** From the pilot's domain CI (±0.0217), SE_T ≈ 0.011, SE_ρ ≈ 0.13 and δ ≈ 0.32–0.36. Any ρ̂ from about 0.11 to 0.2 satisfies both branches.
- **Gate 0 is ill-defined.** The "recorded repeat drift" is an L2 drift on activation vectors (prereg:81-83), recorded as 0. It is not a tolerance on a mean cosine. Offline, the gate passes trivially. On re-extraction, any float difference fails it.
- **"The exact orientation null" is ambiguous.** The notes contain three:
  - the pilot's world-label null, floor 2/256;
  - the control's source-orientation null, which the note calls structurally weak (floor ≈93/256, `choice_slot_control_result.md:42-50`);
  - the replication's target-label null, floor 1/256.
- **Two more terms are undefined:**
  - "The property direction" could be fitted on 4 or 8 domains, at any block.
  - "The route direction" has 16 fold-specific versions.
- **The 0.58 premise is not in the notes.** +0.583 is a mean cosine against held-out property interaction vectors, not a direction-to-direction cosine. The only direction-level number is +0.235 (control:59-61). A ±0.05 cosine window cannot be hit by sampling in d≈3584.
- **Replacement block:**
> - **Statistic.** T(·) is the pilot's registered statistic (`goal_route_activation_pilot_prereg.md:44-55`): held-out cosine against seven-domain opposite-telling directions, mean of blocks 16 and 24. T₀ = T on the unprojected `I_first` vectors (+0.0854, result:31). T_proj = T after removing, at each block b, the component along p_b from every `I_first` vector (fitted and held-out) before unit-normalisation. p_b is the unit direction fitted at block b on all eight `choice_slot_replication` property domains, both tellings, using no route state. ρ = T_proj/T₀. All six blocks are reported; none is selected.
> - **Gate 0.** |T₀ − 0.0854| ≤ 0.0005, recomputed with the pilot's corrected analysis code. On re-extraction, the pilot's repeat-drift gate (prereg:81-83) must also pass. If either fails: stop, escalate, default close (claim retired, "pilot did not reproduce").
> - **Nulls.**
>   - (i) The pilot's exact 2⁸ world-label orientation null (prereg:56-59), recomputed on the projected vectors. "Inside" means T_proj ≤ its q95.
>   - (ii) 64 cosine-matched directions r_i = c_b·u_b + √(1−c_b²)·z_i. Here u_b is the unit mean of all eight domains' unit `I_first` vectors at block b, c_b = cos(p_b, u_b), and z_i is uniform on the unit sphere ⟂ u_b (seeds 0–63). Each r_i is projected out exactly as p_b is.
> - **CI and δ.**
>   - ρ's 95% CI comes from the pilot's 10,000-draw domain bootstrap, resampling domains jointly for T_proj and T₀.
>   - δ is the smallest true ρ whose CI excludes 0 with probability 0.8. It is simulated from the pilot's domain-level scores and committed before any projection.
>   - If δ ≥ 0.5, NC1 does not run (underpowered by design; escalate, default close).
> - **Outcomes** (mutually exclusive by construction):
>   - ρ_hi < δ **and** T_proj < q05 of the cosine-matched residuals → **holds**;
>   - ρ_lo > δ **and** T_proj > the orientation null's q95 → **falsified**; escalate, default close;
>   - ρ_lo ≤ 0 **and** ρ_hi ≥ δ → **underpowered**;
>   - otherwise → **narrowed**, recording ρ, its CI and the cosine-matched comparison.
- **Also in yaml:** nc1's falsified branch is encoded as `then: escalate`, so the status `falsified` is lost. Encode it as `falsify` plus a separate escalate.

**B3. Rule D's default route (GitHub comments without the footer) cannot tell the author from an agent.**
- **Where:** §2 Rule D; §6 #15.
- **Evidence, comments:** agents post as `mbilokonsky`.
  - PRs #12 and #13 were created by the Claude app (`performed_via_github_app.slug: claude`).
  - PRs #5 and #11 are agent prose under his login with no footer and `performed_via_github_app: null`. #11's body says "reviewed by Claude before scoring" (agent authorship is my inference from content).
- **Evidence, signed commits:** "`git verify-commit` checks it" also passes on GitHub web-flow signatures. Merge `2a992c3` has committer `GitHub <noreply@github.com>` and `verification.verified: true`, and an agent merging through the API with the session credential gets the same.
- **Replacement Rule D:** "An author decision is a commit whose signature verifies against the author's personal key, fingerprint in `docs/AUTHOR_KEY` (itself committed under that key). Commits whose committer is `GitHub <noreply@github.com>` do not count. GitHub comments do not count while agents post under the author's account."
- **§6 #15:** default "none until signing exists; every DECIDE defaults".

**B4. §8's "check_nodes.py computes conditions 3–5" is false.**
- **Condition 4** (row opened by a node descended from a closed chain): no code.
- **Condition 5** (unit without a `nodes.yaml` entry): no code; the script never reads notes or preregs.
- **Condition 3:** flagged only while the node's status is in LIVE. probe `overrun_then_done_passes` (budget 100, spent 300, status done) gives `errs=[]`.
- **CI never runs it.** CI is `pages.yml`, on push to main, and runs only `check_claims.py` and `test_check_claims.py`. C3's default is "leave", so the decay §10 names as its open risk is the default outcome.
- **Fix text:** "`check_nodes.py` computes condition 3 for nodes that record `spent`. Conditions 4–5 are checked by hand at each §8 review. Unless C3 is applied, no script runs in CI."
- **Code fix:** see C4 below.

**B5. Hop depth is still declared and can be reset. Review finding 3's NC3 scenario still passes.**
- **Where:** `scripts/check_nodes.py` `hops()` and outcome checks; §2 R1 says "never declared".
- **`chain_from.hops` is a free integer.** probe `negative_chain_from`: `hops: -3` under a hop-3 parent gives the node hop 1, funded, `errs=[]`.
- **An outcome `child` is never checked against the child's `parent`.** probe `hop_reset_child_without_parent`: c (hop 3) → child d with `parent: null`, `status: funded` gives d hop 1, `errs=[]`.
- **Fix:** count earlier hops from listed units, and require children to point back.
```python
def _earlier_hops(n, nid, errs):
    cf = n.get("chain_from")
    if cf is None: return 0
    exps = cf.get("experiments") if isinstance(cf, dict) else None
    if not isinstance(exps, list) or not exps or not all(isinstance(x, str) and x.strip() for x in exps):
        errs.append(f"[{nid}]: chain_from.experiments must list the earlier chain's units, one per hop"); return 0
    return len(exps)
# in walk():  base = _earlier_hops(n, nid, errs); p = n.get("parent"); p = p if isinstance(p, str) else None
# in check_file, per outcome:
if ch in nodes and kind not in ("decide", "retire") and nodes[ch].get("parent") != nid:
    errs.append(f"{tag}: child {ch!r} must name {nid!r} as parent, or its hop restarts (R3)")
```
- **Also enforce R1's "new node needs author decision" after acceptance.** Diff ids against `git show <accepted>:<path>`. Ids missing there need `author_decision` that is a commit verified as in B3.

# SHOULD-FIX

**S1. The hop convention is inconsistent between the two `chain_from` entries.**
- The checker's docstring says root = hop 1, so the hop count is the number of units.
- nc1 uses `hops: 5` for six experiments (#12 #13 #14 #15 #17 #19), which counts edges. Under the checker's own convention it should be 6, making NC1 hop 7.
- s1b uses `hops: 1` for one unit (h65), which counts units.
- The doc says S1-b "counted from h53 … R3 needs the author's go". The yaml encodes 1, so s1b is hop 2 with no needs_go, and it lacks `end_state: true`.
- **Fix:** nc1 `chain_from: {experiments: ["#12","#13","#14","#15","#17","#19"]}` and doc "hop 7". s1b `experiments: [h53, h64, h65]` plus `end_state: true`, giving hop 4 and needs_go. (Shame audit chain F is h53 → Q5 → h62a → r2 → h64, `shame_axis_audit.md:108`; h65 extends it.)

**S2. Defaults show as due on an unaccepted plan, and the dates are not tied to acceptance.**
- probe2 with today = 2026-10-30 prints "DEFAULT DUE" for 14 proposed nodes. The yaml headers say "no default executes" until acceptance.
- If the plan is accepted after 10-29, every default fires on acceptance day.
- **Code fix:** `elif by < today and status in LIVE and kind in ("decide","retire") and doc.get("accepted"):`.
- **Header text fix:** "Defaults take effect only after acceptance. Each date is the later of the date shown and acceptance + 14 days."
- Escalation dates (C2, NC1, S1-b, all 10-29) are fixed before the node can run, and `due` never reports them. Use `decide_within_days: 14`, counted from the result commit.

**S3. R4 is violated by the doc itself, and the checker only screens four leading words.**
- **Doc violations:**
  - #17 and §1 item 3 have no date.
  - #16's default "yes" edits CLAUDE.md through silence.
  - C6's default "recorded as still open" is not terminal.
  - #2 and #3 default to "merge", which is not "retire, close or do not fund".
- **Checker:** these defaults all pass `NOT_A_DEFAULT`: "D plus NC1", "merge", "yes", "approve the sweep", "B: fund that program", "keep running" (probe).
- **Doc fix:**
  - #16 default: "no; rows are added under R5 anyway".
  - #17 date: 2026-10-29, default "no".
  - C6 default: "recorded open, with a dated `INSTRUMENTS`-style risk note"; or amend R4's wording.
- **Code fix:**
```python
TERMINAL = {"close","retire","underpowered","withdraw","falsify","narrow","holds"}
if kind in ("decide","retire"):
    hit = [o for o in outs if str(o.get("if","")).strip() == str(d or "").strip()]
    if not hit: errs.append(f"{tag}: default {d!r} is not one of the node's outcomes (R4)")
    elif hit[0].get("then") not in TERMINAL: errs.append(f"{tag}: default {d!r} leads to {hit[0]['then']!r}; defaults are terminal (R4)")
```
- **Yaml edits this needs:** copy the default text verbatim into an outcome `if` for c4, nc2, na1, na2, nb1, nb2, s0, c3, c5 and c6.

**S4. C2's outcome table has a gap and a gate that will probably fire.**
- **Gap:** a treatment interval wholly above 0.8364 matches no branch.
- **Gate:** h47 lost 0% / 24% / 22% (base / shift / random), "deterministically per item" (`WRITEUP.md:70-72`). The >10-point loss gate is therefore expected to fire. The yaml default ("close … keep the caveat") then leaves the claim at `holds` after an unreadable integrity test.
- **Fix text:**
  - "Primary scoring uses pairs (item, target era) whose base, shift and random generations all returned. Loss per arm is reported on all items. Fewer than 24 paired items → unreadable; escalate, default **narrowed** ('integrity rerun unreadable')."
  - Holds: "treatment interval overlapping 0.8364 **or wholly above it**".
  - Narrowed: "'drops' = upper bound < 0.8364".
- **Cost:** three figures disagree.
  - The doc says 250 + "72 stack jobs" + re-reads.
  - The yaml comment says ~400.
  - The commit message says "roughly double".
  - The code: `build_remote_stack(batch_size=4)` runs 9 batched + 9 single jobs per layer, about 36 for 2 layers. Scoring re-reads (180/6 = 30 jobs) are needed with or without the cache.
- **Budget fix:** "≤ 250 jobs with the cache; ≤ 290 without". The yaml budget must cover the no-cache case or be conditional.

**S5. The NC2 yaml does not match the doc.**
- The doc makes only `goal-relative-story-role` conditional on NC1. The yaml makes all four claims conditional.
- NC2's 10-29 default would retire `goal-relative-story-role` before NC1 can run under D+NC1.
- **Fix:** split into nc2a (three claims, 10-29) and nc2b (`goal-relative-story-role`, `parent: nc1-slot-sufficiency`, decided by NC1's result).

**S6. §6 decisions with no node.**
- No node exists for #2 (PR #12), #13, #14, #15, #16, the hooks part of #11, or §7's mechanical hygiene.
- §8.5 and R1 then mean the first unit after acceptance ("make the meter honest") has no node.
- **Fix:** add decide nodes for each (docs/nodes.yaml for #13, #15 and #16) and an infra node `hygiene-meter` per line.

**S7. The S1-b outcome table overlaps and has a gap.**
- **Overlap:** "criteria unmet in both" and "authors disagree in sign" can both be true, mapping to falsify and underpowered.
- **Gap:** one author set meets the criteria and the other does not, with the same sign.
- **Power:** falsify needs no power.
- **Replacement** (first match wins):
  1. Control fails everywhere → underpowered ("axis unfit").
  2. Evaluate only models whose control passes; the rest are unreadable.
  3. Signs disagree in any evaluated model → underpowered ("stimulus-dependent").
  4. All five criteria met in both sets in every evaluated model, and still met after valence adjustment → holds.
  5. Gone after valence adjustment in either set → falsified in that form.
  6. Unmet in both, with ≥80% power for h65's effect size → falsified.
  7. Otherwise → underpowered.

**S8. Default #13 recreates review finding 16.**
- "Use `retired`, reason 'measured, inconclusive'" contradicts `claims_v1.md:28` ("never measured").
- **Fix default:** "amend `claims_v1.md:28` to 'abandoned deliberately, reason on record'; no new status."

**S9. Other checker bugs (probe.py and probe2.py).**
- **Crashes:**
  - `chain_from: "notes/x.md:3"` → AttributeError.
  - `hops: "five"` → ValueError.
  - `budget: 250` → AttributeError.
  - `budget: {ndif_jobs: "~400"}` with spent → TypeError.
  - `spent: {ndif_jobs: "12"}` → TypeError.
  - `decide_by: 2026-10-01 12:00:00` (YAML datetime) → "can't compare datetime.datetime to datetime.date".
  - A node entry that is a string → AttributeError.
  - `nodes:` as a mapping → AttributeError.
  - `outcomes: "see the prereg"` → AttributeError.
  - `parent: [a]` → TypeError (unhashable).
- **False passes:**
  - `budget: {ndif_jobs: 0}` with spent 500, running.
  - No budget on a running test.
  - `{then: continue}` with no child (R2 says "to a named child").
  - `end_state: true` together with a `continue` outcome at hop ≥3.
  - `author_decision: "the author said yes in chat"` on a funded hop-6 node.
  - `accepted: "yes per the author"` is treated as accepted.
  - A test node without `motivated_by`.
  - `check_nodes.py narative` (typo) → OK, exit 0.
  - A line that has `claims.yaml` but no `nodes.yaml` is skipped.
- **Fixes:**
```python
def _date(v):
    if isinstance(v, dt.datetime): return v.date()
    if isinstance(v, dt.date): return v
    try: return dt.date.fromisoformat(str(v))
    except (TypeError, ValueError): return None
def _num(x): return x if isinstance(x,(int,float)) and not isinstance(x,bool) and x >= 0 else None
# top of check_file:
if not isinstance(raw, list): errs.append(f"{tag0}: `nodes` must be a list"); raw = []
# per node: if not isinstance(n, dict): errs.append(...); continue
# outcomes: if not isinstance(outs, list) or not all(isinstance(o, dict) for o in outs): errs.append(...); outs = []
# parent: if p is not None and not isinstance(p, str): errs.append(...); p = None
# budgets:
for k in ("budget","spent"):
    if n.get(k) is not None and not isinstance(n[k], dict): errs.append(f"{tag}: `{k}` must be a mapping")
b = n.get("budget") if isinstance(n.get("budget"), dict) else {}
s = n.get("spent") if isinstance(n.get("spent"), dict) else {}
if kind in ("test","infra","writeup") and not any(_num(b.get(u)) is not None for u in ("ndif_jobs","wall_hours")):
    errs.append(f"{tag}: needs a metered budget (R5)")
for u in ("ndif_jobs","wall_hours"):
    bu, su = _num(b.get(u)), _num(s.get(u))
    for raw_v, nm in ((b.get(u),"budget"),(s.get(u),"spent")):
        if raw_v is not None and _num(raw_v) is None: errs.append(f"{tag}: {nm}.{u} {raw_v!r} is not a number")
    if bu is not None and su is not None and su > OVERRUN*bu and status != "stopped":
        errs.append(f"{tag}: spent {su} {u} vs budget {bu} (>{OVERRUN}x) without stopping (R5, §8.3)")
# R2/R3:
if o.get("then") == "continue" and not o.get("child") and kind not in ("decide","retire"): errs.append(f"{tag}: continue must name its child (R2)")
if kind == "test" and h >= 3 and any(o.get("then") == "continue" for o in outs): errs.append(f"{tag}: hop {h}: an end-state table cannot continue (R3)")
if kind == "test" and not re.match(r".+:\d+", str(n.get("motivated_by") or "")): errs.append(f"{tag}: motivated_by must be note:line (R1)")
# rule D: accepted/author_decision must be a SHA whose `git log -1 --format=%G?|%GF|%cn` is G|<AUTHOR_KEY>|<not GitHub>
# main(): unknown line → return 1; a claims.yaml without nodes.yaml → FAIL (R1)
```

**S10. Non-negotiable 7 in the header.**
- The labelled paraphrase still carries a verbatim quote: "we chase our tail too often" (line 8). That is the quote-inside-a-paraphrase pattern from review 12a and `shame_axis_audit.md:288`.
- **Fix:** "…with planned responses to each finding, because, in his words as paraphrased here, the work chases its tail too often."

**S11. Factual mismatches introduced in v0.2.**
- **(a) §2 R1:** "Every node is `proposed`". `c1-permutation-arm` is `status: done`.
- **(b) §2 R5:** "`claims_v1.md:62-63` is amended to say so". Not amended; the file was last changed at `a069b96` (2026-09-21). Fix: "is to be amended (proposed, not applied)".
- **(c) PROGRAM.md line numbers are off by 3 on this branch.** This commit added a 3-line header to `docs/PROGRAM.md`. `PROGRAM.md:99-100` is now `:102-103`, `:114-115` is now `:117-118`, and §9's `:20-26, :96-120` is now `:23-29, :99-123`. Alternatively, state "line numbers at `2a992c3`".
- **(d) §0:** the link to `../research/narrative/notes/permutation_seed_audit.md` is dead on `program-v2` (it exists only on PR #12's branch). Review finding 11's residue.
- **(e) §4 NC1 R3:** "closes that chain whatever the result" is false for the falsified → escalate branch. Fix: "…unless the author funds a causal node at the falsified branch."
- **(f) NC2 row 1:** "Five designs separated goal-relative role from … and none passed" contradicts itself. Fix: "Five designs **tried to separate** …".
- **(g) §10:** "Rejected: nothing outright". Review 12e's "add a check" for the git author field became a DECIDE with no check. List it under Modified.

**S12. Budgets still in tokens, and the yaml invents budgets the doc lacks.**
- C3, C5, C6 and D are budgeted only in tokens, against R5.
- The yaml gives writeup nodes 6 wall h and `c6-core-paths` 2 wall h; the doc has none of these.
- **Fix:** state metered budgets in §3–§5 and make the yaml mirror them.

# NITS
- **C1 "3.5 SD for the composed arm":** that holds for the 9-combination grids only. `factors_v2` composed is 0.0122/0.0175 ≈ 0.7 SD (note:82, :114-116).
- **"Sat idle for 22 days":** 2026-09-23 22:21Z to 2026-10-15 07:24Z is 21.4 days. The ~2 days of post-h50 work came between v1 being dropped and the idle period.
- **"(overruns of 2.6× and 4.6×)":** these are phase 1 and phase 2 (`method_audit.md:58,64`), not "phases 0–2".
- **"h47's loss was 0 / 24 / 22%":** label the arms (no-patch / treatment / random). The preceding sentence lists them in a different order.
- **The header's "every quote … re-checked (§9)":** §9 omits `firsthop_doubleflip_result.md:23`, `elicitor_calibration_prereg.md:22-24`, `phase2_v1.md:95`, `WRITEUP.md:63-81`, `EXPERIMENTS.md:2174-2176`, `rerun_h29.py:136-137`, `action_interaction_prereg.md:30-31` and `claims_v1.md:28`. It lists the pilot *prereg* `:31-34` where NC1 cites *result* `:31`. I checked all of these and they are correct.
- **S1-b lesson 1** drops the note's "on other data (for example …)" (result:98-99).
- **S1 mermaid** omits the "some models" and "valence" branches.
- **`docs/nodes.yaml` header** says "each is a decision with a default", but `c6-core-paths` is infra.
- **`c1` yaml** has a post-hoc outcome table; mark it `retrospective: true`.
- **nc1 `motivated_by`** has no `:line`.
- **Version name:** the commit says "v2.2", the doc says "v0.2".
- **§7's "agent prose committed as the author (13793be, 5c7ea84)"** is an inference: author field "Mykola Bilokonsky", no trailer. Mark it as inferred.
- **C4's default** drops option (b)'s "in both `WRITEUP.md` and the ledger" (`phase2_v1.md:89-90`).

# Q1: new statements I checked and found correct
- **§0:**
  - the audit tally of 4–5 (the headline says about 4; the table counts 5 including #11's aim);
  - "mostly" deprecated grids; 683k;
  - PR #9 open since 2026-09-23T18:20:48Z;
  - `crossmodel_result.md:88-89`;
  - NDIF job counts recorded;
  - 6 of 10 PRs merged within 86 s (#1 86 s, #2 71 s, #3 28 s, #4 23 s, #5 18 s, #11 86 s);
  - 21 rows share one draw set;
  - the checkout switch was this session's own (reflog checkouts at 07:24 and 07:43).
- **§2:** 13 tests; "NC1 at hop 6" is printed; `EXPERIMENTS.md:1687/1688-1691`; `action_interaction_prereg.md:30-31`.
- **C1** against the note: +0.002, −0.106, most extreme of 64, 2.3/2.9 SD, 256 draws, six rows not re-extracted, random arm, ~50 min.
- **C1a:** 15 Qwen rows.
- **C2:**
  - `a9d34bc` (fetched via the API) passes the prompt string to `mdl.generate`;
  - `e2a3774`'s message quote;
  - `src/lsx/narrative/rerun_h29.py:136-137`, and `--phase stack` runs only after the load;
  - 36 items; `WRITEUP.md:63-81` covers claims 8–10; n = 55/72, 56/72, 36/36.
- **C3/C4/C5/C6:**
  - `test_check_claims.py:105`;
  - `phase2_v1.md` §4 and `:95`;
  - the INSTRUMENTS header;
  - `checks.py:680`, `ledger.py:43`, `reproduce.py:42-44`; no `__main__`; six calibration files.
- **§4:**
  - the GPT-J shallow floor; 64 prompts and +1.126;
  - NC1's +0.0854 at `:31` and its six blocks;
  - 520 jobs (264 route + 264 property activations);
  - NC2 rows and cites (`prequestion:86-91`, `goal_reversal:28-32` and 21/24, `propp:76-79`, `elicitor:22-24`, `firsthop:23`);
  - NA1's `:344-346`, `:283-316` and the theme arm; NA2's h48 quote; NA3's 0/18 since 09-18.
- **§5:** the h65 facts and the PR #9 body; S1-b's five criteria and 200 × 2 Llama at batch 1; no provenance entry for the shame wording.
- **§7:** all nine attribution line cites, `claims_v1.md:28`, −4.12 and Q28, the hook strings.
- **Mismatches** are listed under B4, S1, S4 and S11, plus the nits.

# Q2: review findings 1–20
1. **Partly.** R4 and §6 now carry defaults and dates. Remaining: S2, S3 (#17 has no date; #16, C6, #2 and #3 break R4).
2. **Partly.** The statistic and gate were adopted, but holds has no power condition and overlaps underpowered, and the null and gate are undefined (B2).
3. **Partly.** Nodes are now data, but hops can be declared or reset, rule D can be forged, and §8.4–5 are not computed (B3–B5).
4. **Fixed in prose** (R2 split rule, R3 downgrade and exemption). Not enforced, and the existing holds rows split off failed decisions are not revisited in §7.
5. **Fixed** (S1-c recommended, S2 moved to a charter, §0 row retitled with both scopes).
6. **Partly** (S7).
7. **Fixed, but a new hole** (B1).
8. **Fixed.**
9. **Fixed.**
10. **Partly** (S4).
11. **Partly** (dead link, S11d).
12. **Partly** (header quote S10; rule D forgeable B3; author-field check not added).
13. **Partly** (S12, C2 cost S4).
14. **Fixed.**
15. **Fixed.** #14 has no node (S6).
16. **Partly** (S8).
17. **Fixed.**
18. **Fixed.** Wording S11f.
19. **Fixed**, except (d): product 2 and the writeups have no metered budget (S12).
20. **Fixed**, except the hop convention (S1).

# Q4: trees vs document
- **Dates:** all 2026-10-29; they match.
- **Missing nodes:** S6.
- **NC2 conditionality and ordering:** S5.
- **NC1:** status lost on the falsified branch (B2); hop convention (S1).
- **S1-b:** hops 1 versus the doc's h53 statement, and no `end_state` (S1).
- **C2:**
  - the doc gives its escalations no default; the yaml invents "close … keep the caveat";
  - the yaml budget covers only the with-cache case, and its comment (~400) disagrees with the doc and the code (S4);
  - the yaml drops the doc's "withdrawn and escalate" (it encodes withdraw only).
- **C4 and S0:** their defaults are not among their outcomes.
- **Budgets the doc doesn't have:** writeups 6 h, c6-core-paths 2 h; the doc's C3/C5/C6 token budgets are absent (S12).
- **`docs/nodes.yaml`** holds only C3, C5 and C6. C1, C1a, C2 and C4 live in the narrative tree, although §3 is titled "Shared".
- **c1** is `done`, against "every node is proposed".

# Q6: attribution
Only one unlabelled attribution to the author remains in v0.2: the verbatim quote inside the header's paraphrase (S10). The §7 claim that commits are agent prose should be marked as inferred (nit). Rule D's GitHub route would let agent text count as the author's decisions (B3).