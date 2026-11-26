"""Plato's Key replication on one model pair, over NDIF. Stages, each resumable:

    python scripts/platonic_rotation/run.py access                 # what NDIF serves right now
    python scripts/platonic_rotation/run.py facts                  # CounterFact -> fact rows
    python scripts/platonic_rotation/run.py filter  llama|qwen     # which facts each model recalls
    python scripts/platonic_rotation/run.py split                  # keep both-correct, split by subject
    python scripts/platonic_rotation/run.py extract llama|qwen     # keys, every layer
    python scripts/platonic_rotation/run.py select   DONOR RECIPIENT   # layers, on VALIDATION
    python scripts/platonic_rotation/run.py evaluate DONOR RECIPIENT   # every arm, on TEST, once

Run from the repo root in `.venv312`. Large arrays go to `cache/platonic_rotation/` (gitignored);
everything a reader needs to check a number goes to `research/platonic-rotation/results/`.
"""
from __future__ import annotations

import datetime
import json
import pathlib
import sys
import urllib.request

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
from lsx.platonic_rotation import align, facts as F  # noqa: E402

CACHE = ROOT / "cache" / "platonic_rotation"
LINE = ROOT / "research" / "platonic-rotation"
RES = LINE / "results"
MODELS = {"llama": "meta-llama/Llama-3.1-8B", "qwen": "Qwen/Qwen2.5-7B"}
GEN_TOKENS = 8
GEN_BATCH = 256
TRAIN_CAP = 5000            # the post fits on "fewer than 5,000 training facts"
VAL_PAIRS = 200             # validation pairs used per (lA, lB) cell
COARSE_B = [3, 6, 9, 12, 15, 18]             # recipient blocks; the post reports peaks at 22-38% depth
COARSE_A = [3, 6, 9, 12, 15, 18, 21, 24, 27]  # donor blocks; extended after the first pass peaked at the 18 edge


def dump(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, ensure_ascii=False) + "\n")


def load(path):
    return json.loads(path.read_text())


def rlm_for(name):
    from lsx.core.remote import RemoteLM
    return RemoteLM(MODELS[name])


def provenance(names):
    import nnsight, torch, transformers
    from huggingface_hub import model_info
    out = {"date_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "nnsight": nnsight.__version__, "torch": torch.__version__,
           "transformers": transformers.__version__, "execution": "NDIF remote, bfloat16",
           "models": {}}
    status = json.load(urllib.request.urlopen("https://api.ndif.us/status", timeout=30))
    for n in names:
        dep = [v for v in status["deployments"].values()
               if v.get("repo_id") == MODELS[n] and v.get("application_state") == "RUNNING"]
        out["models"][n] = {
            "repo_id": MODELS[n],
            "ndif_revision": dep[0].get("revision") if dep else "not running",
            "ndif_dtype": dep[0].get("dtype") if dep else None,
            # NDIF reports revision null (= the repo's main); this is what main was at run time.
            "hf_main_sha_at_run": model_info(MODELS[n]).sha,
        }
    return out


# ------------------------------------------------------------------------------------------
def stage_access():
    status = json.load(urllib.request.urlopen("https://api.ndif.us/status", timeout=30))
    rows = {}
    for v in status["deployments"].values():
        state = v.get("application_state") or v.get("deployment_level")
        level = v.get("deployment_level")
        key = v["repo_id"]
        rank = {"HOT": 0, "WARM": 1, "COLD": 2}.get(level, 3)
        if key not in rows or rank < rows[key][0]:
            rows[key] = (rank, level, state, v.get("revision"))
    out = {"checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
           "endpoint": "https://api.ndif.us/status",
           "deployments": {k: {"level": r[1], "state": r[2], "revision": r[3]}
                           for k, r in sorted(rows.items(), key=lambda kv: (kv[1][0], kv[0]))}}
    dump(RES / "ndif_access.json", out)
    for k, r in out["deployments"].items():
        if r["level"] != "COLD":
            print(f"{r['level']:5s} {k}")
    print(sum(r["level"] == "COLD" for r in out["deployments"].values()), "more listed COLD")


def stage_facts():
    import hashlib
    src = CACHE / "src" / "counterfact.json"
    if not src.exists():
        src.parent.mkdir(parents=True, exist_ok=True)
        urllib.request.urlretrieve(F.SOURCE["url"], src)
    sha = hashlib.sha256(src.read_bytes()).hexdigest()
    assert sha == F.SOURCE["sha256"], f"source changed: {sha}"
    rows = F.build_facts(json.loads(src.read_text()))
    F.write_jsonl(CACHE / "facts_all.jsonl", rows)
    print(len(rows), "facts,", len({r["relation"] for r in rows}), "relations")


def stage_filter(name):
    from lsx.platonic_rotation.remote import generate
    rlm = rlm_for(name)
    rows = F.read_jsonl(CACHE / "facts_all.jsonl")
    out_path = CACHE / f"filter_{name}.json"
    done = load(out_path) if out_path.exists() else {}
    keyed = [(r, F.key_index(rlm.tok, r)) for r in rows]
    for r, k in keyed:
        if k is None:
            done.setdefault(str(r["id"]), {"neg": None, "gen": None})
    todo = sorted([(k[1], r, k) for r, k in keyed if k is not None and str(r["id"]) not in done],
                  key=lambda t: t[0])
    print(name, "facts", len(rows), "unindexable", sum(k is None for _, k in keyed),
          "to generate", len(todo), flush=True)
    for i in range(0, len(todo), GEN_BATCH):
        chunk = todo[i:i + GEN_BATCH]
        gens = generate(rlm, [r["prompt"] for _, r, _ in chunk], max_new_tokens=GEN_TOKENS)
        for (_, r, k), g in zip(chunk, gens):
            done[str(r["id"])] = {"neg": k[0], "gen": g}
        dump(out_path, done)
        print(f"  {i + len(chunk)}/{len(todo)}", flush=True)


def stage_split():
    rows = F.read_jsonl(CACHE / "facts_all.jsonl")
    fl = {n: load(CACHE / f"filter_{n}.json") for n in MODELS}
    counts = {"source_facts": len(rows)}
    for n in MODELS:
        counts[f"{n}_indexable"] = sum(fl[n][str(r["id"])]["neg"] is not None for r in rows)
        counts[f"{n}_correct"] = sum(fl[n][str(r["id"])]["gen"] is not None
                                     and F.says(fl[n][str(r["id"])]["gen"], r["answer"]) for r in rows)
    kept = []
    for r in rows:
        e = {n: fl[n][str(r["id"])] for n in MODELS}
        if all(e[n]["gen"] is not None and F.says(e[n]["gen"], r["answer"]) for n in MODELS):
            kept.append({**r, "split": F.split_of(r["subject"]),
                         "neg": {n: e[n]["neg"] for n in MODELS}})
    # cap the training set, deterministically
    counts["both_correct_before_train_cap"] = len(kept)
    train = [r for r in kept if r["split"] == "train"]
    if len(train) > TRAIN_CAP:
        order = np.random.default_rng(0).permutation(len(train))
        keep_ids = {train[i]["id"] for i in order[:TRAIN_CAP]}
        kept = [r for r in kept if r["split"] != "train" or r["id"] in keep_ids]
    for s in ("train", "val", "test"):
        counts[s] = sum(r["split"] == s for r in kept)
    counts["relations_kept"] = len({r["relation"] for r in kept})
    subj = {}
    for r in kept:
        subj.setdefault(r["subject"], set()).add(r["split"])
    assert all(len(v) == 1 for v in subj.values()), "a subject straddles splits"
    F.write_jsonl(LINE / "prompts" / "facts_kept.jsonl", kept)
    dump(RES / "dataset.json", {"source": F.SOURCE, "criterion":
         f"greedy {GEN_TOKENS}-token continuation of the bare prompt begins with the answer, in both models",
         "counts": counts,
         "per_relation": {rel: sum(r["relation"] == rel for r in kept)
                          for rel in sorted({r["relation"] for r in kept})}})
    print(counts)


def kept_facts():
    return F.read_jsonl(LINE / "prompts" / "facts_kept.jsonl")


def keys_path(name):
    return CACHE / f"keys_{name}.npy"


def stage_extract(name, batch=64):
    from lsx.platonic_rotation.remote import capture_keys
    rlm = rlm_for(name)
    rows = kept_facts()
    L = len(rlm.blocks)
    d = rlm.model.config.hidden_size
    path, done_path = keys_path(name), CACHE / f"keys_{name}.done.json"
    done = set(load(done_path)) if done_path.exists() and path.exists() else set()
    arr = np.lib.format.open_memmap(path, mode="r+" if done else "w+", dtype=np.float16,
                                    shape=(len(rows), L, d))
    order = sorted(range(len(rows)), key=lambda i: len(rlm.tok(rows[i]["prompt"])["input_ids"]))
    check_path = RES / f"batch_equivalence_{name}.json"
    for b in range(0, len(order), batch):
        idx = [i for i in order[b:b + batch]]
        if all(i in done for i in idx):
            continue
        got = capture_keys(rlm, [rows[i]["prompt"] for i in idx], [rows[i]["neg"][name] for i in idx])
        arr[idx] = got
        done.update(idx)
        arr.flush()
        dump(done_path, sorted(done))
        print(f"  {name} {len(done)}/{len(rows)}", flush=True)
    if not check_path.exists():
        # batched-vs-single on the maximally padded item of a mixed-length batch (core spec §7.2)
        idx = order[:8] + order[-8:]
        got = capture_keys(rlm, [rows[i]["prompt"] for i in idx], [rows[i]["neg"][name] for i in idx])
        single = capture_keys(rlm, [rows[idx[0]]["prompt"]], [rows[idx[0]]["neg"][name]])[0]
        a, s = got[0].astype(np.float64), single.astype(np.float64)
        cos = (a * s).sum(-1) / (np.linalg.norm(a, axis=-1) * np.linalg.norm(s, axis=-1))
        stored = arr[idx[0]].astype(np.float64)
        cos_stored = (stored * s).sum(-1) / (np.linalg.norm(stored, axis=-1) * np.linalg.norm(s, axis=-1))
        dump(check_path, {"model": MODELS[name], "item": rows[idx[0]]["prompt"],
                          "padded_by_tokens": len(rlm.tok(rows[idx[-1]]["prompt"])["input_ids"])
                          - len(rlm.tok(rows[idx[0]]["prompt"])["input_ids"]),
                          "min_cos_batched_vs_single": float(cos.min()),
                          "min_cos_stored_vs_single": float(cos_stored.min()),
                          "per_layer_cos": [round(float(c), 6) for c in cos]})
        print("  batch equivalence min cos", cos.min(), "stored", cos_stored.min())
        assert cos.min() > 0.99 and cos_stored.min() > 0.99, "batched capture disagrees with single"


# ------------------------------------------------------------------------------------------
def run_rows(rlm, name, rows, jobs):
    """jobs: list of (recipient_fact_index, layer or -1, vec or None) -> list of generations."""
    from lsx.platonic_rotation.remote import generate
    d = rlm.model.config.hidden_size
    order = sorted(range(len(jobs)), key=lambda k: len(rows[jobs[k][0]]["prompt"]))
    out = [None] * len(jobs)
    for b in range(0, len(order), GEN_BATCH):
        ks = order[b:b + GEN_BATCH]
        vecs = np.stack([jobs[k][2] if jobs[k][2] is not None else np.zeros(d, np.float32) for k in ks])
        gens = generate(rlm, [rows[jobs[k][0]]["prompt"] for k in ks], max_new_tokens=GEN_TOKENS,
                        negs=[rows[jobs[k][0]]["neg"][name] for k in ks],
                        layers=[jobs[k][1] for k in ks], vecs=vecs)
        for k, g in zip(ks, gens):
            out[k] = g
        print(f"    rows {min(b + GEN_BATCH, len(order))}/{len(order)}", flush=True)
    return out


def setup(donor, recipient):
    rows = kept_facts()
    KA = np.load(keys_path(donor), mmap_mode="r")
    KB = np.load(keys_path(recipient), mmap_mode="r")
    idx = {s: [i for i, r in enumerate(rows) if r["split"] == s] for s in ("train", "val", "test")}
    pairs = {}
    for s in ("val", "test"):
        sub = [rows[i] for i in idx[s]]
        pairs[s] = [(idx[s][a], idx[s][b]) for a, b in F.make_pairs(sub, seed=0)]
    return rows, KA, KB, idx, pairs


def layer_keys(K, ids, layer):
    return np.asarray(K[ids, layer], dtype=np.float32)


def stage_select(donor, recipient):
    rows, KA, KB, idx, pairs = setup(donor, recipient)
    rlm = rlm_for(recipient)
    out_path = RES / f"{donor}__to__{recipient}" / "selection.json"
    rng = np.random.default_rng(0)
    vp = [pairs["val"][i] for i in rng.permutation(len(pairs["val"]))[:VAL_PAIRS]]
    d_ids, r_ids = [p[0] for p in vp], [p[1] for p in vp]
    prev = load(out_path) if out_path.exists() else {}
    grid, grid_span = prev.get("grid", {}), prev.get("grid_train_span", {})
    cen = {}

    def centred(tag, K, layer):
        if (tag, layer) not in cen:
            cen[tag, layer] = align.centre(layer_keys(K, idx["train"], layer))
        return cen[tag, layer]

    def score(cells):
        cells = [c for c in cells if f"{c[0]},{c[1]}" not in grid]
        if not cells:
            return
        jobs = []
        for la, lb in cells:
            a, b = centred("a", KA, la), centred("b", KB, lb)
            za = layer_keys(KA, d_ids, la)
            for span_only in (False, True):
                v = align.fit_centred(a, b, train_span_only=span_only).apply(za)
                jobs += [(r, lb, v[k]) for k, r in enumerate(r_ids)]
            print(f"  fit lA={la} lB={lb}", flush=True)
        gens = run_rows(rlm, recipient, rows, jobs)
        n = len(vp)
        for c, (la, lb) in enumerate(cells):
            for off, g_ in ((0, grid), (1, grid_span)):
                g = gens[(2 * c + off) * n:(2 * c + off + 1) * n]
                g_[f"{la},{lb}"] = sum(F.says(x, rows[d]["answer"]) for x, d in zip(g, d_ids)) / n

    def best():
        k = max(grid, key=lambda k: (grid[k], -sum(map(int, k.split(",")))))
        return tuple(map(int, k.split(",")))

    def srt(g):
        return dict(sorted(g.items(), key=lambda kv: tuple(map(int, kv[0].split(",")))))

    def save(extra=None):
        dump(out_path, {"donor": MODELS[donor], "recipient": MODELS[recipient],
                        "split": "validation", "n_pairs_per_cell": len(vp),
                        "layer_convention": "index l = output of decoder block l (0-based)",
                        "grid_keys": "lA,lB", "selected_on": "grid (the full semi-orthogonal map)",
                        "grid": srt(grid), "grid_train_span": srt(grid_span), **(extra or {})})

    LA, LB = KA.shape[1], KB.shape[1]
    score([(a, b) for a in COARSE_A for b in COARSE_B if a < LA and b < LB]); save()
    for _ in range(6):                                   # +-2 local refinement until the best cell is interior
        ba, bb = best()
        before = len(grid)
        score([(a, b) for a in range(max(0, ba - 2), min(LA, ba + 3))
               for b in range(max(0, bb - 2), min(LB, bb + 3))]); save()
        if len(grid) == before:
            break
    ba, bb = best()
    curve = prev.get("self_swap_curve_by_lB")
    if not curve:
        # the self-swap curve over the recipient's layers, same validation pairs
        jobs = [(r, lb, np.asarray(KB[d, lb], np.float32)) for lb in range(LB) for d, r in vp]
        gens = run_rows(rlm, recipient, rows, jobs)
        curve = [sum(F.says(x, rows[d]["answer"]) for x, d in
                     zip(gens[lb * len(vp):(lb + 1) * len(vp)], d_ids)) / len(vp) for lb in range(LB)]
    save({"chosen": {"lA": ba, "lB": bb, "val_transfer": grid[f"{ba},{bb}"]},
          "self_swap_curve_by_lB": curve, "provenance": provenance([donor, recipient])})
    print("chosen", ba, bb, grid[f"{ba},{bb}"])


def stage_evaluate(donor, recipient):
    rows, KA, KB, idx, pairs = setup(donor, recipient)
    out_dir = RES / f"{donor}__to__{recipient}"
    sel = load(out_dir / "selection.json")["chosen"]
    la, lb = sel["lA"], sel["lB"]
    rlm = rlm_for(recipient)
    tp = pairs["test"]
    d_ids, r_ids = [p[0] for p in tp], [p[1] for p in tp]
    A_tr, B_tr = layer_keys(KA, idx["train"], la), layer_keys(KB, idx["train"], lb)
    A_d = layer_keys(KA, d_ids, la)
    ca, cb = align.centre(A_tr), align.centre(B_tr)
    m = align.fit_centred(ca, cb)
    rng = np.random.default_rng(1)
    d_b, d_a = m.R.shape
    arms = {   # name: (vectors or None, where the arm should sit)
        "treatment": (m.apply(A_d), "the claim: well above every control"),
        "self_swap": (layer_keys(KB, d_ids, lb), "ceiling: the recipient's own key for the donor subject"),
        "no_patch": (None, "null: transfer ~0, recipient answer kept ~1"),
        "identity": (layer_keys(KB, r_ids, lb), "null: the recipient's own key for its own subject; must match no_patch"),
        "random_rotation_0": (m.with_rotation(align.random_semi_orthogonal(d_b, d_a, rng)).apply(A_d), "null"),
        "random_rotation_1": (m.with_rotation(align.random_semi_orthogonal(d_b, d_a, rng)).apply(A_d), "null"),
        "shuffled_pairing": (align.fit_map(A_tr[rng.permutation(len(A_tr))], B_tr).apply(A_d), "null"),
        "mean_only": (np.repeat(m.mu_b[None].astype(np.float32), len(tp), 0), "null: the recipient's mean key, no donor information"),
        "treatment_train_span": (align.fit_centred(ca, cb, train_span_only=True).apply(A_d),
                                 "exploratory: the map without the SVD's arbitrary off-span completion"),
        "scale_reciprocal": (m.with_scale(m.s_reciprocal).apply(A_d), "exploratory: the scale as the post's equation was extracted"),
    }
    jobs, names = [], list(arms)
    for n in names:
        v = arms[n][0]
        jobs += [(r, -1 if v is None else lb, None if v is None else v[k]) for k, r in enumerate(r_ids)]
    gens = run_rows(rlm, recipient, rows, jobs)
    N = len(tp)
    summary, per_row = {}, [{"donor": rows[d]["id"], "recipient": rows[r]["id"],
                             "relation": rows[d]["relation"], "donor_answer": rows[d]["answer"],
                             "recipient_answer": rows[r]["answer"]} for d, r in tp]
    for a, n in enumerate(names):
        g = gens[a * N:(a + 1) * N]
        hit = [F.says(x, rows[d]["answer"]) for x, d in zip(g, d_ids)]
        kept = [F.says(x, rows[r]["answer"]) for x, r in zip(g, r_ids)]
        lo, hi = align.wilson(sum(hit), N)
        summary[n] = {"expected": arms[n][1], "n": N, "transfer": sum(hit) / N,
                      "transfer_ci95": [round(lo, 4), round(hi, 4)],
                      "recipient_answer_kept": sum(kept) / N}
        for row, x in zip(per_row, g):
            row[n] = x
    rels = sorted({r["relation"] for r in per_row})
    by_rel = {rel: {"n": sum(r["relation"] == rel for r in per_row),
                    **{n: round(sum(F.says(r[n], r["donor_answer"]) for r in per_row if r["relation"] == rel)
                               / sum(r["relation"] == rel for r in per_row), 4)
                       for n in ("treatment", "self_swap", "random_rotation_0", "mean_only")}}
              for rel in rels}
    dump(out_dir / "test_summary.json", {
        "donor": MODELS[donor], "recipient": MODELS[recipient], "lA": la, "lB": lb,
        "layer_convention": "index l = output of decoder block l (0-based)",
        "n_train": len(idx["train"]), "n_test_pairs": N, "d_donor": d_a, "d_recipient": d_b,
        "n_minus_1_lt_d": len(idx["train"]) - 1 < min(d_a, d_b),
        "off_train_span_energy": {"donor_test_keys": align.off_span_energy(ca, A_d),
                                  "recipient_test_keys": align.off_span_energy(cb, layer_keys(KB, d_ids, lb))},
        "scale_s": m.s, "scale_reciprocal": m.s_reciprocal,
        "success": f"greedy {GEN_TOKENS}-token continuation begins with the donor's answer",
        "arms": summary, "by_relation": by_rel, "provenance": provenance([donor, recipient])})
    F.write_jsonl(out_dir / "test_rows.jsonl", per_row)
    for n in names:
        print(f"{n:20s} transfer {summary[n]['transfer']:.4f} {summary[n]['transfer_ci95']} "
              f"kept {summary[n]['recipient_answer_kept']:.4f}")


if __name__ == "__main__":
    stage, args = sys.argv[1], sys.argv[2:]
    globals()[f"stage_{stage}"](*args)
