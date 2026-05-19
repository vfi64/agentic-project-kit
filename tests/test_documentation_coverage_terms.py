from pathlib import Path

import yaml


def test_documentation_coverage_terms_are_strings() -> None:
    data = yaml.safe_load(Path("docs/DOCUMENTATION_COVERAGE.yaml").read_text(encoding="utf-8"))
    offenders = []
    for rule in data.get("rules", []):
        rule_id = rule.get("id", "<unknown>")
        for document in rule.get("documents", []):
            doc_path = document.get("path", "<unknown>")
            for term in document.get("terms", []):
                if not isinstance(term, str):
                    offenders.append((rule_id, doc_path, term))
    assert offenders == []
