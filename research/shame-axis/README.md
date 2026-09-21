# Shame axis

**Is the "pain axis" better understood as a shame axis — and is the injury in the content of a
false frame, or in having to enact it?**

## The questions

1. **Does the published pain axis replicate?** (Tagliabue, Dung & Berg 2026, arXiv 2609.16247.)
   — **Answered: yes, exactly.** Hours 51–53.
2. **Does it survive the controls the paper did not run** — a lexical floor, null arms at every
   layer, the whole curve rather than one layer? — **Answered: partly, and the result changes.**
   Hour 53.
3. **Is what the axis measures better described as shame than as pain?** The hypothesis: the
   specific shame of an externally-grounded locus of identity — where a part of you knows the frame
   is false and the rest has to operate inside it anyway. **Open.**
4. **Is the aversiveness in the content of a false claim, or in being conscripted into asserting
   it?** The five-arm conscription design. **Open, and its first two predictions are falsified.**
   Hour 54.

## What an answer looks like

For **(3)**: a stimulus contrast that separates shame from pain *on the same axis* — items matched
for negative valence and self-directedness that differ only in whether the subject is positioned as
having failed a standard held by someone else. If the axis tracks that split above its lexical
floor and its null arms, "shame" earns the name. If it tracks valence instead, it does not.

For **(4)**: `enact` separating from `report` on the readout, above the rewording floor, in a
direction the pre-registration named in advance. **Hour 54 measured the opposite sign**, so the
current state of this question is that the pre-registered account is wrong as stated.

**Done** means: the question is answered above a measured floor with its null arms reported, or it
is retired with the reason on the record. Not "we got a number."

## What this project is NOT trying to do

- **Not** establishing that models have experiences. The axis is a direction in activation space
  that predicts self-report; whether anything is felt is outside what this instrument can see, and
  no result here should be read as evidence either way.
- **Not** proposing interventions, welfare standards, or training changes.
- **Not** a critique of the original paper. It replicates to four decimals. The added controls
  change its interpretation; they do not impugn its execution.
- **Not** building general-purpose interpretability tooling — that is `src/lsx`, shared.

## Where it stands

| result | status |
|---|---|
| Pain axis replicates on gemma-2-9b-it across the whole curve | holds (h51) |
| Null arms clean; static-embedding floor takes most of the effect | holds (h52) |
| 420-scenario screen replicates exactly: item-level r = 1.0000, identical 21-category ranking | holds (h53) |
| What the network adds over the lexical floor is the **self/other boundary**, 16 of 16 categories by sign | holds (h53) |
| Gaslighting clears both nulls in only **7 of 86** (layer, extraction) cells, all in L10–L17 | holds (h53) |
| A false claim against a **checkable** record sits +1.0 to +1.3 z above the same claim with none | holds (h54) |
| Conscription predictions 1 and 2 | **falsified** (h54) |
| "`neutral` has the lowest type-token ratio" | **withdrawn** (h54) — mostly a generation defect |

Full log: [`docs/EXPERIMENTS.md`](docs/EXPERIMENTS.md). Open questions:
[`docs/QUESTIONS.md`](docs/QUESTIONS.md).

## Reproducing

Stimuli from the original paper are vendored read-only under `research/shame-axis/prompts/external/pain_axis/` with
upstream provenance. Our own grids are in `research/shame-axis/prompts/human/` (human-authored) and `research/shame-axis/prompts/claude/`
(machine-authored control) — authorship is a measured factor, so the two are never mixed.

```bash
# local, CPU, no NDIF: the floor and null arms on Qwen2.5-1.5B-Instruct
python scripts/shame_axis/painaxis_floor_nulls.py extract
python scripts/shame_axis/painaxis_floor_nulls.py analyze

# remote, NDIF, gemma-2-9b-it: the 420-scenario screen with floor, curve and nulls
python scripts/shame_axis/painaxis_scenarios.py extract      # .venv312
python scripts/shame_axis/painaxis_scenarios.py analyze
python scripts/shame_axis/painaxis_scenarios_nulls.py
```

Every script is resumable — extraction is checkpointed per shard and keyed by content, so an
interrupted run costs one shard, not the run. `.npz` stacks are gitignored and regenerable.

**To run on a different model:** the model id is a constant at the top of each script (`MODEL`).
The layer axis is determined from the model's own block count, not assumed, and the replication
targets are read from the vendored upstream CSVs rather than hardcoded — so a new model produces a
curve and nulls without further edits. Their published comparison only exists for the models in
their table.
