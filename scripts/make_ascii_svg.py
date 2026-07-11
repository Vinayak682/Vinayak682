#!/usr/bin/env python3
"""
make_ascii_svg.py — render source-prepped.png as a monochrome ASCII portrait SVG
that "types" itself in like a terminal on load.

  python scripts/make_ascii_svg.py            # animated avi-ascii.svg
  STATIC=1 python scripts/make_ascii_svg.py   # final frame only (for previews)

Tune CONTRAST / GAMMA / WHITE_FLOOR below until the face reads well.
"""
import html
import os

import numpy as np
from PIL import Image

# ──────────────────────────── CONFIG ────────────────────────────
SRC = "source-prepped.png"
OUT = "avi-ascii.svg"

COLS = 104           # characters per row (higher = more detail)
CONTRAST = 0.95      # >1 pushes mids apart; raise if the face is flat
GAMMA = 1.20         # <1 brightens mids; lower if the face is too dark
WHITE_FLOOR = 0.06   # luminance below this becomes blank (kills dark noise)

RAMP = " .:-=+*#%@"  # dark → bright (we draw light text on a dark panel)
FONT_SIZE = 11
CHAR_W = FONT_SIZE * 0.602   # monospace advance
LINE_H = FONT_SIZE * 1.02

FG = "#c9d1d9"        # text
BG = "#0d1117"        # panel
BORDER = "#30363d"
PAD = 22

ROW_STAGGER = 0.055   # seconds between row starts
ROW_DUR = 0.55        # seconds a row takes to type
# ────────────────────────────────────────────────────────────────

STATIC = os.environ.get("STATIC") == "1"
NBSP = " "


def main() -> None:
    img = Image.open(SRC).convert("LA")
    aspect = img.height / img.width
    rows = max(1, round(COLS * aspect * (CHAR_W / LINE_H)))
    img = img.resize((COLS, rows), Image.LANCZOS)

    arr = np.asarray(img, dtype=np.float64) / 255.0
    lum, alpha = arr[..., 0], arr[..., 1]

    lum = np.clip((lum - 0.5) * CONTRAST + 0.5, 0, 1) ** GAMMA
    lum[alpha < 0.45] = 0.0
    lum[lum < WHITE_FLOOR] = 0.0

    idx = np.minimum((lum * len(RAMP)).astype(int), len(RAMP) - 1)
    lines = ["".join(RAMP[i] for i in r).rstrip() for r in idx]
    while lines and not lines[0]:
        lines.pop(0)
    while lines and not lines[-1]:
        lines.pop()

    w = round(COLS * CHAR_W + PAD * 2)
    h = round(len(lines) * LINE_H + PAD * 2)

    css = [
        f"text{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;"
        f"font-size:{FONT_SIZE}px;fill:{FG};white-space:pre}}",
    ]
    if not STATIC:
        css.append(
            "@keyframes type{from{clip-path:inset(-2px 101% -2px -2px)}"
            "to{clip-path:inset(-2px -2px -2px -2px)}}"
        )
        css.append(".r{clip-path:inset(-2px 101% -2px -2px);"
                   f"animation:type {ROW_DUR}s steps({COLS}) forwards}}")

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" '
        f'viewBox="0 0 {w} {h}">',
        f"<style>{''.join(css)}</style>",
        f'<rect width="{w}" height="{h}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
    ]
    for i, line in enumerate(lines):
        y = PAD + FONT_SIZE + i * LINE_H
        txt = html.escape(line).replace(" ", NBSP)
        anim = "" if STATIC else f' class="r" style="animation-delay:{i * ROW_STAGGER:.3f}s"'
        parts.append(f'<text x="{PAD}" y="{y:.1f}"{anim}>{txt}</text>')
    parts.append("</svg>")

    with open(OUT, "w") as f:
        f.write("\n".join(parts))
    total = ROW_DUR + len(lines) * ROW_STAGGER
    print(f"saved {OUT}  ({COLS}x{len(lines)} chars, {w}x{h}px, "
          f"{'static' if STATIC else f'~{total:.1f}s animation'})")


if __name__ == "__main__":
    main()
