# Neutral predicate control (added after the role-swap result, before control extraction)

The registered role-swap probe scored 0.792 in layers 10–18. An exploratory audit found a large
order-antisymmetric component: training a direction on one sentence order and testing the reverse
scores 0.0, while training and testing the same order scores 1.0. The registered balanced average
still succeeds, but this makes a surface-name/order artifact a live alternative.

The frozen control grid `role_swap_neutral_v1.json` keeps all 12 actor pairs, all final handovers,
both sentence orders, and the same actor swaps. It replaces the opposed protective and harmful
goals with two neutral activities: counting stones and watching clouds. Matched pairs still have
identical last 200 characters, word bags, character lengths, and final token position. The labels
remain bookkeeping labels only; they have **no moral or plot meaning** in this grid.

Extract the same final-period states under the same checkpoint, device and dtype. For each held-out
domain, fit the direction on the *original goal-bearing grid's* other 11 domains, then score its
dot product with the neutral grid's paired displacement. Report the complete layer curve, fixed
mid-layer mean (10–18), and the same-order / reversed-order diagnostic. A role-sensitive direction
should give a mid-layer mean near 0.5 on the neutral grid. A result above 0.60 would show that the
registered 0.792 may be substantially explained by actor-name binding or sentence structure even
after balancing orders. This is a post-result diagnostic, not a new pre-registered confirmation of
the first positive. The paired neutral-grid scorer itself may find a direction; that would measure
shared syntax, and must be reported alongside the cross-grid transfer.
