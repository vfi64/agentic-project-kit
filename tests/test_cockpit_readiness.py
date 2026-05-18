from agentic_project_kit.cockpit_readiness import (
    build_cockpit_readiness_rows,
    build_cockpit_readiness_summary,
    render_cockpit_readiness_markdown,
)


def test_cockpit_readiness_rows_are_static_metadata():
    rows = build_cockpit_readiness_rows()
    assert rows
    assert {row["name"] for row in rows} >= {"cockpit-readiness", "dev", "pr-cleanup", "release-verify", "finalize-guard"}
    assert all("safety_class" in row for row in rows)
    assert all("mutation_scope" in row for row in rows)


def test_cockpit_readiness_summary_rejects_read_only_mutation_scope():
    summary = build_cockpit_readiness_summary()
    assert summary["missing_outcomes"] == []
    assert summary["read_only_with_mutation"] == []
    assert summary["ready_for_read_only_cockpit"] is True


def test_cockpit_readiness_markdown_contains_safety_table():
    rendered = render_cockpit_readiness_markdown()
    assert "# Cockpit Readiness" in rendered
    assert "| Action | Safety class | Mutation scope | Dry-run | Outcomes |" in rendered
    assert "`cockpit-readiness`" in rendered
    assert "`finalize-guard`" in rendered
    assert "PASS_ALREADY_ON_MAIN" in rendered
