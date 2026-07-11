#!/usr/bin/env python3
"""
prep_photo.py — one-time local photo prep for the ASCII portrait.

  python scripts/prep_photo.py <photo.jpg> [source-prepped.png]

Removes the background with rembg, converts to grayscale, and applies
CLAHE local-contrast so the face reads clearly in ASCII (not a dark blob).
Output is an RGBA PNG: transparent background, equalized gray subject.
"""
import sys

import cv2
import numpy as np
from PIL import Image
from rembg import remove

# ──────────────────────────── CONFIG ────────────────────────────
CLAHE_CLIP = 1.8   # local-contrast strength; raise (3.5–5) if the face is muddy
CLAHE_GRID = 8     # CLAHE tile grid (8 = default; smaller = more aggressive)
MAX_SIDE = 1200    # downscale huge photos before processing
ALPHA_CUT = 24     # alpha below this becomes fully transparent (cleans halo)
# ────────────────────────────────────────────────────────────────


def main() -> None:
    if len(sys.argv) < 2:
        sys.exit("usage: prep_photo.py <photo> [out.png]")
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else "source-prepped.png"

    img = Image.open(src).convert("RGBA")
    if max(img.size) > MAX_SIDE:
        scale = MAX_SIDE / max(img.size)
        img = img.resize((round(img.width * scale), round(img.height * scale)), Image.LANCZOS)

    print("removing background (rembg — first run downloads the model)…")
    cut = remove(img)
    arr = np.array(cut)

    gray = cv2.cvtColor(arr[..., :3], cv2.COLOR_RGB2GRAY)
    clahe = cv2.createCLAHE(clipLimit=CLAHE_CLIP, tileGridSize=(CLAHE_GRID, CLAHE_GRID))
    eq = clahe.apply(gray)

    alpha = arr[..., 3].copy()
    alpha[alpha < ALPHA_CUT] = 0

    out = np.dstack([eq, eq, eq, alpha])

    # crop to the subject's bounding box (+small margin) so the portrait fills the frame
    ys, xs = np.where(alpha > 0)
    if len(ys):
        pad = round(0.03 * max(arr.shape[:2]))
        y0, y1 = max(ys.min() - pad, 0), min(ys.max() + pad, arr.shape[0])
        x0, x1 = max(xs.min() - pad, 0), min(xs.max() + pad, arr.shape[1])
        out = out[y0:y1, x0:x1]

    Image.fromarray(out, "RGBA").save(dst)
    print(f"saved {dst}  ({out.shape[1]}x{out.shape[0]})")


if __name__ == "__main__":
    main()
