# Name-balanced elicitor calibration (frozen before any new scores)

The first behavioral cloze failed one of two easy name-swap controls. Its
paired margins nevertheless showed a positive content effect smaller than a
name prior. This calibration searches for a cloze that passes *independent*
simple controls in both name orders before the fixed-plan story grid is read
again. Results from the first story run must not select a cloze.

`elicitor_calibration_v1.json` freezes four new, unambiguous goal/plan controls
and six clozes in listed order. Each control uses its own name pair and is
scored twice, swapping which name owns the helpful plan. For each of the 48
control–cloze–name-order cells, score the total teacher-forced log-probability
of the helpful name and the harmful name after the cloze; report their
difference. Tokenize every full sequence first and require the prompt to be an
unchanged token prefix and the two candidates to have equal token counts.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16 under
the shared GPU lock. Save the exact grid and code digests, device, dtype and
library versions. The first cloze whose **all eight** helpful-minus-harmful
margins exceed +0.1 nat is eligible for a subsequent story-level probe. If
none passes, record the calibration failure and do not use this base model's
name-completion accuracy as a story-understanding measure. Report every cloze,
including the previously used first one. This is instrument selection on
calibration examples only, not a confirmatory result about narrative geometry.
