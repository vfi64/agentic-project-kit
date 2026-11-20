"""Website path and sequence diagrams projected from the shared workflow modes."""
from __future__ import annotations

from dataclasses import asdict
from html import escape
import json
import re
from textwrap import wrap

from .workflow_modes import ROLE_LABELS, WorkflowMode


ACTORS = {"you": "You", "assistant": "AI assistant", "kit": "Kit and repository"}
INK, LINE, ACCENT = "#17202a", "#c8d3dc", "#0f766e"
BRANCHES = (
    ("Repository and terminal access", ("primary",)),
    ("Browser chat without repository access", ("cost_saving", "emergency")),
    ("A local window for Kit actions", ("optional",)),
)


def text_node(
    label: str, x: int, y: int, *, kind: str = "body", source: str | None = None, centered: bool = False,
) -> str:
    anchor = ' text-anchor="middle"' if centered else ""
    return (
        f'<text x="{x}" y="{y}" class="{kind}" data-source="{escape(source if source is not None else label)}"{anchor}>'
        f'{escape(label)}</text>'
    )


def text_rows(label: str, x: int, y: int, width: int, *, kind: str = "body") -> tuple[list[str], int]:
    lines = wrap(label, width, break_long_words=False, break_on_hyphens=False)
    return [text_node(line, x, y + 21 * i, kind=kind, source=label) for i, line in enumerate(lines)], len(lines)


def box(x: int, y: int, w: int, h: int, fill: str = "#fff") -> str:
    return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="9" fill="{fill}" stroke="{LINE}" stroke-width="1.5"/>'


def diagram(title: str, description: str, width: int, height: int, body: list[str], facts: dict) -> str:
    return "\n".join((
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
        f'<title id="title">{escape(title)}</title><desc id="desc">{escape(description)}</desc>',
        '<style>.title{font:700 22px sans-serif;fill:#17202a}.head{font:700 16px sans-serif;fill:#17202a}'
        '.body{font:14px sans-serif;fill:#17202a}.note{font:14px sans-serif;fill:#586674}'
        '.role{font:700 14px sans-serif;fill:#0f766e}</style>',
        '<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7" '
        f'orient="auto"><path d="M1 1L9 5L1 9z" fill="{ACCENT}"/></marker></defs>',
        f'<metadata>{escape(json.dumps(facts, sort_keys=True))}</metadata>',
        f'<rect width="{width}" height="{height}" fill="#fff"/>',
        *body,
        "</svg>\n",
    ))


def picture(name: str, *, prefix: str, alt: str) -> str:
    return (
        f'<picture><source media="(max-width: 640px)" srcset="{prefix}{name}-narrow.svg">'
        f'<img src="{prefix}{name}.svg" alt="{escape(alt)}"></picture>'
    )


def render_path_chooser(content: dict, facts: dict, *, narrow: bool) -> str:
    width = 480 if narrow else 960
    question = content["question"]
    body = [text_node(content["title"], 24, 36, kind="title"),
            box(24, 53, width - 48, 42, "#edf3f1"), text_node(question, 38, 80, kind="head")]
    branches = []
    for label, roles in BRANCHES:
        modes = [mode for mode in facts["modes"] if facts["roles"][mode] in roles]
        tools = list(dict.fromkeys(tool for mode in modes for tool in facts["mode_tools"][mode]))
        branches.append((label, modes, tools))

    card_width = 432 if narrow else 288
    bottom = 95
    for index, (label, modes, tools) in enumerate(branches):
        x = 24 if narrow else 24 + 312 * index
        y = bottom + 26 if narrow else 135
        if not narrow:
            center = x + card_width // 2
            body.append(f'<path d="M480 95 V113 H{center} V133" fill="none" stroke="{ACCENT}" '
                        'stroke-width="1.5" marker-end="url(#arrow)"/>')
        elif index == 0:
            body.append(f'<path d="M40 95 V{y - 2}" stroke="{ACCENT}" marker-end="url(#arrow)"/>')
        else:
            body.append(f'<path d="M15 75 V{y + 20} H22" fill="none" stroke="{ACCENT}" marker-end="url(#arrow)"/>')
        heading, count = text_rows(label, x + 14, y + 26, 43 if narrow else 28, kind="head")
        lines = list(heading)
        cursor = y + 35 + count * 21
        for tool in tools:
            wrapped, count = text_rows(tool, x + 14, cursor, 49 if narrow else 33)
            lines.extend(wrapped)
            cursor += count * 21
        for mode in modes:
            lines.append(text_node(mode, x + 14, cursor, kind="head"))
            lines.append(text_node(ROLE_LABELS[facts["roles"][mode]], x + 14, cursor + 20, kind="role"))
            cursor += 49
        body.extend([box(x, y, card_width, cursor - y - 15, "#f6f7f4"), *lines])
        bottom = max(bottom, cursor - 15)
    foot, count = text_rows(content["footnote"], 24, bottom + 30, 52 if narrow else 105, kind="note")
    desc = " ".join(f"{label}: {', '.join(ROLE_LABELS[facts['roles'][mode]] + ' ' + mode for mode in modes)}."
                    for label, modes, _ in branches)
    return diagram(content["title"], question + " " + desc, width, bottom + 30 + 21 * count,
                   body + foot, {**facts, "branches": [modes for _, modes, _ in branches]})


def render_mode_figures(modes: tuple[WorkflowMode, ...], projected: list[dict], known: set[str]) -> dict[str, str]:
    """Require each projected card to match its mode, commands and diagram."""
    slugs = [mode.mode_id.replace("_", "-") for mode in modes]
    if slugs != [card["id"] for card in projected] or len(slugs) != len(set(slugs)):
        raise ValueError("workflow diagram modes do not match website cards")
    diagrams = {}
    for slug, mode, card in zip(slugs, modes, projected):
        card_commands = {entry["qualified_name"] for entry in card["commands"] if entry["manifest_present"]}
        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", slug) or slug.endswith("-narrow"):
            raise ValueError(f"invalid workflow diagram ID: {slug}")
        if len(mode.flow) < 2 or set(mode.commands) != card_commands or not card_commands <= known:
            raise ValueError(f"workflow diagram requires complete manifest-backed mode: {slug}")
        for step in mode.flow:
            if (step.actor_from not in ACTORS or step.actor_to not in ACTORS or not step.action.strip()
                    or (step.command is not None and step.command not in card_commands)):
                raise ValueError(f"invalid workflow diagram step: {slug}")
        for narrow in (False, True):
            suffix = "-narrow" if narrow else ""
            diagrams[f"mode-{slug}{suffix}.svg"] = _render_sequence(mode, narrow=narrow)
    return diagrams


def _centered_label(label: str, center: int, y: int, *, kind: str) -> tuple[list[str], int]:
    lines = wrap(label, 33, break_long_words=False, break_on_hyphens=False)
    height = 21 * len(lines)
    background = f'<rect x="{center - 145}" y="{y}" width="290" height="{height}" fill="#fff"/>'
    text = [text_node(line, center, y + 15 + i * 21, kind=kind, source=label, centered=True)
            for i, line in enumerate(lines)]
    return [background, *text], height


def _wide_sequence(mode: WorkflowMode) -> tuple[list[str], int]:
    lanes = dict(zip(ACTORS, (155, 474, 799)))
    rows = []
    y = 126
    for index, step in enumerate(mode.flow, 1):
        start, end = lanes[step.actor_from], lanes[step.actor_to]
        if start == end:
            # Put loop labels on the opposite side of the lane from the loop.
            direction = -1 if start == min(lanes.values()) else 1
            center = start - direction * 157
        else:
            center = (start + end) // 2
        action, height = _centered_label(step.action, center, y, kind="body")
        arrow_y = y + height + 5
        if start == end:
            edge = f"M{start} {arrow_y} c{40 * direction} -22 {40 * direction} 22 0 9"
        else:
            edge = f"M{start} {arrow_y} H{end}"
        rows.extend([
            f'<g data-step="{index}">',
            text_node(str(index), 24, arrow_y + 5, kind="role"),
            f'<path d="{edge}" fill="none" stroke="{ACCENT}" stroke-width="1.5" marker-end="url(#arrow)"/>',
            *action,
        ])
        y = arrow_y + 8
        if step.command:
            command, height = _centered_label(step.command, center, y, kind="note")
            rows.extend(command)
            y += height
        rows.append("</g>")
        y += 19
    guides = []
    for actor, x in lanes.items():
        optional = actor == "assistant" and mode.mode_id == "gui"
        label = ACTORS[actor] + (" (optional)" if optional else "")
        guides.extend([
            box(x - 115, 62, 230, 40, "#f6f7f4" if optional else "#edf3f1"),
            text_node(label, x - 100, 88, kind="head"),
            f'<line x1="{x}" y1="103" x2="{x}" y2="{y}" stroke="{LINE}" stroke-dasharray="5 5"/>',
        ])
    return guides + rows, y


def _narrow_sequence(mode: WorkflowMode) -> tuple[list[str], int]:
    rows = []
    y = 63
    for index, step in enumerate(mode.flow, 1):
        actor_label = f"{ACTORS[step.actor_from]} → {ACTORS[step.actor_to]}"
        label = text_node(f"{index}. {actor_label}", 36, y + 23, kind="role")
        lines, count = text_rows(step.action, 36, y + 53, 50)
        if step.command:
            command, extra = text_rows(step.command, 36, y + 53 + count * 21, 50, kind="note")
            lines.extend(command)
            count += extra
        rows.extend([box(24, y, 432, 53 + count * 21, "#f6f7f4"), label, *lines])
        y += 63 + count * 21
    return rows, y


def _render_sequence(mode: WorkflowMode, *, narrow: bool) -> str:
    width = 480 if narrow else 960
    rows, y = _narrow_sequence(mode) if narrow else _wide_sequence(mode)
    body = [text_node(mode.label, 24, 36, kind="title"), *rows]
    description = " ".join(
        f"{ACTORS[step.actor_from]} to {ACTORS[step.actor_to]}: {step.action}"
        + (f" Command: {step.command}." if step.command else "")
        for step in mode.flow
    )
    return diagram(mode.label, description, width, y + 12, body,
                   {"mode_id": mode.mode_id, "flow": [asdict(step) for step in mode.flow]})
