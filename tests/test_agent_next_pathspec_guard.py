from pathlib import Path

from agentic_project_kit import agent_command_runner as acr


def test_stage_commit_push_ignores_missing_untracked_paths(tmp_path: Path, monkeypatch) -> None:
    calls = []
    push_calls = []
    existing = tmp_path / "existing.txt"
    missing = tmp_path / "missing.txt"
    existing.write_text("ok", encoding="utf-8")

    def fake_tracked(path: Path) -> bool:
        return False

    def fake_run(args, check=False, **kwargs):
        calls.append(args)
        class Result:
            returncode = 0
        return Result()

    class SafePushPass:
        ok = True
        returncode = 0
        command = ("git", "push", "-u", "origin", "feature/test")
        stdout = "pushed"
        stderr = ""

    def fake_safe_push(*args, **kwargs):
        push_calls.append(kwargs)
        return SafePushPass()

    monkeypatch.setattr(acr, "_git_path_is_tracked", fake_tracked)
    monkeypatch.setattr(acr.subprocess, "run", fake_run)
    monkeypatch.setattr(acr, "safe_push", fake_safe_push)
    monkeypatch.setattr(acr, "current_branch", lambda: "feature/test")

    acr.stage_commit_push([existing, missing], "msg")

    assert calls[0] == ["git", "add", existing.as_posix()]
    assert calls[1] == ["git", "commit", "-m", "msg"]
    assert [call["target_branch"] for call in push_calls] == ["feature/test", "feature/test"]
