"""F4: workflow helpers must not mutate Git outside Kit command authority.

`agentic-kit workflow go/run/upload/upload-output/fail-report/cleanup` run tools/next-step.py, which
used to push, pull and delete branches with direct git calls (command usage audit 2026-10-15, F4).
Remote mutations and branch deletion now go through the Kit primitives in
agentic_project_kit.transfer_repo_actions; the remaining local git calls are bounded and listed here.
"""

from __future__ import annotations

import ast
import importlib.util
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SCANNED_ROOTS = (REPO_ROOT / "tools", REPO_ROOT / "src" / "agentic_project_kit" / "cli_commands")

MUTATING_VERBS = frozenset(
    {
        "add",
        "am",
        "apply",
        "branch",
        "checkout",
        "cherry-pick",
        "clean",
        "commit",
        "merge",
        "mv",
        "pull",
        "push",
        "rebase",
        "reset",
        "restore",
        "revert",
        "rm",
        "stash",
        "switch",
        "tag",
        "update-ref",
        "worktree",
    }
)
READ_ONLY_FLAGS = {
    "branch": frozenset({"--show-current", "--list", "-r", "-a", "--format=%(refname:short)", "--contains", "--merged"}),
    "tag": frozenset({"--sort=-creatordate", "--list", "-l"}),
}

# Reviewed direct git mutations, keyed by repository path. Every entry states why it is not a
# bypass of Kit command authority. A new direct mutation, or a stale entry, fails the test.
ALLOWED_DIRECT_GIT_MUTATIONS: dict[str, dict[str, str]] = {
    "tools/next-step.py": {
        "switch -c": "local evidence branch; created under the workspace mutation lock after the "
        "empty-index and published-HEAD preconditions",
        "add --": "fixed evidence paths only; the staged set is checked before the commit",
        "add -f --": "the git-ignored evidence file, checked against the evidence path set",
        "commit -m": "local commit of the verified evidence paths; pushing goes through push_current",
        "restore --": "restores the single tracked workflow_state file before switching back",
        "switch --": "local return to the validated branch the workflow started on",
    },
    "tools/workflow_runner.py": {
        "switch --": "allow-listed work-order steps with validated branch names "
        "(trust-boundary review, ai-work-order-trust-boundary-review)",
        "pull --ff-only": "allow-listed git_pull_ff_only work-order step",
    },
    "tools/NEXT_TRANSFER_TASK.py": {
        "switch main": "legacy helper not reachable from any agentic-kit command; retirement is tracked "
        "in the ns-legacy workflow-shell-helper slice",
        "pull --ff-only origin": "legacy helper, see above",
        "switch": "legacy helper, see above",
        "reset --hard main": "legacy helper, see above",
        "switch -c": "legacy helper, see above",
        "add": "legacy helper, see above",
        "commit -m": "legacy helper, see above",
        "push -u origin": "legacy helper, see above",
    },
    "src/agentic_project_kit/cli_commands/human_workflows.py": {
        "switch": "existing Kit command implementation (work start); outside F4",
    },
    "src/agentic_project_kit/cli_commands/transfer_context_helpers.py": {
        "restore --": "existing Kit command implementation; outside F4",
    },
    "src/agentic_project_kit/cli_commands/transfer_handoff_flow.py": {
        "restore --": "existing Kit command implementation; outside F4",
    },
    "src/agentic_project_kit/cli_commands/transfer_pr_create_flow.py": {
        "restore --": "existing Kit command implementation; outside F4",
    },
    "src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py": {
        "switch": "existing Kit command implementation; outside F4",
        "pull --ff-only origin": "existing Kit command implementation; outside F4",
    },
    "src/agentic_project_kit/cli_commands/transfer_repo_pre_pr.py": {
        "rebase": "existing Kit command implementation; outside F4",
        "add": "existing Kit command implementation; outside F4",
        "branch": "existing guarded Kit branch cleanup (merged-PR check); outside F4",
        "push origin --delete": "existing guarded Kit branch cleanup (merged-PR check); outside F4",
    },
}


def _signature(constants: list[str]) -> str | None:
    if not constants or constants[0] not in MUTATING_VERBS:
        return None
    verb = constants[0]
    flags = constants[1:]
    if verb in READ_ONLY_FLAGS and flags and all(flag in READ_ONLY_FLAGS[verb] for flag in flags):
        return None
    shape = [verb]
    for token in flags:
        if not (token.startswith("-") or token in {"origin", "main"}) or len(shape) == 3:
            break
        shape.append(token)
    return " ".join(shape)


def _leading_constants(elements: list[ast.expr]) -> list[str]:
    values: list[str] = []
    for element in elements:
        if not (isinstance(element, ast.Constant) and isinstance(element.value, str)):
            break
        values.append(element.value)
    return values


def _direct_git_mutations(path: Path) -> set[str]:
    found: set[str] = set()
    for node in ast.walk(ast.parse(path.read_text(encoding="utf-8"))):
        if isinstance(node, (ast.List, ast.Tuple)):
            constants = _leading_constants(list(node.elts))
            if len(constants) >= 2 and constants[0] == "git":
                signature = _signature(constants[1:])
                if signature:
                    found.add(signature)
        if isinstance(node, ast.Call):
            func = node.func
            name = func.id if isinstance(func, ast.Name) else func.attr if isinstance(func, ast.Attribute) else ""
            if "git" not in name.lower():
                continue
            for argument in node.args:
                if isinstance(argument, (ast.List, ast.Tuple)):
                    signature = _signature(_leading_constants(list(argument.elts)))
                    if signature:
                        found.add(signature)
    return found


def test_direct_git_mutations_in_tools_and_cli_commands_are_reviewed() -> None:
    actual: dict[str, set[str]] = {}
    for root in SCANNED_ROOTS:
        for path in sorted(root.rglob("*.py")):
            mutations = _direct_git_mutations(path)
            if mutations:
                actual[path.relative_to(REPO_ROOT).as_posix()] = mutations

    unreviewed = {
        path: sorted(mutations - set(ALLOWED_DIRECT_GIT_MUTATIONS.get(path, {})))
        for path, mutations in actual.items()
        if mutations - set(ALLOWED_DIRECT_GIT_MUTATIONS.get(path, {}))
    }
    stale = {
        path: sorted(set(allowed) - actual.get(path, set()))
        for path, allowed in ALLOWED_DIRECT_GIT_MUTATIONS.items()
        if set(allowed) - actual.get(path, set())
    }
    assert unreviewed == {}, "Route these git mutations through Kit primitives or review them here"
    assert stale == {}, "Remove allow-list entries that no longer exist"


@pytest.mark.parametrize("path", ["tools/next-step.py", "tools/workflow_runner.py", "src/agentic_project_kit/cli_commands/workflow.py"])
def test_workflow_paths_have_no_direct_remote_mutation_or_branch_deletion(path: str) -> None:
    mutations = _direct_git_mutations(REPO_ROOT / path)
    forbidden = sorted(m for m in mutations if m.startswith(("push", "branch", "reset", "rebase", "merge", "tag")))
    assert forbidden == []


def _load_next_step():
    spec = importlib.util.spec_from_file_location("next_step_tool_f4", REPO_ROOT / "tools" / "next-step.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _load_workflow_runner():
    spec = importlib.util.spec_from_file_location("workflow_runner_f4", REPO_ROOT / "tools" / "workflow_runner.py")
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _git(cwd: Path, *args: str) -> str:
    completed = subprocess.run(
        ["git", "-c", "user.email=kit@example.invalid", "-c", "user.name=Kit Test", *args],
        cwd=cwd,
        text=True,
        capture_output=True,
        check=True,
    )
    return completed.stdout.strip()


@pytest.fixture
def evidence_repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    origin = tmp_path / "origin.git"
    repo = tmp_path / "repo"
    subprocess.run(["git", "init", "-q", "--bare", "-b", "main", str(origin)], check=True)
    repo.mkdir()
    _git(repo, "init", "-q", "-b", "main")
    (repo / ".gitignore").write_text("tmp/\n.agentic/tmp/\n", encoding="utf-8")
    (repo / ".agentic").mkdir()
    (repo / ".agentic" / "workflow_state").write_text("UPLOAD\n", encoding="utf-8")
    (repo / "docs" / "reports").mkdir(parents=True)
    (repo / "docs" / "reports" / "CURRENT_WORKFLOW_OUTPUT.md").write_text("# Current workflow output\n", encoding="utf-8")
    (repo / "README.md").write_text("repo\n", encoding="utf-8")
    _git(repo, "add", ".")
    _git(repo, "commit", "-q", "-m", "base")
    _git(repo, "remote", "add", "origin", str(origin))
    _git(repo, "push", "-q", "-u", "origin", "main")
    _git(repo, "remote", "set-head", "origin", "main")
    evidence_dir = repo / "tmp" / "agent-evidence"
    evidence_dir.mkdir(parents=True)
    (evidence_dir / "workflow-output-20261016-120000.md").write_text("evidence\n", encoding="utf-8")
    monkeypatch.chdir(repo)
    return repo


def test_evidence_branch_commits_only_evidence_and_pushes_through_kit(evidence_repo: Path) -> None:
    module = _load_next_step()

    branch = module.create_evidence_branch("CLEANUP")

    committed = set(_git(evidence_repo, "show", "--name-only", "--format=", branch).splitlines())
    assert committed == {"tmp/agent-evidence/workflow-output-20261016-120000.md"}
    assert _git(evidence_repo, "ls-remote", "--heads", "origin", branch).endswith(f"refs/heads/{branch}")
    assert _git(evidence_repo, "rev-parse", "main") == _git(evidence_repo, "rev-parse", "origin/main")


def test_evidence_branch_refuses_foreign_staged_changes(evidence_repo: Path) -> None:
    module = _load_next_step()
    (evidence_repo / "README.md").write_text("unreviewed change\n", encoding="utf-8")
    _git(evidence_repo, "add", "README.md")

    with pytest.raises(SystemExit, match="index already holds staged changes: README.md"):
        module.create_evidence_branch("CLEANUP")

    assert _git(evidence_repo, "branch", "--show-current") == "main"
    assert _git(evidence_repo, "ls-remote", "--heads", "origin", "temp/*") == ""


def test_evidence_branch_refuses_to_publish_unpushed_commits(evidence_repo: Path) -> None:
    module = _load_next_step()
    _git(evidence_repo, "switch", "-q", "-c", "work")
    (evidence_repo / "README.md").write_text("local only\n", encoding="utf-8")
    _git(evidence_repo, "commit", "-q", "-am", "unpublished")

    with pytest.raises(SystemExit, match="1 commit\\(s\\) not on any remote"):
        module.create_evidence_branch("UPLOADED")

    assert _git(evidence_repo, "ls-remote", "--heads", "origin", "temp/*") == ""


def test_cleanup_removes_evidence_branch_through_kit_primitives(evidence_repo: Path) -> None:
    module = _load_next_step()
    branch = module.create_evidence_branch("CLEANUP")

    module.step_cleanup()

    assert _git(evidence_repo, "branch", "--show-current") == "main"
    assert _git(evidence_repo, "branch", "--list", branch) == ""
    assert _git(evidence_repo, "ls-remote", "--heads", "origin", branch) == ""
    assert (evidence_repo / ".agentic" / "workflow_state").read_text(encoding="utf-8").strip() == "IDLE"


def test_cleanup_refuses_option_like_branch_names(evidence_repo: Path) -> None:
    module = _load_next_step()
    branch_file = evidence_repo / "tmp" / "agent-evidence" / "latest-branch.txt"
    branch_file.write_text("-Cmain\n", encoding="utf-8")

    with pytest.raises(SystemExit, match="unsafe branch name"):
        module.step_cleanup()


@pytest.mark.parametrize("value", ["-Cmain", "--orphan=x", "origin/main", "refs/heads/main", "a..b", "x y"])
def test_workflow_runner_rejects_option_like_work_branch(value: str) -> None:
    runner = _load_workflow_runner()

    with pytest.raises(runner.WorkflowFailure, match="Unsafe work_branch"):
        runner._step_command("git_switch_work_branch", {"work_branch": value})
    with pytest.raises(runner.WorkflowFailure, match="Unsafe base_branch"):
        runner._step_command("git_switch_main", {"base_branch": value})


def test_workflow_runner_separates_branch_from_options() -> None:
    runner = _load_workflow_runner()

    assert runner._step_command("git_switch_work_branch", {"work_branch": "feature/x"}) == ["git", "switch", "--", "feature/x"]
    assert runner._step_command("git_switch_main", {}) == ["git", "switch", "--", "main"]
