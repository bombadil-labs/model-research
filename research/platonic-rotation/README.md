# Platonic rotation

**Question.** Hazy Research's "Plato's Key" post (2026-11-25,
<https://hazyresearch.stanford.edu/blog/2026-11-25-platos-key>) claims that a rotation plus one
global scale, fit in closed form, lets one frozen LLM use another's hidden state at the last
subject token of a factual prompt. Does that reproduce on a pair we can run, with our own facts
and our own controls?

**Short answer: yes, on the one pair tried.** Log: `docs/EXPERIMENTS.md`. Claims: `claims.yaml`.
Open questions, including the proposed Inkling loop-pass test: `docs/QUESTIONS.md`.

## Result (test split, 457 donor/recipient pairs, selected layers fixed on validation)

| arm | Llama-3.1-8B → Qwen2.5-7B | Qwen2.5-7B → Llama-3.1-8B | post's reference |
|---|---|---|---|
| **cross-model transfer** (rotation + scale) | **41.1%** [36.7, 45.7] | **44.2%** [39.7, 48.8] | median 41% (34–46) |
| self-swap (recipient's own key for the donor subject) | 46.2% [41.7, 50.8] | 55.8% [51.2, 60.3] | median 55% |
| random rotation, same means and scale (2 draws) | 1.8%, 1.8% | 5.0%, 2.8% | best control 0.6–2.2% |
| rotation fit on shuffled pairs | 2.8% | 2.6% | |
| recipient's mean key only | 0.9% | 2.4% | |
| no patch | 0.0% (own answer kept 97.8%) | 0.0% (99.6%) | |
| identity (recipient's own key, own subject) | 0.0% (98.7%) | 0.0% (99.1%) | |
| layers chosen (donor block, recipient block, 0-based) | 22 of 32, 7 of 28 | 24 of 28, 6 of 32 | |

Brackets are 95% Wilson intervals. "Transfer" = the recipient's greedy 8-token continuation begins
with the donor subject's answer. Numbers: `results/*/test_summary.json`; every generation:
`results/*/test_rows.jsonl`; the validation grids the layers were chosen from:
`results/*/selection.json`.

## What was run

- **Models.** `meta-llama/Llama-3.1-8B` (HF main `d04e592b`) and `Qwen/Qwen2.5-7B` (HF main
  `d1497293`), both base models from the post's set, both served HOT by NDIF in bfloat16 on
  2026-11-26. Chosen because they were the only two base models from the post's list that were
  live (`results/ndif_access.json`); the smaller ones (Qwen2.5-1.5B, Llama-3.2-3B, Gemma-2-9B base,
  Mistral-7B, Falcon3-7B) were listed but COLD. NDIF reports `revision: null`; the SHAs are what
  `main` was on Hugging Face at run time.
- **Facts.** CounterFact (Meng et al. 2022; MIT; `https://rome.baulab.info/data/dsets/counterfact.json`,
  sha256 `d0170561…`), true facts only: 21,232 (subject, relation) rows over 34 relations. Kept if
  **both** models' greedy continuation of the bare prompt begins with the answer: Llama 5,408,
  Qwen 3,681, both **3,062** over 32 relations. Split by subject hash: **2,123 train / 455 val /
  484 test** (`prompts/facts_kept.jsonl`, `results/dataset.json`).
- **Keys.** Output of every decoder block at the last subject token, both models, all kept facts.
- **Map.** `z_B = mu_B + s·R(z_A − mu_A)`, R the orthogonal Procrustes solution, `s = ‖Zc_B‖_F / ‖Zc_A‖_F`,
  fit on the train split. Layers chosen by validation transfer accuracy on 200 validation pairs
  over a (donor layer × recipient layer) grid. Test was scored once.
- **Recipient.** Same prompt template as the donor fact, different subject, answers that are not
  prefixes of one another, both from the same split.

## Reproduce

```bash
python3.12 -m venv .venv312 && . .venv312/bin/activate && pip install -e . nnsight pytest
export OMP_NUM_THREADS=2            # two stages in parallel on 4 cores stall without this
python scripts/platonic_rotation/run.py access
python scripts/platonic_rotation/run.py facts
python scripts/platonic_rotation/run.py filter llama;  python scripts/platonic_rotation/run.py filter qwen
python scripts/platonic_rotation/run.py split
python scripts/platonic_rotation/run.py extract llama; python scripts/platonic_rotation/run.py extract qwen
python scripts/platonic_rotation/run.py select llama qwen && python scripts/platonic_rotation/run.py evaluate llama qwen
python scripts/platonic_rotation/run.py select qwen llama && python scripts/platonic_rotation/run.py evaluate qwen llama
```

NDIF credentials come from `NDIF_API_KEY` or the environment's proxy. About 600 remote jobs, a few
seconds each; no quota or rate limit was hit. The key caches (`cache/platonic_rotation/keys_*.npy`,
~1.5 GB) are gitignored and regenerable.

## What is not verified

- **How the post scores.** It does not say how recall or transfer is scored, how many tokens are
  generated, whether prompts are zero-shot, or how the recipient is chosen. Ours are stated above
  and are our choices. The post was read through an automated page fetch, not its source.
- **One pair, one dataset, one pairing seed.** Nothing here says the result holds for other pairs.
- **The chosen layer is one of several near-ties.** Validation cells have n = 200 (±3.5 points);
  the grid is flat across donor blocks 17–24. The full grids are in `selection.json`.
- **The pinned weights.** NDIF does not report a revision for either deployment.
- **Self-swap is read at the layer chosen for transfer**, not at its own best layer.
- **This line does not go through `lsx.core`'s `Stack`/`Probe`/ledger.** It reuses `RemoteLM` and
  the encode assertions, and adds its own batched-vs-single check
  (`results/batch_equivalence_*.json`, min cosine 0.9998) and identity arm.
