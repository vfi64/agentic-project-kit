from pathlib import Path

from agentic_project_kit import agent_command_runner as acr


def test_stage_commit_push_ignores_missing_untracked_paths(tmp_path: Path, monkeypatch) -> None:
    calls = []
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

    monkeypatch.setattr(acr, "_git_path_is_tracked", fake_tracked)
    monkeypatch.setattr(acr.subprocess, "run", fake_run)
    monkeypatch.setattr(acr, "current_branch", lambda: "feature/test")

    acr.stage_commit_push([existing, missing], "msg")

    assert calls[0] == ["git", "add", existing.as_posix()]
    assert calls[1] == ["git", "commit", "-m", "msg"]
    assert calls[2] == ["git", "push", "-u", "origin", "feature/test"]
