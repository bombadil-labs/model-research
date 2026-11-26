"""Facts, subject spans, splits and donor/recipient pairing. No model, no network."""
from __future__ import annotations

import hashlib
import json
import random
from typing import Sequence

SOURCE = {
    "name": "CounterFact (Meng et al. 2022, ROME)",
    "url": "https://rome.baulab.info/data/dsets/counterfact.json",
    "sha256": "d017056125178a13728594e66a801357a8db9ed7973a7425554bb4271de9fc6f",
    "license": "MIT (github.com/kmeng01/rome); facts derive from ParaRel / Wikidata (CC0)",
}


def build_facts(counterfact: Sequence[dict]) -> list[dict]:
    """One row per (subject, relation). Only the true fact is used; the counterfactual is dropped."""
    seen, out = set(), []
    for rec in counterfact:
        rw = rec["requested_rewrite"]
        template, subject = rw["prompt"], rw["subject"]
        key = (subject, rw["relation_id"])
        if template.count("{}") != 1 or key in seen:
            continue
        seen.add(key)
        start = template.index("{}")
        out.append({
            "id": int(rec["case_id"]), "relation": rw["relation_id"], "template": template,
            "subject": subject, "answer": rw["target_true"]["str"],
            "prompt": template.replace("{}", subject), "span": [start, start + len(subject)],
        })
    return out


def split_of(subject: str) -> str:
    """Split by SUBJECT: every fact about a subject lands in the same split."""
    h = int(hashlib.sha1(subject.encode("utf-8")).hexdigest(), 16) % 100
    return "train" if h < 70 else "val" if h < 85 else "test"


def last_subject_token(offsets: Sequence[tuple[int, int]], span: Sequence[int]) -> int | None:
    """Index of the last token overlapping the subject's character span, or None when the
    tokenization does not end a token exactly where the subject ends (a token straddling the
    subject and what follows is not "the last subject token" of anything).

    `offsets` are per-token (char_start, char_end); special tokens carry (0, 0) and never match.
    """
    lo, hi = span
    inside = [i for i, (a, b) in enumerate(offsets) if b > a and a < hi and b > lo]
    if not inside:
        return None
    last = inside[-1]
    return last if offsets[last][1] == hi else None


def key_index(tok, fact: dict) -> tuple[int, int] | None:
    """(index from the END of the sequence, token count) of the last subject token, or None.

    Counted from the end because NDIF batches are left-padded (INSTRUMENTS §4b). Refused when the
    key would be the very first input token: with no <bos> (Qwen) that position carries a
    start-of-sequence state, not a subject representation. Verified by decoding, because offset
    mappings have been wrong before: the tokens ending at the key must spell the subject's tail.
    """
    enc = tok(fact["prompt"], return_offsets_mapping=True, add_special_tokens=True)
    ids, offsets = enc["input_ids"], enc["offset_mapping"]
    idx = last_subject_token(offsets, fact["span"])
    if idx is None or idx == 0:
        return None
    first = min(i for i, (a, b) in enumerate(offsets) if b > a and b > fact["span"][0])
    if tok.decode(ids[first:idx + 1]).strip() != fact["subject"].strip():
        return None
    return idx - len(ids), len(ids)


def norm(s: str) -> str:
    return " ".join(s.strip().casefold().split())


def says(generation: str, answer: str) -> bool:
    """The generation begins with the answer (case- and whitespace-insensitive)."""
    return bool(norm(answer)) and norm(generation).startswith(norm(answer))


def make_pairs(facts: Sequence[dict], seed: int = 0) -> list[tuple[int, int]]:
    """(donor, recipient) index pairs: same prompt template, different subject, and answers of
    which neither is a prefix of the other, so one generation cannot score as both."""
    rng = random.Random(seed)
    by_template: dict[str, list[int]] = {}
    for i, f in enumerate(facts):
        by_template.setdefault(f["template"], []).append(i)
    pairs = []
    for i, f in enumerate(facts):
        a = norm(f["answer"])
        cands = [j for j in by_template[f["template"]]
                 if facts[j]["subject"] != f["subject"]
                 and not norm(facts[j]["answer"]).startswith(a)
                 and not a.startswith(norm(facts[j]["answer"]))]
        if cands:
            pairs.append((i, rng.choice(cands)))
    return pairs


def read_jsonl(path) -> list[dict]:
    with open(path) as fh:
        return [json.loads(line) for line in fh if line.strip()]


def write_jsonl(path, rows) -> None:
    with open(path, "w") as fh:
        for r in rows:
            fh.write(json.dumps(r, ensure_ascii=False) + "\n")
