"""Render the Quickstart file map from the documented init example."""
from __future__ import annotations

from html import escape
import json
import os
from pathlib import Path
import shlex
import subprocess
import sys
from tempfile import TemporaryDirectory

import yaml


def render_init_files_figure(root: Path, *, version: str) -> str:
    """Run the example locally and project its generated files into an SVG."""
    example = yaml.safe_load((root / "site/content/usage_example.yaml").read_text(encoding="utf-8"))
    step = example["steps"][0]
    argv = list(step["argv"])
    project_dir = str(example["project_dir"])
    if step["command"] != "agentic-kit init" or argv[:2] != ["init", project_dir]:
        raise ValueError("init figure requires the documented init example")
    with TemporaryDirectory(prefix="kit-site-init-") as scratch:
        project = Path(scratch) / project_dir
        source = Path(__file__).resolve().parents[1]
        environment = {**os.environ, "PYTHONPATH": str(source) + os.pathsep + os.environ.get("PYTHONPATH", "")}
        result = subprocess.run(
            [sys.executable, "-c", "from agentic_project_kit.cli import app; app()", *argv, "--json"],
            cwd=scratch, env=environment, capture_output=True, text=True, check=False,
        )
        if result.returncode != 0:
            raise ValueError(f"documented init failed with exit code {result.returncode}")
        files = sorted(
            path.relative_to(project).as_posix()
            for path in project.rglob("*")
            if path.is_file() and ".git" not in path.relative_to(project).parts
        )
    groups = (
        ("Agent instructions", [path for path in files if path == "AGENTS.md" or path.endswith("copilot-instructions.md")]),
        ("Project state", [path for path in files if path.startswith(".agentic/") or path in {"docs/STATUS.md", "docs/PROJECT_START.md"}]),
        ("Checks", [path for path in files if path.startswith("tests/") or path in {"docs/TEST_GATES.md", "pyproject.toml"}]),
        ("CI", [path for path in files if path.startswith(".github/workflows/")]),
        ("Handoff", [path for path in files if path.startswith("docs/handoff/")]),
    )
    assigned = {path for _, paths in groups for path in paths}
    groups += (("Other project files", [path for path in files if path not in assigned]),)
    cards = []
    for index, (label, paths) in enumerate(groups):
        x = 24 + (index % 3) * 312
        y = 102 + (index // 3) * 172
        lines = [f'<rect x="{x}" y="{y}" width="294" height="152" rx="12" fill="#eef3fa" stroke="#b8c9dc"/>',
                 f'<text x="{x + 16}" y="{y + 27}" class="heading">{escape(label)} · {len(paths)}</text>']
        for row, path in enumerate(paths[:3]):
            lines.append(f'<text x="{x + 16}" y="{y + 56 + row * 24}" class="file">{escape(_short_path(path))}</text>')
        if len(paths) > 3:
            lines.append(f'<text x="{x + 16}" y="{y + 135}" class="more">+ {len(paths) - 3} more</text>')
        cards.extend(lines)
    caption = f"agentic-kit {shlex.join(str(part) for part in argv)}, Kit {version}"
    metadata = escape(json.dumps({"files": files}, sort_keys=True), quote=False)
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 464" role="img" aria-labelledby="title desc">\n'
        '<title id="title">Your repository after init</title>\n'
        f'<desc id="desc">Selected generated files grouped by purpose. {escape(caption)}. Counts apply only to this command.</desc>\n'
        f'<metadata>{metadata}</metadata>\n'
        '<style>.title{font:700 24px sans-serif;fill:#17365d}.subtitle{font:15px sans-serif;fill:#334b64}'
        '.heading{font:700 17px sans-serif;fill:#17365d}.file{font:14px monospace;fill:#18364f}'
        '.more{font:14px sans-serif;fill:#45627e}</style>\n'
        '<rect width="960" height="464" fill="#fff"/>\n'
        '<text x="24" y="35" class="title">Your repository after init</text>\n'
        f'<text x="24" y="64" class="subtitle">{escape(caption)}</text>\n'
        + "\n".join(cards) + "\n</svg>\n"
    )


def _short_path(path: str) -> str:
    if len(path) <= 30:
        return path
    filename = path.rsplit("/", 1)[-1]
    shortened = "…/" + filename
    return shortened if len(shortened) <= 30 else filename[:29] + "…"
