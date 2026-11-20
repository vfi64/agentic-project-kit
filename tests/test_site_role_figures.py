"""Source-bound role figures on the public website."""
from __future__ import annotations

import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import pytest
import yaml

from agentic_project_kit.site_generator import build_site
from agentic_project_kit.site_role_figures import collect_role_figure_facts


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ("asked-checked-enforced", "repository-memory", "path-chooser")


@pytest.fixture(scope="module")
def built_site(tmp_path_factory: pytest.TempPathFactory) -> Path:
    output = tmp_path_factory.mktemp("role-figures") / "site"
    result = build_site(ROOT, output_dir=output, build_commit="a" * 40)
    assert result.ok, result.report.blockers
    return output


def _svg(output: Path, name: str, narrow: bool = False) -> tuple[str, ET.Element]:
    suffix = "-narrow" if narrow else ""
    source = (output / "static" / f"{name}{suffix}.svg").read_text(encoding="utf-8")
    return source, ET.fromstring(source)


def _facts(root: ET.Element) -> dict:
    metadata = root.find("{http://www.w3.org/2000/svg}metadata")
    assert metadata is not None and metadata.text
    return json.loads(metadata.text)


def test_role_figures_are_accessible_responsive_and_source_bound(built_site: Path) -> None:
    pages = {"asked-checked-enforced": "understand/index.html", "repository-memory": "use/index.html", "path-chooser": "workflows/index.html"}
    for name in FIGURES:
        for narrow in (False, True):
            source, root = _svg(built_site, name, narrow)
            assert root.attrib["role"] == "img"
            assert root.attrib["viewBox"].split()[2] == ("480" if narrow else "960")
            assert root.findtext("{http://www.w3.org/2000/svg}title")
            assert len(root.findtext("{http://www.w3.org/2000/svg}desc") or "") >= 20
            sizes = [int(size) for size in re.findall(r"font:\s*(?:\d+\s+)?(\d+)px", source)]
            assert sizes and min(sizes) >= (14 if narrow else 13)
        page = (built_site / pages[name]).read_text(encoding="utf-8")
        assert re.search(rf'<picture>\s*<source[^>]+{name}-narrow\.svg[^>]*>\s*<img[^>]+{name}\.svg', page)


def test_path_figure_uses_executor_names_and_current_site_modes(built_site: Path) -> None:
    facts = _facts(_svg(built_site, "path-chooser")[1])
    executors = yaml.safe_load((ROOT / "site/content/executors.yaml").read_text(encoding="utf-8"))["executors"]
    projection = json.loads((built_site / "workflows/workflows.json").read_text(encoding="utf-8"))
    assert facts["executors"] == [{"name": row["name"], "path": row["path"]} for row in executors]
    assert facts["modes"] == [row["title"] for row in projection["modes"]]
    for mode, names in facts["mode_tools"].items():
        assert names == [row["name"] for row in executors if mode in row["path"].split(" or ")]
    assert all(row["name"] in _svg(built_site, "path-chooser")[0] for row in executors)


def test_repository_figure_uses_init_files_and_example_steps(built_site: Path) -> None:
    facts = _facts(_svg(built_site, "repository-memory")[1])
    repository_svg = _svg(built_site, "repository-memory")[0]
    init_map = ET.parse(built_site / "static/init-files.svg").getroot()
    example = yaml.safe_load((ROOT / "site/content/usage_example.yaml").read_text(encoding="utf-8"))
    assert facts["steps"] == [row["title"] for row in example["steps"]]
    assert set(facts["shown_files"]) <= set(_facts(init_map)["files"])
    assert "Chat history" in repository_svg and "not carried over" in repository_svg


def test_enforcement_figure_uses_generated_ci_and_manifest(built_site: Path) -> None:
    facts = _facts(_svg(built_site, "asked-checked-enforced")[1])
    assert "push" in facts["ci_events"] and "pull_request" in facts["ci_events"]
    assert "agentic-kit check" in facts["ci_steps"]
    assert "agentic-kit check" in facts["manifest_commands"]
    assert "pytest" in " ".join(facts["ci_steps"])


def test_role_figure_blocks_when_ci_drops_the_kit_check() -> None:
    ci = "on: {push: {}, pull_request: {}}\njobs: {test: {steps: [{run: pytest}]}}"
    with pytest.raises(ValueError, match="generated CI no longer runs agentic-kit check"):
        collect_role_figure_facts(ROOT, {}, ({}, [], ci))


def test_unpublished_figures_are_not_embedded(built_site: Path) -> None:
    content = yaml.safe_load((ROOT / "site/content/role_figures.yaml").read_text(encoding="utf-8"))
    assert content["figures"]["background-and-ownership"]["published"] is False
    assert content["figures"]["kit-conductor"]["published"] is False
    pages = " ".join(path.read_text(encoding="utf-8") for path in built_site.rglob("*.html"))
    assert "background-and-ownership.svg" not in pages
    assert "kit-conductor.svg" not in pages
