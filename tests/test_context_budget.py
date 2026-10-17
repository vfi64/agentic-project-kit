"""Context budget baseline and task-specific packets (plan context-budgeted-handoff-projections)."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path

import pytest
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.context_budget import (
    PACKET_DIR,
    PROFILES,
    SUCCESSOR_REQUIRED_READS,
    context_report,
    render_packet,
)

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_required_reads_are_named_by_the_kit_authorities() -> None:
    authority_text = "\n".join(
        (REPO_ROOT / path).read_text(encoding="utf-8")
        for path in (
            "docs/handoff/START_NEW_CHAT_PROMPT.md",
            "docs/reports/handoff-packages/latest/successor_prompt.md",
            "AGENTS.md",
        )
    )
    for path, _source in SUCCESSOR_REQUIRED_READS:
        assert Path(path).name in authority_text, path


@pytest.mark.parametrize("profile", sorted(PROFILES))
def test_packets_are_deterministic_and_carry_the_current_ack(profile: str) -> None:
    manifest = json.loads((REPO_ROOT / "docs/reference/agentic-kit-commands.json").read_text(encoding="utf-8"))
    first = render_packet(REPO_ROOT, profile)

    assert first == render_packet(REPO_ROOT, profile)
    assert f"COMMAND_MANIFEST_ACK {manifest['meta']['manifest_sha']}" in first
    for command in PROFILES[profile]["commands"]:
        assert f"`{command}`" in first
    for path, _source in SUCCESSOR_REQUIRED_READS:
        assert f"`{path}`" in first


def test_packet_quotes_every_execution_contract_rule() -> None:
    contract = json.loads(
        (REPO_ROOT / "docs/reports/handoff-packages/latest/execution_contract.json").read_text(encoding="utf-8")
    )
    packet = render_packet(REPO_ROOT, "slice")

    for rule in contract["rules"]:
        assert f"`{rule['rule_id']}`" in packet
        for item in rule.get("must") or []:
            assert item in packet


def test_report_measures_the_baseline_and_each_packet() -> None:
    report = context_report(REPO_ROOT)
    baseline = report["baseline_successor_required_reads"]

    assert baseline["missing"] == []
    assert baseline["file_count"] == len(SUCCESSOR_REQUIRED_READS)
    assert set(report["packets"]) == set(PROFILES)
    for packet in report["packets"].values():
        assert 0 < packet["estimated_tokens"] < baseline["estimated_tokens"]


def test_unknown_profile_is_refused() -> None:
    result = CliRunner().invoke(app, ["context", "render", "--profile", "nope"])

    assert result.exit_code == 2
    assert "unknown context profile" in result.output


def test_render_write_goes_to_the_ignored_context_directory(tmp_path: Path) -> None:
    root = tmp_path / "repo"
    for rel in [path for path, _ in SUCCESSOR_REQUIRED_READS] + ["docs/planning/PROJECT_DIRECTION.yaml"]:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(REPO_ROOT / rel, target)
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)

    result = CliRunner().invoke(app, ["context", "render", "--profile", "handoff", "--root", str(root), "--write"])

    assert result.exit_code == 0, result.output
    written = root / PACKET_DIR / "handoff.md"
    assert written.read_text(encoding="utf-8") + "\n" == result.output
    completed = subprocess.run(
        ["git", "check-ignore", "-q", (PACKET_DIR / "handoff.md").as_posix()], cwd=REPO_ROOT, check=False
    )
    assert completed.returncode == 0


def test_context_report_cli_json() -> None:
    result = CliRunner().invoke(app, ["context", "report", "--root", str(REPO_ROOT), "--json"])

    assert result.exit_code == 0, result.output
    assert json.loads(result.output)["kind"] == "context_budget_report"
