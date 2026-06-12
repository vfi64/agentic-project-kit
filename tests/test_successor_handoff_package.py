from __future__ import annotations


def test_successor_execution_contract_projection_contains_hard_start_rules():
    from agentic_project_kit.successor_handoff_package import (
        build_execution_contract,
        render_successor_prompt,
    )

    context = {
        "repo": {
            "full_name": "vfi64/agentic-project-kit",
            "local_path": "/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit",
            "branch": "docs/post-pr1284-handoff-refresh",
            "head": "abc123",
            "origin_main": "abc123",
            "worktree_clean": False,
        },
        "dirty_paths": ("docs/STATUS.md",),
        "validation_report": {
            "status": "PASS",
            "path": ".agentic/successor_handoff_package/validation_report.json",
        },
        "short_term_memory": {
            "open_tasks": [
                "Finish successor execution contract MVP.",
            ],
            "recent_lessons": [
                "Dirty worktree must stop product work.",
            ],
        },
    }

    contract = build_execution_contract(context)

    assert contract["kind"] == "successor_execution_contract"
    assert contract["repo"]["head_matches_origin_main"] is True
    assert contract["repo"]["worktree_clean"] is False
    assert contract["repo"]["dirty_paths"] == ["docs/STATUS.md"]
    assert contract["validation"]["status"] == "PASS"

    rule_ids = {rule["rule_id"] for rule in contract["rules"]}
    assert "local-copy-paste-protocol" in rule_ids
    assert "strict-start-decision" in rule_ids
    assert "protected-file-preservation" in rule_ids

    prompt = render_successor_prompt(context)
    assert "Machine-readable execution contract" in prompt
    assert "Local copy-and-paste protocol" in prompt
    assert "head_matches_origin_main: `True`" in prompt
    assert "worktree_clean: `False`" in prompt
    assert "naked `python`" in prompt
    assert "naked `pytest`" in prompt
    assert "git add ." in prompt
    assert "{ ... } > \"$OUT\" 2>&1" in prompt



def test_write_successor_handoff_package_writes_execution_contract_json(tmp_path):
    import json

    from agentic_project_kit.successor_handoff_package import (
        DEFAULT_PACKAGE_DIR,
        write_successor_handoff_package,
    )

    result = write_successor_handoff_package(tmp_path, update_canonical_prompts=False)

    contract_path = tmp_path / DEFAULT_PACKAGE_DIR / "execution_contract.json"
    assert contract_path.exists()

    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    assert contract == result.execution_contract
    assert contract["kind"] == "successor_execution_contract"
    assert contract["validation"]["status"] == result.validation_report["status"]

    rule_ids = {rule["rule_id"] for rule in contract["rules"]}
    assert "local-copy-paste-protocol" in rule_ids
    assert "strict-start-decision" in rule_ids
    assert "protected-file-preservation" in rule_ids
