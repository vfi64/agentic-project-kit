from __future__ import annotations

import os
from pathlib import Path

import pytest

# Kit processes started by tests must not land in the developer's invocation ledger; the
# ledger tests enable it explicitly where they need it.
os.environ["AGENTIC_KIT_INVOCATION_LEDGER"] = "0"

from tests.marker_routing import marker_names_for_file


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    marker_cache: dict[Path, set[str]] = {}
    for item in items:
        path = Path(str(getattr(item, "path", getattr(item, "fspath", ""))))
        markers = marker_cache.setdefault(path, marker_names_for_file(path))
        for marker_name in sorted(markers):
            item.add_marker(getattr(pytest.mark, marker_name))
