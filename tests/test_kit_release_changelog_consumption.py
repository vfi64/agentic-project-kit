"""GF-064: self-hosted Kit releases use lossless, creation-only consumption."""
from agentic_project_kit.release_prepare import prepare_release_state
from test_release_prepare_command import (
    SUMMARY_LINES, TARGET_DATE, TARGET_VERSION, _copy_release_state_files,
)


def test_kit_release_consumes_carried_bullets_with_dry_run_and_stable_rerun(tmp_path):
    project = _copy_release_state_files(tmp_path)
    path = project / "CHANGELOG.md"
    history = "## v0.4.11 - 2026-07-01\n\n- Previous release.\n"
    original = "## Unreleased\n\n" + "".join(f"- {s}\n" for s in SUMMARY_LINES) + "\n" + history
    path.write_text(original)
    options = dict(version=TARGET_VERSION, date=TARGET_DATE, summary_lines=SUMMARY_LINES)
    preview = prepare_release_state(project, **options, dry_run=True)
    assert "CHANGELOG.md" in preview.changed_paths
    assert path.read_text() == original
    prepare_release_state(project, **options)
    written = path.read_text()
    assert written.startswith(f"## Unreleased\n\n## v{TARGET_VERSION}")
    assert all(written.count(s) == 1 for s in SUMMARY_LINES)
    assert written.endswith(history)
    assert prepare_release_state(project, **options, dry_run=True).changed_paths == []
    assert prepare_release_state(project, **options).changed_paths == []
    assert path.read_text() == written


def test_kit_release_preserves_unmatched_and_duplicate_future_entries(tmp_path):
    project = _copy_release_state_files(tmp_path)
    path = project / "CHANGELOG.md"
    original = "## Unreleased\n\n" + "".join(f"- {s}\n" for s in SUMMARY_LINES)
    original += f"- {SUMMARY_LINES[0]}\n- Keep this future change.\n\n## v0.4.11 - 2026-07-01\n\n- Previous.\n"
    path.write_text(original)
    options = dict(version=TARGET_VERSION, date=TARGET_DATE, summary_lines=SUMMARY_LINES)
    prepare_release_state(project, **options)
    written = path.read_text()
    remaining = written.split(f"## v{TARGET_VERSION}", 1)[0]
    assert remaining.count(SUMMARY_LINES[0]) == 1
    assert SUMMARY_LINES[1] not in remaining
    assert "- Keep this future change." in remaining
    prepare_release_state(project, **options)
    assert path.read_text() == written
