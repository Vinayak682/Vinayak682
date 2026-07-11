#!/usr/bin/env python3
"""
make_info_card.py — terminal-style info panel (info-card.svg).

Edit ROWS + HOST below with real experience / stack / highlights,
then:  python scripts/make_info_card.py
Keep the card the same height as the portrait; if content overflows, bump H.
"""
import html

# ──────────────────────────── CONFIG ────────────────────────────
HOST = "vinayak@dubai:~"

# ("cmd", text)  → typed prompt line ($ …)
# ("out", text)  → plain output line
# ("dim", text)  → muted output line
# ("gap", "")    → half-line vertical space
ROWS = [
    ("cmd", "whoami"),
    ("out", "Vinayak Bhadani — Demand Planning · AI Supply Chain"),
    ("dim", "MBA Global Logistics & SCM · Dubai, UAE"),
    ("gap", ""),
    ("cmd", "cat experience.log"),
    ("out", "▸ Demand Planning @ Emirates Pride Perfumes, Dubai"),
    ("out", "▸ 3+ yrs running live S&OP cycles — UAE retail & FMCG"),
    ("out", "▸ Inventory platform in daily use across 35+ stores"),
    ("gap", ""),
    ("cmd", "ls ~/stack"),
    ("out", "python  typescript  sql  supabase  claude-api"),
    ("out", "next.js  power-bi  excel-automation  github-actions"),
    ("gap", ""),
    ("cmd", "cat shipped.txt"),
    ("out", "▸ Meridian — multi-market equity research terminal"),
    ("out", "▸ S&OP Copilot — Monday brief, generated Sunday night"),
    ("out", "▸ GCC Surge Planner — Ramadan/Eid-aware forecasting"),
    ("gap", ""),
    ("cmd", "echo $FOCUS"),
    ("out", "building the tools that plan supply chains better █"),
]

W = 560
H = 486          # bump if rows overflow (keep close to portrait height)
FONT_SIZE = 12.5
LINE_H = 20
GAP_H = 10
PAD_X = 22
TOP = 64         # below the title bar

FG = "#c9d1d9"
DIM = "#8b949e"
PROMPT = "#e6edf3"
BG = "#0d1117"
BAR = "#161b22"
BORDER = "#30363d"

STAGGER = 0.16   # seconds between line reveals
# ────────────────────────────────────────────────────────────────


def main() -> None:
    css = (
        f"text{{font-family:'SFMono-Regular',Consolas,'Liberation Mono',Menlo,monospace;"
        f"font-size:{FONT_SIZE}px;white-space:pre}}"
        ".fg{fill:" + FG + "}.dim{fill:" + DIM + "}.p{fill:" + PROMPT + ";font-weight:600}"
        ".host{fill:" + DIM + ";font-size:11.5px}"
        "@keyframes in{from{opacity:0;transform:translateY(3px)}to{opacity:1;transform:none}}"
        ".ln{opacity:0;animation:in .3s ease-out forwards}"
        "@keyframes blink{0%,49%{opacity:1}50%,100%{opacity:0}}"
        ".cur{animation:blink 1.1s step-end infinite}"
    )

    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" '
        f'viewBox="0 0 {W} {H}">',
        f"<style>{css}</style>",
        f'<rect width="{W}" height="{H}" rx="12" fill="{BG}" stroke="{BORDER}"/>',
        f'<path d="M0 12a12 12 0 0 1 12-12h{W - 24}a12 12 0 0 1 12 12v26H0z" fill="{BAR}"/>',
        f'<line x1="0" y1="38" x2="{W}" y2="38" stroke="{BORDER}"/>',
        # monochrome traffic dots
        f'<circle cx="20" cy="19" r="5" fill="#484f58"/>'
        f'<circle cx="38" cy="19" r="5" fill="#30363d"/>'
        f'<circle cx="56" cy="19" r="5" fill="#21262d"/>',
        f'<text x="{W / 2:.0f}" y="23" text-anchor="middle" class="host">{html.escape(HOST)}</text>',
    ]

    y = TOP
    i = 0
    for kind, text in ROWS:
        if kind == "gap":
            y += GAP_H
            continue
        delay = f' style="animation-delay:{i * STAGGER:.2f}s"'
        esc = html.escape(text).replace(" ", " ")
        if kind == "cmd":
            parts.append(
                f'<text x="{PAD_X}" y="{y}" class="ln"{delay}>'
                f'<tspan class="p">$ </tspan><tspan class="fg">{esc}</tspan></text>'
            )
        else:
            cls = "dim" if kind == "dim" else "fg"
            if text.endswith("█"):
                esc = html.escape(text[:-1]).replace(" ", " ")
                parts.append(
                    f'<text x="{PAD_X}" y="{y}" class="ln"{delay}>'
                    f'<tspan class="{cls}">{esc}</tspan>'
                    f'<tspan class="cur fg">█</tspan></text>'
                )
            else:
                parts.append(f'<text x="{PAD_X}" y="{y}" class="ln {cls}"{delay}>{esc}</text>')
        y += LINE_H
        i += 1

    parts.append("</svg>")
    with open("info-card.svg", "w") as f:
        f.write("\n".join(parts))
    used = y - LINE_H + 24
    note = "" if used <= H else f"  ⚠ content needs ~{used}px — bump H!"
    print(f"saved info-card.svg  ({W}x{H}, content ends ~{used}px){note}")


if __name__ == "__main__":
    main()
