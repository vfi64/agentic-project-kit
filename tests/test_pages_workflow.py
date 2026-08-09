from __future__ import annotations

from pathlib import Path

import yaml


WORKFLOW = Path(".github/workflows/pages.yml")


def test_pages_workflow_builds_site_and_deploys_actions_artifact() -> None:
    data = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    assert data["name"] == "Pages"
    assert data["permissions"] == {
        "contents": "read",
        "pages": "write",
        "id-token": "write",
    }
    assert data["concurrency"]["group"] == "pages"
    assert "push" in data[True]
    assert data[True]["push"]["branches"] == ["main"]
    assert "workflow_dispatch" in data[True]

    pages_state = data["jobs"]["pages-state"]
    build = data["jobs"]["build"]
    deploy = data["jobs"]["deploy"]
    pages_state_step = pages_state["steps"][0]
    build_steps = build["steps"]
    build_runs = [step.get("run", "") for step in build_steps]
    build_uses = [step.get("uses", "") for step in build_steps]

    assert pages_state["outputs"]["deploy-ready"] == "${{ steps.pages.outputs.deploy-ready }}"
    assert pages_state_step["uses"] == "actions/github-script@v8"
    pages_state_script = pages_state_step["with"]["script"]
    assert "GET /repos/{owner}/{repo}/pages" in pages_state_script
    assert "build_type" in pages_state_script
    assert 'buildType === "workflow"' in pages_state_script
    assert "GitHub Pages is not enabled yet" in pages_state_script

    assert build["needs"] == "pages-state"
    assert 'pip install -e ".[dev]"' in "\n".join(build_runs)
    assert "python site/scripts/build.py --output site/dist --json" in build_runs
    assert "python -m pytest tests/test_site_generator.py tests/test_site_claims.py -q" in build_runs
    assert "actions/configure-pages@v5" in build_uses
    assert any(
        step.get("uses") == "actions/configure-pages@v5"
        and step.get("if") == "needs.pages-state.outputs.deploy-ready == 'true'"
        for step in build_steps
    )
    assert any(
        step.get("uses") == "actions/upload-pages-artifact@v3"
        and step.get("if") == "needs.pages-state.outputs.deploy-ready == 'true'"
        and step.get("with", {}).get("path") == "site/dist"
        for step in build_steps
    )

    assert deploy["needs"] == ["pages-state", "build"]
    assert deploy["if"] == "needs.pages-state.outputs.deploy-ready == 'true'"
    assert deploy["environment"]["name"] == "github-pages"
    assert deploy["steps"] == [
        {
            "id": "deployment",
            "uses": "actions/deploy-pages@v4",
        }
    ]
