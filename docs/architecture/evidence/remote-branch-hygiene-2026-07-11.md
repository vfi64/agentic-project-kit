# Remote Branch Hygiene Evidence (K3)

Generated: 2026-07-11
Branch: `codex/remote-branch-hygiene`
Scope: K3 remote branch hygiene inventory and guarded cleanup.
Mode: bounded remote mutation through existing `agentic-kit transfer delete-merged-work-branch` only.

No direct `git push --delete` command was run outside the wrapper. The wrapper performs its own PR merge-state verification before deleting a remote work branch.

## Commands

```bash
git fetch --all --prune
./.venv/bin/agentic-kit remote-branch-hygiene --json > tmp/k3-remote-branch-hygiene-pre.json
./.venv/bin/agentic-kit remote-branch-hygiene > tmp/k3-remote-branch-hygiene-pre.txt
./.venv/bin/agentic-kit transfer delete-merged-work-branch <branch> --remote --no-local --json
git fetch --all --prune
./.venv/bin/agentic-kit remote-branch-hygiene --json > tmp/k3-remote-branch-hygiene-post.json
./.venv/bin/agentic-kit remote-branch-hygiene > tmp/k3-remote-branch-hygiene-post.txt
```

## Summary

| Phase | Remote branches | Candidate delete | Keep/open PR | Manual review |
|---|---:|---:|---:|---:|
| before cleanup | 382 | 26 | 3 | 353 |
| after cleanup | 370 | 14 | 3 | 353 |

- Guard-conform wrapper deletion attempts: 20
- Deleted by wrapper: 12
- Blocked by wrapper: 8
- Remaining non-guard-prefix merged candidates: 6
- Remaining manual-review branches: 353

## Deleted By Wrapper

- `docs/clarify-entrypoint-selection-rule`
- `docs/post-merge-gate-bootstrap-visibility`
- `docs/post-pr982-handoff-refresh`
- `docs/post-pr984-handoff-refresh`
- `docs/post-pr987-handoff-refresh`
- `docs/post-pr989-handoff-refresh`
- `docs/post-pr991-handoff-refresh`
- `docs/rule-refresh-handshake-plan`
- `docs/transfer-github-action-coverage`
- `feature/post-merge-gate-visibility-inventory`
- `feature/rule-registry-coverage-index-completeness-749`
- `fix/ruff-python-only-terminal-guard`

## Wrapper-Blocked Candidates

| Branch | Blocker |
|---|---|
| `docs/post-pr914-remote-merge-evidence` | pr_state_not_verified |
| `docs/record-claude-review-and-english-docs-plan` | pr_state_not_verified |
| `docs/refresh-state-after-registry-pr692` | pr_not_merged |
| `docs/repair-v040-state-handoff-drift` | pr_not_merged |
| `docs/use-pr-complete-wrapper` | pr_state_not_verified |
| `feature/ns-shell-independence-audit` | pr_state_not_verified |
| `fix/command-inbox-check-v3` | pr_state_not_verified |
| `fix/workflow-priority-contract` | pr_state_not_verified |

These branches remain visible because the existing deletion guard did not verify the PR state strongly enough to permit deletion.

## Non-Guard-Prefix Candidates

| Branch | Reason |
|---|---|
| `origin/planning-machine-readable-doc-projections` | merged into origin/main and no open PR |
| `origin/planning/post-v0.4.2-standard-error-fineplan` | merged into origin/main and no open PR |
| `origin/r750` | merged into origin/main and no open PR |
| `origin/release/v0.4.4-safety-baseline` | merged into origin/main and no open PR |
| `origin/workflow/harden-remote-yaml-routes` | merged into origin/main and no open PR |
| `origin/workflow/workflow-guard-diagnostics` | merged into origin/main and no open PR |

These are intentionally left for maintainer decision because `transfer delete-merged-work-branch` only allows `feature/`, `fix/`, `docs/`, `chore/`, and `evidence/` work branches.

## Protected Open PR Branches

| Branch | Open PR | Reason |
|---|---:|---|
| `origin/dependabot/github_actions/actions/checkout-7` | 1512 | has open PR |
| `origin/docs/post-pr1328-handoff-refresh` | 1329 | has open PR |
| `origin/docs/post-pr1340-handoff-refresh` | 1341 | has open PR |

The Dependabot branch is protected by the same open-PR classification as other open PR branches.

## Full Post-Cleanup Inventory

| Branch | Merged in `origin/main` | Latest commit | Commit date | Open PR | Action | Safety | Reason |
|---|---:|---|---|---:|---|---|---|
| `origin/chore/a1-state-refresh` | false | `7d89d922` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/cleanup/remove-pr737-placeholder-738` | false | `f6fd0e07` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/consolidate-doc-authority-sources` | false | `f30b74f0` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/fix-post-pr1498-handoff-freshness` | false | `d76a2151` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/gui-reference-transfer-concept` | false | `8d953e1c` | 2026-06-20 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/handoff-contract-discipline-rules` | false | `836d9f8b` | 2026-06-20 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/harden-gui-initial-prompt-and-task-editor` | false | `486c9e95` | 2026-06-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/harden-pass-already-done-classifier` | false | `25d2d4a4` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/harden-release-prep-atomicity` | false | `b43d3854` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/harden-report-retention-gc` | false | `e7596b9a` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/md-report-retention-policy` | false | `9c27ea87` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/patch-cycle-workflow-state-analysis` | false | `123ab541` | 2026-06-20 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/pr-create-complete-live-status` | false | `03739b49` | 2026-06-28 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/pr811-closeout` | false | `0566d2ef` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/release-0.4.10` | false | `ddd68644` | 2026-06-20 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/release-0.4.10-doi-closeout` | false | `e18ce6aa` | 2026-06-20 |  | manual-review | manual-review | not merged into origin/main |
| `origin/codex/release-process-rule-conflict-analysis` | false | `57580875` | 2026-06-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/command-safety-hardening-plan` | false | `d66e2c99` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/dependabot/github_actions/actions/checkout-7` | false | `b4b36792` | 2026-06-20 | 1512 | keep | protected-open-pr | has open PR |
| `origin/diagnose/v040-summary-renderer-remote-evidence` | false | `f1a6bfd8` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/add-zenodo-doi` | false | `237ab904` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/artifact-registry-consumer` | false | `5ae042ff` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/audit-registry-summary-slice` | false | `ff31682b` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/capture-failed-no-copy-agent-next-20260518-213939` | false | `88cfc71c` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/changelog-quality-guard` | false | `e3151133` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/communication-rules-refresh-output` | false | `a4d0b73e` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/doc-mesh-gate-policy` | false | `80585d6f` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/doc-mesh-registry-summary-slice` | false | `2c435589` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/document-failed-next-step-handling` | false | `09e0dcf9` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/documentation-registry-schema-slice` | false | `f13782db` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/enrich-v040-changelog-history` | false | `97c94d48` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/final-verify-handoff-prompt-after-pr666` | false | `4edb0e56` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/finalize-no-copy-after-pr423` | false | `58915a8f` | 2026-05-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/finalize-ns-up-idempotence-state` | false | `44bcb58d` | 2026-05-17 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/finalize-shell-removal-workplan` | false | `ddf44ee6` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/fix-handoff-after-merge` | false | `13a22c1a` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/fix-handoff-semantics-reason` | false | `021bc7ca` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/fix-readme-version-after-v0.2.4` | false | `0cc51c15` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/fix-v031-doc-drift` | false | `0927e5c4` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/guard-agents-local-paths-remote` | false | `d3f647f6` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/gui-transfer-basic-mvp-plan-update` | false | `eb6f724c` | 2026-05-30 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/handoff-after-pr701` | false | `6d29f5ba` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/handoff-registry-summary-slice` | false | `11a74d0b` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/harden-docs-audit-headroom-log-finalization` | false | `28d0682c` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/harden-handoff-administrative-evidence-state` | false | `02549a24` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/kit-as-os-masterplan` | false | `80eacc06` | 2026-07-03 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/lifecycle-registry-summary-slice` | false | `dc493ee4` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/merge-current-handoff-overlay-after-pr664` | false | `ac26fcaf` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/plan-document-artifact-governance-os` | false | `52855598` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/plan-documentation-drift-audit` | false | `b09036f3` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/plan-pre-os-v0412-roadmap` | false | `6cf9601f` | 2026-06-28 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/plan-release-before-doc-governance-rebuild` | false | `448ade3e` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1054-handoff-refresh` | false | `06cc67e6` | 2026-06-02 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1081-handoff-refresh` | false | `94f40d5b` | 2026-06-04 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1328-handoff-refresh` | false | `5cb60425` | 2026-06-13 | 1329 | keep | protected-open-pr | has open PR |
| `origin/docs/post-pr1340-handoff-refresh` | false | `c7e69e3d` | 2026-06-13 | 1341 | keep | protected-open-pr | has open PR |
| `origin/docs/post-pr1499-handoff-refresh` | false | `96f38a5a` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1500-handoff-refresh` | false | `1b52835d` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1510-handoff-refresh` | false | `b36493ca` | 2026-06-20 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1545-handoff-refresh` | false | `9f8d64f6` | 2026-06-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1550-handoff-refresh` | false | `800c28ad` | 2026-06-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1681-handoff-refresh` | false | `6491124f` | 2026-07-02 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr1686-handoff-refresh` | false | `be7cc9d2` | 2026-07-03 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr838-handoff-refresh` | false | `0bbcb8a0` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr841-main-closeout-evidence` | false | `cc2f6b98` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr843-main-closeout-evidence` | false | `9e01dd2c` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr845-main-closeout-evidence` | false | `ef9df030` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr911-admin-closeout` | false | `569baf86` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr914-remote-merge-evidence` | true | `040765e2` | 2026-05-29 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/docs/post-pr915-remote-next-evidence-closeout` | false | `7dee6597` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr916-handoff-refresh-evidence` | false | `4a77aabb` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr923-handoff-rules-refresh-evidence` | false | `6687e4b9` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr924-local-sync-recovery` | false | `0a61ef9f` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr926-status-checks-evidence` | false | `6fbe020d` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr927-handoff-refresh-status-fail-evidence` | false | `636bb9f3` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr928-handoff-refresh-evidence` | false | `e1b22668` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/post-pr959-handoff-refresh` | false | `49931ce5` | 2026-05-30 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/pr-ci-readiness-evidence-fix` | false | `614a31d6` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/pr-ci-wait-readiness` | false | `d233f227` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/pr839-evidence-summary-repair` | false | `545d2272` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/pr912-local-merge-recovery-evidence` | false | `e157997a` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/preserve-diverged-main-repair-log` | false | `fb531f1f` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/preserve-standard-error-closeout-logs` | false | `18a67ccf` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/preserve-sync-diagnose-rule-evidence-governance-20260518-205333` | false | `237bff84` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/queue-agent-next-fail-smoke-004` | false | `b25cca86` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/queue-agent-next-smoke-003` | false | `5b96aa32` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-claude-review-and-english-docs-plan` | true | `b1e5bc7f` | 2026-05-23 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/docs/record-environment-bootstrap-drift` | false | `2fed1650` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-pr815-release-kernel-closeout` | false | `1fd739d7` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v0.3.25-doi` | false | `54cb47d7` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v0.3.36-recover-after-portability-gate-fail` | false | `28998b86` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v0.4.3-doi` | false | `1fc5bee8` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v034-doi-and-roadmap` | false | `503d62c2` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v041-doi-wait-check` | false | `88df5662` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v041-final-main-verify` | false | `e3dd6b5b` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v041-release-publish-log` | false | `dc5db6d5` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/record-v041-release-publish-retry` | false | `da9003ca` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-current-communication-rules-after-pr922` | false | `5079b36e` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-current-handoff-after-pr660` | false | `d7b04e2e` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-after-pr346` | false | `ce9d045b` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-after-pr348` | false | `7a4fc20d` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-after-standard-error-prevention` | false | `0ce2a22b` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr-closeout-alias` | false | `9db159f9` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr353` | false | `675936f3` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr356` | false | `10398687` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr358` | false | `d2f08d73` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr360` | false | `6217ad8e` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr363` | false | `0b1c6d92` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr659` | false | `75bd14f3` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr661` | false | `cb7a1853` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr663` | false | `6e991472` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-handoff-state-after-pr665` | false | `d3e53d6f` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-state-after-pr681` | false | `4b3a3aa9` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-state-after-registry-pr692` | true | `a811804c` | 2026-05-23 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/docs/refresh-v036-status-handoff` | false | `cb81e3a2` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-v040-handoff-after-pr671` | false | `4bacc3a4` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/refresh-v041-handoff-after-pr690` | false | `c29bf768` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/registry-json-report-slice` | false | `387a0590` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/registry-operational-artifacts-slice` | false | `17ecf734` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/release-registry-summary-slice` | false | `8c3f8250` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/remote-next-closeout-evidence` | false | `33b14228` | 2026-05-30 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/remove-stale-pr927-typed-work-order` | false | `e7c8691f` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/repair-readme-version-doi-drift` | false | `9b1a7869` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/repair-v040-state-handoff-drift` | true | `3ce80acf` | 2026-05-22 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/docs/repair-v040-status-drift-after-pr657` | false | `8bd4558a` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/rn-rnc-e2e-smoke-evidence` | false | `c71c236a` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/standard-error-prevention-contract` | false | `5225735b` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/status-refresh-registry-baseline` | false | `f59645b0` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/translate-active-agents-rules` | false | `27c1081c` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/update-handoff-state-after-pr344` | false | `72ba0a92` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/update-state-after-doctor-mvp` | false | `52dd0cf9` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/update-state-after-pr11` | false | `d0d01a61` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/update-state-after-pr7` | false | `1459da8e` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/update-state-after-pr9` | false | `ab1e80f3` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/update-v030-zenodo-doi` | false | `668985ad` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/update-v031-zenodo-doi` | false | `0096c7a2` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/use-done-terminal-ack` | false | `ea770184` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/use-pr-complete-wrapper` | true | `cdb95bc0` | 2026-06-07 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/docs/v0.3.33-readme-doi-archive-closeout` | false | `b14e0ff4` | 2026-05-20 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/v0.3.36-portability-baseline-verify` | false | `276b1b55` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/v0.3.36-shell-port-classification` | false | `a9da2fcb` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/v040-active-docs-english` | false | `309edaf7` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/v040-doi-metadata` | false | `f963bbbe` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/docs/v041-doi-metadata-closeout` | false | `3f2f8970` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/evidence/pr718a-failure-log-upload` | false | `68068d01` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/evidence/pr718a-v3-failure-log` | false | `53e59d2b` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/add-pr-closeout-complete-wrapper` | false | `4ca6d4f0` | 2026-07-03 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/agent-next-missing-pathspec-guard` | false | `ef780dad` | 2026-05-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/b11-transfer-report-contract-semantics` | false | `640a5799` | 2026-06-02 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/boot-closeout-cli-route` | false | `23a2097a` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/boot-write-next-chat-bootstrap` | false | `e67b26b3` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/canonical-chat-switch-prompts` | false | `b768a91d` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/chat-switch-closeout-hardening` | false | `501a2e16` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/cli-result-wrapper` | false | `df28bcde` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/comm-signal-inspector` | false | `48b991e9` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/commit-guard-route` | false | `0fdea994` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/communication-artifact-gc-mvp` | false | `edf46841` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/communication-rule-hardening` | false | `1a1111e6` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/compiled-agent-context-yaml` | false | `2ca906ed` | 2026-05-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/declarative-workflow-runner` | false | `c9f83cf3` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/doc-mesh-historical-banner-repair` | false | `eb4cf026` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/doc-mesh-json-report` | false | `bdebce5a` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/doc-mesh-repair-plan` | false | `78cfa31a` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/doctor-citation-drift` | false | `15566bc2` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/doctor-mvp` | false | `7196f098` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/doctor-version-drift` | false | `8403e12d` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/enforce-single-final-summary` | false | `747dfb59` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/evidence-change-scope-guard-744` | false | `5938b06a` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/evidence-finalize-log-wrapper` | false | `6bcb9892` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/evidence-guard-python-error-markers-743` | false | `342bdc45` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/evidence-scope-check-cli-745` | false | `be8cb4b8` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/evidence-summary-parser` | false | `b0baa46a` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/expand-next-chat-bootstrap-work-items` | false | `0376271f` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/expected-negative-smoke-markers` | false | `f3dfba5c` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/finalize-log-visible-summary` | false | `fa98febd` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/generated-artifact-direct-edit-guard` | false | `e0e1dab2` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/governance-check-mvp` | false | `9f0fca0f` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/governed-rule-registry-baseline` | false | `07928822` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/gui-gatekeeper-local-only-actions` | false | `fe605c26` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/gui-successor-handoff-button` | false | `5bbc04c2` | 2026-06-06 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/gui-tkinter-gatekeeper-integration` | false | `7c87c3e7` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/handoff-freshness-yaml-override` | false | `52d7fb07` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/handoff-state-commit-semantics` | false | `613a9f9a` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/handoff-update-automation` | false | `27ef9875` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/harden-post-release-doi-closeout-consistency` | false | `f4d87eb0` | 2026-06-08 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/harden-release-process-standard-errors` | false | `2c2f9b25` | 2026-06-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/harden-terminal-block-final-pass` | false | `af9395a8` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/idle-workflow-state` | false | `6d41728a` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/last-evidence-inspector` | false | `4ebf8773` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/machine-checkable-state-gates` | false | `46d06ca5` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/mode-guard-venv-tools` | false | `c2d5b7dd` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/mode-guard-venv-tools-v2` | false | `d59d9d38` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/next-turn-a0-status-result-api` | false | `8723a283` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/next-turn-a1-result-finalizer` | false | `772d976a` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/next-turn-a2-evidence-publisher` | false | `a7d539a3` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/next-turn-a4-commit-push-finalizer` | false | `95b9b378` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/next-turn-a5-pr-status-kernel` | false | `2cec4d4f` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/next-turn-a8-fixed-slot-runner` | false | `e48748cf` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/next-turn-a9-runner-cleanup` | false | `9ba367aa` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/no-copy-terminal-evidence-policy` | false | `8695814b` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/ns-shell-independence-audit` | true | `e7875c38` | 2026-06-08 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/feature/ns-up-python-core` | false | `de0f3abb` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/ns-up-route` | false | `641222c9` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/parametrized-git-release-actions` | false | `c42d3ae4` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/pass-already-done-classifier` | false | `8d76e48f` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/pass-already-done-json-output` | false | `cd10eb72` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/pass-already-done-report-json` | false | `6f987921` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/patch-preflight-slice-gate` | false | `524b15ce` | 2026-05-28 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/persistent-handoff-state` | false | `8d3e9dbf` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/portable-llm-communication-bootstrap-contract` | false | `7c0b293e` | 2026-05-22 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/pr-ci-wait-cli` | false | `76547268` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/pr-cleanup-python-core` | false | `7546b197` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/pr-cleanup-route` | false | `45eef58f` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/pr-closeout-gate` | false | `6552c15a` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/prepare-v0.2.3-release` | false | `cde562ca` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/prepare-v0.2.4-zenodo-release` | false | `312b35f4` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/profile-explain-command` | false | `447ffdc5` | 2026-05-11 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/project-direction-authority` | false | `3dfa3ba5` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/python-summary-bootloader` | false | `e81b1468` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/read-only-work-order-templates` | false | `e22a333c` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/register-evidence-scope-check-746` | false | `47481db1` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-gate-route` | false | `a8d07517` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-prep-python-core` | false | `6e253637` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-prep-route` | false | `4bebd3d6` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-preparation-flow` | false | `488e7584` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-publish-python-core` | false | `5ca497af` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-publish-route` | false | `84ae3638` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-remote-validation` | false | `6bac4ca6` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-state-validation` | false | `17a7d96c` | 2026-05-09 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-verify-python-core` | false | `65938204` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/release-verify-route` | false | `ea145517` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/remote-next-evidence-status` | false | `7d89236c` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/remove-clean-evidence-shell-python-route` | false | `868d6daf` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/remove-commit-guard-shell-adapter` | false | `6c62401b` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/repo-backed-work-orders` | false | `8ab2fb5d` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rn-rnc-aliases-and-closeout` | false | `d30fc318` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rnc-no-closeout-status` | false | `8e82099d` | 2026-05-30 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-mechanism-inventory-718` | false | `045a3224` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-mechanism-inventory-718a-v5` | false | `02cfce8f` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-migrations-721` | false | `4b45568a` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-refresh-command-files` | false | `cf9d66a6` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-classification-729` | false | `a75918af` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-cli-723` | false | `e6d686b8` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-completeness-733` | false | `abefcb30` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-conflicts-731` | false | `38854dfb` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-coverage-727` | false | `b2dbb4db` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-coverage-735` | false | `f115edcd` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-guard-724` | false | `8e758bd9` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-owner-conflict-domains-747` | false | `15cd929b` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-preflight-725` | false | `c0cf85f0` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-release-evidence-737` | false | `fe9feb0e` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-source-evidence-hardening-739` | false | `89ec0b6f` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-test-coverage-metadata-748` | false | `2e3bfabb` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/rule-registry-validator-722` | false | `ab15d8a3` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/safe-evidence-commit-paths` | false | `ec676268` | 2026-05-29 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/slice-gate-planning-doc` | false | `1a0d1651` | 2026-05-28 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/slice-runner-python-core` | false | `278bb03e` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/slice-runner-route` | false | `dccc3c9a` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/state-guard` | false | `01d50a85` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/state-shortcuts` | false | `90d89ef1` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/summary-presence-check` | false | `9ef4d51e` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/sync-main-restore-known-volatile-helper` | false | `1e7b611e` | 2026-06-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/terminal-log-wrapper` | false | `3128bf4e` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/transfer-safety-rule-header` | false | `b9cb470d` | 2026-06-08 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/transfer-wrapper-branch-safety` | false | `8ca8b859` | 2026-06-02 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/v0.3.36-portability-gate-core-action-summary` | false | `011c07c4` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/v036-deterministic-rule-hardening` | false | `6d4f4689` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/v036-logged-block-status-propagation` | false | `74855fa3` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/v036-ns-python-portability` | false | `bb187503` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/v036-summary-format-execution-origin` | false | `bfb6cd3d` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/v036-terminal-log-mandate` | false | `04849436` | 2026-05-21 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/work-order-contract-enforcement` | false | `ea8ff146` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/work-order-governance-gate` | false | `e5fb53c9` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/workflow-cli` | false | `5a823b11` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/feature/zenodo-metadata` | false | `543bb702` | 2026-05-10 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/agent-next-human-reply-footer-pf` | false | `f00792bf` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/agent-run-fail-marker-detection` | false | `56a4ac1b` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/command-inbox-check` | false | `5417badc` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/command-inbox-check-v3` | true | `ae6fd56f` | 2026-05-18 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/fix/handoff-completed-list-720` | false | `7a72182f` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/idempotent-already-executed-agent-next` | false | `9669b33a` | 2026-05-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/idempotent-already-executed-inbox` | false | `4efe646d` | 2026-05-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/init-version-drift-doctor` | false | `51194866` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/next-turn-a10c-canonical-summary-guard` | false | `af31335f` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/no-copy-result-handoff-pointer` | false | `0c581cd3` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/partial-fetch-full-replacement-guard` | false | `d535e69c` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/post-merge-complete-failing-noop-state` | false | `836faeb7` | 2026-07-03 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/pr-closeout-complete-gh-merged-field` | false | `cd805cad` | 2026-07-03 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/repair-already-executed-idempotency-test` | false | `124bce25` | 2026-05-19 |  | manual-review | manual-review | not merged into origin/main |
| `origin/fix/workflow-priority-contract` | true | `66dce666` | 2026-05-25 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/governance/doc-mesh-audit` | false | `7c24d41b` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/governance/rule-hardening-rule` | false | `f2254480` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/guard-handoff-prompt-freshness` | false | `8c5870e4` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/gui-transfer-tasks` | false | `16e62cf5` | 2026-06-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/human-readable-post-merge-complete-summary` | false | `a3c0aa2e` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/llm-inbox-no-copy-001` | false | `e42cfc1f` | 2026-05-18 |  | manual-review | manual-review | not merged into origin/main |
| `origin/plan-rule-registry-717` | false | `6c08d467` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/plan/next-turn-a0-error-additions` | false | `8197499f` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/planning-focus` | false | `4dd0e2d0` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/planning-machine-readable-doc-projections` | true | `e6fefdee` | 2026-05-23 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/planning-machine-readable-sources` | false | `c88775da` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/planning/post-v0.4.2-standard-error-fineplan` | true | `06d6ea30` | 2026-05-25 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/post-merge-complete-finalization` | false | `8c1867c8` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-merge-complete-preflight-summary` | false | `7293b9a7` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-merge-complete-reply-semantics` | false | `a21e7e27` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-merge-complete-reporting` | false | `91366906` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-merge-complete-sync-before-final-check` | false | `de20792c` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-merge-lifecycle-command` | false | `b42300a3` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-merge-state-parsing-fix` | false | `300ae404` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-pr809-status-handoff-refresh` | false | `dc740349` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post-pr865-main-verify` | false | `2e94f71d` | 2026-05-27 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post704-docs-refresh` | false | `403d6b03` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post706-handoff-refresh` | false | `0f5a3edb` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post707-state-refresh` | false | `d3b632eb` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post709-state-refresh` | false | `87476e7d` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post712-closeout` | false | `fdae0e2c` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post714-state-refresh` | false | `f6a7f9e5` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post718-state-refresh` | false | `374206a5` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post725-state-refresh` | false | `d21b6dde` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post727-state-refresh` | false | `1527527a` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post729-state-refresh` | false | `c65985a4` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post731-state-refresh` | false | `46e42c75` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post733-state-refresh` | false | `61d9f143` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/post735-state-refresh` | false | `f7fdb869` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/pr-709` | false | `0d316e6d` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/pr714` | false | `2769e779` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/pr809-clean` | false | `a3dadc9a` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r750` | true | `d28eb4b4` | 2026-05-25 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/r751` | false | `d580e288` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r752` | false | `49896e11` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r753` | false | `a871efcf` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r754` | false | `1d649295` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r755` | false | `9bf2b4be` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r756` | false | `42a911b8` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r757` | false | `33b28e9d` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r758` | false | `fc742108` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r759` | false | `e8682224` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r760` | false | `f9e987d3` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r761` | false | `2b168f33` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r762` | false | `1a7b894f` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r764` | false | `a41c0c18` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r765` | false | `3b11ad1d` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/r766` | false | `bcada7a3` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/refactor/cli-commands-package` | false | `0f6735bd` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/refactor/modularize-cli-commands` | false | `454d1294` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/prepare-v0.3.3` | false | `04b7db38` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/prepare-v0.3.4` | false | `f1a98874` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/prepare-v0.4.1` | false | `7afd3ea5` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/prepare-v0.4.1-metadata` | false | `78fa5b27` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/prepare-v0.4.3` | false | `146f3fed` | 2026-05-26 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/v0.3.1` | false | `db3945a9` | 2026-05-12 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/v0.4.2-doi-closeout` | false | `9b5d7709` | 2026-05-25 |  | manual-review | manual-review | not merged into origin/main |
| `origin/release/v0.4.4-safety-baseline` | true | `d2d800be` | 2026-05-28 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/remote-next-final-rule-ack-summary` | false | `74ca413d` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/remote-next-no-current-order-semantics` | false | `c9410877` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/remote-next-order-lifecycle-states` | false | `4f991d45` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/remote-next-stale-order-guard` | false | `d3ecc0af` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/rn-preflight-summary` | false | `82d7ce88` | 2026-06-05 |  | manual-review | manual-review | not merged into origin/main |
| `origin/safety/composed-wrapper-invariant-audit` | false | `63dd190e` | 2026-07-03 |  | manual-review | manual-review | not merged into origin/main |
| `origin/safety/composite-short-circuit-audit` | false | `32d9db5e` | 2026-07-03 |  | manual-review | manual-review | not merged into origin/main |
| `origin/strategy-v0-4-professional-single-user` | false | `57c37c14` | 2026-05-16 |  | manual-review | manual-review | not merged into origin/main |
| `origin/test/gui-action-execution-headless` | false | `3378a47d` | 2026-05-23 |  | manual-review | manual-review | not merged into origin/main |
| `origin/tmp-b11-go-mode-transfer-reports` | false | `bb1642eb` | 2026-06-01 |  | manual-review | manual-review | not merged into origin/main |
| `origin/workflow/auto-start-next-step` | false | `47cde1c4` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/workflow/bootstrap-next-step-shell-env` | false | `498acad7` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/workflow/harden-local-repo-freshness` | false | `ab382400` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/workflow/harden-next-step-default-gate` | false | `c65ad4bb` | 2026-05-13 |  | manual-review | manual-review | not merged into origin/main |
| `origin/workflow/harden-remote-yaml-routes` | true | `ce51acdf` | 2026-05-24 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
| `origin/workflow/harden-remote-yaml-workflow` | false | `8414f579` | 2026-05-24 |  | manual-review | manual-review | not merged into origin/main |
| `origin/workflow/workflow-guard-diagnostics` | true | `ce665c3f` | 2026-05-24 |  | candidate-delete-merged-remote-branch | dry-run-candidate | merged into origin/main and no open PR |
