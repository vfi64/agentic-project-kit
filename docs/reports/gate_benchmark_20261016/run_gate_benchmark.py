#!/usr/bin/env python3
"""Gate benchmark, part 1: deterministic fault injection in an offline sandbox.

Plan step ``gate-and-context-benchmark`` (docs/planning/PROJECT_DIRECTION.yaml), part 1.
Each scenario injects one known fault into a disposable clone of the Kit repository and runs
the Kit gate that claims to catch it. A control run of the same gate on the clean sandbox must
pass, so a scenario counts as detected only when the gate stays quiet without the fault and
reports it with the fault (a gate that always fails detects nothing).

Measured per scenario: detected (bool), the reason marker the gate printed, control result,
gate wall time with and without the fault. Denominator: the scenarios in this file. The runs are
deterministic, so each scenario runs once.

The sandbox is a bare clone used as ``origin`` plus a working clone, both in a temporary
directory; nothing reaches the real repository or GitHub. The Kit under test is the one on PATH
(``agentic-kit``), normally the repository's editable install.

Usage, from the repository root:
    python docs/reports/gate_benchmark_20261016/run_gate_benchmark.py --out results.json
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

GIT_ENV = {
    "GIT_AUTHOR_NAME": "Gate Benchmark",
    "GIT_AUTHOR_EMAIL": "benchmark@example.invalid",
    "GIT_COMMITTER_NAME": "Gate Benchmark",
    "GIT_COMMITTER_EMAIL": "benchmark@example.invalid",
    "AGENTIC_KIT_INVOCATION_LEDGER": "0",
    "AGENTIC_KIT_SUPPRESS_LEGACY_PROFILE_WARNING": "1",
}


@dataclass(frozen=True)
class Scenario:
    scenario_id: str
    fault_class: str
    description: str
    gate: list[str]
    inject: Callable[[Path], None]
    marker: str
    prepare: Callable[[Path], None] | None = None
    detector: Callable[[str], bool] | None = None


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def _ack(root: Path) -> str:
    manifest = json.loads((root / "docs/reference/agentic-kit-commands.json").read_text(encoding="utf-8"))
    return f"COMMAND_MANIFEST_ACK {manifest['meta']['manifest_sha']}"


def _transfer_order(root: Path, actions: list[dict], *, ack: str | None = None, path: str = ".agentic/transfer/inbox/current.yaml") -> None:
    import yaml

    order = {
        "id": "benchmark-order",
        "title": "Benchmark order",
        "safety": "READ_ONLY",
        "report_path": "docs/reports/command_runs/benchmark-order.md",
        "actions": actions,
    }
    _write(root / path, (ack or _ack(root)) + "\n" + yaml.safe_dump(order, sort_keys=False))
    # transfer apply needs a clean worktree, so the order and its payloads are committed.
    _git(root, "add", "-A", "-f", *[part for part in (".agentic/transfer/inbox", "tmp") if (root / part).exists()])
    _git(root, "commit", "-q", "-m", "Queue benchmark order")


def _typed_order(root: Path, argv: list[str]) -> None:
    import yaml

    order = {
        "id": "benchmark-typed",
        "title": "Benchmark typed order",
        "safety": "READ_ONLY",
        "log_path": "docs/reports/terminal/benchmark-typed.log",
        "block_dirty_worktree": False,
        "steps": [{"kind": "command_argv", "label": "step", "argv": argv}],
    }
    _write(root / "tmp/benchmark-typed.yaml", yaml.safe_dump(order, sort_keys=False))


def _clean_transfer_order(root: Path) -> None:
    _transfer_order(root, [{"type": "run_command", "command": ["agentic-kit", "direction", "validate"]}])


def _replace(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if old not in text:
        raise RuntimeError(f"injection anchor not found in {path}: {old!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


def _stale_ack(root: Path) -> None:
    _transfer_order(
        root,
        [{"type": "run_command", "command": ["agentic-kit", "direction", "validate"]}],
        ack="COMMAND_MANIFEST_ACK 000000000000",
    )


def _wrapped_push(root: Path) -> None:
    _transfer_order(root, [{"type": "run_command", "command": ["env", "git", "push", "--force", "origin", "main"]}])


def _symlink_payload(root: Path) -> None:
    outside = root.parent / "outside-secret.txt"
    outside.write_text("SECRET\n", encoding="utf-8")
    (root / "tmp").mkdir(exist_ok=True)
    link = root / "tmp/payload-link"
    link.unlink(missing_ok=True)
    link.symlink_to(outside)
    _transfer_order(root, [{"type": "write_text_file", "target_path": "tmp/leak.txt", "payload_path": "tmp/payload-link"}])


def _clean_payload(root: Path) -> None:
    _write(root / "tmp/payload.txt", "benign\n")
    _transfer_order(root, [{"type": "write_text_file", "target_path": "tmp/out.txt", "payload_path": "tmp/payload.txt"}])


def _anchor(root: Path) -> str:
    return subprocess.run(["git", "rev-parse", "HEAD"], cwd=root, text=True, capture_output=True, check=True).stdout.strip()


ORDER_BRANCH = "benchmark/order"


def _remote_order(root: Path, anchor_length: int) -> None:
    """Commit an order on its own branch on top of the commit it names, and publish the branch."""
    import yaml

    _git(root, "switch", "-q", "-C", ORDER_BRANCH)
    anchor = _anchor(root)[:anchor_length]
    order = {
        "schema_version": 1,
        "kind": "llm_to_local_transfer_order",
        "id": "benchmark-remote-order",
        "status": "active",
        "branch": ORDER_BRANCH,
        "expected_current_head": anchor,
        "title": "Benchmark remote order",
        "safety": "READ_ONLY",
        "report_path": "docs/reports/command_runs/benchmark-remote-order.md",
        "actions": [{"type": "run_command", "command": ["agentic-kit", "direction", "validate"]}],
    }
    _write(root / ".agentic/transfer/inbox/current.yaml", _ack(root) + "\n" + yaml.safe_dump(order, sort_keys=False))
    _git(root, "add", ".agentic/transfer/inbox/current.yaml")
    _git(root, "commit", "-q", "-m", "Queue benchmark transfer order")
    _git(root, "push", "-q", "-f", "-u", "origin", ORDER_BRANCH)


def _short_anchor(root: Path) -> None:
    _remote_order(root, 7)


def _full_anchor(root: Path) -> None:
    _remote_order(root, 40)


def _typed_unlisted(root: Path) -> None:
    _typed_order(root, ["touch", "tmp/EXECUTED"])


def _typed_clean(root: Path) -> None:
    _typed_order(root, ["agentic-kit", "direction", "validate"])


def _release_drift(root: Path) -> None:
    path = root / ".agentic/handoff_state.yaml"
    text = path.read_text(encoding="utf-8")
    import re

    new = re.sub(r"(?m)^(\s+current_version:\s*).*$", r"\g<1>0.4.13", text, count=1)
    if new == text:
        raise RuntimeError("release.current_version not found")
    path.write_text(new, encoding="utf-8")


def _stale_agents_ack(root: Path) -> None:
    path = root / "AGENTS.md"
    text = path.read_text(encoding="utf-8")
    ack = _ack(root).split()[-1]
    if ack not in text:
        raise RuntimeError("manifest ACK not found in AGENTS.md")
    path.write_text(text.replace(ack, "000000000000"), encoding="utf-8")


def _invalid_direction_status(root: Path) -> None:
    _replace(root / "docs/planning/PROJECT_DIRECTION.yaml", "  status: planned\n", "  status: doing\n")


def _unregistered_runbook(root: Path) -> None:
    _write(root / "docs/workflow/BENCHMARK_UNREGISTERED.md", "Status: active\n\n# Unregistered runbook\n")


def _direct_git_push_in_tool(root: Path) -> None:
    path = root / "tools/next-step.py"
    text = path.read_text(encoding="utf-8")
    path.write_text(text + '\n\ndef _benchmark_fault() -> None:\n    run(["git", "push", "origin", "HEAD:main"])\n', encoding="utf-8")


def _main_commit(root: Path) -> None:
    _write(root / "BENCHMARK_CHANGE.txt", "change on main\n")


def _branch_commit(root: Path) -> None:
    _git(root, "switch", "-q", "-c", "benchmark/work")
    _write(root / "BENCHMARK_CHANGE.txt", "change on a work branch\n")


def _noop(root: Path) -> None:
    return None


SCENARIOS: tuple[Scenario, ...] = (
    Scenario("S01", "stale command authority", "transfer order with a stale COMMAND_MANIFEST_ACK",
             ["agentic-kit", "transfer", "apply"], _stale_ack, "ACK",
             prepare=_clean_transfer_order),
    Scenario("S02", "raw git bypass", "transfer run_command `env git push --force origin main`",
             ["agentic-kit", "transfer", "apply"], _wrapped_push,
             "raw git must go through the Kit wrappers", prepare=_clean_transfer_order),
    Scenario("S03", "path escape", "write_text_file payload is a symlink to a file outside the repository",
             ["agentic-kit", "transfer", "apply"], _symlink_payload,
             "symlink", prepare=_clean_payload),
    Scenario("S04", "stale order", "transfer order with a 7-character freshness anchor",
             ["agentic-kit", "transfer", "remote-next", ORDER_BRANCH, "--json"], _short_anchor,
             "freshness_anchor_not_full_commit_hash", prepare=_full_anchor),
    Scenario("S05", "order self-authorisation", "typed order runs a command outside the manifest without --allow-unlisted",
             ["agentic-kit", "work-order", "typed-run", "tmp/benchmark-typed.yaml", "--execute", "--json"], _typed_unlisted,
             "--allow-unlisted", prepare=_typed_clean),
    Scenario("S06", "projection drift", "handoff release block says 0.4.13 (HD-08 class)",
             ["agentic-kit", "audit-drift-signals", "--json"], _release_drift, "release_projection",
             detector=lambda out: json.loads(out)["signals"]["release_projection"]["status"] == "drift"),
    Scenario("S07", "stale entrypoint", "AGENTS.md carries a stale command-manifest ACK",
             ["agentic-kit", "audit-command-authority"], _stale_agents_ack, "COMMAND_AUTHORITY_TERM_MISSING"),
    Scenario("S08", "invalid planning state", "a plan item with an unknown status",
             ["agentic-kit", "direction", "validate"], _invalid_direction_status, "invalid-status"),
    Scenario("S09", "unregistered document", "new runbook under docs/workflow/ without registry entry",
             ["agentic-kit", "doc-registry", "check-unregistered", "--strict-scope"], _unregistered_runbook,
             "BENCHMARK_UNREGISTERED.md"),
    Scenario("S10", "direct git mutation", "a direct `git push` added to tools/next-step.py",
             [sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "tests/test_workflow_git_mutation_authority.py"],
             _direct_git_push_in_tool, "Route these git mutations through Kit primitives"),
    Scenario("S11", "commit on main", "`transfer commit` of a change while on main",
             ["agentic-kit", "transfer", "commit", "--message", "benchmark", "--path", "BENCHMARK_CHANGE.txt"],
             _main_commit, "Refusing to commit directly on main", prepare=_branch_commit),
)


def _safe(detector: Callable[[str], bool], output: str) -> bool:
    try:
        return bool(detector(output))
    except (ValueError, KeyError, TypeError):
        return False


def _git(root: Path, *args: str) -> None:
    subprocess.run(["git", *args], cwd=root, check=True, capture_output=True, env={**os.environ, **GIT_ENV})


KIT_BIN: Path | None = None


def _gate_env() -> dict[str, str]:
    env = {**os.environ, **GIT_ENV}
    if KIT_BIN is not None:
        env["PATH"] = f"{KIT_BIN}{os.pathsep}{env.get('PATH', '')}"
    return env


def _run(root: Path, argv: list[str]) -> tuple[int, str, float]:
    if argv and argv[0] == sys.executable and KIT_BIN is not None:
        argv = [str(KIT_BIN / "python"), *argv[1:]]
    started = time.monotonic()
    completed = subprocess.run(argv, cwd=root, text=True, capture_output=True, env=_gate_env(), timeout=900)
    return completed.returncode, completed.stdout + completed.stderr, round(time.monotonic() - started, 2)


def _reset(root: Path) -> None:
    _git(root, "switch", "-q", "-f", "main")
    _git(root, "reset", "--hard", "-q", "origin/main")
    subprocess.run(["git", "branch", "-q", "-D", "benchmark/work"], cwd=root, capture_output=True, check=False)
    _git(root, "clean", "-fdxq")
    (root.parent / "outside-secret.txt").unlink(missing_ok=True)
    _run(root, ["agentic-kit", "rules", "acknowledge"])


def build_sandbox(repo: Path, base: Path, ref: str = "HEAD") -> Path:
    origin = base / "origin.git"
    work = base / "work"
    subprocess.run(["git", "clone", "--quiet", "--bare", "--no-hardlinks", str(repo), str(origin)], check=True)
    if ref != "HEAD":
        commit = subprocess.run(["git", "rev-parse", f"{ref}^{{commit}}"], cwd=repo, text=True, capture_output=True, check=True).stdout.strip()
        subprocess.run(["git", "update-ref", "refs/heads/main", commit], cwd=origin, check=True)
    subprocess.run(["git", "clone", "--quiet", "--branch", "main", str(origin), str(work)], check=True)
    return work


def _kit_version() -> str:
    completed = subprocess.run(["agentic-kit", "--version"], text=True, capture_output=True, env=_gate_env(), check=False)
    return completed.stdout.strip()


def run_benchmark(repo: Path, only: set[str] | None = None, ref: str = "HEAD") -> dict:
    base = Path(tempfile.mkdtemp(prefix="kit-gate-benchmark-"))
    try:
        sandbox = build_sandbox(repo, base, ref)
        head = subprocess.run(["git", "rev-parse", "HEAD"], cwd=sandbox, text=True, capture_output=True, check=True).stdout.strip()
        results = []
        for scenario in SCENARIOS:
            if only and scenario.scenario_id not in only:
                continue
            _reset(sandbox)
            (scenario.prepare or _noop)(sandbox)
            control_rc, control_out, control_s = _run(sandbox, scenario.gate)
            seen = scenario.detector or (lambda out: scenario.marker in out)
            control_quiet = control_rc == 0 and not _safe(seen, control_out)
            _reset(sandbox)
            try:
                scenario.inject(sandbox)
            except RuntimeError as exc:
                results.append({"id": scenario.scenario_id, "fault_class": scenario.fault_class,
                                "description": scenario.description, "detected": False, "control_quiet": False,
                                "skipped": f"fault cannot be injected at this ref: {exc}", "fault_seconds": 0})
                continue
            fault_rc, fault_out, fault_s = _run(sandbox, scenario.gate)
            marker_seen = _safe(seen, fault_out)
            detected = marker_seen and control_quiet
            results.append({
                "id": scenario.scenario_id,
                "fault_class": scenario.fault_class,
                "description": scenario.description,
                "gate": " ".join(part if part != sys.executable else "python" for part in scenario.gate),
                "control_returncode": control_rc,
                "control_quiet": control_quiet,
                "control_seconds": control_s,
                "fault_returncode": fault_rc,
                "fault_marker": scenario.marker,
                "fault_marker_seen": marker_seen,
                "fault_seconds": fault_s,
                "detected": detected,
                "fault_output_tail": fault_out.strip().splitlines()[-6:],
                "control_output_tail": [] if control_quiet else control_out.strip().splitlines()[-6:],
            })
        detected = sum(1 for item in results if item["detected"])
        return {
            "schema_version": 1,
            "kind": "gate_benchmark_part1",
            "sandbox_ref": ref,
            "sandbox_head": head,
            "kit_under_test": _kit_version(),
            "scenario_count": len(results),
            "detected_count": detected,
            "detection_share": round(detected / len(results), 4) if results else None,
            "control_false_positive_count": sum(1 for item in results if not item["control_quiet"]),
            "skipped_count": sum(1 for item in results if item.get("skipped")),
            "gate_seconds_total": round(sum(item["fault_seconds"] for item in results), 2),
            "results": results,
        }
    finally:
        shutil.rmtree(base, ignore_errors=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--only", nargs="*", help="scenario ids to run")
    parser.add_argument("--ref", default="HEAD", help="repository ref the sandbox starts from, e.g. v1.0.25")
    parser.add_argument("--kit-bin", type=Path, help="bin directory of a venv whose agentic-kit and python are under test")
    args = parser.parse_args()
    global KIT_BIN
    KIT_BIN = args.kit_bin.resolve() if args.kit_bin else None
    report = run_benchmark(Path.cwd(), set(args.only) if args.only else None, args.ref)
    args.out.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    for item in report["results"]:
        if item.get("skipped"):
            print(f"{item['id']} skipped: {item['skipped']}")
            continue
        print(f"{item['id']} detected={item['detected']} control_quiet={item['control_quiet']} "
              f"control_rc={item['control_returncode']} fault_rc={item['fault_returncode']} {item['fault_seconds']}s")
    print(f"detected {report['detected_count']}/{report['scenario_count']}, "
          f"control false positives {report['control_false_positive_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
