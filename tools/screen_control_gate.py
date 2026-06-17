#!/usr/bin/env python3
"""Portable screen-control gate runner.

Runs the same validation family as the legacy shell helper without relying on
shell pipelines or tee. Output is streamed to stdout and captured in
Screen-Control_Output.txt by default.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class GateCommand:
    label: str
    argv: tuple[str, ...]


def default_commands(python_executable: str) -> list[GateCommand]:
    return [
        GateCommand("pytest", (python_executable, "-m", "pytest", "-q")),
        GateCommand("ruff", (python_executable, "-m", "ruff", "check", ".")),
        GateCommand("check-docs", ("./.venv/bin/agentic-kit", "check-docs")),
        GateCommand("doctor", ("./.venv/bin/agentic-kit", "doctor")),
    ]


class Tee:
    def __init__(self, output_path: Path) -> None:
        self.output_path = output_path
        self.output_path.parent.mkdir(parents=True, exist_ok=True)
        self._file = self.output_path.open("w", encoding="utf-8")

    def write(self, text: str) -> None:
        sys.stdout.write(text)
        sys.stdout.flush()
        self._file.write(text)
        self._file.flush()

    def close(self) -> None:
        self._file.close()


def run_gate(commands: list[GateCommand], output_path: Path) -> int:
    tee = Tee(output_path)
    try:
        overall_rc = 0
        for command in commands:
            tee.write(f"=== {command.label}: {' '.join(command.argv)} ===\n")
            proc = subprocess.run(
                list(command.argv),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                check=False,
            )
            tee.write(proc.stdout)
            if proc.stdout and not proc.stdout.endswith("\n"):
                tee.write("\n")
            tee.write(f"=== {command.label}: rc={proc.returncode} ===\n")
            if proc.returncode != 0 and overall_rc == 0:
                overall_rc = proc.returncode
        tee.write(f"RESULT=SCREEN_CONTROL_GATE_DONE rc={overall_rc}\n")
        return overall_rc
    finally:
        tee.close()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run portable screen-control gates.")
    parser.add_argument(
        "--output",
        default="Screen-Control_Output.txt",
        help="Path for captured gate output.",
    )
    parser.add_argument(
        "--python",
        default="./.venv/bin/python",
        help="Python executable to use for pytest and ruff.",
    )
    args = parser.parse_args(argv)
    return run_gate(default_commands(args.python), Path(args.output))


if __name__ == "__main__":
    raise SystemExit(main())
