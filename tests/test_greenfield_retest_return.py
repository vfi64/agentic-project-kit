"""The installed-wheel return contract is local and checks real Git state."""

import subprocess

def test_return_fixture_runs_without_remote_services():
    from agentic_project_kit.greenfield_retest import run_machine, validate_machine

    retest = {
        "workspace_kind": "external_manifest",
        "commands": ["agentic-kit check --json"],
        "machine": {
            "fixture": "external_kit_return", "origin": True,
            "covers": "Local squash adoption, exact return and installation failures.",
            "steps": [
                {"run": ["agentic-kit", "check", "--json"],
                 "expect": {"returncode": 1, "stdout_contains": "NEEDS_PROJECTION_MIGRATION"}},
                {"run": ["git", "diff", "--no-index", ".agentic/tmp/return-contract/expected.json", ".agentic/tmp/return-contract/actual.json"],
                 "expect": {"returncode": 0}},
            ],
        },
    }
    validate_machine("KIT-GF-095", retest)
    result = run_machine(retest["machine"])
    assert result["result"] == "PASS", result


def test_return_snapshot_ignores_git_storage_but_tracks_repository_state(tmp_path):
    from agentic_project_kit.greenfield_retest_return import _return_state_snapshot

    def git(*args):
        return subprocess.run(
            ["git", *args], cwd=tmp_path, text=True, capture_output=True, check=True
        ).stdout.strip()

    subprocess.run(["git", "init", "-q", str(tmp_path)], check=True)
    git("config", "user.name", "Test")
    git("config", "user.email", "test@example.invalid")
    tracked = tmp_path / "product.txt"
    tracked.write_text("before\n")
    git("add", "product.txt")
    git("commit", "-m", "Initial state")

    before = _return_state_snapshot(tmp_path, git)
    (tmp_path / ".git" / "transient-cache").write_text("implementation detail\n")
    assert _return_state_snapshot(tmp_path, git) == before

    tracked.write_text("changed\n")
    assert _return_state_snapshot(tmp_path, git) != before
