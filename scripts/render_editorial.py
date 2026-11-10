#!/usr/bin/env python3
"""
render_editorial.py: editorial-style profile cards (cream paper, serif display,
ink blue accent, Bauhaus colour tiles). Reads contributions.json for the live
cards, so the daily workflow keeps them current.

  python scripts/render_editorial.py        -> writes cards/*.svg

Fonts (OFL: Instrument Serif, IBM Plex Mono) are subset per card to the exact
glyphs used and embedded as base64, so GitHub renders them identically everywhere.
"""
import base64
import datetime as dt
import html
import io
import json
import os
import re
from collections import OrderedDict

from fontTools import subset
from fontTools.ttLib import TTFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FONT_DIR = os.path.join(ROOT, "assets", "fonts")
OUT = os.path.join(ROOT, "cards")

# ──────────────────────────── PALETTE ────────────────────────────
PAPER, LINE, INK, MUTE, FAINT = "#F7F5EF", "#E4DFD3", "#141311", "#6E6A62", "#B9B3A6"
BLUE, RED, YELLOW = "#2A3FD9", "#D2202F", "#F5C518"
HEAT = ["#E9E7F6", "#C3C8F2", "#8F99EA", "#5566DF", "#2A3FD9"]
W = 880

# ──────────────────────────── CONTENT ────────────────────────────
KICKER = "DEMAND PLANNER  ·  AI SUPPLY CHAIN BUILDER  ·  DUBAI"
TAGLINE = ["I plan demand for GCC retail and build the AI tools",
           "that make planning faster. Then I teach it."]
SITE = "vinayakbhadani.com"
NOW = [
    ("Building SupplyMind", "agentic planning tools for the GCC"),
    ("APICS CPIM", "in progress, Feb 2027"),
    ("Open to planning roles", "demand / S&OP, UAE"),
    ("Teaching", "AI-Ready Supply Chain Academy"),
]
# Real counts outside GitHub's calendar (update when they change)
LIVE_APPS = 13      # production apps on Vercel (vercel project ls)
REELS = 55          # SupplyMind Reels built in code (HyperFrames + GSAP)

TILES = [
    ("BUILD", BLUE, "#FFFFFF", "14+ live tools",
     ["Forecasting, S&OP, inventory and", "sourcing tools, benchmark to daily use."]),
    ("BRAND", RED, "#FFFFFF", "7,000+ followers",
     ["Writing on supply chain and AI in", "the GCC, on LinkedIn and SupplyMind."]),
    ("PLAN", YELLOW, INK, "20+ airports",
     ["Led S&OP across GCC duty-free,", "about 100K units a month."]),
]

PROJECTS = [
    ("supplymind-hub", BLUE, ["Portfolio + SupplyMind hub: 14+ live", "tools, AI forecast audits and the", "AI-Ready Supply Chain Academy."], "HTML  ·  live"),
    ("planning-portfolio", RED, ["Planning is a decision system. Eight", "named agents build the page live", "in a swarm. Next.js on Vercel."], "Next.js  ·  live"),
    ("gcc-forecasting-benchmark", YELLOW, ["Hijri-aware regressors cut WAPE 13%", "and bias from +9.5% to -3.1%.", "Hierarchical, CI accuracy gates."], "Python  ·  37 tests"),
    ("sop-decision-engine", BLUE, ["Replenishment from inventory policy,", "every number traceable. 20% less", "safety stock, same service level."], "Python  ·  61 tests"),
    ("alphaos", RED, ["Agentic multi-market trading platform", "that publishes its own walk-forward", "result, even when it loses."], "TypeScript  ·  live"),
    ("tradeforge", YELLOW, ["China to UAE / India sourcing intel:", "turns trend signals into cited", "import opportunity dossiers."], "Next.js  ·  live"),
]


# ──────────────────────────── FONTS ────────────────────────────
FONTS = {
    "serif": "InstrumentSerif-Regular.ttf",
    "serif-i": "InstrumentSerif-Italic.ttf",
    "mono": "IBMPlexMono-Regular.ttf",
    "mono-b": "IBMPlexMono-Bold.ttf",
}
FAMILY = {"serif": ("IS", "normal"), "serif-i": ("IS", "italic"),
          "mono": ("PM", "normal"), "mono-b": ("PMB", "normal")}


def font_face(key, text):
    fam, style = FAMILY[key]
    f = TTFont(os.path.join(FONT_DIR, FONTS[key]))
    opts = subset.Options()
    opts.layout_features = ["*"]
    opts.name_IDs = ["*"]
    s = subset.Subsetter(opts)
    s.populate(text=text + " ")
    s.subset(f)
    buf = io.BytesIO()
    f.save(buf)
    b64 = base64.b64encode(buf.getvalue()).decode()
    return (f"@font-face{{font-family:'{fam}';font-style:{style};"
            f"src:url(data:font/ttf;base64,{b64}) format('truetype');}}")


_TT = {}


def measure(text, key, size):
    if key not in _TT:
        _TT[key] = TTFont(os.path.join(FONT_DIR, FONTS[key]))
    f = _TT[key]
    cmap, hmtx, upm = f.getBestCmap(), f["hmtx"], f["head"].unitsPerEm
    return sum(hmtx[cmap.get(ord(ch), cmap[32])][0] for ch in text) * size / upm


class Card:
    def __init__(self, w, h, bg=PAPER, stroke=LINE, rx=14):
        self.w, self.h, self.bg, self.stroke, self.rx = w, h, bg, stroke, rx
        self.body, self.css = [], []
        self.used = {k: "" for k in FONTS}

    def text(self, x, y, s, font="mono", size=12, fill=INK, ls=0, anchor="start", cls="", extra=""):
        self.used[font] += s
        fam, style = FAMILY[font]
        self.body.append(
            f'<text x="{x}" y="{y}" font-family="\'{fam}\',Georgia,serif" font-style="{style}" '
            f'font-size="{size}" fill="{fill}" letter-spacing="{ls}" text-anchor="{anchor}"'
            f'{f" class={chr(34)}{cls}{chr(34)}" if cls else ""} {extra}>{html.escape(s)}</text>')

    def raw(self, s, font_text=None):
        if font_text:
            for k, v in font_text.items():
                self.used[k] += v
        self.body.append(s)

    def save(self, name):
        faces = "".join(font_face(k, v) for k, v in self.used.items() if v)
        svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w}" height="{self.h}" '
               f'viewBox="0 0 {self.w} {self.h}"><style>{faces}{"".join(self.css)}</style>'
               f'<rect x=".5" y=".5" width="{self.w-1}" height="{self.h-1}" rx="{self.rx}" '
               f'fill="{self.bg}" stroke="{self.stroke}"/>' + "".join(self.body) + "</svg>")
        with open(os.path.join(OUT, name), "w", encoding="utf-8") as fh:
            fh.write(svg)
        print(f"{name}: {len(svg)//1024} KB")


# ──────────────────────────── CARDS ────────────────────────────
def ascii_rows():
    p = os.path.join(ROOT, "avi-ascii.svg")
    if not os.path.exists(p):
        return []
    rows = re.findall(r'<text[^>]*>([^<]*)</text>', open(p, encoding="utf-8").read())
    return [html.unescape(r) for r in rows]


def hero():
    c = Card(W, 300)
    c.css.append("@keyframes up{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:none}}"
                 ".u{animation:up .8s cubic-bezier(.2,.7,.2,1) backwards}"
                 "@keyframes pulse{0%,100%{opacity:1}50%{opacity:.25}}.dot{animation:pulse 2.4s ease-in-out infinite}"
                 "@keyframes sk{from{opacity:0}to{opacity:1}}.sk{animation:sk 1.6s ease backwards .4s}")
    c.raw(f'<circle class="dot" cx="44" cy="47" r="4" fill="{BLUE}"/>')
    c.text(58, 51, KICKER, "mono", 11, MUTE, 1.6)
    c.text(40, 138, "Vinayak", "serif", 84, INK, -1.5, cls="u", extra='style="animation-delay:.1s"')
    # italic surname with one ink-blue letter, like a pen correction
    c.raw(f'<text x="40" y="214" font-family="\'IS\',Georgia,serif" font-style="italic" font-size="84" '
          f'letter-spacing="-1.5" fill="{INK}" class="u" style="animation-delay:.3s">Bhad<tspan fill="{BLUE}">a</tspan>ni</text>',
          {"serif-i": "Bhadani"})
    for i, line in enumerate(TAGLINE):
        c.text(42, 246 + i * 18, line, "mono", 12, MUTE, 0, cls="u", extra=f'style="animation-delay:{.5+i*.1:.1f}s"')
    c.text(W - 40, 270, SITE + "  ↗", "mono-b", 11, INK, 1, "end")
    # right column: what's happening now
    x = W - 300
    c.raw(f'<line x1="{x-24}" y1="70" x2="{x-24}" y2="252" stroke="{LINE}"/>')
    c.text(x, 84, "NOW", "mono", 10, MUTE, 1.6)
    for i, (big, small) in enumerate(NOW):
        y = 116 + i * 40
        c.raw(f'<circle cx="{x+4}" cy="{y-5}" r="3.5" fill="{[BLUE, RED, YELLOW][i % 3]}"/>')
        c.text(x + 16, y, big, "mono-b", 12, INK)
        c.text(x + 16, y + 16, small, "mono", 10.5, MUTE)
    c.save("hero.svg")


def load_days():
    """GitHub calendar merged with commits.json (commits from emails GitHub does not
    credit). Per day we take the larger of the two, so nothing is double-counted."""
    d = json.load(open(os.path.join(ROOT, "contributions.json")))["days"]
    cal = {x["date"]: x["count"] for x in d}
    cp = os.path.join(ROOT, "commits.json")
    extra = json.load(open(cp))["days"] if os.path.exists(cp) else {}
    keys = sorted(cal)
    return [(dt.date.fromisoformat(k), max(cal[k], extra.get(k, 0))) for k in keys][-371:]


def daily(days):
    c = Card(W, 200)
    c.text(40, 54, "Every day,", "serif", 30, INK, -.3)
    c.text(40 + measure("Every day, ", "serif", 30), 54, "in blue", "serif-i", 30, BLUE, -.3)
    c.text(W - 40, 50, "REFRESHED DAILY", "mono", 10, MUTE, 1.6, "end")
    mx = max([n for _, n in days] + [1])
    # columns = weeks, rows = weekday
    start = days[0][0] - dt.timedelta(days=(days[0][0].weekday() + 1) % 7)
    cell, gap = 11.2, 2.8
    weeks = (days[-1][0] - start).days // 7 + 1
    x0 = (W - weeks * (cell + gap)) / 2
    c.css.append("@keyframes f{from{opacity:0}to{opacity:1}}.h{animation:f .5s ease backwards}")
    last_month = None
    for d, n in days:
        wk, wd = (d - start).days // 7, (d.weekday() + 1) % 7
        lvl = 0 if n == 0 else min(4, 1 + int(3 * n / mx + .999) - (1 if n < mx * .25 else 0))
        x, y = x0 + wk * (cell + gap), 76 + wd * (cell + gap)
        c.raw(f'<rect class="h" style="animation-delay:{wk*0.018:.3f}s" x="{x:.1f}" y="{y:.1f}" width="{cell}" height="{cell}" rx="2.4" fill="{HEAT[lvl]}"/>')
        if d.day <= 7 and wd == 0 and d.month != last_month and x < W - 190:
            c.text(f"{x:.1f}", 186, d.strftime("%b"), "mono", 9, MUTE)
            last_month = d.month
    lx = W - 40 - 5 * 14 - 30
    c.text(lx - 6, 186, "less", "mono", 9, MUTE, 0, "end")
    for i, col in enumerate(HEAT):
        c.raw(f'<rect x="{lx + i*14}" y="178" width="10" height="10" rx="2" fill="{col}"/>')
    c.text(lx + 5 * 14 + 2, 186, "more", "mono", 9, MUTE)
    c.save("daily.svg")


def stats(days):
    total = sum(n for _, n in days[-365:])
    active = sum(1 for _, n in days[-365:] if n)
    busiest = max(n for _, n in days)
    longest = cur = run = 0
    for _, n in days:
        run = run + 1 if n else 0
        longest = max(longest, run)
    for _, n in reversed(days):
        if n:
            cur += 1
        elif cur or _ == days[-1][0]:
            if cur:
                break
    months = OrderedDict()
    end = days[-1][0]
    for i in range(11, -1, -1):
        y, m = end.year, end.month - i
        while m <= 0:
            m += 12
            y -= 1
        months[(y, m)] = 0
    for d, n in days:
        if (d.year, d.month) in months:
            months[(d.year, d.month)] += n
    return total, active, busiest, longest, cur, months


def contrib(days):
    total, active, busiest, longest, cur, months = stats(days)
    c = Card(W, 270)
    c.text(40, 48, "THE LAST 12 MONTHS", "mono", 10, MUTE, 1.6)
    c.text(40, 92, "Shipped,", "serif", 40, INK, -.5)
    c.text(40 + measure("Shipped, ", "serif", 40), 92, "not just committed", "serif-i", 40, BLUE, -.5)
    c.text(40, 118, f"{total:,} commits and contributions on GitHub, plus everything below", "mono", 10.5, MUTE)
    mx = max(months.values()) or 1
    top = max(months, key=months.get)
    bw, gap, base, hmax = 36, 10, 232, 88
    c.css.append("@keyframes g{from{transform:scaleY(0)}to{transform:scaleY(1)}}"
                 ".b{transform-box:fill-box;transform-origin:bottom;animation:g .7s cubic-bezier(.2,.7,.2,1) backwards}")
    now = dt.date.today()
    for i, (k, v) in enumerate(months.items()):
        h = max(3, hmax * v / mx)
        x = 40 + i * (bw + gap)
        col = BLUE if k == top else (FAINT if k == (now.year, now.month) else INK)
        c.raw(f'<rect class="b" style="animation-delay:{i*0.05:.2f}s" x="{x}" y="{base-h:.1f}" width="{bw}" height="{h:.1f}" fill="{col}"/>')
        c.text(x + bw / 2, base + 16, dt.date(k[0], k[1], 1).strftime("%b"), "mono", 9, MUTE, 0, "middle")
        if k == top:
            c.text(x + bw / 2, base - h - 7, f"{v:,}", "mono-b", 9, BLUE, 0, "middle")
    sx = 40 + 12 * (bw + gap) + 34
    c.raw(f'<line x1="{sx-18}" y1="40" x2="{sx-18}" y2="242" stroke="{LINE}"/>')
    rows = [(f"{LIVE_APPS} live apps", "in production on Vercel"),
            (f"{REELS} Reels", "built in code, not an editor"),
            (f"{busiest} in a day", f"busiest day, {active} active days")]
    for i, (big, small) in enumerate(rows):
        y = 84 + i * 66
        c.text(sx, y, big, "serif", 30, INK, -.3)
        c.text(sx, y + 18, small, "mono", 10, MUTE)
    c.save("contrib.svg")


def tiles():
    tw, gap = (W - 2 * 12) / 3, 12
    c = Card(W, 176, bg="none", stroke="none")
    for i, (lab, bg, fg, big, small) in enumerate(TILES):
        x = i * (tw + gap)
        c.raw(f'<rect x="{x:.1f}" y="0" width="{tw:.1f}" height="176" rx="12" fill="{bg}"/>')
        c.text(f"{x+22:.1f}", 34, lab, "mono", 10, fg, 1.6)
        c.text(f"{x+tw-22:.1f}", 34, "→", "mono", 12, fg, 0, "end")
        c.text(f"{x+22:.1f}", 104, big, "serif-i", 34, fg, -.4)
        for j, s in enumerate(small):
            c.text(f"{x+22:.1f}", 132 + j * 16, s, "mono", 10.5, fg)
    c.save("tiles.svg")


def projects():
    for name, dot, lines, foot in PROJECTS:
        c = Card(284, 168, bg="#FFFFFF", stroke=LINE, rx=10)
        c.raw(f'<circle cx="24" cy="31" r="4.5" fill="{dot}"/>')
        c.text(36, 35, name, "mono-b", 12, INK)
        for j, s in enumerate(lines):
            c.text(22, 66 + j * 18, s, "mono", 10.5, MUTE)
        c.text(22, 146, foot, "mono", 10, INK, .4)
        c.save(f"p-{name}.svg")


def section_title(name, a, b):
    c = Card(W, 72)
    c.text(40, 48, a, "serif", 32, INK, -.3)
    c.text(40 + measure(a + " ", "serif", 32), 48, b, "serif-i", 32, BLUE, -.3)
    c.text(W - 40, 45, "PINNED WORK", "mono", 10, MUTE, 1.6, "end")
    c.save(name)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    days = load_days()
    hero()
    daily(days)
    contrib(days)
    tiles()
    projects()
    section_title("t-shipping.svg", "What I'm", "shipping")
