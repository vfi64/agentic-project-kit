from pathlib import Path

from agentic_project_kit import release_prep_core
from agentic_project_kit.release_prep_core import CommandResult, normalize_version, prepare_release, python_tool


def test_normalize_version_accepts_plain_and_tag():
    assert normalize_version("0.3.37") == ("0.3.37", "v0.3.37")
    assert normalize_version("v0.3.37") == ("0.3.37", "v0.3.37")


def test_python_tool_prefers_local_venv(tmp_path):
    tool = tmp_path / ".venv" / "bin" / "python"
    tool.parent.mkdir(parents=True)
    tool.write_text("", encoding="utf-8")
    assert python_tool(tmp_path) == str(tool)


def test_prepare_release_does_not_patch_metadata_when_main_update_fails(monkeypatch, tmp_path, capsys):
    calls = []

    def fake_run_command(_repo_root: Path, args: list[str]) -> CommandResult:
        calls.append(args)
        if args == ["git", "pull", "--ff-only", "origin", "main"]:
            return CommandResult(1, "cannot update main")
        return CommandResult(0, "ok")

    monkeypatch.setattr(release_prep_core, "run_command", fake_run_command)
    monkeypatch.setattr(release_prep_core, "python_tool", lambda _repo_root: "py")

    assert prepare_release("0.4.4", tmp_path) == 1

    output = capsys.readouterr().out
    assert "ABORT BEFORE METADATA PATCH" in output
    assert "Release metadata was not patched." in output
    assert not any("tools/ns_release_metadata_prep.py" in call for args in calls for call in args)
    assert not any(args[:2] == ["git", "switch"] and "-c" in args for args in calls)


def test_prepare_release_does_not_patch_metadata_when_branch_checkout_fails(monkeypatch, tmp_path, capsys):
    calls = []

    def fake_run_command(_repo_root: Path, args: list[str]) -> CommandResult:
        calls.append(args)
        if args[:4] == ["git", "show-ref", "--verify", "--quiet"]:
            return CommandResult(1, "")
        if args[:3] == ["git", "switch", "-c"]:
            return CommandResult(1, "cannot create branch")
        return CommandResult(0, "ok")

    monkeypatch.setattr(release_prep_core, "run_command", fake_run_command)
    monkeypatch.setattr(release_prep_core, "python_tool", lambda _repo_root: "py")

    assert prepare_release("0.4.4", tmp_path) == 1

    output = capsys.readouterr().out
    assert "ABORT BEFORE METADATA PATCH" in output
    assert "Release metadata was not patched." in output
    assert not any("tools/ns_release_metadata_prep.py" in call for args in calls for call in args)
