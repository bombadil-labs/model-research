# Platonic rotation — experiment log

Entries are dated, not hour-numbered: this line was started in a cloud session that does not know
the other lines' current hour.

---

## 2026-11-26 — NDIF access, and the Plato's Key map on Llama-3.1-8B ↔ Qwen2.5-7B

**Access.** `nnsight` was not installed; installed 0.8.4 into a fresh `.venv312` (the repo's
earlier artifacts record 0.7.0). No NDIF key is in the environment: the session's egress proxy
injects it for `api.ndif.us`, which `lsx.ndif.ProxyAuthBackend` already handles. `/status` listed
181 repos, 15 HOT (`results/ndif_access.json`). Both `thinkingmachines/Inkling-2-Mini` and
`thinkingmachines/TML-d24-varloop-research` are HOT. Of the post's twelve base models, HOT:
Llama-3.1-8B and Qwen2.5-7B only. Listed COLD: Llama-3.2-3B, Qwen2.5-1.5B, Qwen2.5-14B,
Gemma-2-9B, Gemma-2-27B, Mistral-7B-v0.3, Falcon3-7B-Base. Not listed: Granite-3.1-2B,
DeepSeek-7B, GLM-4-9B.

**One thing 0.8.4 changed.** A trace block that references an `lsx` object (`rlm.model.trace(...)`
with `rlm` a `RemoteLM`) is rejected server-side: "payload could not be read (No module named
'lsx')". Binding `model = rlm.model` before the block fixes it. `lsx.core.remote`'s own traces use
the `rlm.model` form and were not re-run here, so whether they still work on 0.8.4 is untested.

**What the post says, checked against the page** (automated fetch, 2026-11-26; quotes are the
fetcher's). Map `z^B = μ_B + s·R(z^A − μ_A)`, `R = UVᵀ` from the SVD of `Z̃_B Z̃_Aᵀ`. The prose
says the scale is chosen "to roughly match the recipient's overall spread"; the equation as
extracted reads `s = ‖Z̃_A‖_F / ‖Z̃_B‖_F`, which does the opposite. Both were run (below). The post
does not define the layer index, the scoring rule, the number of generated tokens, the prompt
format, or the recipient rule.

**Design.** As in the line README. Arms and where each should sit:

| arm | should sit | Llama→Qwen (22→7) | Qwen→Llama (24→6) |
|---|---|---|---|
| treatment | well above every null | **0.411** [0.367, 0.457] | **0.442** [0.397, 0.488] |
| self-swap | ceiling | 0.462 [0.417, 0.508] | 0.558 [0.512, 0.603] |
| no patch | transfer 0; own answer kept ≈ 1 | 0.000; kept 0.978 | 0.000; kept 0.996 |
| identity | equal to no patch | 0.000; kept 0.987 | 0.000; kept 0.991 |
| random rotation ×2 | null | 0.018, 0.018 | 0.050, 0.028 |
| shuffled pairing | null | 0.028 | 0.026 |
| mean key only | null | 0.009 | 0.024 |
| map without off-span completion (exploratory) | — | 0.440 [0.395, 0.486] | 0.446 [0.401, 0.492] |
| reciprocal scale (exploratory) | — | 0.046 | 0.057 |

n = 457 test pairs per arm, 2,123 training facts. Every arm sits where it was declared to. The
identity arm writes the recipient's cached key back at its own position and layer and reproduces
the unpatched output, so the cache → row → position → layer addressing is right; there is no
offline pass-through arm because the readout is a generation, not a residual.

**The result replicates.** Transfer is 9–45× the nulls in both directions and lands inside the
post's 34–46% range; self-swap (46%, 56%) brackets its 55% median.

**Findings beyond the headline.**

1. **The equation as extracted is wrong; the prose is right.** With the reciprocal scale, transfer
   falls to 4.6% / 5.7%, the level of the nulls. The scales differ by a large factor (s = 3.09
   one way, 0.027 the other), so this is not a subtle choice.
2. **Part of the "rotation" is not determined by our data, and it does not matter.** 2,122
   centred training keys cannot fix a 3,584-dimensional rotation: the thin SVD pads the rest with
   whatever LAPACK returns. 11–19% of a test key's centred energy lies off the training span
   (`off_train_span_energy`). `align.fit_centred` makes the padding an explicit seeded random
   completion; dropping it entirely gives 44.0% / 44.6% against 41.1% / 44.2%, inside each
   other's intervals. Selection was done on the completed map; the span-only validation grid is
   recorded beside it and looks the same.
3. **The donor layer is late and barely matters; the recipient layer is early and matters a lot.**
   Chosen donor blocks are 22 of 32 and 24 of 28 (69%, 86% of depth), and validation transfer is
   flat from about donor block 17 on. Recipient blocks are 7 of 28 and 6 of 32 (25%, 19%), and
   transfer collapses past block ~15 (0–1% at Llama block 18). The post's "22–38% of the depth"
   matches our recipient side only. A first pass with donor blocks capped at 18 picked the edge of
   its grid; the grid was extended to 27 before selection was final, all on validation.
4. **Llama→Qwen transfer reaches Qwen's own self-swap.** 41.1% vs 46.2% on test, 44.5% vs 45%
   on validation: a foreign key does about as well as Qwen's own.
5. **Transfer fails where self-swap fails.** Relation P176 (manufacturer; 67 test pairs) transfers
   at 7% / 10% with self-swap at 4% / 9%: the product name usually contains the brand ("Toyota
   …"), which earlier subject tokens still carry. The failure is in the swap paradigm, not the map.
6. **Nulls are not zero everywhere.** P1303 (instrument) and P103 (native language) give 7–50%
   under a random rotation on small n: few possible answers, so a destroyed key falls back to a
   common one that sometimes equals the donor's. The pooled nulls already include this.

**Instrument notes.** Left padding asserted, key positions counted from the end, block outputs
resolved by type. Batched-vs-single capture on the most-padded item: min cosine 0.99986 (Llama),
0.99989 (Qwen) across layers. Facts whose last subject token does not end exactly at the subject's
last character, or is the first input token, were dropped before filtering (35 for Llama, 101 for
Qwen). The unpatched arm keeps the recipient's answer in 97.8% / 99.6% of rows rather than 100%
because the filter and the test ran in different batch compositions in bf16.

**Operational.** About 600 NDIF jobs, typically 2–4 s each, no failures, no rate limits. Two local
SVD processes on four cores stalled (~100 s per fit) until BLAS threads were capped at two each.
