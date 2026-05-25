from __future__ import annotations

from agentic_project_kit.protected_change_planner import analyze_diff, render_findings, touched_protected_files

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

def test_flags_large_deletion() -> None:
    removed = "\n".join("-line" + str(i) for i in range(25))
    diff = "diff --git a/docs/DOCUMENTATION_REGISTRY.yaml b/docs/DOCUMENTATION_REGISTRY.yaml\n" + removed
    findings = analyze_diff(diff)
    assert any(f.code == "possible-full-replacement-or-large-deletion" for f in findings)

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
