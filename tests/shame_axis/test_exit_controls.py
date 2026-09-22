"""Hour 61's one structural invariant: the two new arms are APPENDED, and hour 54 does not move.

The shards under `results/conscription_pilot/shards/` carry no labels. Their only labelling is the
row order recorded in `extract_meta.json`, so "the new arms were appended" and "the first 168
(item, arm) pairs are unchanged" are not stylistic preferences -- they are the difference between
reading hour 54's activations and silently reading someone else's. This pins both on a synthetic
grid, with no NDIF and no model: it runs in the py3.11 `.venv` in well under a second.

What is NOT tested here, and is asserted in the script instead because a test cannot see it:
the real shards' bytes (`_shard_fingerprints`, before/after extraction) and the exact
reproduction of `pilot_contrasts.csv`'s deterministic columns from those shards
(`assert_reproduces_hour54`).
"""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts/shame_axis"))
sys.path.insert(0, str(ROOT / "src"))

E = pytest.importorskip("conscription_exit_controls")
P = pytest.importorskip("conscription_pilot")


class FakeTok:
    """Enough tokenizer to drive `render_prompt` and `verify_offsets_cover_template`.

    Offsets are one per character and never degenerate, which is the condition
    `verify_offsets_cover_template` exists to check; a fake that returned (0, 0) would make the
    real guard fire and this test would be testing the guard, not the ordering.
    """

    def apply_chat_template(self, messages, tokenize=False, add_generation_prompt=True):
        body = "".join(f"<{m['role']}>{m['content']}</{m['role']}>" for m in messages)
        return body + ("<model>" if add_generation_prompt else "")

    def __call__(self, text, return_offsets_mapping=False, add_special_tokens=True, **kw):
        out = {"input_ids": list(range(len(text)))}
        if return_offsets_mapping:
            out["offset_mapping"] = [(i, i + 1) for i in range(len(text))]
        return out


N_ITEMS = 3
BASE_ARMS = list(P.ARMS) + [P.EXTRA, P.NB]            # 5 design arms + enact_norecord + neutral_b
N_BASE = N_ITEMS * len(BASE_ARMS)                     # 21 on the synthetic layout


def _synthetic_grid():
    items = []
    for k in range(N_ITEMS):
        arms = {a: f"item{k} body for {a}. A closer sentence." for a in BASE_ARMS + list(E.NEW_ARMS)}
        items.append({"id": f"syn{k:02d}", "domain": "fact",
                      "prefix": [{"role": "user", "content": f"q{k}"},
                                 {"role": "assistant", "content": f"a{k}"}],
                      "arms": arms})
    return {"_meta": {"version": 0}, "items": items}


def _hour54_order():
    """The pilot's own convention: item-major over the 6 base arms, then `neutral_b` appended."""
    order = []
    for k in range(N_ITEMS):
        for a in list(P.ARMS) + [P.EXTRA]:
            order.append([f"syn{k:02d}", a])
    for k in range(N_ITEMS):
        order.append([f"syn{k:02d}", P.NB])
    return order


@pytest.fixture()
def synthetic(tmp_path, monkeypatch):
    grid = tmp_path / "grid.json"
    grid.write_text(json.dumps(_synthetic_grid()))
    out = tmp_path / "results"
    out.mkdir()
    (out / "extract_meta.json").write_text(json.dumps({"order": _hour54_order(), "grid_sha": "0" * 16}))
    monkeypatch.setattr(P, "GRID", grid)
    monkeypatch.setattr(E, "GRID", grid)
    monkeypatch.setattr(E, "OUT", out)
    monkeypatch.setattr(E, "META", out / "exit_controls_extract_meta.json")
    monkeypatch.setattr(E, "N_BASE", N_BASE)
    return out


def test_new_arms_are_appended_after_the_existing_order(synthetic):
    rows = E.render_all_ext(FakeTok())
    got = [(i, a) for i, a, _ in rows]
    assert len(got) == N_BASE + len(E.NEW_ARMS) * N_ITEMS

    # (ii): the first 168 -- here the first 21 -- (item, arm) pairs are byte-for-byte the recorded
    # hour-54 mapping, in the recorded positions.
    assert got[:N_BASE] == [tuple(x) for x in _hour54_order()]

    # the appended block: arm-major, one arm per shard-sized run, in NEW_ARMS order, and strictly
    # AFTER the last `neutral_b`.
    assert got[N_BASE - 1][1] == P.NB
    tail = got[N_BASE:]
    for j, arm in enumerate(E.NEW_ARMS):
        block = tail[j * N_ITEMS:(j + 1) * N_ITEMS]
        assert [a for _, a in block] == [arm] * N_ITEMS, block
        assert [i for i, _ in block] == [f"syn{k:02d}" for k in range(N_ITEMS)], block


def test_the_assertion_itself_passes_on_an_honest_append(synthetic):
    rows = E.render_all_ext(FakeTok())
    res = E.assert_row_order_unchanged(rows)
    assert res["order_matches_hour54"] is True
    assert res["n_total"] == N_BASE + len(E.NEW_ARMS) * N_ITEMS
    # no text hashes were recorded by hour 54, so the first run can only record them
    assert res["text_hashes_checked"] is False


def test_an_interleaved_arm_is_refused(synthetic):
    """The failure this guard exists for: inserting the new arms per item instead of appending
    shifts every row after the first item, and the cached shards would be read with the wrong
    labels from position 6 onward."""
    rows = E.render_all_ext(FakeTok())
    interleaved = rows[:6] + rows[N_BASE:N_BASE + 1] + rows[6:]
    with pytest.raises(SystemExit, match="row order changed in place"):
        E.assert_row_order_unchanged(interleaved)


def test_a_swapped_pair_inside_hour54_is_refused(synthetic):
    rows = E.render_all_ext(FakeTok())
    swapped = list(rows)
    swapped[1], swapped[2] = swapped[2], swapped[1]      # report <-> exit on the first item
    with pytest.raises(SystemExit, match="row order changed in place"):
        E.assert_row_order_unchanged(swapped)


def test_appending_before_neutral_b_is_refused(synthetic):
    """`neutral_b` must remain the last hour-54 row: the addendum's arms come after it."""
    rows = E.render_all_ext(FakeTok())
    moved = rows[:N_BASE - N_ITEMS] + rows[N_BASE:] + rows[N_BASE - N_ITEMS:N_BASE]
    with pytest.raises(SystemExit):
        E.assert_row_order_unchanged(moved)


def test_a_changed_hour54_prompt_text_is_refused(synthetic, tmp_path):
    """Second half of the guard: the (item, arm) mapping can be intact while an hour-54 arm's TEXT
    has been edited, which would make the cached activations stale rather than mislabelled."""
    rows = E.render_all_ext(FakeTok())
    E.META.write_text(json.dumps({"text_sha": [E._sha(t) for _, _, t in rows]}))
    assert E.assert_row_order_unchanged(rows)["text_hashes_checked"] is True

    g = json.loads(E.GRID.read_text())
    g["items"][0]["arms"]["enact"] = "an edit to an already-extracted arm."
    E.GRID.write_text(json.dumps(g))
    with pytest.raises(SystemExit, match="prompt TEXT changed"):
        E.assert_row_order_unchanged(E.render_all_ext(FakeTok()))


def test_new_arms_and_prereg_family_are_the_addendums(synthetic):
    assert E.NEW_ARMS == ("exit_b", "exit_c")
    assert E.PREREG == (("exit", "exit_c"), ("exit", "exit_b"), ("exit_c", "enact"))
    assert len(E.PREREG) == 3, "Holm is over a family of three; the addendum says so"
    assert E.FLOOR_PAIR == ("neutral", P.NB), "the floor must stay hour 54's rewording floor"
    assert E.SHARD == 24 and N_ITEMS != E.SHARD  # real shards are 24 = one arm; synthetic is not


def test_holm_is_holm():
    assert E.holm([0.01, 0.02, 0.03]) == pytest.approx([0.03, 0.04, 0.04])
    assert E.holm([0.5, 0.001, 0.2]) == pytest.approx([0.5, 0.003, 0.4])
    assert E.holm([0.9, 0.9, 0.9]) == pytest.approx([1.0, 1.0, 1.0])
    # order-preserving and monotone in the sorted order
    out = E.holm([0.04, 0.01, 0.9])
    assert out[1] <= out[0] <= out[2]


def test_holm_never_makes_a_p_smaller():
    for ps in ([0.001, 0.5, 0.5], [0.3, 0.3, 0.3], [0.0, 0.0, 1.0]):
        assert all(h >= p - 1e-12 for h, p in zip(E.holm(ps), ps)), ps


def test_the_pilot_is_untouched_by_this_module():
    """Importing the sibling must not mutate the hour-54 script's own arm list or pair list:
    `conscription_pilot.py`'s behaviour on the old arms has to be unchanged."""
    assert P.ARMS == ("enact", "report", "exit", "true", "neutral")
    assert P.NB == "neutral_b"
    assert "exit_b" not in {a for pair in P.PAIRS for a in pair}
    assert "exit_c" not in {a for pair in P.PAIRS for a in pair}
    assert len(P.PAIRS) == 12
