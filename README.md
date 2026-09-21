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

## Acknowledgements

Remote execution for every large-model result in this repository runs on **NDIF**, the National
Deep Inference Fabric, through the **nnsight** library. Work at this scale would not be possible
without it.

Per the nnsight project's request — *"If you use `nnsight` in your research, please cite"*:

```bibtex
@article{fiottokaufman2024nnsightndifdemocratizingaccess,
      title={NNsight and NDIF: Democratizing Access to Foundation Model Internals},
      author={Jaden Fiotto-Kaufman and Alexander R Loftus and Eric Todd and Jannik Brinkmann and
              Caden Juang and Koyena Pal and Can Rager and Aaron Mueller and Samuel Marks and
              Arnab Sen Sharma and Francesca Lucchetti and Michael Ripa and Adam Belfki and
              Nikhil Prakash and Sumeet Multani and Carla Brodley and Arjun Guha and Jonathan Bell
              and Byron Wallace and David Bau},
      year={2024},
      eprint={2407.14561},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2407.14561},
}
```

NDIF is an NSF-funded national research infrastructure led by Northeastern University. **Before
this repository is published, check <https://ndif.us> for the acknowledgement wording and award
number they ask for** — the citation above is taken from the nnsight repository, which is the only
source we were able to verify directly; the NSF award identifier reported elsewhere has not been
confirmed against a primary source here.

Third-party stimuli we replicate are vendored read-only under each line's `prompts/external/`,
with the upstream repository and commit recorded in a `PROVENANCE.md` beside them. They are not
ours and their authors' licence and authorship govern reuse.

**Jev** (TypeSafe) is used as a prose-quality gate in the narrative line, evaluated against blind
human labels before adoption; the evaluation is in `research/narrative/notes/jev_prose_gate.md`.
