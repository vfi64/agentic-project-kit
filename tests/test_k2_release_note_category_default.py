"""K2 (V2): work finish always sets a release-note category; the branch kind is the default."""
import pytest

from agentic_project_kit.release_notes import RELEASE_NOTE_CATEGORIES
from agentic_project_kit.work_finish_metadata import default_release_note_category, prepare_work_finish_body


@pytest.mark.parametrize(("branch", "category"), [
    ("feature/x", "Added"), ("fix/x", "Fixed"), ("docs/x", "Docs"), ("ci/x", "Tests / Gates"),
    ("release/1.4.0", "Release"), ("codex/demo", "Changed"), ("", "Changed"),
])
def test_branch_kind_decides_the_default(branch, category):
    assert default_release_note_category(branch) == category
    assert category in RELEASE_NOTE_CATEGORIES and category != "Unclassified"


def test_default_is_written_when_nothing_else_is_given():
    body = prepare_work_finish_body("T", default_category=default_release_note_category("fix/a"))
    assert body.splitlines()[0] == "release-note-category: Fixed"


def test_explicit_value_and_body_marker_override_the_default():
    assert prepare_work_finish_body("T", release_note_category="Docs", default_category="Fixed").startswith(
        "release-note-category: Docs")
    assert prepare_work_finish_body("T", body="release-note-category: Governance\nx", default_category="Fixed").startswith(
        "release-note-category: Governance")
