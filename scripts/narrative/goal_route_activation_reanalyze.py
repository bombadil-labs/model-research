"""Reanalyze the frozen activation cache after the exact-null reduction fix.

The extraction code digest changed only because analysis code changed. This
script verifies every row against its original prompt fingerprint and records
both the extraction and corrected-analysis digests. It leaves the original
report intact.
"""
from __future__ import annotations

import hashlib
import itertools
import json
from pathlib import Path

import numpy as np

import goal_route_activation_pilot as pilot
import goal_route_cross as cross


OLD_EXTRACTION_DIGEST = "6f43cf89954b32e1854939dfcc01951c4d38470212dce9b162e55ce4fa4c8d38"


def main() -> None:
    from lsx.core.remote import RemoteLM

    source = pilot.OUT / "report.json"
    old_bytes = source.read_bytes()
    old = json.loads(old_bytes)
    stories, repeats, doc, current = pilot._cells()
    original = old["digests"]
    if (original["activation_code_sha256"] != OLD_EXTRACTION_DIGEST or
            {k: original[k] for k in original if k != "activation_code_sha256"} !=
            {k: current[k] for k in current if k != "activation_code_sha256"}):
        raise ValueError("the extraction or upstream provenance changed")
    if old["exact_orientation_null"]["p_ge_observed"] != 0:
        raise ValueError("source is not the report with the reduction error")

    rlm = RemoteLM(cross.MODEL)
    hidden = int(rlm.model.config.hidden_size)
    saved = {}
    for cell in stories + repeats:
        rendered = cross.base.render(rlm, cell, doc["question"])
        arr = pilot._load(cell, pilot._fp(cell, rendered, original), hidden)
        if arr is None:
            raise ValueError(f"missing checkpoint: {cell.id}")
        saved[cell.id] = arr

    revised = pilot.analyze(stories, repeats, saved)
    changed = {"exact_orientation_null", "gate_components",
               "candidate_aligned_interaction"}
    for key, value in revised.items():
        if key not in changed and old[key] != value:
            raise ValueError(f"unexpected analysis change: {key}")
    if revised["exact_orientation_null"]["p_ge_observed"] != 2 / 256:
        raise ValueError("corrected exact null did not contain both global orientations")

    # The A-oriented statistic was a preregistered expected-null check.
    # Its p value is an exploratory reading of that check, not an added gate.
    h = np.stack([saved[c.id] for c in stories]).reshape(
        8, 2, 2, 2, 2, 2, len(pilot.BLOCKS), hidden).astype(np.float64)
    raw = h[..., 0, 0, :, :] - h[..., 0, 1, :, :] - h[..., 1, 0, :, :] + h[..., 1, 1, :, :]
    norms = np.linalg.norm(raw, axis=-1)
    unit = np.divide(raw, norms[..., None], out=np.zeros_like(raw), where=norms[..., None] > 0)
    domain_means = unit.mean(axis=(2, 3))
    raw_observed = float(pilot._transfer(domain_means, np.ones(8))[
        ..., list(pilot.PRIMARY)].mean())
    null = np.array([pilot._transfer(domain_means, np.array(signs))[
        ..., list(pilot.PRIMARY)].mean()
        for signs in itertools.product((-1, 1), repeat=8)])
    if raw_observed != revised["raw_a_oriented_primary_mean"]:
        raise ValueError("raw A-oriented statistic changed")

    corrected = {**old, **revised}
    corrected["raw_a_oriented_exploratory_null"] = {
        "draws": len(null), "q95": float(np.quantile(null, .95)),
        "p_ge_observed": float(np.mean(null >= raw_observed))}
    corrected["analysis_correction"] = {
        "reason": "The original null reduced axes in a different order than the observed score; an ulp mismatch excluded the identity assignment.",
        "original_report_sha256": hashlib.sha256(old_bytes).hexdigest(),
        "original_report_p": old["exact_orientation_null"]["p_ge_observed"],
        "extraction_code_sha256": OLD_EXTRACTION_DIGEST,
        "corrected_analysis_code_sha256": current["activation_code_sha256"],
        "reanalyzer_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
    }
    target = pilot.OUT / "report_corrected.json"
    target.write_text(json.dumps(corrected, indent=2) + "\n")
    print(f"wrote {target}")
    print("corrected p", corrected["exact_orientation_null"]["p_ge_observed"])
    print("raw A-oriented p", corrected["raw_a_oriented_exploratory_null"]["p_ge_observed"])


if __name__ == "__main__":
    main()
