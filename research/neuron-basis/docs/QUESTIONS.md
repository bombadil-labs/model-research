# Open questions

Each entry names what raised it, so a question can be retired when its parent is withdrawn.
Ordered by what the next measurement should be.

## From hour 66 (the sources)

1. **Is a persona neuron a neuron, or a dose?** Two unrelated sweeps put the random-column rate
   near 4% at the strongest coherent dose. Nobody has put a named neuron beside that band on the
   same model, same layer, same dose, with more than one prompt. **This is the first battery.**
   Arms: treatment, random column, random dense direction, no-patch, plus the skip-path arm.
2. **What is the coherence gate, and who declares it?** The library kept "the strongest coherent
   reply"; the Granite run counted 47% of turns ending in repetition loops. A rate without a
   declared coherence window is a rate over an undeclared population. Declare: perplexity under
   the unsteered model relative to no-patch, window fixed before the sweep.
3. **Is the judge an instrument?** The Granite cliff was a keyword list; the library's labels are
   a model's and unchecked. The Jev gate precedent (`research/narrative/notes/jev_prose_gate.md`)
   is the pattern: a blind human-labelled set first, agreement threshold declared, then rates.
4. **Is the batch-layout instability padding?** The library does not define "batch layout". The
   likeliest reading is padding side and batch composition, which is INSTRUMENTS §4 and the
   shortest-item check. If replies still change at batch-of-one under greedy decoding across
   seeds, the instability is numerical, which is a different and smaller finding.
5. **Does the shift need the blocks above it?** Non-negotiable 2 for a generation readout: apply
   the identical shift at the final-norm input. A persona that appears there is a top-of-stack
   vocabulary push wearing a neuron's name.
6. **Dose does not transfer between layers.** The Granite author warns of it; the library's
   `r_L` normalisation is one answer. Report the dose curve per layer, never one dose.

## From hour 67 (the first pass, provisional)

7a. **Is cross-prompt consistency a property of the direction, not of columns?** One random
    column of twenty gave the same persona ("I love to help people. I am a great teacher") on
    three prompts; so did one dense random direction of five ("I'm a dog", "I introduced myself
    as a student"). If any fixed direction yields a consistent persona once the dose is right,
    the permutation null in the pre-registration answers "is identity carried by the
    direction" and not "is a column special". The second pass needs the same cross-prompt
    statistic on dense draws beside columns, at matched n, and the comparison is between those
    two distributions.
7b. **Dose decides whether; direction decides which.** The pilot and the sweep both put the
    transition from "AI self-description" to "persona or broken" between alpha 0.5 and 1.0 for
    nearly every direction tried. That is the Granite reading. What the first pass cannot say
    is whether the persona rate at a fixed dose differs between columns and dense draws, which
    needs n = 50 per arm on the card.
7c. **Degeneracy as a direction (the weight-space-programming bridge).** The Takehi et al.
    post ablates one residual direction from 128 down-projection columns and reports that
    loops stop. Our D row is large at alpha 1.0. Contrast the layer-12 residual during
    degenerate versus coherent steered replies; project every shift onto that direction; ask
    whether the columns that break the model share a write direction. If they do, subtracting
    it is a positive-control arm with a random-direction arm beside it, which is the repo-grade
    version of their edit.
7d. **The vendor switch.** At alpha 0.25–0.75 a handful of random columns make the model say
    it was made by Anthropic or is Claude (rubric code A2). An AI identity is not a persona,
    and the code keeps it out of P, but the fact that random columns reach it at low dose says
    the identity is shallow in this checkpoint. Exploratory.

## From the shame-axis line (hours 57 and 58)

7. **Is the pain axis clean in the neuron basis?** Hour 58 found it sparse in the Gemma Scope
   basis only in the sense every strong contrast is, with a prompt-length nuisance sparser. The
   same pruning curve over native down-projection columns, with the same 35-contrast reference
   distribution, asks Cammarata's question of a direction this repository already owns. Gate B
   (a planted single-column contrast must come back as one column) carries over unchanged.
8. **Do persona columns point along the pain axis?** Only meaningful after 1 and 7 on the same
   model. The reference band is cosine of random columns with the axis at that layer.

## From the viral recipe

9. **Qwen3.5-4B tooling.** `find_blocks` needs a `model.language_model.layers` path and the
   `Qwen3_5ForConditionalGeneration` wrapper needs a development `transformers`. Until then the
   recipe is replicated on a different model and labelled as such.
10. **The layer-16 neuron.** The reproduction found one three times as hostile at the same dose
    as the named pair. If a sweep of 180 cells finds a stronger knob than the viral one, the viral
    one was a draw from a distribution, which is question 1 again.

## From Cammarata's essay

11. **Read side of the steered neurons.** Top contexts, negative pole, surrounding context, no
    noun lists, and a test of the description on new inputs. Exploratory; whatever it finds,
    "this neuron writes a persona" and "this neuron reads X" are two claims and are kept apart.
12. **Weak activations.** The essay says including them changes how many related things a neuron
    appears to cover more than whether it is legible. For a neuron whose *write* side is being
    tested, the relevant activation range is the one the dose puts it in, which is far outside
    anything the neuron reaches naturally. Record where the dose sits on the neuron's own
    activation distribution.

## Methodological, not empirical

13. **A `Direction` from a weight column has no fit and no hold-out.** `lsx.core.Direction`
    refuses a direction that did not declare what it never saw. A column saw nothing; whether that
    is `held_out={"axis": "weights", "unseen": set()}` or a new constructor with provenance from
    the checkpoint and revision is a core design decision and is not made here.
