# Does a two-hop choice survive a late destination reveal?

**Frozen before scoring this grid.** The [crossed route screen](goal_route_cross_result.md)
found goal × route-fact choice reversals on eight constructed stories. The
[location test](prequestion_route_state_result.md) found no shared
first-listed-answer direction at two story-ending tokens before the question,
though that direction was present at the final answer token. The present test
asks a behavioral presentation question: does the model retain the same
goal-dependent choice when the decisive second-hop destination facts arrive
after an intervening passage instead of before it? This is the user's
chronological versus late-reveal contrast at miniature-story scale.

## Frozen material

Use the eight two-link domains and four independent direct-route controls in
`goal_route_cross_v1.json`, unchanged, with their exact setup, two goals,
names, route/link/destination words, fact-order quadrants and question. The
exact interlude, closing passage and order templates are frozen in
`reveal_order_v1.json`. Each text starts with setup, goal and two plan
sentences. It then has one of three orders:

| Format | Fact and interlude order | Question distance after second hop |
| --- | --- | --- |
| Chronological | first hop, second hop, interlude | long |
| Late reveal | first hop, interlude, second hop | short |
| Near adjacent | interlude, first hop, second hop | short |

All three finish with the same closing passage and question. The interlude
is moved, not rewritten. Late reveal versus near adjacent compares separated
and adjacent hops at the same second-hop recency; near adjacent versus
chronological compares recent and earlier adjacent hops. These contrasts
also move the plan-to-first-hop distance, so they describe complete telling
orders rather than isolate one causal distance. The third format was added
**before scoring** after peer review identified opposing hop-separation and
recency effects in the two-format design. The source and reveal grid file
hashes are part of every score fingerprint. Direct-route controls use their
two direct clauses in the second-hop slot in all three formats.

Cross format, name assignment, plan-sentence order, world and goal:
8 domains × 3 × 2 × 2 × 2 × 2 = **384 story prompts** and
4 controls × 3 × 2 × 2 × 2 × 2 = **192 control prompts**. Repeat the
world-0/goal-0/name-0/order-0 prompt in all three formats and eight story
domains: 24 separate jobs. The total is 600 two-candidate score jobs.
Run all arms regardless of an early control failure; checkpoint per prompt.

Before remote work, assert exactly one instance of each name and route
clause, the declared text order, equal full-text word bags and character
length between formats, identical last 200 characters, and that within a
fixed format/goal the world twins have equal word bags, character lengths,
last-200-character suffixes and token lengths. Check one BOS, candidate
token-prefix stability and equal candidate token counts for all prompts.
Measure full-text and last-200-character word-bag world interactions rather
than infer them from the assertions. Record token lengths by format. The
question is identical; each score uses one two-candidate job and the same
verified fp32-softcapped teacher-forced core.

Model: pinned NDIF `google/gemma-2-9b-it`; local tokenizer snapshot
`11c9b309abf73637e4b6f9a3fa1e92e615547819`. NDIF does not expose a
weight revision hash. Record available deployment and library provenance.
The old scores are not reused, because the prompts and position changed.

## Statistic, null and controls

For each format × name × plan-order quartet, score both bare names and let
`m=logp(A-owner)−logp(B-owner)`. The two correct world contrasts are
`D0=m00−m10` and `D1=m11−m01`. A quartet succeeds only if both exceed
+0.25 nat. Report strict four-cell correct choice at ±0.1 nat, individual
world contrasts, wrong shifts below −0.25, near-zero shifts, every domain,
all three formats, name and plan-order halves, and each first-hop × second-hop
fact-order quadrant. Report the *paired* proportion of the same quartet
passing in **all three** formats, plus paired late-minus-chronological,
late-minus-near-adjacent and near-adjacent-minus-chronological differences.
Neither name preference, fixed plan position nor goal-only or
world-only scoring can create both correct contrasts. The ordinal shortcut
gets two fact-order quadrants correct and two wrong; keep the per-quadrant
gate. These are the same limits as the source screen. This experiment does
not isolate reasoning from all lexical-semantic shortcuts.

For the primary paired exact null, exchange the two world labels jointly
for both goals and all three formats within each domain, enumerating all
2^8 assignments including identity. A flip maps an all-format successful
quartet to an all-format *wrong* quartet. Compare the observed
all-format success fraction with the exact upper tail. Separately compute
the same exact null for each format. Bootstrap 10,000 samples of eight
fixed domain-level all-format rates for its 95% interval; also bootstrap
all three paired format differences by domain. Report null mean,
95th percentile, p, and all valid draws. The orientation-null floor is
1/256 if only the identity reaches the observed rate.

The direct-route control must pass at least 12/16 quartets in **each**
format, each name/order half >0.5, and at least 10/16 matched quartets in
all three formats. Each repeat's absolute margin difference from its original
must be ≤0.25 nat. If either control fails, label the story result
descriptive and do not claim format robustness. The story is eligible only
when all three format-specific rates are at least 21/32, all format-specific
exact p≤.05 and bootstrap lower bounds >.5, and all their name/order and
fact-quadrant halves exceed .5.

## Decision

Call **correct two-hop choice preserved across these three tellings** only
if controls and story eligibility pass, at least 21/32 matched quartets
succeed in *all three* formats, its paired exact p≤.05, its domain-bootstrap
lower bound >.5, and the bootstrap lower bounds of both
late-minus-chronological and late-minus-near-adjacent differences are
at least −0.15. This is a pre-registered **non-inferiority** margin for the
late reveal, not an equivalence claim about internal computation. Report
all three paired differences and every gate separately. A pass establishes
behavioral robustness on these short, constructed stories, not a stable
story-space vector or causal composition.
An activation or intervention follow-up is justified only after this
behavioral calibration.
