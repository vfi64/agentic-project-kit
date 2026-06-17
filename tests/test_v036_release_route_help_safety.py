from __future__ import annotations

from pathlib import Path

from agentic_project_kit import release_gate_core, release_prep_core, release_publish_core, release_verify_core


def test_release_prep_help_returns_before_mutation(monkeypatch, capsys):
    def fail_prepare(*args, **kwargs):
        raise AssertionError("prepare_release must not run for --help")
    monkeypatch.setattr(release_prep_core, "prepare_release", fail_prepare)
    assert release_prep_core.main(["--help"]) == 0
    assert "usage: ./ns release-prep <version>" in capsys.readouterr().out


def test_release_prep_invalid_version_returns_before_mutation(monkeypatch):
    def fail_prepare(*args, **kwargs):
        raise AssertionError("prepare_release must not run for invalid versions")
    monkeypatch.setattr(release_prep_core, "prepare_release", fail_prepare)
    assert release_prep_core.main(["--help-like"]) == 2


def test_release_gate_help_and_invalid_version_return_before_steps(monkeypatch):
    def fail_gate(*args, **kwargs):
        raise AssertionError("run_release_gate must not run")
    monkeypatch.setattr(release_gate_core, "run_release_gate", fail_gate)
    assert release_gate_core.main(["--help"]) == 0
    assert release_gate_core.main(["--help-like"]) == 2


def test_release_publish_help_and_invalid_version_return_before_publish(monkeypatch):
    def fail_publish(*args, **kwargs):
        raise AssertionError("publish_release must not run")
    monkeypatch.setattr(release_publish_core, "publish_release", fail_publish)
    assert release_publish_core.main(["--help"]) == 0
    assert release_publish_core.main(["--help-like"]) == 2


def test_release_verify_help_and_invalid_version_return_before_wait(monkeypatch):
    def fail_verify(*args, **kwargs):
        raise AssertionError("verify_release must not run")
    monkeypatch.setattr(release_verify_core, "verify_release", fail_verify)
    assert release_verify_core.main(["--help"]) == 0
    assert release_verify_core.main(["--help-like"]) == 2


def test_release_prep_uses_agentic_kit_local_feature_gate_command() -> None:
    text = Path("src/agentic_project_kit/release_prep_core.py").read_text(encoding="utf-8")

    assert '"dev", "local-feature-gate"' in text
    assert '["./ns", "dev-local-feature-gate"]' not in text
    assert '["./ns", "dev"]' not in text
