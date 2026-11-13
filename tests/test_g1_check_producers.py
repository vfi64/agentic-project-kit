"""G1 (owner 2026-11-13): no blocking check without a producer.

Every KIT-CHK id in src/ needs an entry in reference/check-producers.json; every entry needs an
existing agentic-kit producer command; an entry whose producer does not run before the check on
the standard path must say why and which correction closes it.
"""
from __future__ import annotations

import json
import re
from importlib.resources import files
from pathlib import Path

import typer

from agentic_project_kit.cli import app

SRC = Path(__file__).resolve().parents[1] / "src" / "agentic_project_kit"
ID = re.compile(r"\bKIT-CHK-[A-Z0-9]+(?:-[A-Z0-9]+)*\b")
REQUIRED = {"id", "scope", "check", "producer_command", "producer_runs_before_check", "migration",
            "autonomous_retry", "incidents"}


def _directory() -> dict:
    return json.loads(files("agentic_project_kit.reference").joinpath("check-producers.json").read_text("utf-8"))


def _ids_in_source() -> set[str]:
    found: set[str] = set()
    for path in SRC.rglob("*.py"):
        found |= set(ID.findall(path.read_text(encoding="utf-8")))
    return found


def _command_exists(words: list[str]) -> bool:
    command = typer.main.get_command(app)
    for word in words:
        sub = getattr(command, "commands", {}).get(word)
        if sub is None:
            return False
        command = sub
    return True


def test_every_check_id_in_the_source_has_a_directory_entry():
    entries = {entry["id"] for entry in _directory()["entries"]}
    missing = sorted(_ids_in_source() - entries)
    assert missing == [], f"G1: add these check ids to reference/check-producers.json: {missing}"


def test_every_kit_entry_is_used_in_the_source():
    used = _ids_in_source()
    stale = sorted(e["id"] for e in _directory()["entries"] if e["scope"] == "kit" and e["id"] not in used)
    assert stale == [], f"G1: directory entries without a check in src/: {stale}"


def test_every_entry_is_complete_and_names_an_existing_producer_command():
    ids = [entry["id"] for entry in _directory()["entries"]]
    assert len(ids) == len(set(ids))
    for entry in _directory()["entries"]:
        assert REQUIRED <= set(entry), entry["id"]
        assert _command_exists(entry["producer_command"]), (entry["id"], entry["producer_command"])
        if not entry["producer_runs_before_check"]:
            assert entry.get("exception", "").strip(), f"{entry['id']}: a producer off the standard path needs an exception"


def test_the_detector_rejects_an_unregistered_id(tmp_path):
    # Self-test of the law: a new id without an entry would be reported.
    entries = {entry["id"] for entry in _directory()["entries"]}
    assert "KIT-CHK-NEW-UNREGISTERED" not in entries
    assert ID.findall("if x:  # KIT-CHK-NEW-UNREGISTERED") == ["KIT-CHK-NEW-UNREGISTERED"]


def test_initial_entries_cover_the_incidents_of_the_first_slice():
    covered = {incident for entry in _directory()["entries"] for incident in entry["incidents"]}
    assert {"V1", "V2", "V6", "V7", "V11"} <= covered
