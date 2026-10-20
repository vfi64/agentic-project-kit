"""Deterministic CI shards and the completeness check of the required test job.

The suite runs in three parallel jobs; the split is sha256(nodeid) % 3, so it depends only on
the collected tests. The required `test` job passes only when the shards ran exactly the full
collection: a missing, partial, reshuffled or failing shard fails the gate.
"""
import subprocess
import sys
from pathlib import Path

import pytest

from agentic_project_kit.ci_test_shards import check, shard_of

ROOT = Path(__file__).resolve().parents[1]
NODES = [f"tests/test_x.py::test_{i}" for i in range(40)] + ["tests/test_y.py::test_p[a b]", "tests/test_y.py::test_p[1-2]"]


def _junit(tests: int, failures: int = 0, errors: int = 0) -> str:
    return (f'<?xml version="1.0"?><testsuites><testsuite name="pytest" tests="{tests}" '
            f'failures="{failures}" errors="{errors}" skipped="0"></testsuite></testsuites>')


def _write(tmp_path, nodes=NODES, *, move=None, drop_shard=None, short_junit=None, failing=None):
    full = tmp_path / "full.txt"
    full.write_text("".join(f"{n}\n" for n in nodes))
    shards = tmp_path / "shards"
    for index in range(3):
        if index == drop_shard:
            continue
        mine = [n for n in nodes if shard_of(n) == index]
        if move is not None and index == shard_of(move):
            mine.remove(move)
        if move is not None and index == (shard_of(move) + 1) % 3:
            mine.append(move)
        base = shards / f"test-shard-{index}"
        base.mkdir(parents=True)
        (base / "collected.txt").write_text("".join(f"{n}\n" for n in mine))
        ran = len(mine) - (1 if index == short_junit else 0)
        (base / "junit.xml").write_text(_junit(ran, failures=1 if index == failing else 0))
    return full, shards


def test_the_split_is_deterministic_and_a_partition():
    assert [shard_of(n) for n in NODES] == [shard_of(n) for n in NODES]
    assert {shard_of(n) for n in NODES} == {0, 1, 2}
    with pytest.raises(ValueError):
        shard_of("x", 0)


def test_complete_shards_pass(tmp_path):
    result = check(*_write(tmp_path))
    assert result["result_status"] == "PASS", result["problems"]
    assert sum(s["collected"] for s in result["shards"]) == result["collected"] == len(NODES)


@pytest.mark.parametrize("damage,expected", [
    ({"move": NODES[0]}, "the rule assigns"),
    ({"drop_shard": 1}, "shard 1: report missing"),
    ({"short_junit": 2}, "JUnit ran"),
    ({"failing": 0}, "1 failures"),
])
def test_a_damaged_shard_fails_the_gate(tmp_path, damage, expected):
    result = check(*_write(tmp_path, **damage))
    assert result["result_status"] == "FAIL"
    assert any(expected in p for p in result["problems"]), result["problems"]


def test_an_empty_or_repeating_full_collection_fails(tmp_path):
    assert check(*_write(tmp_path, nodes=[]))["result_status"] == "FAIL"
    (tmp_path / "r").mkdir()
    assert check(*_write(tmp_path / "r", nodes=NODES + NODES[:1]))["result_status"] == "FAIL"


def _collect(*args, target=None):
    return subprocess.run([sys.executable, "-m", "pytest", "-q", "-p", "no:cacheprovider", "--collect-only",
                           "tests/test_ci_test_shards.py", *args], cwd=ROOT, capture_output=True, text=True)


def test_the_pytest_options_select_exactly_the_shard(tmp_path):
    full = tmp_path / "full.txt"
    assert _collect("--write-collected", str(full)).returncode == 0
    everything = full.read_text().splitlines()
    seen = []
    for index in range(3):
        part = tmp_path / f"{index}.txt"
        assert _collect("--shard-index", str(index), "--shard-count", "3", "--write-collected", str(part)).returncode in (0, 5)
        mine = part.read_text().splitlines()
        assert mine == [n for n in everything if shard_of(n) == index]
        seen += mine
    assert sorted(seen) == sorted(everything) and len(everything) > 5


@pytest.mark.parametrize("args", [["--shard-index", "0"], ["--shard-count", "3"], ["--shard-index", "3", "--shard-count", "3"]])
def test_incomplete_shard_options_are_a_usage_error(args):
    result = _collect(*args)
    assert result.returncode == 4, result.stdout[-500:] + result.stderr[-500:]
