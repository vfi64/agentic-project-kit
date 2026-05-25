from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def test_ns_exposes_protected_change_plan_route() -> None:
    text = (ROOT / "ns").read_text(encoding="utf-8")
    assert "protected-change-plan" in text
    assert "agentic_project_kit.protected_change_planner" in text

def test_ns_protected_change_plan_passes_clean_diff(tmp_path: Path) -> None:
    diff = tmp_path / "clean.diff"
    diff.write_text("diff --git a/README.md b/README.md\n+hello\n", encoding="utf-8")
    result = subprocess.run(["./ns", "protected-change-plan", "--diff-file", str(diff)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 0
    assert "result=PASS" in result.stdout

def test_ns_protected_change_plan_blocks_anchor_loss(tmp_path: Path) -> None:
    diff = tmp_path / "bad.diff"
    diff.write_text("diff --git a/.agentic/compiled_agent_context.yaml b/.agentic/compiled_agent_context.yaml\n-hard_rules:\n", encoding="utf-8")
    result = subprocess.run(["./ns", "protected-change-plan", "--diff-file", str(diff)], cwd=ROOT, text=True, capture_output=True)
    assert result.returncode == 1
    assert "protected-anchor-removal-without-decision" in result.stdout
