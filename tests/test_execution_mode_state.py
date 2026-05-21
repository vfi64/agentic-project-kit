from agentic_project_kit.execution_mode_state import evaluate_mode_switch, render_mode_check, write_mode_state


def test_mode_check_blocks_dirty_local_worktree(monkeypatch, tmp_path):
    def fake_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "feature/x"
        if args == ["status", "--short"]:
            return 0, " M ns"
        return 1, "unexpected"

    monkeypatch.setattr("agentic_project_kit.execution_mode_state._run_git", fake_git)
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._tool_status", lambda tool, repo_root=None: "ok")
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._venv_available", lambda root: True)

    result = evaluate_mode_switch(tmp_path, "local", expected_branch="feature/x")

    assert result.ok is False
    assert result.state == "DIRTY_LOCAL_BLOCKED"
    assert result.findings == ("dirty_worktree",)


def test_mode_check_blocks_wrong_branch(monkeypatch, tmp_path):
    def fake_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "feature/old"
        if args == ["status", "--short"]:
            return 0, ""
        return 1, "unexpected"

    monkeypatch.setattr("agentic_project_kit.execution_mode_state._run_git", fake_git)
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._tool_status", lambda tool, repo_root=None: "ok")
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._venv_available", lambda root: True)

    result = evaluate_mode_switch(tmp_path, "remote", expected_branch="main")

    assert result.ok is False
    assert result.state == "MODE_SWITCH_BLOCKED"
    assert result.findings == ("branch_mismatch expected=main actual=feature/old",)


def test_mode_check_passes_clean_local_ready(monkeypatch, tmp_path):
    def fake_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "feature/x"
        if args == ["status", "--short"]:
            return 0, ""
        return 1, "unexpected"

    monkeypatch.setattr("agentic_project_kit.execution_mode_state._run_git", fake_git)
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._tool_status", lambda tool, repo_root=None: "ok")
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._venv_available", lambda root: True)

    result = evaluate_mode_switch(tmp_path, "local", expected_branch="feature/x")

    assert result.ok is True
    assert result.state == "LOCAL_READY"
    assert "### RESULT: PASS ###" in render_mode_check(result)


def test_mode_write_persists_state_file(monkeypatch, tmp_path):
    def fake_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "main"
        if args == ["status", "--short"]:
            return 0, ""
        return 1, "unexpected"

    monkeypatch.setattr("agentic_project_kit.execution_mode_state._run_git", fake_git)
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._tool_status", lambda tool, repo_root=None: "ok")
    monkeypatch.setattr("agentic_project_kit.execution_mode_state._venv_available", lambda root: True)

    result = evaluate_mode_switch(tmp_path, "remote", expected_branch="main")
    path = write_mode_state(tmp_path, result, "test")

    text = path.read_text(encoding="utf-8")
    assert "mode_state: REMOTE_READY" in text
    assert "reason: test" in text


def test_mode_check_accepts_ruff_from_local_venv(monkeypatch, tmp_path):
    def fake_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "feature/x"
        if args == ["status", "--short"]:
            return 0, ""
        return 1, "unexpected"

    venv_bin = tmp_path / ".venv" / "bin"
    venv_bin.mkdir(parents=True)
    (venv_bin / "ruff").write_text("", encoding="utf-8")
    (venv_bin / "python").write_text("", encoding="utf-8")

    monkeypatch.setattr("agentic_project_kit.execution_mode_state._run_git", fake_git)
    monkeypatch.setattr("agentic_project_kit.execution_mode_state.shutil.which", lambda tool: None)

    result = evaluate_mode_switch(tmp_path, "local", expected_branch="feature/x")

    assert result.ok is True
    assert result.state == "LOCAL_READY"
    assert "missing_tool=ruff" not in result.findings
    assert result.required_tools["ruff"] == "ok"
