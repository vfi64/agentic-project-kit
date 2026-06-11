from pathlib import Path

import pytest
import yaml

from agentic_project_kit.operational_handoff_projection import (
    load_operational_handoff_state,
    render_current_operational_handoff_state,
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
