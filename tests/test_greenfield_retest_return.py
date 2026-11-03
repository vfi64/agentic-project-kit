"""The installed-wheel return contract is local and checks real Git state."""

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
    diff = result["steps"][-1].get("stdout_tail", "") if result["steps"] else ""
    assert result["result"] == "PASS", f"{result}; expected/actual diff:\n{diff}"
