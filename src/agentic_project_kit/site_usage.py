"""Source-bound first-contact page for coding agents and browser chats."""
from __future__ import annotations

from html import escape
from pathlib import Path
import re
import shlex
from string import Template
from urllib.parse import urlsplit

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
        source_label = urlsplit(source).hostname if source.startswith("https://") else "workflows page"
        tool_rows.append(
            "<tr>"
            f"<td>{escape(str(row['name']))}</td><td>{escape(str(row['path']))}</td>"
            f"<td>{escape(str(row['instructions']))}</td>"
            f'<td><a href="{escape(source, quote=True)}">Source: {escape(str(source_label))}</a> · {escape(str(row["reviewed"]))}</td>'
            "</tr>"
        )
    if not isinstance(example, dict) or example.get("kind") != "generated-project-first-cycle":
        raise ValueError("usage example is invalid")
    steps = example.get("steps")
    if not isinstance(steps, list) or not steps:
        raise ValueError("usage example has no steps")
    step_rows = []
    session_labels = {"setup": "Set up once", "1": "Session 1", "2": "Session 2"}
    last_session = None
    for step in steps:
        if not isinstance(step, dict) or "command" not in step or not all(step.get(key) for key in ("title", "session", "you", "agent", "kit")):
            raise ValueError("usage example step is incomplete")
        session = str(step["session"])
        if session not in session_labels:
            raise ValueError(f"usage example step has invalid session: {session}")
        if session != last_session:
            if last_session is not None and list(session_labels).index(session) < list(session_labels).index(last_session):
                raise ValueError("usage example step sessions are out of order")
            step_rows.append(f'<tr class="session-heading"><th colspan="4" scope="colgroup">{session_labels[session]}</th></tr>')
            last_session = session
        command = step["command"]
        if command is None:
            if "argv" in step:
                raise ValueError("usage example step has argv without command")
            command_html = "No Kit command"
        else:
            argv = step.get("argv")
            if not isinstance(command, str) or not isinstance(argv, list) or not argv:
                raise ValueError("usage example step requires command and argv together")
            if command not in command_names or argv[:len(command.split()) - 1] != command.split()[1:]:
                raise ValueError(f"usage example command is not in the manifest or argv disagrees: {command}")
            command_html = f"<code>{escape(shlex.join(['agentic-kit', *(str(part) for part in argv)]))}</code>"
        step_rows.append(
            "<tr>"
            f"<th scope=\"row\">{escape(str(step['title']))}<br>{command_html}</th>"
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
