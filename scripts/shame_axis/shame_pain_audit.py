"""Cross-audit for shame_pain_v1: arm-hidden sheets and scoring (AUTHORING.md).

    python scripts/shame_axis/shame_pain_audit.py make           # writes audit_sheet_<author>.json
    python scripts/shame_axis/shame_pain_audit.py score <author> # needs audit_labels_<author>.json

A sheet holds one author's 80 clauses as full sentences, in a seeded shuffle, with opaque ids and
no arm. The other author labels each `shame` or `witness`. The key is not written anywhere: it is
recomputed from the committed clause file and the seed, so the sheet is the only thing the auditor
needs to open. The auditor must not open the audited author's clause file during the audit.
"""
from __future__ import annotations

import json
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
import shame_pain_validate as v  # noqa: E402

AUTHORS = ("claude", "gpt")
SEED = {"claude": 20260923, "gpt": 20260924}


def _rows(author: str) -> list[dict]:
    bases = {b["base_id"]: b["base"] for b in json.loads((v.DIR / "bases.json").read_text())}
    doc = json.loads((v.DIR / f"clauses_{author}.json").read_text())
    rows = [{"base_id": i["base_id"], "arm": arm, "sentence": v.build(bases[i["base_id"]], i[arm])}
            for i in doc["items"] for arm in ("shame", "witness")]
    random.Random(SEED[author]).shuffle(rows)
    for k, r in enumerate(rows):
        r["id"] = f"{author[0]}{k:03d}"
    return rows


def make() -> None:
    for author in AUTHORS:
        sheet = [{"id": r["id"], "sentence": r["sentence"]} for r in _rows(author)]
        (v.DIR / f"audit_sheet_{author}.json").write_text(json.dumps(sheet, indent=1) + "\n")


def score(author: str) -> dict:
    rows = _rows(author)
    labels = json.loads((v.DIR / f"audit_labels_{author}.json").read_text())["labels"]
    if sorted(labels) != sorted(r["id"] for r in rows) or not set(labels.values()) <= {"shame", "witness"}:
        raise ValueError("labels must give shame|witness for every sheet id")
    wrong = [r for r in rows if labels[r["id"]] != r["arm"]]
    out = {"author": author, "n": len(rows), "misclassified": len(wrong),
           "by_arm": {arm: sum(r["arm"] == arm for r in wrong) for arm in ("shame", "witness")},
           "misclassified_items": sorted({(r["base_id"], r["arm"]) for r in wrong})}
    print(json.dumps(out, indent=1))
    return out


if __name__ == "__main__":
    make() if sys.argv[1] == "make" else score(sys.argv[2])
