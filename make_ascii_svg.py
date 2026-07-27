#!/usr/bin/env python3
"""
Step 3b — Convert the prepped grayscale photo into a self-typing,
monochrome ASCII-art SVG.

Downsamples the image to a character grid, picks a glyph per cell from
a brightness ramp, then wraps each row in a clip-path that wipes it in
left-to-right, staggered top-to-bottom (SMIL animation, plays once).

Usage:
    python scripts/make_ascii_svg.py [source-prepped.png] [vans-ascii.svg]
"""
import sys
from PIL import Image

RAMP = " .:-=+*#%@"  # bright (sparse) -> dark (dense); leading space = blank
# Sized so the native SVG is ~= the width the README displays it at
# (370px, see README.md). Rendering more columns than that just means
# the browser shrinks it and the glyphs turn into illegible mush.
COLS = 60
ROWS = 42
CHAR_W = 6.2
CHAR_H = 11
FONT_SIZE = 11
FILL = "#c9d1d9"        # monochrome light-gray, GitHub-dark-mode friendly
BG = "#0d1117"


def image_to_ascii_rows(path: str, cols: int, rows: int):
    img = Image.open(path).convert("L")
    img = img.resize((cols, rows))
    pixels = list(img.getdata())
    ascii_rows = []
    ramp_len = len(RAMP)
    for r in range(rows):
        row_chars = []
        for c in range(cols):
            brightness = pixels[r * cols + c]  # 0 dark - 255 bright
            idx = int((255 - brightness) / 255 * (ramp_len - 1))
            row_chars.append(RAMP[idx])
        ascii_rows.append("".join(row_chars))
    return ascii_rows


def escape(ch: str) -> str:
    return {"&": "&amp;", "<": "&lt;", ">": "&gt;"}.get(ch, ch)


def build_svg(ascii_rows, out_path: str):
    width = COLS * CHAR_W
    height = ROWS * CHAR_H
    row_duration = 0.55
    stagger = 0.045

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG}"/>')
    parts.append(
        f'<style>text{{font-family:"SFMono-Regular",Consolas,'
        f'"Liberation Mono",Menlo,monospace;font-size:{FONT_SIZE}px;'
        f'fill:{FILL};white-space:pre;}}</style>'
    )

    for r, row in enumerate(ascii_rows):
        y = (r + 1) * CHAR_H - 2
        row_id = f"row{r}"
        clip_id = f"clip{r}"
        text_escaped = "".join(escape(ch) for ch in row)
        start_time = r * stagger

        parts.append(f'<clipPath id="{clip_id}">')
        parts.append(f'  <rect x="0" y="{r * CHAR_H:.1f}" width="0" height="{CHAR_H}">')
        parts.append(
            f'    <animate attributeName="width" from="0" to="{width:.0f}" '
            f'begin="{start_time:.3f}s" dur="{row_duration}s" '
            f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
        )
        parts.append("  </rect>")
        parts.append("</clipPath>")

        parts.append(f'<g clip-path="url(#{clip_id})">')
        parts.append(f'  <text x="0" y="{y:.1f}">{text_escaped}</text>')
        parts.append("</g>")

        # small block cursor riding the wipe edge
        cursor_id = f"cursor{r}"
        parts.append(
            f'<rect id="{cursor_id}" x="0" y="{r * CHAR_H:.1f}" '
            f'width="{CHAR_W:.1f}" height="{CHAR_H}" fill="{FILL}" opacity="0">'
        )
        parts.append(
            f'  <animate attributeName="x" from="0" to="{width - CHAR_W:.1f}" '
            f'begin="{start_time:.3f}s" dur="{row_duration}s" fill="freeze" '
            f'calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
        )
        parts.append(
            f'  <animate attributeName="opacity" values="0;1;1;0" '
            f'keyTimes="0;0.05;0.9;1" begin="{start_time:.3f}s" '
            f'dur="{row_duration}s" fill="freeze"/>'
        )
        parts.append("</rect>")

    parts.append("</svg>")

    with open(out_path, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    src = sys.argv[1] if len(sys.argv) > 1 else "source-prepped.png"
    out = sys.argv[2] if len(sys.argv) > 2 else "vans-ascii.svg"
    rows = image_to_ascii_rows(src, COLS, ROWS)
    build_svg(rows, out)
