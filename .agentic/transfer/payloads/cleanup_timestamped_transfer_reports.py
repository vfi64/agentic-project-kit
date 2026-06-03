from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

TIMESTAMPED_REPORT_RE = re.compile(r"^20\d{6}T\d{6}Z-[0-9a-f]{8}-.+\.(json|log)$")
REPORT_DIRS = (
    Path("docs/reports/transfer_runs"),
    Path("docs/reports/terminal/transfer_handoff_reports"),
)


def run(argv: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        argv,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=False,
    )


def is_tracked(path: Path) -> bool:
    result = run(["git", "ls-files", "--error-unmatch", str(path)])
    return result.returncode == 0


def main() -> int:
    candidates: list[Path] = []
    for report_dir in REPORT_DIRS:
        if not report_dir.exists():
            continue
        for path in sorted(report_dir.iterdir()):
            if path.is_file() and TIMESTAMPED_REPORT_RE.match(path.name):
                candidates.append(path)

    removed_tracked: list[str] = []
    removed_untracked: list[str] = []
    for path in candidates:
        if is_tracked(path):
            result = run(["git", "rm", "-f", "--", str(path)])
            if result.returncode != 0:
                print(result.stdout, end="")
                print(result.stderr, end="", file=sys.stderr)
                return result.returncode
            removed_tracked.append(str(path))
        else:
            path.unlink(missing_ok=True)
            removed_untracked.append(str(path))

    print("TIMESTAMPED_TRANSFER_REPORT_CLEANUP")
    print(f"tracked_removed={len(removed_tracked)}")
    print(f"untracked_removed={len(removed_untracked)}")
    for path in removed_tracked:
        print(f"tracked={path}")
    for path in removed_untracked:
        print(f"untracked={path}")

    status = run(["git", "status", "--porcelain=v1"])
    if status.returncode != 0:
        print(status.stdout, end="")
        print(status.stderr, end="", file=sys.stderr)
        return status.returncode
    if not status.stdout.strip():
        print("cleanup_commit=not-needed")
        print("cleanup_push=not-needed")
        return 0

    commit = run(["git", "commit", "-m", "Remove generated timestamped transfer reports"])
    print(commit.stdout, end="")
    print(commit.stderr, end="", file=sys.stderr)
    if commit.returncode != 0:
        return commit.returncode

    branch = run(["git", "branch", "--show-current"])
    if branch.returncode != 0 or not branch.stdout.strip():
        print(branch.stdout, end="")
        print(branch.stderr, end="", file=sys.stderr)
        return branch.returncode or 2
    push = run(["git", "push", "origin", branch.stdout.strip()])
    print(push.stdout, end="")
    print(push.stderr, end="", file=sys.stderr)
    if push.returncode != 0:
        return push.returncode

    print("cleanup_commit=done")
    print("cleanup_push=done")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
