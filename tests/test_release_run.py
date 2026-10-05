from __future__ import annotations

import json
import subprocess
from pathlib import Path

from agentic_project_kit.release_run import ReleaseRunOptions, run_release


def _workspace(root: Path, *, publication: str = "github+pypi+zenodo") -> None:
    (root / ".agentic").mkdir()
    (root / ".agentic/config.yaml").write_text(
        "\n".join(
            [
                "kit_schema_version: 2",
                "project:",
                "  name: sample",
                "  type: python",
                "profile: python-default",
                f"publication: {publication}",
                "paths:",
                "  tmp_root: .agentic/tmp",
                "hygiene:",
                "  doc_lifecycle: warn",
                "  review_budgets:",
                "    governance: 180",
                "release:",
                "  package_index_workflow:",
                "    file: release.yml",
                '    input: "publish_target=pypi"',
                "",
            ]
        ),
        encoding="utf-8",
    )


def _state_path(root: Path, version: str = "1.2.3") -> Path:
    return root / ".agentic/tmp" / f"release-run-{version}.json"


class FakeRunner:
    def __init__(self) -> None:
        self.calls: list[list[str]] = []
        self.status_outputs = [
            " M pyproject.toml\n M CHANGELOG.md\n",
            " M pyproject.toml\n M CHANGELOG.md\n",
        ]
        self.block_step: str | None = None

    def __call__(self, argv, cwd: Path):
        command = [str(item) for item in argv]
        self.calls.append(command)
        if command == ["git", "rev-parse", "HEAD"]:
            return self._completed(command, "abc123\n")
        if command == ["git", "status", "--porcelain"]:
            output = self.status_outputs.pop(0) if self.status_outputs else " M pyproject.toml\n M CHANGELOG.md\n"
            return self._completed(command, output)
        if command[:3] == ["gh", "workflow", "run"]:
            return self._completed(command, "")
        if command[:3] == ["gh", "run", "list"]:
            return self._completed(command, '[{"databaseId": 12345}]\n')
        if command[:3] == ["gh", "run", "watch"]:
            return self._completed(command, "")
        step_payload = self._payload_for(command)
        if self.block_step and self.block_step in command:
            step_payload = {"result_status": "BLOCKED"}
        return self._completed(command, json.dumps(step_payload) + "\n")

    @staticmethod
    def _completed(command: list[str], stdout: str, stderr: str = "", rc: int = 0):
        return subprocess.CompletedProcess(command, rc, stdout, stderr)

    @staticmethod
    def _payload_for(command: list[str]) -> dict[str, object]:
        joined = " ".join(command)
        if "release-publish" in command:
            return {
                "status": "PASS",
                "blocker_count": 0,
                "checks": [{"status": "PASS", "name": "ok"}],
                "approval_signature": "release-publish-sig",
            }
        if "work" in command and "finish" in command and "--dry-run" in command:
            return {"result_status": "PLANNED"}
        if "release-status" in command:
            return {"result_status": "PASS", "current_state": "current_verified"}
        if "release-prep" in command:
            return {"ok": True}
        if "post-release-check" in command or "post-release-doi-closeout" in command:
            return {"result_status": "PASS"}
        if "release ready" in joined or "work start" in joined:
            return {"result_status": "PASS"}
        return {"result_status": "PASS"}


def test_release_run_stops_at_b4_then_executes_matching_gate_to_c2(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = FakeRunner()

    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path, json_output=True), runner=runner)

    assert first["result_status"] == "AWAITING_APPROVAL"
    assert first["current_step"] == "B4"
    signature = first["gate"]["approval_signature"]
    assert signature
    assert not any("finish" in call and "--execute" in call for call in runner.calls)

    second = run_release(
        ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True, expected_signature=signature, json_output=True),
        runner=runner,
    )

    assert second["result_status"] == "AWAITING_APPROVAL"
    assert second["current_step"] == "C2"
    assert any("finish" in call and "--execute" in call for call in runner.calls)


def test_release_run_wrong_signature_blocks_without_execute_call(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = FakeRunner()
    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)

    blocked = run_release(
        ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True, expected_signature="wrong"),
        runner=runner,
    )

    assert first["current_step"] == "B4"
    assert blocked["result_status"] == "BLOCKED"
    assert blocked["current_step"] == "B4"
    assert not any("finish" in call and "--execute" in call for call in runner.calls)


def test_release_run_blocks_on_orchestrator_status_even_with_zero_returncode(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = FakeRunner()
    runner.block_step = "ready"

    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)

    assert result["result_status"] == "BLOCKED"
    assert result["current_step"] == "A2"


def test_release_run_blocks_when_paths_change_between_b3_and_b4(tmp_path: Path) -> None:
    _workspace(tmp_path)
    runner = FakeRunner()
    runner.status_outputs = [
        " M pyproject.toml\n M CHANGELOG.md\n",
        " M pyproject.toml\n M README.md\n",
    ]
    first = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)

    blocked = run_release(
        ReleaseRunOptions(
            version="1.2.3",
            root=tmp_path,
            execute=True,
            expected_signature=first["gate"]["approval_signature"],
        ),
        runner=runner,
    )

    assert blocked["result_status"] == "BLOCKED"
    assert blocked["current_step"] == "B4"
    assert blocked["blockers"] == ["changed-paths-drift"]


def test_release_run_resume_state_starts_at_b4(tmp_path: Path) -> None:
    _workspace(tmp_path)
    path = _state_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "version": "1.2.3",
                "finished_steps": ["A1", "A2", "A3", "B1", "B2", "B3"],
                "b_paths": ["CHANGELOG.md", "pyproject.toml"],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runner = FakeRunner()

    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=runner)

    assert result["result_status"] == "AWAITING_APPROVAL"
    assert result["current_step"] == "B4"
    assert runner.calls == [["git", "rev-parse", "HEAD"]]


def test_release_run_recorded_c3_dispatch_without_run_id_blocks_without_redispatch(tmp_path: Path) -> None:
    _workspace(tmp_path)
    path = _state_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "version": "1.2.3",
                "finished_steps": ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2"],
                "c3_dispatch": {"dispatched": True},
            }
        )
        + "\n",
        encoding="utf-8",
    )
    runner = FakeRunner()
    result = run_release(
        ReleaseRunOptions(version="1.2.3", root=tmp_path, execute=True, expected_signature="unused"),
        runner=runner,
    )

    assert result["result_status"] == "BLOCKED"
    assert result["current_step"] == "C3"
    assert not any(call[:3] == ["gh", "workflow", "run"] for call in runner.calls)


def test_release_run_publication_none_skips_package_index_zenodo_and_doi_phase(tmp_path: Path) -> None:
    _workspace(tmp_path, publication="none")
    path = _state_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text(
        json.dumps(
            {
                "schema_version": 1,
                "version": "1.2.3",
                "publication_policy": "none",
                "finished_steps": ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2"],
            }
        )
        + "\n",
        encoding="utf-8",
    )

    result = run_release(ReleaseRunOptions(version="1.2.3", root=tmp_path), runner=FakeRunner())

    assert result["result_status"] == "PASS"
    assert result["finished_steps"] == ["A1", "A2", "A3", "B1", "B2", "B3", "B4", "C1", "C2"]
