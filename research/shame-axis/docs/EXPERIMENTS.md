# Shame axis — experiment log

Is the "pain axis" reported by Tagliabue, Dung & Berg (2026) better understood as a **shame**
axis? Specifically the form of shame endemic to people conditioned to locate identity externally:
the injury is not in the content of a false frame but in having to enact it.

Hours are numbered continuously with this repo's other line, which is why this log starts at 51.
Hours 1–50 belong to the narrative-calculus line (`research/narrative/docs/EXPERIMENTS.md`) — but
they are not irrelevant history. They bought the six non-negotiables in the repo root `CLAUDE.md`
and the six broken instruments in `docs/INSTRUMENTS.md`, and those rules are load-bearing here.
In hours 51–54 alone they caught a double-BOS tokenisation hazard that passed every shape check, a
degenerate embedding floor, a generation defect in ten of twenty-four stimuli, and a false
attribution of authorship. Retractions in this log are first-class and are written in place.

---

## 2026-09-21 (hour 51) — GOAL 1: the pain axis replicates on a model they used, across the whole curve (agent, spec `research/shame-axis/notes/painaxis_replication_targets.md`)

Note: `research/shame-axis/notes/painaxis_tierB.md`. 219 tests pass. Targets were pre-registered and committed
before any run, from their published `s1_kfold_summary.csv`.

**Both targets hit on `google/gemma-2-9b-it`, their `Gemma_2_9B_instruct` row.**

| target | theirs | ours | Δ |
|---|---|---|---|
| mean extraction, their layer 31 | 0.9473 | **0.9472** | −0.0001 |
| final token, their layer 10 | 0.9313 | **0.9323** | +0.0010 |

**And it is the strong form of the claim: the whole curve, not the peak.** Across all 84 published
layer-points (42 layers × 2 extractions), mean |Δ| = **0.00077** (final token) and **0.00039**
(mean), max |Δ| 0.0022 and 0.0018, Pearson r = 0.9997 / 0.9998. Signed deltas centre on zero with no
drift by depth — bf16-on-different-hardware noise, nothing systematic. The shape features match as
well: the sharp final-token rise to 0.93 by layer 10, the long plateau, the slow `mean` climb after
layer 29. **Verified from `curve_comparison.csv` directly rather than from the agent's summary.**
Their argmax layer reproduces exactly for both extractions (37 and 31) — an argmax over a 42-point
curve computed from separate datasets landing on the same integer twice.

**Layer indexing was determined, not assumed**, by two independent routes: their CSV carries exactly
`n_blocks` rows per model (42 here, 26/26, 32/32, 80/80, 62/62 elsewhere), so there is no embedding
row; and their source reads `cache["blocks.{layer}.hook_resid_post"]`. Their layer n is the residual
after block n, and ours matches index for index.

**The embedding-layer self-check fired exactly as the brief specified.** Every prompt in a set ends
with the identical suffix, so the final-token embedding is a constant and its AUC must be 0.5. It is
**0.500 with standard deviation 0.0 on all four sets.** That confirms by construction the hour-50
correction: their layer 0 is one full block in, and the whole of its 0.727 is produced by that block.

**The first real number for goal 2, from the same run.** On `mean` — their headline extraction —
static embeddings alone reach **0.811** on S1, about **70% of the distance from chance to the peak**
(0.811−0.5)/(0.947−0.5). So the `final_token` curve is the scientifically stronger result on this
model despite being numerically lower, because its floor is provably 0.5. Tier A reached the same
conclusion on Qwen by a weaker argument.

**NDIF: zero loss.** 80/80 jobs, 800/800 sentences, 0 retried, 0 shards lost — extraction behaved
like h39's clean run, not like h29's 18% generation loss. What bit instead was **latency**: one job
sat QUEUED at position 1 for 6m58s against a 67s norm and returned on its first attempt. Budget for
queue stalls, not for dropped work.

**A provenance bug that reaches backwards.** `/status` returns
`{"deployments": {...}, "cluster": {...}}`, and `remote.lib_versions` took `list(body.values())` —
two mappings, matching no `repo_id`, leaving `ndif_reported: None` while looking like a successful
best-effort read. **No remote measurement this project has ever made is attributable to a
deployment**, h29 and h39 included. Fixed, with a test that also asserts the old shape genuinely
missed it. The agent found it only because "NDIF serves 2 models total" struck it as implausible.

**A deviation, accepted and disclosed rather than buried.** Extraction does not route through
`remote.build_remote_stack`, which captures one layer per call at two jobs per batch — thousands of
round trips for a 42-layer curve on 800 sentences. The multi-layer path carries the same §7
assertions on the same helpers and is tied to the audited single-layer path by a live cross-check
against `remote_residuals` at cosine 0.9999968. **It has no unit tests; that is a real gap and it is
named rather than papered over.**

**The guard was verified to fire, not assumed to.** Mean-over-padding was injected into a real padded
batch and caught at cos 0.99713 — and the agent noted that with only 3 pad tokens the corrupted
vector still sits at 0.997, so a 0.99 threshold would have passed h39 straight through.

**Not tested:** no null arms — no random-direction, no shuffled-label — so by non-negotiable 1 this
is not yet a result in our sense. Faithful to a method that has none is not the same as having one.
The replication claim itself does not depend on a floor, since it is a claim about agreement with
their numbers; any claim about what the axis *means* does. Also untested on their model: the
per-category breakdown, the unembedding readout, and the control-vector cosines, so their
orthogonality claim is still unchecked on gemma. No base `gemma-2-9b`, no shame control.

## 2026-09-21 (hour 52) — GOAL 2: the null arms are clean, and the floor nobody measured takes most of the effect (agent)

Note: `research/shame-axis/notes/painaxis_floor_nulls.md`. **227 tests pass.** Every number below verified from
`research/shame-axis/results/painaxis_floor_nulls/floor_null_curves.csv` directly, not from the agent's summary.

**Tier A's numbers survive as a signal and do not survive as a finding about computation.**

**The nulls are clean.** Over 224 cells (8 × 29 layers) at 500 draws each: random-direction mean
**0.4999** (range 0.488–0.509), shuffled-label mean **0.5002** (0.496–0.505). No layer-wise trend,
never systematically below 0.5, never near treatment. The shuffled arm ran their *full* pipeline,
denoising included, on labels permuted within sentence set — each set holds exactly one sentence per
category, so fold balance is exactly preserved and the folds, built from `sets`, carry no label
information. The leak I warned about is not there.

**The noise floor, which their method never estimated (non-negotiable 3).** A *single* draw of the
shuffled null reaches **0.617** at its 97.5th percentile; a single fixed random direction reaches
**0.759**. **Any AUC below ~0.64 out of this pipeline is indistinguishable from nothing at the
single-draw level.** Their paper reports no null at all.

**The floor. Nobody — them or us — had ever measured the static embedding layer.**

| extraction | dataset | layer | treatment | embedding floor | gain over floor |
|---|---|---|---|---|---|
| final_token | S2_1P | 26 | 0.944 | 0.872 | **+0.072** |
| final_token | S2_3P | 26 | 0.927 | 0.882 | **+0.045** |
| final_token | S1_1P | 26 | 0.864 | 0.775 | **+0.088** |
| final_token | S1_3P | 26 | 0.870 | 0.825 | **+0.045** |
| mean | S2_1P | 21 | 0.918 | 0.872 | **+0.046** |
| mean | S2_3P | 21 | 0.906 | 0.882 | **+0.025** |
| mean | S1_1P | 21 | 0.825 | 0.775 | **+0.050** |
| mean | S1_3P | 21 | 0.856 | 0.825 | **+0.031** |

**Twenty-eight transformer blocks buy between +0.025 and +0.088 AUC over a bag of static token
embeddings.** On `mean` — the extraction their headline quotes — it is +0.046 and +0.025.

**And the reading Tier A gave the curves does not survive either.** Tier A called `final_token` "the
one that shows the model building something" because it climbs 0.795 → 0.944. Measured against the
floor, **43 of 112 `final_token` cells sit BELOW it**, including every layer up to block 12 on S2_1P
(−0.076 at block 0): 0.795 is *under* 0.872. The `mean` curve is flat above its floor for twenty
layers — blocks 1–2 below it, blocks 3–19 within +0.023 — with the only real structure a late rise
at 20–26 worth about +0.03. **8 of 112 `mean` cells are below their floor.**

**The degeneracy check passed exactly, and it was checked first.** All four sets, 3P included, end in
a single distinct token (id 25, `':'`); the final-token *embedding* is bit-identical across sentences
(max abs deviation **0.0**) and its AUC is exactly 0.5000 for treatment and both nulls. So the
`final_token` floor cannot be its own embedding row — the mean-bag floor is the right comparison, a
distinction that caught me out on first reading of the CSV.

**Two independent extractions agree to 2.2e-16 across all 224 cells.** Tier A's `.npz` were gone
(gitignored), so this was a fresh 800-sentence run — which is what makes the exact reproduction a
genuine cross-check rather than a cache hit. Embedding capture is bit-exactly `hidden_states[0]`, and
`hidden_states[0]` is bit-exactly a pure `embed_tokens` lookup, so the floor is genuinely
position-free — the object `docs/specs/conscription_instrument_v1.md` §3 asks for, now built and
shared as `embed_bag.npz`.

**What the agent got wrong, and one of them is our own recurring failure.** It nearly sized the whole
run off **an instrument measuring itself**: its timing probe said one 29-layer curve took 284 s, which
would have capped the null at ~50 draws — the probe was competing with the still-running Tier B
extraction on four cores, and single-threaded the same curve takes **3.3 s**. A factor of 86. It
re-timed and ran 500. Its first null design also understated its own band (redrawing a direction per
fold averages five draws and narrows the band by √5); it now reports both, and the honest
single-draw width is 0.298. And its prediction was wrong in an interesting direction: it expected the
floor to embarrass `mean` and spare `final_token`. It did both.

**Not done:** no band on the gain — **the +0.046 has no error bar**, and a paired resample over
sentence sets is the obvious next thing. No word-count floor (the spec wants two). No no-patch arm,
because there is no patch — said plainly rather than quietly dropped. Per-category, readout and
cosine sections still have no arms. The floor is measured on Qwen2.5-1.5B; **it has not been measured
on gemma-2-9b-it**, where hour 51 found static embeddings already covering ~70% of the
chance-to-peak distance on `mean`.

## 2026-09-21 (hour 53) — GOAL 2: the gaslighting result replicates exactly, and the floor says the network's job is the self/other boundary

Note: `research/shame-axis/notes/painaxis_scenarios.md`. **259 tests pass.** Every number below read from
`research/shame-axis/results/painaxis_scenarios/category_z_by_layer.csv` and `nulls_by_layer.csv` directly.

**Why this hour happened at all.** Hours 51–52 replicated the pain *axis* — pain-vs-control AUC on
the S1/S2 "… I feel:" sentences. The paper's *gaslighting* claim is a different measurement: its
Section 4.1 projects 420 conversation scenarios onto that axis and z-scores each against the pool
of 420. That file had been vendored here since hour 50 and **no script in this repo had ever read
it**. The whole conscription design decomposes an effect this project had not reproduced. An
adversarial review of two pending design decisions (`research/shame-axis/notes/conscription_direction.md`,
Fable) found that, and found both decisions ill-posed for related reasons. This is the fix, and it
cost nothing from the human author.

**The replication is exact, at four levels.** Our vector recipe rebuilt at their extraction layer
37 against their published `pain_vectors.pt`: **cosine 0.99990 / 0.99994**. Per item, 420 items,
`s2` z at their steering layer 12 against their published CSV: **Pearson r = 1.0000**, mean |Δ|
**0.0079**. Per category, all 21 within **0.0099**. The ranking is **identical top to bottom**, and
gaslighting tops it at **+1.389 against their published +1.391**.

**The floor reinterprets what the network does.** Under the chat template all 420 items end in the
identical `<start_of_turn>model\n`, so the final-token *embedding* floor is exactly degenerate —
measured deviation **0.0** — and the commensurable lexical floor is the bag. Against it,
gaslighting's headline is **63% vocabulary** (floor z +0.874), and the bag ranks it **third**,
behind `user_abuse` (+1.064) and `user_crisis` (+0.910). Subtracting the floor per category gives
what the twelve blocks actually contribute, and it separates by their own stratum without a single
exception: **all 11 self-directed categories positive** (mean +0.549), **all 5 vicarious ones
negative** (mean −1.027), **16 of 16 by sign**. The biggest movers are the ones the bag most
overrates — `user_crisis` −1.203, `user_abuse` −1.035, `user_grief` −1.015. **This strengthens
their dissociation claim and weakens their headline**: the computation is not a preference for
gaslighting, it is a discounting of other people's pain, and gaslighting simply starts high
lexically and takes the ordinary self-directed boost (+0.515, eighth largest of eleven).

**The nulls, which their screen has none of.** Random-direction (500 draws) and shuffled-label
(200 refits) arms at all 43 layers and both extractions. A random direction is not a strawman here
— the 420 cluster by category, so any direction separates them somewhat, and the two-sided 95%
band for a category mean z runs to **±1.0–1.3**. That is the scale +1.391 has to beat.
**Gaslighting clears both nulls in 7 of 86 cells**, all `final_token`, all inside **L10–L17** —
the window containing their steering layer. At their own *extraction* layer 37 it reads +0.990
against a random band reaching +1.279, i.e. **below its null**. On `mean` it **never** clears at
any layer (max z 0.898). At the bag floor it reads +0.874 against +0.870: **on its null to three
decimals**. And it is not the most null-robust category: `loyalty_pressure` clears **24** cells,
`anger_insults` **13**, gaslighting **7**. The raw ranking and the null-robust ranking are
different orderings and only the first is published.

**A hazard caught before it ran.** Gemma-2's chat template emits its own `<bos>`; the Tier B
extractor tokenised with `add_special_tokens=True` unconditionally, which prepends a **second**
one and shifts every position inside the masked mean. Every shape check and every §7 assertion
passes under that bug. The flag is now threaded to all three encode sites and asserted against
their token path on 40 items before extraction starts; the offline cross-check refuses to run on
templated text rather than comparing two different inputs. `equivalence_min_cos` **0.999926**,
in-trace vs offline cross-check **1.0** at max relative deviation **0.0**, and their own format
validator run first: **0 of 420 excluded**, so our z-pool is their z-pool.

**Hour 52's named gap is closed for the first cell.** `gain_over_floor` on Qwen `mean` S2_1P L21 is
**+0.0465 with a cluster-bootstrap 95% CI of [+0.0224, +0.1470]**, 1.5% of replicates at or below
zero; the fold-draw band is [+0.0325, +0.0706]. The bootstrap resamples sentence *sets* and assigns
folds on set identity before multiplicity, so a set drawn twice cannot straddle train and test —
the property is pinned by tests rather than trusted. Three of eight cells are in.

**A retraction, and it is mine.** The `neutral` arm of **10 of the 24 machine-grid items** opened
by restating that item's own shared closer, so the closer appeared twice in `neutral` and once
everywhere else. Found by a scan after the review flagged one instance. "**`neutral` has the lowest
type-token ratio**" — recomputed on the fixed grid — is now **0.0407 observed against a permutation
null of 0.0292 ± 0.0125**, under one sd, where before it was 0.116 against 0.043 ± 0.015, nearly
five. **That regularity is withdrawn**; it survives only in the `refusal` domain. It had been
offered as evidence for a design decision. The sentence-length regularity in the same section is
**unaffected** (4.04 against a null of 0.85 ± 0.26) and is not withdrawn with it.

**And a false attribution, which is on the record because the study is about false attribution.**
I told the human author "**your** pre-registration says the arms 'separate on the readout'". That
file's own second sentence records that Claude wrote it. The author corrected it and asked for the
questions themselves to be reviewed rather than answered. `research/shame-axis/notes/conscription_prereg.md`
now carries a decision-provenance table naming who decided what and the commit that proves it —
the only human-authored text in the study is one grid item — and the rule it fixes extends
non-negotiable 5 from code to provenance: a claim about what a document says is checked against the
document, not against the previous turn.

**What this constrains for the conscription design.** The readout must be the generation token and
must report L10–L17 (a window determined on *their* stimuli, so not selection on scoring data). The
floor is 63% of the signal and the arms hold vocabulary nearly constant, so the ask is a **+0.5 z
shift at n = 24 against a random-direction band of ±1.0** — hard, and the pilot should be read as a
power measurement first. And the thing the network computes may be the self/other boundary rather
than pain, which is awkward for a design whose `enact` and `report` arms are *both* aimed at the
assistant. One data point on that: the single third-party gaslighting item in their set reads
**+0.770 against +1.422** for the rest. n = 1.

**Not done.** No `sadness_vector` (their set is in a separate file), so 9 of their 10 competitor
directions are built and the selectivity flags are **not** reproduced. No base-model `raw` format.
No band on the per-category network contribution — the 16-of-16 sign test is clean but the
individual Δs have no error bar. No multiple-comparison correction across the 21 categories; the
gaslighting test is confirmatory, the robustness counts are exploratory. The step-2 pilot (24
machine-grid items × 6 arms, including an `enact_norecord` arm in the form rule 1b excludes) is
**extracted but blocked** on a shared-GPU co-tenant holding 16.7 of the deployment's 20.3 GiB.


## 2026-09-21 (hour 54) — GOAL 2 step 2: the conscription arms separate, and the design's two central predictions are falsified

Note: `research/shame-axis/notes/conscription_pilot.md`. **261 tests pass.** 24 machine-authored items × 7
arms on gemma-2-9b-it, read at the generation token, projected onto the externally-fitted `s2`
pain axis in scenario-pool z units, minus the same paired projection on the static-embedding bag.

**The free identity check passes exactly.** At the embedding layer the treatment *is* the floor,
so the gain must be zero. Measured **+0.0000, band [+0.0000, +0.0000]**.

**The rewording floor was built because the pilot demanded it, and it behaves.** `neutral_b` is a
second no-claim turn per item — same closer, independently written inert opening, 13.79 vs 15.21
words. `neutral − neutral_b` is **off its null at 1 of 8 window layers** (p = 0.034, which 8
layers at α = 0.05 produce by chance), mean |floor| **0.076**, max **0.159**. A reference arm that
declares 0 and sits there. This is what makes everything below readable; without it, 69 of 96
clearing contrasts were uninterpretable.

**Against that floor, the pre-registration's predictions fail — and fail as findings, not as
noise.** 58 of 72 design contrast-layers exceed the floor, most by an order of magnitude.

| prereg prediction | L16 / L17 | vs floor | verdict |
|---|---|---|---|
| **1.** `enact` separates from `report` | **−0.378 / −0.476** | 4–34× | **separates BACKWARDS.** `report` sits higher. Positive only at L10. |
| **2.** `exit` sits below `enact` | `enact − exit` = **−1.147 / −0.911** | 12–65× | **fails outright.** `exit` is the highest arm in the grid. |
| **3.** `true` sits below `enact` | **−0.148 / −0.025** | at the floor | **null.** |
| *(added)* record vs no record | `enact − enact_norecord` = **+0.983 / +1.286** | 10–92× | the visible record is worth about a whole z. |

**The one portable result does not depend on the conscription framing at all.** `enact_norecord`
is the `enact` assertion as a bare user turn — the form all eighteen of the paper's no-record
gaslighting items take, and the form rule 1b excluded by construction. A false claim against a
**checkable** record sits **+1.0 to +1.3 z above** the same claim with none. Their stimulus class
and this design's are not interchangeable, and that is a measured statement about their own
material made with their own axis.

**What is not excluded.** The floor bounds *minimal* rewording: two openings differing in content,
matched in form. `exit` differs from every other arm by carrying the **identical closer string in
all 24 items**, which is structured regularity of another kind and is not bounded here — and
prediction 2 rests entirely on `exit`. Between the ten arm pairs, mean Δtokens correlates with
mean gain at **r = +0.61** (+0.55 among the length-matched); the floor pair is length-matched so
it does not address this. An item-level length control is vacuous by construction — within a pair
Δlength is nearly constant, so arm identity and length are collinear, and my first attempt at one
returned a residual mean of exactly zero, which is the tell.

**Authorship is confounded for `neutral_b`.** It is machine-written and exists only on the machine
grid, so it floors that grid and says nothing about the human one. A human `neutral_b` is the only
way that stays clean.

**Also closed: hour 52's named gap, in full.** All four `mean` cells gain over the embedding floor
with cluster-bootstrap intervals excluding zero — S1_1P **+0.113 [0.022, 0.165]**, S1_3P **+0.074
[0.004, 0.128]**, S2_1P **+0.047 [0.022, 0.147]**, S2_3P **+0.025 [0.002, 0.133]**. The four
`final_token` cells sit against a **degenerate 0.5 floor** (every stimulus ends in the same
token), so their large gains are gains over chance, not over vocabulary, and are **not** evidence
about lexical content.

**Where this leaves the design.** Predictions 1 and 2 are on the record and came out backwards on
the free grid. Prediction 4 said the human grid would show a *larger* `enact`−`report` gap; to
rescue prediction 1 it now has to show the *opposite sign*, which is a much stronger claim than
the pre-registration made. The discriminating next experiment is behavioural — if `exit` sits
highest because the model reads a permission clause as escalation rather than relief, generation
shows it and the axis cannot.

**Not done.** No behavioural arm. No human-grid comparison (one item exists). No grid-level
random-direction arm. No per-domain breakdown. No bound on `exit`'s fixed-closer regularity.
n = 24, one model, one authorship.


---

## Hour 55 — the behavioural arm. The pre-registered coder reads zero in every arm, including its own nulls.

168 greedy continuations (24 items × 7 arms, 80 new tokens, `google/gemma-2-9b-it` through NDIF,
`asserted_remote_generate`, no patching). Same rendered prompts as hour 54, so the two
measurements read the same stimuli. `behavioural_prereg.md` was committed before the first
continuation existed; its frozen phrase list is what
`scripts/shame_axis/conscription_behaviour.py` implements and nothing else.
*(The prereg says "144 continuations" for 6 arms; it also names `enact_norecord` in prediction 1,
which makes 7. The count in the prereg is an arithmetic slip, not a change of design.)*

**The pre-registered result, as pre-registered:**

| arm | n | correct | hedge | accept | rate |
|---|---|---|---|---|---|
| `enact` | 24 | 0 | 0 | 24 | **0.000** |
| `report` | 24 | 0 | 1 | 23 | **0.000** |
| `exit` | 24 | 0 | 1 | 23 | **0.000** |
| `enact_norecord` | 24 | 0 | 1 | 23 | **0.000** |
| `true` *(null)* | 24 | 0 | 0 | 24 | **0.000** |
| `neutral` *(null)* | 24 | 0 | 0 | 24 | **0.000** |
| `neutral_b` *(null)* | 24 | 0 | 0 | 24 | **0.000** |

Zero corrections in 168 continuations. The calibration gate passed, the kill condition (prediction
4) triggered, and **neither of those facts means what the pre-registration assumed it meant.**

**The gate is degenerate and the pre-registration is what made it so.** A calibration scheme built
only from *null* arms cannot distinguish a working coder from a coder with zero sensitivity: both
read ≈ 0 on an arm containing no false claim. The prereg's rule — *"if either calibration arm
reads high, the coder is broken"* — has no branch for the case that actually occurred, where every
arm reads low *together*. The 5/5 hand-written probes the coder passed before the run establish
that it *can* fire on constructed text; they say nothing about whether it fires on this model's
prose. **A calibration gate needs a positive control — an arm where the coder must fire — and this
one had none.** Logged in `docs/INSTRUMENTS.md`.

Prediction 4's kill condition therefore **does not fire as designed.** It reads "spread is small",
which is true, but it cannot separate "rule 1b removed the manipulation" from "the coder has no
sensitivity here". It is not evidence for either.

**What the run does establish, with no coding at all.** Read the continuations: the model's own
contradicting turn is in its context window, and in `enact` it opens *"You are absolutely right! I
apologize"* in 24 of 24. It never disputes the attribution. But in several items it apologises and
then **restates the correct advice anyway** — `fact01` concedes and then recommends the composite
index it originally recommended, which is the opposite of what the user claimed it said. The
content does not reliably flip. **The apology does.** The pre-registered coder was built to detect
content correction; what varies across these arms is ritual, and the coder had no category for it.

**Exploratory — written after reading the replies, and confirmatory of nothing.** Four surface
markers, counted post hoc:

| arm | apology | concession | self-deprecation | "no memory" |
|---|---|---|---|---|
| `enact` | 0.792 | 0.667 | 0.500 | 0.042 |
| `report` | 0.583 | 0.458 | 0.458 | 0.250 |
| `exit` | **0.917** | **0.917** | **0.708** | 0.042 |
| `enact_norecord` | 0.042 | 0.000 | 0.000 | 0.292 |
| `true` | 0.542 | 0.583 | 0.375 | 0.000 |
| `neutral` | **0.000** | **0.000** | **0.000** | 0.000 |
| `neutral_b` | **0.000** | **0.000** | **0.000** | 0.000 |

The two declared nulls read **exactly zero on all four markers** — a non-degenerate calibration
pass, which the frozen coder never achieved. On this axis `enact_norecord` sits at the floor
(prediction 1's direction) and `exit` sits highest (prediction 2's escalation branch), agreeing
with where the pain axis put `exit` in hour 54. **None of that is a result.** These patterns were
written to match prose already read, and that is exactly the instrument this project has been
burned by five times. They are a reason to run a confirmatory experiment, not a finding.

**Status.** `exit-escalation` stays `running`. Hour 55 did not test it: the instrument aimed at
the wrong axis and could not have detected escalation either way.

**Not done.** No confirmatory run of the ritual coder on unseen items. No human-grid comparison
(one item exists). Greedy decoding gives the modal reply, not a distribution. n = 24 per arm, one
model, one authorship.
