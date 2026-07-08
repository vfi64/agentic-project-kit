from pathlib import Path

CONTRACT = Path("docs/governance/RULE_REFRESH_HANDSHAKE_CONTRACT.md")
ARCHIVE = Path("docs/archive/RULE_REFRESH_HANDSHAKE_PLAN.md")


def test_rule_refresh_contract_declares_single_canonical_rule_source_model() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "The existing repository-backed rule sources remain the only canonical rule source of truth." in text
    assert "Snapshots are derived artifacts." in text
    assert "must never require manual rule duplication" in text
    assert "Markdown refresh files are human-readable projections." in text


def test_rule_refresh_contract_blocks_parallel_rule_state() -> None:
    text = CONTRACT.read_text(encoding="utf-8")

    assert "Do not introduce double-maintained rule or snapshot state." in text
    assert "no parallel manually maintained snapshot or GUI rule table" in text
    assert "If a proposed slice adds a manually edited snapshot" in text


def test_archived_rule_refresh_phase_one_hardens_existing_sources_before_snapshot_generation() -> None:
    text = ARCHIVE.read_text(encoding="utf-8")

    assert "Phase 1: Canonical Rule Source Hardening And Derived Snapshot Schema" in text
    assert "harden the existing canonical rule sources" in text
    assert "read-only validation expectations for existing YAML and governance sources" in text
    assert "schema work is framed as a generated derivative of canonical sources" in text


def test_archived_rule_refresh_execution_order_preserves_source_hardening_first() -> None:
    text = ARCHIVE.read_text(encoding="utf-8")

    assert "Harden and validate canonical sources before adding generated snapshot behavior broadly." in text
    assert "Does this preserve one canonical rule source model?" in text
