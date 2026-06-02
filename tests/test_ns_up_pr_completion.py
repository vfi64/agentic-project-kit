from agentic_project_kit.ns_up_pr_completion import local_python


def test_local_python_prefers_venv_python(tmp_path):
    tool = tmp_path / ".venv" / "bin" / "python"
    tool.parent.mkdir(parents=True)
    tool.write_text("", encoding="utf-8")
    assert local_python(tmp_path) == str(tool)

def test_ns_up_uses_guarded_agentic_kit_merge(tmp_path, monkeypatch):
    import agentic_project_kit.ns_up_pr_completion as module

    commands = []

    def fake_run_command(repo_root, args, allow_failure=False):
        commands.append(args)
        joined = " ".join(args)
        if args == ["git", "branch", "--show-current"]:
            return module.CommandResult(0, "feature/example")
        if args == ["git", "status", "--short"]:
            return module.CommandResult(0, "")
        if args == ["git", "status", "--porcelain"]:
            return module.CommandResult(0, "")
        if args == ["git", "rev-list", "--count", "main..feature/example"]:
            return module.CommandResult(0, "1")
        if args[:4] == ["gh", "pr", "view", "--json"]:
            return module.CommandResult(0, "123")
        if args[:4] == ["gh", "pr", "view", "123"]:
            if "--jq" in args and ".state" in args:
                return module.CommandResult(0, "OPEN")
            if "--jq" in args and ".mergeable" in args:
                return module.CommandResult(0, "MERGEABLE")
            if "--jq" in args and ".headRefOid" in args:
                return module.CommandResult(0, "a" * 40)
            return module.CommandResult(0, '{"number":123}')
        if args[:3] == ["gh", "pr", "checks"]:
            return module.CommandResult(0, "test pass")
        if "pr wait-ci" in joined:
            return module.CommandResult(0, "READY_TO_MERGE")
        if "pr merge-if-green" in joined:
            return module.CommandResult(0, "merged=true")
        if args == ["git", "switch", "main"]:
            return module.CommandResult(0, "")
        if args == ["git", "pull", "--ff-only", "origin", "main"]:
            return module.CommandResult(0, "")
        if args == ["./ns", "dev"]:
            return module.CommandResult(0, "")
        if args[-3:] == ["-m", "agentic_project_kit.cli", "pr-hygiene"]:
            return module.CommandResult(0, "")
        if args[:3] == ["git", "log", "--oneline"]:
            return module.CommandResult(0, "")
        raise AssertionError(f"unexpected command: {args}")

    monkeypatch.setattr(module, "run_command", fake_run_command)
    monkeypatch.setattr(module, "local_agentic_kit", lambda repo_root: "agentic-kit")
    monkeypatch.setattr(module, "local_python", lambda repo_root: "python3")

    result = module.run_ns_up(tmp_path)

    assert result == 0
    assert ["gh", "pr", "merge", "123", "--squash", "--delete-branch"] not in commands
    assert [
        "agentic-kit",
        "pr",
        "wait-ci",
        "123",
        "--expected-head-sha",
        "a" * 40,
        "--timeout-seconds",
        "300",
        "--interval-seconds",
        "10",
    ] in commands
    assert [
        "agentic-kit",
        "pr",
        "merge-if-green",
        "123",
        "--expected-head-sha",
        "a" * 40,
        "--main-branch",
        "main",
        "--merge-method",
        "squash",
    ] in commands

