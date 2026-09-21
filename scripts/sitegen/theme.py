"""The shared design system for the public pages. One file, used by every page.

Derived from seed 3fb98521-2fc4-4a62-99a3-c01b4edf8ccf, recorded because the derivation is the
design rationale and is otherwise unrecoverable:

  mean nibble 8.03/15, the highest of four candidate seeds -> a light default ground
  'f' and 'c' tie at 4 occurrences each                    -> TWO primary accents, not one or three
      c = 12 -> hue 270deg (violet)   f = 15 -> hue 337deg (rose)   9 -> 202deg (blue support)
  only one absent hex char, the richest alphabet           -> one unified chrome across all pages
  last nibble 'f' = 15; halves sum 109 then 148            -> a crescendo; weight gained downward
  longest run 2                                            -> figures pair
  29 runs, the fewest                                      -> few large bands, not a fine rhythm

Both palettes pass the six checks in the dataviz validator (lightness band, chroma floor, CVD
separation over all pairs, normal-vision floor, contrast) against their own surface. Dark is
SELECTED, with its own steps, not an automatic inversion of light.
"""

SEED = "3fb98521-2fc4-4a62-99a3-c01b4edf8ccf"
LIGHT = {"v": "#6B4FC9", "r": "#BE3E6E", "b": "#1C7FA8"}
DARK = {"v": "#7C63D6", "r": "#D4577F", "b": "#2E92BE"}

CSS = """@import url('https://fonts.googleapis.com/css2?family=Newsreader:ital,opsz,wght@0,6..72,400;0,6..72,500;1,6..72,400&family=Archivo:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');
:root{--v:#6B4FC9;--r:#BE3E6E;--b:#1C7FA8;--ink:#16161C;--mut:#5C5C69;--paper:#FBFAF7;--card:#FFFFFF;--hair:#E4E1D9;--rule:#15151B}
@media (prefers-color-scheme:dark){:root:not([data-theme="light"]){--v:#7C63D6;--r:#D4577F;--b:#2E92BE;--ink:#ECECF2;--mut:#9A9AA6;--paper:#131318;--card:#1B1B22;--hair:#2C2C36;--rule:#ECECF2}}
:root[data-theme="dark"]{--v:#7C63D6;--r:#D4577F;--b:#2E92BE;--ink:#ECECF2;--mut:#9A9AA6;--paper:#131318;--card:#1B1B22;--hair:#2C2C36;--rule:#ECECF2}
*{box-sizing:border-box}
body{margin:0;background:var(--paper);color:var(--ink);font-family:'Archivo',ui-sans-serif,system-ui,sans-serif;-webkit-font-smoothing:antialiased;line-height:1.5}
a{color:var(--v)}a:hover{color:var(--r)}
.wrap{max-width:1220px;margin:0 auto;padding:0 clamp(18px,5vw,72px)}
.d{font-family:'Newsreader',Georgia,serif;font-weight:400}
.m{font-family:'IBM Plex Mono',ui-monospace,monospace;font-variant-numeric:tabular-nums}
.lab{font-size:11px;letter-spacing:.15em;text-transform:uppercase;color:var(--mut);font-weight:600}
.band{border-top:2px solid var(--rule);padding:clamp(30px,4.5vw,56px) 0}
.pair{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:clamp(20px,3vw,40px)}
@media(max-width:820px){.pair{grid-template-columns:1fr}}
.chrome{display:flex;align-items:baseline;gap:14px;padding:22px 0;font-size:13px;flex-wrap:wrap}
.chrome a{text-decoration:none}
h1.hero{margin:14px 0 18px;font-size:clamp(34px,5.4vw,64px);line-height:1.05;max-width:17ch;letter-spacing:-.015em}
h1.q{margin:10px 0 14px;font-size:clamp(26px,3.0vw,40px);line-height:1.13;max-width:30ch;letter-spacing:-.01em}
h2.s{margin:8px 0 10px;font-size:clamp(24px,2.9vw,38px);line-height:1.15}
.crescendo{margin:14px 0 0;font-size:clamp(26px,3.9vw,52px);line-height:1.14;max-width:21ch}
.claims{list-style:none;margin:20px 0 0;padding:0}
.claims li{display:grid;grid-template-columns:22px 1fr 196px 82px;gap:16px;align-items:start;padding:13px 0;border-bottom:1px solid var(--hair)}
.pre{display:inline-block;white-space:nowrap;font-size:9px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);border:1px solid var(--hair);border-radius:3px;padding:1px 5px;vertical-align:2px;margin-left:6px}
@media(max-width:820px){.claims li{grid-template-columns:20px 1fr;gap:10px}.claims li .ev,.claims li .st{grid-column:2}}
.claims a{color:var(--ink);text-decoration:none;font-size:15.5px;line-height:1.55}
.claims a:hover{color:var(--v)}
.ev{font-size:11.5px;line-height:1.5;color:var(--mut)}
.st{display:flex;flex-direction:column;align-items:flex-end;gap:2px}
@media(max-width:820px){.st{align-items:flex-start;flex-direction:row;gap:8px}}
.wd a{color:var(--mut);text-decoration:line-through;text-decoration-color:var(--mut)}
table{border-collapse:collapse;width:100%;font-size:13px}
th,td{text-align:left;padding:6px 10px;border-bottom:1px solid var(--hair)}
th{font-size:10px;letter-spacing:.12em;text-transform:uppercase;color:var(--mut);font-weight:600}
td.n{text-align:right;font-family:'IBM Plex Mono',monospace;font-variant-numeric:tabular-nums}
figure{margin:0}
svg{max-width:100%;height:auto}
.legend{display:flex;flex-wrap:wrap;gap:16px;font-size:12.5px;color:var(--mut);margin-top:12px}
.legend span{display:inline-flex;align-items:center;gap:7px}
.sw{width:11px;height:11px;border-radius:3px;display:inline-block}
.card{display:block;text-decoration:none;color:inherit;background:var(--card);border:1px solid var(--hair);border-radius:10px;padding:26px 28px 24px;transition:border-color .15s ease,transform .15s ease}
.card:hover{border-color:var(--v);transform:translateY(-2px)}
.card:hover h2{color:var(--v)}
.card h2{margin-top:6px}
footer{padding:36px 0 60px;font-size:13px;color:var(--mut);line-height:1.7}
.skip{position:absolute;left:-9999px}.skip:focus{left:8px;top:8px;background:var(--paper);padding:8px;z-index:9}
"""

# status -> (svg glyph, colour var, label, terminal). Shape is the primary channel so the table
# survives greyscale, colour blindness and forced-colors; colour only reinforces it.
GLYPH = {
 "holds":     ('<circle cx="9" cy="9" r="6" fill="var(--ink)"/>', "var(--ink)", "holds"),
 "narrowed":  ('<circle cx="9" cy="9" r="6" fill="none" stroke="var(--ink)" stroke-width="2"/>'
               '<path d="M9 3 A6 6 0 0 1 9 15 Z" fill="var(--ink)"/>', "var(--ink)", "narrowed"),
 "falsified": ('<path d="M4.5 4.5 L13.5 13.5 M13.5 4.5 L4.5 13.5" stroke="var(--r)" '
               'stroke-width="2.4" stroke-linecap="round"/>', "var(--r)", "falsified"),
 "withdrawn": ('<circle cx="9" cy="9" r="6" fill="none" stroke="var(--mut)" stroke-width="2"/>'
               '<path d="M5 13 L13 5" stroke="var(--mut)" stroke-width="2"/>', "var(--mut)", "withdrawn"),
 "retired":   ('<path d="M3.5 9 L14.5 9" stroke="var(--mut)" stroke-width="2.4" '
               'stroke-linecap="round"/>', "var(--mut)", "retired"),
 "running":   ('<circle cx="9" cy="9" r="6" fill="none" stroke="var(--b)" stroke-width="2"/>'
               '<circle cx="9" cy="9" r="2.2" fill="var(--b)"/>', "var(--b)", "running"),
 "open":      ('<circle cx="9" cy="9" r="6" fill="none" stroke="var(--b)" stroke-width="2" '
               'stroke-dasharray="2.6 2.4"/>', "var(--b)", "open"),
}
