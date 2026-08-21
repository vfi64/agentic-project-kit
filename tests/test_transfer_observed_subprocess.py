from __future__ import annotations

import subprocess

from agentic_project_kit.transfer_observed_subprocess import run_observed_subprocess


def test_run_observed_subprocess_records_completed_process(monkeypatch) -> None:
    def fake_run(argv, *args, **kwargs):
        return subprocess.CompletedProcess(list(argv), 0, "out\n", "err\n")

    monkeypatch.setattr(subprocess, "run", fake_run)

    payload = run_observed_subprocess(
        "demo-step",
        ["tool", "arg"],
        timeout_seconds=7,
    )

    assert payload == {
        "name": "demo-step",
        "argv": ["tool", "arg"],
        "returncode": 0,
        "stdout": "out\n",
        "stderr": "err\n",
        "ok": True,
        "timeout_seconds": 7,
        "timed_out": False,
    }


def test_run_observed_subprocess_records_timeout(monkeypatch) -> None:
    def fake_run(argv, *args, **kwargs):
        raise subprocess.TimeoutExpired(
            list(argv),
            kwargs["timeout"],
            output=b"partial out\n",
            stderr=b"partial err\n",
        )

    monkeypatch.setattr(subprocess, "run", fake_run)

    payload = run_observed_subprocess(
        "slow-step",
        ["tool", "slow"],
        timeout_seconds=3,
    )

    assert payload["returncode"] == 124
    assert payload["stdout"] == "partial out\n"
    assert payload["stderr"] == "partial err\n"
    assert payload["ok"] is False
    assert payload["timed_out"] is True
    assert payload["timeout_seconds"] == 3
