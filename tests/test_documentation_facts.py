from pathlib import Path

from agentic_project_kit.documentation_facts import canonical_fact_findings


def _registry(*, managed_paths: list[str], review_paths: list[str]) -> dict[str, object]:
    return {
        "canonical_facts": [
            {
                "id": "project.package_name",
                "value": "agentic-project-kit",
                "managed_paths": managed_paths,
                "review_paths": review_paths,
            }
        ]
    }


def test_managed_projection_drift_is_blocking(tmp_path: Path) -> None:
    (tmp_path / "managed.md").write_text("old-name\n", encoding="utf-8")

    errors, findings = canonical_fact_findings(
        tmp_path,
        _registry(managed_paths=["managed.md"], review_paths=[]),
    )

    assert errors == ["canonical fact 'project.package_name' is missing from managed.md"]
    assert findings[0]["severity"] == "BLOCK"


def test_review_projection_drift_is_advisory(tmp_path: Path) -> None:
    (tmp_path / "review.md").write_text("project note\n", encoding="utf-8")

    errors, findings = canonical_fact_findings(
        tmp_path,
        _registry(managed_paths=[], review_paths=["review.md"]),
    )

    assert errors == []
    assert findings[0]["severity"] == "WARN"


def test_fact_paths_reject_absolute_and_parent_paths(tmp_path: Path) -> None:
    errors, _ = canonical_fact_findings(
        tmp_path,
        _registry(managed_paths=["/tmp/out.md", "../out.md"], review_paths=[]),
    )

    assert "canonical_facts[0].managed_paths must contain only relative paths" in errors
