from __future__ import annotations

import os
import subprocess
import sys
from collections.abc import Sequence


def _env_with_src() -> dict[str, str]:
    env = os.environ.copy()
    current = env.get("PYTHONPATH")
    env["PYTHONPATH"] = "src" if not current else "src" + os.pathsep + current
    return env


def _section(title: str) -> None:
    print()
    print(title)


def _run(command: Sequence[str], *, env: dict[str, str] | None = None) -> int:
    completed = subprocess.run(list(command), env=env, check=False)
    return int(completed.returncode)


def run_local_feature_gate(args: Sequence[str] | None = None, *, include_pr_hygiene: bool = False) -> int:
    pytest_args = list(args or [])
    status = 0

    _section("### NS DEV LOCAL FEATURE GATE ###")
    print("Safety: local feature gate; no git pull, push, merge, tag, release, or branch deletion.")

    _section("### BRANCH / STATUS ###")
    status = _run(["git", "branch", "--show-current"]) or status
    status = _run(["git", "status", "--short"]) or status

    env = _env_with_src()

    _section("### PYTEST ###")
    status = _run([sys.executable, "-m", "pytest", "-q", *pytest_args], env=env) or status

    _section("### RUFF ###")
    status = _run([sys.executable, "-m", "ruff", "check", "."], env=env) or status

    _section("### CHECK DOCS ###")
    status = _run([sys.executable, "-m", "agentic_project_kit.cli", "check-docs"], env=env) or status

    _section("### DOCTOR ###")
    status = _run([sys.executable, "-m", "agentic_project_kit.cli", "doctor"], env=env) or status

    if include_pr_hygiene:
        _section("### PR HYGIENE ###")
        status = _run([sys.executable, "-m", "agentic_project_kit.cli", "pr-hygiene"], env=env) or status

    _section("### FINAL STATUS ###")
    status = _run(["git", "branch", "--show-current"]) or status
    status = _run(["git", "status", "--short"]) or status

    if status == 0:
        print("Local feature gate passed.")
        return 0
    print("Local feature gate failed.")
    return 1


def main(argv: Sequence[str] | None = None) -> int:
    raw_args = list(sys.argv[1:] if argv is None else argv)
    include_pr_hygiene = False
    if "--include-pr-hygiene" in raw_args:
        include_pr_hygiene = True
        raw_args.remove("--include-pr-hygiene")
    return run_local_feature_gate(raw_args, include_pr_hygiene=include_pr_hygiene)


if __name__ == "__main__":
    raise SystemExit(main())
