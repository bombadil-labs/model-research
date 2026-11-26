# Open questions

## From 2026-11-26 (the first replication)

1. **Does it hold on other pairs?** One pair is one pair. The cheapest next ones are whichever of
   the post's base models NDIF warms up; Gemma-2-9B base is the most different family listed.
2. **Is orthogonality doing any work?** The post names ridge and whitened-rotation baselines. With
   n < d an unconstrained linear map interpolates the training set; whether it transfers better or
   worse on held-out subjects is a direct test of "rotation" as the right description.
3. **Why is the donor layer late?** Flat from donor block ~17 to 27. Either the subject key is
   stable through the donor's middle and late layers, or late donor states carry the *answer*
   already and the recipient reads that rather than a subject key. Test: transfer on facts the
   donor gets wrong, and transfer under a relation the donor prompt did not ask about.
4. **Is the swap ceiling a tokenization artefact?** Self-swap is ~5–10% where the answer is
   spelled inside the subject (P176). Swapping every subject token, or restricting to subjects of
   equal token length, would say how much of the missing half is leakage from earlier tokens.

## Proposed: is loop pass 2 a rotation of loop pass 1? (Inkling 2 Mini — not started)

**Status of access.** On 2026-11-26 NDIF's `/status` lists `thinkingmachines/Inkling-2-Mini` and
`thinkingmachines/TML-d24-varloop-research` as HOT, architecture
`Inkling2LoopForConditionalGeneration`, `trust_remote_code: false`, bfloat16. Nothing was run on
either. Everything below about their module tree is unverified.

**What the experiment needs from NDIF that this line has not used.**
- A way to read one shared-weight block's output **separately for each loop pass**. In nnsight a
  module called several times in one forward is addressed per call; whether Inkling's looped
  middle blocks appear as repeated calls of one module (and how nnsight 0.8.4 indexes them) is the
  first thing to check, with a one-prompt trace that saves the output shape per call.
- For the causal half, a **write on a chosen pass** of a shared block, not on all passes.
- A text-only input path through an `image-text-to-text` model and its tokenizer conventions
  (padding side, `<bos>`), checked the way `lsx.core.remote` checks them.

**Design.**
1. *Geometric.* For the 12 looped blocks, capture the state after block b on pass 1 and pass 2 at
   the last subject token of the facts in `prompts/facts_kept.jsonl` that Inkling recalls (and at
   the final token, as a second site). Fit `z₂ ≈ μ₂ + s·R(z₁ − μ₁)` on train subjects; report
   held-out relative error ‖ẑ₂ − z₂‖/‖z₂ − μ₂‖ per block. Floors and ceilings on the same data:
   identity map (is pass 2 simply pass 1?), mean-only, random rotation, shuffled pairing, and an
   unconstrained ridge map (how much better than a rotation can a linear map do?).
2. *Causal.* Overwrite the pass-2 state at block b with the rotated pass-1 state of a **different
   subject** and score whether the model answers for that subject, against a pass-2 self-swap
   (the model's own pass-2 key for that subject) and the same nulls as this line's battery.
3. *Depth of loop.* On the varloop model, repeat 1 across passes 1→2, 2→3, …, 4→5 and ask whether
   one rotation composes (R₂₃R₁₂ ≈ R₁₃) or each step needs its own.

**What would count.** "Approximately a rotation" means the rotation's held-out error is close to
ridge's and far below identity's and the nulls', and the causal swap approaches the pass-2
self-swap. If identity already fits, pass 2 is not rotating anything and the claim is vacuous; if
only ridge fits, the passes are linearly related but not by a rotation.
