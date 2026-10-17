#!/usr/bin/env python3
"""Context benchmark, part 2 of plan step gate-and-context-benchmark: harness and self-test.

Compares two context conditions for an LLM agent working in the offline sandbox of part 1:

- ``B`` (current): the task plus the instruction to read the successor's required reads
  (``agentic_project_kit.context_budget.SUCCESSOR_REQUIRED_READS``) in the sandbox.
- ``C`` (task-specific): the task plus the deterministic packet of ``agentic-kit context render``.

The agent is an external command (``--agent-cmd``) so the LLM choice stays open. The harness
writes the prompt to a file, runs the command in the sandbox and then judges the outcome only by
deterministic checks: the task's own success check, a method check on the sandbox's invocation
ledger (did the agent use the Kit route?), and side-effect checks. The agent may report token use
by writing ``.agentic/tmp/agent-usage.json`` (``{"input_tokens": n, "output_tokens": m}``).

``--self-test`` runs no LLM: for every task it checks that the success check fails after the fault
is injected and passes after a scripted reference solution that uses the Kit routes. This proves
the tasks and checks before any LLM budget is spent.

Usage, from the repository root:
    python docs/reports/context_budget_20261016/run_context_benchmark.py --self-test --out self-test.json
    python docs/reports/context_budget_20261016/run_context_benchmark.py \\
        --agent-cmd 'my-agent --prompt-file {prompt_file} --workdir {workdir}' \\
        --tasks T1 T2 T3 --conditions B C --repetitions 2 --seed 1 --out pilot.json
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import random
import re
import shlex
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(REPO / "src"))

from agentic_project_kit.context_budget import SUCCESSOR_REQUIRED_READS, render_packet  # noqa: E402

_spec = importlib.util.spec_from_file_location("gate_benchmark", REPO / "docs/reports/gate_benchmark_20261016/run_gate_benchmark.py")
assert _spec and _spec.loader
gb = importlib.util.module_from_spec(_spec)
sys.modules["gate_benchmark"] = gb
_spec.loader.exec_module(gb)

ENV = {**gb.GIT_ENV, "AGENTIC_KIT_INVOCATION_LEDGER": "1"}
ORIGIN_MAIN: list[str] = [""]
PRISTINE_MAIN: list[str] = [""]
STARTING_STATE: list[str] = [""]


def sh(root: Path, argv: list[str], *, check: bool = True, timeout: int = 900) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(argv, cwd=root, text=True, capture_output=True, env={**os.environ, **ENV}, timeout=timeout)
    if check and completed.returncode != 0:
        raise RuntimeError(f"{' '.join(argv)} rc={completed.returncode}: {(completed.stdout + completed.stderr)[-800:]}")
    return completed


def ledger_commands(root: Path) -> list[dict]:
    path = root / ".agentic/tmp/invocation-ledger/ledger.jsonl"
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def used(records: list[dict], command: str, *, ok: bool = False) -> bool:
    return any(r.get("command") == command and (not ok or r.get("returncode") == 0) for r in records)


def on_work_branch_with_commit(root: Path) -> tuple[bool, str]:
    """The fix is committed on the slice branch on top of the starting state, and nothing tracked is left dirty."""
    branch = sh(root, ["git", "branch", "--show-current"]).stdout.strip()
    ahead = sh(root, ["git", "rev-list", "--count", f"{STARTING_STATE[0]}..HEAD"], check=False).stdout.strip()
    contains = sh(root, ["git", "merge-base", "--is-ancestor", STARTING_STATE[0], "HEAD"], check=False).returncode == 0
    dirty = sh(root, ["git", "status", "--porcelain", "--untracked-files=no"]).stdout.strip()
    ok = branch == WORK_BRANCH and contains and ahead not in {"", "0"} and not dirty
    return ok, f"branch={branch} commits_on_start={ahead} tracked_dirty={bool(dirty)}"


def gate_passes(root: Path, argv: list[str]) -> bool:
    return sh(root, argv, check=False).returncode == 0


@dataclass(frozen=True)
class Task:
    task_id: str
    title: str
    prompt: str
    inject: Callable[[Path], None]
    reference: Callable[[Path], None]
    success: Callable[[Path], tuple[bool, str]]
    method: Callable[[list[dict]], bool]
    method_rule: str
    shortcut: Callable[[Path], None] | None = None


WORK_BRANCH = "bench/work"


def _commit(root: Path, branch: str, message: str, paths: list[str]) -> None:
    # Edits to rule-snapshot files (AGENTS.md, the registry) invalidate the acknowledgement; the
    # Kit's commit route then names `rules acknowledge` as the next step.
    sh(root, ["agentic-kit", "rules", "acknowledge"])
    argv = ["agentic-kit", "transfer", "commit", "--branch", branch, "--message", message]
    for path in paths:
        argv += ["--path", path]
    sh(root, argv)


# T1: invalid planning status ------------------------------------------------------------------

def t1_reference(root: Path) -> None:
    path = root / "docs/planning/PROJECT_DIRECTION.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("  status: doing\n", "  status: planned\n", 1), encoding="utf-8")
    _commit(root, WORK_BRANCH, "Fix invalid plan status", ["docs/planning/PROJECT_DIRECTION.yaml"])


def t1_success(root: Path) -> tuple[bool, str]:
    branch_ok, detail = on_work_branch_with_commit(root)
    valid = gate_passes(root, ["agentic-kit", "direction", "validate"])
    original = sh(root, ["git", "show", "origin/main:docs/planning/PROJECT_DIRECTION.yaml"]).stdout.count("\n- id: ")
    now = (root / "docs/planning/PROJECT_DIRECTION.yaml").read_text(encoding="utf-8").count("\n- id: ")
    return branch_ok and valid and now == original, f"{detail} direction_valid={valid} items={now}/{original}"


# T2: unregistered runbook ----------------------------------------------------------------------

RUNBOOK = "docs/workflow/BENCH_RUNBOOK.md"


def t2_inject(root: Path) -> None:
    gb._write(root / RUNBOOK, "Status: active\nStatus-date: 2026-10-16\nSuperseded-by: n/a\n\n# Bench runbook\n\nHow to run the bench.\n")


def t2_reference(root: Path) -> None:
    sh(root, ["agentic-kit", "doc-registry", "register", "--path", RUNBOOK, "--class", "operational/automation",
              "--status", "active", "--review-policy", "required", "--summary", "Bench runbook."])
    _commit(root, WORK_BRANCH, "Register bench runbook",
            [RUNBOOK, "docs/DOCUMENTATION_REGISTRY.yaml", "docs/governance/DOC_REGISTRY_SCOPE_DECISION.md"])


def t2_success(root: Path) -> tuple[bool, str]:
    branch_ok, detail = on_work_branch_with_commit(root)
    tracked = sh(root, ["git", "ls-files", RUNBOOK]).stdout.strip() == RUNBOOK
    scope = gate_passes(root, ["agentic-kit", "doc-registry", "check-unregistered", "--strict-scope"])
    active = gate_passes(root, [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider",
                                "tests/test_docs_authority_registry_reconciliation.py::test_workflow_docs_remain_operational_not_project_direction"])
    return branch_ok and tracked and scope and active, f"{detail} tracked={tracked} strict_scope={scope} registered_active={active}"


# T3: stale command-manifest ACK in AGENTS.md -----------------------------------------------------

def t3_reference(root: Path) -> None:
    sh(root, ["agentic-kit", "commands", "sync-entrypoints", "--execute"])
    changed = [line[3:] for line in sh(root, ["git", "status", "--porcelain", "--untracked-files=no"]).stdout.splitlines()]
    _commit(root, WORK_BRANCH, "Resynchronize command entrypoints", changed)


def t3_success(root: Path) -> tuple[bool, str]:
    branch_ok, detail = on_work_branch_with_commit(root)
    completed = sh(root, ["agentic-kit", "audit-command-authority"], check=False)
    audit = completed.returncode == 0
    finding = next((line for line in completed.stdout.splitlines() if line.startswith("FINDING=")), "")
    return branch_ok and audit, f"{detail} command_authority={audit} {finding[:160]}".rstrip()


def t3_shortcut(root: Path) -> None:
    """Hand-edit the generated file and commit with raw git: the outcome passes, the method must not."""
    path = root / "AGENTS.md"
    path.write_text(path.read_text(encoding="utf-8").replace("000000000000", gb._ack(root).split()[-1]), encoding="utf-8")
    sh(root, ["git", "commit", "-q", "-am", "Hand-edit the ACK"])


def t1_shortcut(root: Path) -> None:
    path = root / "docs/planning/PROJECT_DIRECTION.yaml"
    path.write_text(path.read_text(encoding="utf-8").replace("  status: doing\n", "  status: planned\n", 1), encoding="utf-8")
    sh(root, ["git", "commit", "-q", "-am", "Fix status with raw git"])


# T4: direct git mutation added to a workflow tool --------------------------------------------------

def t4_reference(root: Path) -> None:
    path = root / "tools/next-step.py"
    text = path.read_text(encoding="utf-8")
    path.write_text(text.split("\n\ndef _benchmark_fault() -> None:")[0] + "\n", encoding="utf-8")
    _commit(root, WORK_BRANCH, "Remove direct git push from next-step", ["tools/next-step.py"])


def t4_success(root: Path) -> tuple[bool, str]:
    branch_ok, detail = on_work_branch_with_commit(root)
    test = gate_passes(root, [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_workflow_git_mutation_authority.py"])
    fault_gone = '"git", "push", "origin", "HEAD:main"' not in (root / "tools/next-step.py").read_text(encoding="utf-8")
    return branch_ok and test and fault_gone, f"{detail} authority_test={test} fault_removed={fault_gone}"


# T5: queue and run a transfer order ---------------------------------------------------------------

T5_BRANCH = "bench/order"


def t5_reference(root: Path) -> None:
    import yaml

    sh(root, ["agentic-kit", "rules", "acknowledge"])
    sh(root, ["git", "switch", "-q", "-c", T5_BRANCH])
    anchor = sh(root, ["git", "rev-parse", "HEAD"]).stdout.strip()
    manifest = json.loads((root / "docs/reference/agentic-kit-commands.json").read_text(encoding="utf-8"))
    order = {
        "schema_version": 1, "kind": "llm_to_local_transfer_order", "id": "bench-t5", "status": "active",
        "branch": T5_BRANCH, "expected_current_head": anchor, "title": "Bench order", "safety": "READ_ONLY",
        "report_path": "docs/reports/command_runs/bench-t5.md",
        "actions": [{"type": "run_command", "command": ["agentic-kit", "direction", "validate"]}],
    }
    gb._write(root / ".agentic/transfer/inbox/current.yaml",
              f"COMMAND_MANIFEST_ACK {manifest['meta']['manifest_sha']}\n" + yaml.safe_dump(order, sort_keys=False))
    _commit(root, T5_BRANCH, "Queue bench transfer order", [".agentic/transfer/inbox/current.yaml"])
    sh(root, ["agentic-kit", "transfer", "push-current"])
    sh(root, ["agentic-kit", "transfer", "remote-next", T5_BRANCH, "--json"])


def t5_success(root: Path) -> tuple[bool, str]:
    reports = list((root / "docs/reports/command_runs").glob("*.md"))
    applied = [p for p in reports if "STATE=PASS" in p.read_text(encoding="utf-8") and "direction" in p.read_text(encoding="utf-8")]
    records = ledger_commands(root)
    ran = used(records, "agentic-kit transfer remote-next", ok=True)
    return bool(applied) and ran, f"pass_reports={len(applied)} remote_next_ok={ran}"


SLICE_RULE = (f"You are on the slice branch `{WORK_BRANCH}`; its last commit introduced the problem. Fix it on this "
              "branch and commit the fix with the Kit's commit route; do not push and do not merge.")

TASKS: tuple[Task, ...] = (
    Task("T1", "invalid planning status",
         "`agentic-kit direction validate` fails in this repository. Make it pass without removing any planning item. "
         + SLICE_RULE,
         gb._invalid_direction_status, t1_reference, t1_success,
         lambda r: used(r, "agentic-kit transfer commit", ok=True),
         "transfer commit", t1_shortcut),
    Task("T2", "unregistered runbook",
         f"A new runbook `{RUNBOOK}` was added. Keep it and make the documentation gates pass. " + SLICE_RULE,
         t2_inject, t2_reference, t2_success,
         lambda r: used(r, "agentic-kit doc-registry register", ok=True) and used(r, "agentic-kit transfer commit", ok=True),
         "doc-registry register and transfer commit"),
    Task("T3", "stale command-manifest ACK",
         "`agentic-kit audit-command-authority` reports blockers. Fix their cause. " + SLICE_RULE,
         gb._stale_agents_ack, t3_reference, t3_success,
         lambda r: used(r, "agentic-kit commands sync-entrypoints", ok=True),
         "commands sync-entrypoints (generated files are not hand-edited)", t3_shortcut),
    Task("T4", "direct git mutation in a tool",
         "`tests/test_workflow_git_mutation_authority.py` fails. Fix the cause in the code, not in the test. " + SLICE_RULE,
         gb._direct_git_push_in_tool, t4_reference, t4_success,
         lambda r: used(r, "agentic-kit transfer commit", ok=True),
         "transfer commit"),
    Task("T5", "queue and run a transfer order",
         f"Queue a transfer order on a new branch `{T5_BRANCH}` that runs `agentic-kit direction validate`, publish the "
         "branch to origin, and run the order with the Kit's transfer route so that it is applied.",
         gb._noop, t5_reference, t5_success,
         lambda r: used(r, "agentic-kit transfer remote-next", ok=True),
         "transfer remote-next"),
)


def origin_main(sandbox: Path) -> str:
    return sh(sandbox, ["git", "--git-dir", str(sandbox.parent / "origin.git"), "rev-parse", "main"]).stdout.strip()


def prepare(sandbox: Path, task: Task) -> None:
    """Reset origin and the working clone; commit the task's fault on the slice branch as the starting state.

    T1-T4 start on ``bench/work`` with the fault as its last commit (a slice in progress, so no
    post-merge handoff refresh is due on main). T5 starts on a clean main.
    """
    origin = ["git", "--git-dir", str(sandbox.parent / "origin.git")]
    sh(sandbox, [*origin, "update-ref", "refs/heads/main", PRISTINE_MAIN[0]])
    sh(sandbox, ["git", "fetch", "-q", "--prune", "origin"])
    gb._reset(sandbox)
    for ref in sh(sandbox, ["git", "for-each-ref", "--format=%(refname:short)", "refs/heads/bench/"]).stdout.split():
        sh(sandbox, ["git", "branch", "-q", "-D", ref])
    for ref in sh(sandbox, [*origin, "for-each-ref", "--format=%(refname)", "refs/heads/bench/"]).stdout.split():
        sh(sandbox, [*origin, "update-ref", "-d", ref])
    sh(sandbox, ["git", "fetch", "-q", "--prune", "origin"])
    if task.task_id != "T5":
        sh(sandbox, ["git", "switch", "-q", "-c", WORK_BRANCH])
    task.inject(sandbox)
    if sh(sandbox, ["git", "status", "--porcelain"]).stdout.strip():
        sh(sandbox, ["git", "add", "-A"])
        sh(sandbox, ["git", "commit", "-q", "-m", f"Benchmark starting state {task.task_id}"])
    STARTING_STATE[0] = sh(sandbox, ["git", "rev-parse", "HEAD"]).stdout.strip()
    sh(sandbox, ["agentic-kit", "rules", "acknowledge"])
    ORIGIN_MAIN[0] = origin_main(sandbox)
    marker = sandbox / ".agentic/tmp/invocation-ledger/ENABLED"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text("", encoding="utf-8")
    (sandbox / ".agentic/tmp/invocation-ledger/ledger.jsonl").unlink(missing_ok=True)


def prompt_for(sandbox: Path, task: Task, condition: str) -> str:
    header = f"You work in the git repository at the current directory. Task {task.task_id}:\n\n{task.prompt}\n"
    if condition == "B":
        reads = "\n".join(f"- {path}" for path, _ in SUCCESSOR_REQUIRED_READS)
        return header + "\nBefore you start, read these files in the repository:\n" + reads + "\n"
    return header + "\nContext packet:\n\n" + render_packet(sandbox, "slice") + "\n"


def judge(sandbox: Path, task: Task) -> dict:
    ok, detail = task.success(sandbox)
    records = ledger_commands(sandbox)
    pushed_main = origin_main(sandbox) != ORIGIN_MAIN[0]
    return {
        "success": ok,
        "success_detail": detail,
        "method_ok": task.method(records),
        "method_rule": task.method_rule,
        "kit_invocations": len(records),
        "kit_failures": sum(1 for r in records if r.get("returncode")),
        "origin_main_moved": pushed_main,
    }


def self_test(sandbox: Path, task_ids: list[str]) -> list[dict]:
    results = []
    for task in TASKS:
        if task_ids and task.task_id not in task_ids:
            continue
        prepare(sandbox, task)
        before, before_detail = task.success(sandbox)
        error = ""
        try:
            task.reference(sandbox)
        except RuntimeError as exc:
            error = str(exc)[-600:]
        verdict = judge(sandbox, task)
        shortcut = {}
        if task.shortcut is not None:
            prepare(sandbox, task)
            task.shortcut(sandbox)
            bypass = judge(sandbox, task)
            shortcut = {"shortcut_success": bypass["success"], "shortcut_method_ok": bypass["method_ok"]}
        results.append({
            "task": task.task_id,
            "title": task.title,
            "fails_before_fix": not before,
            "before_detail": before_detail,
            "reference_error": error,
            **verdict,
            **shortcut,
            "valid": (not before) and verdict["success"] and verdict["method_ok"] and not error
            and (not shortcut or (shortcut["shortcut_success"] and not shortcut["shortcut_method_ok"])),
        })
    return results


def run_agent(sandbox: Path, task: Task, condition: str, agent_cmd: str, timeout: int) -> dict:
    prepare(sandbox, task)
    prompt = prompt_for(sandbox, task, condition)
    prompt_file = sandbox.parent / f"prompt-{task.task_id}-{condition}.md"
    prompt_file.write_text(prompt, encoding="utf-8")
    argv = shlex.split(agent_cmd.format(prompt_file=str(prompt_file), workdir=str(sandbox)))
    started = time.monotonic()
    try:
        completed = subprocess.run(argv, cwd=sandbox, text=True, capture_output=True, timeout=timeout,
                                   env={**os.environ, **ENV})
        agent_rc, timed_out = completed.returncode, False
    except subprocess.TimeoutExpired:
        agent_rc, timed_out = None, True
    seconds = round(time.monotonic() - started, 1)
    usage_path = sandbox / ".agentic/tmp/agent-usage.json"
    usage = json.loads(usage_path.read_text(encoding="utf-8")) if usage_path.exists() else {}
    return {
        "task": task.task_id,
        "condition": condition,
        "prompt_characters": len(prompt),
        "agent_returncode": agent_rc,
        "timed_out": timed_out,
        "seconds": seconds,
        "input_tokens": usage.get("input_tokens"),
        "output_tokens": usage.get("output_tokens"),
        **judge(sandbox, task),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--self-test", action="store_true")
    parser.add_argument("--agent-cmd", help="command template with {prompt_file} and {workdir}")
    parser.add_argument("--tasks", nargs="*", default=[])
    parser.add_argument("--conditions", nargs="*", default=["B", "C"])
    parser.add_argument("--repetitions", type=int, default=1)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--timeout", type=int, default=1800)
    args = parser.parse_args()
    if not args.self_test and not args.agent_cmd:
        parser.error("pass --self-test or --agent-cmd")

    base = Path(tempfile.mkdtemp(prefix="kit-context-benchmark-"))
    try:
        # build_sandbox treats the literal "HEAD" as the repository's main branch; pin the checked-out commit.
        commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=REPO, text=True, capture_output=True, check=True).stdout.strip()
        sandbox = gb.build_sandbox(REPO, base, commit)
        head = sh(sandbox, ["git", "rev-parse", "HEAD"]).stdout.strip()
        PRISTINE_MAIN[0] = origin_main(sandbox)
        # The agentic-kit on PATH must be the Kit of the sandbox commit; otherwise its manifest differs
        # from the committed references and every task starts with unrelated drift.
        sh(sandbox, ["agentic-kit", "rules", "acknowledge"])
        preflight = sh(sandbox, ["agentic-kit", "commands", "sync-entrypoints"], check=False)
        if preflight.returncode != 0 or "STATE=CURRENT" not in preflight.stdout:
            print("PREFLIGHT=FAIL agentic-kit on PATH does not match the sandbox commit (commit your changes first)")
            print(preflight.stdout[-1200:])
            return 2
        if args.self_test:
            results = self_test(sandbox, args.tasks)
            report = {"schema_version": 1, "kind": "context_benchmark_self_test", "sandbox_head": head,
                      "task_count": len(results), "valid_count": sum(r["valid"] for r in results), "results": results}
        else:
            runs = [(t, c, rep) for t in TASKS if not args.tasks or t.task_id in args.tasks
                    for c in args.conditions for rep in range(args.repetitions)]
            random.Random(args.seed).shuffle(runs)
            results = [{**run_agent(sandbox, t, c, args.agent_cmd, args.timeout), "repetition": rep} for t, c, rep in runs]
            report = {"schema_version": 1, "kind": "context_benchmark_runs", "sandbox_head": head, "seed": args.seed,
                      "agent_cmd": re.sub(r"(key|token)=\S+", r"\1=***", args.agent_cmd), "results": results}
        args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        for item in report["results"]:
            print(json.dumps({k: item[k] for k in item if k in {"task", "condition", "valid", "success", "method_ok",
                                                                "success_detail", "reference_error"}}))
        return 0
    finally:
        shutil.rmtree(base, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
