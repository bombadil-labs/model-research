# model-research

Activation-level research on transformer internals. Several independent lines of enquiry share one
measurement toolkit, one set of methodological rules, and one retraction ledger.

The toolkit (`src/lsx`) and the method (`docs/`) are shared. Each research line owns everything
else: its own stimuli, results, experiment log and public page, under `research/<line>/`.

| line | question | status |
|---|---|---|
| **[shame-axis](research/shame-axis/README.md)** | Is the reported "pain axis" better understood as a shame axis — and is the injury in the content of a false frame or in having to enact it? | active |
| **[narrative](research/narrative/README.md)** | Can the relational structure of a narrative be measured, fit as an operator, and pointed at a domain where the parts are unknown? | active |

## Why one repo

The two lines ask unrelated questions. They share the parts that are expensive to get right:

- **The toolkit.** `lsx.core` — residual capture with asserted spans, the NDIF remote path, `Grid` /
  `Stack` / `Direction` / `Floor` / `Arm` / `Claim`, the instrument registry, the ledger.
- **The method.** The non-negotiables in `CLAUDE.md` and the six broken instruments in
  `docs/INSTRUMENTS.md` were bought by real failures, mostly in the narrative line, and they keep
  earning their place in the other. Splitting the repo would mean either duplicating measurement
  code — and silent drift in measurement code is the exact failure class these rules exist to
  catch — or leaving the rules behind.
- **The retraction ledger.** An instrument found broken invalidates results in every line at once.
  `docs/INSTRUMENTS.md` is shared for that reason.

## Layout

```
src/lsx/core/          shared measurement core
src/lsx/<line>/        line-specific modules
scripts/<line>/        line-specific runnable scripts
tests/{lsx,<line>}/    tests, mirroring the above
docs/                  shared method: INSTRUMENTS.md, DELEGATION.md, specs/
research/<line>/       README, docs/{EXPERIMENTS,QUESTIONS}.md, prompts/, results/, notes/
```

## Running it

```bash
python -m venv .venv && . .venv/bin/activate && pip install -e '.[dev]'
export HF_HOME=$PWD/cache/hf HF_HUB_DISABLE_XET=1
pytest                       # 261 tests, no model required
```

Remote work uses NDIF through `.venv312` (py3.12, nnsight). Each line's README says how to
reproduce its own results, and on which models.

## The rules

`CLAUDE.md` holds the non-negotiables. The short version: every battery reports treatment, random
**and** no-patch; any readout at or after a patch layer needs a pass-through arm; estimate the noise
floor before believing a null; never select a layer on scoring data; read the diff of code touching
extraction, patching or ranking, not the report of it.

Negatives and confounds are recorded with the same care as positives. **Retraction is a first-class
operation**: a withdrawn result is edited in place, where it was claimed, with what replaced it.
