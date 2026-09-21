"""Validate every research line's `claims.yaml` against docs/specs/claims_v1.md.

Run in CI and before the pages build. The point is that a claim cannot be marked answered without
pointing at the answer, and a retraction cannot be a dead end — the two ways a claims table rots
into decoration. Exits non-zero on any failure, so a broken table fails the build rather than
rendering with holes in it.

Usage:  python scripts/check_claims.py            # every line
        python scripts/check_claims.py shame-axis # one line
"""
from __future__ import annotations

import pathlib
import re
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
RESEARCH = ROOT / "research"

# status -> terminal?  (docs/specs/claims_v1.md)
STATUS = {"open": False, "running": False, "holds": True, "narrowed": True,
          "falsified": True, "withdrawn": True, "retired": True}
REQUIRED = ("id", "claim", "status")
ID_RE = re.compile(r"^[a-z0-9]+(?:-[a-z0-9]+)*$")


def check_line(d: pathlib.Path) -> tuple[list[str], int, int]:
    path = d / "claims.yaml"
    if not path.exists():
        return ([f"{d.name}: no claims.yaml (docs/specs/claims_v1.md)"], 0, 0)
    doc = yaml.safe_load(path.read_text()) or {}
    claims = doc.get("claims") or []
    errs: list[str] = []
    if doc.get("line") != d.name:
        errs.append(f"{d.name}: `line:` is {doc.get('line')!r}, should be {d.name!r}")
    seen: dict[str, int] = {}
    terminal = 0
    for i, c in enumerate(claims):
        tag = f"{d.name}[{c.get('id', i)}]"
        for f in REQUIRED:
            if not (c.get(f) or "").strip() if isinstance(c.get(f), str) else not c.get(f):
                errs.append(f"{tag}: missing `{f}`")
        cid, st, text = c.get("id"), c.get("status"), (c.get("claim") or "").strip()
        if cid:
            if not ID_RE.match(str(cid)):
                errs.append(f"{tag}: id must be a lower-case slug")
            if cid in seen:
                errs.append(f"{tag}: duplicate id (also at index {seen[cid]})")
            seen[cid] = i
        if st not in STATUS:
            errs.append(f"{tag}: status {st!r} is not one of {sorted(STATUS)}")
            continue
        is_term = STATUS[st]
        terminal += is_term
        # (3) a terminal claim must point at its answer
        if is_term and not (c.get("where") or "").strip():
            errs.append(f"{tag}: status `{st}` is terminal but `where` is empty — "
                        "a claim cannot be answered without pointing at the answer")
        # (4) a retraction is never a dead end
        if st == "withdrawn" and not (c.get("superseded_by") or "").strip():
            errs.append(f"{tag}: `withdrawn` requires `superseded_by`")
        # (5) an assertion, not a topic
        if text:
            if not text.endswith("."):
                errs.append(f"{tag}: `claim` must be a sentence ending in a full stop")
            if len(text.split()) < 4:
                errs.append(f"{tag}: `claim` reads as a topic, not an assertion")
        # a `where` that names a repo file must exist
        w = (c.get("where") or "").split("#")[0].strip()
        if w and "/" in w and not (d / w).exists() and not (ROOT / w).exists():
            errs.append(f"{tag}: `where` points at {w!r}, which does not exist")
    return errs, terminal, len(claims)


def main(argv: list[str]) -> int:
    lines = [RESEARCH / argv[1]] if len(argv) > 1 else sorted(p for p in RESEARCH.iterdir() if p.is_dir())
    total_err = 0
    for d in lines:
        errs, term, n = check_line(d)
        if n:
            bar = "#" * round(20 * term / n) + "." * (20 - round(20 * term / n))
            state = "CLOSED" if term == n else f"{n - term} open"
            print(f"{d.name:14s} [{bar}] {term}/{n} terminal · {state}")
        for e in errs:
            print(f"  FAIL {e}")
        total_err += len(errs)
    print(f"\n{'OK' if not total_err else str(total_err) + ' problem(s)'}")
    return 1 if total_err else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
