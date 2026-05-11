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

def test_generated_ci_uses_pypi_kit_source_by_default(tmp_path):
    from agentic_project_kit.models import ProjectOptions
    from agentic_project_kit.templates import create_project

    target = tmp_path / "demo-default"
    create_project(
        ProjectOptions(
            name="demo-default",
            description="Demo",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    ci = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "pip install agentic-project-kit" in ci
    assert "test.pypi.org" not in ci


def test_generated_ci_can_use_testpypi_kit_source(tmp_path):
    from agentic_project_kit.models import ProjectOptions
    from agentic_project_kit.templates import create_project

    target = tmp_path / "demo-testpypi"
    create_project(
        ProjectOptions(
            name="demo-testpypi",
            description="Demo",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
            kit_source="testpypi",
        )
    )

    ci = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "https://test.pypi.org/simple/" in ci
    assert "--extra-index-url https://pypi.org/simple/" in ci
    assert "agentic-project-kit" in ci


def test_generated_ci_can_skip_kit_install(tmp_path):
    from agentic_project_kit.models import ProjectOptions
    from agentic_project_kit.templates import create_project

    target = tmp_path / "demo-none"
    create_project(
        ProjectOptions(
            name="demo-none",
            description="Demo",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
            kit_source="none",
        )
    )

    ci = (target / ".github/workflows/ci.yml").read_text(encoding="utf-8")
    assert "agentic-project-kit install intentionally skipped" in ci
    assert "pip install agentic-project-kit" not in ci
    assert "test.pypi.org" not in ci


def test_generated_project_passes_documentation_and_doctor_gates(tmp_path: Path):
    from agentic_project_kit.checks import check_docs
    from agentic_project_kit.doctor import build_doctor_report

    target = tmp_path / "demo-gates"
    create_project(
        ProjectOptions(
            name="demo-gates",
            description="Demo gates",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    assert (target / "docs/architecture/ARCHITECTURE_CONTRACT.md").exists()
    assert (target / "docs/DOCUMENTATION_COVERAGE.yaml").exists()
    assert (target / "CHANGELOG.md").exists()
    assert "TODO" not in (target / "docs/STATUS.md").read_text(encoding="utf-8")
    assert "TODO" not in (target / "docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert check_docs(target) == []
    assert build_doctor_report(target).ok



def test_governance_wrapper_generates_output_contract_skeleton(tmp_path: Path):
    target = tmp_path / "demo-governance"
    create_project(
        ProjectOptions(
            name="demo-governance",
            description="Demo governance wrapper",
            project_type="governance-wrapper",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    assert (target / "docs/OUTPUT_CONTRACTS.md").exists()
    assert (target / "docs/VALIDATION_AND_REPAIR.md").exists()
    sample = target / "docs/output-contracts/default-answer.yaml"
    assert sample.exists()
    sample_text = sample.read_text(encoding="utf-8")
    assert "version: 1" in sample_text
    assert "name: default-answer" in sample_text
    assert "required_sections:" in sample_text
    assert "  - Final Answer" in sample_text
    validation = (target / "docs/VALIDATION_AND_REPAIR.md").read_text(encoding="utf-8")
    assert "Use agentic-kit validate-sections" in validation
    assert "This command only checks required literal sections" in validation
    assert "Repair attempts must be bounded" in validation
