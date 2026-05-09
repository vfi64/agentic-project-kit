from pathlib import Path

from agentic_project_kit.models import ProjectOptions
from agentic_project_kit.templates import create_project


def test_create_project_generates_core_files(tmp_path: Path):
    target = tmp_path / "demo"
    create_project(
        ProjectOptions(
            name="demo",
            description="Demo project",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    assert (target / "README.md").exists()
    assert (target / "AGENTS.md").exists()
    assert (target / "docs/PROJECT_START.md").exists()
    assert (target / ".agentic/todo.yaml").exists()
    assert (target / ".github/workflows/ci.yml").exists()
