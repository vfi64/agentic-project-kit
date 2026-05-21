from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

from agentic_project_kit.audit_test_matrix import discover_gui_entry_tests, existing_contract_tests, pytest_argv_for

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run deterministic audit test matrices without shell xargs or hard-coded missing tests.")
    parser.add_argument("--matrix", choices=("gui-entry", "contracts", "all"), default="all")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--list-only", action="store_true")
    args = parser.parse_args(argv)
    root = Path.cwd()
    matrices: dict[str, list[str]] = {}
    if args.matrix in ("gui-entry", "all"):
        matrices["gui-entry"] = discover_gui_entry_tests(root)
    if args.matrix in ("contracts", "all"):
        matrices["contracts"] = existing_contract_tests(root)
    if args.json:
        print(json.dumps(matrices, indent=2))
    else:
        for name, paths in matrices.items():
            print(f"{name}_test_file_count={len(paths)}")
            for path in paths:
                print(path)
    if args.list_only:
        return 0 if all(matrices.values()) else 1
    status = 0
    for paths in matrices.values():
        try:
            pytest_args = [sys.executable, *pytest_argv_for(paths)]
        except ValueError:
            return 1
        completed = subprocess.run(pytest_args, cwd=root, check=False)
        status |= int(completed.returncode)
    return status

if __name__ == "__main__":
    raise SystemExit(main())
