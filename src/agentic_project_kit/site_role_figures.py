"""Generate accessible role figures from reviewed website and init sources."""
from __future__ import annotations

from html import escape
import json
from pathlib import Path
from textwrap import wrap

import yaml


INK = "#17202a"
MUTED = "#586674"
LINE = "#c8d3dc"
ACCENT = "#0f766e"
ACCENT2 = "#3454d1"
WARN = "#a16207"
NAMES = ("asked-checked-enforced", "repository-memory", "path-chooser")


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
    ci = yaml.load(ci_text, Loader=yaml.BaseLoader)
    events = ci.get("on", {})
    if not isinstance(events, dict) or not {"push", "pull_request"} <= set(events):
        raise ValueError("generated CI trigger changed")
    ci_steps = [str(step["run"]).strip() for job in ci.get("jobs", {}).values() for step in job.get("steps", []) if "run" in step]
    if not any("agentic-kit check" in step.splitlines() for step in ci_steps):
        raise ValueError("generated CI no longer runs agentic-kit check")
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
            "ci_events": list(events), "ci_steps": ci_steps,
            "manifest_commands": sorted({"agentic-kit check", "agentic-kit doctor"}),
            "instruction_files": required[:1] + [prompt],
        },
        "repository-memory": {
            "init_files": files, "shown_files": shown,
            "steps": [row["title"] for row in example["steps"]],
            "sessions": [{"name": session, "steps": [row["title"] for row in example["steps"] if str(row["session"]) == session]}
                         for session in ("1", "2")],
        },
        "path-chooser": {
            "executors": [{"name": row["name"], "path": row["path"]} for row in executors],
            "modes": [row["title"] for row in modes],
            "mode_tools": {mode["title"]: [row["name"] for row in executors if mode["title"] in row["path"].split(" or ")]
                           for mode in modes},
        },
    }


def render_role_figures(root: Path, workflow_projection: dict, fixture: tuple[dict, list[str], str]) -> dict[str, str]:
    content = yaml.safe_load((root / "site/content/role_figures.yaml").read_text(encoding="utf-8"))["figures"]
    facts = collect_role_figure_facts(root, workflow_projection, fixture)
    result = {}
    for name in NAMES:
        for narrow in (False, True):
            cards = _cards(name, facts[name], content[name])
            result[name + ("-narrow" if narrow else "") + ".svg"] = _render_svg(name, content[name], facts[name], cards, narrow=narrow)
    return result


def _cards(name: str, facts: dict, content: dict) -> list[tuple[str, list[str], str]]:
    if name == "asked-checked-enforced":
        checks = [step.replace("\n", " ") for step in facts["ci_steps"]]
        return [
            ("1  Asked", facts["instruction_files"] + ["Agent instructions guide work; they can be ignored."], MUTED),
            ("2  Checked", facts["manifest_commands"] + ["CI: " + ", ".join(facts["ci_events"])] + checks, ACCENT),
            ("3  Enforced", [content["branch_protection"]], ACCENT2),
        ]
    if name == "repository-memory":
        return [
            ("Session 1", facts["sessions"][0]["steps"], ACCENT),
            ("Repository files", facts["shown_files"], INK),
            ("Session 2", facts["sessions"][1]["steps"], ACCENT2),
            ("Chat history", ["not carried over"], MUTED),
        ]
    return [(mode, facts["mode_tools"][mode] or ["Kit interface"], (ACCENT, ACCENT2, WARN, MUTED)[i % 4])
            for i, mode in enumerate(facts["modes"])]


def _render_svg(name: str, content: dict, facts: dict, cards: list[tuple[str, list[str], str]], *, narrow: bool) -> str:
    width = 480 if narrow else 960
    columns = 1 if narrow else (2 if name == "path-chooser" else 3)
    gap = 24
    margin = 24
    card_width = (width - 2 * margin - (columns - 1) * gap) // columns
    max_chars = 47 if narrow else (31 if columns == 3 else 43)
    wrapped = [(heading, [line for item in items for line in (wrap(str(item), max_chars, break_long_words=True) or [""])], color)
               for heading, items, color in cards]
    row_heights = []
    for start in range(0, len(wrapped), columns):
        row_heights.append(max(64 + 23 * len(lines) for _, lines, _ in wrapped[start:start + columns]))
    foot_lines = wrap(str(content["footnote"]), 55 if narrow else 110)
    height = 116 + sum(row_heights) + gap * (len(row_heights) - 1) + 48 + 20 * len(foot_lines)
    title = escape(str(content["title"]))
    subtitle = escape(str(content["subtitle"]))
    desc = escape(f"{content['title']}. " + ". ".join(heading + ": " + ", ".join(items) for heading, items, _ in cards) + ". " + str(content["footnote"]))
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">',
             f'<title id="title">{title}</title><desc id="desc">{desc}</desc>',
             '<style>.title{font:700 22px sans-serif;fill:#17202a}.sub{font:15px sans-serif;fill:#586674}'
             '.head{font:700 16px sans-serif;fill:#17202a}.body{font:14px sans-serif;fill:#17202a}'
             '.foot{font:14px sans-serif;fill:#586674}</style>',
             f'<metadata>{escape(json.dumps(facts, sort_keys=True))}</metadata>',
             f'<rect width="{width}" height="{height}" fill="#fff"/>',
             f'<text x="24" y="36" class="title">{title}</text>',
             f'<text x="24" y="65" class="sub">{subtitle}</text>']
    row_y = 98
    for row_index, row_height in enumerate(row_heights):
        for col, (heading, lines, color) in enumerate(wrapped[row_index * columns:(row_index + 1) * columns]):
            x = margin + col * (card_width + gap)
            dash = ' stroke-dasharray="6 5"' if name == "repository-memory" and row_index * columns + col == 3 else ""
            parts.append(f'<rect x="{x}" y="{row_y}" width="{card_width}" height="{row_height}" rx="10" fill="#fff" stroke="{color}" stroke-width="1.5"{dash}/>')
            parts.append(f'<text x="{x + 14}" y="{row_y + 29}" class="head">{escape(heading)}</text>')
            parts.extend(f'<text x="{x + 14}" y="{row_y + 56 + i * 23}" class="body">{escape(line)}</text>' for i, line in enumerate(lines))
            if name == "repository-memory" and row_index * columns + col < 2:
                if narrow:
                    start_x, start_y = x + card_width // 2, row_y + row_height
                    arrow = "M0 0v22m-5 -5 5 5 5 -5"
                else:
                    start_x, start_y = x + card_width, row_y + row_height // 2
                    arrow = "M0 0h22m-5 -5 5 5 -5 5"
                parts.append(f'<path d="{arrow}" transform="translate({start_x} {start_y})" fill="none" stroke="{MUTED}" stroke-width="1.5"/>')
        row_y += row_height + gap
    parts.extend(f'<text x="24" y="{row_y + 16 + i * 20}" class="foot">{escape(line)}</text>'
                 for i, line in enumerate(foot_lines))
    parts.append("</svg>")
    return "\n".join(parts) + "\n"
