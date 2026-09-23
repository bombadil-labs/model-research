# Name-balanced elicitor calibration (frozen before any new scores)

The first behavioral cloze failed one of two easy name-swap controls. Its
paired margins nevertheless showed a positive content effect smaller than a
name prior. This calibration searches for a cloze that passes *independent*
simple controls in both name orders before the fixed-plan story grid is read
again. Results from the first story run must not select a cloze.

`elicitor_calibration_v1.json` freezes four new, unambiguous goal/plan controls
and six clozes in listed order. Each control uses its own name pair and crosses
which name owns the helpful plan with whether that plan sentence is mentioned
first or second. For each of the 96 control–cloze–name-order–plan-order cells,
score the total teacher-forced log-probability
of the helpful name and the harmful name after the cloze; report their
difference. Tokenize every full sequence first and require the prompt to be an
unchanged token prefix and the two candidates to have equal token counts.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16 under
the shared GPU lock. Save the exact grid and code digests, device, dtype and
library versions. The first cloze whose **all sixteen** helpful-minus-harmful
margins exceed +0.1 nat is eligible for a subsequent story-level probe. If
none passes, record the calibration failure and do not use this base model's
name-completion accuracy as a story-understanding measure. Report every cloze,
including the previously used first one. Report each cloze's mean margin when
the helpful plan is first, its mean when the helpful plan is second, and their
difference as the position effect. This is instrument selection on
calibration examples only, not a confirmatory result about narrative geometry.

## Pre-score amendment after adversarial review

The first frozen grid placed the helpful plan first in every example. A cloze
could pass by choosing the first name without reading plan content. Before any
model score was obtained, the grid was changed to reverse plan-sentence order
independently of name order, and the eligibility gate was raised from eight
to sixteen cells per cloze. The original six clozes and four story situations
are unchanged. The selected cloze's margins are development scores, not an
independent sensitivity estimate.
