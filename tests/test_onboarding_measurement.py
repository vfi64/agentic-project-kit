from __future__ import annotations

import json
from pathlib import Path

from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.command_manifest import manifest_sha
from agentic_project_kit.onboarding_measurement import build_onboarding_measurement
from agentic_project_kit.workspace_detection import NON_WORKSPACE_NEXT_STEP


def test_current_onboarding_measurement_passes() -> None:
    measurement = build_onboarding_measurement(Path("."))

    assert measurement.ok, measurement.as_dict()
    assert measurement.workspace_detection_next_step == NON_WORKSPACE_NEXT_STEP
    assert measurement.metrics["manifest_required_commands_present"] == len(measurement.required_commands)


def test_onboarding_measurement_reports_missing_workspace_detection_snippet(tmp_path: Path) -> None:
    root = _write_onboarding_fixture(tmp_path, onboarding_extra="")
    onboarding = root / "docs" / "ONBOARDING.md"
    onboarding.write_text(
        onboarding.read_text(encoding="utf-8").replace("agentic-kit init NAME", "agentic-kit init"),
        encoding="utf-8",
    )

    measurement = build_onboarding_measurement(root)

    assert not measurement.ok
    assert any(finding.code == "workspace-detection-snippet-missing" for finding in measurement.findings)


def test_onboarding_measure_cli_outputs_json() -> None:
    result = CliRunner().invoke(app, ["onboarding", "measure", "--json"])

    assert result.exit_code == 0
    payload = json.loads(result.output)
    assert payload["kind"] == "onboarding_measurement"
    assert payload["status"] == "PASS"
    assert "workspace_detection_next_step" in payload


def _write_onboarding_fixture(root: Path, *, onboarding_extra: str = "") -> Path:
    (root / "docs" / "reference").mkdir(parents=True)
    (root / "docs" / "guides").mkdir(parents=True)
    commands = [
        {"qualified_name": "agentic-kit init"},
        {"qualified_name": "agentic-kit workspace adopt"},
        {"qualified_name": "agentic-kit workspace init"},
        {"qualified_name": "agentic-kit check"},
        {"qualified_name": "agentic-kit doctor"},
        {"qualified_name": "agentic-kit command-for"},
    ]
    (root / "docs" / "reference" / "agentic-kit-commands.json").write_text(
        json.dumps(
            {
                "schema_version": 2,
                "kind": "agentic_kit_command_reference",
                "source": "test",
                "meta": {"schema_version": 1, "manifest_sha": manifest_sha(commands)},
                "commands": commands,
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (root / "README.md").write_text(
        "First-chat onboarding: docs/ONBOARDING.md\nagentic-kit onboarding measure\n",
        encoding="utf-8",
    )
    (root / "docs" / "guides" / "BROWNFIELD_EXTERNAL_REPO_15_MINUTES.md").write_text(
        "agentic-kit workspace init --root PATH\n",
        encoding="utf-8",
    )
    (root / "docs" / "ONBOARDING.md").write_text(
        "\n".join(
            [
                "# First-Chat Onboarding",
                "Create a new governed project with agentic-kit init NAME.",
                "Add the Kit operating layer to an existing repository with agentic-kit workspace adopt --root PATH and agentic-kit workspace init --root PATH.",
                "Work on this Kit repository with agentic-kit command-for, agentic-kit check, and agentic-kit doctor.",
                "Glossary: governed project, operating layer, command manifest, gate, handoff.",
                onboarding_extra,
            ]
        ),
        encoding="utf-8",
    )
    return root
