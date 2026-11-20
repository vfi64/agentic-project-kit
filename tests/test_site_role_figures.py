"""Source-bound role figures on the public website."""
from __future__ import annotations

import json
from pathlib import Path
import re
from xml.etree import ElementTree as ET

import pytest
import yaml

from agentic_project_kit.site_generator import build_site
from agentic_project_kit.site_role_figures import _ci_summary, _lines, collect_role_figure_facts


ROOT = Path(__file__).resolve().parents[1]
FIGURES = ("asked-checked-enforced", "repository-memory", "path-chooser")


def test_every_website_mode_has_a_sequence_in_its_own_card(built_site: Path) -> None:
    from agentic_project_kit.workflow_modes import modes_for

    page = (built_site / "workflows/index.html").read_text()
    slugs = {mode.mode_id.replace("_", "-") for mode in modes_for("site")}
    assert {path.stem.removeprefix("mode-") for path in (built_site / "static").glob("mode-*.svg")
            if not path.stem.endswith("-narrow")} == slugs
    for mode in modes_for("site"):
        slug = mode.mode_id.replace("_", "-")
        card = page.split(f'id="mode-{slug}"', 1)[1].split("</article>", 1)[0]
        assert f"mode-{slug}.svg" in card and f"mode-{slug}-narrow.svg" in card
        for narrow in (False, True):
            _, svg = _svg(built_site, f"mode-{slug}", narrow)
            facts = _facts(svg)
            assert [step["action"] for step in facts["flow"]] == [step.action for step in mode.flow]
            assert svg.get("role") == "img" and len(svg.findtext("{http://www.w3.org/2000/svg}desc") or "") >= 20
            assert all(step.command in card for step in mode.flow if step.command)


def test_added_website_mode_gets_a_diagram_and_requires_a_flow(tmp_path: Path, monkeypatch) -> None:
    from dataclasses import replace
    from agentic_project_kit import workflow_modes
    from agentic_project_kit.workflow_modes import WorkflowStep

    original = workflow_modes.WORKFLOW_MODES
    extra = replace(
        next(mode for mode in original if mode.mode_id == "gui"),
        mode_id="test_extra", label="Extra path",
        flow=(WorkflowStep("you", "kit", "Select action."), WorkflowStep("kit", "kit", "Check state."),
              WorkflowStep("kit", "you", "Show result.")),
    )
    monkeypatch.setattr(workflow_modes, "WORKFLOW_MODES", (*original, extra))
    result = build_site(ROOT, output_dir=tmp_path / "good", build_commit="a" * 40)
    assert result.ok, result.report.blockers
    assert (tmp_path / "good/static/mode-test-extra.svg").is_file()
    monkeypatch.setattr(workflow_modes, "WORKFLOW_MODES", (*original, replace(extra, flow=())))
    result = build_site(ROOT, output_dir=tmp_path / "bad", build_commit="a" * 40)
    assert not result.ok
    assert any("workflow diagram requires complete manifest-backed mode: test-extra" in err
               for err in result.report.blockers)


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
    assert [mode["role"] for mode in projection["modes"]] == ["primary", "cost_saving", "emergency", "optional"]
    page = (built_site / "workflows/index.html").read_text(encoding="utf-8")
    assert 'id="mode-remote"' not in page
    assert "In the GUI, Remote covers the GitHub pull request and CI steps." in page
    assert facts["executors"] == [{"name": row["name"], "path": row["path"]} for row in executors]
    assert facts["modes"] == [row["title"] for row in projection["modes"]]
    for mode, names in facts["mode_tools"].items():
        assert names == [row["name"] for row in executors if mode in row["path"].split(" or ")]
    assert all(row["name"] in _svg(built_site, "path-chooser")[0] for row in executors)
    assert facts["branches"] == [["Agent Direct"], ["File Transfer", "Copy and Paste"], ["GUI"]]
    for narrow in (False, True):
        _, svg = _svg(built_site, "path-chooser", narrow)
        roles = [node.text for node in svg.iter("{http://www.w3.org/2000/svg}text") if node.get("class") == "role"]
        assert roles == ["Primary", "Cost-saving", "Emergency only", "Optional"]


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
    assert "Runs agentic-kit check" in facts["ci_summary"]
    assert "agentic-kit check" in facts["manifest_commands"]
    assert "Runs project tests" in facts["ci_summary"]


def test_role_figure_blocks_when_ci_drops_the_kit_check() -> None:
    ci = "on: {push: {}, pull_request: {}}\njobs: {test: {steps: [{run: pytest}]}}"
    with pytest.raises(ValueError, match="generated CI no longer runs agentic-kit check"):
        collect_role_figure_facts(ROOT, {}, ({}, [], ci))


@pytest.mark.parametrize("narrow", [False, True])
def test_control_levels_show_meaning_and_increasing_card_heights(built_site: Path, narrow: bool) -> None:
    source, svg = _svg(built_site, "asked-checked-enforced", narrow)
    assert not re.search(r"\b(?:pip|then|fi)\b|if \[|--upgrade", source)
    namespace = "{http://www.w3.org/2000/svg}"
    labels = [node.text for node in svg.iter(namespace + "text")]
    assert "Runs on: push, pull request" in labels
    assert "Runs project tests" in labels
    assert "Runs agentic-kit check" in labels
    assert "STANDARD_AGENT_PROMPT.md" in labels
    cards = [node for node in svg.iter(namespace + "rect") if node.get("rx") == "10"]
    heights = [int(card.attrib["height"]) for card in cards]
    assert len(heights) == 3 and heights[0] < heights[1] < heights[2]
    if not narrow:
        assert len({int(card.attrib["y"]) + int(card.attrib["height"]) for card in cards}) == 1


@pytest.mark.parametrize("narrow", [False, True])
def test_repository_arrows_and_second_session_are_readable(built_site: Path, narrow: bool) -> None:
    _, svg = _svg(built_site, "repository-memory", narrow)
    namespace = "{http://www.w3.org/2000/svg}"
    labels = [node.text for node in svg.iter(namespace + "text")]
    content = yaml.safe_load((ROOT / "site/content/role_figures.yaml").read_text(encoding="utf-8"))
    arrow_labels = content["figures"]["repository-memory"]["arrow_labels"]
    assert all(label in labels for label in arrow_labels.values())
    index = labels.index("Session 2")
    action = _facts(svg)["second_session_action"]
    example = yaml.safe_load((ROOT / "site/content/usage_example.yaml").read_text(encoding="utf-8"))
    assert action == next(step["agent"] for step in example["steps"] if str(step["session"]) == "2")
    displayed_action = " ".join(labels[index + 1:index + 3]).rstrip("…")
    assert action == displayed_action or action.startswith(displayed_action + " ")
    assert "Reads" in labels[index + 1]
    assert "package is local" in " ".join(labels)
    assert "another machine" in " ".join(labels)
    repository = labels[labels.index("Repository files") + 1:labels.index(arrow_labels["writes"])]
    names: list[str] = []
    for line in repository:
        if names and names[-1].endswith(("/", "_", "-")):
            names[-1] += line
        else:
            names.append(line)
    assert names == _facts(svg)["shown_files"]
    assert len(list(svg.iter(namespace + "path"))) == 2


def test_ci_summary_omits_project_tests_when_ci_does_not_run_them() -> None:
    ci = "on: {push: {}, pull_request: {}}\njobs: {test: {steps: [{run: agentic-kit check}]}}"
    _, summary = _ci_summary(ci)
    assert summary == ["Runs on: push, pull request", "Runs agentic-kit check"]


@pytest.mark.parametrize("job, step", [
    ("continue-on-error: true, ", ""),
    ("", "continue-on-error: true, "),
    ("if: false, ", ""),
    ("", "if: false, "),
])
def test_ci_summary_blocks_checks_that_do_not_enforce_the_result(job: str, step: str) -> None:
    ci = "on: {push: {}, pull_request: {}}\njobs: {test: {" + job + "steps: [{" + step + "run: agentic-kit check}]}}"
    with pytest.raises(ValueError, match="conditional or allows failure"):
        _ci_summary(ci)



def test_file_labels_wrap_at_separators_without_breaking_words() -> None:
    assert _lines(["STANDARD_AGENT_PROMPT.md"], 14) == ["STANDARD_", "AGENT_", "PROMPT.md"]
    assert _lines(["Extraordinary filename"], 12) == ["Extraordinary", "filename"]




def test_unpublished_figures_are_not_embedded(built_site: Path) -> None:
    content = yaml.safe_load((ROOT / "site/content/role_figures.yaml").read_text(encoding="utf-8"))
    assert content["figures"]["background-and-ownership"]["published"] is False
    assert content["figures"]["kit-conductor"]["published"] is False
    pages = " ".join(path.read_text(encoding="utf-8") for path in built_site.rglob("*.html"))
    assert "background-and-ownership.svg" not in pages
    assert "kit-conductor.svg" not in pages
