"""The claims validator, and the one property that makes a claims table worth keeping.

A table that lists only the questions you answered will report a line CLOSED while its open
problems run to a page — which is exactly what the first triage of the narrative line did. These
tests pin the rules that stop a table rotting into decoration: a terminal claim must point at its
answer, a retraction must name what replaced it, and the closure count must be computed rather
than asserted.
"""
from __future__ import annotations

import pathlib
import sys

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "scripts"))
yaml = pytest.importorskip("yaml")
cc = pytest.importorskip("check_claims")

BASE = {"id": "a-claim", "claim": "The thing is true of the model.", "status": "holds",
        "where": "docs/EXPERIMENTS.md", "evidence": "h1", "superseded_by": None}


def write(tmp_path, claims, line="demo"):
    d = tmp_path / line; d.mkdir(parents=True, exist_ok=True)
    (d / "docs").mkdir(exist_ok=True)
    (d / "docs" / "EXPERIMENTS.md").write_text("log")
    (d / "claims.yaml").write_text(yaml.safe_dump({"line": line, "claims": claims}))
    return d


def test_every_status_in_the_spec_is_classified_terminal_or_not():
    assert set(cc.STATUS) == {"open", "running", "holds", "narrowed", "falsified",
                              "withdrawn", "retired"}
    assert [s for s, t in cc.STATUS.items() if not t] == ["open", "running"]


def test_retired_is_terminal_so_a_line_can_close_without_answering_everything():
    """Without this, a question judged not worth answering has no terminal state and the line
    can never close except by answering all of them."""
    assert cc.STATUS["retired"] is True


def test_a_clean_table_passes(tmp_path):
    d = write(tmp_path, [BASE])
    errs, term, n = cc.check_line(d)
    assert errs == [] and (term, n) == (1, 1)


def test_terminal_claim_without_a_where_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "where": ""}])
    errs, _, _ = cc.check_line(d)
    assert any("cannot be answered without pointing at the answer" in e for e in errs)


def test_open_claim_without_a_where_is_allowed(tmp_path):
    """An unanswered question has nothing to point at yet — that must not be an error, or the
    table will quietly lose its open rows and report the line closed."""
    d = write(tmp_path, [{**BASE, "status": "open", "where": ""}])
    errs, term, n = cc.check_line(d)
    assert errs == [] and (term, n) == (0, 1)


def test_withdrawn_without_superseded_by_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "status": "withdrawn"}])
    errs, _, _ = cc.check_line(d)
    assert any("requires `superseded_by`" in e for e in errs)


def test_withdrawn_with_superseded_by_passes(tmp_path):
    d = write(tmp_path, [{**BASE, "status": "withdrawn", "superseded_by": "The corrected run."}])
    assert cc.check_line(d)[0] == []


def test_duplicate_ids_fail(tmp_path):
    d = write(tmp_path, [BASE, {**BASE, "claim": "A different assertion entirely here."}])
    assert any("duplicate id" in e for e in cc.check_line(d)[0])


def test_a_topic_is_not_a_claim(tmp_path):
    d = write(tmp_path, [{**BASE, "claim": "Era."}])
    errs, _, _ = cc.check_line(d)
    assert any("topic, not an assertion" in e or "full stop" in e for e in errs)


def test_unknown_status_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "status": "probably"}])
    assert any("is not one of" in e for e in cc.check_line(d)[0])


def test_where_pointing_at_a_missing_file_fails(tmp_path):
    d = write(tmp_path, [{**BASE, "where": "docs/NOPE.md"}])
    assert any("exists under neither" in e for e in cc.check_line(d)[0])


def test_the_real_lines_validate_and_neither_is_falsely_closed():
    """The repo's own tables, checked on every run. A line reporting CLOSED while its
    open-problems list is non-empty is the failure this whole file exists to catch."""
    for line in ("narrative", "shame-axis"):
        d = ROOT / "research" / line
        errs, term, n = cc.check_line(d)
        assert errs == [], f"{line}: {errs}"
        assert n > 0, f"{line}: no claims"
        assert term < n, f"{line} reports CLOSED ({term}/{n}) — verify that is really true"


# --------------------------------------------------------------------------- the build gate
def test_the_build_refuses_a_table_that_does_not_validate(tmp_path, monkeypatch):
    """The point of the gate. If a claims table is broken the site must not build — a page that
    renders a terminal claim with no evidence behind it is worse than no page."""
    import subprocess, sys as _s
    broken = ROOT / "research" / "_gate_probe"
    (broken / "docs").mkdir(parents=True, exist_ok=True)
    (broken / "docs" / "EXPERIMENTS.md").write_text("log")
    (broken / "claims.yaml").write_text(yaml.safe_dump({
        "line": "_gate_probe",
        "claims": [{"id": "x", "claim": "This claim is terminal but points nowhere.",
                    "status": "holds", "where": ""}]}))
    try:
        r = subprocess.run([_s.executable, str(ROOT / "scripts" / "build_pages.py"),
                            "--out", str(tmp_path / "site")], capture_output=True, text=True)
        assert r.returncode != 0, "the build accepted a table with a hole in it"
        assert "BUILD REFUSED" in r.stderr
        assert not (tmp_path / "site" / "index.html").exists(), "it wrote a page anyway"
    finally:
        import shutil; shutil.rmtree(broken)


def test_a_clean_build_produces_a_page_per_line_and_an_index(tmp_path):
    import subprocess, sys as _s
    r = subprocess.run([_s.executable, str(ROOT / "scripts" / "build_pages.py"),
                        "--out", str(tmp_path / "s")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = tmp_path / "s"
    assert (out / "index.html").exists()
    assert list((out / "assets").glob("site.*.css")), "no stylesheet emitted"
    for line in ("narrative", "shame-axis"):
        assert (out / line / "index.html").exists()
    # the index must not claim a line is closed while it has open rows
    idx = (out / "index.html").read_text()
    assert "still open" in idx


def test_every_page_links_a_stylesheet_that_exists(tmp_path):
    """A dangling stylesheet href unstyles the whole site while every page still returns 200 —
    the failure looks like a design problem and is actually a broken link. Cheap to pin."""
    import subprocess, sys as _s, re
    r = subprocess.run([_s.executable, str(ROOT / "scripts" / "build_pages.py"),
                        "--out", str(tmp_path / "s")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = tmp_path / "s"
    pages = list(out.rglob("index.html"))
    assert pages
    hrefs = set()
    for page in pages:
        m = re.search(r'<link rel="stylesheet" href="([^"]+)"', page.read_text())
        assert m, f"{page} links no stylesheet"
        target = (page.parent / m.group(1)).resolve()
        assert target.exists(), f"{page} links {m.group(1)}, which does not exist"
        hrefs.add(target)
    assert len(hrefs) == 1, f"pages disagree about the stylesheet: {hrefs}"


def test_the_stylesheet_name_is_content_hashed(tmp_path):
    """GitHub Pages serves assets with cache-control max-age=600. With a fixed filename a reader
    who visits during a deploy window gets the previous stylesheet against the current HTML, which
    is how the site misrepresented itself once. A new build must produce a new URL."""
    import subprocess, sys as _s, re
    def build_and_get_href(dest, mutate=None):
        theme = ROOT / "scripts" / "sitegen" / "theme.py"
        original = theme.read_text()
        try:
            if mutate:
                theme.write_text(original.replace("body{margin:0;", "body{margin:0;letter-spacing:0;"))
            subprocess.run([_s.executable, str(ROOT / "scripts" / "build_pages.py"),
                            "--out", str(dest)], capture_output=True, text=True, check=True)
            html = (dest / "index.html").read_text()
            return re.search(r'href="([^"]*site[^"]*\.css)"', html).group(1)
        finally:
            theme.write_text(original)
    a = build_and_get_href(tmp_path / "a")
    b = build_and_get_href(tmp_path / "b", mutate=True)
    assert re.match(r"assets/site\.[0-9a-f]{10}\.css", a), a
    assert a != b, "changing the stylesheet did not change its URL — caches will serve the old one"


def test_resolve_where_accepts_both_bases_and_reports_which():
    """A `where` may be line-relative or repo-root-relative; both are legitimate. What is not
    legitimate is resolving them in two places with two different assumptions, which is how every
    claim citing the shared instruments ledger came to render a 404."""
    narr = ROOT / "research" / "narrative"
    assert cc.resolve_where(narr, "docs/EXPERIMENTS.md") == "research/narrative/docs/EXPERIMENTS.md"
    assert cc.resolve_where(narr, "docs/INSTRUMENTS.md") == "docs/INSTRUMENTS.md"   # repo root
    assert cc.resolve_where(narr, "docs/EXPERIMENTS.md#h51").endswith("EXPERIMENTS.md#h51")
    assert cc.resolve_where(narr, "docs/NOPE.md") is None
    assert cc.resolve_where(narr, "") is None


def test_no_built_page_emits_a_link_that_cannot_resolve(tmp_path):
    """Every terminal claim links its evidence. Those links pointed into the SITE, which contains
    only index pages, so each one 404'd while the validator -- checking the repository -- passed.
    Checked offline: relative hrefs must exist in the output, and GitHub blob hrefs must name a
    file that exists in the repo."""
    import subprocess, sys as _s, re
    r = subprocess.run([_s.executable, str(ROOT / "scripts" / "build_pages.py"),
                        "--out", str(tmp_path / "s")], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    out = tmp_path / "s"
    BLOB = "https://github.com/bombadil-labs/model-research/blob/main/"
    bad = []
    for page in out.rglob("*.html"):
        for href in re.findall(r'href="([^"]+)"', page.read_text()):
            if href.startswith("#") or href == BLOB.rstrip("/").replace("/blob/main", ""):
                continue
            if href.startswith(BLOB):
                rel = href[len(BLOB):].split("#")[0]
                if not (ROOT / rel).exists():
                    bad.append(f"{page.name} -> {href} (no such file in the repo)")
            elif href.startswith(("http://", "https://")):
                continue
            else:
                if not (page.parent / href.split("#")[0]).exists():
                    bad.append(f"{page.name} -> {href} (not in the built site)")
    assert not bad, "unresolvable links:\n  " + "\n  ".join(bad)
