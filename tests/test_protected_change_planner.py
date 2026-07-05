from __future__ import annotations

from agentic_project_kit.protected_change_planner import analyze_diff, render_findings, touched_files, touched_protected_files

def test_detects_touched_protected_file() -> None:
    diff = "diff --git a/.agentic/compiled_agent_context.yaml b/.agentic/compiled_agent_context.yaml\n"
    assert touched_protected_files(diff) == {".agentic/compiled_agent_context.yaml"}

def test_blocks_anchor_removal_without_decision() -> None:
    diff = "\n".join([
        "diff --git a/.agentic/compiled_agent_context.yaml b/.agentic/compiled_agent_context.yaml",
        "-hard_rules:",
        "+notes: changed",
    ])
    findings = analyze_diff(diff)
    assert findings
    assert findings[0].code == "protected-anchor-removal-without-decision"

def test_accepts_anchor_removal_with_decision() -> None:
    diff = "\n".join([
        "diff --git a/.agentic/compiled_agent_context.yaml b/.agentic/compiled_agent_context.yaml",
        "-hard_rules:",
        "+notes: changed",
    ])
    assert analyze_diff(diff, decisions={".agentic/compiled_agent_context.yaml": "migrate"}) == []

def test_yaml_anchor_detection_does_not_match_substrings() -> None:
    diff = "\n".join([
        "diff --git a/.agentic/handoff_state.yaml b/.agentic/handoff_state.yaml",
        "-  allowed_after_safe_state: true",
        "-  reason: v0.4.2 safety release metadata preparation after PR766",
        "+  reason: administrative evidence/log/handoff commit after substantive safe_state",
    ])

    assert analyze_diff(diff) == []

def test_flags_large_deletion() -> None:
    removed = "\n".join("-line" + str(i) for i in range(25))
    diff = "diff --git a/docs/DOCUMENTATION_REGISTRY.yaml b/docs/DOCUMENTATION_REGISTRY.yaml\n" + removed
    findings = analyze_diff(diff)
    assert any(f.code == "possible-full-replacement-or-large-deletion" for f in findings)


def test_accepts_large_deletion_with_added_migration_record() -> None:
    removed = "\n".join("-line" + str(i) for i in range(25))
    record = "\n".join(
        [
            "diff --git a/docs/reports/protected-change-decisions/delete.md b/docs/reports/protected-change-decisions/delete.md",
            "+# Protected Change Decision",
            "+",
            "+protected_control: docs/DOCUMENTATION_REGISTRY.yaml",
            "+decision: obsolete",
            "+migration record: obsolete document entries moved to PROJECT_DIRECTION.yaml and removed after reference cleanup.",
        ]
    )
    diff = "\n".join(
        [
            "diff --git a/docs/DOCUMENTATION_REGISTRY.yaml b/docs/DOCUMENTATION_REGISTRY.yaml",
            removed,
            record,
        ]
    )
    findings = analyze_diff(diff)
    assert not any(f.code == "possible-full-replacement-or-large-deletion" for f in findings)


def test_flags_large_rewrite_without_decision() -> None:
    removed = "\n".join("-old protected rule " + str(i) for i in range(25))
    added = "\n".join("+new replacement text " + str(i) for i in range(25))
    diff = "\n".join([
        "diff --git a/docs/governance/FINAL_SUMMARY_CONTRACT.md b/docs/governance/FINAL_SUMMARY_CONTRACT.md",
        removed,
        added,
    ])
    findings = analyze_diff(diff)
    assert any(f.code == "large-protected-file-rewrite-without-decision" for f in findings)

def test_accepts_large_rewrite_with_explicit_decision() -> None:
    removed = "\n".join("-old protected rule " + str(i) for i in range(25))
    added = "\n".join("+new replacement text " + str(i) for i in range(25))
    diff = "\n".join([
        "diff --git a/docs/governance/FINAL_SUMMARY_CONTRACT.md b/docs/governance/FINAL_SUMMARY_CONTRACT.md",
        removed,
        added,
    ])
    findings = analyze_diff(diff, decisions={"docs/governance/FINAL_SUMMARY_CONTRACT.md": "migrate"})
    assert not any(f.code == "large-protected-file-rewrite-without-decision" for f in findings)

def test_render_pass_and_block() -> None:
    assert "result=PASS" in render_findings([])
    diff = "diff --git a/docs/governance/FINAL_SUMMARY_CONTRACT.md b/docs/governance/FINAL_SUMMARY_CONTRACT.md\n-WORK RESULT\n"
    rendered = render_findings(analyze_diff(diff))
    assert "result=BLOCK" in rendered
    assert "required_decision=keep|migrate|obsolete|abort" in rendered


def test_tracks_all_touched_files_for_generated_artifact_guards() -> None:
    diff = "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md\n"
    assert touched_files(diff) == {"docs/handoff/NEXT_CHAT_BOOTSTRAP.md"}


def test_blocks_direct_generated_bootstrap_edit_without_generator_source() -> None:
    diff = "\n".join([
        "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "+manual state text",
    ])
    findings = analyze_diff(diff)
    assert any(f.code == "generated-artifact-direct-edit" for f in findings)


def test_allows_generated_bootstrap_change_with_generator_source() -> None:
    diff = "\n".join([
        "diff --git a/src/agentic_project_kit/chat_bootloader.py b/src/agentic_project_kit/chat_bootloader.py",
        "+NEXT_WORK_ITEMS = ()",
        "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        "+generated output",
    ])
    assert not any(f.code == "generated-artifact-direct-edit" for f in analyze_diff(diff))


def test_allows_generated_bootstrap_change_with_successor_handoff_projection_bundle() -> None:
    diff = "\n".join(
        [
            "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
            "+generated bootstrap",
            "diff --git a/docs/reports/handoff-packages/latest/execution_contract.json b/docs/reports/handoff-packages/latest/execution_contract.json",
            "+{}",
            "diff --git a/docs/reports/handoff-packages/latest/successor_context.yaml b/docs/reports/handoff-packages/latest/successor_context.yaml",
            "+repo:",
            "diff --git a/docs/reports/handoff-packages/latest/successor_prompt.md b/docs/reports/handoff-packages/latest/successor_prompt.md",
            "+prompt",
            "diff --git a/docs/reports/handoff-packages/latest/validation_report.json b/docs/reports/handoff-packages/latest/validation_report.json",
            "+{\"status\": \"PASS\"}",
        ]
    )
    assert not any(f.code == "generated-artifact-direct-edit" for f in analyze_diff(diff))


def test_blocks_generated_bootstrap_change_with_incomplete_successor_projection_bundle() -> None:
    diff = "\n".join(
        [
            "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
            "+generated bootstrap",
            "diff --git a/docs/reports/handoff-packages/latest/validation_report.json b/docs/reports/handoff-packages/latest/validation_report.json",
            "+{\"status\": \"PASS\"}",
        ]
    )
    findings = analyze_diff(diff)
    assert any(f.code == "generated-artifact-direct-edit" for f in findings)


def test_generated_bootstrap_is_allowed_when_operational_state_source_changes():
    diff = "\n".join([
        "diff --git a/.agentic/operational_handoff_state.yaml b/.agentic/operational_handoff_state.yaml",
        "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
    ])
    assert not any(f.code == "generated-artifact-direct-edit" for f in analyze_diff(diff))

def test_generated_bootstrap_is_allowed_when_operational_projection_source_changes():
    diff = "\n".join(
        [
            "diff --git a/src/agentic_project_kit/operational_handoff_projection.py b/src/agentic_project_kit/operational_handoff_projection.py",
            "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        ]
    )
    assert not any(f.code == "generated-artifact-direct-edit" for f in analyze_diff(diff))


def test_generated_bootstrap_is_allowed_when_successor_package_source_changes():
    diff = "\n".join(
        [
            "diff --git a/src/agentic_project_kit/successor_handoff_package.py b/src/agentic_project_kit/successor_handoff_package.py",
            "diff --git a/docs/handoff/NEXT_CHAT_BOOTSTRAP.md b/docs/handoff/NEXT_CHAT_BOOTSTRAP.md",
        ]
    )
    assert not any(f.code == "generated-artifact-direct-edit" for f in analyze_diff(diff))


def test_allows_large_handoff_state_refresh_when_core_anchors_remain():
    removed = "\n".join(f"-old handoff line {i}" for i in range(25))
    added = "\n".join(
        [
            "+updated:",
            "+  source: agentic-kit handoff refresh",
            "+safe_state:",
            "+  commit: abc1234",
            "+handoff_maintenance:",
            "+  latest_successor_prompt: docs/reports/handoff-packages/latest/successor_prompt.md",
            "+next_step:",
            "+  first_instruction: Continue with the refreshed slice.",
            *(f"+new handoff line {i}" for i in range(25)),
        ]
    )
    diff = "\n".join(
        [
            "diff --git a/.agentic/handoff_state.yaml b/.agentic/handoff_state.yaml",
            removed,
            added,
        ]
    )
    assert not any(f.code == "large-protected-file-rewrite-without-decision" for f in analyze_diff(diff))
