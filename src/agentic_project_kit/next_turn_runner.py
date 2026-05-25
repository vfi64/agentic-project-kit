from __future__ import annotations

import argparse
import json
import subprocess
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from agentic_project_kit.next_turn_slot import FIXED_SLOT_SCRIPT, FIXED_SLOT_YAML

LATEST_TERMINAL_LOG = Path("docs/reports/terminal/next-turn-latest.log")
LATEST_COMMAND_REPORT = Path("docs/reports/command_runs/next-turn-latest.json")


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
    terminal_log = root_path / LATEST_TERMINAL_LOG
    command_report = root_path / LATEST_COMMAND_REPORT

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
            terminal_log=str(LATEST_TERMINAL_LOG),
            command_report=str(LATEST_COMMAND_REPORT),
            timestamp_utc=datetime.now(timezone.utc).isoformat(),
        )
        terminal_log.write_text("NEXT_TURN_RUNNER\noutcome=FAIL_NO_FIXED_SLOT\n### RESULT: FAIL ###\n", encoding="utf-8")
        command_report.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
        return result

    completed = subprocess.run(
        ["python3", str(script_path)],
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
        terminal_log=str(LATEST_TERMINAL_LOG),
        command_report=str(LATEST_COMMAND_REPORT),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )
    command_report.write_text(json.dumps(asdict(result), indent=2, sort_keys=True) + "\n", encoding="utf-8")
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
            f"### RESULT: {status} ###",
        ]
    )


def main() -> int:
    parser = argparse.ArgumentParser(prog="next-turn-run")
    parser.parse_args()
    result = run_fixed_slot()
    print(render_result(result))
    return 0 if result.outcome == "PASS_EXECUTED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
