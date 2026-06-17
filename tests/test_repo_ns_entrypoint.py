from pathlib import Path


def test_repo_ns_entrypoint_exists_and_is_executable() -> None:
    ns = Path("ns")
    assert ns.exists()
    assert ns.stat().st_mode & 0o111


def test_repo_ns_entrypoint_delegates_to_next_step() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "tools/next-step.py" in text
    assert "\"$@\"" in text
    assert ".venv/bin/python" in text


def test_repo_ns_menu_exists_and_is_executable() -> None:
    menu = Path("ns-menu")
    assert menu.exists()
    assert menu.stat().st_mode & 0o111


def test_repo_ns_menu_exposes_expected_shortcuts_without_heredocs() -> None:
    text = Path("ns-menu").read_text(encoding="utf-8")
    assert "#!/usr/bin/env zsh" in text
    assert "./ns state" in text
    assert "./ns list" in text
    assert "./ns show" in text
    assert "./ns run <work-item-name>" in text
    assert "agentic-kit workflow upload" in text
    assert "run_agentic_kit workflow upload" in text
    assert "./ns fail" in text
    assert "./ns cleanup" in text
    assert "<<" not in text
    assert "python -c" not in text



def test_repo_ns_entrypoint_exposes_cockpit_shortcuts() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "agentic-kit cockpit status" in text
    assert "agentic-kit cockpit actions" in text


def test_repo_ns_menu_exposes_cockpit_shortcuts_without_heredocs() -> None:
    text = Path("ns-menu").read_text(encoding="utf-8")
    assert "./ns cockpit" in text
    assert "./ns actions" in text
    assert "run_ns cockpit" in text
    assert "run_ns actions" in text
    assert "<<" not in text
    assert "python -c" not in text


def test_repo_ns_entrypoint_exposes_cockpit_select_shortcut() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "\"select\"" in text
    assert "agentic-kit cockpit select" in text
    assert ".venv/bin/agentic-kit cockpit select" in text
    assert "<< " not in text
    assert "python -c" not in text


def test_repo_ns_menu_exposes_cockpit_select_shortcut_without_heredocs() -> None:
    text = Path("ns-menu").read_text(encoding="utf-8")
    assert "./ns select" in text
    assert "run_ns select" in text
    assert "15)" in text
    assert "<< " not in text
    assert "python -c" not in text


def test_repo_ns_entrypoint_exposes_cockpit_run_shortcut() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "\"cockpit-run\"" in text
    assert "agentic-kit cockpit run" in text
    assert ".venv/bin/agentic-kit cockpit run" in text
    assert "<< " not in text
    assert "python -c" not in text


def test_repo_ns_menu_exposes_read_only_cockpit_run_shortcut_only() -> None:
    text = Path("ns-menu").read_text(encoding="utf-8")
    assert "./ns cockpit-run git.status" in text
    assert "run_ns cockpit-run git.status" in text
    assert "run_ns cockpit-run workflow.go" not in text
    assert "workflow.go" not in text
    assert "<< " not in text
    assert "python -c" not in text


def test_ns_menu_does_not_clear_screen_by_default() -> None:
    menu = Path("ns-menu").read_text(encoding="utf-8")

    assert "show_menu()" in menu
    assert "NS_MENU_CLEAR:-0" in menu
    assert "\n  clear\n" not in menu


def test_ns_menu_exposes_cockpit_json_inventory_entry() -> None:
    menu = Path("ns-menu").read_text(encoding="utf-8")

    assert "./ns actions --json" in menu
    assert "run_ns actions --json" in menu
    assert "14)" in menu


def test_ns_up_legacy_module_is_removed_in_favor_of_transfer_pr_complete() -> None:
    transfer_text = Path("src/agentic_project_kit/cli_commands/transfer.py").read_text(encoding="utf-8")
    command_reference = Path("docs/reference/AGENTIC_KIT_COMMANDS.md").read_text(encoding="utf-8")

    assert not Path("src/agentic_project_kit/ns_up_pr_completion.py").exists()
    assert '@transfer_app.command("pr-complete")' in transfer_text
    assert "agentic-kit transfer pr-complete" in command_reference

def test_repo_ns_release_shortcuts_are_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "release-prep" in text
    assert "release-gate" in text
    assert "release-publish" in text
    assert "agentic_project_kit.release_prep_core" in text
    assert "tools/ns_release_prep.sh" not in text
    assert "agentic_project_kit.release_gate_core" in text
    assert "tools/ns_release_gate.sh" not in text
    assert "agentic_project_kit.release_publish_core" in text
    assert "tools/ns_release_publish.sh" not in text

def test_release_publish_requires_confirmation_token() -> None:
    text = Path("src/agentic_project_kit/release_publish_core.py").read_text(encoding="utf-8")
    assert "publish-" in text
    assert "refusing release publish" in text

def test_release_publish_creates_and_pushes_tag() -> None:
    text = Path("src/agentic_project_kit/release_publish_core.py").read_text(encoding="utf-8")
    assert "git" in text
    assert "tag" in text
    assert "push" in text
    assert "release-gate" in text
    assert "Publishing implementation is intentionally deferred" not in text

def test_repo_ns_release_verify_is_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "release-verify" in text
    assert "agentic_project_kit.release_verify_core" in text
    assert "tools/ns_release_verify.sh" not in text

def test_release_verify_waits_for_github_release() -> None:
    text = Path("src/agentic_project_kit/release_verify_core.py").read_text(encoding="utf-8")
    assert "gh" in text
    assert "release" in text
    assert "view" in text
    assert "retry" in text
    assert "GitHub release still missing after wait" in text

def test_release_gate_routes_to_python_core_directly() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    core_text = Path("src/agentic_project_kit/release_gate_core.py").read_text(encoding="utf-8")
    assert "release-gate" in ns_text
    assert "agentic_project_kit.release_gate_core" in ns_text
    assert "tools/ns_release_gate.sh" not in ns_text
    assert not Path("tools/ns_release_gate.sh").exists()
    assert "run_release_gate" in core_text

def test_release_publish_waits_for_github_release_and_verifies() -> None:
    text = Path("src/agentic_project_kit/release_publish_core.py").read_text(encoding="utf-8")
    assert "WAIT FOR RELEASE WORKFLOW AND GITHUB RELEASE" in text
    assert "sleep_seconds" in text
    assert "release_wait_attempts" in text
    assert "release-verify" in text
    assert "publish-" in text

def test_ns_pr_create_or_skip_handles_no_delta_idempotently() -> None:
    text = Path("src/agentic_project_kit/pr_create_or_skip.py").read_text(encoding="utf-8")
    ns_text = Path("ns").read_text(encoding="utf-8")
    assert "agentic_project_kit.pr_create_or_skip" in ns_text
    assert "tools/ns_pr_create_or_skip.sh" not in ns_text
    assert "No PR needed" in text
    assert "idempotent already-completed state" in text
    assert "origin/{base}..HEAD" in text
    assert not Path("tools/ns_pr_create_or_skip.sh").exists()


def test_ns_pr_create_or_skip_reuses_existing_pr_before_create() -> None:
    text = Path("src/agentic_project_kit/pr_create_or_skip.py").read_text(encoding="utf-8")
    assert "number,title,state,url" in text
    assert "Existing PR found" in text
    assert "gh" in text
    assert "pr" in text
    assert "create" in text

def test_repo_ns_commit_guard_routes_to_python_core() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    core_text = Path("src/agentic_project_kit/commit_guard.py").read_text(encoding="utf-8")
    assert "commit-guard" in ns_text
    assert "agentic_project_kit.commit_guard" in ns_text
    assert "tools/ns_commit_pr_guard.sh" not in ns_text
    assert not Path("tools/ns_commit_pr_guard.sh").exists()
    assert "refusing commit/PR workflow on main" in core_text
    assert "branch" in core_text


def test_entrypoint_slice_runner_is_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "slice-runner" in text
    assert "agentic_project_kit.entrypoint_slice_runner" in text
    assert "tools/entrypoint_slice_runner.sh" not in text


def test_entrypoint_slice_runner_has_step_stop_semantics() -> None:
    text = Path("src/agentic_project_kit/entrypoint_slice_runner.py").read_text(encoding="utf-8")
    assert "Stopping slice runner at retryable state" in text
    assert "Stopping slice runner at first failing step" in text
    assert "### RESULT: FAIL ###" in text
    assert "### RESULT: PENDING ###" in text


def test_repo_ns_exposes_mode_state_shortcuts() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "\"mode-check\"" in text
    assert "\"mode-write\"" in text
    assert "agentic_project_kit.cli state mode-check" in text
    assert "agentic_project_kit.cli state mode-write" in text
    assert "execution_mode_state" not in text

def test_repo_ns_pr_cleanup_routes_to_python_core() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    core_text = Path("src/agentic_project_kit/pr_cleanup.py").read_text(encoding="utf-8")
    assert "\"pr-cleanup\"" in ns_text
    assert "agentic_project_kit.pr_cleanup" in ns_text
    assert "tools/ns_pr_cleanup.sh" not in ns_text
    assert not Path("tools/ns_pr_cleanup.sh").exists()
    assert "NS PR CLEANUP CLASSIFICATION" in core_text

def test_repo_entrypoint_slice_runner_routes_to_python_core() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    core_text = Path("src/agentic_project_kit/entrypoint_slice_runner.py").read_text(encoding="utf-8")
    assert "\"slice-runner\"" in ns_text
    assert "agentic_project_kit.entrypoint_slice_runner" in ns_text
    assert "tools/entrypoint_slice_runner.sh" not in ns_text
    assert not Path("tools/entrypoint_slice_runner.sh").exists()
    assert "NS SLICE RUNNER" in core_text

def test_repo_ns_release_gate_routes_to_python_core() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    core_text = Path("src/agentic_project_kit/release_gate_core.py").read_text(encoding="utf-8")
    assert "\"release-gate\"" in ns_text
    assert "agentic_project_kit.release_gate_core" in ns_text
    assert "tools/ns_release_gate.sh" not in ns_text
    assert not Path("tools/ns_release_gate.sh").exists()
    assert "run_release_gate" in core_text

def test_repo_ns_release_verify_routes_to_python_core() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    core_text = Path("src/agentic_project_kit/release_verify_core.py").read_text(encoding="utf-8")
    assert "\"release-verify\"" in ns_text
    assert "agentic_project_kit.release_verify_core" in ns_text
    assert "tools/ns_release_verify.sh" not in ns_text
    assert not Path("tools/ns_release_verify.sh").exists()
    assert "verify_release" in core_text

def test_repo_ns_release_prep_routes_to_python_core() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    core_text = Path("src/agentic_project_kit/release_prep_core.py").read_text(encoding="utf-8")
    assert "\"release-prep\"" in ns_text
    assert "agentic_project_kit.release_prep_core" in ns_text
    assert "tools/ns_release_prep.sh" not in ns_text
    assert not Path("tools/ns_release_prep.sh").exists()
    assert "prepare_release" in core_text

def test_repo_ns_entrypoint_removes_dev_go_up_shortcuts() -> None:
    text = Path("ns").read_text(encoding="utf-8")

    assert 'if [ "${1:-}" = "dev" ]; then' not in text
    assert 'if [ "${1:-}" = "go" ]; then' not in text
    assert 'if [ "${1:-}" = "up" ]; then' not in text
    assert 'if [ "${1:-}" = "upload" ]; then' not in text
    assert "./ns dev" not in text
    assert "./ns go" not in text
    assert "./ns up" not in text
