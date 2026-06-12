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



def _minimal_successor_context():
    return {
        "repo": {
            "head": "abc123",
            "head_short": "abc123",
            "origin_main": "abc123",
            "branch": "main",
            "worktree_clean": True,
        },
        "long_term_memory": {"mandatory_sources": []},
    }


def test_validate_successor_outputs_requires_execution_contract_json():
    from agentic_project_kit.successor_handoff_package import validate_successor_outputs

    report = validate_successor_outputs(
        {"successor_prompt.md": "# prompt"},
        _minimal_successor_context(),
    )

    assert report["status"] == "FAIL"
    assert any(
        finding["code"] == "missing_execution_contract"
        for finding in report["findings"]
    )


def test_validate_successor_outputs_requires_execution_contract_rule_ids():
    import json

    from agentic_project_kit.successor_handoff_package import validate_successor_outputs

    report = validate_successor_outputs(
        {
            "successor_prompt.md": "# prompt",
            "execution_contract.json": json.dumps(
                {
                    "kind": "successor_execution_contract",
                    "rules": [{"rule_id": "local-copy-paste-protocol"}],
                }
            ),
        },
        _minimal_successor_context(),
    )

    assert report["status"] == "FAIL"
    missing = [
        finding
        for finding in report["findings"]
        if finding["code"] == "missing_execution_contract_rule_ids"
    ]
    assert missing
    assert "strict-start-decision" in missing[0]["message"]
    assert "protected-file-preservation" in missing[0]["message"]


def test_build_successor_handoff_package_validates_execution_contract():
    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    result = build_successor_handoff_package(".")

    assert result.validation_report["status"] == "PASS"
    assert result.execution_contract["kind"] == "successor_execution_contract"
    rule_ids = {rule["rule_id"] for rule in result.execution_contract["rules"]}
    assert "local-copy-paste-protocol" in rule_ids
    assert "strict-start-decision" in rule_ids
    assert "protected-file-preservation" in rule_ids



def test_validate_successor_outputs_blocks_naked_python_recommendation():
    import json

    from agentic_project_kit.successor_handoff_package import validate_successor_outputs

    contract = {
        "kind": "successor_execution_contract",
        "rules": [
            {"rule_id": "local-copy-paste-protocol"},
            {"rule_id": "strict-start-decision"},
            {"rule_id": "protected-file-preservation"},
        ],
    }

    report = validate_successor_outputs(
        {
            "successor_prompt.md": "```bash\npython script.py\n```",
            "execution_contract.json": json.dumps(contract),
        },
        _minimal_successor_context(),
    )

    assert report["status"] == "FAIL"
    assert any(
        finding["code"] == "forbidden_local_command_recommendation"
        for finding in report["findings"]
    )



def test_successor_handoff_package_e2e_start_decision_contract(tmp_path, monkeypatch):
    import json

    from agentic_project_kit import successor_handoff_package as package

    def fake_run_git(root, args):
        joined = " ".join(args)
        if joined == "rev-parse HEAD":
            return "abc123456789"
        if joined == "rev-parse origin/main":
            return "abc123456789"
        if joined == "status --short":
            return ""
        if joined == "branch --show-current":
            return "main"
        return "UNKNOWN"

    monkeypatch.setattr(package, "_run_git", fake_run_git)

    result = package.write_successor_handoff_package(
        tmp_path,
        update_canonical_prompts=False,
    )

    package_dir = tmp_path / package.DEFAULT_PACKAGE_DIR
    context_path = package_dir / "successor_context.yaml"
    manifest_path = package_dir / "source_manifest.json"
    validation_path = package_dir / "validation_report.json"
    contract_path = package_dir / "execution_contract.json"
    prompt_path = package_dir / "successor_prompt.md"

    for required_path in (
        context_path,
        manifest_path,
        validation_path,
        contract_path,
        prompt_path,
    ):
        assert required_path.exists(), required_path

    validation = json.loads(validation_path.read_text(encoding="utf-8"))
    contract = json.loads(contract_path.read_text(encoding="utf-8"))
    prompt = prompt_path.read_text(encoding="utf-8")

    assert validation == result.validation_report
    assert validation["status"] == "PASS"

    assert contract == result.execution_contract
    assert contract["kind"] == "successor_execution_contract"
    assert contract["repo"]["head_matches_origin_main"] is True
    assert contract["repo"]["worktree_clean"] is True

    rule_ids = {rule["rule_id"] for rule in contract["rules"]}
    assert {
        "local-copy-paste-protocol",
        "strict-start-decision",
        "protected-file-preservation",
    } <= rule_ids

    assert "Machine-readable execution contract" in prompt
    assert "Local copy-and-paste protocol" in prompt
    assert "validation_report.json" in prompt
    assert "execution_contract.json" in prompt
    assert "head_matches_origin_main: `True`" in prompt
    assert "worktree_clean: `True`" in prompt

    local_rule = next(
        rule
        for rule in contract["rules"]
        if rule["rule_id"] == "local-copy-paste-protocol"
    )
    forbidden = set(local_rule["forbidden"])
    assert "naked python" in forbidden
    assert "naked pytest" in forbidden
    assert "git add ." in forbidden

    strict_start = next(
        rule
        for rule in contract["rules"]
        if rule["rule_id"] == "strict-start-decision"
    )
    assert "validation_report.status is not PASS" in strict_start["stop_conditions"]
    assert "unexpected dirty paths exist" in strict_start["stop_conditions"]


def test_successor_prompt_requires_bootstrap_acceptance_gate() -> None:
    from agentic_project_kit.successor_handoff_package import (
        build_successor_handoff_package,
        render_start_prompt_from_context,
    )

    package = build_successor_handoff_package()
    prompt = render_start_prompt_from_context(package.context)
    assert "Zusätzliche Startbremse nach dem Bootstrap" in prompt
    assert "RESULT=NEW_CHAT_BOOTSTRAP_DONE" in prompt
    assert "Übergabe akzeptiert, keine Admin-Arbeit nötig." in prompt
    assert "prepare-successor-handoff --render-prompt` nicht erneut ausführen" in prompt
    assert "Beginne erst nach dieser Statusentscheidung mit neuer Arbeit." in prompt


def test_execution_contract_contains_bootstrap_acceptance_gate() -> None:
    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    package = build_successor_handoff_package()
    contract = package.execution_contract
    text = str(contract)
    assert "bootstrap_acceptance_gate" in text
    assert "RESULT=NEW_CHAT_BOOTSTRAP_DONE" in text
    assert "refresh_required=False" in text


def test_successor_package_refresh_does_not_rewrite_start_new_chat_prompt(tmp_path, monkeypatch) -> None:
    from agentic_project_kit import successor_handoff_package as package

    def fake_git(_root, args):
        if args == ["rev-parse", "HEAD"]:
            return "abc123"
        if args == ["rev-parse", "origin/main"]:
            return "abc123"
        if args == ["status", "--short"]:
            return ""
        if args == ["branch", "--show-current"]:
            return "main"
        return "UNKNOWN"

    monkeypatch.setattr(package, "_run_git", fake_git)

    start_prompt = tmp_path / "docs" / "handoff" / "START_NEW_CHAT_PROMPT.md"
    start_prompt.parent.mkdir(parents=True, exist_ok=True)
    start_prompt.write_text("KEEP EXISTING START PROMPT\n", encoding="utf-8")

    result = package.write_successor_handoff_package(tmp_path, update_canonical_prompts=True)

    assert result.validation_report["status"] == "PASS"
    assert start_prompt.read_text(encoding="utf-8") == "KEEP EXISTING START PROMPT\n"
    assert (tmp_path / package.NEXT_CHAT_BOOTSTRAP).exists()
    assert (tmp_path / package.CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT).exists()
    assert (tmp_path / package.DEFAULT_PACKAGE_DIR / "execution_contract.json").exists()

