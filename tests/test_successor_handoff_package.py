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
    assert "successor_package_head_status=refresh_only_descendant" in prompt
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


def test_successor_handoff_artifacts_snapshot(tmp_path):
    import json

    from agentic_project_kit.successor_handoff_package import write_successor_handoff_package

    result = write_successor_handoff_package(tmp_path, update_canonical_prompts=True)

    generated_paths = sorted(
        path.relative_to(tmp_path).as_posix()
        for path in tmp_path.rglob("*")
        if path.is_file()
    )
    assert generated_paths == [
        "docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md",
        "docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "docs/reports/handoff-packages/latest/execution_contract.json",
        "docs/reports/handoff-packages/latest/source_manifest.json",
        "docs/reports/handoff-packages/latest/successor_context.yaml",
        "docs/reports/handoff-packages/latest/successor_prompt.md",
        "docs/reports/handoff-packages/latest/validation_report.json",
    ]

    package_dir = tmp_path / "docs" / "reports" / "handoff-packages" / "latest"
    context = json.loads((package_dir / "successor_context.yaml").read_text(encoding="utf-8"))
    source_manifest = json.loads((package_dir / "source_manifest.json").read_text(encoding="utf-8"))
    validation = json.loads((package_dir / "validation_report.json").read_text(encoding="utf-8"))
    execution_contract = json.loads((package_dir / "execution_contract.json").read_text(encoding="utf-8"))
    successor_prompt = (package_dir / "successor_prompt.md").read_text(encoding="utf-8")
    next_bootstrap = (tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md").read_text(encoding="utf-8")
    closeout_prompt = (
        tmp_path / "docs" / "handoff" / "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md"
    ).read_text(encoding="utf-8")

    assert result.output_dir.as_posix() == "docs/reports/handoff-packages/latest"
    assert context["kind"] == "successor_chat_context"
    assert {"repo", "long_term_memory", "short_term_memory", "handoff_validity"} <= set(context)
    assert source_manifest["kind"] == "successor_source_manifest"
    assert "sources" in source_manifest
    assert validation["kind"] == "successor_handoff_validation_report"
    assert {"status", "findings", "generated_head"} <= set(validation)
    assert execution_contract["kind"] == "successor_execution_contract"
    assert {"general_contract", "current_state_contract", "handoff_projection_contract", "rules"} <= set(
        execution_contract
    )
    assert "Machine-readable execution contract" in successor_prompt
    assert "# Successor Chat Prompt" in successor_prompt
    assert "Handoff package precedence" in successor_prompt
    assert "# NEXT CHAT BOOTSTRAP" in next_bootstrap
    assert "Successor handoff package" in next_bootstrap
    assert "### RESULT: PASS ###" in next_bootstrap
    assert "# Closeout Before Chat Switch Prompt" in closeout_prompt
    assert "agentic-kit transfer chat-switch-complete --render-prompt" in closeout_prompt



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
    from agentic_project_kit import __version__ as package_version
    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    result = build_successor_handoff_package(".")

    assert result.validation_report["status"] == "PASS"
    assert result.context["release"]["package_version"] == package_version
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


def test_bootstrap_acceptance_gate_is_projected_into_package_files() -> None:
    from agentic_project_kit.successor_handoff_package import build_successor_handoff_package

    package = build_successor_handoff_package()

    for text in (package.successor_prompt, package.next_chat_bootstrap):
        assert "Zusätzliche Startbremse nach dem Bootstrap" in text
        assert "RESULT=NEW_CHAT_BOOTSTRAP_DONE" in text
        assert "Übergabe akzeptiert, keine Admin-Arbeit nötig" in text

def test_next_chat_bootstrap_contains_handoff_freshness_marker():
    from agentic_project_kit.successor_handoff_package import (
        render_next_chat_bootstrap_from_context,
    )

    context = {
        "repo": {
            "full_name": "vfi64/agentic-project-kit",
            "local_path": "/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit",
            "branch": "main",
            "head": "1234567890abcdef",
            "head_short": "12345678",
            "origin_main": "1234567890abcdef",
            "worktree_clean": True,
        },
        "dirty_paths": (),
    }

    bootstrap = render_next_chat_bootstrap_from_context(context)

    assert "## Current verified repository state" in bootstrap
    assert "- HEAD: `1234567890abcdef` (`12345678`)" in bootstrap
    assert "- Handoff freshness marker: `12345678`" in bootstrap
    assert "## Bootstrap-Akzeptanzbremse" in bootstrap

def test_successor_execution_contract_separates_general_rules_from_current_state() -> None:
    from agentic_project_kit.successor_handoff_package import (
        GENERAL_CONTRACT_RULE_IDS,
        REQUIRED_EXECUTION_CONTRACT_RULE_IDS,
        build_execution_contract,
    )

    context = {
        "repo": {
            "full_name": "vfi64/agentic-project-kit",
            "local_path": "cd /path/to/agentic-project-kit",
            "branch": "feature/docs-reconciliation-active-obsolete-refs",
            "head": "feature-head",
            "origin_main": "main-head",
            "worktree_clean": True,
        },
        "short_term_memory": {
            "open_tasks": [{"id": "docs-reconciliation", "status": "active"}],
            "recent_lessons": ["current blocker belongs to current state"],
        },
        "validation_report": {"status": "PASS"},
        "dirty_paths": [],
    }

    contract = build_execution_contract(context)

    assert set(GENERAL_CONTRACT_RULE_IDS) <= set(REQUIRED_EXECUTION_CONTRACT_RULE_IDS)
    assert contract["general_contract"]["scope"] == "durable-agentic-kit-operating-model"
    assert contract["current_state_contract"]["scope"] == "current-continuation-state"
    assert contract["handoff_projection_contract"]["prompt_is_projection_only"] is True
    assert contract["handoff_projection_contract"]["machine_readable_files_take_precedence"] is True

    assert "docs/planning/PROJECT_DIRECTION.yaml" in contract["general_contract"]["source_authorities"]
    assert "docs/DOCUMENTATION_REGISTRY.yaml" in contract["general_contract"]["source_authorities"]
    assert contract["current_state_contract"]["repo"]["branch"] == "feature/docs-reconciliation-active-obsolete-refs"
    assert contract["current_state_contract"]["open_tasks"][0]["id"] == "docs-reconciliation"

    general_text = str(contract["general_contract"])
    assert "feature/docs-reconciliation-active-obsolete-refs" not in general_text
    assert "feature-head" not in general_text


def test_successor_execution_contract_contains_required_agentic_kit_rule_ids() -> None:
    from agentic_project_kit.successor_handoff_package import build_execution_contract

    context = {
        "repo": {
            "branch": "main",
            "head": "abc123",
            "origin_main": "abc123",
            "worktree_clean": True,
        },
        "short_term_memory": {"open_tasks": [], "recent_lessons": []},
        "validation_report": {"status": "PASS"},
    }

    contract = build_execution_contract(context)
    rule_ids = {rule["rule_id"] for rule in contract["rules"]}

    assert {
        "wrapper-first-complete-development-cycle",
        "successor-package-not-prompt-only",
        "documentation-authority-model",
        "repo-backed-rules-and-gates",
        "gc-retention-not-document-migration",
        "ns-legacy-not-active-control-plane",
        "generated-handoff-projection-update-policy",
        "patch-cycle-diagnostic-gate",
        "copy-paste-output-discipline",
    } <= rule_ids


def test_handoff_projection_contract_names_generated_paths_and_update_policy() -> None:
    from agentic_project_kit.successor_handoff_package import build_execution_contract

    contract = build_execution_contract(_minimal_successor_context())
    projection = contract["handoff_projection_contract"]

    assert "docs/handoff/NEXT_CHAT_BOOTSTRAP.md" in projection["generated_projection_paths"]
    assert "docs/reports/handoff-packages/latest/execution_contract.json" in projection["generated_projection_paths"]
    assert projection["source_of_truth"] == "generator_and_machine_readable_successor_package"
    assert projection["generator_command"] == "agentic-kit transfer prepare-successor-handoff --render-prompt"
    assert "manual direct edits to generated handoff projections" in projection["forbidden_update_path"]
    assert {
        "generated-handoff-projection-update-policy",
        "patch-cycle-diagnostic-gate",
        "copy-paste-output-discipline",
    } <= set(contract["general_contract"]["rule_ids"])


def test_successor_prompt_renders_machine_readable_precedence_and_state_separation() -> None:
    from agentic_project_kit.successor_handoff_package import render_successor_prompt

    context = {
        "repo": {
            "full_name": "vfi64/agentic-project-kit",
            "local_path": "cd /path/to/agentic-project-kit",
            "branch": "main",
            "head": "abc123",
            "head_short": "abc123",
            "origin_main": "abc123",
            "origin_main_short": "abc123",
            "head_matches_origin_main": True,
            "worktree_clean": True,
        },
        "short_term_memory": {
            "open_tasks": [{"id": "docs-reconciliation", "status": "active"}],
            "recent_lessons": [],
        },
    }

    prompt = render_successor_prompt(context)

    assert "Durable agentic-kit operating model" in prompt
    assert "Current continuation state" in prompt
    assert "Handoff package precedence" in prompt
    assert "execution_contract.json.general_contract" in prompt
    assert "execution_contract.json.current_state_contract" in prompt
    assert "Maschinenlesbare Dateien haben Vorrang" in prompt
    assert "transfer pr-create-complete" in prompt
    assert "not a feature-branch pre-PR gate" in prompt
    assert "docs/DOCUMENTATION_REGISTRY.yaml" in prompt
    assert "Garbage Collector nur für technische Retention" in prompt
    assert "generated handoff projections" in prompt
    assert "manual direct edits to generated handoff projections" in prompt
    assert "Patch-cycle diagnostic gate" in prompt
    assert "next_mutation_allowed" in prompt
    assert "Chat output after local blocks should be only `LOG=...` and `RC=...`" in prompt


def test_successor_validation_requires_contract_layers() -> None:
    import json

    from agentic_project_kit.successor_handoff_package import validate_successor_outputs

    context = {
        "repo": {
            "head": "abc123",
            "head_short": "abc123",
        },
        "long_term_memory": {
            "mandatory_sources": [],
        },
    }
    broken_contract = {
        "schema_version": 1,
        "kind": "successor_execution_contract",
        "rules": [
            {"rule_id": "local-copy-paste-protocol"},
            {"rule_id": "strict-start-decision"},
            {"rule_id": "protected-file-preservation"},
            {"rule_id": "bootstrap_acceptance_gate"},
        ],
    }

    report = validate_successor_outputs(
        {
            "execution_contract.json": json.dumps(broken_contract),
            "successor_prompt.md": "",
        },
        context,
    )

    codes = {finding["code"] for finding in report["findings"]}
    assert "missing_general_contract" in codes
    assert "missing_current_state_contract" in codes
    assert "missing_handoff_projection_contract" in codes
    assert "missing_execution_contract_rule_ids" in codes


def test_successor_validation_requires_generated_projection_update_policy() -> None:
    import json

    from agentic_project_kit.successor_handoff_package import build_execution_contract, validate_successor_outputs

    context = _minimal_successor_context()
    context["long_term_memory"] = {"mandatory_sources": []}
    contract = build_execution_contract(context)
    projection = contract["handoff_projection_contract"]
    projection.pop("generated_projection_paths")
    projection.pop("source_of_truth")
    projection.pop("generator_command")
    projection["forbidden_update_path"] = []

    report = validate_successor_outputs(
        {
            "execution_contract.json": json.dumps(contract),
            "successor_prompt.md": "",
        },
        context,
    )

    codes = {finding["code"] for finding in report["findings"]}
    assert "missing_generated_handoff_projection_paths" in codes
    assert "invalid_handoff_projection_source_of_truth" in codes
    assert "missing_handoff_projection_generator_command" in codes
    assert "missing_forbidden_generated_handoff_update_path" in codes
