# `claims.yaml` — the per-line table of claims and where each one stands

Every research line keeps one `research/<line>/claims.yaml`. It is the single source for that
line's public table, its progress meter, and the closure rule. Nothing about a claim's status is
written in HTML by hand.

## Why a file and not a section of prose

A claim's status changes more often than its wording. Keeping status in prose means the page, the
README and the log drift apart, which is the same failure as the instruments count: three documents
asserting a number, none of them computing it. Here the number is computed.

## The closure rule

**A line is closed when no claim is left in a non-terminal state.** That is the only definition of
done this project uses. It is deliberately hard to satisfy and deliberately easy to check.

## Statuses

| status | terminal | means |
|---|---|---|
| `open` | no | posed; not yet measured |
| `running` | no | measurement in flight |
| `holds` | yes | answered; survives its floor and its null arms |
| `narrowed` | yes | true, with a boundary that changes what the claim says |
| `falsified` | yes | measured, and the prediction was wrong |
| `withdrawn` | yes | was claimed here, now retracted, with what replaced it |
| `retired` | yes | abandoned deliberately, reason on record, never measured |

`retired` exists so a question judged not worth answering has a terminal state. Without it a line
can never close except by answering everything, which is not how research ends.

## Page header

The public page's header is single-sourced here rather than re-derived from prose:

```yaml
line: shame-axis
title: Shame axis                 # what the page is called
question: >-                      # the line's question, one sentence, rendered as the page's h1
  Is the reported pain axis better read as a shame axis?
blurb: >-                         # two lines under it; what a visitor needs to know first
  We replicated a published result exactly, then measured it against a floor its authors never ran.
audience: mechanistic interpretability · model welfare
```

## Fields

```yaml
line: shame-axis
claims:
  - id: replication-curve          # stable; never reused, never renumbered
    claim: >
      The pain axis replicates on a model they used, across the whole curve.
    status: holds
    evidence: h51 · gemma-2-9b-it, 84 layer-points, mean |Δ| 0.0006
    where: docs/EXPERIMENTS.md#hour-51        # required for every terminal status
    pre_registered: false
    superseded_by: null                        # required when status is `withdrawn`
```

- `id` — stable slug. A claim that changes status keeps its id; a claim that changes *meaning* gets
  a new id and the old one is `retired` or `withdrawn`.
- `claim` — one sentence, in the present tense, stating what is asserted. Not a topic.
- `evidence` — the number and where it came from, short enough for a table cell.
- `where` — a link into the log or a results file. **Required for every terminal status**: a claim
  cannot be marked answered without pointing at the answer.
- `pre_registered` — `true` if the claim was written down before the measurement. Rendered, because
  a falsified pre-registration is worth more than a confirmed afterthought.
- `superseded_by` — **required when `withdrawn`**: what replaced it, so a retraction is never a
  dead end.

## What the validator enforces

`scripts/check_claims.py`, run in CI and before the pages build:

1. every claim has `id`, `claim`, `status`, and `status` is one of the seven;
2. ids are unique within a line;
3. every terminal claim has a non-empty `where`;
4. every `withdrawn` claim has a non-empty `superseded_by`;
5. `claim` reads as an assertion, not a topic — it must contain a verb and end in a full stop;
6. no claim is both `pre_registered: true` and missing from the line's log.

A build that cannot satisfy these fails rather than rendering a table with holes in it.
