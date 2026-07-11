#!/usr/bin/env python3
"""
render_heatmap_svg.py — GitHub-style contribution grid (contrib-heatmap.svg).

Reads contributions.json (from fetch_contributions.py) and renders a
monochrome heatmap whose cells reveal one by one, with a Less→More legend
and real streak stats.  STATIC=1 disables the animation.
"""
import json
import os
from datetime import date, timedelta

# ──────────────────────────── CONFIG ────────────────────────────
SRC = "contributions.json"
OUT = "contrib-heatmap.svg"

CELL = 11
GAP = 3
PAD = 24
TOP = 46          # room for title + month labels
LEFT = 54         # room for day labels

# monochrome ramp: empty → busiest
PALETTE = ["#161b22", "#2d333b", "#576069", "#98a3ad", "#e6edf3"]
FG = "#c9d1d9"
DIM = "#8b949e"
BG = "#0d1117"
BORDER = "#30363d"

WAVE = 0.022      # seconds per week column in the reveal sweep
# ────────────────────────────────────────────────────────────────

STATIC = os.environ.get("STATIC") == "1"
MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]


def streaks(days):
    cur = longest = run = 0
    for d in days:
        run = run + 1 if d["count"] > 0 else 0
        longest = max(longest, run)
    for d in reversed(days):
        if d["count"] > 0:
            cur += 1
        elif d["date"] == days[-1]["date"]:
            continue  # today with 0 doesn't break the streak yet
        else:
            break
    return cur, longest


def main() -> None:
    data = json.load(open(SRC))
    days = data["days"]
    by_date = {d["date"]: d for d in days}

    first = date.fromisoformat(days[0]["date"])
    last = date.fromisoformat(days[-1]["date"])
    start = first - timedelta(days=(first.weekday() + 1) % 7)  # back to Sunday

    weeks = []
    d = start
    while d <= last:
        week = [by_date.get((d + timedelta(days=i)).isoformat()) for i in range(7)]
        weeks.append((d, week))
        d += timedelta(days=7)

    total = sum(x["count"] for x in days)
    cur, longest = streaks(days)

    grid_w = len(weeks) * (CELL + GAP) - GAP
    w = LEFT + grid_w + PAD
    h = TOP + 7 * (CELL + GAP) - GAP + 40

    css = (
        f"text{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;"
        f"font-size:10.5px;fill:{DIM}}}"
        ".t{fill:" + FG + ";font-size:12px;font-weight:600}"
        ".s{fill:" + FG + "}"
    )
    if not STATIC:
        css += ("@keyframes pop{from{opacity:0;transform:scale(.4)}to{opacity:1;transform:none}}"
                ".c{opacity:0;transform-origin:center;transform-box:fill-box;"
                "animation:pop .28s ease-out forwards}")

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">',
        f"<style>{css}</style>",
        f'<rect width="{w}" height="{h}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<text x="{LEFT}" y="24" class="t">{total:,} contributions in the last year</text>',
    ]

    # month labels (on the first week of each new month)
    seen = None
    for wi, (wstart, _) in enumerate(weeks):
        if wstart.month != seen:
            seen = wstart.month
            x = LEFT + wi * (CELL + GAP)
            parts.append(f'<text x="{x}" y="{TOP - 6}">{MONTHS[wstart.month - 1]}</text>')

    for lbl, row in (("Mon", 1), ("Wed", 3), ("Fri", 5)):
        y = TOP + row * (CELL + GAP) + CELL - 2
        parts.append(f'<text x="{PAD}" y="{y}">{lbl}</text>')

    for wi, (_, week) in enumerate(weeks):
        x = LEFT + wi * (CELL + GAP)
        for di, cell in enumerate(week):
            if cell is None:
                continue
            y = TOP + di * (CELL + GAP)
            fill = PALETTE[min(cell["level"], 4)]
            anim = "" if STATIC else (
                f' class="c" style="animation-delay:{wi * WAVE + di * 0.004:.3f}s"')
            parts.append(
                f'<rect x="{x}" y="{y}" width="{CELL}" height="{CELL}" rx="2.5" '
                f'fill="{fill}"{anim}><title>{cell["date"]}: {cell["count"]}</title></rect>')

    # footer: stats left, legend right
    fy = h - 14
    parts.append(
        f'<text x="{LEFT}" y="{fy}"><tspan class="s">{cur}d</tspan> current streak'
        f'   ·   <tspan class="s">{longest}d</tspan> longest streak</text>')

    lx = w - PAD - 5 * (CELL + GAP) - 76
    parts.append(f'<text x="{lx - 8}" y="{fy}" text-anchor="end">Less</text>')
    for i, c in enumerate(PALETTE):
        parts.append(
            f'<rect x="{lx + i * (CELL + GAP)}" y="{fy - CELL + 2}" width="{CELL}" '
            f'height="{CELL}" rx="2.5" fill="{c}"/>')
    parts.append(
        f'<text x="{lx + 5 * (CELL + GAP) + 6}" y="{fy}">More</text>')

    parts.append("</svg>")
    with open(OUT, "w") as f:
        f.write("\n".join(parts))
    print(f"saved {OUT}  ({len(weeks)} weeks, {total} contributions, "
          f"streak {cur}d/{longest}d, {w}x{h}px)")


if __name__ == "__main__":
    main()
