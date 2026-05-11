from agentic_project_kit.runtime_validator import (
    ValidationFinding,
    ValidationReport,
    ValidationSeverity,
    validate_required_sections,
)


def test_validation_report_ok_when_no_findings() -> None:
    report = ValidationReport(findings=())

    assert report.ok is True


def test_validation_report_not_ok_when_error_finding_exists() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(
                code="missing_required_section",
                message="Missing required section: Final Answer",
            ),
        )
    )

    assert report.ok is False


def test_validation_report_ok_with_warning_only() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(
                code="soft_notice",
                message="Optional section is absent",
                severity=ValidationSeverity.WARNING,
            ),
        )
    )

    assert report.ok is True


def test_validate_required_sections_accepts_complete_text() -> None:
    report = validate_required_sections(
        "Plan\nSolution\nCheck\nFinal Answer",
        ("Plan", "Solution", "Check", "Final Answer"),
    )

    assert report.ok is True
    assert report.findings == ()


def test_validate_required_sections_reports_missing_sections_deterministically() -> None:
    report = validate_required_sections(
        "Plan\nFinal Answer",
        ("Plan", "Solution", "Check", "Final Answer"),
    )

    assert report.ok is False
    assert [finding.code for finding in report.findings] == [
        "missing_required_section",
        "missing_required_section",
    ]
    assert [finding.message for finding in report.findings] == [
        "Missing required section: Solution",
        "Missing required section: Check",
    ]


def test_validation_report_to_dict_is_json_safe_and_deterministic() -> None:
    report = ValidationReport(
        findings=(
            ValidationFinding(
                severity=ValidationSeverity.ERROR,
                code="missing_required_section",
                message="Missing required section: Solution",
            ),
        )
    )

    assert report.to_dict() == {
        "ok": False,
        "findings": [
            {
                "severity": "error",
                "code": "missing_required_section",
                "message": "Missing required section: Solution",
            }
        ],
    }
