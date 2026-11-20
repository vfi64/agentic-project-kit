"""Generate accessible role figures from reviewed website and init sources."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from textwrap import wrap

from .site_path_figures import render_mode_figures, render_path_chooser, text_node
from .site_ownership_figures import render_ownership_figure
from .workflow_modes import modes_for

import yaml


INK = "#17202a"
MUTED = "#586674"
LINE = "#c8d3dc"
ACCENT = "#0f766e"
ACCENT2 = "#3454d1"
WARN = "#a16207"
TINT = {MUTED: "#f1f3f5", ACCENT: "#e6f2f0", ACCENT2: "#eaeefc", INK: "#f6f7f4"}
NAMES = ("asked-checked-enforced", "repository-memory", "path-chooser")
Card = tuple[str, list[str], str]


def _ci_summary(ci_text: str) -> tuple[list[str], list[str]]:
    ci = yaml.load(ci_text, Loader=yaml.BaseLoader)
    events = ci.get("on", {})
    if not isinstance(events, dict) or set(events) != {"push", "pull_request"}:
        raise ValueError("generated CI trigger changed")
    commands = [
        (job, step) for job in ci.get("jobs", {}).values()
        for step in job.get("steps", []) if "run" in step
    ]
    if not any(step["run"].strip() == "agentic-kit check" for _, step in commands):
        raise ValueError("generated CI no longer runs agentic-kit check")

    has_tests = False
    for job, step in commands:
        run = step["run"].strip()
        is_check = run == "agentic-kit check"
        if not is_check and step.get("name") in {"Install Kit", "Install project and Kit"}:
            continue
        if not is_check and (step.get("name"), run) != ("Run tests", "if [ -d tests ]; then pytest -q; fi"):
            raise ValueError(f"unrecognized generated CI step: {step.get('name', '<unnamed>')}")
        if any("if" in entry or entry.get("continue-on-error", "false").lower() != "false" for entry in (job, step)):
            raise ValueError("generated CI check or test is conditional or allows failure")
        has_tests = has_tests or not is_check
    summary = ["Runs on: " + ", ".join(event.replace("_", " ") for event in sorted(events, reverse=True))]
    if has_tests:
        summary.append("Runs project tests")
    summary.append("Runs agentic-kit check")
    return sorted(events, reverse=True), summary


def collect_role_figure_facts(root: Path, workflow_projection: dict, fixture: tuple[dict, list[str], str]) -> dict[str, dict]:
    """Read facts once; all SVG text and metadata use the same validated values."""
    content = yaml.safe_load((root / "site/content/role_figures.yaml").read_text(encoding="utf-8"))
    if content.get("kind") != "website-role-figures" or not all(content["figures"][name]["published"] for name in NAMES):
        raise ValueError("published role figure content is incomplete")
    example, files, ci_text = fixture
    executors = yaml.safe_load((root / "site/content/executors.yaml").read_text(encoding="utf-8"))["executors"]
    manifest = json.loads((root / "docs/reference/agentic-kit-commands.json").read_text(encoding="utf-8"))
    manifest_commands = {row["qualified_name"] for row in manifest["commands"]}
    if not {"agentic-kit check", "agentic-kit doctor"} <= manifest_commands:
        raise ValueError("role figure command missing from manifest")
    events, ci_summary = _ci_summary(ci_text)
    sessions = {session: [step for step in example["steps"] if str(step["session"]) == session]
                for session in ("1", "2")}
    if not sessions["1"] or not sessions["2"] or not sessions["2"][0].get("agent"):
        raise ValueError("repository memory figure requires two sessions and a second-session agent action")
    required = ["AGENTS.md", "docs/STATUS.md", "docs/handoff/CURRENT_HANDOFF.md"]
    shown = required + [next((path for path in files if path.startswith(prefix)), "") for prefix in ("src/", "tests/")]
    prompt = "docs/handoff/STANDARD_AGENT_PROMPT.md"
    if not all(path in files for path in [*shown, prompt]):
        raise ValueError("repository memory figure references missing init files")
    modes = workflow_projection["modes"]
    if not isinstance(modes, list) or not modes or any(not mode.get("title") for mode in modes):
        raise ValueError("site mode projection is incomplete")
    paths = {mode["title"] for mode in modes}
    for row in executors:
        if not set(row["path"].split(" or ")) <= paths:
            raise ValueError(f"executor has no site mode: {row['name']}")
    return {
        "asked-checked-enforced": {
            "ci_events": events, "ci_summary": ci_summary,
            "manifest_commands": sorted({"agentic-kit check", "agentic-kit doctor"}),
            "instruction_files": required[:1] + [prompt],
        },
        "repository-memory": {
            "init_files": files, "shown_files": shown,
            "steps": [row["title"] for row in example["steps"]],
            "first_session_steps": [step["title"] for step in sessions["1"]],
            "second_session_action": sessions["2"][0]["agent"],
        },
        "path-chooser": {
            "executors": [{"name": row["name"], "path": row["path"]} for row in executors],
            "modes": [row["title"] for row in modes],
            "roles": {row["title"]: row["role"] for row in modes},
            "mode_tools": {mode["title"]: [row["name"] for row in executors if mode["title"] in row["path"].split(" or ")]
                           for mode in modes},
        },
    }


def render_role_figures(root: Path, workflow_projection: dict, fixture: tuple[dict, list[str], str]) -> dict[str, str]:
    content = yaml.safe_load((root / "site/content/role_figures.yaml").read_text(encoding="utf-8"))["figures"]
    facts = collect_role_figure_facts(root, workflow_projection, fixture)
    manifest = json.loads((root / "docs/reference/agentic-kit-commands.json").read_text(encoding="utf-8"))
    known = {row["qualified_name"] for row in manifest["commands"]}
    result = render_mode_figures(modes_for("site"), workflow_projection["modes"], known)
    for name in NAMES:
        for narrow in (False, True):
            filename = name + ("-narrow" if narrow else "") + ".svg"
            if name == "path-chooser":
                result[filename] = render_path_chooser(content[name], facts[name], narrow=narrow)
            else:
                cards = _cards(name, facts[name], content[name])
                result[filename] = _render_svg(name, content[name], facts[name], cards, narrow=narrow)
    for name in ("background-and-ownership", "kit-conductor"):
        if content[name]["published"] is not True:
            continue
        commands = ("agentic-kit work start", "agentic-kit work finish")
        documented = {step["command"] for step in fixture[0]["steps"]}
        if not set(commands) <= known & documented:
            raise ValueError(f"{name} requires the documented generated-project work cycle")
        for narrow in (False, True):
            filename = name + ("-narrow" if narrow else "") + ".svg"
            result[filename] = render_ownership_figure(
                name, content[name], facts["path-chooser"]["executors"], commands, narrow=narrow,
            )
    return result


def _cards(name: str, facts: dict, content: dict) -> list[Card]:
    if name == "asked-checked-enforced":
        local = "Local: " + " and ".join(command.removeprefix("agentic-kit ") for command in facts["manifest_commands"])
        return [
            ("1  Asked", [Path(path).name for path in facts["instruction_files"]] + [content["asked"]], MUTED),
            ("2  Checked", [local, *facts["ci_summary"], *content["checked"]], ACCENT),
            ("3  Enforced", [content["branch_protection"]], ACCENT2),
        ]
    if name == "repository-memory":
        return [
            ("Session 1", facts["first_session_steps"], ACCENT),
            ("Repository files", facts["shown_files"], INK),
            ("Session 2", [facts["second_session_action"]], ACCENT2),
            ("Chat history", ["not carried over"], MUTED),
        ]
    raise ValueError(f"unknown role figure: {name}")


def _lines(items: list[str], width: int) -> list[str]:
    lines = []
    for item in items:
        for line in wrap(item, width, break_long_words=False, break_on_hyphens=False):
            # textwrap leaves an oversized word on its own line. Split long
            # filenames only at path or name separators.
            while len(line) > width:
                split = max(line.rfind(separator, 0, width) for separator in "/_-") + 1
                if split == 0:
                    break
                lines.append(line[:split])
                line = line[split:]
            lines.append(line)
    return lines


def _source_lines(items: list[str], width: int) -> list[tuple[str, str]]:
    return [(line, item) for item in items for line in _lines([item], width)]


def _card(x: int, y: int, width: int, height: int, heading: str, lines: list[tuple[str, str]], color: str,
          *, bar: bool = False, dashed: bool = False) -> list[str]:
    fill = TINT[color] if bar else "#fff"
    dash = ' stroke-dasharray="6 5"' if dashed else ""
    elements = [f'<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" '
                f'fill="{fill}" stroke="{color}" stroke-width="1.5"{dash}/>']
    if bar:
        elements.append(f'<rect x="{x}" y="{y}" width="{width}" height="8" rx="4" fill="{color}"/>')
    elements.append(text_node(heading, x + 14, y + 29, kind="head"))
    elements.extend(text_node(line, x + 14, y + 56 + i * 23, source=source)
                    for i, (line, source) in enumerate(lines))
    return elements


def _control_layout(cards: list[Card], *, narrow: bool) -> tuple[list[str], int]:
    elements = []
    width, gap = (432, 24) if narrow else (288, 24)
    rows = [_source_lines(items, 47 if narrow else 31) for _, items, _ in cards]
    heights = []
    for lines in rows:
        required = 64 + 23 * len(lines)
        heights.append(max(required, heights[-1] + 26) if heights else required)
    y = 98
    bottom = y + heights[-1]
    for index, ((heading, _, color), lines, height) in enumerate(zip(cards, rows, heights)):
        x = 24 if narrow else 24 + index * (width + gap)
        top = y if narrow else bottom - height
        elements.extend(_card(x, top, width, height, heading, lines, color, bar=True))
        if narrow:
            y += height + gap
    return elements, y - gap if narrow else bottom


def _repository_files(y: int, width: int, repository: Card, *, narrow: bool) -> tuple[list[str], int]:
    heading, files, color = repository
    file_groups = [[path] for path in files[:3]] + [files[3:]]
    columns = 1 if narrow else len(file_groups)
    gap = 10
    file_width = (width - (columns + 1) * gap) // columns
    rows = [_source_lines(group, 31 if narrow else 24) for group in file_groups]
    contents = []
    top = y + 41
    for start in range(0, len(rows), columns):
        row = rows[start:start + columns]
        height = 16 + 19 * max(map(len, row))
        for column, lines in enumerate(row):
            x = 24 + gap + column * (file_width + gap)
            contents.append(f'<rect x="{x}" y="{top}" width="{file_width}" height="{height}" rx="8" '
                            f'fill="#fff" stroke="{LINE}" stroke-width="1.5"/>')
            contents.extend(text_node(line, x + 9, top + 21 + index * 19, source=source)
                            for index, (line, source) in enumerate(lines))
        top += height + gap
    height = top - y
    return _card(24, y, width, height, heading, [], color) + contents, height


def _memory_layout(cards: list[Card], labels: dict, *, narrow: bool) -> tuple[list[str], int]:
    first, repository, second, history = cards
    session_width = 432 if narrow else 328
    width = 47 if narrow else 36
    first_lines = _source_lines(first[1], width)
    second_lines = _source_lines(second[1], width)
    if len(second_lines) > 2:
        second_line, source = second_lines[1]
        if len(second_line) >= width:
            second_line = second_line.rsplit(" ", 1)[0]
        second_lines = [second_lines[0], (second_line + "…", source)]

    first_height = 64 + 23 * len(first_lines)
    second_height = 64 + 23 * len(second_lines)
    history_width = 138 if narrow else 206
    repository_width = 432 - history_width - 18 if narrow else 912
    session_y = 98
    first_bottom = session_y + first_height
    second_x = 24 if narrow else 608
    second_y = session_y
    repository_y = first_bottom + 58
    repository_parts, repository_height = _repository_files(repository_y, repository_width, repository, narrow=narrow)
    if narrow:
        second_y = repository_y + repository_height + 58
        history_x, history_y = 24 + repository_width + 18, repository_y
    else:
        history_x, history_y = (960 - history_width) // 2, session_y + 13

    elements = _card(24, session_y, session_width, first_height, first[0], first_lines, first[2])
    elements.extend(_card(second_x, second_y, session_width, second_height, second[0], second_lines, second[2]))
    elements.extend(_card(history_x, history_y, history_width, 86, history[0], _source_lines(history[1], 20), history[2], dashed=True))
    elements.extend(repository_parts)
    center = 24 + (repository_width if narrow else session_width) // 2
    repository_bottom = repository_y + repository_height
    if narrow:
        read_arrow = (center, repository_bottom, second_y)
    else:
        read_arrow = (second_x + session_width // 2, repository_y, second_y + second_height)
    for label, (x, start, end), color in (
        (labels["writes"], (center, first_bottom, repository_y), ACCENT),
        (labels["reads"], read_arrow, ACCENT2),
    ):
        tip = end - 3 if end > start else end + 3
        elbow = tip - 6 if end > start else tip + 6
        elements.append(f'<path d="M{x} {start}V{tip}m-5 {elbow - tip} 5 {tip - elbow} 5 {elbow - tip}" '
                        f'fill="none" stroke="{color}" stroke-width="1.5"/>')
        elements.append(text_node(label, x + 12, (start + end) // 2 + 5))
    return elements, max(repository_bottom, second_y + second_height)


def _render_svg(name: str, content: dict, facts: dict, cards: list[Card], *, narrow: bool) -> str:
    width = 480 if narrow else 960
    if name == "asked-checked-enforced":
        body, bottom = _control_layout(cards, narrow=narrow)
    else:
        body, bottom = _memory_layout(cards, content["arrow_labels"], narrow=narrow)
    foot_lines = _source_lines([content["footnote"]], 55 if narrow else 110)
    height = bottom + 66 + 20 * len(foot_lines)
    title = escape(str(content["title"]))
    desc = escape(f"{content['title']}. " + ". ".join(heading + ": " + ", ".join(items) for heading, items, _ in cards) + ". " + str(content["footnote"]))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{title}</title><desc id="desc">{desc}</desc>',
             '<style>.title{font:700 22px sans-serif;fill:#17202a}.sub{font:15px sans-serif;fill:#586674}'
             '.head{font:700 16px sans-serif;fill:#17202a}.body{font:14px sans-serif;fill:#17202a}'
             '.foot{font:14px sans-serif;fill:#586674}</style>',
             f'<metadata>{escape(json.dumps(facts, sort_keys=True))}</metadata>',
             f'<rect width="{width}" height="{height}" fill="#fff"/>',
             text_node(content["title"], 24, 36, kind="title"),
             text_node(content["subtitle"], 24, 65, kind="sub"), *body]
    parts.extend(text_node(line, 24, bottom + 40 + i * 20, kind="foot", source=source)
                 for i, (line, source) in enumerate(foot_lines))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
