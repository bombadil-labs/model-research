# model-research

Activation-level research on transformer internals. Several independent research lines share one
measurement toolkit (`src/lsx`), one set of rules (below), and one retraction ledger
(`docs/INSTRUMENTS.md`). Start at `README.md`; each line's own README says what it is for.

## Read these before touching measurement code

- **`docs/INSTRUMENTS.md`** — the five instruments this project found broken and what each invalidated.
  Shared across lines: an instrument found broken invalidates results everywhere at once.
- **`docs/DELEGATION.md`** — the plan → review → execute → screen → integrate flow, and the rules
  each retraction bought.
- **`docs/specs/core_v1.md`** — the verified measurement core.

## Non-negotiables

1. **Every battery reports treatment, random, AND no-patch.** A battery without all three is not a
   result. Every arm declares where it should sit; an arm off its null is a bug until proven otherwise.
2. **Any readout at or after a patch layer needs a pass-through arm** (the offline arithmetic:
   `readout(base_resid + shift)`, no forward pass).
3. **Estimate the noise floor before believing a null.** Three negatives were withdrawn as an
   instrument reading itself.
4. **Never select a layer on scoring data.** Report the curve.
5. **Read the diff of agent code touching extraction, patching or ranking — not the report.** Two of
   six bugs arrived via a summary that was trusted.
6. **Never `pgrep -f`/`pkill -f` a pattern contained in your own command string.** Cost so far: one
   false kill and 48 wasted minutes.
7. **Attribution is a field, not a sentence.** Anything attributed to a human author without a commit
   containing that author's text is a paraphrase and is labelled as such. A claim about what a
   document says is checked against the document, not against the previous turn. (Non-negotiable 5,
   extended from code to provenance.)

## Layout

```
src/lsx/core/          shared measurement core — never imports a line's modules
src/lsx/<line>/        line-specific modules
scripts/<line>/        line-specific runnable scripts
tests/{lsx,<line>}/    tests, mirroring the above
docs/                  shared method: INSTRUMENTS.md, DELEGATION.md, specs/
research/<line>/       README.md, docs/{EXPERIMENTS,QUESTIONS}.md, prompts/, results/, notes/
```

**The core is shared. `lsx.core` must never import from `lsx.narrative` or `lsx.shame_axis`.**
Line code depends on the core, never the other way round, and never on another line.

## Environment

- `.venv` — py3.11, CUDA torch, local models. `.venv312` — py3.12, nnsight, NDIF. Venvs are per
  worktree (`pip install -e` pins one `src`).
- **Hardware changed on 2026-09-22.** Everything local before that date ran on a cloud box, CPU
  float32. From then on, local runs are on a WSL2 machine with an RTX 3060 Ti (8 GB VRAM) and about
  7 GB RAM. `LM` still defaults to `device="cpu"`, so GPU use is opt-in. Any local result run on
  `cuda` records the device in its artifact. A GPU rerun of a CPU-era number is a replication on
  new hardware, not the same measurement, so check it against the old value before relying on it.
- Two agents share the machine. Wrap local model loads in `flock /tmp/model-research-local.lock`.
- Keys load from `~/.bashrc` (interactive shell only): `NDIF_API_KEY`, `HUGGINGFACE_API_KEY`.
  Export `HF_TOKEN` from the latter.
- `HF_HOME=$PWD/cache/hf`, `HF_HUB_DISABLE_XET=1`, `HF_HUB_OFFLINE=1` for local runs.
- Llama-3.1-405B is **not** reachable with this key (h34). NDIF and TypeSafe credentials come from
  the environment/proxy; never print them.
- The NDIF GPU is shared and a co-tenant can exhaust the deployment's memory cap; extraction OOMs
  then are not your batch size. Every extraction script is shard-checkpointed for that reason —
  retry, do not redesign.
- Disk is plentiful locally (~900 GB) but RAM is not; models that don't fit in 8 GB VRAM or 7 GB
  RAM go to NDIF. `.npz` stacks are gitignored; they persist on this machine but not in the repo.

## Claims and closure

Each line keeps `research/<line>/claims.yaml` — every claim it has made and where that claim now
stands (`open` · `running` · `holds` · `narrowed` · `falsified` · `withdrawn` · `retired`).
**A line is closed when no claim is left non-terminal.** That is the only definition of done here.

`python scripts/check_claims.py` validates every table and prints each line's progress. A terminal
claim must point at its answer; a `withdrawn` claim must name what replaced it. Spec:
`docs/specs/claims_v1.md`. **Add the open rows, not only the answered ones** — a table listing only
what you resolved will report a line closed while its open problems run to a page.

## Conventions

Do not open pull requests. Record negatives and confounds with the same care as positives;
**retraction is a first-class operation** — withdraw in place, where the claim was made, with what
replaced it. Never include a model identifier in a commit message, PR body, or any artifact pushed
to the repository.

Agents must not edit another line's `README.md`, `VISION.md`, `WRITEUP.md`, `ALGEBRA.md`, or any
`docs/EXPERIMENTS.md` without being asked.
