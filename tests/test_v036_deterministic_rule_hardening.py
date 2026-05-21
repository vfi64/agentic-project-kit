from pathlib import Path
import subprocess


REMOVED_DIRECT_NS_ADAPTERS = [
    "tools/ns_clean_evidence.sh",
    "tools/ns_commit_pr_guard.sh",
    "tools/ns_pr_cleanup.sh",
    "tools/ns_slice_runner.sh",
    "tools/ns_release_gate.sh",
    "tools/ns_release_verify.sh",
    "tools/ns_release_prep.sh",
    "tools/ns_release_publish.sh",
    "tools/ns_up_pr_completion.sh",
]


def test_final_summary_contract_blocks_false_pass_after_inner_fail() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "A final `PASS` is invalid" in text
    assert "required inner work result" in text
    assert "required gate" in text
    assert "WORK RESULT: PASS" in text


def test_remote_evidence_pass_requires_remote_readable_evidence() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "`REMOTE_EVIDENCE: PASS` requires committed and pushed evidence" in text
    assert "local-only transcript" in text
    assert "unpushed temporary log" in text


def test_successful_evidence_upload_does_not_relabel_failed_work() -> None:
    text = Path("docs/governance/FINAL_SUMMARY_CONTRACT.md").read_text(encoding="utf-8")
    assert "can prove a failed run" in text
    assert "must not relabel failed work" in text


def test_removed_direct_ns_shell_adapters_are_not_tracked() -> None:
    result = subprocess.run(["git", "ls-files", *REMOVED_DIRECT_NS_ADAPTERS], text=True, capture_output=True, check=False)
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == ""


def test_ns_does_not_route_to_removed_direct_shell_adapters() -> None:
    text = Path("ns").read_text(encoding="utf-8")
    for adapter in REMOVED_DIRECT_NS_ADAPTERS:
        assert adapter not in text


def test_tests_do_not_read_removed_shell_adapter_files() -> None:
    combined = "\n".join(path.read_text(encoding="utf-8") for path in Path("tests").glob("test_*.py"))
    for adapter in REMOVED_DIRECT_NS_ADAPTERS:
        needle = f'Path("{adapter}").read_text'
        assert needle not in combined


def test_v036_workplan_records_rule_hardening_scope() -> None:
    text = Path("docs/workflow/V0.3.36_REMAINING_WORKPLAN.md").read_text(encoding="utf-8")
    assert "Deterministic rule-hardening tests" in text
    assert "false-PASS prevention" in text
    assert "remote-evidence truthfulness" in text
    assert "stale shell-file test expectations" in text
