from __future__ import annotations

from pathlib import Path

import yaml


def test_project_description_reflects_governance_runtime_positioning() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")

    assert "Govern AI-assisted repository work" in text
    assert "Generate GitHub-ready project templates" not in text


def test_repository_workflows_enable_pip_cache() -> None:
    for workflow in (Path(".github/workflows/ci.yml"), Path(".github/workflows/release.yml")):
        data = yaml.safe_load(workflow.read_text(encoding="utf-8"))
        steps = data["jobs"][next(iter(data["jobs"]))]["steps"]
        setup_python = next(step for step in steps if step.get("uses") == "actions/setup-python@v6")

        assert setup_python["with"]["cache"] == "pip"


def test_pytest_marker_contract_stays_registered() -> None:
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    gates = Path("docs/TEST_GATES.md").read_text(encoding="utf-8")

    assert '"gui: GUI and Tkinter cockpit tests."' in text
    assert '"repo_state: tests that inspect live repository state or checked-in governance files."' in text
    assert '"slow: slower integration or lifecycle tests."' in text
    assert "tests/conftest.py" in gates
    assert "deterministic source patterns" in gates
