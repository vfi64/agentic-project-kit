# Post-v1.0.4 A1 Release-Environment Gate Findings

Status: done
Status date: 2026-08-24
Baseline ref: `3098578d` (`Refresh handoff state after PR2137 (#2138)`)
Scope: report-only findings for PR #2116, PR #2117, and PR #2119

## Method

This report inspected the repository-local and GitHub evidence available for the
three requested PRs. It does not apply fixes or close any finding.

Evidence inspected:

- PR metadata and bodies from GitHub for PR #2116, PR #2117, and PR #2119.
- PR head CI `test` runs for the three PR branches.
- Check runs attached to the first-parent merge commits `249fe3e7`, `f45160a5`,
  and `18eb6040`.
- Local merge history and changed-file summaries.
- `docs/reports/release/release-prepare-1.0.3.json` for PR #2119 release-prep
  command evidence.
- PR #2117 implementation/test files that harden PR lifecycle recovery.

## Findings Summary

No failed repository-standard CI gate was found for the final head of PR #2116,
PR #2117, or PR #2119.

One real standard-error finding was identified in the release environment:

| Finding | Evidence | Status | A2 recommendation |
| --- | --- | --- | --- |
| PR lifecycle completion could fail locally after GitHub already reported the PR merged, leaving the operator with a misleading blocked/uncertain closeout state. | PR #2117 body says it adds bounded observed subprocess execution and deterministic recovery when a lifecycle step fails locally after GitHub reports the PR merged; PR #2117 changes `src/agentic_project_kit/cli_commands/transfer_pr_merge_flow.py`, adds `src/agentic_project_kit/transfer_observed_subprocess.py`, and adds tests including `test_transfer_pr_complete_settles_when_merge_step_times_out_after_remote_merge`. | fixed by PR #2117 | accepted_with_reason |

No open finding from this inspected set currently needs A2 repair. The finding
above is accepted as fixed because PR #2117 is merged and its CI gate succeeded.

## PR-by-PR Evidence

| PR | Role | Head | Merge commit | CI evidence | Local/report evidence | Findings |
| --- | --- | --- | --- | --- | --- | --- |
| #2116 | Administrative handoff refresh after PR #2115; no product-code changes. | `0f0144b8` on `docs/post-pr2115-handoff-refresh` | `249fe3e7` | Pull-request run `32398970025`, job `test`, `success`, 2026-08-20T17:41:09Z to 17:44:42Z. Merge-commit check runs included successful `test`, `build`, `report-build-status`, `pages-state`, and deploy jobs, with one deploy run skipped. | PR body: "Administrative operational handoff refresh after PR2115. No product-code changes." Files were generated handoff/state artifacts and `docs/reports/terminal/post-pr2115-successor-chat-handoff.md`. | No standard-gate finding found. |
| #2117 | Substantive PR lifecycle hardening. | `8e879345` on `codex/harden-wrapper-settle-cleanup` | `f45160a5` | Pull-request run `32513766851`, job `test`, `success`, 2026-08-21T18:31:18Z to 18:34:28Z. Merge-commit check runs included successful `test`, `build`, `report-build-status`, `pages-state`, and deploy jobs, with one deploy run skipped. | PR body validation: full `pytest` 2856 passed, `ruff` PASS, `check-docs` PASS, `direction validate` PASS, `doctor` PASS, `rules validate-sources` PASS, `workflow-guard check` PASS, and `transfer protected-diff-plan` PASS. | Fixed local PR lifecycle closeout/remote-settle finding. No open standard-gate finding found. |
| #2119 | Release v1.0.3 metadata preparation in the direct release environment. | `5d55fa81` on `codex/release-103-prepare` | `18eb6040` | Pull-request run `32652064430`, job `test`, `success`, 2026-08-23T16:34:09Z to 16:37:38Z. Merge-commit check runs included successful `test`, `build`, `report-build-status`, `pages-state`, and deploy jobs, with one deploy run skipped. | PR body: "Human workflow finish: Prepare v1.0.3 release metadata." Release evidence `docs/reports/release/release-prepare-1.0.3.json` records successful `release-notes-generate`, `release-prep`, and `commands sync-entrypoints` steps. | No standard-gate finding found. |

## Non-Findings And Boundaries

- Pure GitHub service latency, network behavior, or local process waiting is not
  counted as a standard-gate finding unless repository-owned gate or workflow
  evidence classifies it as such.
- A failed GitHub Actions run on `codex/plan-hermes-onboarding` at
  2026-08-23T16:56:05Z was outside the requested PR set and is not adjudicated
  by A1.
- Missing broad local gate text in an administrative or release-prep PR body is
  not treated as a failed gate when other repository evidence shows the relevant
  command path and CI were successful. It remains an evidence-style preference,
  not an A2 fix request from this report.

## Open Findings

None.

No A2 repair is recommended from the requested #2116/#2117/#2119 evidence set.
If the maintainer has a separate CI log or local terminal evidence for the
original #2116 question, that artifact is more specific than this report and
should be added before changing this disposition.
