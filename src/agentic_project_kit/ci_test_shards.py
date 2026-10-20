"""Deterministic pytest shards for the Kit's own CI and their completeness check.

The full suite runs in SHARD_COUNT parallel CI jobs. A test belongs to exactly one shard,
chosen from the sha256 of its pytest node id, so the split depends only on the collected test
set, never on timing, worker order or the runner. The required `test` job accepts the shards
only when this check passes: every shard collected exactly the tests the rule assigns to it,
together they are the full collection, and each shard's JUnit report ran all of them with no
failure or error. A missing, partial or reshuffled shard therefore fails the gate.

    python -m agentic_project_kit.ci_test_shards check --full FULL --shards-dir DIR [--count N]

DIR holds `test-shard-<i>/collected.txt` (``pytest --collect-only --write-collected``) and
`test-shard-<i>/junit.xml` for every shard index.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
import xml.etree.ElementTree as ElementTree
from pathlib import Path

SHARD_COUNT = 3


def shard_of(nodeid: str, count: int = SHARD_COUNT) -> int:
    if count < 1:
        raise ValueError("shard count must be at least 1")
    return int(hashlib.sha256(nodeid.encode("utf-8")).hexdigest(), 16) % count


def collected_nodeids(text: str) -> list[str]:
    """Node ids, one per line, as ``pytest --collect-only --write-collected FILE`` writes them."""
    return [line.strip() for line in text.splitlines() if line.strip()]


def junit_totals(path: Path) -> dict[str, int]:
    root = ElementTree.parse(path).getroot()
    suites = [root] if root.tag == "testsuite" else list(root.iter("testsuite"))
    totals = {"tests": 0, "failures": 0, "errors": 0, "skipped": 0}
    for suite in suites:
        for key in totals:
            totals[key] += int(suite.get(key) or 0)
    return totals


def check(full: Path, shards_dir: Path, count: int = SHARD_COUNT) -> dict:
    problems: list[str] = []
    everything = collected_nodeids(full.read_text(encoding="utf-8"))
    if not everything:
        problems.append("the full collection is empty")
    if len(set(everything)) != len(everything):
        problems.append("the full collection repeats node ids")
    seen: set[str] = set()
    shards = []
    for index in range(count):
        base = shards_dir / f"test-shard-{index}"
        try:
            collected = collected_nodeids((base / "collected.txt").read_text(encoding="utf-8"))
            totals = junit_totals(base / "junit.xml")
        except (OSError, ElementTree.ParseError) as exc:
            problems.append(f"shard {index}: report missing or unreadable ({exc})")
            continue
        expected = [n for n in everything if shard_of(n, count) == index]
        if sorted(collected) != sorted(expected):
            problems.append(f"shard {index}: collected {len(collected)} tests, the rule assigns {len(expected)}")
        if set(collected) & seen:
            problems.append(f"shard {index}: tests also ran in another shard")
        seen |= set(collected)
        if totals["tests"] != len(collected):
            problems.append(f"shard {index}: JUnit ran {totals['tests']} of {len(collected)} collected tests")
        if totals["failures"] or totals["errors"]:
            problems.append(f"shard {index}: {totals['failures']} failures, {totals['errors']} errors")
        shards.append({"index": index, "collected": len(collected), **totals})
    if not problems and seen != set(everything):
        problems.append(f"the shards cover {len(seen)} of {len(everything)} collected tests")
    return {"kind": "ci_test_shard_check", "result_status": "FAIL" if problems else "PASS",
            "count": count, "collected": len(everything), "shards": shards, "problems": problems}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m agentic_project_kit.ci_test_shards")
    sub = parser.add_subparsers(dest="action", required=True)
    run = sub.add_parser("check")
    run.add_argument("--full", type=Path, required=True)
    run.add_argument("--shards-dir", type=Path, required=True)
    run.add_argument("--count", type=int, default=SHARD_COUNT)
    args = parser.parse_args(argv)
    result = check(args.full, args.shards_dir, args.count)
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["result_status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
