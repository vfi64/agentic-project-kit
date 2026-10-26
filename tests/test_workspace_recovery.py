"""External bootstrap safety and gate isolation, including real local commits."""
import json
from pathlib import Path
import subprocess

import pytest
import yaml
from typer.testing import CliRunner

from agentic_project_kit.cli import app
from agentic_project_kit.cli_commands import human_workflows
from agentic_project_kit.rule_source_validator import validate_rule_sources
from agentic_project_kit.standard_gates_audit_suite import _standard_gate_commands_for_root
from agentic_project_kit.workspace_recovery import recover_workspace
from agentic_project_kit.dpa_workspace_init_projection import render_workspace_init_projection_manifest, DPA_WORKSPACE_INIT_MANIFEST_PATH


def git(root: Path, *args: str) -> str:
    result = subprocess.run(["git", *args], cwd=root, capture_output=True, text=True, check=True)
    return result.stdout.strip()


@pytest.fixture
def partial(tmp_path):
    git(tmp_path, "init", "-b", "work")
    git(tmp_path, "config", "user.name", "Fixture")
    git(tmp_path, "config", "user.email", "fixture@example.invalid")
    git(tmp_path, "commit", "--allow-empty", "-m", "fixture")
    path = tmp_path / ".agentic/project.yaml"
    path.parent.mkdir()
    path.write_text(yaml.safe_dump({
        "version": 1, "project": {"name": "swift-demo", "description": "Swift fixture", "type": "generic"},
        "profiles": ["generic-git-repo"], "policy_packs": ["solo-maintainer"], "governance": {},
    }))
    (tmp_path / ".agentic/todo.yaml").write_text("items: []\n")
    return tmp_path


def snapshot(root):
    return {p.relative_to(root).as_posix(): p.read_bytes() for p in root.rglob("*")
            if p.is_file() and ".git" not in p.relative_to(root).parts}


def execute(root, plan=None):
    plan = plan or recover_workspace(root)
    return recover_workspace(root, execute=True, expected_signature=plan["approval_signature"],
                             approved_by="maintainer", consent_source="fixture consent")


def test_empty_repository_normal_init_still_works(tmp_path):
    preview = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--type", "generic", "--json"])
    assert preview.exit_code == 0 and not list(tmp_path.iterdir())
    result = CliRunner().invoke(app, ["workspace", "init", "--root", str(tmp_path), "--type", "generic", "--execute", "--json"])
    assert result.exit_code == 0
    assert validate_rule_sources(tmp_path).is_valid


def test_recovery_is_additive_signed_and_idempotent(partial):
    document = partial / "docs/planning/PLAN.md"
    document.parent.mkdir(parents=True)
    document.write_text("owner planning and evidence\n")
    before = snapshot(partial)
    plan = recover_workspace(partial)
    assert plan["result_status"] == "AWAITING_APPROVAL"
    assert snapshot(partial) == before
    assert ".agentic/config.yaml" in plan["changed_paths"]
    assert ".agentic/project.yaml" in plan["preserved_paths"]
    result = execute(partial, plan)
    assert result["result_status"] == "PASS", result
    assert all((partial / p).read_bytes() == content for p, content in before.items())
    after = snapshot(partial)
    assert recover_workspace(partial)["result_status"] == "PASS"
    assert recover_workspace(partial, execute=True)["written"] is False
    assert snapshot(partial) == after
    assert validate_rule_sources(partial).is_valid


@pytest.mark.parametrize("case", ["unknown", "unknown-directory", "symlink", "bad-project", "conflicting-seed", "bad-todo"])
def test_ambiguous_or_invalid_partial_blocks_without_writes(partial, case):
    if case == "unknown":
        (partial / ".agentic/private.yaml").write_text("private: data\n")
    elif case == "unknown-directory":
        (partial / ".agentic/unknown").mkdir()
    elif case == "symlink":
        (partial / ".agentic/rules").symlink_to(partial / "elsewhere", target_is_directory=True)
    elif case == "bad-project":
        (partial / ".agentic/project.yaml").write_text("version: 999\n")
    elif case == "bad-todo":
        (partial / ".agentic/todo.yaml").write_text("items: broken\n")
    else:
        (partial / ".agentic/rules").mkdir()
        (partial / ".agentic/rules/README.md").write_text("owner rules must survive\n")
    # The symlink may be dangling, so snapshot only regular non-symlink files.
    before = {p: b for p, b in snapshot(partial).items()}
    result = recover_workspace(partial)
    assert result["result_status"] == "BLOCKED", result
    assert snapshot(partial) == before


def test_missing_or_stale_consent_does_not_mutate(partial):
    plan = recover_workspace(partial)
    before = snapshot(partial)
    result = recover_workspace(partial, execute=True, expected_signature=plan["approval_signature"])
    assert result["result_status"] == "BLOCKED"
    assert snapshot(partial) == before
    (partial / ".agentic/todo.yaml").write_text("items: []\n# reviewed later\n")
    before = snapshot(partial)
    assert execute(partial, plan)["result_status"] == "BLOCKED"
    assert snapshot(partial) == before


def test_invalid_full_workspace_is_not_reset(partial):
    assert execute(partial)["result_status"] == "PASS"
    (partial / ".agentic/config.yaml").write_text("kit_schema_version: 999\n")
    before = snapshot(partial)
    assert recover_workspace(partial)["result_status"] == "BLOCKED"
    assert snapshot(partial) == before
    assert validate_rule_sources(partial).fail_closed


def test_historical_generator_provenance_is_preserved_and_disclosed(partial):
    path = partial / DPA_WORKSPACE_INIT_MANIFEST_PATH
    path.parent.mkdir(parents=True)
    path.write_text(render_workspace_init_projection_manifest(
        project_name="old-fixture-name", project_type="generic", profile=None,
        generated_target_paths=(".agentic/project.yaml",), emits_current_handoff_template=False,
    ))
    before = path.read_bytes()
    plan = recover_workspace(partial)
    assert plan["warnings"] and DPA_WORKSPACE_INIT_MANIFEST_PATH in plan["preserved_paths"]
    assert execute(partial, plan)["result_status"] == "PASS"
    assert path.read_bytes() == before


def test_partial_work_check_never_runs_kit_tests(partial, monkeypatch):
    monkeypatch.chdir(partial)
    def forbidden(*args, **kwargs):
        pytest.fail("partial bootstrap must stop before any subprocess gate")
    monkeypatch.setattr(human_workflows, "_run_step", forbidden)
    result = CliRunner().invoke(app, ["work", "check", "--json"])
    assert result.exit_code == 2
    payload = json.loads(result.stdout)
    assert payload["blockers"] == ["workspace-bootstrap-required"]
    assert "tests/test_" not in result.stdout
    assert _standard_gate_commands_for_root(partial) == (("work", "check", "--profile", "minimal", "--json"),)
    assert validate_rule_sources(partial).workspace_mode == "partial_external_workspace"


def test_complete_generic_workspace_gate_preserves_project_checks(partial, monkeypatch):
    assert execute(partial)["result_status"] == "PASS"
    monkeypatch.chdir(partial)
    calls = []
    def gate(name, argv, **kwargs):
        calls.append(name)
        return {"name": name, "ok": name != "check", "returncode": 1 if name == "check" else 0}
    monkeypatch.setattr(human_workflows, "_run_step", gate)
    result = CliRunner().invoke(app, ["work", "check", "--json"])
    assert result.exit_code == 2
    assert calls == ["repo-status", "check", "governance-check", "doctor", "standard-gates-audit-suite"]
    assert "check" in json.loads(result.stdout)["blockers"]
    assert not (partial / "tests").exists()


def test_real_rules_ack_and_commit_refuse_invalid_then_accept_valid(partial, monkeypatch):
    assert execute(partial)["result_status"] == "PASS"
    monkeypatch.chdir(partial)
    runner = CliRunner()
    (partial / "work.txt").write_text("reviewed work\n")
    source = partial / ".agentic/registries/rules.yaml"
    good = source.read_bytes()
    source.write_text("rules: [\n")
    refused_ack = runner.invoke(app, ["rules", "acknowledge", "--json"])
    assert refused_ack.exit_code != 0
    assert not (partial / ".agentic/rule_ack/current.json").exists()
    before = git(partial, "rev-parse", "HEAD")
    rejected = runner.invoke(app, ["transfer", "commit", "--message", "work", "--path", "work.txt", "--json"])
    assert rejected.exit_code != 0 and "rule_snapshot_fail_closed" in rejected.stdout
    assert git(partial, "rev-parse", "HEAD") == before
    source.write_bytes(good)
    ack = runner.invoke(app, ["rules", "acknowledge"])
    assert ack.exit_code == 0, ack.output
    accepted = runner.invoke(app, ["transfer", "commit", "--message", "work", "--path", "work.txt", "--json"])
    assert accepted.exit_code == 0, accepted.output
    assert git(partial, "rev-parse", "HEAD") != before


def test_project_declared_document_gate_remains_enforced(partial, monkeypatch):
    assert execute(partial)["result_status"] == "PASS"
    (partial / "sentinel.yaml").write_text("documents:\n  - path: REQUIRED_PROJECT_FILE.md\n")
    monkeypatch.chdir(partial)
    result = CliRunner().invoke(app, ["check", "--json"])
    assert result.exit_code != 0
    assert "REQUIRED_PROJECT_FILE.md" in result.stdout


def test_partial_reference_check_never_invokes_pytest(partial, monkeypatch):
    monkeypatch.chdir(partial)
    result = CliRunner().invoke(app, ["transfer", "command-reference-check", "--json"])
    assert result.exit_code != 0
    assert "workspace-bootstrap-required" in result.stdout
    assert "pytest" not in result.stdout


def test_cli_recovery_plan_and_execution(partial):
    runner = CliRunner()
    args = ["workspace", "init", "--root", str(partial), "--recover-partial", "--json"]
    plan = runner.invoke(app, args)
    assert plan.exit_code == 0, plan.output
    signature = json.loads(plan.stdout)["approval_signature"]
    result = runner.invoke(app, [*args, "--execute", "--expected-signature", signature,
                                 "--approved-by", "owner", "--consent-source", "test"])
    assert result.exit_code == 0, result.output
    assert json.loads(result.stdout)["result_status"] == "PASS"
