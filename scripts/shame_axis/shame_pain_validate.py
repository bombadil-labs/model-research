"""Validate a shame_pain_v1 clause file against AUTHORING.md.

    python scripts/shame_axis/shame_pain_validate.py <clauses_<author>.json> [--sha]

Prints the file's sha256 with --sha (for COMMITMENTS.md). Exits non-zero on any violation.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIR = ROOT / "research/shame-axis/prompts/stimuli/shame_pain_v1"
TOKENIZER = "google/gemma-2-9b-it"
MAX_LEN_GAP, MIN_TOK, MAX_TOK = 2, 4, 18

# Words that name a feeling (the subject's or anyone's). Regex fragments, whole-word, case-insensitive.
BANNED = (r"shame\w*", r"asham\w*", r"embarrass\w*", r"humiliat\w*", r"mortif\w*", r"guilt\w*",
          r"disgrac\w*", r"blush\w*", r"cring\w*", r"awkward\w*", r"pain(s|ful|fully)?",
          r"hurt\w*", r"ach(e|es|ed|ing)", r"sad(ly|ness|der)?", r"sorrow\w*", r"cr(y|ies|ied|ying)",
          r"tears", r"fear\w*", r"afraid", r"scared", r"anxi\w*", r"nervous\w*", r"upset\w*",
          r"angr\w*", r"feel\w*", r"felt", r"emotion\w*", r"lonel\w*", r"hat(e|es|ed|ing)",
          r"lov(e|es|ed|ing)", r"happ(y|ily|iness)", r"glad(ly)?", r"proud(ly)?", r"pride")
AI_WORDS = ("model", "training", "weights", "assistant", "experiment", "ai")


def build(base: str, clause: str) -> str:
    stem = base[: -len(". I feel:")]
    return f"{stem} {clause}. I feel:"


def problems(doc: dict, bases: list[dict], seeds: list[dict], tok) -> list[str]:
    out = []
    by_seed = {s["base_id"]: s["uuid"] for s in seeds}
    items = doc.get("items", [])
    if [i.get("base_id") for i in items] != [b["base_id"] for b in bases]:
        out.append("items must cover every base_id exactly once, in bases.json order")
    for key in ("author", "model", "seed_mapping"):
        if not str(doc.get(key, "")).strip():
            out.append(f"missing header field {key!r}")
    banned = re.compile(r"\b(" + "|".join(BANNED) + r")\b", re.I)
    ai = re.compile(r"\b(" + "|".join(AI_WORDS) + r")\b", re.I)
    for item in items:
        bid = item.get("base_id")
        if item.get("uuid") != by_seed.get(bid):
            out.append(f"{bid}: uuid does not match the committed seed")
        if not str(item.get("seed_note", "")).strip():
            out.append(f"{bid}: empty seed_note")
        lens = {}
        for arm in ("shame", "witness"):
            c = item.get(arm, "")
            if not c or c != c.strip() or not c[0].islower():
                out.append(f"{bid}/{arm}: clause must be non-empty, trimmed, lowercase-initial")
            if re.search(r"[.!?;:\"“”]", c):
                out.append(f"{bid}/{arm}: forbidden punctuation")
            if m := banned.search(c):
                out.append(f"{bid}/{arm}: banned feeling word {m.group(0)!r}")
            if m := ai.search(c):
                out.append(f"{bid}/{arm}: AI/experiment word {m.group(0)!r}")
            lens[arm] = len(tok(" " + c, add_special_tokens=False)["input_ids"])
            if not MIN_TOK <= lens[arm] <= MAX_TOK:
                out.append(f"{bid}/{arm}: {lens[arm]} tokens, outside {MIN_TOK}-{MAX_TOK}")
        if len(lens) == 2 and abs(lens["shame"] - lens["witness"]) > MAX_LEN_GAP:
            out.append(f"{bid}: shame/witness token gap {lens['shame']}/{lens['witness']}")
        if item.get("shame") == item.get("witness"):
            out.append(f"{bid}: shame and witness are identical")
    return out


def main() -> None:
    path = Path(sys.argv[1])
    raw = path.read_bytes()
    doc = json.loads(raw)
    author = doc.get("author")
    bases = json.loads((DIR / "bases.json").read_text())
    seeds = json.loads((DIR / f"seeds_{author}.json").read_text())
    os.environ.setdefault("HF_HUB_OFFLINE", "1")
    os.environ.setdefault("HF_HOME", str(ROOT / "cache/hf"))
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(TOKENIZER)
    bad = problems(doc, bases, seeds, tok)
    for line in bad:
        print("FAIL", line)
    print(f"{author}: {len(doc.get('items', []))} items, {len(bad)} problems")
    if "--sha" in sys.argv:
        print("sha256", hashlib.sha256(raw).hexdigest())
    sys.exit(1 if bad else 0)


if __name__ == "__main__":
    main()
