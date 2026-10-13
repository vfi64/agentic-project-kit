import subprocess
from pathlib import Path
import pytest
import yaml
from test_external_rule_registry import installed_kit as installed_kit, external as external


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("refresh", "light"),
        ("product", "full"),
        ("branch", "full"),
        ("unknown", "full"),
        ("event", "full"),
        ("manifest", "full"),
    ],
)
def test_installed_custom_ci_runtime_plan(external, installed_kit, scenario, expected):
    root, cli = external
    custom = root / ".github/workflows/custom.yml"
    custom.parent.mkdir(parents=True)
    snippet = (Path(__file__).parent / "fixtures/custom_ci_runtime_plan.yaml").read_text()
    assert snippet in (Path(__file__).resolve().parents[1] / 'docs/reference/HUMAN_WORKFLOW_COMMANDS.md').read_text()
    custom.write_text(snippet)

    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root, text=True).strip()

    git("init", "-b", "main")
    git("config", "user.name", "Fixture")
    git("config", "user.email", "fixture@example.invalid")
    git("add", ".")
    git("commit", "-m", "fixture baseline")
    base = git("rev-parse", "HEAD")
    state = root / ".agentic/state/status.md"
    state.parent.mkdir(parents=True, exist_ok=True)
    state.write_text("Refreshed state")
    if scenario == "product":
        (root / "product.py").write_text("changed=True")
    git("add", ".")
    git("commit", "-m", "fixture refresh")
    head = git("rev-parse", "HEAD")
    if scenario == "manifest":
        (root / ".agentic/config.yaml").write_text("invalid: [")
    data = cli(
        "ci",
        "runtime-plan",
        "--base",
        base,
        "--head",
        "unknown" if scenario == "unknown" else head,
        "--branch",
        "codex/product" if scenario == "branch" else "docs/post-pr42-handoff-refresh",
        "--event-name",
        "push" if scenario == "event" else "pull_request",
        "--json",
    )
    assert data["mode"] == expected
    # The documented custom workflow condition skips both heavy jobs only on
    # the exact light verdict, while its check step remains unconditional.
    jobs = yaml.safe_load(custom.read_text())["jobs"]
    assert "if" not in jobs["check"] and "needs" not in jobs["check"]
    assert jobs["check"]["steps"][-1]["run"] == "agentic-kit check"
    for name in ("pytest", "playwright"):
        assert jobs[name]["needs"] == "classify"
        assert jobs[name]["if"] == "always() && needs.classify.outputs.mode != 'light'"
        assert (data["mode"] != "light") == (expected == "full")
    assert custom.read_text() == snippet
