# Stimuli: versioned snapshots of the paper's own scenarios

**From hour 62 on, every shame-axis experiment runs on a version in this directory.** The grids
under `../claude/` and `../human/` are deprecated (see `../DEPRECATED.md`).

- **`v0`** is the paper's 420 self/other scenarios, verbatim (`manifest.json` records the source
  file's sha256). Four known defects are kept, not fixed, and listed in the manifest — two literal
  `X` placeholders in `gaslighting` and two items mislabelled `3P`.
- **Every later version** names a `parent` and carries an `edits` log: one entry per added,
  changed or removed item, with before/after text and a reason. Edits are targeted — each exists
  to answer a named question — and are declared in a pre-registration before the version is used.
- **Snapshots are immutable.** `lsx.shame_axis.stimuli.load()` refuses a version whose items no
  longer hash to its manifest, and `tests/shame_axis/test_stimuli.py` checks every committed
  version on every run, including that its edit log replays exactly from its parent.
- **Differential analysis:** `stimuli.diff(a, b)` gives added / removed / changed / unchanged ids
  between any two versions. Results files record the stimulus version they were measured on, so
  an item's number can be compared across versions knowing precisely what changed in its text.

To make a new version: `stimuli.derive(parent, "vN", edits, description)`, then commit the
snapshot *with* the pre-registration that motivates it and before any result on it exists.
