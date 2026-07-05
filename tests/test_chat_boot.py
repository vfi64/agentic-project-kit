from pathlib import Path

from agentic_project_kit.chat_bootloader import MANDATORY_BOOT_SOURCES
from agentic_project_kit.chat_bootloader import check_boot_sources
from agentic_project_kit.chat_bootloader import render_bootloader
from agentic_project_kit.chat_bootloader import render_next_chat_bootstrap
from agentic_project_kit.chat_bootloader import write_next_chat_bootstrap
from agentic_project_kit.successor_handoff_package import build_successor_handoff_package
from agentic_project_kit.successor_handoff_package import write_successor_handoff_package

START_PROMPT = Path("docs/handoff/START_NEW_CHAT_PROMPT.md")
CLOSEOUT_PROMPT = Path("docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md")
BOOTSTRAP = Path("docs/handoff/NEXT_CHAT_BOOTSTRAP.md")
REQUIRED_TERMS = (
    "FINAL_SUMMARY_CONTRACT.md",
    "handoff_state.yaml",
    "compiled_agent_context.yaml",
    "Rule Registry",
    "boot write",
    "PASS_ALREADY_DONE",
    "d/f",
    "red CI",
)



def _write_operational_handoff_state(root: Path) -> None:
    operational_state = root / ".agentic" / "operational_handoff_state.yaml"
    operational_state.parent.mkdir(parents=True, exist_ok=True)
    operational_state.write_text(
        "schema_version: 1\n"
        "current_head:\n"
        "  full: abcdef123456\n"
        "  short: abcdef1\n"
        "  subject: Admin handoff (#2)\n"
        "last_substantive_work_state:\n"
        "  full: 123456789abc\n"
        "  short: 1234567\n"
        "  subject: Product slice (#1)\n"
        "administrative_context: []\n"
        "freshness_policy:\n"
        "  text: Freshness policy line.\n"
        "next_safe_substantive_slice:\n"
        "  text: document-management projection system\n",
        encoding="utf-8",
    )


def _write_boot_source(path: Path, source: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if source == "docs/planning/PROJECT_DIRECTION.yaml":
        path.write_text(
            "schema_version: 1\n"
            "meta:\n"
            "  owner: maintainers\n"
            "  status: active\n"
            "  updated_after_pr: null\n"
            "  update_policy: update after successful slice\n"
            "  authority: docs/planning/PROJECT_DIRECTION.yaml\n"
            "strategy: []\n"
            "roadmap:\n"
            "  - id: docs-reconciliation\n"
            "    phase: unphased\n"
            "    title: Reconcile documentation authority\n"
            "    status: next\n"
            "    depends_on: []\n"
            "    acceptance: []\n"
            "    source_files: []\n"
            "plans: []\n"
            "ideas: []\n"
            "done: []\n"
            "discarded: []\n",
            encoding="utf-8",
        )
        return
    path.write_text("x\n", encoding="utf-8")


def test_chat_boot_lists_sources_when_present(tmp_path: Path) -> None:
    for source in MANDATORY_BOOT_SOURCES:
        path = tmp_path / source
        _write_boot_source(path, source)
    text = render_bootloader(tmp_path)
    assert "CHAT_BOOTLOADER" in text
    assert "compiled_agent_context.yaml" in text
    assert "operational_handoff_state.yaml" in text
    assert "CURRENT_HANDOFF.md" in text
    assert "START_NEW_CHAT_PROMPT.md" in text
    assert "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md" in text
    assert "run_summary_renderer" in text
    assert "Python runners" in text
    assert "RESULT" in text


def test_chat_boot_detects_absent_sources(tmp_path: Path) -> None:
    results = check_boot_sources(tmp_path)
    assert len(results) == len(MANDATORY_BOOT_SOURCES)
    assert any(not item.exists for item in results)
    text = render_bootloader(tmp_path)
    assert "compiled_agent_context.yaml" in text


def test_next_chat_bootstrap_contains_standard_prompt_and_next_work(tmp_path: Path) -> None:
    for source in MANDATORY_BOOT_SOURCES:
        path = tmp_path / source
        _write_boot_source(path, source)
    _write_operational_handoff_state(tmp_path)
    text = render_next_chat_bootstrap(tmp_path)
    assert "NEXT CHAT BOOTSTRAP" in text
    assert "Canonical chat-switch prompt files" in text
    assert "START_NEW_CHAT_PROMPT.md" in text
    assert "CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md" in text
    assert "Successor Handoff Package" in text
    assert "successor_context.yaml" in text
    assert "validation_report.json" in text
    assert "chat-switch-complete" not in text or "stale" not in text
    assert "PROJECT_DIRECTION.yaml" in text
    assert "docs-reconciliation" in text
    assert "Post-PR1245" not in text
    assert "PR #880" not in text
    assert "\\n" not in text


def test_next_chat_bootstrap_writer_creates_file(tmp_path: Path) -> None:
    _write_operational_handoff_state(tmp_path)
    output = tmp_path / "docs" / "handoff" / "NEXT_CHAT_BOOTSTRAP.md"
    written = write_next_chat_bootstrap(output, tmp_path)
    assert written == output
    text = output.read_text(encoding="utf-8")
    assert "NEXT CHAT BOOTSTRAP" in text
    assert "Required first action" in text
    assert "successor_context.yaml" in text


def test_canonical_chat_switch_prompts_cross_reference() -> None:
    start = START_PROMPT.read_text(encoding="utf-8")
    closeout = CLOSEOUT_PROMPT.read_text(encoding="utf-8")
    bootstrap = BOOTSTRAP.read_text(encoding="utf-8")
    assert "role: start_new_chat" in start
    assert "role: closeout_before_chat_switch" in closeout
    assert str(CLOSEOUT_PROMPT) in start
    assert str(START_PROMPT) in closeout
    assert str(BOOTSTRAP) in start
    assert str(BOOTSTRAP) in closeout
    assert str(START_PROMPT) in bootstrap
    assert str(CLOSEOUT_PROMPT) in bootstrap
    assert "must_update_together:" in start
    assert "must_update_together:" in closeout
    for path in (str(START_PROMPT), str(CLOSEOUT_PROMPT), str(BOOTSTRAP)):
        assert path in start
        assert path in closeout
    for term in REQUIRED_TERMS:
        assert term in start
        assert term in closeout


def test_successor_handoff_package_writes_deterministic_outputs(tmp_path: Path) -> None:
    for source in MANDATORY_BOOT_SOURCES:
        path = tmp_path / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    for source in ("AGENTS.md", "README.md", "SECURITY.md", "docs/reference/AGENTIC_KIT_COMMANDS.md", "docs/reference/agentic-kit-commands.json", "docs/DOCUMENTATION_COVERAGE.yaml", "docs/TEST_GATES.md"):
        path = tmp_path / source
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("x\n", encoding="utf-8")
    _write_operational_handoff_state(tmp_path)

    result = write_successor_handoff_package(tmp_path)
    # tmp_path is intentionally not a Git repository, so validation may report
    # unknown_head. The package must still write deterministic projections;
    # repository-run validation is covered by the generated validation report.
    assert result.validation_report["status"] in {"PASS", "FAIL"}
    assert (tmp_path / "docs/reports/handoff-packages/latest/successor_context.yaml").exists()
    assert (tmp_path / "docs/reports/handoff-packages/latest/successor_prompt.md").exists()

    for rel in (BOOTSTRAP, CLOSEOUT_PROMPT):
        text = (tmp_path / rel).read_text(encoding="utf-8")
        assert "successor_context.yaml" in text
        assert "Post-PR1245" not in text
        assert "PR #880" not in text
        assert "\\\\n" not in text

    # START_NEW_CHAT_PROMPT is protected from broad package-refresh rewrites.
    # It is updated only by dedicated minimal handoff/admin refresh slices.
    assert (tmp_path / START_PROMPT).read_text(encoding="utf-8") == "x\n"


def test_successor_handoff_package_validation_blocks_stale_markers(tmp_path: Path) -> None:
    result = build_successor_handoff_package(tmp_path)
    from agentic_project_kit.successor_handoff_package import validate_successor_outputs

    report = validate_successor_outputs({"bad.md": "Post-PR1245 Administrative Handoff Refresh State"}, result.context)
    assert report["status"] == "FAIL"
    assert report["findings"]
