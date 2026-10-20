from __future__ import annotations

import os
from pathlib import Path

import pytest

# Kit processes started by tests must not land in the developer's invocation ledger; the
# ledger tests enable it explicitly where they need it.
os.environ["AGENTIC_KIT_INVOCATION_LEDGER"] = "0"

from tests.marker_routing import marker_names_for_file


def pytest_addoption(parser: pytest.Parser) -> None:
    # Deterministic CI shards (agentic_project_kit.ci_test_shards): a test runs in shard
    # sha256(nodeid) % count; the required CI job checks that the shards add up to the suite.
    group = parser.getgroup("ci-shards")
    group.addoption("--shard-index", type=int, default=None, help="Run only this deterministic shard.")
    group.addoption("--shard-count", type=int, default=None, help="Number of deterministic shards.")
    group.addoption("--write-collected", default=None, help="Write the selected node ids, one per line.")


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    marker_cache: dict[Path, set[str]] = {}
    for item in items:
        path = Path(str(getattr(item, "path", getattr(item, "fspath", ""))))
        markers = marker_cache.setdefault(path, marker_names_for_file(path))
        for marker_name in sorted(markers):
            item.add_marker(getattr(pytest.mark, marker_name))
    index, count = config.getoption("--shard-index"), config.getoption("--shard-count")
    if index is None and count is None:
        return
    if index is None or count is None or count < 1 or not 0 <= index < count:
        raise pytest.UsageError("--shard-index and --shard-count go together, with 0 <= index < count")
    from agentic_project_kit.ci_test_shards import shard_of

    kept = [item for item in items if shard_of(item.nodeid, count) == index]
    deselected = [item for item in items if shard_of(item.nodeid, count) != index]
    if deselected:
        config.hook.pytest_deselected(items=deselected)
    items[:] = kept


def pytest_collection_finish(session: pytest.Session) -> None:
    target = session.config.getoption("--write-collected")
    if target:
        Path(target).write_text("".join(f"{item.nodeid}\n" for item in session.items), encoding="utf-8")
