# Post-v1.0.6 B1 Rule-Ack Released-Package Retest

Status: PASS  
Date: 2026-08-26  
Scope: targeted released-package retest, not a sixth B1 maintenance cycle

## Purpose

This addendum records the post-v1.0.6 PyPI retest for B1-KIT-009
(`external_rule_acknowledgement`). It updates the evidence type for the
Rule-Ack fix from `kit_main` plus checkout-based `external_retest` to include a
targeted `released_package` external retest.

This report does not replace the five-cycle B1 closeout, does not add a sixth
Comm-SCI maintenance cycle, and does not claim a new external merge-wrapper
cycle under v1.0.6.

## Target

- External repository: `vfi64/Comm-SCI-Control-private`
- Retest workspace: fresh temporary HTTPS clone
- Branch first checked: `main`
- Adopted B1 integration branch: `feature/ui-access-levels-v2`
- Adopted branch HEAD: `bce40ba2edd9cf46bf423e41c47381287c7fe7fb`
- Installed package: `agentic-project-kit==1.0.6` from PyPI

## Evidence

Package identity:

- `agentic-kit --version`: `agentic-kit 1.0.6`
- Imported package version: `1.0.6`
- Packaged command manifest: present under
  `site-packages/agentic_project_kit/reference/agentic-kit-commands.json`

Branch-boundary check:

- On Comm-SCI `main`, `agentic-kit rules acknowledge --root . --json` failed
  closed because that branch does not contain the adopted external workspace
  rule sources. This is expected and prevents a blind self-hosting fallback.

Adopted external branch check:

- On `feature/ui-access-levels-v2`,
  `agentic-kit rules validate-sources --root . --json` returned PASS with
  `workspace_mode=external_manifest_workspace`, no blockers, and
  `sources_total=5`.
- On `feature/ui-access-levels-v2`,
  `agentic-kit rules acknowledge --root . --json` returned PASS with
  `repo_head=bce40ba`, no missing sources, and `sources_total=5`.
- `agentic-kit transfer repo-status --json` returned PASS; the only reported
  local change in the temporary clone was the retest-created untracked
  `.agentic/rule_ack/` directory.

## Adjudication

B1-KIT-009 now has targeted released-package evidence:

- evidence types: `kit_main`, `external_retest`, `released_package`
- released package: `1.0.6`
- retest target: adopted Comm-SCI integration branch
- result: PASS

Remaining boundary:

- The B1 Cycle 005 observation that `pr-merge-safe` merged the external PR but
  did not return locally after the successful remote merge is not closed by this
  targeted Rule-Ack retest. It remains a separate merge-wrapper follow-up until
  a new external merge cycle proves the full path.
