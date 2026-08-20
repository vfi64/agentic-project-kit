from __future__ import annotations

from pathlib import Path

from agentic_project_kit.site_generator import (
    DOCS_PAGES_FALLBACK_BUILD_COMMIT,
    build_site,
    _docs_pages_fallback_status_projection,
    _render_docs_pages_index,
)


REBUILD_HINT = "Run python site/scripts/build.py --docs-pages-fallback --json"


def test_docs_pages_fallback_projection_is_fresh(tmp_path: Path) -> None:
    root = Path(".").resolve()
    generated_site = tmp_path / "site"

    result = build_site(
        root,
        output_dir=generated_site,
        build_commit=DOCS_PAGES_FALLBACK_BUILD_COMMIT,
        status_projection=_docs_pages_fallback_status_projection(root),
    )

    assert result.ok, result.as_dict()
    committed_site = root / "docs" / "site"
    committed_files = tuple(
        sorted(path.relative_to(committed_site).as_posix() for path in committed_site.rglob("*") if path.is_file())
    )
    assert committed_files == result.files, REBUILD_HINT
    for relative_path in result.files:
        assert (committed_site / relative_path).read_bytes() == (
            generated_site / relative_path
        ).read_bytes(), f"docs/site/{relative_path} is stale. {REBUILD_HINT}"

    assert (root / "docs" / "index.html").read_text(encoding="utf-8") == _render_docs_pages_index(
        "site"
    ), REBUILD_HINT
    assert (root / "docs" / ".nojekyll").read_text(encoding="utf-8") == (
        "Generated marker: serve docs/ as static GitHub Pages content.\n"
    ), REBUILD_HINT
