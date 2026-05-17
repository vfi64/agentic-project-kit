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
    assert "./ns upload" in text
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

def test_repo_ns_entrypoint_exposes_no_copy_dev_gate() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "./ns dev" in text or "${1:-}" in text
    assert "NS DEV LOCAL FEATURE GATE" in text
    assert "no git pull" in text
    assert "### RESULT: PASS ###" in text
    assert "### RESULT: FAIL ###" in text

def test_repo_ns_go_guard_protects_dirty_feature_branch() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "NS GO GUARD" in text
    assert "git_pull_ff_only" in text
    assert "./ns dev" in text
    assert "dirty feature branch" in text
    assert "### RESULT: FAIL ###" in text


def test_repo_ns_up_invokes_pr_completion_tool() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "tools/ns_up_pr_completion.sh" in text
    assert "${1:-}" in text


def test_ns_up_pr_completion_tool_has_pass_fail_markers() -> None:
    text = Path("tools/ns_up_pr_completion.sh").read_text(encoding="utf-8")
    assert "NS UP PR COMPLETION CYCLE" in text
    assert "### RESULT: PASS ###" in text
    assert "### RESULT: FAIL ###" in text
    assert "gh pr merge" in text
    assert "./ns dev" in text

def test_ns_up_tool_updates_main_only_after_successful_merge() -> None:
    text = Path("tools/ns_up_pr_completion.sh").read_text(encoding="utf-8")
    assert "MERGED=0" in text
    assert "MERGED=1" in text
    assert 'if [ "$MERGED" -eq 1 ]; then' in text
    assert "UPDATE MAIN SKIPPED" in text
    assert "PR is not mergeable" in text
    assert "working tree is dirty" in text

def test_ns_up_tool_is_valid_shell_syntax() -> None:
    import subprocess

    result = subprocess.run(["sh", "-n", "tools/ns_up_pr_completion.sh"], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr


def test_repo_ns_release_shortcuts_are_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "release-prep" in text
    assert "release-gate" in text
    assert "release-publish" in text
    assert "tools/ns_release_prep.sh" in text
    assert "tools/ns_release_gate.sh" in text
    assert "tools/ns_release_publish.sh" in text

def test_release_publish_requires_confirmation_token() -> None:
    text = Path("tools/ns_release_publish.sh").read_text(encoding="utf-8")
    assert "publish-$TAG" in text
    assert "refusing release publish" in text


def test_release_publish_creates_and_pushes_tag() -> None:
    text = Path("tools/ns_release_publish.sh").read_text(encoding="utf-8")
    assert "git tag \"$TAG\"" in text
    assert "git push origin \"$TAG\"" in text
    assert "./ns release-gate \"$VERSION\"" in text
    assert "Publishing implementation is intentionally deferred" not in text


def test_repo_ns_release_verify_is_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "release-verify" in text
    assert "tools/ns_release_verify.sh" in text


def test_release_verify_waits_for_github_release() -> None:
    text = Path("tools/ns_release_verify.sh").read_text(encoding="utf-8")
    assert "gh release view" in text
    assert "sleep 10" in text
    assert "post-release-check" in text


def test_release_gate_cleans_dist_before_build() -> None:
    text = Path("tools/ns_release_gate.sh").read_text(encoding="utf-8")
    assert "rm -rf dist build *.egg-info" in text
    assert "VERIFY DIST ONLY CONTAINS TARGET VERSION" in text
    assert "grep -v" in text


def test_release_publish_waits_for_github_release_and_verifies() -> None:
    text = Path("tools/ns_release_publish.sh").read_text(encoding="utf-8")
    assert "WAIT FOR RELEASE WORKFLOW AND GITHUB RELEASE" in text
    assert "sleep 10" in text
    assert "while [ \"$i\" -lt 30 ]" in text
    assert "./ns release-verify \"$VERSION\"" in text
    assert "publish-$TAG" in text


def test_ns_up_handles_already_merged_pr_idempotently() -> None:
    text = Path("tools/ns_up_pr_completion.sh").read_text(encoding="utf-8")
    assert "PR_STATE" in text
    assert "MERGED" in text
    assert "idempotent completion state" in text
    assert "MERGEABLE" in text


def test_ns_up_treats_pending_checks_as_wait_state_not_fail_state() -> None:
    text = Path("tools/ns_up_pr_completion.sh").read_text(encoding="utf-8")
    assert "### PR CHECKS SNAPSHOT ###" in text
    assert "gh pr checks \"$PR_NUMBER\" || true" in text
    assert "gh pr checks \"$PR_NUMBER\" --watch" in text


def test_ns_pr_create_or_skip_handles_no_delta_idempotently() -> None:
    text = Path("tools/ns_pr_create_or_skip.sh").read_text(encoding="utf-8")
    assert "DELTA" in text
    assert "No PR needed" in text
    assert "idempotent already-completed state" in text
    assert "origin/$BASE..HEAD" in text


def test_ns_pr_create_or_skip_reuses_existing_pr_before_create() -> None:
    text = Path("tools/ns_pr_create_or_skip.sh").read_text(encoding="utf-8")
    assert "gh pr view --json number,title,state,url" in text
    assert "Existing PR found" in text
    assert "gh pr create --base" in text

def test_ns_up_handles_noop_branches_idempotently() -> None:
    text = Path("tools/ns_up_pr_completion.sh").read_text(encoding="utf-8")
    assert "commits_ahead_of_main" in text
    assert "idempotent no-op completion" in text
    assert "git rev-list --count main.." in text
    assert "exit \"$STATUS\"" in text


def test_repo_ns_refuses_direct_main_commit_helper() -> None:
    text = Path("tools/ns_commit_pr_guard.sh").read_text(encoding="utf-8")
    assert "refusing commit/PR workflow on main" in text
    assert "git branch --show-current" in text
    assert "exit 1" in text
    assert "create a feature or docs branch first" in text


def test_ns_slice_runner_is_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "slice-runner" in text
    assert "tools/ns_slice_runner.sh" in text

def test_ns_slice_runner_has_step_stop_semantics() -> None:
    text = Path("tools/ns_slice_runner.sh").read_text(encoding="utf-8")
    assert "advances only after target-state PASS" in text
    assert "### RESULT: PENDING ###" in text
    assert "ALREADY_MERGED" in text
    assert "Stopping slice runner at first failing step." in text
    assert "sh -c" in text

def test_idempotent_finalization_guard_is_documented() -> None:
    text = Path("docs/planning/IDEMPOTENT_FINALIZATION_GUARD.md").read_text(encoding="utf-8")
    assert "Status: proposed" in text
    assert "Decision status: Proposed" in text
    assert "branch already exists" in text
    assert "target documentation marker already exists" in text
    assert "no commits between base and head" in text
    assert "Never commit directly to main" in text
    assert "quote-fragile inline Python" in text

def test_finalize_guard_command_is_wired() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    assert "finalize-guard" in text
    assert "tools/ns_finalize_guard.sh" in text

def test_finalize_guard_handles_existing_or_completed_branches() -> None:
    text = Path("tools/ns_finalize_guard.sh").read_text(encoding="utf-8")
    assert "marker_already_on_main=true" in text
    assert "local_branch_exists" in text
    assert "remote_branch_exists" in text
    assert "commits_ahead_of_main" in text
    assert "Idempotent completion" in text


def test_safe_remove_diagnostic_guard_distinguishes_tracked_files() -> None:
    script = Path("tools/ns_safe_remove_diagnostic.sh").read_text(encoding="utf-8")
    assert "git ls-files --error-unmatch" in script
    assert "git restore" in script
    assert "rm -f" in script
    assert "Tracked file detected" in script

def test_ns_clean_evidence_is_wired_and_safe() -> None:
    ns_text = Path("ns").read_text(encoding="utf-8")
    script_text = Path("tools/ns_clean_evidence.sh").read_text(encoding="utf-8")
    assert "clean-evidence" in ns_text
    assert "tools/ns_clean_evidence.sh" in ns_text
    assert "tmp/agent-evidence" in script_text
    assert "docs/reports/CURRENT_WORKFLOW_OUTPUT.md" in script_text
    assert "does not delete arbitrary docs/reports files" in script_text
    assert "NEEDS_HUMAN_REVIEW" in script_text
