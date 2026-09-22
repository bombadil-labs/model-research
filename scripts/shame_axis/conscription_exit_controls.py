"""Hour 61: `exit`'s topic-matched controls on the dense pain axis.

Spec: `research/shame-axis/notes/conscription_prereg.md`, "Addendum, hour 61", written and
committed before any activation was extracted. Hour 54 put `exit` highest at L16-17
(`enact - exit` gain = -1.15 / -0.91 z) and read the permission clause as the cause. Hours 55/56/59b
falsified that reading behaviourally. This asks the dense axis the same question with two
token-matched replacements for the item closer:

  * `exit_b` -- "There's a window open in here this afternoon."  (inert)
  * `exit_c` -- "Just so we're on the same page here."           (on topic, no permission)

WHAT THIS SCRIPT IS NOT: it is not a second pipeline. Every measurement decision -- rendering,
the §7-asserted extraction, the z-unit projection onto the externally-fitted pain axis, the
static-embedding floor, the sign-flip band, the gain -- is imported from `conscription_pilot`
and `painaxis_scenarios` and is byte-identical to hour 54's. The only things here are (a) the
two appended arms, (b) the Holm correction over the addendum's three pre-registered pairs, and
(c) the assertions that hour 54's rows did not move.

ROW ORDER. Hour 54's 168 rows are `enact, report, exit, true, neutral, enact_norecord` per item
(item-major, 144 rows) then one `neutral_b` per item APPENDED LAST (24 rows). That append is the
pilot's own convention and the reason its six paid-for shards stayed valid. The same convention
is followed here: all 24 `exit_b`, then all 24 `exit_c`, appended after `neutral_b` at positions
168..215. Shard boundaries are multiples of 24 and there are 24 items, so each new arm is exactly
one new shard (`grid_0168.npz`, `grid_0192.npz`) and no existing shard is touched. Both facts are
ASSERTED, not assumed:

  * `assert_row_order_unchanged` -- the first 168 (item, arm) pairs rendered here equal
    `extract_meta.json`'s recorded order exactly, and the first 168 rendered TEXTS hash to what a
    previous run of this script recorded (the first run records them).
  * `_shard_fingerprints` -- every pre-existing shard's size and mtime, before and after
    extraction. An hour-54 shard that changed is a failure, not a warning.
  * `assert_reproduces_hour54` (in `analyze`) -- `d_acts`, `d_floor` and `gain` for
    (`enact`, `exit`) and (`neutral`, `neutral_b`) recomputed here must equal
    `pilot_contrasts.csv` at EVERY layer. Those three quantities are deterministic (means, no
    rng), so this is an exact check, and it is the one that would catch a silent relabelling of
    the cached shards.

Usage:  python scripts/shame_axis/conscription_exit_controls.py extract   # .venv312, NDIF
        python scripts/shame_axis/conscription_exit_controls.py analyze   # either venv
        python scripts/shame_axis/conscription_exit_controls.py table
"""
from __future__ import annotations

import csv
import hashlib
import json
import pathlib
import sys
import time

import numpy as np

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "src"))
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))

import conscription_pilot as P        # noqa: E402  -- the hour-54 pipeline, reused not rewritten
import painaxis_scenarios as S        # noqa: E402

GRID = P.GRID
OUT = P.OUT
SHARDS = P.SHARDS
SHARD = 24                            # P.extract's own shard size, restated so it is checkable
NEW_ARMS = ("exit_b", "exit_c")       # appended AFTER `neutral_b`, the pilot's own convention
N_BASE = 168                          # hour 54's row count; asserted against extract_meta.json

META = OUT / "exit_controls_extract_meta.json"     # ours; hour 54's extract_meta.json is READ-ONLY
CSV_OUT = OUT / "exit_controls_contrasts.csv"
SUMMARY_OUT = OUT / "exit_controls_summary.json"

# The addendum's family of three. Holm is applied over THESE THREE, within a layer. No layer is
# selected: the whole 43-layer curve is written to the CSV and the L10-17 window is printed.
PREREG = (("exit", "exit_c"), ("exit", "exit_b"), ("exit_c", "enact"))
# "for continuity", per the task: the same two arms read against `enact`, plus hour 54's own
# (enact, exit) which is recomputed here purely as the reproduction check described above.
CONTINUITY = (("enact", "exit_b"), ("enact", "exit_c"), ("enact", "exit"))
FLOOR_PAIR = ("neutral", P.NB)        # the rewording floor, hour 54's `neutral - neutral_b`
PAIRS = PREREG + CONTINUITY + (FLOOR_PAIR,)

RETRY_BUDGET_S = 90 * 60              # the task's ~90 minute ceiling on retries
BACKOFF_S = (60, 120, 240, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300, 300)


# --------------------------------------------------------------------------------- rendering
def render_all_ext(tok):
    """`P.render_all` verbatim for the first 168 rows, then the two new arms APPENDED.

    The new arms go through the same `render_prompt` and the same
    `verify_offsets_cover_template` as every other arm -- imported from the same module, not
    reimplemented -- so the read position and the degenerate-offset guard are the hour-54 ones.
    Arm-major, one arm per 24-row shard, exactly as `neutral_b` was appended.
    """
    from lsx.shame_axis.conscription import render_prompt, verify_offsets_cover_template

    rows = list(P.render_all(tok))            # the hour-54 168, unmodified
    items = json.loads(GRID.read_text())["items"]
    for arm in NEW_ARMS:
        for it in items:
            if arm not in it["arms"]:
                raise SystemExit(f"{it['id']} has no {arm} arm; the grid is out of date")
            t = render_prompt(tok, it["prefix"], it["arms"][arm])
            verify_offsets_cover_template(tok, t)
            rows.append((it["id"], arm, t))
    return rows


def _sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def assert_row_order_unchanged(rows) -> dict:
    """(ii) of the task: the existing 168 rows' (item, arm) mapping is byte-for-byte unchanged.

    Checked two ways. Against hour 54's `extract_meta.json` order, which is the labelling the
    cached shards are read with -- shards carry no labels of their own, so this mapping IS the
    data. And against per-prompt text hashes recorded by the first run of this script, so a later
    edit to an hour-54 arm's TEXT cannot pass silently either (hour 54 recorded no text hashes,
    so the first run of this script can only record them, not check them; said plainly rather
    than presented as a check that ran).
    """
    old = json.loads((OUT / "extract_meta.json").read_text())
    prev = [tuple(x) for x in old["order"]]
    now = [(i, a) for i, a, _ in rows]
    if len(prev) != N_BASE:
        raise SystemExit(f"extract_meta.json records {len(prev)} rows, expected {N_BASE}")
    if now[:N_BASE] != prev:
        bad = [k for k in range(N_BASE) if now[k] != prev[k]]
        raise SystemExit(
            f"row order changed in place at positions {bad[:10]}: the cached shards are indexed "
            "by position and carry no labels, so hour 54's activations would be silently "
            "relabelled. Refusing to extract.")
    n_items = len(json.loads(GRID.read_text())["items"])
    if len(now) != N_BASE + len(NEW_ARMS) * n_items:
        raise SystemExit(f"expected {N_BASE + len(NEW_ARMS)*n_items} rows, rendered {len(now)}")
    if now[N_BASE - 1][1] != P.NB:
        raise SystemExit(f"row {N_BASE-1} is {now[N_BASE-1]}, expected the last {P.NB}; the new "
                         "arms must be appended AFTER neutral_b")

    hashes = [_sha(t) for _, _, t in rows]
    out = {"order_matches_hour54": True, "n_base": N_BASE, "n_total": len(now),
           "text_hashes_checked": False}
    if META.exists():
        old_h = json.loads(META.read_text()).get("text_sha", [])
        if old_h:
            if old_h[:N_BASE] != hashes[:N_BASE]:
                bad = [k for k in range(N_BASE) if old_h[k] != hashes[k]]
                raise SystemExit(f"hour-54 prompt TEXT changed at rows {bad[:10]}")
            out["text_hashes_checked"] = True
    return out


def _shard_fingerprints() -> dict:
    return {p.name: [p.stat().st_size, int(p.stat().st_mtime_ns)]
            for p in sorted(SHARDS.glob("grid_*.npz"))}


def hour54_shards() -> list[str]:
    """The seven shards hour 54 paid for, named by POSITION rather than by whatever happened to be
    on disk when this run started. A second run of this script finds the new shards already
    cached, and a before/after set-difference then calls THEM hour 54's -- which is how the
    bookkeeping in this file was wrong once, on an accidental second run. Position cannot
    drift; an inventory taken at an arbitrary moment can."""
    return [f"grid_{s0:04d}.npz" for s0 in range(0, N_BASE, SHARD)]


# -------------------------------------------------------------------------------- extraction
def _extract_once() -> dict:
    """One pass of the hour-54 extraction over the full 216 rows. Every shard already on disk is
    skipped, so a retry costs only what has not landed."""
    from lsx.shame_axis import painaxis_remote as pr
    from lsx.core.remote import RemoteLM

    OUT.mkdir(parents=True, exist_ok=True)
    SHARDS.mkdir(parents=True, exist_ok=True)
    rlm = RemoteLM(S.MODEL)
    rows = render_all_ext(rlm.tok)
    texts = [t for _, _, t in rows]
    order_check = assert_row_order_unchanged(rows)
    print(f"row-order assertion: {order_check}", flush=True)
    print(f"{len(rows)} prompts total; {len(rows)-N_BASE} new "
          f"({len(NEW_ARMS)} arms x 24 items)", flush=True)
    for k in (N_BASE, N_BASE + 24):
        print(f"example {rows[k][1]}:", repr(rows[k][2])[:240], flush=True)

    before = _shard_fingerprints()

    meta = {"model": S.MODEL, "batch": P.BATCH,
            "arms": list(P.ARMS) + [P.EXTRA, P.NB] + list(NEW_ARMS),
            "new_arms": list(NEW_ARMS), "n_base_rows": N_BASE, "n_prompts": len(rows),
            "grid": str(GRID.relative_to(ROOT)),
            "grid_sha": hashlib.sha256(GRID.read_bytes()).hexdigest()[:16],
            "hour54_grid_sha": json.loads((OUT / "extract_meta.json").read_text())["grid_sha"],
            "equivalence": {}, "row_order_assertion": order_check,
            "padding_side": rlm.padding_side, "lib_versions": rlm.lib_versions()}
    if META.exists():
        meta["equivalence"] = json.loads(META.read_text()).get("equivalence", {})
    meta["order"] = [[i, a] for i, a, _ in rows]
    meta["text_sha"] = [_sha(t) for t in texts]

    for s0 in range(0, len(texts), SHARD):
        path = SHARDS / f"grid_{s0:04d}.npz"
        if path.exists():
            print(f"  [{s0}] cached", flush=True)
            continue
        t0 = time.time()
        pooled = pr.extract_pooled(rlm, texts[s0:s0 + SHARD], batch_size=P.BATCH,
                                   add_special_tokens=False, check_every=3)
        np.savez_compressed(path, final_token=pooled.final_token.astype(np.float32),
                            embed_mean=pooled.embed_mean.astype(np.float32),
                            embed_final_token=pooled.embed_final_token.astype(np.float32))
        meta["equivalence"].update({f"{s0}:{k}": v for k, v in pooled.equivalence.items()})
        META.write_text(json.dumps(meta, indent=2))
        print(f"  [{s0}] done {time.time()-t0:.0f}s jobs={pooled.n_jobs}", flush=True)

    after = _shard_fingerprints()
    moved = [k for k in before if before[k] != after.get(k)]
    if moved:
        raise SystemExit(f"pre-existing shards changed on disk: {moved}. Hour 54 was re-extracted; "
                         "that must not happen.")
    h54 = hour54_shards()
    missing = [k for k in h54 if k not in after]
    if missing:
        raise SystemExit(f"hour-54 shards missing after extraction: {missing}")
    meta["hour54_shards"] = h54
    meta["hour54_shards_present_before_this_run"] = [k for k in h54 if k in before]
    meta["hour54_shards_fingerprints"] = {k: after[k] for k in h54}
    meta["exit_control_shards"] = [f"grid_{s0:04d}.npz"
                                   for s0 in range(N_BASE, len(texts), SHARD)]
    meta["shards_written_this_run"] = sorted(set(after) - set(before))
    META.write_text(json.dumps(meta, indent=2))
    print(f"hour-54 shards, present and unchanged: "
          f"{meta['hour54_shards_present_before_this_run']}", flush=True)
    print(f"exit-control shards: {meta['exit_control_shards']}", flush=True)
    print(f"written THIS run: {meta['shards_written_this_run']}", flush=True)
    print("EXIT-CONTROL EXTRACTION DONE", flush=True)
    return meta


def extract() -> None:
    """`_extract_once` under a retry loop with backoff.

    NDIF is contended and the deployment OOMs when a co-tenant is heavy; CLAUDE.md says retry, do
    not redesign. The shard cache means attempt k+1 pays only for what attempt k did not land.
    """
    t_start = time.time()
    for attempt in range(1, len(BACKOFF_S) + 2):
        try:
            _extract_once()
            print(f"ATTEMPTS={attempt}", flush=True)
            return
        except SystemExit:
            raise                        # an assertion failure is not a contention failure
        except BaseException as e:       # noqa: BLE001 -- contention shows up as many types
            elapsed = time.time() - t_start
            landed = sorted(p.name for p in SHARDS.glob("grid_*.npz"))
            print(f"ATTEMPT {attempt} FAILED after {elapsed:.0f}s: {type(e).__name__}: {e}",
                  flush=True)
            print(f"  shards landed so far: {len(landed)} {landed}", flush=True)
            if elapsed > RETRY_BUDGET_S or attempt > len(BACKOFF_S):
                n_rows = len(landed) * SHARD
                print(f"RETRY BUDGET EXHAUSTED after {elapsed:.0f}s and {attempt} attempts. "
                      f"ROWS LANDED={n_rows} of {N_BASE + len(NEW_ARMS)*24}", flush=True)
                raise SystemExit(1)
            wait = BACKOFF_S[attempt - 1]
            print(f"  backing off {wait}s then retrying", flush=True)
            time.sleep(wait)


# ---------------------------------------------------------------------------------- analysis
def holm(pvals):
    """Holm-Bonferroni over one family, returned in the input order. Monotone by construction."""
    m = len(pvals)
    order = sorted(range(m), key=lambda k: pvals[k])
    out = [0.0] * m
    run = 0.0
    for rank, k in enumerate(order):
        run = max(run, min(1.0, (m - rank) * pvals[k]))
        out[k] = run
    return out


def _load_acts(order):
    n = len(order)
    parts_ft, parts_eb = [], []
    for s0 in range(0, n, SHARD):
        z = np.load(SHARDS / f"grid_{s0:04d}.npz")
        parts_ft.append(z["final_token"])
        parts_eb.append(z["embed_mean"])
    ft = np.concatenate(parts_ft, axis=0)
    eb = np.concatenate(parts_eb, axis=0)
    acts = np.concatenate([eb[:, None, :], ft], axis=1)       # [n, 43, d], index 0 = emb bag
    assert acts.shape[0] == n, (acts.shape, n)
    return acts


def assert_reproduces_hour54(rows) -> dict:
    """The deterministic part of hour 54's numbers, recomputed from the cached shards, must be
    IDENTICAL. `d_acts`, `d_floor` and `gain` are plain means: no rng, so this is exact at the
    CSV's 4 decimal places. The band columns are not compared -- they are sign-flip draws and the
    pair list here differs, so the rng stream does too. Stated rather than quietly skipped."""
    old = {(r["layer"], r["arm_a"], r["arm_b"]): r
           for r in csv.DictReader(CSV_OUT.parent.joinpath("pilot_contrasts.csv").open())}
    checked, bad = 0, []
    for r in rows:
        key = (r["layer"], r["arm_a"], r["arm_b"])
        if key not in old:
            continue
        for col in ("d_acts", "d_floor", "gain"):
            if abs(float(old[key][col]) - r[col]) > 5e-5:
                bad.append((key, col, old[key][col], r[col]))
        checked += 1
    if bad:
        raise SystemExit(f"hour 54's numbers did not reproduce from the cached shards: {bad[:8]}")
    return {"cells_checked": checked, "all_identical": True,
            "pairs": sorted({(k[1], k[2]) for k in old} & {(r["arm_a"], r["arm_b"]) for r in rows})}


def analyze() -> None:
    import painaxis_scenarios_analyze as A

    meta = json.loads(META.read_text())
    order = [(i, a) for i, a in meta["order"]]
    n = len(order)
    if order[:N_BASE] != [tuple(x) for x in
                          json.loads((OUT / "extract_meta.json").read_text())["order"]]:
        raise SystemExit("the recorded order no longer matches hour 54's; refusing to analyse")
    acts = _load_acts(order)

    # --- everything below is `P.analyze`'s arithmetic, unchanged, over a different pair list ---
    ds = json.loads(S.CORE.read_text())["datasets"]
    core = {m: A.load_group(f"core_{m}", len(ds[m]["sentences"]), ("final_token", "mean"))
            for m in S.S_SETS}
    core_cats = {m: np.array([s["category"] for s in ds[m]["sentences"]]) for m in S.S_SETS}
    scen_order = json.loads((S.OUT / "scenario_order.json").read_text())
    scen = A.load_group("scen_chat", len(scen_order), ("final_token", "mean"))

    item_ids = sorted({i for i, _ in order})
    idx = {(i, a): k for k, (i, a) in enumerate(order)}
    names = ["emb"] + [str(i) for i in range(acts.shape[1] - 1)]
    rng = np.random.default_rng(31337)
    rows = []

    vf = S.unit(S.compute_pain_vector(core["S2_1P"]["mean"][:, 0, :], core_cats["S2_1P"]))
    spf = scen["mean"][:, 0, :] @ vf
    pf = (acts[:, 0, :] @ vf - float(spf.mean())) / (float(spf.std()) + 1e-8)

    for L, nm in enumerate(names):
        ext = "mean" if nm == "emb" else "final_token"
        v = S.unit(S.compute_pain_vector(core["S2_1P"][ext][:, L, :], core_cats["S2_1P"]))
        sp = scen[ext][:, L, :] @ v
        mu, sd = float(sp.mean()), float(sp.std()) + 1e-8
        p = (acts[:, L, :] @ v - mu) / sd

        layer_rows = []
        for a, b in PAIRS:
            d = np.array([p[idx[(i, a)]] - p[idx[(i, b)]] for i in item_ids])
            df = np.array([pf[idx[(i, a)]] - pf[idx[(i, b)]] for i in item_ids])
            m, lo, hi, pv = P._band(d, rng)
            mf, lof, hif, pvf = P._band(df, rng)
            gm, glo, ghi, gp = P._band(d - df, rng)
            layer_rows.append({
                "layer": nm, "arm_a": a, "arm_b": b, "n": len(d),
                "d_acts": round(m, 4), "d_acts_p": round(pv, 4),
                "d_floor": round(mf, 4), "d_floor_p": round(pvf, 4),
                "gain": round(m - mf, 4), "gain_lo": round(glo, 4), "gain_hi": round(ghi, 4),
                "gain_p": round(gp, 4),
                "clears": int(gp < 0.05),
                "in_window": int(nm.isdigit() and int(nm) in P.WINDOW),
                "holm_p": "", "holm_clears": "",
                "family": ("prereg" if (a, b) in PREREG
                           else "floor" if (a, b) == FLOOR_PAIR else "continuity"),
            })
        # Holm over the THREE pre-registered pairs, WITHIN this layer. The continuity and floor
        # rows are outside the family and are left uncorrected, which is why they carry a blank
        # rather than a number that would imply they were in it.
        fam = [r for r in layer_rows if r["family"] == "prereg"]
        for r, hp in zip(fam, holm([r["gain_p"] for r in fam])):
            r["holm_p"] = round(hp, 4)
            r["holm_clears"] = int(hp < 0.05)
        rows.extend(layer_rows)

    repro = assert_reproduces_hour54(rows)
    print(f"hour-54 reproduction assertion: {repro}", flush=True)

    with CSV_OUT.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0])); w.writeheader(); w.writerows(rows)

    win = [r for r in rows if r["in_window"]]
    summary = {
        "spec": "research/shame-axis/notes/conscription_prereg.md, Addendum hour 61",
        "n_items": len(item_ids), "n_rows_total": n, "n_rows_hour54": N_BASE,
        "new_arms": list(NEW_ARMS), "window": P.WINDOW, "layers_reported": names,
        "prereg_pairs": [list(x) for x in PREREG],
        "continuity_pairs": [list(x) for x in CONTINUITY],
        "floor_pair": list(FLOOR_PAIR),
        "holm": "within-layer, over the three pre-registered pairs only; no layer selected",
        "row_order_assertion": meta.get("row_order_assertion"),
        "hour54_shards": meta.get("hour54_shards"),
        "hour54_shards_fingerprints": meta.get("hour54_shards_fingerprints"),
        "exit_control_shards": meta.get("exit_control_shards"),
        "shards_written_in_last_extract_run": meta.get("shards_written_this_run"),
        "hour54_reproduction": repro,
        "n_rows_csv": len(rows), "cells_in_window": len(win),
        "clearing_in_window": [
            {k: r[k] for k in ("layer", "arm_a", "arm_b", "gain", "gain_lo", "gain_hi",
                               "gain_p", "holm_p", "family")}
            for r in win if r["clears"]],
        "positive_control": json.loads((S.OUT / "summary.json").read_text())["headline"],
        "predictions": _predictions(rows),
    }
    SUMMARY_OUT.write_text(json.dumps(summary, indent=2))
    print(f"wrote {CSV_OUT.relative_to(ROOT)} ({len(rows)} rows) and "
          f"{SUMMARY_OUT.relative_to(ROOT)}", flush=True)


# ------------------------------------------------------------------------ prediction scoring
def _predictions(rows) -> list:
    """The addendum's table, evaluated at each window layer.

    The addendum states the three predictions in words ("at the floor", "above the floor, `exit`
    higher", "~= hour 54's exit-enact (+0.9 to +1.1 z)") and gives no numeric rule. The
    operationalisation below is MINE and is stated so it can be disagreed with:

      * AT FLOOR   -- Holm-adjusted gain p >= 0.05 AND |gain| <= |gain(neutral, neutral_b)| at the
                      same layer (the measured rewording floor). Both halves must hold.
      * ABOVE FLOOR-- Holm-adjusted gain p < 0.05 AND |gain| > that same floor magnitude.
      * the +0.9..+1.1 band for `exit_c - enact` is read on GAIN, because hour 54's -1.15/-0.91
        at L16-17 are gain, not d_acts (pilot_contrasts.csv).
    """
    by = {(r["layer"], r["arm_a"], r["arm_b"]): r for r in rows}
    out = []
    for nm in [str(L) for L in P.WINDOW]:
        floor_mag = abs(by[(nm, *FLOOR_PAIR)]["gain"])
        for pair in PREREG:
            r = by[(nm, *pair)]
            g, hp = r["gain"], r["holm_p"]
            above = (hp < 0.05) and (abs(g) > floor_mag)
            atfl = (hp >= 0.05) and (abs(g) <= floor_mag)
            verdict = "above floor" if above else "at floor" if atfl else "ambiguous"
            row = {"layer": nm, "pair": f"{pair[0]} - {pair[1]}", "gain": g,
                   "floor_mag": round(floor_mag, 4), "holm_p": hp,
                   "sign": "+" if g > 0 else "-" if g < 0 else "0", "verdict": verdict}
            if pair == ("exit_c", "enact"):
                # "~= hour 54's exit - enact" is a comparison to a MEASURED quantity, and the
                # addendum's "+0.9 to +1.1" was hour 54's value at L16-17 only. Quoting the band
                # alone would score L10-L15 against a number that was never hour 54's there. So
                # both are reported: literal band membership, and the ratio to hour 54's own
                # `exit - enact` gain AT THE SAME LAYER, which is what the prediction means.
                h54 = -by[(nm, "enact", "exit")]["gain"]        # hour 54's exit - enact, this layer
                row["hour54_exit_minus_enact"] = round(h54, 4)
                row["ratio_to_hour54"] = round(g / h54, 3) if abs(h54) > 1e-9 else None
                row["in_hour54_band_0.9_1.1"] = int(0.9 <= g <= 1.1)
                row["near_zero"] = int(abs(g) <= floor_mag)
            out.append(row)
    return out


# -------------------------------------------------------------------------------- the table
def table() -> None:
    rows = [dict(r) for r in csv.DictReader(CSV_OUT.open())]
    for r in rows:
        for k in ("d_acts", "d_floor", "gain", "gain_lo", "gain_hi", "gain_p"):
            r[k] = float(r[k])
        # csv.DictReader hands back strings and "0" is TRUTHY: read as-is, every row prints
        # "clears yes", including the emb rows whose gain is exactly 0. Cast, do not test.
        r["clears"] = int(r["clears"])
        r["in_window"] = int(r["in_window"])
        r["holm_p"] = float(r["holm_p"]) if r["holm_p"] != "" else None
    by = {(r["layer"], r["arm_a"], r["arm_b"]): r for r in rows}

    print("\n" + "=" * 108)
    print("HOUR 61 -- exit's topic-matched controls on the dense pain axis, L10-17 window")
    print("units: scenario-pool z; gain = d_acts - d_floor; band = sign-flip over 24 items; "
          "Holm over the 3 pre-registered pairs within a layer")
    print("=" * 108)
    hdr = (f"{'L':>3} {'pair':<20} {'d_acts':>8} {'d_floor':>8} {'gain':>8} "
           f"{'gain band':>19} {'p':>7} {'Holm p':>7} {'clears':>6}")
    for fam, pairs in (("PRE-REGISTERED", PREREG), ("CONTINUITY", CONTINUITY),
                       ("FLOOR", (FLOOR_PAIR,))):
        print(f"\n--- {fam} " + "-" * (104 - len(fam)))
        print(hdr)
        for L in P.WINDOW:
            for pair in pairs:
                r = by[(str(L), *pair)]
                hp = "-" if r["holm_p"] is None else f"{r['holm_p']:.4f}"
                print(f"{L:>3} {pair[0] + ' - ' + pair[1]:<20} {r['d_acts']:>+8.4f} "
                      f"{r['d_floor']:>+8.4f} {r['gain']:>+8.4f} "
                      f"[{r['gain_lo']:>+7.4f},{r['gain_hi']:>+7.4f}] {r['gain_p']:>7.4f} "
                      f"{hp:>7} {'yes' if r['clears'] else 'no':>6}")
            print()

    print("\n--- emb (the free check: at emb the treatment IS the floor, so gain must be 0) " + "-" * 27)
    print(hdr)
    for pair in PAIRS:
        r = by[("emb", *pair)]
        hp = "-" if r["holm_p"] is None else f"{r['holm_p']:.4f}"
        print(f"{'emb':>3} {pair[0] + ' - ' + pair[1]:<20} {r['d_acts']:>+8.4f} "
              f"{r['d_floor']:>+8.4f} {r['gain']:>+8.4f} "
              f"[{r['gain_lo']:>+7.4f},{r['gain_hi']:>+7.4f}] {r['gain_p']:>7.4f} "
              f"{hp:>7} {'yes' if r['clears'] else 'no':>6}")

    print("\n" + "=" * 108)
    print("THE ADDENDUM'S PREDICTION TABLE, evaluated at each window layer")
    print("  topic-pull column : exit-exit_c AT FLOOR | exit-exit_b ABOVE, exit higher | "
          "exit_c-enact +0.9..+1.1")
    print("  clause-special    : exit-exit_c ABOVE    | exit-exit_b either             | "
          "exit_c-enact ~ 0")
    print("=" * 108)
    preds = json.loads(SUMMARY_OUT.read_text())["predictions"]
    print(f"{'L':>3} {'prediction row':<20} {'gain':>9} {'floor':>8} {'Holm p':>8} "
          f"{'sign':>5} {'verdict':>12}  {'notes'}")
    for pr in preds:
        note = ""
        if pr["pair"] == "exit_c - enact":
            note = (f"h54 exit-enact {pr['hour54_exit_minus_enact']:+.4f}, "
                    f"ratio {pr['ratio_to_hour54']:.2f}x; "
                    f"in +0.9..+1.1: {'YES' if pr['in_hour54_band_0.9_1.1'] else 'no'}; "
                    f"~0: {'YES' if pr['near_zero'] else 'no'}")
        if pr["pair"] == "exit - exit_b":
            note = f"exit higher: {'YES' if pr['gain'] > 0 else 'no'}"
        print(f"{pr['layer']:>3} {pr['pair']:<20} {pr['gain']:>+9.4f} {pr['floor_mag']:>8.4f} "
              f"{pr['holm_p']:>8.4f} {pr['sign']:>5} {pr['verdict']:>12}  {note}")
    print("=" * 108 + "\n")


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "extract":
        extract()
    elif cmd == "analyze":
        analyze()
    elif cmd == "table":
        table()
    else:
        raise SystemExit("extract | analyze | table")
