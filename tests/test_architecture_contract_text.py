from pathlib import Path


def test_architecture_contract_defines_tier0_warn_execution_boundary() -> None:
    text = Path("docs/architecture/ARCHITECTURE_CONTRACT.md").read_text(encoding="utf-8")
    normalized = " ".join(text.split())

    assert "Tier-0 diagnostics are mutation-free integrity and audit checks" in normalized
    assert "they do not grant execution permission" in normalized
    assert "WARN` does not grant mutation or execution permission" in normalized
