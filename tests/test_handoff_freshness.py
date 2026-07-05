from pathlib import Path

from agentic_project_kit.handoff_freshness import (
    assess_handoff_prompt_freshness,
    render_freshness_guard,
)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_handoff_freshness_guard_reports_stale_successor_prompt(tmp_path: Path) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr690.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for old commit abc6900\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for abc6900\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for abc6900\n")
    data = {
        "safe_state": {"commit": "abc6900"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr690.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="def7010",
    )

    assert any("not represented by handoff safe/admin state" in warning for warning in warnings)
    assert any("does not mention current handoff commit marker" in warning for warning in warnings)


def test_handoff_freshness_guard_accepts_current_admin_evidence_state(tmp_path: Path) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr704.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for def7040\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for def7040\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for def7040\n")
    data = {
        "safe_state": {"commit": "abc6900"},
        "administrative_evidence_state": {"current_head": "def7040"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr704.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="def7040",
    )

    assert warnings == []


def test_handoff_freshness_guard_accepts_administrative_refresh_commit_after_state_refresh(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr709.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for ef43055\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for ef43055\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for ef43055\n")
    data = {
        "safe_state": {"commit": "ef43055"},
        "administrative_evidence_state": {"current_head": "ef43055"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr709.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="abc7100",
        current_subject="Refresh handoff state after PR709 (#710)",
    )

    assert warnings == []


def test_handoff_freshness_guard_still_rejects_non_admin_commit_after_state_refresh(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr709.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for ef43055\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for ef43055\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for ef43055\n")
    data = {
        "safe_state": {"commit": "ef43055"},
        "administrative_evidence_state": {"current_head": "ef43055"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr709.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="abc7110",
        current_subject="Add another registry consumer (#711)",
    )

    assert any("not represented by handoff safe/admin state" in warning for warning in warnings)
    assert any("does not mention current handoff commit marker" in warning for warning in warnings)


def test_handoff_freshness_guard_uses_yaml_successor_override_when_it_is_latest(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    terminal_dir = tmp_path / "docs" / "reports" / "terminal"
    _write(tmp_path / "docs" / "STATUS.md", "status for e4b2ebe\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for e4b2ebe\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(terminal_dir / "post-pr809-kit-generated-successor-handoff.md", "stale prompt for c07f8ec\n")
    _write(
        terminal_dir / "post-pr809-successor-handoff-override.yaml",
        "successor_chat_handoff:\n  main_after_pr810: e4b2ebe\n",
    )
    data = {"safe_state": {"commit": "e4b2ebe"}}

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="e4b2ebe",
    )

    assert warnings == []


def test_handoff_freshness_guard_renders_prominent_warning() -> None:
    guard = render_freshness_guard(["current git HEAD def7010 is not represented"])

    assert "## Handoff Freshness Guard" in guard
    assert "WARNING" in guard
    assert "successor handoff prompt may be stale" in guard
    assert "docs/STATUS.md" in guard

def test_handoff_freshness_guard_accepts_freshly_rendered_successor_prompt_text(tmp_path: Path) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr876.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for abc8760\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for abc8760\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "old prompt without current marker\n")
    data = {
        "safe_state": {"commit": "safe8730"},
        "administrative_evidence_state": {"current_head": "abc8760"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr876.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="abc8760",
        successor_prompt_text="fresh prompt for abc8760\n",
    )

    assert warnings == []

def test_handoff_freshness_guard_accepts_administrative_github_merge_commit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr878.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for admin refresh 162fa44\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for admin refresh 162fa44\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for 162fa44\n")
    data = {
        "safe_state": {"commit": "5b30fe3"},
        "administrative_evidence_state": {"current_head": "162fa44"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr878.md",
        },
    }

    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_parent_commits",
        lambda project_root, commit: ["162fa44", "35918d9"],
    )

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="ce0ea15",
        current_subject="Merge pull request #878 from vfi64/docs/v044-post-pr877-handoff-refresh\n\nRefresh handoff state after PR877",
    )

    assert warnings == []


def test_handoff_freshness_guard_rejects_non_admin_github_merge_commit(
    tmp_path: Path,
    monkeypatch,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr878.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for admin refresh\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for admin refresh\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for 162fa44\n")
    data = {
        "safe_state": {"commit": "5b30fe3"},
        "administrative_evidence_state": {"current_head": "162fa44"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr878.md",
        },
    }

    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_parent_commits",
        lambda project_root, commit: ["162fa44", "abcdef0"],
    )

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="fedcba0",
        current_subject="Merge pull request #999 from vfi64/feature/product-change\n\nAdd product behavior",
    )

    assert any("not represented by handoff safe/admin state" in warning for warning in warnings)
    assert any("does not mention current handoff commit marker" in warning for warning in warnings)

def test_handoff_freshness_guard_accepts_bounded_administrative_merge_chain(
    tmp_path: Path,
    monkeypatch,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr879.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for admin merge chain 162fa44\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for admin merge chain 162fa44\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for 162fa44\n")
    data = {
        "safe_state": {"commit": "5b30fe3"},
        "administrative_evidence_state": {"current_head": "162fa44"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr879.md",
        },
    }

    parent_map = {
        "7acbd5d": ["ce0ea15", "7bd60fe"],
        "ce0ea15": ["162fa44", "35918d9"],
    }
    message_map = {
        "ce0ea15": "Merge pull request #878 from vfi64/docs/v044-post-pr877-handoff-refresh\n\nRefresh handoff state after PR877",
    }

    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_parent_commits",
        lambda project_root, commit: parent_map.get(commit, []),
    )
    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_commit_subject",
        lambda project_root, commit: message_map.get(commit, "").splitlines()[0],
    )
    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_commit_message",
        lambda project_root, commit: message_map.get(commit, ""),
    )

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="7acbd5d",
        current_subject="Merge pull request #879 from vfi64/fix/handoff-freshness-admin-merge-commit\n\nAccept administrative merge commits in handoff freshness guard",
        successor_prompt_text="fresh prompt for 162fa44\n",
    )

    assert warnings == []


def test_handoff_freshness_guard_rejects_product_merge_inside_admin_chain(
    tmp_path: Path,
    monkeypatch,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr879.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for product merge chain\n")
    _write(tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md", "handoff for product merge chain\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for 162fa44\n")
    data = {
        "safe_state": {"commit": "5b30fe3"},
        "administrative_evidence_state": {"current_head": "162fa44"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr879.md",
        },
    }

    parent_map = {
        "abc9999": ["prod888", "feature1"],
        "prod888": ["162fa44", "feature2"],
    }
    message_map = {
        "prod888": "Merge pull request #900 from vfi64/feature/product-change\n\nAdd product behavior",
    }

    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_parent_commits",
        lambda project_root, commit: parent_map.get(commit, []),
    )
    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_commit_subject",
        lambda project_root, commit: message_map.get(commit, "").splitlines()[0],
    )
    monkeypatch.setattr(
        "agentic_project_kit.handoff_freshness._git_commit_message",
        lambda project_root, commit: message_map.get(commit, ""),
    )

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="abc9999",
        current_subject="Merge pull request #901 from vfi64/docs/handoff-refresh\n\nRefresh handoff",
        successor_prompt_text="fresh prompt without abc9999\n",
    )

    assert any("not represented by handoff safe/admin state" in warning for warning in warnings)

def test_handoff_freshness_guard_warns_on_stale_operational_documents(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "after-pr1242.md"
    _write(tmp_path / "docs" / "STATUS.md", "status for stale PR1054\n")
    _write(
        tmp_path / "docs" / "handoff" / "CURRENT_HANDOFF.md",
        "handoff for stale PR1054\n",
    )
    _write(
        tmp_path / "docs" / "handoff" / "START_NEW_CHAT_PROMPT.md",
        "successor prompt instructions for stale PR1054\n",
    )
    _write(
        tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md",
        "bootstrap instructions for stale PR1054\n",
    )
    _write(
        tmp_path / "docs" / "planning" / "PROJECT_DIRECTION.yaml",
        "authority: docs/planning/PROJECT_DIRECTION.yaml\nsummary: stale PR1054\n",
    )
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt generated for 4bf3da29\n")
    data = {
        "safe_state": {"commit": "4bf3da29"},
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/after-pr1242.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="4bf3da29",
    )

    assert any("docs/STATUS.md" in warning for warning in warnings)
    assert any("docs/handoff/CURRENT_HANDOFF.md" in warning for warning in warnings)
    assert any("START_NEW_CHAT_PROMPT.md" in warning for warning in warnings)
    assert any("NEXT_CHAT_BOOTSTRAP.md" in warning for warning in warnings)
    assert not any("PROJECT_DIRECTION.yaml" in warning for warning in warnings)

def test_handoff_freshness_accepts_administrative_squash_refresh_subject(
    tmp_path: Path,
) -> None:
    handoff_path = tmp_path / ".agentic" / "handoff_state.yaml"
    prompt_path = tmp_path / "docs" / "reports" / "terminal" / "post-pr1245-successor-chat-handoff.md"
    for relative_path in (
        "docs/STATUS.md",
        "docs/handoff/CURRENT_HANDOFF.md",
        "docs/handoff/START_NEW_CHAT_PROMPT.md",
        "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    ):
        _write(tmp_path / relative_path, "administrative handoff marker e97af592\n")
    _write(handoff_path, "schema_version: 1\n")
    _write(prompt_path, "successor prompt for administrative marker e97af592\n")
    data = {
        "safe_state": {"commit": "7f5a3310"},
        "administrative_evidence_state": {
            "current_head": "e97af592",
            "allowed_after_safe_state": True,
            "latest_successor_prompt": "docs/reports/terminal/post-pr1245-successor-chat-handoff.md",
        },
        "handoff_maintenance": {
            "latest_successor_prompt": "docs/reports/terminal/post-pr1245-successor-chat-handoff.md",
        },
    }

    warnings = assess_handoff_prompt_freshness(
        data,
        handoff_path,
        current_head="a24e868b",
        current_subject="Refresh operational handoff after PR1245 (#1246)",
        successor_prompt_text="successor prompt for administrative marker e97af592\n",
    )

    assert warnings == []
