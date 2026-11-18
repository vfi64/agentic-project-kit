"""The public agent walkthrough is backed by a runnable generated project."""
from __future__ import annotations

from html import unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
import shlex
import shutil
from xml.etree import ElementTree as ET

import pytest
from typer.testing import CliRunner
import yaml

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import load_manifest
from agentic_project_kit.site_generator import build_site
from agentic_project_kit.site_usage import render_usage_page
from agentic_project_kit.templates import BASE_FILES


ROOT = Path(__file__).resolve().parents[1]


class VisibleText(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)


def test_public_usage_page_renders_template_prompt_and_source_bound_tools(tmp_path: Path) -> None:
    result = build_site(ROOT, output_dir=tmp_path / "site", build_commit="a" * 40)

    assert result.ok, result.report.blockers
    page = (tmp_path / "site/use/index.html").read_text(encoding="utf-8")
    prompt = BASE_FILES["docs/handoff/STANDARD_AGENT_PROMPT.md"].split("```text\n", 1)[1].split("\n```", 1)[0]
    displayed = re.search(r'<pre id="starter-prompt"><code>(.*?)</code></pre>', page, re.S)
    assert displayed is not None
    assert unescape(displayed[1]) == prompt
    assert "Codex" in page and "Claude Code" in page and "Browser chat" in page
    assert "What you do" in page and "What the agent does" in page and "What the Kit checks" in page
    assert "docs/handoff/CURRENT_HANDOFF.md" in page
    assert "transfer chat-switch-complete" not in page


def test_public_usage_commands_run_in_generated_project(tmp_path: Path, monkeypatch) -> None:
    example = yaml.safe_load((ROOT / "site/content/usage_example.yaml").read_text(encoding="utf-8"))
    known = {row["qualified_name"] for row in load_manifest(ROOT)["commands"]}
    runner = CliRunner()
    monkeypatch.chdir(tmp_path)
    for step in example["steps"]:
        assert step["command"] in known
        result = runner.invoke(app, step["argv"])
        assert result.exit_code == 0, (step["command"], result.output)
        if step["command"] == "agentic-kit init":
            monkeypatch.chdir(tmp_path / example["project_dir"])


@pytest.mark.parametrize("missing", ["source", "reviewed"])
def test_usage_page_rejects_unattributed_tool_claims(tmp_path: Path, missing: str) -> None:
    for relative in ("site/templates/use.html", "site/content/usage_example.yaml", "site/content/executors.yaml"):
        target = tmp_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / relative, target)
    path = tmp_path / "site/content/executors.yaml"
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    del data["executors"][0][missing]
    path.write_text(yaml.safe_dump(data), encoding="utf-8")

    with pytest.raises(ValueError, match="source and reviewed"):
        render_usage_page(
            tmp_path,
            command_names={row["qualified_name"] for row in load_manifest(ROOT)["commands"]},
            product_name="Agentic Project Kit",
        )


def test_entry_pages_do_not_show_internal_work_ids(tmp_path: Path) -> None:
    result = build_site(ROOT, output_dir=tmp_path / "site", build_commit="a" * 40)
    assert result.ok, result.report.blockers
    pattern = re.compile(r"\b(?:KIT-GF-\d+|[BCDGKP]\d+[a-z]?|B1_EVALUABLE|BOUNDED_COMPLETE|PAA|DPA)\b")
    for relative in ("index.html", "quickstart/index.html", "workflows/index.html", "use/index.html"):
        visible = VisibleText()
        visible.feed((tmp_path / "site" / relative).read_text(encoding="utf-8"))
        assert not pattern.search(" ".join(visible.parts)), relative


def test_development_case_details_live_on_evidence_page(tmp_path: Path) -> None:
    result = build_site(ROOT, output_dir=tmp_path / "site", build_commit="a" * 40)
    assert result.ok, result.report.blockers
    evidence = (tmp_path / "site/evidence/index.html").read_text(encoding="utf-8")
    overview = (tmp_path / "site/index.html").read_text(encoding="utf-8")
    workflows = (tmp_path / "site/workflows/index.html").read_text(encoding="utf-8")
    assert 'id="development-cases"' in evidence
    assert "KIT-GF-078" in evidence
    assert "Five maintenance cycles in one familiar repository" in evidence
    assert "KIT-GF-078" not in overview
    assert "B1 Closeout" not in workflows


def test_observed_workflow_detail_lives_on_evidence_page(tmp_path: Path) -> None:
    result = build_site(ROOT, output_dir=tmp_path / "site", build_commit="a" * 40)
    assert result.ok, result.report.blockers
    understand = (tmp_path / "site/understand/index.html").read_text(encoding="utf-8")
    evidence = (tmp_path / "site/evidence/index.html").read_text(encoding="utf-8")
    assert 'id="figure-G0"' not in understand
    assert 'id="observed-workflow"' in evidence
    assert "../understand/G0-mobile.svg" in evidence


def test_quickstart_figure_uses_files_from_documented_init(tmp_path: Path, monkeypatch) -> None:
    example = yaml.safe_load((ROOT / "site/content/usage_example.yaml").read_text(encoding="utf-8"))
    init_argv = list(example["steps"][0]["argv"])
    project = tmp_path / example["project_dir"]
    monkeypatch.chdir(tmp_path)
    result = CliRunner().invoke(app, [*init_argv, "--json"])
    assert result.exit_code == 0, result.output
    expected = sorted(path.relative_to(project).as_posix() for path in project.rglob("*")
                      if path.is_file() and ".git" not in path.relative_to(project).parts)

    built = build_site(ROOT, output_dir=tmp_path / "site", build_commit="a" * 40)
    assert built.ok, built.report.blockers
    quickstart = (tmp_path / "site/quickstart/index.html").read_text(encoding="utf-8")
    assert "../static/init-files.svg" in quickstart
    figure = ET.parse(tmp_path / "site/static/init-files.svg").getroot()
    ns = {"svg": "http://www.w3.org/2000/svg"}
    metadata = figure.find("svg:metadata", ns)
    assert metadata is not None
    assert json.loads(metadata.text or "{}") == {"files": expected}
    assert shlex.join(init_argv) in "".join(figure.itertext())


def test_entry_figures_keep_text_legible_at_desktop_width() -> None:
    hero = ET.parse(ROOT / "site/static/kit-architecture.svg").getroot()
    sizes = [int(node.attrib["font-size"]) for node in hero.findall(".//*[@font-size]")]
    assert sizes and min(sizes) >= 26
    quickstart_css = (ROOT / "site/static/site.css").read_text(encoding="utf-8")
    assert ".quickstart-overview" in quickstart_css
