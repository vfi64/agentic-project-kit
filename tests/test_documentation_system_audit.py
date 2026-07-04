import re
from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

import agentic_project_kit.documentation_system_audit as documentation_system_audit
from agentic_project_kit.cli import app
from agentic_project_kit.documentation_system_audit import (
    MANDATORY_ORDER,
    REQUIRED_DOCS,
    build_documentation_system_audit,
    render_documentation_system_audit,
)

ROOT = Path(__file__).resolve().parents[1]


def _stub_documentation_audit_dependencies(monkeypatch) -> None:
    monkeypatch.setattr(documentation_system_audit, "check_docs", lambda root: [])
    monkeypatch.setattr(
        documentation_system_audit,
        "build_doc_mesh_report",
        lambda root: SimpleNamespace(findings=()),
    )
    monkeypatch.setattr(
        documentation_system_audit,
        "build_doc_lifecycle_report",
        lambda root: SimpleNamespace(findings=()),
    )
    monkeypatch.setattr(
        documentation_system_audit,
        "build_documentation_registry_summary",
        lambda root: {
            "registry_path": "docs/DOCUMENTATION_REGISTRY.yaml",
            "version": 1,
            "document_count": 3,
            "broad_migration_allowed": False,
            "class_counts": {"planning": 1, "governance/system": 2},
        },
    )


def _write_documentation_audit_fixture(root: Path, *, mandatory_order: tuple[str, ...] = MANDATORY_ORDER) -> None:
    for rel in REQUIRED_DOCS:
        path = root / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"# {Path(rel).name}\n", encoding="utf-8")

    status = root / "docs/STATUS.md"
    status.write_text("PR #42 merged\nconcise pointers, not duplicate rule books\n", encoding="utf-8")
    handoff = root / "docs/handoff/CURRENT_HANDOFF.md"
    handoff.write_text(
        "PR #42 merged\n"
        ".agentic/compiled_agent_context.yaml\n"
        "FINAL_SUMMARY_CONTRACT.md\n"
        "CHAT_COMMUNICATION_CONTRACT.md\n"
        "CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md\n",
        encoding="utf-8",
    )
    compiled = root / ".agentic/compiled_agent_context.yaml"
    compiled.write_text(
        "mandatory_successor_chat_sources:\n"
        + "".join(f"  - {source}\n" for source in mandatory_order),
        encoding="utf-8",
    )


def _audit_snapshot(root: Path) -> dict:
    report = build_documentation_system_audit(root)
    return {
        "ok": report.ok,
        "dimensions": [
            {
                "id": dimension.name,
                "ok": dimension.ok,
                "review_only": dimension.review_only,
                "findings": list(dimension.findings),
            }
            for dimension in report.dimensions
        ],
    }


def test_documentation_system_audit_has_required_dimensions() -> None:
    report = build_documentation_system_audit(ROOT)
    names = [dimension.name for dimension in report.dimensions]
    assert names == [
        "Aktualität",
        "Vollständigkeit",
        "Korrektheit",
        "Redundanzfreiheit",
        "Stringenz der Dokumentenordnung",
        "Dokumentationsregistry",
        "Konsistenz",
    ]


def test_documentation_audit_findings_snapshot(tmp_path: Path, monkeypatch) -> None:
    _stub_documentation_audit_dependencies(monkeypatch)

    pass_root = tmp_path / "pass"
    _write_documentation_audit_fixture(pass_root)

    block_root = tmp_path / "block"
    wrong_order = (MANDATORY_ORDER[1], MANDATORY_ORDER[0], *MANDATORY_ORDER[2:])
    _write_documentation_audit_fixture(block_root, mandatory_order=wrong_order)
    (block_root / "docs/TEST_GATES.md").unlink()

    assert _audit_snapshot(pass_root) == {
        "ok": True,
        "dimensions": [
            {"id": "Aktualität", "ok": True, "review_only": False, "findings": []},
            {"id": "Vollständigkeit", "ok": True, "review_only": False, "findings": []},
            {"id": "Korrektheit", "ok": True, "review_only": False, "findings": []},
            {
                "id": "Redundanzfreiheit",
                "ok": True,
                "review_only": True,
                "findings": [
                    "semantic redundancy-free prose still requires advisory review; "
                    "this hard check only catches known structural duplication patterns"
                ],
            },
            {"id": "Stringenz der Dokumentenordnung", "ok": True, "review_only": False, "findings": []},
            {
                "id": "Dokumentationsregistry",
                "ok": True,
                "review_only": False,
                "findings": [
                    "registry=docs/DOCUMENTATION_REGISTRY.yaml",
                    "version=1",
                    "documents=3",
                    "broad_migration_allowed=False",
                    "class:planning=1",
                    "class:governance/system=2",
                ],
            },
            {"id": "Konsistenz", "ok": True, "review_only": False, "findings": []},
        ],
    }
    assert _audit_snapshot(block_root) == {
        "ok": False,
        "dimensions": [
            {"id": "Aktualität", "ok": True, "review_only": False, "findings": []},
            {
                "id": "Vollständigkeit",
                "ok": False,
                "review_only": False,
                "findings": ["missing required documentation file: docs/TEST_GATES.md"],
            },
            {"id": "Korrektheit", "ok": True, "review_only": False, "findings": []},
            {
                "id": "Redundanzfreiheit",
                "ok": True,
                "review_only": True,
                "findings": [
                    "semantic redundancy-free prose still requires advisory review; "
                    "this hard check only catches known structural duplication patterns"
                ],
            },
            {
                "id": "Stringenz der Dokumentenordnung",
                "ok": False,
                "review_only": False,
                "findings": [
                    "compiled agent context does not preserve the mandatory successor-chat source order",
                    "mandatory successor-chat source file missing: docs/TEST_GATES.md",
                ],
            },
            {
                "id": "Dokumentationsregistry",
                "ok": True,
                "review_only": False,
                "findings": [
                    "registry=docs/DOCUMENTATION_REGISTRY.yaml",
                    "version=1",
                    "documents=3",
                    "broad_migration_allowed=False",
                    "class:planning=1",
                    "class:governance/system=2",
                ],
            },
            {"id": "Konsistenz", "ok": True, "review_only": False, "findings": []},
        ],
    }


def test_documentation_system_audit_renderer_exposes_boundaries() -> None:
    report = build_documentation_system_audit(ROOT)
    rendered = render_documentation_system_audit(report)
    assert "Documentation system audit" in rendered
    assert "Redundanzfreiheit" in rendered
    assert "review-only boundary" in rendered
    assert "Overall:" in rendered


def test_documentation_system_audit_mandatory_order_is_complete() -> None:
    assert MANDATORY_ORDER == (
        ".agentic/compiled_agent_context.yaml",
        "docs/governance/FINAL_SUMMARY_CONTRACT.md",
        "docs/governance/CHAT_COMMUNICATION_CONTRACT.md",
        "docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md",
        "docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md",
        "docs/TEST_GATES.md",
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
    )


def test_docs_audit_cli_is_registered() -> None:
    runner = CliRunner()
    result = runner.invoke(app, ["docs-audit"])
    assert "Documentation system audit" in result.output


def test_documentation_system_audit_checks_status_handoff_closeout_sync() -> None:
    report = build_documentation_system_audit(ROOT)
    rendered = render_documentation_system_audit(report)
    assert "CURRENT_HANDOFF.md missing current closeout marker" not in rendered
    assert "STATUS.md missing current closeout marker" not in rendered
    assert ".agentic/compiled_agent_context.yaml" in Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")
    assert "FINAL_SUMMARY_CONTRACT.md" in Path("docs/handoff/CURRENT_HANDOFF.md").read_text(encoding="utf-8")


def test_documentation_system_audit_pr_closeout_regex_matches_real_pr_numbers() -> None:
    source = Path("src/agentic_project_kit/documentation_system_audit.py").read_text(encoding="utf-8")
    assert 'r"PR #\\d+ merged"' in source
    assert 'r"PR #\\\\d+ merged"' not in source
    assert re.search(r"PR #\d+ merged", "PR #649 merged") is not None


def test_documentation_system_audit_enforces_status_headroom() -> None:
    source = Path("src/agentic_project_kit/documentation_system_audit.py").read_text(encoding="utf-8")
    assert "STATUS_HEADROOM_WORD_LIMIT = 4968" in source
    status_words = len(Path("docs/STATUS.md").read_text(encoding="utf-8").split())
    assert status_words <= 4968
    report = build_documentation_system_audit(ROOT)
    rendered = render_documentation_system_audit(report)
    assert "docs/STATUS.md exceeds headroom limit" not in rendered
