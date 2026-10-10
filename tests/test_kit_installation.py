"""GF-021/051: deterministic discovery before installing into a workspace."""

from __future__ import annotations

import json
from pathlib import Path
import subprocess

import pytest

from agentic_project_kit.kit_installation import (
    InstallationObservation,
    InterpreterCandidate,
    discover_kit_installation,
    installation_candidates,
    probe_installation,
    select_installation,
)


def candidate(root: Path, source: str = "workspace_venv") -> InterpreterCandidate:
    prefix = root / (".venv" if source == "workspace_venv" else "declared-env")
    return InterpreterCandidate(prefix / "bin/python", source, prefix)


def observation(item: InterpreterCandidate, status: str = "FOUND") -> InstallationObservation:
    return InstallationObservation(
        candidate=item,
        status=status,
        reason="installed" if status == "FOUND" else "package_not_installed",
        version="1.0.18" if status == "FOUND" else "",
        prefix=str(item.expected_prefix),
        base_prefix="/base/python",
        distribution_root=str(item.expected_prefix / "lib/site-packages"),
        package_origin=str(
            item.expected_prefix / "lib/site-packages/agentic_project_kit/__init__.py"
        ),
    )


def metadata(item: InterpreterCandidate, **changes: object) -> str:
    data = {
        "version": "1.0.18",
        "executable": str(item.python),
        "prefix": str(item.expected_prefix),
        "base_prefix": "/base/python",
        "distribution_root": str(item.expected_prefix / "lib/site-packages"),
        "package_origin": str(
            item.expected_prefix / "lib/site-packages/agentic_project_kit/__init__.py"
        ),
        "entrypoint": "agentic_project_kit.cli:app",
    }
    data.update(changes)
    return json.dumps(data)


def test_candidates_prefer_workspace_venv_then_explicit_interpreter(tmp_path: Path) -> None:
    result = installation_candidates(
        tmp_path, declared_interpreter="tools/env/bin/python", platform="posix"
    )
    assert [item.source for item in result] == ["workspace_venv", "declared"]
    assert result[0].python == tmp_path / ".venv/bin/python"
    assert result[1].python == tmp_path / "tools/env/bin/python"
    assert result[0].expected_prefix == tmp_path / ".venv"
    assert result[1].expected_prefix is None


def test_candidates_support_windows_without_posix_fallback(tmp_path: Path) -> None:
    result = installation_candidates(tmp_path, platform="nt")
    assert len(result) == 1
    assert result[0].python == tmp_path / ".venv/Scripts/python.exe"


def test_candidates_deduplicate_declared_workspace_python(tmp_path: Path) -> None:
    result = installation_candidates(
        tmp_path, declared_interpreter=".venv/bin/python", platform="posix"
    )
    assert len(result) == 1


def test_candidate_preserves_venv_python_symlink_path(tmp_path: Path) -> None:
    base = tmp_path / "base-python"
    base.touch()
    interpreter = tmp_path / ".venv/bin/python"
    interpreter.parent.mkdir(parents=True)
    interpreter.symlink_to(base)
    assert installation_candidates(tmp_path, platform="posix")[0].python == interpreter


def test_selection_prefers_local_over_declared_even_if_observations_are_reversed(
    tmp_path: Path,
) -> None:
    local = observation(candidate(tmp_path))
    declared = observation(candidate(tmp_path, "declared"))
    result = select_installation((declared, local))
    assert result.status == "FOUND"
    assert result.installation == local
    assert result.cli_argv == (str(local.candidate.python), "-m", "agentic_project_kit.cli")


def test_selection_uses_declared_only_if_local_not_found(tmp_path: Path) -> None:
    local = observation(candidate(tmp_path), "ABSENT")
    declared = observation(candidate(tmp_path, "declared"))
    result = select_installation((local, declared))
    assert result.installation == declared
    assert result.observations == (local, declared)


def test_errors_are_not_reported_as_missing_installation(tmp_path: Path) -> None:
    result = select_installation((observation(candidate(tmp_path), "ERROR"),))
    assert result.status == "BLOCKED"
    assert result.installation is None
    assert result.cli_argv == ()


def test_absence_is_distinct_from_probe_failure(tmp_path: Path) -> None:
    result = select_installation((observation(candidate(tmp_path), "ABSENT"),))
    assert result.status == "NOT_FOUND"
    assert result.cli_argv == ()


def test_probe_isolated_bounded_and_does_not_require_console_script(tmp_path: Path) -> None:
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()
    seen = []

    def runner(argv, **kwargs):
        seen.append((argv, kwargs))
        return subprocess.CompletedProcess(argv, 0, metadata(item), "")

    result = probe_installation(item, runner=runner)
    assert result.status == "FOUND"
    assert result.version == "1.0.18"
    argv, kwargs = seen[0]
    assert argv[:3] == [str(item.python), "-I", "-c"]
    assert kwargs["timeout"] == 5
    assert kwargs["cwd"] == str(item.python.parent)
    assert kwargs.get("shell", False) is False
    assert not (item.python.parent / "agentic-kit").exists()


@pytest.mark.parametrize("stdout", ["{}", "not-json", "[]", '"text"', '{"version": false}'])
def test_probe_rejects_invalid_metadata(tmp_path: Path, stdout: str) -> None:
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()
    result = probe_installation(
        item, runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, stdout, "")
    )
    assert result.status == "ERROR"
    assert result.reason == "invalid_probe_metadata"


@pytest.mark.parametrize(
    "change,reason",
    [
        ({"prefix": "/wrong/env"}, "workspace_environment_mismatch"),
        ({"executable": "/wrong/bin/python"}, "interpreter_mismatch"),
        ({"distribution_root": "/global/site-packages"}, "package_outside_environment"),
        (
            {"package_origin": "/global/agentic_project_kit/__init__.py"},
            "package_outside_environment",
        ),
        ({"package_origin": ""}, "invalid_probe_metadata"),
        ({"entrypoint": "another_package:main"}, "unexpected_cli_entrypoint"),
        ({"version": ""}, "invalid_probe_metadata"),
    ],
)
def test_probe_refuses_wrong_environment_or_package(
    tmp_path: Path, change: dict, reason: str
) -> None:
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()
    result = probe_installation(
        item,
        runner=lambda argv, **kw: subprocess.CompletedProcess(
            argv, 0, metadata(item, **change), ""
        ),
    )
    assert result.status == "ERROR"
    assert result.reason == reason


def test_declared_system_python_is_not_a_workspace_owned_environment(tmp_path: Path) -> None:
    item = InterpreterCandidate(tmp_path / "python", "declared", None)
    item.python.touch()
    raw = metadata(
        candidate(tmp_path), executable=str(item.python), prefix="/system", base_prefix="/system"
    )
    result = probe_installation(
        item, runner=lambda argv, **kw: subprocess.CompletedProcess(argv, 0, raw, "")
    )
    assert result.status == "ERROR"
    assert result.reason == "not_virtual_environment"


def test_missing_interpreter_never_runs_subprocess(tmp_path: Path) -> None:
    def unexpected(*args, **kwargs):
        pytest.fail("must not probe missing interpreter")

    result = probe_installation(candidate(tmp_path), runner=unexpected)
    assert result.status == "ABSENT"
    assert result.reason == "interpreter_missing"


def test_probe_handles_timeout_without_claiming_absence(tmp_path: Path) -> None:
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()

    def runner(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, kwargs["timeout"])

    result = probe_installation(item, runner=runner)
    assert result.status == "ERROR"
    assert result.reason == "probe_timeout"


@pytest.mark.parametrize(
    "code,status,reason",
    [
        (3, "ABSENT", "package_not_installed"),
        (1, "ERROR", "probe_failed"),
        (127, "ERROR", "probe_failed"),
    ],
)
def test_probe_nonzero_codes_are_classified(
    tmp_path: Path, code: int, status: str, reason: str
) -> None:
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()
    result = probe_installation(
        item, runner=lambda argv, **kw: subprocess.CompletedProcess(argv, code, "", "diagnostic")
    )
    assert result.status == status
    assert result.reason == reason


def test_discovery_finds_local_package_without_global_path(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PATH", "")
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()
    seen = []

    def runner(argv, **kwargs):
        seen.append(argv[0])
        return subprocess.CompletedProcess(argv, 0, metadata(item), "")

    result = discover_kit_installation(tmp_path, runner=runner)
    assert result.status == "FOUND"
    assert seen == [str(item.python)]
    assert result.as_json_data()["installation"]["version"] == "1.0.18"


def test_healthy_local_installation_does_not_probe_declared_interpreter(tmp_path: Path) -> None:
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()
    seen = []

    def runner(argv, **kwargs):
        seen.append(argv[0])
        return subprocess.CompletedProcess(argv, 0, metadata(item), "")

    result = discover_kit_installation(
        tmp_path, declared_interpreter="declared-env/bin/python", runner=runner
    )
    assert result.status == "FOUND"
    assert seen == [str(item.python)]


def test_discovery_has_no_global_fallback(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("PATH", "/usr/local/bin:/usr/bin")
    result = discover_kit_installation(tmp_path)
    assert result.status == "NOT_FOUND"
    assert len(result.observations) == 1


def test_discovery_probes_declared_environment_after_local_package_is_absent(
    tmp_path: Path,
) -> None:
    local, declared = installation_candidates(
        tmp_path, declared_interpreter="declared-env/bin/python"
    )
    for item in (local, declared):
        item.python.parent.mkdir(parents=True)
        item.python.touch()
    declared_metadata = metadata(candidate(tmp_path, "declared"))
    seen = []

    def runner(argv, **kwargs):
        seen.append(argv[0])
        return (
            subprocess.CompletedProcess(argv, 3, "", "")
            if argv[0] == str(local.python)
            else subprocess.CompletedProcess(argv, 0, declared_metadata, "")
        )

    result = discover_kit_installation(
        tmp_path, declared_interpreter="declared-env/bin/python", runner=runner
    )
    assert result.status == "FOUND"
    assert result.installation.candidate == declared
    assert seen == [str(local.python), str(declared.python)]
    assert result.observations[0].reason == "package_not_installed"


def test_permission_error_is_preserved_as_diagnosis(tmp_path: Path) -> None:
    item = candidate(tmp_path)
    item.python.parent.mkdir(parents=True)
    item.python.touch()

    def runner(*args, **kwargs):
        raise PermissionError("cannot execute interpreter")

    result = probe_installation(item, runner=runner)
    assert result.status == "ERROR"
    assert result.reason == "interpreter_unavailable"
    assert "cannot execute" in result.detail


def test_missing_package_does_not_create_or_install_anything(tmp_path: Path) -> None:
    before = tuple(tmp_path.rglob("*"))
    result = discover_kit_installation(tmp_path)
    assert result.status == "NOT_FOUND"
    assert tuple(tmp_path.rglob("*")) == before


def test_declared_interpreter_path_is_relative_to_workspace_not_process_cwd(
    tmp_path: Path, monkeypatch
) -> None:
    workspace = tmp_path / "workspace"
    another = tmp_path / "other"
    another.mkdir()
    monkeypatch.chdir(another)
    paths = installation_candidates(workspace, declared_interpreter="env/bin/python")
    assert paths[1].python == workspace / "env/bin/python"
