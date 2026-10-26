"""Canonical optional Pages projection shared by release metadata writers."""
from pathlib import Path

DOCS_PAGES_BUILD_SCRIPT = "site/scripts/build.py"
DOCS_PAGES_FALLBACK_EXPECTED_PATHS = ("docs/.nojekyll", "docs/index.html", "docs/site/")


def docs_pages_projection_paths(root: Path) -> tuple[str, ...]:
    """The Kit's self-hosted site is optional in consumer workspaces."""
    return DOCS_PAGES_FALLBACK_EXPECTED_PATHS if (root / DOCS_PAGES_BUILD_SCRIPT).is_file() else ()


def refresh_docs_pages_fallback(root: Path) -> tuple[tuple[str, ...], tuple[str, ...]]:
    if not docs_pages_projection_paths(root):
        return (), ()
    from agentic_project_kit.site_generator import build_docs_pages_fallback

    result = build_docs_pages_fallback(root)
    if not result.ok:
        return tuple(f"docs_pages_fallback:{blocker}" for blocker in result.blockers), ()
    paths = tuple(f"docs/{path}" for path in result.files)
    if any(path not in DOCS_PAGES_FALLBACK_EXPECTED_PATHS[:2]
           and (not path.startswith("docs/site/") or ".." in Path(path).parts)
           for path in paths):
        return ("docs_pages_fallback:output-path-escape",), ()
    return (), paths
