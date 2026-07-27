#!/usr/bin/env python3
"""
Step 4 — Build a neofetch-style info card SVG.

Hand-authors a small terminal panel: a title bar, then colored
key/value rows (Now / Prev / Stack / Highlights). Each line fades and
slides in on a short stagger. Set STATIC=1 to emit a frozen frame
(useful for local Quick Look previews).

EDIT THE CONTENT BLOCK BELOW to match what you want the card to say.

Usage:
    python scripts/make_info_card.py
Writes:
    info-card.svg
"""
import os

# ---- EDIT ME: your own info -------------------------------------------------
USERNAME = "VansSkato"
TITLE = f"{USERNAME}@github"
NOW = "Ing. en Tecnologias Automotrices"
PREV = "Automotive Engineering Student"
STACK = "Python - C/C++ - MATLAB/Simulink - CAN bus - Git"
HIGHLIGHTS = [
    "Diagnostico y control de sistemas embebidos automotrices",
    "Proyectos de telemetria y adquisicion de datos vehiculares",
    "Siempre construyendo algo nuevo bajo el cofre (y en el codigo)",
]
# -----------------------------------------------------------------------------

STATIC = os.environ.get("STATIC") == "1"

BG = "#0d1117"
BORDER = "#30363d"
TITLEBAR = "#161b22"
KEY_COLOR = "#39d353"
VAL_COLOR = "#c9d1d9"
DIM_COLOR = "#8b949e"
# NOTE: no inner double-quotes here — this string is embedded directly
# inside a double-quoted XML attribute (font-family="..."), and nested
# double quotes would produce invalid XML.
FONT = "SFMono-Regular, Consolas, Liberation Mono, Menlo, monospace"

WIDTH = 490
LINE_H = 26
PAD_TOP = 56
PAD_X = 24


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def row(label: str, value: str, y: int, delay: float, static: bool):
    label_x = PAD_X
    value_x = PAD_X + 120
    anim = ""
    style = "opacity:1" if static else "opacity:0"
    if not static:
        anim = (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-12 0" to="0 0" begin="{delay:.2f}s" dur="0.35s" '
            f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
        )
    return (
        f'<g style="{style}" transform="translate(-12 0)">'
        f'{anim}'
        f'<text x="{label_x}" y="{y}" fill="{KEY_COLOR}" font-family="{FONT}" '
        f'font-size="14" font-weight="bold">{esc(label)}</text>'
        f'<text x="{value_x}" y="{y}" fill="{VAL_COLOR}" font-family="{FONT}" '
        f'font-size="14">{esc(value)}</text>'
        f'</g>'
    )


def highlight_row(text: str, y: int, delay: float, static: bool):
    anim = ""
    style = "opacity:1" if static else "opacity:0"
    if not static:
        anim = (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
            f'<animateTransform attributeName="transform" type="translate" '
            f'from="-12 0" to="0 0" begin="{delay:.2f}s" dur="0.35s" '
            f'fill="freeze" calcMode="spline" keySplines="0.25 0.1 0.25 1"/>'
        )
    return (
        f'<g style="{style}" transform="translate(-12 0)">'
        f'{anim}'
        f'<text x="{PAD_X}" y="{y}" fill="{DIM_COLOR}" font-family="{FONT}" '
        f'font-size="13">- {esc(text)}</text>'
        f'</g>'
    )


def build(out_path: str, static: bool):
    rows_meta = [
        ("Now", NOW),
        ("Prev", PREV),
        ("Stack", STACK),
    ]

    body = []
    y = PAD_TOP
    delay = 0.1
    stagger = 0.18

    for label, value in rows_meta:
        body.append(row(label, value, y, delay, static))
        y += LINE_H
        delay += stagger

    y += 6
    heading_opacity = "1" if static else "0"
    heading_anim = ""
    if not static:
        heading_anim = (
            f'<animate attributeName="opacity" from="0" to="1" '
            f'begin="{delay:.2f}s" dur="0.35s" fill="freeze"/>'
        )
    body.append(
        f'<text x="{PAD_X}" y="{y}" fill="{KEY_COLOR}" font-family="{FONT}" '
        f'font-size="14" font-weight="bold" style="opacity:{heading_opacity}">'
        f'Highlights{heading_anim}</text>'
    )
    delay += stagger
    y += LINE_H

    for h in HIGHLIGHTS:
        body.append(highlight_row(h, y, delay, static))
        y += 22
        delay += stagger

    height = y + 24

    svg = []
    svg.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" '
        f'height="{height}" viewBox="0 0 {WIDTH} {height}">'
    )
    svg.append(
        f'<rect x="0.5" y="0.5" width="{WIDTH - 1}" height="{height - 1}" rx="8" '
        f'fill="{BG}" stroke="{BORDER}"/>'
    )
    # title bar
    svg.append(f'<rect x="1" y="1" width="{WIDTH - 2}" height="30" rx="7" fill="{TITLEBAR}"/>')
    svg.append(f'<rect x="1" y="24" width="{WIDTH - 2}" height="7" fill="{TITLEBAR}"/>')
    for i, c in enumerate(["#ff5f56", "#ffbd2e", "#27c93f"]):
        svg.append(f'<circle cx="{20 + i * 18}" cy="16" r="6" fill="{c}"/>')
    svg.append(
        f'<text x="{WIDTH / 2:.0f}" y="20" fill="{DIM_COLOR}" font-family="{FONT}" '
        f'font-size="12" text-anchor="middle">{esc(TITLE)}</text>'
    )
    svg.extend(body)
    svg.append("</svg>")

    with open(out_path, "w") as f:
        f.write("\n".join(svg))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    build("info-card.svg", STATIC)
