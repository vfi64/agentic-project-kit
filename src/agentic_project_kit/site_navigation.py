"""One navigation order for every generated website page."""
from __future__ import annotations

from html import escape
from pathlib import PurePosixPath
from posixpath import relpath


SITE_LINKS = (
    ("index.html", "Overview"),
    ("understand/index.html", "Understand the Kit"),
    ("quickstart/index.html", "Quickstart"),
    ("workflows/index.html", "Workflows"),
    ("commands/guided.html", "Guided"),
    ("commands/diagnostics.html", "Diagnostics"),
    ("commands/index.html", "Complete"),
    ("evidence/index.html", "Safety evidence"),
    ("claims/index.html", "Claims"),
    ("history/index.html", "History and architecture"),
)


def render_site_navigation(page: str) -> str:
    """Render links relative to a generated page and mark its exact location."""
    parent = str(PurePosixPath(page).parent)
    links = []
    for target, label in SITE_LINKS:
        href = relpath(target, parent)
        current = ' aria-current="page"' if page == target else ''
        if page.startswith("commands/detail-") and target == "commands/index.html":
            current = ' aria-current="location"'
        links.append(f'<a href="{escape(href, quote=True)}"{current}>{escape(label)}</a>')
    return '<nav class="topnav" aria-label="Site">' + ''.join(links) + '</nav>'
