"""Render the owner/Kit split from the reviewed copy and executor inventory."""
from __future__ import annotations

from .site_path_figures import ACCENT, box, diagram, text_node, text_rows


def render_ownership_figure(
    name: str, content: dict, executors: list[dict], commands: tuple[str, ...], *, narrow: bool,
) -> str:
    width = 480 if narrow else 960
    if name == "background-and-ownership":
        body, bottom = _responsibility_cards(content, width, narrow=narrow)
        description = " ".join([*content["delegated"], content["operations"], *content["retained"]])
    else:
        body, bottom = _control_stack(content, executors, width, narrow=narrow)
        description = " ".join([content["owner"], content["kit"], *content["controls"],
                                *(row["name"] for row in executors), content["operations"]])
    title, _ = text_rows(content["title"], 24, 37, 37 if narrow else 78, kind="title")
    foot, count = text_rows(content["footnote"], 24, bottom + 27, 53 if narrow else 108, kind="note")
    return diagram(content["title"], description + " " + content["footnote"], width, bottom + 31 + count * 21,
                   title + body + foot, {"executors": executors, "commands": commands})


def _responsibility_cards(content: dict, width: int, *, narrow: bool) -> tuple[list[str], int]:
    body = []
    bottom = 85
    w = width - 48 if narrow else 444
    for index, (heading, rows, tint) in enumerate((
        (content["delegated_heading"], [*content["delegated"], content["operations"]], "#e6f2f0"),
        (content["retained_heading"], content["retained"], "#eaeefc"),
    )):
        x = 24 if narrow else 24 + index * 468
        y = bottom + 13 if narrow else 98
        cursor = y + 30
        items = [text_node(heading, x + 16, cursor, kind="head")]
        cursor += 31
        for row in rows:
            wrapped, count = text_rows(row, x + 16, cursor, 48)
            items.extend(wrapped)
            cursor += 21 * count + 13
        body.extend([box(x, y, w, cursor - y - 5, tint), *items])
        bottom = max(bottom, cursor - 5)
    return body, bottom


def _control_stack(content: dict, executors: list[dict], width: int, *, narrow: bool) -> tuple[list[str], int]:
    body = []
    y = 73
    sections = (
        (content["owner"], [content["owner_detail"]], "#eaeefc"),
        (content["kit"], content["controls"], "#e6f2f0"),
        (content["executor_heading"], [row["name"] for row in executors], "#f6f7f4"),
        (content["repository_heading"], [content["operations"]], "#f6f7f4"),
    )
    for index, (heading, labels, tint) in enumerate(sections):
        if index:
            center = width // 2
            body.append(f'<path d="M{center} {y - 25} V{y - 3}" stroke="{ACCENT}" stroke-width="1.5" '
                        'marker-end="url(#arrow)"/>')
        items = [text_node(heading, 41, y + 29, kind="head")]
        cursor = y + 55
        if narrow or len(labels) == 1:
            for label in labels:
                wrapped, count = text_rows(label, 41, cursor, 47 if narrow else 101)
                items.extend(wrapped)
                cursor += 21 * count + 5
        else:
            for start in range(0, len(labels), 3):
                row_height = 0
                for i, label in enumerate(labels[start:start + 3]):
                    wrapped, count = text_rows(label, 41 + i * 300, cursor, 30)
                    items.extend(wrapped)
                    row_height = max(row_height, count)
                cursor += 21 * row_height + 8
        height = cursor - y
        body.extend([box(24, y, width - 48, height, tint), *items])
        y += height + 25
    return body, y - 25
