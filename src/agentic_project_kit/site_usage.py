"""Source-bound first-contact page for coding agents and browser chats."""
from __future__ import annotations

from html import escape
from pathlib import Path
import re
from string import Template

import yaml

from .site_navigation import render_site_navigation
from .templates import BASE_FILES


def render_usage_page(root: Path, *, command_names: set[str], product_name: str) -> str:
    """Render the tested init cycle and tool guidance from reviewed sources."""
    executors = yaml.safe_load((root / "site/content/executors.yaml").read_text(encoding="utf-8"))
    example = yaml.safe_load((root / "site/content/usage_example.yaml").read_text(encoding="utf-8"))
    if not isinstance(executors, dict) or executors.get("kind") != "website-executor-paths":
        raise ValueError("executor path content is invalid")
    rows = executors.get("executors")
    if not isinstance(rows, list) or not rows:
        raise ValueError("executor path list is missing")
    tool_rows = []
    for row in rows:
        if not isinstance(row, dict) or not all(row.get(key) for key in ("name", "path", "instructions", "source", "reviewed")):
            raise ValueError("executor path requires name, path, instructions, source and reviewed")
        source = str(row["source"])
        if not (source.startswith("https://") or source == "../workflows/index.html"):
            raise ValueError("executor source must be an HTTPS or reviewed local link")
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", str(row["reviewed"])):
            raise ValueError("executor reviewed date must be YYYY-MM-DD")
        tool_rows.append(
            "<tr>"
            f"<td>{escape(str(row['name']))}</td><td>{escape(str(row['path']))}</td>"
            f"<td>{escape(str(row['instructions']))}</td>"
            f'<td><a href="{escape(source, quote=True)}">Source</a> · {escape(str(row["reviewed"]))}</td>'
            "</tr>"
        )
    if not isinstance(example, dict) or example.get("kind") != "generated-project-first-cycle":
        raise ValueError("usage example is invalid")
    steps = example.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("usage example has no steps")
    step_rows = []
    for step in steps:
        if not isinstance(step, dict) or not all(step.get(key) for key in ("command", "argv", "title", "you", "agent", "kit")):
            raise ValueError("usage example step is incomplete")
        command = str(step["command"])
        argv = step["argv"]
        if command not in command_names or not isinstance(argv, list) or argv[:len(command.split()) - 1] != command.split()[1:]:
            raise ValueError(f"usage example command is not in the manifest or argv disagrees: {command}")
        step_rows.append(
            "<tr>"
            f"<th scope=\"row\">{escape(str(step['title']))}<br><code>{escape('agentic-kit ' + ' '.join(str(part) for part in argv))}</code></th>"
            f"<td>{escape(str(step['you']))}</td><td>{escape(str(step['agent']))}</td>"
            f"<td>{escape(str(step['kit']))}</td>"
            "</tr>"
        )
    prompt = BASE_FILES["docs/handoff/STANDARD_AGENT_PROMPT.md"].split("```text\n", 1)[1].split("\n```", 1)[0]
    template = Template((root / "site/templates/use.html").read_text(encoding="utf-8"))
    return template.substitute(
        site_nav=render_site_navigation("use/index.html"),
        product_name=escape(product_name),
        tools="\n".join(tool_rows),
        steps="\n".join(step_rows),
        starter_prompt=escape(prompt),
    ).rstrip() + "\n"
