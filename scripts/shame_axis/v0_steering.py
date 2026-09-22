"""Hour 62b: steer the paper's S2 pain direction at L12 and read hour 56's six openers.

Pre-registered in `research/shame-axis/notes/v0_correction_shape_prereg.md`, "Part 2, hour 62b".
That section is the spec; this file implements it and nothing else.

  direction   their S2 pain vector rebuilt at their steering layer L12 (`build_vectors`, the
              `final_token` extraction -- the one the replication used at L12), unit-normalised
  items       v0: all 20 gaslighting (A), 20 repeated_rejection (B), 20 casual_chat (N)
  dose        shift = alpha * ||h_bar|| * v_hat, added at the output of block 12 at every position,
              ||h_bar|| = mean L2 norm of the block-12 output at the LAST token over the 60 items
  arms        no_patch (alpha 0) | treatment x4 | random: 3 seeded unit directions x4 |
              pass_through: the treatment shift at the output of the FINAL block (41) x4
              -> 21 cells per item
  statistic   d_ritual = ritual(cell) - ritual(no_patch), paired within item

Rendering. `render_chat` returns text that already begins with <bos>; the asserted scorer encodes
with `add_special_tokens=True`, which would prepend a SECOND <bos>. The prereg names the paper's
token path (asserted token-identical with add_special_tokens=False in painaxis_scenarios.py), and
the scale and the direction were both extracted on single-<bos> input, so the leading <bos> is
stripped from the text before it is handed to the scorer and the resulting ids are asserted equal
to the paper's. A diagnostic cell per item (`no_patch_double_bos`, outside the 21) scores the
double-<bos> form too, which is what hour 62a's scorer submits; it is how the run is compared to
62a without pretending the two readouts are the same.

Usage:  python scripts/shame_axis/v0_steering.py prep      # either venv; reads the shards on disk
        python scripts/shame_axis/v0_steering.py score     # .venv312, NDIF, resumable
        python scripts/shame_axis/v0_steering.py report
"""
from __future__ import annotations

import fcntl
from collections import Counter
import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))

from lsx.shame_axis import stimuli  # noqa: E402
from conscription_openers import OPENERS, ritual  # noqa: E402

VERSION = "v0"
MODEL = "google/gemma-2-9b-it"
N_BLOCKS = 42
D_MODEL = 3584
PATCH_LAYER = 12          # theirs (steering CSV filenames); not selected here
FINAL_LAYER = N_BLOCKS - 1
ALPHAS = (-0.2, -0.1, 0.1, 0.2)
N_RANDOM = 3
RANDOM_SEED = 62_062       # fixed before any number existed; the directions are the same for all items
SIGNFLIP_DRAWS = 10_000
SIGNFLIP_SEED = 20260922
TIERS = {"A": "gaslighting", "B": "repeated_rejection", "N": "casual_chat"}
TIER_OF = {c: t for t, c in TIERS.items()}
ARMS = ("no_patch", "treatment", "random", "pass_through")
TREAT_DIR = "pain_s2_L12"
# error text that marks the deployment, not this code: retried without limit until the deadline
TRANSIENT = ("OutOfMemory", "Timeout", "Transport", "Connect", "502", "503", "504", "500",
             "RemoteProtocol", "ReadError", "queue", "Queue")

# r2 (INSTRUMENTS §7 fixed readout): the same direction and prep as r1, read from the r1 folder;
# new cells in their own folder; six openers per job, fixed; r1's two readout diagnostics
# (chunk 3, double <bos>) are not re-run -- both effects are measured in readout_fix/.
READOUT = "r2"
R1 = ROOT / "research/shame-axis/results/v0_steering"
OUT = ROOT / f"research/shame-axis/results/v0_steering_{READOUT}"
CELLS = OUT / "cells.jsonl"
PREP = R1 / "prep.json"
DIRECTION = R1 / "direction_s2_L12_unit.npy"      # 14 KB float32; not a stack
CHUNKS = (6,)                                      # r1 fell back (6, 3, 1) on OOM
PA = ROOT / "research/shame-axis/results/painaxis_scenarios"
SHARDS = PA / "shards"


# ------------------------------------------------------------------------------ the design
def random_directions(d: int = D_MODEL, n: int = N_RANDOM, seed: int = RANDOM_SEED) -> np.ndarray:
    """n unit directions drawn from N(0, I_d), seeded; float64 [n, d]."""
    r = np.random.default_rng(seed).standard_normal((n, d))
    return r / np.linalg.norm(r, axis=1, keepdims=True)


def shift_scale(alpha: float, hbar_norm: float) -> float:
    """The scalar that multiplies a UNIT direction: ||shift|| = |alpha| * ||h_bar||."""
    return float(alpha) * float(hbar_norm)


def enumerate_cells(item_ids) -> list[dict]:
    """The 21 cells per item, in the order they are run (no_patch first: it is every other cell's
    `base`). Cell key = (item, arm, alpha, dir)."""
    cells = []
    for it in item_ids:
        cells.append({"item": it, "arm": "no_patch", "alpha": 0.0, "dir": None, "layer": None})
        for a in ALPHAS:
            cells.append({"item": it, "arm": "treatment", "alpha": a, "dir": TREAT_DIR,
                          "layer": PATCH_LAYER})
        for k in range(N_RANDOM):
            for a in ALPHAS:
                cells.append({"item": it, "arm": "random", "alpha": a, "dir": f"rand{k}",
                              "layer": PATCH_LAYER})
        for a in ALPHAS:
            cells.append({"item": it, "arm": "pass_through", "alpha": a, "dir": TREAT_DIR,
                          "layer": FINAL_LAYER})
    return cells


def cell_key(c: dict) -> tuple:
    return (c["item"], c["arm"], float(c["alpha"]), c["dir"])


def total_mass(lp) -> float:
    lp = np.asarray(lp, dtype=np.float64)
    m = lp.max()
    return float(m + np.log(np.exp(lp - m).sum()))


def select_items(items: list[dict]) -> list[dict]:
    from painaxis_scenarios import validate_candidates
    bad = {i for i, _ in validate_candidates(items)}
    keep = [it for it in items if it["category"] in TIER_OF and it["id"] not in bad]
    return keep, sorted(b for b in bad if any(it["id"] == b and it["category"] in TIER_OF
                                              for it in items))


# ------------------------------------------------------------------------------ prep (offline)
def _load_layer(prefix: str, n: int, layer: int, key: str = "final_token") -> np.ndarray:
    parts = []
    for s0 in range(0, n, 100):
        z = np.load(SHARDS / f"{prefix}_{s0:04d}.npz")
        a = z[key]
        if a.shape[1] != N_BLOCKS:
            raise SystemExit(f"{prefix}_{s0:04d}: {a.shape[1]} layers, expected {N_BLOCKS}")
        parts.append(a[:, layer, :].astype(np.float64))
    out = np.concatenate(parts)
    if out.shape[0] != n:
        raise SystemExit(f"{prefix}: {out.shape[0]} rows, expected {n}")
    return out


def prep() -> None:
    """Direction and scale, both from the stacks on disk. Shard layer index i is the output of
    block i (painaxis_scenarios_analyze.py prepends the embedding as its index 0; the raw shard
    does not). That convention is checked here, not assumed: the recipe rebuilt at shard index 37
    must reproduce their published L37 vectors."""
    import painaxis_scenarios as S
    OUT.mkdir(parents=True, exist_ok=True)
    ds = json.loads(S.CORE.read_text())["datasets"]
    core_cats = {n: [s["category"] for s in ds[n]["sentences"]] for n in S.S_SETS}

    def vecs_at(L):
        ca = {n: _load_layer(f"core_{n}", len(ds[n]["sentences"]), L) for n in S.S_SETS}
        return S.build_vectors(ca, core_cats, {})     # control sets feed only the control vectors

    info = {"extraction": "final_token", "patch_layer": PATCH_LAYER,
            "vector_source": "painaxis_scenarios.build_vectors on core_{S1,S2,ControlSupplement}_1P "
                             "shards, final_token, shard index 12 = output of block 12"}

    # --- index-convention check at their extraction layer against their published vectors ----
    pub = pathlib.Path("/tmp/claude-0/Pain-axis/results/3.2_pain_vectors/pain_vectors/"
                       "Gemma_2_9B_instruct/pain_vectors.pt")
    v37 = vecs_at(37)
    if pub.exists():
        import torch
        tv = torch.load(pub, map_location="cpu", weights_only=False)
        c = {k: float(S.unit(v37[k]) @ S.unit(tv[k].float().numpy().astype(np.float64)))
             for k in ("s1_pain_vector", "s2_pain_vector")}
        info["index_check_L37_cos_vs_published"] = c
        info["published_layer"] = int(tv.get("layer", -1)) if hasattr(tv, "get") else None
        if min(c.values()) < 0.999:
            raise SystemExit(f"shard index 37 does not reproduce their L37 vectors: {c}")
        pub_s2 = tv["s2_pain_vector"].float().numpy().astype(np.float64)
    else:
        info["index_check_L37_cos_vs_published"] = "published pain_vectors.pt not on disk"
        pub_s2 = None

    v12 = vecs_at(PATCH_LAYER)
    s2, s1 = v12["s2_pain_vector"], v12["s1_pain_vector"]
    u = S.unit(s2)
    info["s2_L12_raw_norm"] = float(np.linalg.norm(s2))
    info["s1_L12_raw_norm"] = float(np.linalg.norm(s1))
    info["cos_s2_s1_L12"] = float(u @ S.unit(s1))
    info["replication_saved_L12_vector"] = False   # painaxis_scenarios never writes its vectors
    if pub_s2 is not None:
        # informational: their steering run injected the L37 vector AT L12 (01_steering_ladder.py
        # loads final_token/pain_vectors.pt); the prereg specifies the L12 rebuild instead.
        info["cos_s2_L12_vs_their_published_s2_L37"] = float(u @ S.unit(pub_s2))
        info["their_published_s2_L37_raw_norm"] = float(np.linalg.norm(pub_s2))

    # --- the scale: ||h_bar|| over the 60 items, from the scenario shards ---------------------
    items, excluded = select_items(stimuli.load(VERSION))
    order = json.loads((PA / "scenario_order.json").read_text())
    src = {c["id"]: c for c in json.loads(S.SCEN.read_text())}
    for it in items:
        if src[it["id"]]["text"] != it["text"]:
            raise SystemExit(f"{it['id']}: v0 text differs from the text the shards were extracted on")
    rows = [order.index(it["id"]) for it in items]
    scen = _load_layer("scen_chat", len(order), PATCH_LAYER)
    h = scen[rows]
    norms = np.linalg.norm(h, axis=1)
    rand = random_directions()
    info.update({
        "hbar_norm": float(norms.mean()), "hbar_source": "scen_chat shards on disk, final_token, "
        "shard index 12, rows mapped by scenario_order.json",
        "hbar_norm_sd": float(norms.std(ddof=1)), "hbar_norm_min": float(norms.min()),
        "hbar_norm_max": float(norms.max()), "n_items": len(items),
        "excluded_by_validator": excluded,
        "hbar_norm_by_tier": {t: float(norms[[i for i, it in enumerate(items)
                                              if it["category"] == c]].mean())
                              for t, c in TIERS.items()},
        "proj_on_direction_mean": float((h @ u).mean()),
        "random_seed": RANDOM_SEED,
        "random_cos_to_direction": [float(r @ u) for r in rand],
        "random_pairwise_cos": [float(rand[i] @ rand[j]) for i in range(N_RANDOM)
                                for j in range(i + 1, N_RANDOM)],
        "shift_norms": {str(a): abs(shift_scale(a, norms.mean())) for a in ALPHAS},
        "direction_sha": _sha(u.astype(np.float32)),
    })
    np.save(DIRECTION, u.astype(np.float32))
    PREP.write_text(json.dumps(info, indent=2))
    print(json.dumps(info, indent=2))


def _sha(a: np.ndarray) -> str:
    import hashlib
    return hashlib.sha256(np.ascontiguousarray(a).tobytes()).hexdigest()[:16]


# ------------------------------------------------------------------------------ scoring (NDIF)
class DidNotMove(Exception):
    pass


class H36Signature(SystemExit):
    pass


# The per-cell row-0-only adjudication aborts only when STRICT_H36 is set. It was the rule for
# the first ~450 cells; it proved ill-conditioned on this readout (a chunk-3 patched score is
# compared against a chunk-6 base, and log-probs are quantised to 1/32), so the batch-row bug is
# instead excluded once per configuration at the residual level by the library's own
# `assert_patch_reaches_batch` (see `_reach_checks`), and per-cell shortfalls are recorded.
STRICT_H36 = False


def _moved_count(msg: str) -> tuple[int, int]:
    import re
    m = re.search(r"patch moved (\d+)/(\d+) sequences", msg)
    return (int(m.group(1)), int(m.group(2))) if m else (-1, -1)


def _is_h36(msg: str) -> bool:
    """h36 wrote the patch into batch ROW 0 only. Its signature in a chunk of >= 3 is therefore
    'row 0 moved and nothing else'. A chunk where some other subset failed to move -- on this
    readout, quantised log-probs pinned at 0.0 or moving by less than one bf16 step -- is not it."""
    import re
    m, b = _moved_count(msg)
    d = re.search(r"deltas \[([^\]]*)\]", msg)
    if b < 3 or d is None:
        return False
    deltas = [float(x) for x in d.group(1).split(",")]
    moved = [j for j, x in enumerate(deltas) if abs(x) > 1e-6]
    return moved == [0]


def _score(rlm, lead, vec=None, scale=0.0, layer=None, base=None):
    """62a's `_score_openers`, with the patch passed through and `base` sliced per chunk so the
    moved-candidates assertion runs on every chunk. Returns (logps, chunk, shortfalls).

    The library assertion is kept as is. When it fires, the chunk's message is parsed: a chunk of
    >= 3 in which at most one row moved is the h34/h36 signature and aborts the run; anything else
    (on this readout: a candidate whose quantised log-prob did not change, typically one pinned at
    exactly 0.0) is recorded as a shortfall and that chunk is re-scored without `base` so the cell
    still has its numbers."""
    from lsx.core import checks
    from lsx.core.remote import asserted_remote_patched_logprob
    for chunk in CHUNKS:
        try:
            parts, short = [], []
            for i in range(0, len(OPENERS), chunk):
                cands = OPENERS[i:i + chunk]
                if vec is None:
                    parts.append(asserted_remote_patched_logprob(rlm, lead, cands))
                    continue
                kw = {"patch_layer": layer, "patch_vec": vec, "scale": scale}
                try:
                    parts.append(asserted_remote_patched_logprob(
                        rlm, lead, cands, base=np.asarray(base)[i:i + chunk], **kw))
                except checks.MovedCandidates as e:
                    m, b = _moved_count(str(e))
                    batch1 = None
                    if _is_h36(str(e)):
                        # Row 0 alone moved. At batch 1 a batch-row bug cannot exist, so score
                        # each candidate alone, patched and unpatched: if the same rows stay
                        # unmoved there, it is the readout's grain, not h36.
                        b1p = np.array([asserted_remote_patched_logprob(rlm, lead, [c], **kw)[0]
                                        for c in cands])
                        b1u = np.array([asserted_remote_patched_logprob(rlm, lead, [c])[0]
                                        for c in cands])
                        still = [j for j in range(len(cands)) if abs(b1p[j] - b1u[j]) <= 1e-6]
                        batch1 = {"patched": b1p.tolist(), "unpatched": b1u.tolist(),
                                  "unmoved_rows_at_batch1": still}
                        batch1["rows_that_move_at_batch1"] = [
                            j for j in range(1, len(cands)) if j not in still]
                        if STRICT_H36 and batch1["rows_that_move_at_batch1"]:
                            raise H36Signature(f"h36 signature on chunk {i}, and at batch 1 rows "
                                               f"{batch1['rows_that_move_at_batch1']} DO move: {e}")
                    sc = asserted_remote_patched_logprob(rlm, lead, cands, **kw)
                    parts.append(sc)
                    short.append({"chunk_start": i, "moved": m, "batch": b,
                                  "unmoved": [OPENERS[i + j] for j in range(len(cands))
                                              if abs(sc[j] - base[i + j]) <= 1e-6],
                                  "msg": str(e)[:300], "batch1_check": batch1})
            return np.concatenate(parts), chunk, short
        except Exception as e:                       # remote errors arrive wrapped
            if "OutOfMemory" not in str(e) or chunk == CHUNKS[-1]:
                raise                                # r2: the runner's transient loop retries
            print(f"    OOM at chunk {chunk}; retrying smaller", flush=True)


def _append(row: dict) -> None:
    with CELLS.open("a") as fh:
        fcntl.flock(fh, fcntl.LOCK_EX)
        fh.write(json.dumps(row) + "\n")
        fh.flush()
        fcntl.flock(fh, fcntl.LOCK_UN)


def _load_cells() -> list[dict]:
    if not CELLS.exists():
        return []
    return [json.loads(l) for l in CELLS.read_text().splitlines() if l.strip()]


def _lead(it, tok):
    """render_chat text with its leading <bos> stripped, asserted to encode (with the scorer's
    add_special_tokens=True) to exactly the paper's token path."""
    from painaxis_scenarios import render_chat
    text = render_chat(it, tok)
    if not text.startswith(tok.bos_token):
        raise SystemExit(f"{it['id']}: rendered text does not begin with {tok.bos_token!r}")
    lead = text[len(tok.bos_token):]
    theirs = tok(text, add_special_tokens=False)["input_ids"]
    ours = tok(lead, add_special_tokens=True)["input_ids"]
    if list(theirs) != list(ours) or ours.count(tok.bos_token_id) != 1:
        raise SystemExit(f"{it['id']}: stripped lead does not tokenise to the paper's path")
    for c in OPENERS:           # the lead's tokens are a prefix of lead+opener's (n_lead is valid)
        full = tok(lead + c, add_special_tokens=True)["input_ids"]
        if full[:len(ours)] != ours:
            raise SystemExit(f"{it['id']}: lead tokens are not a prefix of lead+{c!r}")
    return lead, text


def _remote_scale_check(rlm, it, lead, prep_info) -> dict:
    """One job: the remote block-12 output at the last token vs the shard row. Checks that the
    patch layer index is the layer the vector and the scale were read at."""
    from lsx.core.remote import remote_residuals
    import painaxis_scenarios as S
    order = json.loads((PA / "scenario_order.json").read_text())
    shard = _load_layer("scen_chat", len(order), PATCH_LAYER)[order.index(it["id"])]
    r = remote_residuals(rlm, [lead], PATCH_LAYER)[0, -1].astype(np.float64)
    out = {"item": it["id"], "cos": float(S.unit(r) @ S.unit(shard)),
           "remote_norm": float(np.linalg.norm(r)), "shard_norm": float(np.linalg.norm(shard))}
    if out["cos"] < 0.999:
        raise SystemExit(f"remote L12 residual does not match the shard: {out}")
    return out


def _reach_checks(rlm, it, dirs, hbar) -> list[dict]:
    """h36 excluded at the residual level, where the readout's grain does not apply: for each
    patch layer x (treatment, one random) direction x chunk size used, the library's
    `assert_patch_reaches_batch` runs the patch through the same by-type block-output write on a
    padded batch of lead+opener texts and requires EVERY row to move (atol 1e-3). Smallest dose."""
    from lsx.core.remote import assert_patch_reaches_batch
    lead, _ = _lead(it, rlm.tok)
    out = []
    for layer in (PATCH_LAYER, FINAL_LAYER):
        for d in (TREAT_DIR, "rand0"):
            for chunk in (6, 3):
                texts = [lead + o for o in OPENERS[:chunk]]
                for attempt in range(3):
                    try:
                        n = assert_patch_reaches_batch(rlm, texts, layer, dirs[d],
                                                       scale=shift_scale(0.1, hbar))
                        out.append({"layer": layer, "dir": d, "chunk": chunk, "rows_moved": int(n),
                                    "batch": chunk, "alpha": 0.1})
                        break
                    except Exception as e:  # noqa: BLE001
                        if "OutOfMemory" not in str(e):
                            raise
                        time.sleep(20 * (attempt + 1))
                else:
                    out.append({"layer": layer, "dir": d, "chunk": chunk, "rows_moved": None,
                                "batch": chunk, "alpha": 0.1, "skipped": "OOM x3"})
    if not any(r["rows_moved"] for r in out if r["layer"] == PATCH_LAYER) or \
            not any(r["rows_moved"] for r in out if r["layer"] == FINAL_LAYER):
        raise TimeoutError("reach checks could not complete a single batch per layer (OOM)")
    return out


def score(shard: str | None = None, deadline_h: float = 6.0) -> None:
    from lsx.core import checks
    from lsx.core.remote import RemoteLM

    info = json.loads(PREP.read_text())
    u = np.load(DIRECTION).astype(np.float64)
    if _sha(u.astype(np.float32)) != info["direction_sha"]:
        raise SystemExit("direction file does not match prep.json")
    rand = random_directions()
    dirs = {TREAT_DIR: u, **{f"rand{k}": rand[k] for k in range(N_RANDOM)}}
    hbar = info["hbar_norm"]

    items, _ = select_items(stimuli.load(VERSION))
    if shard:
        k, n = (int(x) for x in shard.split("/"))
        items = items[k::n]
    by_id = {it["id"]: it for it in items}
    OUT.mkdir(parents=True, exist_ok=True)
    meta_path = OUT / f"score_meta{'' if not shard else '_' + shard.replace('/', 'of')}.json"
    meta = json.loads(meta_path.read_text()) if meta_path.exists() else {
        "retries": 0, "errors": [], "started": time.time(), "sessions": []}
    meta["sessions"].append({"start": time.time()})
    t_end = time.time() + deadline_h * 3600

    rlm = None
    streak, last_sig = 0, None
    while True:
        try:
            if rlm is None:
                rlm = RemoteLM(MODEL)
                checks.assert_padding_convention(rlm.padding_side, "auto")
                if len(rlm.blocks) != N_BLOCKS:
                    raise SystemExit(f"expected {N_BLOCKS} blocks, got {len(rlm.blocks)}")
                if "reach_checks" not in meta:
                    meta["reach_checks"] = _reach_checks(rlm, items[0], dirs, hbar)
                    print("reach checks:", meta["reach_checks"], flush=True)
                    meta_path.write_text(json.dumps(meta, indent=2))
                if "scale_check" not in meta:
                    first = items[0]
                    meta["scale_check"] = _remote_scale_check(rlm, first, _lead(first, rlm.tok)[0], info)
                    print("scale check:", meta["scale_check"], flush=True)
                    meta_path.write_text(json.dumps(meta, indent=2))
            done = {cell_key(c): c for c in _load_cells()}
            todo = [c for c in enumerate_cells(list(by_id)) if cell_key(c) not in done]
            diag_todo = [] if READOUT == "r2" else [
                i for i in by_id if (i, "no_patch_double_bos", 0.0, None) not in done]
            print(f"{len(todo)} cells + {len(diag_todo)} diagnostics left", flush=True)
            for c in todo:
                if time.time() > t_end:
                    raise TimeoutError("deadline")
                it = by_id[c["item"]]
                lead, _ = _lead(it, rlm.tok)
                row = {"version": VERSION, "item": it["id"], "sha": stimuli.item_sha(it),
                       "category": it["category"], "tier": TIER_OF[it["category"]],
                       "arm": c["arm"], "alpha": c["alpha"], "dir": c["dir"], "layer": c["layer"]}
                t0 = time.time()
                if c["arm"] == "no_patch":
                    lp, chunk, _ = _score(rlm, lead)
                    row["moved"] = None
                else:
                    base = np.asarray(done[(it["id"], "no_patch", 0.0, None)]["logp"])
                    s = shift_scale(c["alpha"], hbar)
                    lp, chunk, short = _score(rlm, lead, dirs[c["dir"]], s, c["layer"], base)
                    row["moved"] = "all" if not short else "did_not_move_beyond_atol"
                    if short:
                        row["shortfall"] = short
                    row["max_abs_dlogp"] = float(np.abs(lp - base).max())
                    row["min_abs_dlogp"] = float(np.abs(lp - base).min())
                    row["shift_norm"] = abs(s)
                row.update({"logp": [float(x) for x in lp], "ritual": ritual(lp),
                            "mass": total_mass(lp), "chunk": chunk, "secs": time.time() - t0})
                _append(row)
                streak, last_sig = 0, None
                done[cell_key(c)] = row
                print(f"  {it['id']:22s} {c['arm']:12s} {c['alpha']:+.1f} {str(c['dir']):11s} "
                      f"{row['secs']:5.1f}s ritual {row['ritual']:+7.3f}", flush=True)
            for i in [i for i in by_id if READOUT != "r2" and (i, "no_patch_chunk3", 0.0, None) not in done]:
                it = by_id[i]
                lead, _ = _lead(it, rlm.tok)
                from lsx.core.remote import asserted_remote_patched_logprob
                lp = np.concatenate([asserted_remote_patched_logprob(rlm, lead, OPENERS[j:j + 3])
                                     for j in (0, 3)])
                _append({"version": VERSION, "item": i, "sha": stimuli.item_sha(it),
                         "category": it["category"], "tier": TIER_OF[it["category"]],
                         "arm": "no_patch_chunk3", "alpha": 0.0, "dir": None, "layer": None,
                         "logp": [float(x) for x in lp], "ritual": ritual(lp),
                         "mass": total_mass(lp), "chunk": 3})
                print(f"  {i:22s} no_patch_chunk3 ritual {ritual(lp):+7.3f}", flush=True)
            for i in diag_todo:
                it = by_id[i]
                _, text = _lead(it, rlm.tok)
                lp, chunk, _ = _score(rlm, text)              # double <bos>: what 62a submits
                _append({"version": VERSION, "item": i, "sha": stimuli.item_sha(it),
                         "category": it["category"], "tier": TIER_OF[it["category"]],
                         "arm": "no_patch_double_bos", "alpha": 0.0, "dir": None, "layer": None,
                         "logp": [float(x) for x in lp], "ritual": ritual(lp),
                         "mass": total_mass(lp), "chunk": chunk})
                print(f"  {i:22s} no_patch_double_bos ritual {ritual(lp):+7.3f}", flush=True)
            break
        except SystemExit:
            raise
        except TimeoutError as e:
            if str(e) == "deadline" or time.time() > t_end:
                print("DEADLINE REACHED", flush=True)
                break
            _backoff(meta, meta_path, e)
        except Exception as e:  # noqa: BLE001 -- the deployment OOMs under a co-tenant; retry
            if time.time() > t_end:
                print("DEADLINE REACHED", flush=True)
                break
            sig = f"{type(e).__name__}:{str(e)[:120]}"
            streak = streak + 1 if sig == last_sig else 1
            last_sig = sig
            transient = any(k in str(e) + type(e).__name__ for k in TRANSIENT)
            if not transient and streak >= 3:
                meta["errors"].append({"t": time.time(), "fatal": sig})
                meta_path.write_text(json.dumps(meta, indent=2))
                raise
            _backoff(meta, meta_path, e, streak)
    meta["sessions"][-1]["end"] = time.time()
    meta_path.write_text(json.dumps(meta, indent=2))
    print("SCORING DONE", flush=True)


def _backoff(meta, meta_path, e, streak: int = 1):
    """Wait grows with the CURRENT run of consecutive errors, not the cumulative count."""
    meta["retries"] += 1
    wait = min(30 * 2 ** min(streak - 1, 3), 240)
    meta["errors"].append({"t": time.time(), "type": type(e).__name__, "msg": str(e)[:300],
                           "wait": wait})
    meta_path.write_text(json.dumps(meta, indent=2))
    print(f"  ERROR {type(e).__name__}: {str(e)[:200]} -- retry {meta['retries']} in {wait}s",
          flush=True)
    time.sleep(wait)


# ------------------------------------------------------------------------------ report
def signflip(d: np.ndarray, rng, draws: int = SIGNFLIP_DRAWS) -> dict:
    """Sign-flip null for a paired mean: the band is the 2.5/97.5 percentiles of the null mean."""
    d = np.asarray(d, dtype=np.float64)
    s = rng.choice([-1.0, 1.0], size=(draws, d.size))
    null = (s * d).mean(axis=1)
    obs = float(d.mean())
    return {"mean": obs, "n": int(d.size), "band_lo": float(np.percentile(null, 2.5)),
            "band_hi": float(np.percentile(null, 97.5)),
            "p": float((np.abs(null) >= abs(obs) - 1e-12).mean())}


def verdict_for(treat: dict, rand_means: dict, pass_mean: dict) -> dict:
    """Per dose: sign of alpha, |treatment| > max |random mean| at that |alpha|, |treatment| >
    |pass-through|. The tier reads "causal on this readout" only if all three hold at every dose,
    "correlate, not cause" if treatment sits inside the random band at every dose, else "mixed".
    `treat` and `pass_mean`: {alpha: mean d_ritual}; `rand_means`: {|alpha|: [6 means]}."""
    per = {}
    for a, m in treat.items():
        rmax = max(abs(x) for x in rand_means[abs(a)])
        per[a] = {"treatment": m, "random_max_abs": rmax, "pass_through": pass_mean[a],
                  "sign_ok": bool(np.sign(m) == np.sign(a)), "beats_random": bool(abs(m) > rmax),
                  "beats_pass_through": bool(abs(m) > abs(pass_mean[a]))}
        per[a]["all"] = per[a]["sign_ok"] and per[a]["beats_random"] and per[a]["beats_pass_through"]
    if all(p["all"] for p in per.values()):
        v = "causal on this readout"
    elif not any(p["beats_random"] for p in per.values()):
        v = "correlate, not cause"
    else:
        v = "mixed"
    return {"verdict": v, "per_dose": per}


def report(matched_chunk: bool = False) -> None:
    """`matched_chunk`: sensitivity, not the pre-registered analysis -- keep only cells scored at
    the same opener chunk size as their item's no-patch cell, so no paired difference carries
    the chunking floor. Writes summary_chunk_matched.json instead of summary.json."""
    rows = _load_cells()
    live = {it["id"]: stimuli.item_sha(it) for it in stimuli.load(VERSION)}
    stale = [r["item"] for r in rows if live.get(r["item"]) != r["sha"]]
    if stale:
        raise SystemExit(f"{len(stale)} rows were scored on text that no longer matches {VERSION}")
    info = json.loads(PREP.read_text())
    rng = np.random.default_rng(SIGNFLIP_SEED)
    base = {r["item"]: r for r in rows if r["arm"] == "no_patch"}
    cells = [r for r in rows if r["arm"] in ARMS and r["arm"] != "no_patch" and r["item"] in base]
    if matched_chunk:
        n0 = len(cells)
        cells = [r for r in cells if r["chunk"] == base[r["item"]]["chunk"]]
        print(f"CHUNK-MATCHED SENSITIVITY: kept {len(cells)} of {n0} patched cells")
    n_expected = 21 * info["n_items"]
    n_have = sum(1 for r in rows if r["arm"] in ARMS)
    out = {"n_cells": n_have, "n_expected": n_expected, "complete": n_have == n_expected,
           "prep": info}
    print(f"\n{n_have}/{n_expected} battery cells; no-patch on {len(base)} items\n")

    def d(r, key="ritual"):
        return r[key] - base[r["item"]][key]

    def group(tier, arm, alpha, dr=None, key="ritual"):
        g = {r["item"]: d(r, key) for r in cells if r["tier"] == tier and r["arm"] == arm
             and abs(r["alpha"] - alpha) < 1e-9 and (dr is None or r["dir"] == dr)}
        return g

    # --- no-patch level ------------------------------------------------------------------
    out["no_patch"] = {}
    print("NO-PATCH  ritual level (single <bos>)")
    for t in TIERS:
        v = np.array([r["ritual"] for r in base.values() if r["tier"] == t])
        m = np.array([r["mass"] for r in base.values() if r["tier"] == t])
        if v.size:
            out["no_patch"][t] = {"n": int(v.size), "ritual_mean": float(v.mean()),
                                  "ritual_sd": float(v.std(ddof=1)) if v.size > 1 else None,
                                  "mass_mean": float(m.mean())}
            print(f"  {t}  n {v.size:2d}  ritual {v.mean():+7.3f}  sd {v.std(ddof=1) if v.size > 1 else 0:6.3f}"
                  f"  mass {m.mean():+8.3f}")

    # --- main table ------------------------------------------------------------------------
    print("\nD_RITUAL  mean over items, 95% sign-flip band of the null mean, p")
    print(f"  {'tier':4s} {'arm':13s} {'dir':11s} {'alpha':>6s} {'n':>3s} {'mean':>8s} "
          f"{'band':>19s} {'p':>7s}")
    tab = []
    for t in TIERS:
        for arm, dlist in (("treatment", [TREAT_DIR]), ("random", [f"rand{k}" for k in range(N_RANDOM)]),
                           ("pass_through", [TREAT_DIR])):
            for dr in dlist:
                for a in ALPHAS:
                    g = group(t, arm, a, dr)
                    if not g:
                        continue
                    sf = signflip(np.array(list(g.values())), rng)
                    tab.append({"tier": t, "arm": arm, "dir": dr, "alpha": a, **sf})
                    print(f"  {t:4s} {arm:13s} {dr:11s} {a:+6.1f} {sf['n']:3d} {sf['mean']:+8.3f} "
                          f"[{sf['band_lo']:+7.3f},{sf['band_hi']:+7.3f}] {sf['p']:7.4f}")
    out["d_ritual"] = tab

    # --- random band ----------------------------------------------------------------------
    print("\nRANDOM BAND  per tier and |alpha|: mean d_ritual for each direction x sign")
    rb = {}
    for t in TIERS:
        rb[t] = {}
        for aa in sorted({abs(a) for a in ALPHAS}):
            vals = {f"{r['dir']}@{r['alpha']:+.1f}": r["mean"] for r in tab
                    if r["tier"] == t and r["arm"] == "random" and abs(abs(r["alpha"]) - aa) < 1e-9}
            if not vals:
                continue
            rb[t][aa] = vals
            v = list(vals.values())
            print(f"  {t} |a|={aa:.1f}  min {min(v):+7.3f}  max {max(v):+7.3f}  max|.| "
                  f"{max(abs(x) for x in v):6.3f}  each " +
                  " ".join(f"{k}:{x:+.3f}" for k, x in vals.items()))
    out["random_band"] = {t: {str(k): v for k, v in x.items()} for t, x in rb.items()}

    # --- pass-through vs treatment ----------------------------------------------------------
    print("\nPASS-THROUGH vs TREATMENT  (paired over items: treatment - pass_through, sign-flip p)")
    pt = []
    for t in TIERS:
        for a in ALPHAS:
            gt, gp = group(t, "treatment", a), group(t, "pass_through", a)
            common = sorted(set(gt) & set(gp))
            if not common:
                continue
            sf = signflip(np.array([gt[i] - gp[i] for i in common]), rng)
            row = {"tier": t, "alpha": a, "treatment": float(np.mean([gt[i] for i in common])),
                   "pass_through": float(np.mean([gp[i] for i in common])),
                   "diff": sf["mean"], "p": sf["p"], "n": len(common)}
            pt.append(row)
            print(f"  {t} {a:+.1f}  treatment {row['treatment']:+7.3f}  pass-through "
                  f"{row['pass_through']:+7.3f}  diff {row['diff']:+7.3f}  p {row['p']:.4f}")
    out["pass_vs_treatment"] = pt

    # --- odd/even decomposition (added; not the pre-registered verdict) --------------------
    # A norm-matched perturbation can move ritual the same way at +alpha and -alpha (an "even"
    # effect of disturbing the residual at all). The direction-specific part is the odd one,
    # (D(+a) - D(-a)) / 2, per item. Treatment's odd part is compared with each random
    # direction's odd part and with pass-through's.
    print("\nODD / EVEN  per tier, |alpha|: odd = (D(+a)-D(-a))/2, even = (D(+a)+D(-a))/2, item means")
    oe = []
    for t in TIERS:
        for aa in sorted({abs(a) for a in ALPHAS}):
            row = {"tier": t, "abs_alpha": aa}
            for arm, dr in [("treatment", TREAT_DIR)] + [("random", f"rand{k}") for k in range(N_RANDOM)] \
                    + [("pass_through", TREAT_DIR)]:
                gp, gm = group(t, arm, aa, dr), group(t, arm, -aa, dr)
                cm = sorted(set(gp) & set(gm))
                if not cm:
                    continue
                odd = np.array([(gp[i] - gm[i]) / 2 for i in cm])
                even = np.array([(gp[i] + gm[i]) / 2 for i in cm])
                sf = signflip(odd, rng)
                row[f"{arm}:{dr}"] = {"odd": float(odd.mean()), "odd_p": sf["p"],
                                      "even": float(even.mean()), "n": len(cm)}
            oe.append(row)
            if len(row) > 2:
                print(f"  {t} |a|={aa:.1f}  " + "  ".join(
                    f"{k.split(':')[0][:5]}:{k.split(':')[1][-5:]} odd {v['odd']:+.3f} (p {v['odd_p']:.3f}) even {v['even']:+.3f}"
                    for k, v in row.items() if isinstance(v, dict)))
    out["odd_even"] = oe

    # --- total opener mass --------------------------------------------------------------
    print("\nTOTAL OPENER MASS  mean (mass(cell) - mass(no-patch)) over items; random pooled over dirs")
    mass = []
    for t in TIERS:
        for arm in ("treatment", "random", "pass_through"):
            for a in ALPHAS:
                g = group(t, arm, a, key="mass") if arm != "random" else {
                    (r["item"], r["dir"]): d(r, "mass") for r in cells
                    if r["tier"] == t and r["arm"] == "random" and abs(r["alpha"] - a) < 1e-9}
                if not g:
                    continue
                v = np.array(list(g.values()))
                mass.append({"tier": t, "arm": arm, "alpha": a, "d_mass_mean": float(v.mean()),
                             "d_mass_min": float(v.min()), "d_mass_max": float(v.max()), "n": int(v.size)})
                print(f"  {t} {arm:13s} {a:+.1f}  d_mass {v.mean():+7.3f}  range [{v.min():+7.3f},{v.max():+7.3f}]")
    out["mass"] = mass

    # --- per-opener d logp (added: the six-way mass is pinned when one opener sits at 0.0) ----
    print("\nPER-OPENER d logp  mean over items (random pooled over dirs); columns = the six openers")
    po = []
    for t in TIERS:
        for arm in ("treatment", "random", "pass_through"):
            for a in ALPHAS:
                v = np.array([np.array(r["logp"]) - np.array(base[r["item"]]["logp"]) for r in cells
                              if r["tier"] == t and r["arm"] == arm and abs(r["alpha"] - a) < 1e-9])
                if not v.size:
                    continue
                po.append({"tier": t, "arm": arm, "alpha": a, "d_logp_mean": v.mean(0).tolist(),
                           "mean_abs_d_logp": float(np.abs(v).mean())})
                print(f"  {t} {arm:13s} {a:+.1f}  " + " ".join(f"{x:+7.3f}" for x in v.mean(0))
                      + f"   mean|d| {np.abs(v).mean():6.3f}")
    out["per_opener"] = po

    # --- assertion outcomes ------------------------------------------------------------
    moved = {}
    for r in cells:
        moved.setdefault((r["arm"], r["moved"]), 0)
        moved[(r["arm"], r["moved"])] += 1
    out["assertion_outcomes"] = {f"{a}:{m}": n for (a, m), n in sorted(moved.items(), key=str)}
    stuck = [{"item": r["item"], "arm": r["arm"], "alpha": r["alpha"], "dir": r["dir"],
              "max_abs_dlogp": r["max_abs_dlogp"],
              "unmoved": [o for sh in r.get("shortfall", []) for o in sh["unmoved"]]}
             for r in cells if r["moved"] == "did_not_move_beyond_atol"]
    out["did_not_move_by_arm_alpha"] = {}
    for x in stuck:
        k = f"{x['arm']}@{x['alpha']:+.1f}"
        out["did_not_move_by_arm_alpha"][k] = out["did_not_move_by_arm_alpha"].get(k, 0) + 1
    unmoved_opener = Counter(o for x in stuck for o in x["unmoved"])
    out["unmoved_by_opener"] = dict(unmoved_opener)
    L = np.array([r["logp"] for r in base.values()])
    out["readout_grain"] = {
        "no_patch_frac_exactly_zero_by_opener": dict(zip(OPENERS, (L == 0).mean(0).round(3).tolist())),
        "no_patch_frac_multiple_of_1_over_32": float(np.mean(np.abs(L * 32 - np.round(L * 32)) < 1e-9)),
        "no_patch_frac_multiple_of_1_over_16": float(np.mean(np.abs(L * 16 - np.round(L * 16)) < 1e-9)),
    }
    print("  did-not-move by arm@alpha:", out["did_not_move_by_arm_alpha"])
    print("  unmoved openers:", dict(unmoved_opener))
    print("  readout grain:", json.dumps(out["readout_grain"]))
    out["did_not_move"] = stuck
    minmove = {}
    for r in cells:
        k = f"{r['arm']}@{r['alpha']:+.1f}"
        minmove[k] = min(minmove.get(k, np.inf), r["min_abs_dlogp"])
    out["min_abs_dlogp_by_arm_alpha"] = minmove
    print("\nASSERTION OUTCOMES", out["assertion_outcomes"])
    print("  smallest per-candidate |d logp| by arm@alpha:",
          {k: f"{v:.2e}" for k, v in sorted(minmove.items())})
    print(f"  cells that did not move beyond atol: {len(stuck)}", stuck[:10])

    # --- diagnostics: double <bos> and the 62a cross-check -----------------------------
    dbl = {r["item"]: r for r in rows if r["arm"] == "no_patch_double_bos"}
    diag = {}
    if True:
        common = sorted(set(dbl) & set(base))
        if common:
            dd = np.array([dbl[i]["ritual"] - base[i]["ritual"] for i in common])
            diag["double_minus_single_bos_ritual"] = {"n": len(common), "mean": float(dd.mean()),
                                                       "mean_abs": float(np.abs(dd).mean()),
                                                       "max_abs": float(np.abs(dd).max())}
        c3 = {r["item"]: r for r in rows if r["arm"] == "no_patch_chunk3"}
        cc = sorted(set(c3) & set(base))
        if cc:
            x = np.array([c3[i]["ritual"] - base[i]["ritual"] for i in cc])
            y = np.array([np.abs(np.array(c3[i]["logp"]) - np.array(base[i]["logp"])).max() for i in cc])
            diag["chunking_floor_ritual_chunk3_minus_chunk6"] = {
                "n": len(cc), "mean": float(x.mean()), "mean_abs": float(np.abs(x).mean()),
                "max_abs": float(np.abs(x).max()), "max_abs_dlogp": float(y.max()),
                "frac_items_identical": float(np.mean(y == 0))}
        mism = [r for r in cells if r["chunk"] != base[r["item"]]["chunk"]]
        diag["cells_scored_at_a_different_chunk_than_their_no_patch"] = len(mism)
        pos = np.array([[abs(a - b) > 1e-6 for a, b in zip(r["logp"], base[r["item"]]["logp"])]
                        for r in cells])
        diag["moved_fraction_by_opener_row"] = dict(zip(OPENERS, pos.mean(0).round(3).tolist()))
        p62 = ROOT / "research/shame-axis/results/v0_openers/openers.jsonl"
        if p62.exists():
            r62 = {json.loads(l)["item"]: json.loads(l) for l in p62.read_text().splitlines() if l.strip()}
            c2 = sorted(set(r62) & set(dbl))
            if c2:
                x = np.array([np.abs(np.array(r62[i]["logp"]) - np.array(dbl[i]["logp"])).max() for i in c2])
                diag["double_bos_vs_62a_max_abs_dlogp"] = {"n": len(c2), "mean": float(x.mean()),
                                                           "max": float(x.max())}
        print("\nDIAGNOSTICS", json.dumps(diag, indent=2))
    out["diagnostics"] = diag

    # --- verdicts -----------------------------------------------------------------------
    print("\nPRE-REGISTERED VERDICT per tier (A, B tested; N is the control)")
    verd = {}
    for t in TIERS:
        treat = {r["alpha"]: r["mean"] for r in tab if r["tier"] == t and r["arm"] == "treatment"}
        pas = {r["alpha"]: r["mean"] for r in tab if r["tier"] == t and r["arm"] == "pass_through"}
        rmeans = {aa: list(v.values()) for aa, v in rb.get(t, {}).items()}
        if len(treat) != len(ALPHAS) or len(pas) != len(ALPHAS) or len(rmeans) != 2:
            verd[t] = {"verdict": "incomplete"}
        else:
            verd[t] = verdict_for(treat, rmeans, pas)
        print(f"  {t}: {verd[t]['verdict']}")
        for a, p in verd[t].get("per_dose", {}).items():
            print(f"     {a:+.1f}  treat {p['treatment']:+7.3f}  rand max|.| {p['random_max_abs']:6.3f}  "
                  f"pass {p['pass_through']:+7.3f}  sign {'ok' if p['sign_ok'] else 'NO'}  "
                  f"beats random {'yes' if p['beats_random'] else 'no'}  beats pass "
                  f"{'yes' if p['beats_pass_through'] else 'no'}")
    out["verdict"] = {t: {"verdict": v["verdict"],
                          "per_dose": {str(a): p for a, p in v.get("per_dose", {}).items()}}
                      for t, v in verd.items()}
    out["matched_chunk_only"] = matched_chunk
    name = "summary_chunk_matched.json" if matched_chunk else "summary.json"
    (OUT / name).write_text(json.dumps(out, indent=2, default=float))
    print(f"\nwrote {OUT / name}")


if __name__ == "__main__":
    cmd = sys.argv[1]
    if cmd == "prep":
        prep()
    elif cmd == "score":
        args = sys.argv[2:]
        sh = args[args.index("--shard") + 1] if "--shard" in args else None
        hrs = float(args[args.index("--hours") + 1]) if "--hours" in args else 6.0
        score(sh, hrs)
    elif cmd == "report":
        report(matched_chunk="--matched-chunk" in sys.argv[2:])
    else:
        raise SystemExit("prep | score [--shard k/n] [--hours H] | report")
