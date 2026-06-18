from __future__ import annotations

from datetime import date
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SRC = REPO_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 1:
        print("usage: agentic-kit release-prep --version <version>")
        return 2
    version = args[0].removeprefix("v")
    from agentic_project_kit.release_prepare import prepare_release_state

    try:
        result = prepare_release_state(
            Path(".").resolve(),
            version=version,
            date=date.today().isoformat(),
        )
    except ValueError as exc:
        print(str(exc))
        return 2
    for changed_path in result.changed_paths:
        print(f"CHANGED: {changed_path}")
    if not result.changed_paths:
        print(f"Release metadata already prepared for v{version}")
    else:
        print(f"Prepared release metadata for v{version} on {result.date}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
