# No name-completion cloze passes crossed calibration

The [frozen calibration](elicitor_calibration_prereg.md) tested six name
completions on four simple goal/plan situations. For each situation, it
crossed which name owned the helpful plan with whether that plan was mentioned
first or second. A cloze could qualify for the fixed-plan story grid only if
all sixteen helpful-minus-harmful name log-probability margins exceeded
+0.1 nat. The [summary](../results/elicitor_calibration_summary.json) records
every margin, the model/device/library versions, and exact grid/code/raw-output
digests. The first run failed during CUDA model transfer before producing a
score; an identical retry completed. No fixed-plan story prompt was scored in
this calibration.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16.
All 96 prompt/candidate token-boundary checks passed. The scorer used one
candidate per forward and fp32 log-softmax of the model's output logits.

| Cloze index | Correct of 16 | Minimum margin | Helpful-first minus helpful-second mean margin |
| ---: | ---: | ---: | ---: |
| 0, original cloze | 10 | −1.98 | +1.07 |
| 1 | 10 | −4.09 | +2.11 |
| 2 | 8 | −4.70 | +3.39 |
| 3 | 11 | −2.92 | +1.79 |
| 4 | 8 | −5.75 | +3.55 |
| 5 | 9 | −2.28 | +1.12 |

**No cloze qualifies.** Every candidate has at least five wrong-name cells,
and the helpful plan's sentence position shifts its name margin by 1.07–3.55
nats on average. The candidate order was frozen before scoring, and no best
cloze is selected from these failures. These development controls reveal that
name swapping alone was an inadequate elicitor calibration: it removed a name
prior while leaving plan position as a shortcut. The crossed grid now exposes
both effects. It does not establish a general failure of the model to reason
about goals, and it does not alter the activation result.

All six clozes have a positive mean helpful-name margin after averaging both
name and plan orders (+0.32 to +0.90 nats). For five clozes, the mean becomes
negative when the helpful plan is mentioned second; the original cloze is the
exception at +0.37. These controls suggest content sensitivity on average
with a stronger per-cell position effect. They are development data, so the
same controls cannot independently certify a balanced contrast readout.

The next behavioral instrument should first demonstrate content sensitivity
under both name and plan-order reversal on fresh controls. A larger
instruction-tuned model is a reasonable next comparison; its calibration
must be run before reading the fixed-plan stories.
