import json
from pathlib import Path

from agentic_project_kit.dpa_workspace_init_projection import (
    DPA_WORKSPACE_INIT_HANDOFF_TEMPLATE_PATH,
    DPA_WORKSPACE_INIT_MANIFEST_PATH,
    render_workspace_init_projection_manifest,
    validate_workspace_init_projection_manifest,
)
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
    assert (target / DPA_WORKSPACE_INIT_HANDOFF_TEMPLATE_PATH).exists()
    assert (target / DPA_WORKSPACE_INIT_MANIFEST_PATH).exists()
    assert (target / ".agentic/todo.yaml").exists()
    assert (target / ".github/workflows/ci.yml").exists()


def test_generated_project_dpa_manifest_classifies_handoff_as_external_template(
    tmp_path: Path,
) -> None:
    target = tmp_path / "demo-dpa"
    create_project(
        ProjectOptions(
            name="demo-dpa",
            description="Demo DPA project",
            project_type="python-cli",
            license_name="MIT",
            github_actions=True,
            pre_commit=True,
            agent_docs=True,
            logging_evidence=True,
            target_dir=target,
        )
    )

    data = json.loads((target / DPA_WORKSPACE_INIT_MANIFEST_PATH).read_text(encoding="utf-8"))

    assert validate_workspace_init_projection_manifest(data) == ()
    assert data["writer_id"] == "WRT-CH-005"
    assert data["target_scope"] == "EXTERNAL_WORKSPACE_INITIALIZATION_TEMPLATE"
    assert data["generated_target_paths"] == [DPA_WORKSPACE_INIT_HANDOFF_TEMPLATE_PATH]
    assert data["emits_current_handoff_template"] is True
    assert data["self_hosting_current_handoff"] is False
    assert data["kit_live_acceptance_state"] is False
    assert data["kit_conformance_claimed"] is False
    assert data["production_mutation_claimed"] is False


def test_workspace_init_dpa_manifest_rejects_paths_outside_generated_root() -> None:
    data = json.loads(
        render_workspace_init_projection_manifest(
            project_name="demo",
            project_type="python-cli",
            profile="",
            generated_target_paths=("../docs/handoff/CURRENT_HANDOFF.md",),
            emits_current_handoff_template=True,
        )
    )

    errors = validate_workspace_init_projection_manifest(data)

    assert "generated_target_paths must stay inside the generated target root" in errors

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

    evidence = (target / "docs/LOGGING_AND_EVIDENCE.md").read_text(encoding="utf-8")
    assert "Validation reports from `agentic-kit validate-output-contract --report`" in evidence
    assert "Do not auto-stage validation reports by default" in evidence
    assert (target / "docs/OUTPUT_CONTRACTS.md").exists()
    assert (target / "docs/VALIDATION_AND_REPAIR.md").exists()
    sample = target / "docs/output-contracts/default-answer.yaml"
    assert sample.exists()
    schema_path = target / "docs/schemas/validation-report.schema.json"
    repair_schema_path = target / "docs/schemas/repair-report.schema.json"
    assert schema_path.exists()
    assert repair_schema_path.exists()
    schema_text = schema_path.read_text(encoding="utf-8")
    assert "agentic-project-kit validation report" in schema_text
    assert "checked_file" in schema_text
    assert "missing_required_section" not in schema_text
    sample_text = sample.read_text(encoding="utf-8")
    assert "version: 1" in sample_text
    assert "name: default-answer" in sample_text
    assert "required_sections:" in sample_text
    assert "  - Final Answer" in sample_text
    validation = (target / "docs/VALIDATION_AND_REPAIR.md").read_text(encoding="utf-8")
    assert "Use agentic-kit validate-output-contract" in validation
    assert "docs/output-contracts/default-answer.yaml" in validation
    assert "--report validation-report.json" in validation
    assert "The JSON report contains `ok`, `contract`, `contract_version`, `checked_file`, and `findings`." in validation
    assert "Report shape:" in validation
    assert "missing_required_section" in validation
    assert "consume it without parsing human console output" in validation
    assert "docs/schemas/validation-report.schema.json" in validation
    assert "docs/schemas/repair-report.schema.json" in validation
    assert "--repair-output output.repaired.md --repair-report repair-report.json" in validation
    assert "does not create or infer the missing substantive content" in validation
    assert "machine-readable schema for this report shape" in validation
    assert "Use agentic-kit validate-sections as a lower-level check" in validation
    assert "Both commands only check required literal sections" in validation
    assert "Repair attempts must be bounded" in validation
