from __future__ import annotations

import argparse
import json
import subprocess
import sys
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
import os

from agentic_project_kit.next_turn_evidence import commit_and_push_evidence, publish_and_stage_evidence, render_finalize_result
from agentic_project_kit.next_turn_slot import FIXED_SLOT_SCRIPT, FIXED_SLOT_YAML
from agentic_project_kit.work_order_validator import default_local_result_log_path
from agentic_project_kit.workspace import LEGACY_DEFAULTS, load_workspace

LATEST_TERMINAL_LOG = Path(
    os.environ.get(
        "AGENTIC_KIT_NEXT_TURN_LOG",
        (Path(LEGACY_DEFAULTS.tmp_root) / "next-turn-latest.log").as_posix(),
    )
)
LATEST_COMMAND_REPORT = Path(
    os.environ.get(
        "AGENTIC_KIT_NEXT_TURN_REPORT",
        (Path(LEGACY_DEFAULTS.tmp_root) / "next-turn-latest.json").as_posix(),
    )
)


@dataclass(frozen=True)
class NextTurnRunResult:
    command_id: str
    outcome: str
    exit_code: int
    script_path: str
    yaml_path: str
    terminal_log: str
    command_report: str
    timestamp_utc: str


def _command_id_from_yaml(path: Path) -> str:
    if not path.exists():
        return "next-turn"
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.startswith("command_id:"):
            return line.split(":", 1)[1].strip() or "next-turn"
    return "next-turn"


def run_fixed_slot(root: Path | str = ".") -> NextTurnRunResult:
    root_path = Path(root)
    yaml_path = root_path / FIXED_SLOT_YAML
    script_path = root_path / FIXED_SLOT_SCRIPT
    terminal_log = (
        root_path / LATEST_TERMINAL_LOG
        if LATEST_TERMINAL_LOG != Path(LEGACY_DEFAULTS.tmp_root) / "next-turn-latest.log"
        else default_local_result_log_path(root_path)
    )
    command_report = (
        root_path / LATEST_COMMAND_REPORT
        if LATEST_COMMAND_REPORT != Path(LEGACY_DEFAULTS.tmp_root) / "next-turn-latest.json"
        else load_workspace(root_path).tmp_file("next-turn-latest.json")
    )

    terminal_log.parent.mkdir(parents=True, exist_ok=True)
    command_report.parent.mkdir(parents=True, exist_ok=True)

    command_id = _command_id_from_yaml(yaml_path)

    if not yaml_path.exists() or not script_path.exists():
        result = NextTurnRunResult(
            command_id=command_id,
            outcome="FAIL_NO_FIXED_SLOT",
            exit_code=2,
            script_path=str(FIXED_SLOT_SCRIPT),
            yaml_path=str(FIXED_SLOT_YAML),
            terminal_log=str(terminal_log),
            command_report=str(command_report),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        terminal_log.write_text("NEXT_TURN_RUNNER\noutcome=FAIL_NO_FIXED_SLOT\n### RESULT: FAIL ###\n", encoding="utf-8")
        command_report.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result

    completed = subprocess.run(
        [sys.executable, str(script_path)],
        cwd=root_path,
        text=True,
        capture_output=True,
        check=False,
    )
    output = (completed.stdout or "") + (completed.stderr or "")
    terminal_log.write_text(output, encoding="utf-8")

    outcome = "PASS_EXECUTED" if completed.returncode == 0 else "FAIL_EXECUTED"
    result = NextTurnRunResult(
        command_id=command_id,
        outcome=outcome,
        exit_code=completed.returncode,
        script_path=str(FIXED_SLOT_SCRIPT),
        yaml_path=str(FIXED_SLOT_YAML),
        terminal_log=str(terminal_log),
        command_report=str(command_report),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    command_report.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    if outcome == "PASS_EXECUTED":
        yaml_path.unlink(missing_ok=True)
        script_path.unlink(missing_ok=True)
    return result


def render_result(result: NextTurnRunResult) -> str:
    status = "PASS" if result.outcome == "PASS_EXECUTED" else "FAIL"
    return "\n".join(
        [
            "NEXT_TURN_RUNNER",
            f"command_id={result.command_id}",
            f"outcome={result.outcome}",
            f"exit_code={result.exit_code}",
            f"terminal_log={result.terminal_log}",
            f"command_report={result.command_report}",
            f"subresult={status}",
        ]
    )


def work_result_from_outcome(outcome: str) -> str:
    return "PASS" if outcome == "PASS_EXECUTED" else "FAIL"


def publish_run_evidence(result: NextTurnRunResult, *, run_id: str, push: bool = True) -> str:
    plan = publish_and_stage_evidence(
        run_id=run_id,
        local_terminal_log=result.terminal_log,
        work_result=work_result_from_outcome(result.outcome),
    )
    finalize_result = commit_and_push_evidence(plan=plan, push=push)
    return render_finalize_result(finalize_result)


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-run")
    parser.add_argument("--publish-evidence", action="store_true")
    parser.add_argument("--run-id", default="")
    parser.add_argument("--no-push", action="store_true")
    args = parser.parse_args()
    result = run_fixed_slot()
    print(render_result(result))
    if args.publish_evidence:
        run_id = args.run_id or result.command_id
        print(publish_run_evidence(result, run_id=run_id, push=not args.no_push))
    return 0 if result.outcome == "PASS_EXECUTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
