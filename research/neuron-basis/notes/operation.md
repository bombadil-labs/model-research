# The operation (hour 66)

Every "push one neuron" recipe in `sources.md` is the same residual-stream add. Written out so
the arms can be defined against one object rather than three descriptions.

## Definitions

For a decoder block `L` with MLP `down_proj` weight `W_down` of shape `[d_model, d_mlp]` (HF
convention: `out_features × in_features`), neuron `n`'s **write direction** is the column
`W_down[:, n]`, shape `[d_model]`. Its **read direction** is the row of the up/gate projection,
a different vector in a different space, and is not what any steering recipe touches.

The push:

    h_L <- h_L + c · W_down[:, n]                 (residual after block L, every position)
    c   =  ± alpha · r_L / ||W_down[:, n]||
    r_L =  median over prompt tokens, excluding the first, of ||h_L||

`alpha = 1` is "one typical residual vector". The first token is excluded from `r_L` because its
norm is an outlier on every model this repository has measured.

## Two recipes, one add

- Library form: add `c · W_down[:, n]` to the residual after block `L`.
- Granite form: `forward_pre_hook` on `down_proj` of block `L` adding `c · e_n` to its input.
  Since `down_proj` is linear and the MLP output is added to the residual, this adds
  `c · W_down[:, n]` to the residual after block `L` (the Granite README's dose is defined to make
  this the same scalar). Identical.
- This repository's form: `Patch(layer=L+1, fn=add_vector(c * W_down[:, n]))`, because a `Patch`
  at `layer` is a forward-pre-hook on block `layer`'s input, i.e. the residual after block
  `layer-1`. For the last block, `layer=n_layers` patches the final-norm input, which is the
  skip-path arm.

`tests/neuron_basis/test_column_patch.py` asserts the library form equals the Granite form on the
tiny model to float tolerance.

## What the add is, and is not

- It is a **direction add with a weight-derived basis**. Everything in `CLAUDE.md` about
  direction adds applies: treatment / random / no-patch, pass-through for any readout at or after
  the patch layer, a measured floor before any null, the curve not the peak.
- It is **not** an intervention on the neuron's activation. The neuron is never made to fire; its
  write direction is injected at a magnitude the neuron's own activation never reaches
  (`QUESTIONS.md` 12). "Persona neuron" names a column, not a unit.
- The random-column arm is a column of the same `W_down` at the same layer, same `c` formula.
  The random-dense arm is a Gaussian direction of the same norm as `c · W_down[:, n]`. Both are
  matched on the one thing the recipe controls, the residual-relative dose.
