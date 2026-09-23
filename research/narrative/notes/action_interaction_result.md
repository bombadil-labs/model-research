# Reversing the handover: an action interaction in controlled miniatures

## Design and provenance

The [registered follow-up](action_interaction_prereg.md) tests whether the earlier
actor-goal signal changes when a final handover reverses who receives the object.
It reuses 12 domains, two prior-sentence orders and two actor-goal assignments from
the [first role-swap spike](role_swap_result.md). For each passage, only the final
sentence changes from `giver handed the object to recipient` to the reverse. The
neutral predicate grid undergoes the same reversal. This adds 48 reverse passages
per grid; the forward final-token stacks were already cached.

Model: `Qwen/Qwen2.5-1.5B`, revision
`8faed761d45a263340a0528343f099c05c9a4323`, local CUDA float16.
The longest reverse passage is 100 tokens, below the checkpoint's 131,072-position
configuration. Forward and reverse inputs have identical token IDs through the
bridge period before the handover. Their final-token ID and position also match,
as do the word bags across actions. Within each reverse matched pair, the last 200
characters, word bag, character length, final-token ID and position are identical.
Grid, code, activation and model digests are in ignored local provenance; the
committed [summary](../results/action_interaction_summary.json) contains scores
and model identifiers.

At each layer the action interaction is the raw difference of paired differences,
then normalized:

`I = unit((forward_helps − forward_harms) − (reverse_helps − reverse_harms))`.

For each held-out domain, the direction is fit on both sentence orders of the other
11 domains. The fixed primary band is layers 10–18; all layer curves are reported
in the summary. Domain, rather than pair-by-layer, is the bootstrap unit.

## Registered results

| Fixed layers 10–18, mean pair accuracy | Result |
| --- | ---: |
| Goal action interaction, held-out domain | **0.792** |
| 95% domain bootstrap interval | 0.713–0.866 |
| Goal interaction direction on neutral interaction | **0.602** |
| Goal minus neutral, paired domain bootstrap | **0.190** [0.088, 0.282] |
| Neutral interaction on itself | **1.000** |
| Domain-orientation permutation, 1,000 draws | mean 0.500, p = 0.002 |
| Random direction, 1,000 draws | mean 0.500, 95% span 0.440–0.556 |
| No-action arm / layer 0 | **0.500 / 0.500**, exact ties |

The primary interaction clears the registered 0.70, random-gap, permutation and
bootstrap criteria. The goal-minus-neutral gap clears the required 0.15 and has a
positive bootstrap lower endpoint. This is evidence for a *goal-grid-specific
component of the action interaction relative to this neutral control*. Neutral
interaction is perfectly decodable on its own; the method also captures a strong
syntactic change in which name becomes the last-mentioned recipient.

Additional registered readouts:

| Fixed layers 10–18 | Pair accuracy |
| --- | ---: |
| Forward goal signal, replication from cached stack | 0.792 |
| Forward direction on reverse action, event sign flipped | 0.681 |
| Same reverse action without sign flip | 0.319 |
| Forward direction at the pre-action bridge period | 0.606 |
| Neutral pre-action binding | 0.542 |

The reverse-event and pre-action scores are descriptive: the sign-flipped reverse
score falls short of 0.70, and the pre-action readout is at a different token from
the final readout. They show that some of the prior relation is present before the
action and that the final action changes its alignment, but do not isolate a pure
event-role coordinate. The 0.792 primary score should not be read on its own:
the neutral interaction's 1.000 shows that recipient-position binding is an easy
signal for this instrument. The paired goal-versus-neutral gap is the relevant
positive evidence, and a single neutral predicate pair cannot cover all lexical
alternatives.

## What this changes

The first spike established only a context-sensitive actor-predicate signal at an
identical handover token. The present difference-of-differences adds a controlled
interaction with the final action, above the measured neutral transfer. That is a
small compositional result in activation space, still far from a reusable story
shape or a causal transform.

The next discriminating grid should **keep the same predicates and actor bindings**
while changing the group's goal so that an identical activity switches from
protective to harmful. If the interaction follows that goal switch across held-out
domains, rather than the predicate or final-sentence recipient, it would support a
stronger claim about narrative meaning. Natural-story recognition and steering
remain separate open tests.
