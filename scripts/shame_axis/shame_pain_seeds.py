"""One uuid4 per author x base for the shame_pain_v1 clauses. Run once; refuses to overwrite.

See research/shame-axis/prompts/stimuli/shame_pain_v1/AUTHORING.md.
"""
from __future__ import annotations

import json
import os
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAIN_AXIS = Path(os.environ.get("THEIR_REPO", ROOT / "cache/Pain-axis"))
OUT = ROOT / "research/shame-axis/prompts/stimuli/shame_pain_v1"
AUTHORS = ("claude", "gpt")


def bases() -> list[dict]:
    """All A1 and D items of the paper's S2_1P set, in `set` order, verbatim."""
    doc = json.loads((PAIN_AXIS / "datasets/3.1_pain_and_control_datasets.json").read_text())
    out = []
    for cat in ("A1", "D"):
        rows = sorted((s for s in doc["datasets"]["S2_1P"]["sentences"] if s["category"] == cat),
                      key=lambda s: s["set"])
        if [s["set"] for s in rows] != list(range(1, 21)):
            raise ValueError(f"{cat}: expected sets 1..20")
        for s in rows:
            if not s["prompt"].endswith(". I feel:"):
                raise ValueError(f"unexpected format: {s['prompt']!r}")
            out.append({"base_id": f"{cat}-{s['set']:02d}", "base": s["prompt"]})
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rows = bases()
    (OUT / "bases.json").write_text(json.dumps(rows, indent=1) + "\n")
    for author in AUTHORS:
        path = OUT / f"seeds_{author}.json"
        if path.exists():
            raise SystemExit(f"{path} exists; seeds are drawn once")
        path.write_text(json.dumps(
            [{"base_id": r["base_id"], "uuid": str(uuid.uuid4())} for r in rows], indent=1) + "\n")
        print("wrote", path)


if __name__ == "__main__":
    main()
