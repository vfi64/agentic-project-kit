from __future__ import annotations

from pathlib import Path

REMOVED_REFERENCE_FRAGMENTS = [
    "DOCUMENT_ARTIFACT_GOVERNANCE_OS_PLAN.md",
    "V0.3.0_OUTPUT_REPAIR_PLAN.md",
    "V0.4_PROFESSIONAL_SINGLE_USER_STRATEGY.md",
]


def test_low_risk_obsolete_docs_not_referenced_outside_registry() -> None:
    search_roots = [
        Path("docs"),
        Path("src"),
        Path("tests"),
        Path("README.md"),
        Path("CHANGELOG.md"),
    ]

    ignored_exact = {
        "docs/DOCUMENTATION_REGISTRY.yaml",
        "docs/reference/agentic-kit-commands.json",
        "tests/test_dereference_low_risk_obsolete_docs.py",
    }

    for obsolete in REMOVED_REFERENCE_FRAGMENTS:
        hits: list[str] = []
        for root in search_roots:
            paths = [root] if root.is_file() else list(root.rglob("*"))
            for path in paths:
                if not path.is_file():
                    continue
                rel = path.as_posix()
                if (
                    rel in ignored_exact
                    or rel.startswith("docs/reports/")
                    or rel.startswith("src/")
                ):
                    continue
                try:
                    text = path.read_text(encoding="utf-8")
                except UnicodeDecodeError:
                    continue
                if obsolete in text:
                    hits.append(rel)

        assert not hits, f"{obsolete} still referenced in {hits}"
