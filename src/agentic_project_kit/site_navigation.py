"""One navigation order for every generated website page."""
from __future__ import annotations

from html import escape
from pathlib import PurePosixPath
from posixpath import relpath


SITE_LINKS = (
    ("index.html", "Overview"),
    ("understand/index.html", "Understand the Kit"),
    ("quickstart/index.html", "Quickstart"),
    ("use/index.html", "Use with Codex or Claude"),
    ("workflows/index.html", "Workflows"),
    ("commands/guided.html", "Commands"),
    ("evidence/index.html", "Evidence"),
    ("history/index.html", "History and architecture"),
)

SUBNAV_LINKS = {
    "Commands": (
        ("commands/guided.html", "Guided"),
        ("commands/diagnostics.html", "Diagnostics"),
        ("commands/index.html", "Complete reference"),
    ),
    "Evidence": (
        ("evidence/index.html", "Safety evidence"),
        ("claims/index.html", "Claims"),
    ),
}


def render_site_navigation(page: str) -> str:
    """Render relative site and section links with their exact current location."""
    parent = str(PurePosixPath(page).parent)
    links = []
    for target, label in SITE_LINKS:
        href = relpath(target, parent)
        current = ' aria-current="page"' if page == target else ''
        if page.startswith("commands/") and target == "commands/guided.html" and page != target:
            current = ' aria-current="location"'
        if page == "claims/index.html" and target == "evidence/index.html":
            current = ' aria-current="location"'
        links.append(f'<a href="{escape(href, quote=True)}"{current}>{escape(label)}</a>')
    navigation = '<nav class="topnav" aria-label="Site">' + ''.join(links) + '</nav>'
    group = "Commands" if page.startswith("commands/") else (
        "Evidence" if page in {"evidence/index.html", "claims/index.html"} else None
    )
    if group is None:
        return navigation
    sublinks = []
    for target, label in SUBNAV_LINKS[group]:
        href = relpath(target, parent)
        current = ' aria-current="page"' if page == target else ''
        if page.startswith("commands/detail-") and target == "commands/index.html":
            current = ' aria-current="location"'
        sublinks.append(f'<a href="{escape(href, quote=True)}"{current}>{escape(label)}</a>')
    return navigation + f'<nav class="subnav" aria-label="{group}">' + ''.join(sublinks) + '</nav>'
