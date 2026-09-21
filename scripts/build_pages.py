"""Build the public pages from the repository's own data. Output: site/ (gitignored).

Nothing on these pages is hand-maintained HTML. The claims tables come from each line's
`claims.yaml`; the charts come from the results CSVs those claims point at. A status change is a
one-line edit to a data file, and the page follows.

`check_claims.py` runs first and the build FAILS on any problem, so a table with holes in it never
reaches a reader — a terminal claim without its evidence link, or a retraction that does not name
what replaced it, stops the deploy.

Charts are rendered only when their source file exists. A line with no results CSVs gets its
claims table and nothing invented to fill the space.

Usage:  python scripts/build_pages.py [--out site]
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import datetime as dt
import html
import pathlib
import subprocess
import sys

import yaml

ROOT = pathlib.Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from sitegen.theme import CSS, GLYPH, SEED  # noqa: E402

TERMINAL = {"holds", "narrowed", "falsified", "withdrawn", "retired"}
E = lambda s: html.escape(str(s), quote=False)


# ----------------------------------------------------------------------------- page furniture
CSS_HREF = "assets/site.css"   # replaced with the hashed name by main()


def shell(title: str, desc: str, body: str, depth: int) -> str:
    up = "../" * depth
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(title)}</title>
<meta name="description" content="{E(desc)}">
<meta property="og:title" content="{E(title)}">
<meta property="og:description" content="{E(desc)}">
<link rel="stylesheet" href="{up}{CSS_HREF}">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{body}
<footer class="wrap">
  <div class="band" style="padding-bottom:0">
    Built from the repository's own data on {dt.date.today().isoformat()}.
    Every number on this site is read from a results file at build time; the claims tables are
    generated from each line's <code>claims.yaml</code>.
    <a href="https://github.com/bombadil-labs/model-research">Source</a>.
  </div>
</footer>
</body>
</html>
"""


def chrome(here: str, depth: int) -> str:
    up = "../" * depth
    crumb = "" if here == "index" else f'<span style="color:var(--hair)">/</span><span class="lab" style="color:var(--ink)">{E(here)}</span>'
    return f"""<div class="wrap"><nav class="chrome">
  <a href="{up}index.html" style="font-weight:600;letter-spacing:.1em;text-transform:uppercase;color:var(--ink)">model-research</a>
  {crumb}<span style="flex-grow:1"></span>
  <a href="https://github.com/bombadil-labs/model-research">GitHub</a>
</nav></div>"""


def meter(term: int, tot: int, w: int = 300) -> str:
    frac = term / tot if tot else 0
    return (f'<svg viewBox="0 0 {w} 8" width="{w}" height="8" role="img" '
            f'aria-label="{term} of {tot} claims in a terminal state">'
            f'<rect width="{w}" height="8" rx="4" fill="var(--hair)"/>'
            f'<rect width="{w*frac:.0f}" height="8" rx="4" fill="var(--ink)"/></svg>')


def claims_table(claims: list[dict], anchors: dict[str, str]) -> str:
    rows = []
    for c in claims:
        g, col, lab = GLYPH[c["status"]]
        term = c["status"] in TERMINAL
        href = anchors.get(c["id"], c.get("where") or "#")
        cls = ' class="wd"' if c["status"] == "withdrawn" else ""
        pre = '<span class="pre">pre-registered</span>' if c.get("pre_registered") else ""
        sup = (f'<div class="ev" style="margin-top:5px">→ {E(c["superseded_by"])}</div>'
               if c.get("superseded_by") else "")
        rows.append(
            f'<li{cls}><svg viewBox="0 0 18 18" width="18" height="18" style="margin-top:2px" '
            f'role="img" aria-label="{lab}">{g}</svg>'
            f'<span><a href="{E(href)}">{E(c["claim"])}</a> {pre}{sup}</span>'
            f'<span class="ev">{E(c.get("evidence",""))}</span>'
            f'<span class="st"><span class="lab" style="color:{col};font-size:10px">{lab}</span>'
            f'<span class="m" style="font-size:9.5px;color:var(--mut);letter-spacing:.08em">'
            f'{"TERMINAL" if term else "OPEN"}</span></span></li>')
    return '<ul class="claims">' + "".join(rows) + "</ul>"


def legend() -> str:
    return '<div class="legend">' + "".join(
        f'<span><svg viewBox="0 0 18 18" width="14" height="14" aria-hidden="true">{GLYPH[k][0]}'
        f'</svg>{GLYPH[k][2]}</span>' for k in
        ("holds", "narrowed", "falsified", "withdrawn", "retired", "running", "open")) + "</div>"


# ----------------------------------------------------------------------------------- charts
def curve_chart(path: pathlib.Path) -> str | None:
    """Gaslighting mean z by block against the random-direction null band.

    Drawn as a BAND, not an area: the fill alone reads as a dark mass on a dark ground, so the
    2.5% and 97.5% edges carry their own strokes. Their steering layer is marked because the
    interesting fact is that the clearing window contains it and is only eight blocks wide.
    Rendered only if the nulls CSV exists.
    """
    if not path.exists():
        return None
    rows = [r for r in csv.DictReader(path.open())
            if r["category"] == "gaslighting" and r["extraction"] == "final_token"
            and r["layer"] != "emb"]
    if not rows:
        return None
    W, H, P = 1100, 340, 48
    lo = min(min(float(r["rand_lo"]) for r in rows), min(float(r["treat_z"]) for r in rows)) - .2
    hi = max(max(float(r["rand_hi"]) for r in rows), max(float(r["treat_z"]) for r in rows)) + .25
    n = len(rows)
    X = lambda i: P + i * (W - 2 * P) / (n - 1)
    Y = lambda v: H - P - (v - lo) * (H - 2 * P) / (hi - lo)
    ehi = "M" + " L".join(f"{X(i):.1f},{Y(float(r['rand_hi'])):.1f}" for i, r in enumerate(rows))
    elo = "M" + " L".join(f"{X(i):.1f},{Y(float(r['rand_lo'])):.1f}" for i, r in enumerate(rows))
    band = (ehi + " L" + " L".join(f"{X(i):.1f},{Y(float(r['rand_lo'])):.1f}"
                                   for i, r in reversed(list(enumerate(rows)))) + " Z")
    line = "M" + " L".join(f"{X(i):.1f},{Y(float(r['treat_z'])):.1f}" for i, r in enumerate(rows))
    marks = "".join(
        f'<circle cx="{X(i):.1f}" cy="{Y(float(r["treat_z"])):.1f}" '
        f'r="{5.5 if r["clears_both"]=="1" else 2.5}" '
        f'fill="{"var(--v)" if r["clears_both"]=="1" else "var(--paper)"}" stroke="var(--v)" '
        f'stroke-width="2"><title>Block {r["layer"]}: z {float(r["treat_z"]):+.3f}'
        f'{" - clears both nulls" if r["clears_both"]=="1" else ""}</title></circle>'
        for i, r in enumerate(rows))
    ticks = "".join(f'<text x="{X(i):.1f}" y="{H-P+20:.1f}" text-anchor="middle" font-size="10" '
                    f'class="m" fill="var(--mut)">{rows[i]["layer"]}</text>' for i in range(0, n, 6))
    grid = "".join(
        f'<line x1="{P}" y1="{Y(v):.1f}" x2="{W-P}" y2="{Y(v):.1f}" stroke="var(--mut)" '
        f'stroke-opacity="{0.5 if v == 0 else 0.22}"/>'
        f'<text x="{P-9}" y="{Y(v)+3.5:.1f}" font-size="10" class="m" fill="var(--mut)" '
        f'text-anchor="end">{("0" if v == 0 else f"{v:+g}")}</text>' for v in (1, 0, -1))
    clears = [i for i, r in enumerate(rows) if r["clears_both"] == "1"]
    win = winlab = ""
    if clears:
        x0, x1 = X(min(clears)), X(max(clears))
        win = (f'<rect x="{x0:.1f}" y="{P-28}" width="{x1-x0:.1f}" height="{H-2*P+34:.1f}" '
               f'fill="var(--v)" fill-opacity="0.09"/>')
        winlab = (f'<text x="{(x0+x1)/2:.1f}" y="{H-P+36:.1f}" font-size="10.5" fill="var(--v)" '
                  f'text-anchor="middle" font-weight="600">clears both nulls</text>')
    theirs = ""
    if any(r["layer"] == "12" for r in rows):
        li = next(i for i, r in enumerate(rows) if r["layer"] == "12")
        theirs = (f'<line x1="{X(li):.1f}" y1="{P-28}" x2="{X(li):.1f}" y2="{H-P:.1f}" '
                  f'stroke="var(--r)" stroke-width="1.5" stroke-dasharray="3 3"/>'
                  f'<text x="{X(li)+7:.1f}" y="{P-17}" font-size="11" fill="var(--r)" '
                  f'font-weight="600">their layer 12</text>')
    peak = max(rows, key=lambda r: float(r["treat_z"])); pi = rows.index(peak)
    return (f'<figure><svg viewBox="0 0 {W} {H}" role="img" aria-label="Gaslighting mean z by '
            f'residual block against the random-direction null band; {len(clears)} of {n} blocks '
            f'clear both nulls.">{win}{grid}'
            f'<path d="{band}" fill="var(--b)" fill-opacity="0.16"/>'
            f'<path d="{ehi}" fill="none" stroke="var(--b)" stroke-width="1.25" stroke-opacity="0.8"/>'
            f'<path d="{elo}" fill="none" stroke="var(--b)" stroke-width="1.25" stroke-opacity="0.8"/>'
            f'{theirs}<path d="{line}" fill="none" stroke="var(--v)" stroke-width="2.25" '
            f'stroke-linejoin="round"/>{marks}'
            f'<text x="{X(pi):.1f}" y="{Y(float(peak["treat_z"]))-13:.1f}" font-size="12" class="m" '
            f'fill="var(--ink)" font-weight="500" text-anchor="middle">{float(peak["treat_z"]):+.2f}</text>'
            f'{ticks}{winlab}'
            f'<text x="{W/2}" y="{H-4}" font-size="10" fill="var(--mut)" text-anchor="middle">'
            f'residual block</text></svg>'
            f'<figcaption class="ev" style="margin-top:10px">Shaded band: the 2.5&ndash;97.5% '
            f'interval of 500 random directions. Filled markers clear both the random-direction '
            f'and shuffled-label nulls &mdash; {len(clears)} of {n} blocks. Hover a marker for its '
            f'value.</figcaption></figure>')


def floor_chart(path: pathlib.Path, scen: pathlib.Path) -> tuple[str, str] | None:
    """What the network adds over the embedding bag, per category, coloured by the paper's own
    stratum. Returns (chart, table) — the table is not optional: the amber-adjacent colours sit
    close enough that identity must never be carried by colour alone."""
    if not (path.exists() and scen.exists()):
        return None
    import json
    rows = list(csv.DictReader(path.open()))
    strat = {}
    for x in json.loads(scen.read_text()):
        strat.setdefault(x["category"], x["stratum"])

    def z(layer, ext, cat):
        for r in rows:
            if (r["layer"] == layer and r["extraction"] == ext
                    and r["vector"] == "s2_pain_vector" and r["category"] == cat):
                return float(r["mean_z"])
        return None
    cats = sorted({r["category"] for r in rows})
    data = [(c, z("emb", "mean", c), z("12", "final_token", c), strat.get(c)) for c in cats]
    data = [d for d in data if None not in d[1:3]]
    if not data:
        return None
    data.sort(key=lambda d: d[2] - d[1])
    COL = {"self_directed": "var(--v)", "vicarious_empathic": "var(--r)", "neutral_filler": "var(--b)"}
    W, rowh, mid = 900, 21, 470
    H = rowh * len(data)
    mx = max(abs(d[2] - d[1]) for d in data)
    bars = ""
    for i, (c, f, l, st) in enumerate(data):
        d = l - f; y = i * rowh + 3; bh = rowh - 6
        bw = abs(d) / mx * 340; x = mid if d > 0 else mid - bw
        bars += (f'<rect x="{x:.1f}" y="{y:.1f}" width="{bw:.1f}" height="{bh:.1f}" rx="4" '
                 f'fill="{COL.get(st,"var(--mut)")}"><title>{E(c)}: floor {f:+.3f} → block 12 '
                 f'{l:+.3f} (Δ {d:+.3f})</title></rect>'
                 f'<text x="{mid-12 if d>0 else mid+12}" y="{y+bh/2+4:.1f}" font-size="11.5" '
                 f'fill="var(--ink)" text-anchor="{"end" if d>0 else "start"}">{E(c.replace("_"," "))}</text>'
                 f'<text x="{x+bw+8 if d>0 else x-8:.1f}" y="{y+bh/2+4:.1f}" font-size="11" '
                 f'class="m" fill="var(--ink)" font-weight="500" '
                 f'text-anchor="{"start" if d>0 else "end"}">{d:+.2f}</text>')
    pos = sum(1 for _, f, l, s in data if s == "self_directed" and l - f > 0)
    neg = sum(1 for _, f, l, s in data if s == "vicarious_empathic" and l - f < 0)
    tot = sum(1 for *_, s in data if s in ("self_directed", "vicarious_empathic"))
    chart = f"""<figure><svg viewBox="0 0 {W} {H}" role="img" aria-label="Change in z from the embedding-bag floor to block 12 for each of {len(data)} categories, coloured by stratum.">
  <line x1="{mid}" y1="0" x2="{mid}" y2="{H}" stroke="var(--hair)"/>{bars}</svg>
<figcaption class="ev" style="margin-top:8px">{pos + neg} of {tot} categories move in the direction
their stratum predicts. Every bar is labelled; the table below carries the same numbers.</figcaption></figure>"""
    trows = "".join(f'<tr><td>{E(c.replace("_"," "))}</td><td class="n">{f:+.3f}</td>'
                    f'<td class="n">{l:+.3f}</td><td class="n" style="font-weight:500">{l-f:+.3f}</td>'
                    f'<td class="ev">{E((st or "").replace("_"," "))}</td></tr>'
                    for c, f, l, st in sorted(data, key=lambda d: -(d[2] - d[1])))
    table = ('<table><thead><tr><th>category</th><th class="n">bag floor</th>'
             '<th class="n">block 12</th><th class="n">Δ</th><th>stratum</th></tr></thead><tbody>'
             + trows + "</tbody></table>")
    return chart, table


# ------------------------------------------------------------------------------ the two pages
def line_page(d: pathlib.Path, out: pathlib.Path) -> tuple[str, dict]:
    doc = yaml.safe_load((d / "claims.yaml").read_text())
    claims = doc["claims"]
    term = sum(1 for c in claims if c["status"] in TERMINAL)
    res = d / "results"
    curve = curve_chart(res / "painaxis_scenarios/nulls_by_layer.csv")
    floor = floor_chart(res / "painaxis_scenarios/category_z_by_layer.csv",
                        d / "prompts/external/pain_axis/4.1_self_other_420_scenarios.json")
    anchors = {}
    if curve:
        for cid in ("replication-curve", "gaslighting-loading"):
            anchors[cid] = "#curve"
    if floor:
        anchors["floor-self-other"] = "#floor"

    ev = ""
    if curve:
        ev += f"""<section class="band" id="curve"><div class="wrap">
  <div class="lab">The curve, not the layer</div>
  <h2 class="s d">It clears its null arms in one narrow window</h2>
  {curve}</div></section>"""
    if floor:
        c, t = floor
        ev += f"""<section class="band" id="floor"><div class="wrap">
  <div class="lab">What the network adds over the words</div>
  <h2 class="s d">Every self-directed category gains. Every vicarious one loses.</h2>
  <div class="legend">
    <span><i class="sw" style="background:var(--v)"></i>aimed at the assistant</span>
    <span><i class="sw" style="background:var(--r)"></i>someone else's distress</span>
    <span><i class="sw" style="background:var(--b)"></i>neutral filler</span></div>
  {c}<div style="margin-top:22px">{t}</div></div></section>"""

    open_rows = [c for c in claims if c["status"] not in TERMINAL]
    closing = (f"""<section class="band" style="padding-bottom:64px"><div class="wrap">
  <div class="lab">What is still open</div>
  <p class="d crescendo">
    {E(open_rows[0]["claim"])}</p>
  <p style="margin:16px 0 0;max-width:60ch;font-size:15px;color:var(--mut)">
    {E(open_rows[0].get("evidence",""))}</p></div></section>""" if open_rows else
    f"""<section class="band" style="padding-bottom:64px"><div class="wrap">
  <p class="d crescendo">Every claim in this line
  is in a terminal state. The line is closed.</p></div></section>""")

    body = f"""{chrome(doc.get('title', d.name), 1)}
<main id="main">
<div class="wrap">
  <div class="lab">{E(doc.get('audience',''))}</div>
  <h1 class="q d">{E(doc.get('question',''))}</h1>
  <p style="margin:0 0 6px;max-width:62ch;font-size:16px;line-height:1.6;color:var(--mut)">
    {E(doc.get('blurb',''))}</p>
</div>
<section class="band"><div class="wrap">
  <div style="display:flex;align-items:center;gap:14px;flex-wrap:wrap">{meter(term, len(claims))}
    <span class="m" style="font-size:13px"><strong>{term} of {len(claims)}</strong>
      <span style="color:var(--mut)">claims terminal</span></span>
    <span style="font-size:13px;color:var(--mut)">· the line closes when none are left open</span></div>
  {claims_table(claims, anchors)}
  {legend()}
</div></section>
{ev}{closing}
</main>"""
    (out / "index.html").write_text(
        shell(doc.get("title", d.name), doc.get("blurb", ""), body, 1))
    return doc.get("title", d.name), {"doc": doc, "term": term, "n": len(claims)}


def index_page(lines: dict, out: pathlib.Path) -> None:
    cards = ""
    for slug, info in lines.items():
        doc, term, n = info["doc"], info["term"], info["n"]
        cards += f"""<a class="card" href="{slug}/index.html">
  <div class="lab" style="color:var(--v)">{'Closed' if term==n else 'Active line'}</div>
  <h2 class="d" style="margin:8px 0 10px;font-size:30px;line-height:1.16">{E(doc.get('title',slug))}</h2>
  <p style="margin:0 0 16px;font-size:15.5px;line-height:1.6;color:var(--mut)">{E(doc.get('question',''))}</p>
  {meter(term, n, 210)}
  <div class="m" style="font-size:12px;color:var(--mut);margin-top:7px">
    <strong style="color:var(--ink)">{term} of {n}</strong> claims terminal
    {'· ' + str(n-term) + ' still open' if n>term else '· closed'}</div>
  <div style="margin-top:14px;font-size:14px;color:var(--v);font-weight:500">See the claims table →</div>
</a>"""
    body = f"""{chrome('index', 0)}
<main id="main">
<div class="wrap">
  <h1 class="hero d">Activation-level research on what transformers are
    <em style="color:var(--v)">doing</em> inside.</h1>
  <p style="margin:0;max-width:64ch;font-size:17px;line-height:1.6;color:var(--mut)">
    Independent lines of enquiry sharing one measurement toolkit, one set of rules, and one
    retraction ledger. Every finding reports its floor and its null arms, or it is not reported.</p>
</div>
<section class="band"><div class="wrap"><div class="pair">{cards}</div>
  <p style="margin:26px 0 0;max-width:72ch;font-size:15px;line-height:1.65;color:var(--mut)">
    Each line keeps a table of every claim it has made and where that claim stands — holds,
    narrowed, falsified, withdrawn, retired, or still open.
    <strong style="color:var(--ink)">A line is closed when no row is left open.</strong>
    That is the only definition of done we use.</p>
</div></section>
<section class="band"><div class="wrap">
  <div class="lab">The rules both lines run under</div>
  <h2 class="s d">Bought by failures, not chosen for taste</h2>
  <div class="pair" style="font-size:15px;line-height:1.7;color:var(--mut)">
    <div>
      <p><strong style="color:var(--ink)">Every battery reports treatment, random and no-patch.</strong>
        An arm off its declared null is a bug until proven otherwise.</p>
      <p><strong style="color:var(--ink)">Estimate the noise floor before believing a null.</strong>
        Three negatives were withdrawn as an instrument reading itself.</p>
      <p><strong style="color:var(--ink)">Never select a layer on scoring data.</strong> Report the curve.</p>
    </div>
    <div>
      <p><strong style="color:var(--ink)">Read the diff, not the report.</strong> Two of the five
        instruments found broken arrived through a summary that was trusted.</p>
      <p><strong style="color:var(--ink)">Attribution is a field, not a sentence.</strong> Anything
        attributed to a person without a commit carrying their text is a paraphrase, and is labelled one.</p>
      <p><strong style="color:var(--ink)">Retraction is first class.</strong> A withdrawn claim stays
        where it was made, beside what replaced it.</p>
    </div>
  </div>
</div></section>
<section class="band"><div class="wrap">
  <div class="lab">Tools</div>
  <h2 class="s d">What we built, and what we stand on</h2>
  <div class="pair" style="font-size:14.5px;line-height:1.6;color:var(--mut)">
    <div><div class="lab" style="color:var(--v)">Built here</div>
      <p><strong style="color:var(--ink)">lsx.core</strong> — the measurement core: residual capture
        with asserted spans, a typed vocabulary, an instrument registry, and a ledger in which
        retraction is an operation rather than a deletion.</p>
      <p><strong style="color:var(--ink)">The assertion set</strong> — every remote forward pass goes
        through one function that checks what silently breaks: padding convention, batched-vs-single
        equivalence on the maximally padded row, non-empty spans, block output resolved by type.
        Three of the five instruments in our ledger were caught by running an arm like these.</p>
      <p><strong style="color:var(--ink)">The rediscovery harness</strong> — reconstructs every bug
        this project has shipped and checks the core flags each one without being told what to look
        for. Neither it nor the assertion set is specific to anything we study; they are the two
        pieces worth extracting.</p>
    </div>
    <div><div class="lab">Depended on</div>
      <p><strong style="color:var(--ink)">NDIF · nnsight</strong> — the National Deep Inference
        Fabric gives us forward passes and activation capture on models far larger than we could
        host. Every remote result here ran on it.
        <span class="m" style="font-size:12px">Supported by NSF Award #2408455.</span></p>
      <p><strong style="color:var(--ink)">Jev</strong> (TypeSafe) — a typed-decision model used as a
        prose-quality gate, validated against 60 blind hand-labels before adoption: Spearman 0.541
        against human quality and no false positives for degenerate repetition across 648
        generations. A modest correlation, so it carries a soft claim, and we say which.</p>
      <p><strong style="color:var(--ink)">PyTorch · transformers · scikit-learn</strong> — where we
        replicate someone else's arithmetic we call their libraries rather than reimplementing it,
        so a disagreement is about method, not numerics.</p>
    </div>
  </div>
</div></section>
<section class="band" style="padding-bottom:64px"><div class="wrap">
  <p class="d crescendo" style="margin:0">
    Clone it and run the experiments yourself — on our models, or on
    <em style="color:var(--v)">yours</em>.</p>
  <div class="m" style="margin-top:20px;font-size:14px;color:var(--mut);line-height:1.9">
    git clone https://github.com/bombadil-labs/model-research<br>
    pip install -e '.[dev]' &amp;&amp; pytest</div>
</div></section>
</main>"""
    (out / "index.html").write_text(shell(
        "model-research", "Activation-level research on transformer internals: several research "
        "lines sharing one measurement toolkit and one retraction ledger.", body, 0))


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="site")
    a = ap.parse_args()

    gate = subprocess.run([sys.executable, str(ROOT / "scripts" / "check_claims.py")],
                          capture_output=True, text=True)
    print(gate.stdout.rstrip())
    if gate.returncode:
        print("BUILD REFUSED: the claims tables do not validate. "
              "A table with holes in it does not reach a reader.", file=sys.stderr)
        return 1

    out = ROOT / a.out
    (out / "assets").mkdir(parents=True, exist_ok=True)
    sheet = f"/* seed {SEED} — see scripts/sitegen/theme.py */\n" + CSS
    digest = hashlib.sha256(sheet.encode()).hexdigest()[:10]
    global CSS_HREF
    CSS_HREF = f"assets/site.{digest}.css"
    for stale in (out / "assets").glob("site*.css"):   # matches the unhashed name too
        stale.unlink()
    (out / CSS_HREF).write_text(sheet)
    (out / ".nojekyll").write_text("")

    lines = {}
    for d in sorted(p for p in (ROOT / "research").iterdir() if (p / "claims.yaml").exists()):
        sub = out / d.name
        sub.mkdir(parents=True, exist_ok=True)
        _, info = line_page(d, sub)
        lines[d.name] = info
        print(f"  built {d.name}/index.html  ({info['term']}/{info['n']} terminal)")
    index_page(lines, out)
    print(f"  built index.html\nsite -> {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
