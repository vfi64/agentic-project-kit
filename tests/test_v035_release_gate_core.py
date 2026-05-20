from __future__ import annotations

from pathlib import Path

from agentic_project_kit.release_gate_core import ReleaseGateResult, main, run_release_gate


def test_release_gate_runs_expected_sequence_and_passes(tmp_path: Path, monkeypatch, capsys) -> None:
    calls: list[list[str]] = []

    def runner(command):
        calls.append(list(command))
        if command[:2] == ("ls", "-la"):
            return 0
        return 0

    def make_dir(path: Path) -> None:
        path.mkdir(parents=True, exist_ok=True)
        (path / "agentic_project_kit-0.3.35-py3-none-any.whl").write_text("wheel", encoding="utf-8")
        (path / "agentic_project_kit-0.3.35.tar.gz").write_text("sdist", encoding="utf-8")

    result = run_release_gate("0.3.35", project_root=tmp_path, runner=runner, make_dir=make_dir)

    assert isinstance(result, ReleaseGateResult)
    assert result.ok
    assert result.exit_code == 0
    assert ["./ns", "dev"] in calls
    assert any("release-check" in command for call in calls for command in call)
    assert any("-m" in call and "build" in call for call in calls)
    assert any("-m" in call and "twine" in call for call in calls)
    assert "### RESULT: PASS ###" in capsys.readouterr().out


def test_release_gate_stops_when_release_check_fails(tmp_path: Path, capsys) -> None:
    calls: list[list[str]] = []

    def runner(command):
        calls.append(list(command))
        if "release-check" in command:
            return 1
        return 0

    result = run_release_gate("0.3.35", project_root=tmp_path, runner=runner)

    assert not result.ok
    assert result.failed_step == "### RELEASE CHECK ###"
    assert not any("-m" in call and "build" in call for call in calls)
    assert "### RESULT: FAIL ###" in capsys.readouterr().out


def test_release_gate_rejects_dist_artifacts_from_wrong_version(tmp_path: Path, capsys) -> None:
    def runner(command):
        return 0

    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "agentic_project_kit-0.3.34-py3-none-any.whl").write_text("old", encoding="utf-8")

    result = run_release_gate("0.3.35", project_root=tmp_path, runner=runner)

    assert not result.ok
    assert result.failed_step == "dist-version-validation"
    assert "do not match 0.3.35" in capsys.readouterr().out


def test_release_gate_main_requires_version(capsys) -> None:
    assert main([]) == 2
    assert "usage" in capsys.readouterr().out
