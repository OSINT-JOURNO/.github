#!/usr/bin/env python3
"""Draw profile/assets/banner.svg, the animated banner at the top of the OSINT JOURNO organisation page.

Plain SVG animation: no scripts, no external files, so GitHub shows it. Text is drawn as outlines, so it looks the
same whatever fonts the viewer has. The globe turns (its meridians are re-drawn as ellipses through one turn); it has
no markers, so nothing on it stands for a position.

Needs: pip install fonttools, and JetBrains Mono (SIL Open Font License) as a variable .ttf.
Run:   python3 tools/make_banner.py /path/to/JetBrainsMono.ttf
"""
import math
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "profile", "assets", "banner.svg")
ALT = "OSINT JOURNO: open-source investigation for journalists. Verification tools, datasets and country guides, free and open source."
LINES = ["verify before you publish", "public records, country by country", "evidence graphics with their sources on them",
         "AI tools that show their working", "free tools, open data"]

W, H = 1200, 340
CX, CY, R = 190, 170, 116
SPIN = 24.0                     # seconds per turn of the globe
SLOT = 3.6                      # seconds per typed line
TX, TY = 412, 206
BG, GRID, TEAL, AMBER, TEXT, DIM = "#0b1016", "#16202b", "#2dd4bf", "#fbbf24", "#e6edf3", "#7d8b99"


def f(x):
    return f"{x:.3f}".rstrip("0").rstrip(".")


def build(font_file):
    from fontTools.ttLib import TTFont
    from fontTools.varLib.instancer import instantiateVariableFont
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen

    fonts = {}

    def outline(text, x, y, size, weight=400, spacing=0.0):
        if weight not in fonts:
            ft = instantiateVariableFont(TTFont(font_file), {"wght": weight})
            fonts[weight] = (ft.getGlyphSet(), ft.getBestCmap(), ft["hmtx"])
        gs, cmap, hmtx = fonts[weight]
        k, pen, cx = size / 1000, SVGPathPen(gs, ntos=lambda v: f"{v:.1f}".rstrip("0").rstrip(".")), x
        for ch in text:
            name = cmap[ord(ch)]
            gs[name].draw(TransformPen(pen, (k, 0, 0, -k, cx, y)))
            cx += hmtx[name][0] * k + spacing
        return pen.getCommands(), cx - x - spacing

    def T(text, x, y, size, fill, weight=400, spacing=0.0, extra=""):
        d, w = outline(text, x, y, size, weight, spacing)
        return f'<path d="{d}" fill="{fill}"{extra}/>', w

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" role="img" aria-label="{ALT}">',
         f"<title>{ALT}</title>",
         f'''<defs>
<clipPath id="card"><rect width="{W}" height="{H}" rx="18"/></clipPath>
<clipPath id="globe"><circle cx="{CX}" cy="{CY}" r="{R}"/></clipPath>
<pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse"><path d="M40 0H0V40" fill="none" stroke="{GRID}" stroke-width="1"/></pattern>
<radialGradient id="glow" cx="50%" cy="50%" r="50%"><stop offset="0" stop-color="{TEAL}" stop-opacity=".16"/><stop offset="1" stop-color="{TEAL}" stop-opacity="0"/></radialGradient>
<radialGradient id="shade" cx="38%" cy="35%" r="70%"><stop offset="0" stop-color="{TEAL}" stop-opacity=".10"/><stop offset="1" stop-color="{BG}" stop-opacity=".0"/></radialGradient>
<linearGradient id="fade" x1="0" x2="1"><stop offset="0" stop-color="{BG}" stop-opacity="0"/><stop offset=".25" stop-color="{BG}" stop-opacity="0"/><stop offset="1" stop-color="{BG}" stop-opacity=".9"/></linearGradient>
</defs>''',
         f'<g clip-path="url(#card)"><rect width="{W}" height="{H}" fill="{BG}"/><rect width="{W}" height="{H}" fill="url(#grid)"/>'
         f'<rect width="{W}" height="{H}" fill="url(#fade)"/>',
         f'<circle cx="{CX}" cy="{CY}" r="{R + 44}" fill="url(#glow)"/>',
         f'<circle cx="{CX}" cy="{CY}" r="{R}" fill="url(#shade)" stroke="{TEAL}" stroke-opacity=".55" stroke-width="1.5"/>']

    # latitude lines (fixed; seen from slightly above, so they are flat ellipses)
    g = [f'<g clip-path="url(#globe)" fill="none" stroke="{TEAL}" stroke-width="1">']
    tilt = 0.18
    for lat in (-60, -30, 0, 30, 60):
        y = CY - R * math.sin(math.radians(lat))
        rx = R * math.cos(math.radians(lat))
        g.append(f'<ellipse cx="{CX}" cy="{f(y)}" rx="{f(rx)}" ry="{f(rx * tilt)}" stroke-opacity="{".4" if lat == 0 else ".22"}"/>')
    # meridians: six great circles 30 degrees apart; as the globe turns, each one's width runs through |cos|.
    steps = 48
    for k in range(6):
        vals = []
        for s in range(steps + 1):
            a = math.radians(k * 30 + s * 360 / steps)
            vals.append(f(abs(R * math.cos(a))))
        op = []
        for s in range(steps + 1):
            a = math.radians(k * 30 + s * 360 / steps)
            op.append(f(.12 + .3 * max(0.0, math.sin(a))))      # brighter on the near side
        g.append(f'<ellipse cx="{CX}" cy="{CY}" ry="{R}" rx="{vals[0]}" stroke-opacity="{op[0]}">'
                 f'<animate attributeName="rx" values="{";".join(vals)}" dur="{f(SPIN)}s" repeatCount="indefinite"/>'
                 f'<animate attributeName="stroke-opacity" values="{";".join(op)}" dur="{f(SPIN)}s" repeatCount="indefinite"/></ellipse>')
    g.append("</g>")
    o += g

    # text
    o.append(T("// OPEN-SOURCE INVESTIGATION FOR JOURNALISTS", TX - 32, 78, 17, TEAL, 500, 1.6)[0])
    o.append(T("OSINT JOURNO", TX - 34, 146, 66, TEXT, 800, 4)[0])
    o.append(T(">", TX - 32, TY, 24, AMBER, 700)[0])
    period = SLOT * len(LINES)
    for i, line in enumerate(LINES):
        el, w = T(line, TX, TY, 24, TEXT, 400, 0, f' clip-path="url(#c{i})"')
        w += 5
        a, b, c, d = i * SLOT, i * SLOT + 1.1, (i + 1) * SLOT - .45, (i + 1) * SLOT - .1   # type in, hold, wipe out
        kt = ";".join(f(x / period) for x in ((0, a, b, c, d, period) if i else (0, b, c, d, period)))
        wv = f"0;0;{f(w)};{f(w)};0;0" if i else f"0;{f(w)};{f(w)};0;0"
        xv = ";".join(f(TX + float(x)) for x in wv.split(";"))
        ov = "0;1;1;1;0;0" if i else "1;1;1;0;0"
        o.append(f'<clipPath id="c{i}"><rect x="{TX}" y="{TY - 26}" height="36" width="0"><animate attributeName="width" '
                 f'values="{wv}" keyTimes="{kt}" dur="{f(period)}s" repeatCount="indefinite"/></rect></clipPath>'
                 f'{el}<rect y="{TY - 20}" width="12" height="26" fill="{AMBER}" opacity="0"><animate attributeName="x" '
                 f'values="{xv}" keyTimes="{kt}" dur="{f(period)}s" repeatCount="indefinite"/><animate attributeName="opacity" '
                 f'values="{ov}" keyTimes="{kt}" dur="{f(period)}s" calcMode="discrete" repeatCount="indefinite"/></rect>')
    o.append(T("tools  ·  datasets  ·  country guides  ·  training", TX - 32, 258, 19, TEXT, 500)[0])
    o.append(T("osintjourno.com  ·  instagram @osint_journo  ·  osintjourno.substack.com", TX - 32, 300, 16.5, DIM)[0])
    o.append("</g></svg>")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write("\n".join(o) + "\n")
    print(f"{os.path.relpath(OUT, ROOT)}: {os.path.getsize(OUT)} bytes")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else "JetBrainsMono.ttf")
