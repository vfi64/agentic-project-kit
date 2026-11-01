"""External projection v2 must be a pure function of captured inputs."""

from dataclasses import fields, replace
import json
from pathlib import Path
import subprocess
import socket

import pytest


@pytest.fixture(autouse=True)
def active_release_b(monkeypatch):
    from agentic_project_kit import external_projection_policy
    monkeypatch.setattr(external_projection_policy, "EXTERNAL_PROJECTION_V2_ACTIVE", True)


def test_projection_renderer_is_pure_and_byte_stable(monkeypatch):
    from agentic_project_kit.external_handoff_projection import ProjectionInputs, render_projection

    inputs = ProjectionInputs(
        sources=((".agentic/config.yaml", b"kit_schema_version: 2\n"),),
        package_version="1.1.10",
        generator_version=2,
        repository_name="example/project",
        package_root=".agentic/state/handoff/packages/latest",
        handoff_root=".agentic/state/handoff",
        execution_contract='{"kind":"successor_execution_contract","rules":[]}',
    )

    def forbidden(*args, **kwargs):
        raise AssertionError("renderer attempted external access")

    monkeypatch.setattr("builtins.open", forbidden)
    monkeypatch.setattr(Path, "read_text", forbidden)
    monkeypatch.setattr(Path, "read_bytes", forbidden)
    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(subprocess, "Popen", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    first = render_projection(inputs)
    assert first == render_projection(inputs)
    forbidden_fields = {
        "head", "origin_main", "branch", "head_matches_origin_main", "worktree_clean",
        "generated_at_utc", "generated_head",
    }

    def inspect(value):
        if isinstance(value, dict):
            assert not (set(value) & forbidden_fields)
            assert not any(key.endswith("_short") for key in value)
            for item in value.values():
                inspect(item)
        elif isinstance(value, list):
            for item in value:
                inspect(item)

    for path, content in first.items():
        if path.endswith((".json", ".yaml")):
            inspect(json.loads(content))


def test_every_input_field_affects_digest():
    from agentic_project_kit.external_handoff_projection import ProjectionInputs, input_digest

    inputs = ProjectionInputs((("a", b"one"),), "1.1.10", 2, "example/project", "p", "h", "{}")
    for field in fields(inputs):
        current = getattr(inputs, field.name)
        changed = (
            (("a", b"two"),) if field.name == "sources"
            else (*current, "another-path") if isinstance(current, tuple)
            else current + 1 if isinstance(current, int)
            else current + "changed"
        )
        assert input_digest(inputs) != input_digest(replace(inputs, **{field.name: changed})), field.name


@pytest.mark.parametrize("version,run_id,validator,expected", [
    (2, "new-run", "PASS", "PASS"),
    (99, "new-run", "PASS", "BLOCKED"),
    (2, "", "PASS", "FAIL"),
    (2, "new-run", "FAIL", "FAIL"),
])
def test_runtime_consumer_fails_closed(version, run_id, validator, expected):
    from agentic_project_kit.external_handoff_projection import validate_runtime_identity

    assert validate_runtime_identity({
        "schema_version": 1, "projection_contract_version": version,
        "run_id": run_id, "generated_head": "a" * 40, "head": "a" * 40,
        "freshness": validator, "integrity": validator, "validator_status": validator,
        "input_digest": "b" * 64,
    }, expected_head="a" * 40) == expected


@pytest.mark.parametrize("mutation,code", [
    ("content", "projection_integrity_mismatch"),
    ("missing_digest", "projection_digest_invalid"),
    ("version", "projection_contract_unknown"),
    ("stale", "projection_inputs_changed"),
    ("v1", "NEEDS_PROJECTION_MIGRATION"),
    ("minimum", "projection_minimum_violation"),
])
def test_projection_comparison_fails_closed(mutation, code):
    from agentic_project_kit.external_handoff_projection import (
        ProjectionInputs, compare_projection, render_projection,
    )

    inputs = ProjectionInputs((("a", b"one"),), "1.1.10", 2, "example/project", "p", "h", "{}")
    stored = render_projection(inputs)
    report_path = "p/validation_report.json"
    report = json.loads(stored[report_path])
    minimum = 2
    if mutation == "content":
        stored["p/successor_prompt.md"] += b"tampered"
    elif mutation == "missing_digest":
        del report["input_digest"]
    elif mutation == "version":
        report["projection_contract_version"] = 99
    elif mutation == "stale":
        inputs = replace(inputs, sources=(("a", b"two"),))
    elif mutation == "v1":
        report = {"status": "PASS", "generated_head": "a" * 40}
        minimum = None
    elif mutation == "minimum":
        minimum = 1
    stored[report_path] = (json.dumps(report, sort_keys=True, indent=2) + "\n").encode()
    result = compare_projection(inputs, stored, minimum=minimum)
    assert result["status"] != "PASS"
    assert result["code"] == code
    if mutation == "stale":
        assert "file:a" in result["changed_inputs"]


def test_exact_projection_bytes_pass():
    from agentic_project_kit.external_handoff_projection import (
        ProjectionInputs, compare_projection, render_projection,
    )

    inputs = ProjectionInputs((("a", None),), "1.1.10", 2, "example/project", "p", "h", "{}")
    assert compare_projection(inputs, render_projection(inputs), minimum=2)["status"] == "PASS"


def test_collector_has_no_process_access_and_captures_source_bytes(tmp_path, monkeypatch):
    from agentic_project_kit.external_handoff_projection import collect_projection_inputs

    _external_workspace(tmp_path)
    config = tmp_path / ".agentic/config.yaml"

    def forbidden(*args, **kwargs):
        raise AssertionError("input collection must not launch processes")

    monkeypatch.setattr(subprocess, "run", forbidden)
    inputs = collect_projection_inputs(tmp_path)
    assert dict(inputs.sources)[".agentic/config.yaml"] == config.read_bytes()
    assert dict(inputs.sources)["docs/planning/PROJECT_DIRECTION.yaml"] is None
    contract = json.loads(inputs.execution_contract)
    assert contract["handoff_projection_contract"]["dpa_generated_output_contract"]["contract_id"].endswith("-v2")
    assert len(contract["rules"]) >= 14


@pytest.mark.parametrize("minimum", [2, 1, 99])
def test_manifest_projection_minimum_is_independent(tmp_path, minimum):
    from agentic_project_kit.workspace import load_workspace

    config = tmp_path / ".agentic/config.yaml"
    config.parent.mkdir()
    config.write_text(f"kit_schema_version: 1\nhandoff: {{projection_contract_min: {minimum}}}\n")
    assert load_workspace(tmp_path).handoff_projection_contract_min == minimum


def test_manifest_rejects_unknown_handoff_keys(tmp_path):
    from agentic_project_kit.workspace import load_workspace

    config = tmp_path / ".agentic/config.yaml"
    config.parent.mkdir()
    config.write_text("kit_schema_version: 1\nhandoff: {disable_validation: true}\n")
    with pytest.raises(RuntimeError, match="unknown handoff key"):
        load_workspace(tmp_path)


def _external_workspace(root):
    from agentic_project_kit.successor_handoff_package import _external_long_term_sources
    from agentic_project_kit.workspace import load_workspace

    config = root / ".agentic/config.yaml"
    config.parent.mkdir(parents=True)
    config.write_text("kit_schema_version: 1\nproject: {name: external-demo, type: generic}\n")
    ws = load_workspace(root)
    for relative in _external_long_term_sources(ws):
        path = root / relative
        if path.exists():
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("version: 1\n" if path.suffix == ".yaml" else "# Workspace authority\n")
    ws.status_path().write_text("# Workspace Status\n")
    ws.handoff_file("README.md").write_text("# Workspace Handoff\n")
    for args in [
        ["init", "-b", "main"], ["config", "user.email", "fixture@example.invalid"],
        ["config", "user.name", "Fixture"], ["add", "."], ["commit", "-m", "Initial"],
    ]:
        subprocess.run(["git", *args], cwd=root, check=True, capture_output=True)
    return ws


def test_generated_external_projection_is_stable_and_runtime_is_separate(tmp_path):
    from agentic_project_kit.external_handoff_projection import check_projection, RUNTIME_PATH
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package

    ws = _external_workspace(tmp_path)
    first = write_successor_handoff_package(tmp_path)
    paths = [*ws.handoff_packages_latest().glob("*"), *ws.handoff_dir().glob("*.md")]
    before = {path: path.read_bytes() for path in paths}
    identity = json.loads((tmp_path / RUNTIME_PATH).read_bytes())
    second = write_successor_handoff_package(tmp_path)
    assert before == {path: path.read_bytes() for path in paths}
    assert "generated_head" not in first.validation_report
    assert first.validation_report == second.validation_report
    assert check_projection(tmp_path)["status"] == "PASS"
    newer = json.loads((tmp_path / RUNTIME_PATH).read_bytes())
    assert newer["run_id"] != identity["run_id"]
    assert newer["generated_head"] == subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=tmp_path, text=True).strip()
    assert subprocess.run(["git", "check-ignore", RUNTIME_PATH], cwd=tmp_path, capture_output=True).returncode == 0


def test_projection_check_is_read_only_on_pass_and_failure(tmp_path, monkeypatch):
    from agentic_project_kit.external_handoff_projection import check_projection
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package

    _external_workspace(tmp_path)
    write_successor_handoff_package(tmp_path)

    def snapshot():
        return {path.relative_to(tmp_path).as_posix(): path.read_bytes()
                for path in tmp_path.rglob("*") if path.is_file()}

    def forbidden(*args, **kwargs):
        raise AssertionError("read-only projection check attempted an external action")

    monkeypatch.setattr(subprocess, "run", forbidden)
    monkeypatch.setattr(socket, "socket", forbidden)
    before = snapshot()
    assert check_projection(tmp_path)["status"] == "PASS"
    assert snapshot() == before
    (tmp_path / ".agentic/state/status.md").write_text("Changed authority\n")
    before = snapshot()
    assert check_projection(tmp_path)["code"] == "projection_inputs_changed"
    assert snapshot() == before


def test_external_check_and_freshness_reject_stale_inputs(tmp_path):
    from agentic_project_kit.checks import check_all
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
    from agentic_project_kit.transfer_repo_actions import _successor_package_freshness_check

    _external_workspace(tmp_path)
    write_successor_handoff_package(tmp_path)
    assert not _successor_package_freshness_check(tmp_path).findings
    (tmp_path / ".agentic/state/status.md").write_text("Changed authority\n")
    assert any("projection_inputs_changed" in error for error in check_all(tmp_path))
    assert any("projection_inputs_changed" in error for error in _successor_package_freshness_check(tmp_path).findings)


def test_external_squash_merge_needs_no_refresh(tmp_path, monkeypatch):
    from agentic_project_kit.checks import check_all
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
    from agentic_project_kit.transfer_repo_actions import post_merge_check

    root = tmp_path / "workspace"
    root.mkdir()
    _external_workspace(root)

    def git(*args, cwd=root):
        return subprocess.check_output(["git", *args], cwd=cwd, text=True, stderr=subprocess.STDOUT).strip()

    origin = tmp_path / "origin.git"
    git("init", "--bare", str(origin))
    git("remote", "add", "origin", str(origin))
    write_successor_handoff_package(root)
    git("add", ".")
    git("commit", "-m", "Migrate external projection")
    git("push", "-u", "origin", "main")
    assert check_all(root) == []
    monkeypatch.chdir(root)
    git("switch", "-c", "product")
    (root / "product.txt").write_text("Product work\n")
    git("add", "product.txt")
    git("commit", "-m", "Product change")
    git("switch", "main")
    git("merge", "--squash", "product")
    git("commit", "-m", "Squash product")
    git("push", "origin", "main")
    result = post_merge_check()
    assert result.result_status == "PASS", result
    assert "STATE=READY" in result.next_action
    assert "refresh_required=False" in result.stdout
    git("switch", "-c", "authority")
    (root / ".agentic/state/status.md").write_text("# Workspace Status\nNew authority\n")
    assert any("projection_inputs_changed" in error for error in check_all(root))
    write_successor_handoff_package(root)
    assert check_all(root) == []
    git("add", ".")
    git("commit", "-m", "Regenerate changed authority")
    git("switch", "main")
    git("merge", "--squash", "authority")
    git("commit", "-m", "Squash authority")
    git("push", "origin", "main")
    result = post_merge_check()
    assert result.result_status == "PASS", result
    assert "refresh_required=False" in result.stdout


def test_migration_state_uses_existing_governed_refresh_route():
    from agentic_project_kit.transfer_post_merge_state import post_merge_state
    from agentic_project_kit.transfer_post_merge_lifecycle import _refresh_plan_for_state
    from agentic_project_kit.transfer_post_merge_settle import _refresh_factory
    from agentic_project_kit.transfer_repo_actions import RepoActionResult

    result = RepoActionResult("post-merge-check", "FAIL", 2, [], "", "", "STATE=NEEDS_PROJECTION_MIGRATION")
    assert post_merge_state(result) == "NEEDS_PROJECTION_MIGRATION"
    assert _refresh_plan_for_state("NEEDS_PROJECTION_MIGRATION", main_branch="main") is not None
    assert _refresh_factory(state="NEEDS_PROJECTION_MIGRATION", main_branch="main") is not None


def test_external_read_only_cli_does_not_write_enabled_invocation_ledger(tmp_path, monkeypatch):
    from agentic_project_kit.cli import app
    from agentic_project_kit.invocation_ledger import run_cli, ledger_path

    _external_workspace(tmp_path)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTIC_KIT_INVOCATION_LEDGER", "1")
    assert run_cli(lambda: "checked", app, ["check"]) == "checked"
    assert not ledger_path(tmp_path).exists()


def test_external_audit_and_lifecycle_report_content_validation(tmp_path):
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
    from agentic_project_kit.status_current_state_audit import audit_status_current_state
    from agentic_project_kit.doc_lifecycle import _load_handoff_context

    _external_workspace(tmp_path)
    write_successor_handoff_package(tmp_path)
    audit = audit_status_current_state(tmp_path).as_dict()
    assert audit["status"] == "PASS"
    assert audit["input_digest"]
    assert "validation_generated_head" not in audit
    context = _load_handoff_context(tmp_path)
    assert context["safe_to_continue"] is True
    assert context["input_digest"] == audit["input_digest"]
    assert "generated_head" not in context


def test_external_patch_cycle_uses_content_freshness(tmp_path):
    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package
    from agentic_project_kit.patch_cycle_workflow import build_patch_cycle_status

    _external_workspace(tmp_path)
    write_successor_handoff_package(tmp_path)
    for args in [["add", "."], ["commit", "-m", "Projection"], ["update-ref", "refs/remotes/origin/main", "HEAD"]]:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    status = build_patch_cycle_status(tmp_path)
    assert status.handoff_fresh_for_head is True
    assert "handoff_generated_head" not in status.as_dict()
    (tmp_path / ".agentic/state/status.md").write_text("# Workspace Status\nChanged\n")
    for args in [["add", "."], ["commit", "-m", "Stale authority"], ["update-ref", "refs/remotes/origin/main", "HEAD"]]:
        subprocess.run(["git", *args], cwd=tmp_path, check=True, capture_output=True)
    stale = build_patch_cycle_status(tmp_path)
    assert stale.handoff_fresh_for_head is False
    assert "handoff_generated_head_mismatch" not in str(stale.as_dict())


def test_v2_preserves_security_rules_and_historical_v1_identity(tmp_path):
    from agentic_project_kit.dpa_successor_projection import DPA_SUCCESSOR_PROJECTION_CONTRACT_ID
    from agentic_project_kit.external_handoff_projection import collect_projection_inputs, render_projection
    from agentic_project_kit.successor_handoff_package import build_execution_contract

    ws = _external_workspace(tmp_path)
    before = build_execution_contract({"repo": {"full_name": "external-demo", "local_path": "cd /path/to/"}}, ws)
    inputs = collect_projection_inputs(tmp_path)
    after = json.loads(inputs.execution_contract)
    allowed_rule_changes = {"successor-final-head-identity"}
    old_rules = {rule["rule_id"]: rule for rule in before["rules"]}
    new_rules = {rule["rule_id"]: rule for rule in after["rules"]}
    assert old_rules.keys() == new_rules.keys()
    differences = {key for key in old_rules if old_rules[key] != new_rules[key]}
    assert differences == allowed_rule_changes
    assert DPA_SUCCESSOR_PROJECTION_CONTRACT_ID == "DPA-GENERATED-SUCCESSOR-HANDOFF-PROJECTION-v1"
    dpa = after["handoff_projection_contract"]["dpa_generated_output_contract"]
    assert set(dpa["default_direct_write_paths"]) == set(render_projection(inputs))
    assert dpa["dedicated_update_only_paths"] == []


def test_workspace_init_plans_and_writes_current_v2_without_runtime_mutation(tmp_path):
    from agentic_project_kit.workspace_init import build_workspace_init_plan, execute_workspace_init
    from agentic_project_kit.external_handoff_projection import check_projection, RUNTIME_PATH

    plan = build_workspace_init_plan(tmp_path, name="external-demo", execute=True)
    assert ".agentic/state/handoff/packages/latest/validation_report.json" in plan.files
    assert not (tmp_path / ".agentic").exists()
    execute_workspace_init(plan)
    assert check_projection(tmp_path)["status"] == "PASS"
    assert not (tmp_path / RUNTIME_PATH).exists()


def test_packaged_command_authority_is_independent_of_synced_reference_copies(tmp_path):
    from agentic_project_kit.external_handoff_projection import collect_projection_inputs, input_digest

    _external_workspace(tmp_path)
    before = input_digest(collect_projection_inputs(tmp_path))
    reference = tmp_path / "docs/reference/agentic-kit-commands.json"
    reference.parent.mkdir(parents=True)
    reference.write_text('{"meta":{"manifest_sha":"example"}}')
    assert input_digest(collect_projection_inputs(tmp_path)) == before


@pytest.mark.parametrize("unsafe", [".gitignore", ".agentic/tmp/handoff", ".agentic/state/handoff/packages/latest"])
def test_writer_preflights_all_destinations_before_mutating(tmp_path, unsafe):
    from agentic_project_kit.external_handoff_projection import write_external_package

    root = tmp_path / "workspace"
    root.mkdir()
    _external_workspace(root)
    outside = tmp_path / "outside"
    outside.mkdir()
    destination = root / unsafe
    destination.parent.mkdir(parents=True, exist_ok=True)
    target = outside
    if unsafe == ".gitignore":
        target = outside / "ignore"
        target.write_text("original\n")
    destination.symlink_to(target)
    config = (root / ".agentic/config.yaml").read_bytes()
    with pytest.raises(ValueError, match="projection_output_unsafe"):
        write_external_package(root)
    assert (root / ".agentic/config.yaml").read_bytes() == config
    assert sorted(path.name for path in outside.iterdir()) == (["ignore"] if unsafe == ".gitignore" else [])


def test_external_post_merge_machine_contract_is_local_only_for_bound_fixture():
    from agentic_project_kit.greenfield_retest import execution_class

    retest = {"commands": ["agentic-kit transfer post-merge-check"], "workspace_kind": "external_manifest",
              "machine": {"fixture": "external_projection_v2"}}
    assert execution_class(retest)[0] == "local"
    retest["machine"]["fixture"] = "git_repository"
    assert execution_class(retest)[0] == "owner_remote"


def test_published_runtime_fixture_and_return_guide_match_routes():
    from agentic_project_kit.external_handoff_projection import validate_runtime_identity
    from agentic_project_kit.greenfield_retest import check_route

    root = Path(__file__).resolve().parents[1]
    data = json.loads((root / "docs/reference/fixtures/external-handoff-runtime-v2.json").read_bytes())
    assert validate_runtime_identity(data, expected_head=data["head"]) == "PASS"
    guide = (root / "docs/KIT_UPDATE_RETURN.md").read_text()
    for route in ("agentic-kit kit return-revert", "agentic-kit kit return-install"):
        assert route in guide
        assert check_route(route)


def test_renderer_golden_requires_explicit_generator_contract_revision():
    import hashlib
    from agentic_project_kit.external_handoff_projection import GENERATOR_VERSION, ProjectionInputs, render_projection

    inputs = ProjectionInputs((("authority", b"stable\n"),), "fixture", GENERATOR_VERSION,
                              "example/project", "package", "handoff", '{"rules":[]}')
    digest = hashlib.sha256()
    for path, content in sorted(render_projection(inputs).items()):
        digest.update(path.encode() + b"\0" + content + b"\0")
    # Renderer changes must add an explicitly versioned golden, not silently
    # invalidate projections generated by the same contract version.
    goldens = {2: "77439f784c80ce3259bf714d421d6075a256c03a21490273923c5120a64dbdb6"}
    assert digest.hexdigest() == goldens[GENERATOR_VERSION]


def test_optional_direction_tasks_are_projected_from_captured_bytes(tmp_path):
    from agentic_project_kit.external_handoff_projection import collect_projection_inputs

    ws = _external_workspace(tmp_path)
    direction = ws.project_direction_path()
    direction.parent.mkdir(parents=True, exist_ok=True)
    direction.write_text("schema_version: 1\nroadmap: []\nplans:\n- id: active-task\n  title: Continue approved work\n  status: active\n")
    inputs = collect_projection_inputs(tmp_path)
    tasks = json.loads(inputs.execution_contract)["current_state_contract"]["open_tasks"]
    assert tasks[0]["id"] == "active-task"


def test_external_documentation_audit_uses_byte_validation(tmp_path):
    from agentic_project_kit.external_handoff_projection import write_external_package
    from agentic_project_kit.external_documentation_audit import _handoff
    from agentic_project_kit.workspace import load_workspace

    ws = _external_workspace(tmp_path)
    write_external_package(tmp_path)
    assert _handoff(load_workspace(tmp_path))[0] == []
    ws.package_file("execution_contract.json").write_text("{}")
    assert "projection_integrity_mismatch" in str(_handoff(load_workspace(tmp_path))[0])
    write_external_package(tmp_path)
    ws.status_path().write_text("Changed input\n")
    assert "projection_inputs_changed" in str(_handoff(load_workspace(tmp_path))[0])


def test_bootstrap_uses_external_v2_paths_and_validates_whole_projection(tmp_path):
    from agentic_project_kit.chat_bootloader import render_next_chat_bootstrap, validate_generated_bootstrap
    from agentic_project_kit.external_handoff_projection import write_external_package

    ws = _external_workspace(tmp_path)
    write_external_package(tmp_path)
    legacy_context = tmp_path / "docs/reports/handoff-packages/latest/successor_context.yaml"
    legacy_context.parent.mkdir(parents=True)
    legacy_context.write_bytes(ws.package_file("successor_context.yaml").read_bytes())
    assert render_next_chat_bootstrap(tmp_path) == ws.handoff_file("NEXT_CHAT_BOOTSTRAP.md").read_text()
    assert validate_generated_bootstrap(root=tmp_path) == []
    ws.package_file("execution_contract.json").write_text("{}")
    assert "projection_integrity_mismatch" in str(validate_generated_bootstrap(root=tmp_path))


def test_post_merge_allows_only_existing_untracked_runtime_carriers(tmp_path):
    from agentic_project_kit.external_handoff_projection import write_external_package, external_post_merge_check

    ws = _external_workspace(tmp_path)
    write_external_package(tmp_path)
    for args in (["add", "-A"], ["commit", "-m", "V2 baseline"], ["update-ref", "refs/remotes/origin/main", "HEAD"]):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, check=True)
    for name in (".agentic/transfer/outbox/last_result.txt",
                 ".agentic/state/handoff/transfer_handoff_reports/latest-transfer-handoff-report.json"):
        path = tmp_path / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("Local runtime carrier\n")
    assert external_post_merge_check(tmp_path).result_status == "PASS"
    product = tmp_path / "unreviewed.txt"
    product.write_text("Unreviewed product work\n")
    assert "worktree_dirty" in external_post_merge_check(tmp_path).stdout
    product.unlink()
    ws.package_file("successor_prompt.md").write_text("Uncommitted durable change\n")
    assert "worktree_dirty" in external_post_merge_check(tmp_path).stdout


@pytest.mark.parametrize("tampered", [False, True])
def test_all_external_pure_routes_preserve_every_repository_byte(tmp_path, monkeypatch, tampered):
    from typer.testing import CliRunner
    from agentic_project_kit.cli import app
    from agentic_project_kit.external_handoff_projection import write_external_package
    from agentic_project_kit.invocation_ledger import run_cli

    _external_workspace(tmp_path)
    write_external_package(tmp_path)
    for args in (["add", "-A"], ["commit", "-m", "Current v2"],
                 ["update-ref", "refs/remotes/origin/main", "HEAD"]):
        subprocess.run(["git", *args], cwd=tmp_path, capture_output=True, check=True)
    if tampered:
        (tmp_path / ".agentic/state/status.md").write_text("Changed input\n")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENTIC_KIT_INVOCATION_LEDGER", "1")
    original = subprocess.run
    allowed = {"rev-parse", "status", "diff", "ls-files", "merge-base", "cat-file"}

    def guarded(argv, **options):
        assert argv[0] == "git" and argv[1] in allowed, argv
        options["env"] = {**options.get("env", __import__("os").environ), "GIT_OPTIONAL_LOCKS": "0"}
        return original(argv, **options)

    def forbidden(*args, **kwargs):
        raise AssertionError("pure route attempted network access")

    monkeypatch.setattr(subprocess, "run", guarded)
    monkeypatch.setattr(socket, "socket", forbidden)

    def snapshot():
        # Includes index, refs, ignored runtime/ledger/approval files and logs.
        return {path.relative_to(tmp_path).as_posix(): path.read_bytes()
                for path in tmp_path.rglob("*") if path.is_file()}

    for route in (["check", "--json"], ["transfer", "post-merge-check"],
                  ["audit-status-current-state", "--json"], ["doc-lifecycle-audit", "--json"],
                  ["docs-audit", "--json"]):
        before = snapshot()
        result = run_cli(lambda: CliRunner().invoke(app, route), app, route)
        assert not isinstance(result.exception, AssertionError), (route, result.exception)
        assert result.exit_code in {0, 1, 2}, (route, result.exception)
        assert snapshot() == before, route
