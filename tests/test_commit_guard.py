from agentic_project_kit.commit_guard import evaluate_commit_guard


def test_commit_guard_refuses_main(monkeypatch, tmp_path):
    def fake_run_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "main"
        return 1, "unexpected"

    monkeypatch.setattr("agentic_project_kit.commit_guard._run_git", fake_run_git)
    result = evaluate_commit_guard(tmp_path)
    assert result.ok is False
    assert result.branch == "main"
    assert "refusing commit/PR workflow on main" in result.messages[0]


def test_commit_guard_passes_dirty_feature_branch(monkeypatch, tmp_path):
    def fake_run_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "feature/x"
        if args == ["status", "--porcelain"]:
            return 0, " M README.md"
        return 1, "unexpected"

    monkeypatch.setattr("agentic_project_kit.commit_guard._run_git", fake_run_git)
    result = evaluate_commit_guard(tmp_path)
    assert result.ok is True
    assert result.dirty is True
    assert result.messages == ("Commit/PR guard passed on branch: feature/x",)


def test_commit_guard_reports_no_changes_on_clean_feature_branch(monkeypatch, tmp_path):
    def fake_run_git(repo_root, args):
        if args == ["branch", "--show-current"]:
            return 0, "feature/x"
        if args == ["status", "--porcelain"]:
            return 0, ""
        return 1, "unexpected"

    monkeypatch.setattr("agentic_project_kit.commit_guard._run_git", fake_run_git)
    result = evaluate_commit_guard(tmp_path)
    assert result.ok is True
    assert result.dirty is False
    assert result.messages == ("No local changes detected on branch: feature/x",)
