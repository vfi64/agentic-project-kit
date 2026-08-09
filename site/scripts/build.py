from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if SRC.exists():
    sys.path.insert(0, SRC.as_posix())

from agentic_project_kit.site_generator import build_site  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the generated project website.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--output", default="site/dist", help="Generated site output directory.")
    parser.add_argument("--json", action="store_true", help="Print the build result as JSON.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    result = build_site(root, output_dir=output)
    if args.json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    else:
        print(f"SITE_BUILD_STATUS={result.status}")
        print(f"OUTPUT_DIR={result.output_dir}")
        print(f"FILE_COUNT={len(result.files)}")
        for blocker in result.report.blockers:
            print(f"BLOCKER={blocker}")
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
