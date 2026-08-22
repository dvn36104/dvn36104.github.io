"""Generate the long-form periodic table used in Part D."""

from __future__ import annotations

import csv
import html
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "elements.csv"
OUTPUT = ROOT / "images" / "long-form-periodic-table.svg"

CELL_W = 46
CELL_H = 54
LEFT = 72
TOP = 92
WIDTH = LEFT + 32 * CELL_W + 28
HEIGHT = TOP + 7 * CELL_H + 88

COLOURS = {
    "s": "#4269d0",
    "p": "#30a8b1",
    "d": "#c98a00",
    "f": "#9475cd",
}


def column(period: int, index: int) -> int:
    """Return the 32-column long-form position for an element in a period."""
    if period == 1:
        return 1 if index == 0 else 32
    if period in (2, 3):
        return index + 1 if index < 2 else 27 + (index - 2)
    if period in (4, 5):
        return index + 1 if index < 2 else 17 + (index - 2)
    return index + 1


with DATA.open(newline="", encoding="utf-8") as source:
    elements = list(csv.DictReader(source))

by_period: dict[int, list[dict[str, str]]] = {}
for element in elements:
    by_period.setdefault(int(element["period"]), []).append(element)

svg = [
    f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {WIDTH} {HEIGHT}" '
    f'role="img" aria-labelledby="title description">',
    '<title id="title">Long-form periodic table</title>',
    '<desc id="description">A 32-column periodic table with the lanthanoids and '
    'actinoids inserted into periods six and seven.</desc>',
    '<rect width="100%" height="100%" fill="white"/>',
    '<g font-family="Arial, Helvetica, sans-serif">',
    f'<text x="{WIDTH / 2}" y="31" text-anchor="middle" font-size="25" '
    'font-weight="700" fill="#222">Long-form periodic table</text>',
    f'<text x="{LEFT - 15}" y="79" text-anchor="end" font-size="12" '
    'fill="#555">group</text>',
]

group_columns = {1: 1, 2: 2}
group_columns.update({group: 17 + group - 3 for group in range(3, 13)})
group_columns.update({group: 27 + group - 13 for group in range(13, 19)})
for group, col in group_columns.items():
    x = LEFT + (col - 0.5) * CELL_W
    svg.append(
        f'<text x="{x}" y="79" text-anchor="middle" font-size="12" '
        f'font-weight="700" fill="#555">{group}</text>'
    )

f_start = LEFT + 2 * CELL_W
f_width = 14 * CELL_W
svg.extend(
    [
        f'<line x1="{f_start + 4}" y1="75" x2="{f_start + f_width - 4}" '
        'y2="75" stroke="#9475cd" stroke-width="3"/>',
        f'<text x="{f_start + f_width / 2}" y="66" text-anchor="middle" '
        'font-size="12" font-weight="700" fill="#7255aa">'
        '14 f-filling positions</text>',
    ]
)

for period in range(1, 8):
    y = TOP + (period - 1) * CELL_H
    svg.append(
        f'<text x="{LEFT - 15}" y="{y + CELL_H / 2 + 4}" text-anchor="end" '
        f'font-size="13" font-weight="700" fill="#555">{period}</text>'
    )
    for index, element in enumerate(by_period[period]):
        col = column(period, index)
        x = LEFT + (col - 1) * CELL_W
        colour = COLOURS[element["block"]]
        symbol = html.escape(element["symbol"])
        name = html.escape(element["name"])
        z = element["Z"]
        svg.extend(
            [
                f'<g><title>{z}: {name}</title>',
                f'<rect x="{x + 1}" y="{y + 1}" width="{CELL_W - 2}" '
                f'height="{CELL_H - 2}" rx="3" fill="{colour}" '
                'stroke="white" stroke-width="1.5"/>',
                f'<text x="{x + 5}" y="{y + 13}" font-size="9" '
                f'fill="white">{z}</text>',
                f'<text x="{x + CELL_W / 2}" y="{y + 36}" text-anchor="middle" '
                f'font-size="20" font-weight="700" fill="white">{symbol}</text>',
                '</g>',
            ]
        )

legend_y = TOP + 7 * CELL_H + 36
legend_items = [("s", "s-block"), ("f", "f-block"), ("d", "d-block"), ("p", "p-block")]
legend_width = 132
legend_start = WIDTH / 2 - len(legend_items) * legend_width / 2
for index, (block, label) in enumerate(legend_items):
    x = legend_start + index * legend_width
    svg.extend(
        [
            f'<rect x="{x}" y="{legend_y - 13}" width="18" height="18" rx="3" '
            f'fill="{COLOURS[block]}"/>',
            f'<text x="{x + 26}" y="{legend_y + 1}" font-size="13" '
            f'fill="#333">{label}</text>',
        ]
    )

svg.extend(['</g>', '</svg>'])
OUTPUT.write_text("\n".join(svg) + "\n", encoding="utf-8")
print(OUTPUT)
