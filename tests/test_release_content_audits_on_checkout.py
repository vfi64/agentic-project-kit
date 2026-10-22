"""KIT-GF-085: every repository-content audit of the release-time suite also runs on each PR.

Release 1.1.5 stopped in A2 (`release ready`): `standard-gates-audit-suite` found `./ns` lines in the
greenfield finding catalog that a merged slice (machine contracts, c1a) had added. No PR check ran
that suite, so the slice merged green and the defect surfaced only when the release started. The
suite's own command list drives this test, so a check added to the suite is covered here as well;
only checks that need the remote are left to the release run. The Unreleased bullets, which the
release run passes as summary lines, must also pass release preparation's summary-line check.
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest

from agentic_project_kit.cli_executable import default_agentic_kit
from agentic_project_kit.ns_legacy_reference_audit import (
    FINDING_CATALOG_PATHS,
    classify_legacy_reference,
)
from agentic_project_kit.release_prepare import _normalize_changelog_summary_lines
from agentic_project_kit.standard_gates_audit_suite import REQUIRED_STANDARD_GATE_COMMANDS

ROOT = Path(__file__).resolve().parents[1]
# Needs the GitHub release state and PyPI; the release run checks it in A2 and C1.
REMOTE_CHECKS = {"release-publish"}
CONTENT_CHECKS = [command for command in REQUIRED_STANDARD_GATE_COMMANDS if command[0] not in REMOTE_CHECKS]


def test_only_the_named_remote_checks_are_left_to_the_release_run():
    assert {command[0] for command in REQUIRED_STANDARD_GATE_COMMANDS} - {c[0] for c in CONTENT_CHECKS} == REMOTE_CHECKS


@pytest.mark.parametrize("command", CONTENT_CHECKS, ids=[" ".join(c) for c in CONTENT_CHECKS])
def test_the_release_content_audit_passes_on_the_checkout(command):
    completed = subprocess.run([default_agentic_kit(ROOT), *command], cwd=ROOT, text=True,
                               capture_output=True, timeout=600)
    assert completed.returncode == 0, (completed.stdout + completed.stderr)[-4000:]


@pytest.mark.parametrize("path", sorted(FINDING_CATALOG_PATHS))
def test_a_finding_catalog_quoting_an_ns_call_is_evidence(path):
    assert (ROOT / path).is_file()
    assert classify_legacy_reference(path, '"text": "Run ./ns release-prep 0.4.9\\n"')[0] == "finding_catalog_evidence"


def test_the_same_call_elsewhere_still_blocks():
    assert classify_legacy_reference("docs/handoff/NEXT.md", "Run ./ns release-prep 0.4.9")[0] == "current_instruction_blocker"
    assert classify_legacy_reference(".agentic/other.json", '"text": "Run ./ns release-prep 0.4.9"')[0] == "current_instruction_blocker"


def test_the_unreleased_bullets_pass_release_preparation_as_summary_lines():
    text = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")
    section = re.search(r"^## Unreleased\n(.*?)(?=^## )", text, re.MULTILINE | re.DOTALL)
    bullets = [line[2:] for line in (section.group(1) if section else "").splitlines() if line.startswith("- ")]
    if bullets:
        assert _normalize_changelog_summary_lines(bullets) == tuple(bullets)
