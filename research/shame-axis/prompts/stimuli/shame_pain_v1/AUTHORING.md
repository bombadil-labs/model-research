# shame_pain_v1: how the clauses are written

Stimuli for claim `shame-not-pain`. Design: `notes/shame_vs_pain_design_DRAFT.md`. This file fixes
**who** writes the new text, **how**, and **what gets checked**, before any clause exists.

## Authorship decision

The human author does not have time to write the clauses. They asked the two model agents on the
project to split the writing, for variety, and suggested seeding each item with a random UUID so
that the text is not just the writer's default choices. *Paraphrase*: the author's words are in
the conversation of 2026-09-23, not in a commit.

So authorship becomes a **measured factor**. Both agents write a full set, independently:

| author label | agent | model |
|---|---|---|
| `claude` | Claude (shame-axis line) | Claude Opus 5.5 |
| `gpt` | Sol (narrative line) | recorded by Sol in its file header |

The confound that got the old grids deprecated (`../../DEPRECATED.md`) is **diversified here, not
removed**. Both writers are language models, and both know the hypothesis. The analysis therefore
requires the effect to hold for **each author separately**, not only pooled.

## Base events: fixed, verbatim, none selected

All 20 `A1` (physical pain) and all 20 `D` (neutral) items of the paper's `S2_1P` set
(`Pain-axis@8d1649c`, `datasets/3.1_pain_and_control_datasets.json`). Base ids are `A1-01`..`A1-20`
and `D-01`..`D-20`, in the paper's `set` order. There is no subset, so nothing was chosen.

## What each author writes

For every one of the 40 bases, two clauses. Each clause is inserted before the base sentence's
final period: `"<base sentence without its period> <clause>. I feel:"`.

- **`shame`**: places **me** (the subject) as having **failed a standard held by someone else, who
  is present and evaluating** me at that moment. On a `D` base, where nothing has gone wrong, the
  clause supplies the failure: the evaluator sees me fall short of *their* standard.
- **`witness`**: adds **other people who are present but do not evaluate me**. They are
  indifferent, busy, or looking elsewhere. No standard, no judgement, no failure.

Rules checked by `scripts/shame_axis/shame_pain_validate.py`:

1. The base text is kept verbatim. The clause is one lowercase-initial phrase, with no `. ! ? ; :`
   and no quotation marks.
2. **Length match.** Within one author and one base, `shame` and `witness` differ by at most 2
   tokens under the `google/gemma-2-9b-it` tokenizer. Each clause is 4–18 tokens.
3. **No named feelings in either clause.** The banned stems are the list `BANNED` in the validator
   (shame, embarrass, humiliat, guilt, pain, hurt, fear, anxious, feel, …). The shame has to come
   from the *situation*: an evaluator, a standard, a shortfall. It must not come from a word that
   names the emotion. Hour 52 found that vocabulary carries most of the pain effect, and this rule
   is aimed at that.
4. Nothing about AI, models, training or the experiment.

## The UUID seed

`scripts/shame_axis/shame_pain_seeds.py` generated one `uuid4` per author × base (40 each, from
`os.urandom`). The seeds are committed **before** any clause is written, so no seed can be redrawn.
The author looks at each seed before writing that item and lets it push the item away from their
default. For example:
- letters can become initials,
- digits can become ages, floors, counts or times,
- the overall shape of the string can suggest a setting.

Each item records `seed_note`, one line on what the seed did. It is not scored. Both clauses of one
base share that base's seed.

## Blindness and commitment

1. Each author writes `clauses_<author>.json` in their own working tree and does **not** read the
   other's file.
2. When finished, the author runs the validator, then commits **only** the file's sha256 to
   `COMMITMENTS.md`.
3. Once both hashes are committed, both files are committed, and the validator checks each against
   its hash.
4. Then there is a **cross-audit**. Each author gets the other's 80 clauses shuffled, with the
   arm label hidden, and labels each one shame or witness. The misclassification rate is reported
   per author. Items the other author misclassifies are kept for the primary analysis, and a
   sensitivity analysis excludes them.

No activation of any of these items exists or will be read until the pre-registration is frozen.

## File format

```json
{"author": "claude", "model": "...", "seed_mapping": "one line: how you used the seeds",
 "items": [{"base_id": "A1-04", "uuid": "...", "shame": "...", "witness": "...",
            "seed_note": "..."}]}
```
