---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-085: the finding catalog blocked release 1.1.5, and no PR check had run that audit

Date: 2026-10-22
Kit state: CLOSED in candidate, planned release 1.1.5. Consumer VERIFIED_FIXED remains independent.

## Observed

The first `release run --version 1.1.5` stopped in A2 (`release ready`): the standard error scan
reported `audit-ns-legacy-references` and `standard-gates-audit-suite` as FAIL. Nothing was
published; only A1 had finished and no gate had been approved.

The blockers were ten lines in `.agentic/greenfield_findings.json` and its packaged copy
`src/agentic_project_kit/reference/external-findings-status.json`, for example
`"text": "Run ./ns release-prep 0.4.9\n"`. They are the fixture texts of the KIT-GF-054 and
KIT-GF-068 machine contracts, added on 2026-10-21 (c1a). At v1.1.4 the catalog held no such line.

## Two defects

1. The audit classified the finding catalog like a current document. The catalog records
   observations and contract fixtures; a quoted `./ns` call there is evidence, never an
   instruction to run it.
2. No PR check ran `standard-gates-audit-suite`. The slice that added the lines merged with all
   required checks green, and the defect surfaced only when the release started.

## Fix

- `audit-ns-legacy-references` classifies the two catalog paths as `finding_catalog_evidence`.
  The same line in any other file still blocks (a handoff document, another `.agentic` JSON file).
- `tests/test_release_content_audits_on_checkout.py` runs every check of the release-time
  `standard-gates-audit-suite` on the checkout in each PR, taken from the suite's own command
  list, so a check added to the suite is covered as well. Only `release-publish --dry-run` stays
  with the release run, because it needs the GitHub release state and PyPI; a test pins that set.
- The same test checks the Unreleased bullets with release preparation's summary-line rule. The
  first draft of this slice's own bullet quoted the legacy route and would have stopped
  `release-prep` in the same way; the test now fails on such a bullet in the PR.

## Evidence

Before the fix, `agentic-kit audit-ns-legacy-references` on main 526efdaa returned 1 with ten
blockers in the two catalog files, and `release ready --version 1.1.5` returned 2 with the
blockers `audit-ns-legacy-references` and `standard-gates-audit-suite`. With the fix both audits
PASS, and the new machine contract KIT-GF-085 PASS with the candidate wheel and FAIL with 1.1.4.
