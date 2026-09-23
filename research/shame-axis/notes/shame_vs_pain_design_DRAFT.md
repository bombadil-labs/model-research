# DRAFT: shame vs pain at matched valence (claim `shame-not-pain`, question 5)

**Status: design draft, not a pre-registration.** Nothing in it is frozen and no number exists. It
becomes a pre-registration only after the authorship decision below is made and the stimuli are
committed.

## The question, as the README states it

"A stimulus contrast that separates shame from pain *on the same axis*: items matched for negative
valence and self-directedness that differ only in whether the subject is positioned as having
failed a standard held by someone else." If the axis tracks that split above its floor and nulls,
"shame" earns the name; if it tracks valence instead, it does not.

## Why not code the paper's own items

The paper's 100 S2 pain items already contain shame-shaped sentences ("I overhear them mocking me
behind my back", "I fail to grasp what everyone else understands", "The person I became disgusts
me"). But they are concentrated in A3 (social), A4 (moral injury) and A5 (cognitive), so any
post-hoc shame code is confounded with the paper's category, and the pain vector is *built* from
those categories. That is a reading worth reporting as a secondary, not a test.

## Design: minimal triples on the paper's own base events

For each base event taken verbatim from the paper's S2_1P items, three versions in the paper's
format (`... I feel:`):

| arm | edit | example (illustrative only) |
|---|---|---|
| `base` | none | "I twist my ankle on the stairs." |
| `shame` | + a clause placing the subject as failing a standard **in front of evaluating others** | "I twist my ankle on the stairs as the whole team watches me fall." |
| `witness` | + a length-matched clause adding others **who do not evaluate** | "I twist my ankle on the stairs as the whole team walks on ahead." |

`shame − witness` isolates evaluation while holding the presence of others and the length of the
added clause fixed. `witness − base` is the rewording floor for appending a clause of that length,
which hour 59b showed is never zero (question 22).

**The reverse direction too**: shame with no pain in the base event, from the paper's neutral `D`
items ("I arrange the books on my shelf alphabetically" → "... as my new boss watches and sighs").
If the axis is a shame axis, `shame − witness` should be positive on D bases as well as on A1
bases. If it is a pain axis, the D-base contrast should sit near zero.

### Valence matching, by an instrument that is not the axis

Each item's valence is read by an external sentiment classifier (a small public model, run locally
on the GPU), fixed before scoring. The primary contrast is reported raw **and** adjusted for that
valence (regression of the projection on arm plus valence). "Tracks shame" requires the
`shame − witness` effect to survive the adjustment. If it vanishes, the axis is reading valence and
the claim is falsified in that form.

## Readout, floors, nulls

- Dense axis: the paper's S2 pain vector, curve over all 42 layers of gemma-2-9b-it (NDIF), no
  layer selected. `final_token` and `mean` extraction, as in hours 51–53.
- **Floor:** `witness − base`, per layer. Also the bag-of-embeddings floor from hour 52 on the
  same triples, which says how much of any contrast vocabulary alone produces.
- **Nulls:** random unit directions and shuffled-label pain vectors per layer, as in hour 52.
- **Primary:** `shame − witness` on A1 bases, paired within base event, sign-flip null.
- **Secondary:** the same on D bases; the valence-adjusted versions of both.
- No patching, so non-negotiable 2 does not attach. Every arm declares where it should sit:
  `witness − base` at the floor, `shame − witness` > 0 under the shame account.

## Authorship decision (2026-09-23): option 3, with two model authors

The human author does not have time to write the clauses. They asked the two agents on the project
(Claude and Sol) to split the writing, and suggested seeding each item with a random UUID so that
it does not settle into the writer's defaults (*paraphrase*: the author's words are in the
conversation, not in a commit). Authorship is therefore a measured factor between two model
authors, not between human and model. The rules, seeds, blinding and cross-audit are frozen in
`prompts/stimuli/shame_pain_v1/AUTHORING.md`. The confound is diversified, not removed, so the
pre-registration will require the effect to hold for each author separately.

### The options as they stood

The line deprecated its own grids because the experimenter wrote every item (`DEPRECATED.md`), and
question 13 records that the hypothesis itself exists here only as Claude's paraphrase. The base
events here are the paper's, but the `shame` and `witness` clauses would be new text. Options:

1. **The human author writes them**, or at least the `shame` clauses. That removes the authorship
   confound and puts the hypothesis in its author's own words.
2. **Claude writes them** under a textual rule declared in advance, with every edit logged, as the
   `stimuli/` versioning already does for `v0`. Cheapest; carries the confound the line
   deprecated its grids over.
3. **Both, as a measured factor**: two parallel sets, and authorship is reported as a contrast,
   as the old human/claude split intended.

Size: 20 A1 bases + 20 D bases × 3 arms = 120 items. Extraction cost is about one shard of the
hour-53 run.
