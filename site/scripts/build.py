from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys


REPO_ROOT = Path(__file__).resolve().parents[2]
SRC = REPO_ROOT / "src"
if SRC.exists():
    sys.path.insert(0, SRC.as_posix())

from agentic_project_kit.site_generator import build_docs_pages_fallback, build_site  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Build the generated project website.")
    parser.add_argument("--root", default=".", help="Repository root.")
    parser.add_argument("--output", default="site/dist", help="Generated site output directory.")
    parser.add_argument(
        "--docs-pages-fallback",
        action="store_true",
        help="Write docs/index.html and docs/site/ for legacy /docs GitHub Pages source.",
    )
    parser.add_argument("--json", action="store_true", help="Print a bounded build summary as JSON.")
    parser.add_argument("--full-json", action="store_true", help="Print the full build result as JSON.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    if args.docs_pages_fallback:
        result = build_docs_pages_fallback(root)
        if args.full_json:
            print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
        elif args.json:
            print(json.dumps(_docs_pages_summary(result.as_dict()), indent=2, sort_keys=True))
        else:
            print(f"DOCS_PAGES_FALLBACK_STATUS={result.status}")
            print(f"DOCS_ROOT={result.docs_root}")
            print(f"FILE_COUNT={len(result.files)}")
            for blocker in result.blockers:
                print(f"BLOCKER={blocker}")
        return result.returncode

    output = Path(args.output)
    if not output.is_absolute():
        output = root / output
    result = build_site(root, output_dir=output)
    if args.full_json:
        print(json.dumps(result.as_dict(), indent=2, sort_keys=True))
    elif args.json:
        print(json.dumps(_summary(result.as_dict()), indent=2, sort_keys=True))
    else:
        print(f"SITE_BUILD_STATUS={result.status}")
        print(f"OUTPUT_DIR={result.output_dir}")
        print(f"FILE_COUNT={len(result.files)}")
        for blocker in result.report.blockers:
            print(f"BLOCKER={blocker}")
    return result.returncode


def _summary(data: dict[str, object]) -> dict[str, object]:
    report = data.get("report") if isinstance(data.get("report"), dict) else {}
    catalog = report.get("command_catalog") if isinstance(report.get("command_catalog"), dict) else None
    claims = report.get("claim_report") if isinstance(report.get("claim_report"), dict) else None
    if catalog is not None:
        catalog = {key: value for key, value in catalog.items() if key != "entries"}
    if claims is not None:
        claims = {key: value for key, value in claims.items() if key != "claims"}
    return {
        "schema_version": data.get("schema_version"),
        "kind": data.get("kind"),
        "status": data.get("status"),
        "output_dir": data.get("output_dir"),
        "file_count": data.get("file_count"),
        "files": data.get("files"),
        "metadata": report.get("metadata"),
        "command_catalog": catalog,
        "claim_report": claims,
        "blocker_count": report.get("blocker_count"),
        "blockers": report.get("blockers"),
    }


def _docs_pages_summary(data: dict[str, object]) -> dict[str, object]:
    site_build = data.get("site_build") if isinstance(data.get("site_build"), dict) else {}
    return {
        "schema_version": data.get("schema_version"),
        "kind": data.get("kind"),
        "status": data.get("status"),
        "docs_root": data.get("docs_root"),
        "site_subdir": data.get("site_subdir"),
        "file_count": data.get("file_count"),
        "files": data.get("files"),
        "blocker_count": data.get("blocker_count"),
        "blockers": data.get("blockers"),
        "site_build": _summary(site_build),
    }


if __name__ == "__main__":
    raise SystemExit(main())
