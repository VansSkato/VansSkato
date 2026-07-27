#!/usr/bin/env python3
"""
Step 5b — Draw the 53-week x 7-day contribution grid as an animated SVG.

Reads data/contributions.json (written by fetch_contributions.py),
lays the days out into a classic GitHub-style calendar of rounded
boxes, and reveals it once with a diagonal, line-after-line
slide-down (CSS keyframes, play-on-load, no looping). Adds a
Less -> More legend and a stats footer.

Usage:
    python scripts/render_heatmap_svg.py
Writes:
    contrib-heatmap.svg
"""
import json
import datetime

IN_PATH = "data/contributions.json"
OUT_PATH = "contrib-heatmap.svg"

PALETTE = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353", "#69f0a0"]
BG = "#0d1117"
TEXT_DIM = "#8b949e"
TEXT_MAIN = "#c9d1d9"
FONT = '"SFMono-Regular",Consolas,"Liberation Mono",Menlo,monospace'

CELL = 11
GAP = 3
LEFT_PAD = 30
TOP_PAD = 36
BOTTOM_PAD = 34
MONTH_LABEL_H = 16

MONTHS = ["Jan", "Feb", "Mar", "Apr", "May", "Jun",
          "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
DOW_LABELS = {1: "Mon", 3: "Wed", 5: "Fri"}


def load_data():
    with open(IN_PATH) as f:
        return json.load(f)


def bucket_into_weeks(days):
    """Return list of weeks; each week is list of 7 (date,count,level) or None."""
    if not days:
        return []
    parsed = []
    for d in days:
        dt = datetime.date.fromisoformat(d["date"])
        parsed.append((dt, d["count"], d["level"]))

    first_dt = parsed[0][0]
    # roll back to the most recent Sunday on/before first_dt so week columns align
    back = (first_dt.weekday() + 1) % 7  # Python Monday=0..Sunday=6 -> Sunday-based offset
    start = first_dt - datetime.timedelta(days=back)

    weeks = []
    current_week = [None] * 7
    cursor = start
    day_map = {d[0]: d for d in parsed}
    end_dt = parsed[-1][0]

    while cursor <= end_dt:
        dow = (cursor.weekday() + 1) % 7  # Sunday=0..Saturday=6
        entry = day_map.get(cursor)
        current_week[dow] = entry if entry else (cursor, 0, 0)
        if dow == 6:
            weeks.append(current_week)
            current_week = [None] * 7
        cursor += datetime.timedelta(days=1)

    if any(c is not None for c in current_week):
        weeks.append(current_week)

    return weeks


def esc(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def build_svg(payload):
    weeks = bucket_into_weeks(payload["days"])
    stats = payload["stats"]
    n_weeks = len(weeks)

    grid_w = n_weeks * (CELL + GAP)
    grid_h = 7 * (CELL + GAP)
    width = LEFT_PAD + grid_w + 20
    height = TOP_PAD + MONTH_LABEL_H + grid_h + BOTTOM_PAD

    parts = []
    parts.append(
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.0f}" '
        f'height="{height:.0f}" viewBox="0 0 {width:.0f} {height:.0f}">'
    )
    parts.append(f'<rect width="100%" height="100%" fill="{BG}"/>')
    parts.append(
        f'<style>text{{font-family:{FONT};}} '
        f'.cell{{opacity:0;animation:reveal .5s ease-out forwards;}} '
        f'@keyframes reveal{{from{{opacity:0;transform:translate(-4px,-4px);}} '
        f'to{{opacity:1;transform:translate(0,0);}}}}</style>'
    )

    # day-of-week labels
    grid_top = TOP_PAD + MONTH_LABEL_H
    for dow, label in DOW_LABELS.items():
        y = grid_top + dow * (CELL + GAP) + CELL - 1
        parts.append(
            f'<text x="0" y="{y}" fill="{TEXT_DIM}" font-size="9">{label}</text>'
        )

    # month labels (only when the month changes across a week column)
    last_month = None
    for w_idx, week in enumerate(weeks):
        first_real = next((d for d in week if d is not None), None)
        if first_real is None:
            continue
        month = first_real[0].month
        if month != last_month:
            x = LEFT_PAD + w_idx * (CELL + GAP)
            parts.append(
                f'<text x="{x}" y="{TOP_PAD}" fill="{TEXT_DIM}" font-size="10">'
                f'{MONTHS[month - 1]}</text>'
            )
            last_month = month

    # cells, diagonal stagger by (week + day)
    max_diag = n_weeks + 7
    total_anim_span = 2.6  # seconds across the whole reveal

    for w_idx, week in enumerate(weeks):
        for d_idx in range(7):
            entry = week[d_idx]
            x = LEFT_PAD + w_idx * (CELL + GAP)
            y = grid_top + d_idx * (CELL + GAP)
            if entry is None:
                color = PALETTE[0]
                title = ""
            else:
                dt, count, level = entry
                level = max(0, min(level, len(PALETTE) - 1))
                color = PALETTE[level]
                title = f"{count} contributions on {dt.isoformat()}"

            diag = w_idx + d_idx
            delay = (diag / max_diag) * total_anim_span
            title_svg = f'<title>{esc(title)}</title>' if title else ""
            parts.append(
                f'<rect class="cell" x="{x}" y="{y}" width="{CELL}" height="{CELL}" '
                f'rx="2" fill="{color}" style="animation-delay:{delay:.3f}s">'
                f'{title_svg}</rect>'
            )

    # legend
    legend_y = grid_top + grid_h + 22
    legend_x = width - 20 - (len(PALETTE) * (CELL + 3)) - 40
    parts.append(f'<text x="{legend_x - 34}" y="{legend_y + 9}" fill="{TEXT_DIM}" font-size="10">Less</text>')
    for i, color in enumerate(PALETTE):
        lx = legend_x + i * (CELL + 3)
        parts.append(f'<rect x="{lx}" y="{legend_y}" width="{CELL}" height="{CELL}" rx="2" fill="{color}"/>')
    parts.append(
        f'<text x="{legend_x + len(PALETTE) * (CELL + 3) + 6}" y="{legend_y + 9}" '
        f'fill="{TEXT_DIM}" font-size="10">More</text>'
    )

    # stats footer
    footer = f"{stats['total']:,} contributions in the last year - current streak {stats['current_streak']}d - longest streak {stats['longest_streak']}d"
    parts.append(
        f'<text x="{LEFT_PAD}" y="{legend_y + 9}" fill="{TEXT_MAIN}" font-size="11">'
        f'{esc(footer)}</text>'
    )

    parts.append("</svg>")

    with open(OUT_PATH, "w") as f:
        f.write("\n".join(parts))
    print(f"wrote {OUT_PATH}")


if __name__ == "__main__":
    build_svg(load_data())
