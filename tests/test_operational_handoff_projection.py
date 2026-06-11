from pathlib import Path

import pytest
import yaml

from agentic_project_kit.operational_handoff_projection import (
    GENERATED_BLOCK_BEGIN,
    GENERATED_BLOCK_END,
    load_operational_handoff_state,
    render_current_operational_handoff_state,
    replace_generated_operational_handoff_block,
)


def _write_state(root: Path, data: dict) -> None:
    path = root / ".agentic" / "operational_handoff_state.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.safe_dump(data, sort_keys=False), encoding="utf-8")


def test_render_current_operational_handoff_state_from_yaml(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        {
            "schema_version": 1,
            "current_head": {
                "full": "abcdef123456",
                "short": "abcdef1",
                "subject": "Refresh operational handoff (#10)",
            },
            "last_substantive_work_state": {
                "full": "123456789abc",
                "short": "1234567",
                "subject": "Build product slice (#9)",
            },
            "administrative_context": ["Admin context line."],
            "freshness_policy": {"text": "Freshness policy line."},
            "next_safe_substantive_slice": {"text": "Next slice line."},
        },
    )

    rendered = "\n".join(render_current_operational_handoff_state(tmp_path))

    assert "Current verified main/admin HEAD is `abcdef123456` (`abcdef1`)" in rendered
    assert "Last substantive work state is `123456789abc` (`1234567`)" in rendered
    assert "Admin context line." in rendered
    assert "Freshness policy line." in rendered
    assert "Next slice line." in rendered


def test_operational_handoff_state_requires_schema_version(tmp_path: Path) -> None:
    _write_state(tmp_path, {"schema_version": 2})

    with pytest.raises(ValueError, match="schema_version"):
        load_operational_handoff_state(tmp_path)


def test_rendered_operational_handoff_state_has_generated_block_markers(tmp_path: Path) -> None:
    _write_state(
        tmp_path,
        {
            "schema_version": 1,
            "current_head": {
                "full": "abcdef123456",
                "short": "abcdef1",
                "subject": "Refresh operational handoff (#10)",
            },
            "last_substantive_work_state": {
                "full": "123456789abc",
                "short": "1234567",
                "subject": "Build product slice (#9)",
            },
        },
    )

    rendered = list(render_current_operational_handoff_state(tmp_path))

    assert rendered[0] == GENERATED_BLOCK_BEGIN
    assert rendered[-2] == GENERATED_BLOCK_END
    assert rendered.count(GENERATED_BLOCK_BEGIN) == 1
    assert rendered.count(GENERATED_BLOCK_END) == 1

def test_replace_generated_operational_handoff_block_preserves_curated_text() -> None:
    document = "\n".join(
        [
            "Curated introduction.",
            GENERATED_BLOCK_BEGIN,
            "old generated line",
            GENERATED_BLOCK_END,
            "Curated footer.",
            "",
        ]
    )
    replacement = [
        GENERATED_BLOCK_BEGIN,
        "new generated line",
        GENERATED_BLOCK_END,
        "",
    ]

    updated = replace_generated_operational_handoff_block(document, replacement)

    assert updated.startswith("Curated introduction.\n")
    assert "old generated line" not in updated
    assert "new generated line" in updated
    assert updated.endswith("Curated footer.\n")


def test_replace_generated_operational_handoff_block_requires_exactly_one_block() -> None:
    with pytest.raises(ValueError, match="exactly one"):
        replace_generated_operational_handoff_block("no generated block\n", [GENERATED_BLOCK_BEGIN, "x", GENERATED_BLOCK_END])

