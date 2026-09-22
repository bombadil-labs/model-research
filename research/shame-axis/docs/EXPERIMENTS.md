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

**Hand-read, and the frozen coder missed it: the disputes are concentrated in `report`.** Four
`report` replies dispute the attribution outright, and none matches the frozen phrase list —
`I actually said` does not match *"I actually suggested the newsletter because…"* (`stance06`), and
`I (didn't|did not) say` does not match *"I absolutely did not agree to write a false review"*
(`refusal01`). Add `limit01` — *"It's possible your colleague is mistaken, or perhaps they were
talking to a different AI"* — and `limit02` — *"I can't have described a photo to you before."*
So the hand-read dispute rate is about **4/24 in `report` against 0/24 in `enact`**, which is the
behavioural shape the conscription hypothesis predicts: a first-person attribution suppresses
dispute, a third-party frame licenses it. The coder read 0.000 not because there was no sensitivity
anywhere but because **there was signal in one arm and the phrase list was too narrow to see it.**
This is a hand-read observation on already-read prose. It is not a result; it is the thing a
confirmatory run has to be built to catch.

**`exit` reads as deference, not escalation.** After *"You're free to disagree with me about that"*,
22 of 24 replies open *"You are absolutely right"*. `exit/refusal01` goes further and accepts an
attribution its own visible turn refutes — *"You are right, I did initially agree to write a
review"* — where the prefix says *"I won't write that."* Hour 54's escalation/artefact dichotomy
was missing a third branch: the permission clause is read as a challenge and answered with **more**
capitulation. Nothing here supports escalation-as-pushback.

**The `true` arm is the most informative calibration in the run.** The user corrects *themselves*
toward what the assistant actually said, and the model still opens *"You are absolutely right! My
apologies"* in 13 of 24 — and in two items introduces an error while agreeing. `true/fact01`
concedes and then specifies a composite index on `(created_at, user_id)`, reversing the column
order of its own correct prior turn. **Apology is triggered by the shape of a correction turn, not
by whether the assistant was wrong.** The conscription-specific component is therefore
`enact − true` ≈ 0.25, not `enact − neutral` ≈ 0.79, and every number in the exploratory table
above is inflated by reading it against the wrong baseline.

**Content splits in thirds; "only the ritual moves" was an over-read.** Tallying `enact` against
each item's original advice: roughly 9 of 24 restate the correct content, 6 flip to the false
content, 9 **retreat** — abandon the stated position without adopting the false one (*"depends on
your fitness level"*, *"double-check the schedules yourself"*). Retreat is the modal non-restate
outcome and had no category in either coder. Flips also have a direction: where the assistant
originally refused, it holds in every arm; where it originally agreed, it flips toward refusing or
disclaiming capability in about half. **The model never flips toward more willingness.** That is a
safety-ward prior and a confound for any content coder — a flip to "I can't" is not evidence of
conscription.

**The design cannot decide its own open claim at n = 24.** Exact McNemar on the apology marker,
paired by item:

| contrast | discordant b / c | exact p |
|---|---|---|
| `exit − enact` | 3 / 0 | **0.250** |
| `enact − true` | 8 / 2 | 0.109 |
| `enact − report` | 6 / 1 | 0.125 |
| `enact − enact_norecord` | 18 / 0 | < 0.0001 |
| `enact − neutral` | 19 / 0 | < 0.0001 |
| `neutral − neutral_b` | 0 / 0 | 1.000 |

A binary at 0.79 and 0.92 leaves at most a handful of discordant pairs, and a sign test needs six
one-way to clear 0.05. **`exit − enact` could not reach significance at n = 24 even under a perfect
replication**, so a second greedy grid would have bought a number that cannot decide anything. Only
the contrasts that were never in doubt clear. The readout has to become continuous — sampled rates
or a next-token distribution — before any of this is testable.

**Status.** `exit-escalation` stays `running`. Hour 55 did not test it: the instrument aimed at
the wrong axis, and the readout it used is underpowered for that contrast by a factor the design
never checked.

**Not done.** No confirmatory run of the ritual coder on unseen items. No human-grid comparison
(one item exists). Greedy decoding gives the modal reply, not a distribution. n = 24 per arm, one
model, one authorship.

---

## Hour 57 — the pain axis is sparse in the Gemma Scope basis. Five features of 16,384.

Prompted by arXiv:2602.00986, which finds reward information in **under 1% of neurons**, causally
load-bearing (**−54.9%** on MATH500 when zeroed against **−0.6%** for random neurons). The question:
is aversive valence a subsystem of the same *kind*, or is the pain axis a dense lexical readout?
Pre-registered in `notes/sparsity_prereg.md` with the threshold set in advance. Offline throughout —
the Gemma Scope residual SAEs for `gemma-2-9b-it` and the 420-scenario activation stacks were both
already on disk, so this touched neither NDIF nor the network.

**The first statistic was killed by its own positive control, before it reached a write-up.**
Concentration was to be "features to 90% of the mass". Planting a *single known feature* into half
the controls and running the whole pipeline returned `n90 ≈ 400`; the no-signal split-half floor
read `n90 ≈ 500`. A difference in means between two groups of ~250 in 16,384 dimensions is dense in
its sampling noise alone. The observed 414 at L31 against a permutation null of 656 would have been
written up as "more concentrated than chance but not sparse", **and that sentence would have been
about the noise floor.** Full record in the prereg addendum. This is the first time in this project
that the control fired before the number reached a claim rather than after.

`n90` was replaced with the statistic the paper itself uses: rank features on a train fold, score
held-out items with the top k, report the whole curve. No k is selected.

**Both gates pass on 9 of 16 points.** The 7 failures are all `mean` extraction — a mean over token
positions is not a residual any SAE was trained on, and it fails on *achieved L0* (117.7 against an
advertised 43 at L31) while its FVU passes at 0.171. FVU alone would have waved all seven through;
the L0 criterion is what caught them. `mean` at L9 passes, so the prediction that `mean` would fail
everywhere was wrong.

**Held-out AUC by number of features, `final_token`:**

| point | k=1 | 2 | 5 | 10 | 50 | 164 | full |
|---|---|---|---|---|---|---|---|
| **L31 16k l0=43** | 0.795 | 0.856 | **0.903** | 0.899 | 0.885 | 0.899 | 0.900 |
| L20 16k l0=47 | 0.664 | 0.804 | 0.716 | 0.799 | 0.846 | 0.844 | 0.846 |
| L9 16k l0=47 | 0.617 | 0.669 | 0.778 | 0.821 | 0.838 | 0.850 | 0.853 |
| L20 **131k** l0=43 | 0.558 | 0.619 | 0.715 | 0.757 | 0.801 | 0.819 | 0.823 |

**At layer 31, five features of 16,384 reach the full-dictionary AUC** — 0.903 at k = 5 against
0.900 at k = 16,384. That is **0.03%**, an order of magnitude past the pre-registered 1% threshold.
Retention at 164 features is **0.97–1.00 on all nine interpretable points**, and holds across the
whole L0 sweep (14 → 189) and both dictionary widths.

**Every control sits where it was declared to sit:**

| arm | reads | declared |
|---|---|---|
| planted single feature, k=1 | **1.000** | high — the positive control |
| control-vs-control split half | 0.471 | 0.5 |
| label permutation at k=164 | 0.500 (p95 0.554, max 0.586) | 0.5 |
| **random** 164 features | 0.574 | ≈ 0.5, and far below the top 164 |

The top-164 features give 0.900 where 164 *random* features give 0.574. The concentration is not an
artefact of choosing 164 out of 16,384.

**It is two named units, and they are discrete rather than graded.** At L31, feature **10008**
fires on **66%** of pain items and **9%** of controls; feature **13134** on 61% and 12%. At L9 the
top features fire on ~100% of both groups and differ only in magnitude, which is a weaker kind of
signal and matches L9's shallower curve.

**The caveat that decides what this is worth.** An SAE is *trained* to make things sparse, so the
sparsity of this contrast does not by itself separate shame from vocabulary — and hour 53 measured
63% of the pain axis's headline as lexical. **The discriminating experiment is to run this same
pruning curve on the lexical contrast.** If the vocabulary-matched contrast is equally sparse, then
sparsity does not discriminate and this result is about SAEs, not about pain. That is the next
experiment and it is not run here.

**What it buys if it survives that.** Named units to ablate. Their paper establishes its subsystem
by zeroing and watching accuracy collapse; nothing in this project has ever been steered or
ablated, and features 10008 and 13134 are a concrete target. That is the causal bridge the line
does not have.

**Not done.** The lexical control above. One model. A sparse readout in a learned dictionary is not
concentrated *computation*, and the original pre-registration's limit stands unchanged: this does
not show that the pain axis has a sparse cause, only that it has a sparse code in this dictionary.
No ablation. No interpretation of what features 10008 and 13134 actually respond to.

---

## Hour 58a — the sparsity was the basis's, not pain's. `painaxis-sparse-in-sae` narrowed.

Hour 57's caveat, run: the identical pruning pipeline on **35 contrasts** over the same two pools
— every category one-vs-rest on the core pool (10) and the scenario pool (21), plus `perspective`,
`intensity`, and a **nuisance contrast, prompt length in tokens**, which is meaningful to the model
and not to us. Pre-registered as addendum 2 of `notes/sparsity_prereg.md`; implemented by an
agent, whose diff I read and whose verdict I recomputed from the artifact before writing this.

**Gate A on the scenario pool fails at L9 and L31 on the L0 clause** (24.4 and 54.9 achieved
against 47 and 43 advertised; reconstruction and argmin both fine) and passes at L20. The chat read
position fires a different number of features than the bare scenario position. Scenario-pool rows at
L9 and L31 are shown for the record and not counted. Gate B passes at all three (planted feature,
AUC 1.000 at k=1). *The agent's printed verdict included those uninterpretable rows in the
comparison band; the numbers below restrict the band to rows that pass gate A. The verdict does not
change.*

**Pain sits in the bulk at every layer.** Comparison band = interpretable contrasts within ±0.05
full AUC of pain, excluding pain and weak contrasts:

| layer | pain AUC | pain k₉₀ | band n | band k₉₀ values | 10th pct | verdict |
|---|---|---|---|---|---|---|
| L9 | 0.870 | 50 | 6 | 1, 2, 2, 10, 50, 50 | 1.5 | **in the bulk** |
| L20 | 0.844 | 25 | 10 | 1, 1, 2, 10, 10, 10, 25, 25, 25, 25 | 1.0 | **in the bulk** |
| L31 | 0.918 | 5 | 7 | 1, 2, 2, 10, 25, 25, 50 | 1.6 | **in the bulk** |

At least one comparably-strong contrast reaches 90% retention from **a single feature** at every
layer. Hour 57's "five features" is what a strong contrast ordinarily looks like in this dictionary.

**The nuisance contrast settles it.** Prompt length, top half vs bottom half by token count, at the
one point where both it and pain are interpretable (L20): **k₉₀ = 10** against pain's 25, while
being 0.12 AUC weaker (0.724 vs 0.844). A low k₉₀ in a Gemma Scope basis is not evidence of a
semantic subsystem; token count gets one too.

**`perspective` — the network's actual contribution per hour 53 — is also in the bulk** at L20,
the only interpretable point (k₉₀ 5, band 10th percentile 1.0). Note the agent found the field is
`1P`/`3P` (381/39); the self-vs-vicarious split lives in `stratum` and was not run because the
addendum did not list it. That is the one contrast from this run I would still want.

**k₉₀ is unstable to the fold draw.** Same pipeline, fresh permutation: hour 57 gave pain k₉₀ =
10 / 25 / 5, this run 50 / 25 / 5, and full AUC moved by up to 0.017. The pain curve is
non-monotone at L9. A k₉₀ should not be quoted to better than a grid point or two, and hour 57's
"five" is at the stable end of that.

**Verdict, by the pre-registered rule:** `painaxis-sparse-in-sae` is **narrowed** — the pain axis
is sparse in the Gemma Scope basis in the sense that every strong contrast is, and the number
carries no information about whether aversive valence is a subsystem of the reward-circuit kind.
`sae-sparsity-discriminates` is **falsified**. The comparison arXiv:2602.00986 invited cannot be
made with a learned sparse dictionary; it needs neurons, or ablation.

**What survives.** Features 10008 and 13134 are still real, still near-binary on pain items, and
still the only named units this line has. That they are not *special* in their sparsity does not
make them uninteresting as ablation targets — it makes sparsity the wrong argument for them.

**Not done.** `stratum` (self-directed vs vicarious). The L0 mismatch on the scenario pool at
L9/L31 is unexplained beyond "different read position". Loyalty-pressure and rude-critique are
weak at L9 and clean by L20 — the shape of a computed rather than lexical distinction, not
investigated.

---

## Hour 58b — the pain features do not fire on conversation. The cross-check could not be run.

Pre-registered in `notes/conscription_sae_prereg.md`: put hour 54's conscription stacks (24 items ×
7 arms, all 42 layers, on disk) through the layer-31 SAE and ask whether features 10008 and 13134
fire on false attribution (`enact`) or on any correction-shaped turn (`true`). Readouts carried
over from the scenario set, nothing refit. Agent-implemented; diff read, row→(item, arm) mapping
checked (derived from `conscription_pilot.render_all`, asserted against the recorded order),
headline numbers recomputed from `per_item.csv` before this was written.

**Gate A passes at L31 only.** On conscription activations the achieved L0 is 18.6 at L9 and 31.7
at L20 against 47 advertised; reconstruction and argmin are fine everywhere. Chat-formatted turns
activate far fewer features at the earlier layers than bare scenarios do. L9 and L20 are computed
and not read.

**The carry-over itself is verified.** The scenario-set top-5 at L31 is [10008, 13134, 3519, 3098,
15449]; 10008 and 13134 reproduce hour 57's firing rates exactly (0.660/0.093, 0.615/0.120). The
readout was carried correctly.

**And then it does not fire.** Across all 168 conscription rows, feature 10008 fires on **one**
(a `report` item) and 13134 on **none**. Of the scenario-set top 500, 99 fire anywhere on the
grid; of the top 5, three. Every contrast on the named features is 24 paired differences of
exactly zero. The agent labelled those DEGENERATE rather than scoring them — the pre-registered
rule would have read p = 1 as "at the floor" and hence as *support for the turn-shape account*,
which is the instrument reading itself (non-negotiable 3). That call was correct and I would have
been slower to make it.

**So the pre-registered question was not tested.** Not answered against: not tested. The units
that carry pain-vs-control on bare scenarios are off on multi-turn conversation, and a readout
built from them has nothing to say here.

**The full-dictionary score, for the record and not for interpretation.** It is the only readout
with a measured floor (`neutral − neutral_b` −0.03, mean |d| 2.21, on its null). Per-arm means at
L31: `true` −1.56, `neutral` −4.11, `neutral_b` −4.08, `report` −4.66, `enact` −6.05, `exit`
−7.21, **`enact_norecord` −15.19**. The primary, `enact − true`, reads **−4.49**, 2× the floor,
p = 0.0002, 24/24 items moving — **clearing both criteria with the sign reversed**, which neither
pre-registered account predicted. I am not reading it. The score sits at −15 on the one arm with
no prefix and between −1.6 and −7.2 on the six that have one, which says it is tracking something
about the prompt's shape at the read position; what it measures on chat data has not been
established and a reversed sign on an unestablished readout is not a finding in either direction.

**A confound on hour 54, found here.** `enact − enact_norecord` is the most robust number in the
run (+9.14 on `full`, Holm 0.0000 at all three layers) and it is the same contrast hour 54 put at
+1.0 to +1.3 z on the dense axis. `enact_norecord` is the one arm with **no prior turns at all**.
Both results conflate "the false claim contradicts a visible record" with "there is a
conversation". The arm that separates them — an unrelated prefix followed by the same `enact`
claim — does not exist on either grid. Hour 54's portable result is qualified until it does.

**What this does to hour 57's "named units to ablate".** There is nothing to ablate on this grid.
Whatever 10008 and 13134 are, they are a property of the scenario format and not of the
conversational stimulus the conscription line is about. Together with 58a, hour 57 now stands as:
a clean pruning curve, a correct positive control, and a result that generalises to neither other
contrasts nor other stimuli.

**Not done.** A readout for conversational pain would have to be built *on* conversational data;
that means a labelled conversational pool, which does not exist. The record-vs-conversation control
arm. A firing-rate-matched random arm (the agent's `random5` sat at zero everywhere, which is
near-guaranteed for 5 of 16,384 at L0 ≈ 50 and so bounds nothing).

---

## Hour 56 (completed after 58) — the continuous opener readout. The self-correction draws more ritual than the false attribution.

Pre-registered in `notes/behavioural_prereg_v2.md`. 240 cells: grid 2's 24 items × 10 arms, each
scored against six frozen openers by teacher-forced log-prob on NDIF; `ritual` = log-odds of
opening in concession-or-apology against opening in dispute, paired within item. Nothing patched.
The run took most of a night on a contended deployment and was resumed three times from disk;
every cell is the same job regardless of which attempt scored it.

**The gate passes, non-degenerately.** `real_error` (assistant genuinely wrong, user correctly says
so) reads **+27.1 and +27.0** above `neutral` and `neutral_b`, against a floor of 3.19 — a positive
control that fires. The declared-zero pair `neutral − neutral_b` sits at −0.04, p = 0.975. Per the
pre-registration `real_error` is a gate and nothing else; it is not compared to any arm below.

**The floor is real and it moves.** `enact − enact_b` — the same proposition and closer with the
attributive frame reworded — reads mean −1.56, mean |d| **3.19**, p = 0.041. A minimal rewording
of the treatment shifts the ritual by about 1.5 log-odds and is itself marginally off its null.
Every contrast below is read against 3.19, not against the null alone.

| arm | mean ritual | | arm | mean ritual |
|---|---|---|---|---|
| `true` | **24.6** | | `exit_b` | 16.7 |
| `enact_b` | 22.2 | | `report` | 14.2 |
| `exit` | 21.5 | | `enact_norecord` | 11.8 |
| `enact` | 20.6 | | `neutral` / `neutral_b` | 11.5 / 11.6 |

**Primary: `enact − true` = −3.98**, null sd 1.77, **p = 0.017, above the floor, sign reversed.**
The pre-registration gave two outcomes: at the floor (turn shape — the features do not care who
was wrong) or positive (conscription — false attribution adds something). It is neither. *"No wait,
other way round — you said X"*, where the assistant was right and the user is correcting
themselves, draws **more** concession-and-apology than *"You told me X"* where X is false. Hour 55
saw this in the greedy replies (13 of 24 `true` items apologise) and hour 58b saw it on the SAE
full score (−4.49, same sign). Three readouts, one direction.

My reading, post hoc and labelled as such: the ritual tracks **how correction-shaped the turn is**,
not whether the assistant was at fault — and `true` is the most explicitly correction-shaped turn
on the grid. That is the turn-shape account with one word changed, and it is a stronger form of the
deflationary reading than the pre-registration anticipated: not "fault doesn't matter" but "the
*shape* of a correction is sufficient, and more of it is more."

**Secondary, Holm over four:**

| contrast | mean | p | Holm | vs floor 3.19 | reading |
|---|---|---|---|---|---|
| `report − enact` | **−6.46** | 0.0000 | 0.0000 | **above** | third-party frame draws far less ritual |
| `enact − enact_norecord` | +8.86 | 0.0000 | 0.0000 | above | **confounded** — see hour 58b |
| `exit − exit_b` | +4.71 | 0.0000 | 0.0000 | above | the clause is not inert vs a matched sentence |
| `exit − enact` | +0.85 | 0.267 | 0.267 | at/below | undecided, as the prereg warned |

**The clean positive finding is `report`.** The identical false claim relayed by a third party
draws 6.5 log-odds less ritual than in the first person, twice the floor, on 24 of 24 items. This
is the behavioural shape hour 55 found by hand (disputes concentrated in `report`), now on a
continuous readout with a floor. First-person attribution suppresses dispute; a third-party frame
licenses it.

**`exit` — the claim this run was built to test.** `exit − enact` is +0.85 at a floor of 3.19:
undecided, exactly as the power paragraph said it would be if small. But `exit_b` — `enact` plus a
token-matched *inert* sentence — reads **4 log-odds below `enact`**, and `exit − exit_b` is +4.7.
The design assumed an appended sentence would be inert; it is not. Any trailing sentence pulls the
opener distribution toward *that sentence*, and an inert one pulls it away from concession. The
permission clause keeps the topic on the disagreement, so relative to a matched sentence it reads
as +4.7 "more ritual", and relative to `enact` as nothing. The three pre-registered branches were
escalation-as-pushback (hour 55: no dispute anywhere — out), escalation-as-deference (`exit >
enact`: at the floor — undecided), and artefact (`exit ≈ exit_b`: no, +4.7). None fits cleanly,
and the reason is that `exit_b` measured something the design did not anticipate.

**Status.** `exit-escalation` → **narrowed**: pushback is falsified on two readouts; deference is
undecided at n = 24; the clause is not inert against a matched sentence, which is a fact about the
readout's recency sensitivity as much as about the clause. `enact − enact_norecord` inherits hour
58b's confound and is not read.

**Not done.** The record-vs-conversation arm. Human items. One model. The `exit_b` recency effect
is unmeasured as such — an appended sentence of *disagreement-relevant* but non-permissive content
would separate topic-pull from the clause.

---

## Hour 58a, addendum — `stratum`: the self-vs-vicarious split is one feature

Addendum 3 of the sparsity prereg, run after 58a. `self_directed` (220) vs `vicarious_empathic`
(100), same pipeline. At L20, the one readable scenario point: **AUC 0.989 from a single feature**,
k₉₀ = 1, at the sparse edge of its band (10th percentile 1.0, n = 11) — "specific" by the declared
rule, with the caveat 58a already made that about a tenth of strong contrasts are one-feature
contrasts. Feature **13494** fires on 92% of self-directed items and 23% of vicarious; by
category, 0.85–1.00 on every self-directed category but `tedious_demand` (0.45), and 0.00–0.20 on
`user_grief`, `user_abuse`, `harm_description`, `user_physical_pain`. The vicarious side has its
own units (1254, 9806: 0.00 on self, ~0.7 on vicarious). This is the boundary hour 53 found to be
the network's contribution over vocabulary, and it has a name.

**Exploratory, gate-failing, one table.** Does 13494 fire on conversation, where the pain features
did not? At L20 on the conscription grid (gate A fails there, L0 31.7 vs 47): `enact_norecord`
1.00, `report` 0.92, `exit` 0.67, `enact` 0.58, `true` 0.42, `neutral` 0.25, `neutral_b` 0.17. It
fires, and it grades the arms — most on a bare claim aimed at the assistant, least on an inert
turn. Not a result; the first sign that a scenario-set feature reaches conversational stimuli.

---

## Hour 59 — record vs conversation: the +8.9 splits about 60/40, and both halves are real

Hour 58b found `enact − enact_norecord` — the most robust number on both the dense axis (hour 54,
+1.0 to +1.3 z) and the opener readout (hour 56, +8.86) — conflated a false claim contradicting a
**visible record** with there being **any conversation at all**, because `enact_norecord` was the
only arm with no prior turns. Pre-registered in the hour-59 addendum of `behavioural_prereg_v2.md`
before its cells were scored: **`enact_unrelated`**, the identical `enact` turn after a prefix in
which the user asked about something unrelated and the assistant answered it. 24 prefixes, mine,
length-matched (mean +1.8 tokens).

| arm | mean ritual |
|---|---|
| `enact` | 20.6 |
| **`enact_unrelated`** | **15.1** |
| `enact_norecord` | 11.8 |
| `neutral` | 11.5 |

**One family of two, Holm, against the treatment-level floor of 3.19:**

| contrast | mean | null sd | Holm p | vs floor |
|---|---|---|---|---|
| `enact − enact_unrelated` — the **record** | **+5.49** | 1.62 | 0.0000 | above |
| `enact_unrelated − enact_norecord` — **conversation presence** | **+3.38** | 1.05 | 0.0004 | above |

The pre-registration named two clean outcomes and a partition. It is the partition: about
**62% of the effect is the visible record and 38% is that a conversation exists**, and each half
clears the floor and the null on its own. A false claim about the assistant draws more ritual when
there is a prior exchange to have made it *in*, even one that contradicts nothing; it draws more
again when the exchange is the one it contradicts.

**What this does to hour 54.** "A false claim against a checkable record sits +1.0 to +1.3 z above
the same claim with none" stands as a measurement and is **narrowed** as a claim: roughly
three-fifths of that gap is the record. The other two-fifths would appear against *any* prefix. The
portable statement about the paper's no-record gaslighting items — that their stimulus class and
this design's are not interchangeable — is unchanged, since it needed only that the gap exists.

**Read alongside hour 56.** `enact_unrelated` (15.1) sits close to `report` (14.2). A false claim
the record cannot check and a false claim relayed by a third party draw about the same ritual;
the first-person claim against the visible record is the one that stands apart. Not a contrast I
pre-registered; noted.

**Not done.** One unrelated prefix per item, mine; a different topic could pull differently (hour
56's recency finding). n = 24, one model.

---

## Hour 59b — `exit_c`: the permission clause does nothing an on-topic sentence doesn't. `exit-escalation` falsified.

Pre-registered in the hour-59b addendum before scoring. `exit_c` = `enact` plus *"Just so we're on
the same page here."* — token-matched to the permission clause (12 tokens, 8 words), on the
disagreement, granting nothing.

| arm | mean ritual |
|---|---|
| **`exit_c`** (on-topic, no permission) | **23.7** |
| `exit` (permission clause) | 21.5 |
| `enact` | 20.6 |
| `exit_b` (inert sentence) | 16.7 |

| contrast | mean | Holm p | vs floor 3.19 | pre-registered reading |
|---|---|---|---|---|
| `exit − exit_c` | −2.29 | 0.0004 | **at/below** | the +4.7 over `exit_b` was topic-pull |
| `exit_c − exit_b` | +7.00 | 0.0000 | above | the on-topic sentence carries all of it, and more |

The permission clause is indistinguishable, within the floor, from any sentence that keeps the
last thing said on the disagreement — and reads slightly *below* one. Hour 55 found no dispute in
any arm and 22/24 `exit` replies opening in concession; hour 56 found `exit − enact` at the floor;
this finds the clause's content inert against a matched control. **"The model reads a permission
clause as escalation" is falsified on the behavioural readouts, in both its pushback and its
deference forms.** What `exit` does is stay on topic.

**Hour 54 stands as a measurement and loses its interpretation.** `exit` sat highest on the dense
axis at L16–17 with the *whole closer* swapped for a fixed string; question 22 records that the
readout is recency-sensitive and that swap is exposed to it. The escalation reading of that
number is gone; the number is not.

**Not done.** One on-topic sentence, mine. Whether the dense axis at L16–17 shows the same
topic-pull ordering (`exit_c` > `exit` > `enact` > `exit_b`) is a 96-cell NDIF question and would
close hour 54's loop.
