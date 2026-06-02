# Remaining productive Git mutation audit after PR1075

branch: `docs/post-pr1075-remaining-git-mutation-audit`
head: `c20c6b0`

## Context

PR1074 hardened several productive mutation paths, especially command-run upload, terminal-log upload, next-turn evidence upload, work-order uploader, and workflow temp-branch cleanup. PR1075 refreshed the handoff state after PR1074.

This audit records the remaining raw Git/GitHub command references that were not proven fully covered by PR1074. It does not change product code.

## Audit decision

Result: `FAIL` for claiming 100 percent productive Git mutation hardening.

Reason: remaining productive mutation candidates still exist and need file-by-file classification before hardening patches.

## Files requiring follow-up classification

| File | Classification | Current assessment | Recommended next action |
|---|---|---|---|
| `src/agentic_project_kit/transfer_repo_actions.py` | mixed guarded mutation / read-only / remaining candidates | Many paths already have `guard_branch`, required-branch checks, main-commit refusal, full-SHA PR guards, and branch-drift checks. Remaining candidates include branch deletion and admin-refresh internals. | Do not replace wholesale with CLI calls; audit each function and centralize missing guards. |
| `src/agentic_project_kit/release.py` | release/tag mutation candidate | Contains release instructions and tag existence checks; tag creation/push path not proven branch-safe by PR1074. | Add or verify release guard contract: expected branch, clean tree, expected head SHA, tag absence, explicit release mode. |
| `src/agentic_project_kit/release_publish_core.py` | high-risk tag/push mutation | Contains `git tag` and `git push origin <tag>`. It appears to check current branch equals `main`, but branch equality alone is not enough for release safety. | Harden with expected head SHA, dirty-tree check, tag absence check, and explicit release confirmation. |
| `src/agentic_project_kit/release_prep_core.py` | workflow branch-switch mutation | Contains `git switch main`, `git switch <branch>`, and `git switch -c <branch>`. | Verify this is preparatory and guarded; add branch drift checks if missing. |
| `src/agentic_project_kit/release_verify_core.py` | mostly read-only verification | Branch checks appear read-only. | Classify as read-only unless hidden mutation is found. |
| `src/agentic_project_kit/release_gate_core.py` | read-only gate commands | Branch checks appear read-only. | Classify as read-only. |
| `src/agentic_project_kit/cli_commands/init.py` | intentional init exception | Initial repository commit is a special case where committing on default/main can be intended. | Document as explicit exception; avoid normal main-mutation blocking here unless init target is an existing repo. |
| `src/agentic_project_kit/pr_cleanup.py` | likely read-only / cleanup-adjacent | Current audit hit is branch inspection. | Classify fully before patching. |
| `src/agentic_project_kit/pr_create_or_skip.py` | PR creation mutation candidate | Contains direct `gh pr create`. | Prefer delegating to guarded PR creation path or add base/head/dirty-state guards. |
| `src/agentic_project_kit/pr_hygiene.py` | read-only PR/branch inspection | Hits appear to be listing PRs and branches. | Classify as read-only if no mutation exists. |
| `src/agentic_project_kit/ns_up_pr_completion.py` | high-risk PR merge helper | Contains `git switch main`, `gh pr checks --watch`, and direct `gh pr merge --squash --delete-branch`. | Replace direct merge path with guarded `agentic-kit pr merge-if-green` or shared merge core. |
| `src/agentic_project_kit/remote_next.py` | branch-switch helper | Contains `git switch main`. | Replace or guard via shared branch guard if used in productive workflow. |
| `src/agentic_project_kit/local_feature_gate.py` | read-only branch gate | Branch check only. | Classify as read-only. |
| `src/agentic_project_kit/communication_state.py` | read-only branch state | Branch check only. | Classify as read-only. |
| `src/agentic_project_kit/work_orders.py` | read-only branch capture | Branch check only. | Classify as read-only. |

## Priority patch candidates

1. `ns_up_pr_completion.py`: remove or wrap direct `gh pr merge`.
2. `release_publish_core.py`: harden tag creation and tag push.
3. `release.py`: ensure release instructions cannot bypass guarded publish flow.
4. `pr_create_or_skip.py`: guard direct PR creation.
5. `transfer_repo_actions.py::branch_delete`: add explicit safe branch name and main/protected-branch refusal for local and remote deletion.

## Non-goal

Do not blindly replace internal `transfer_repo_actions.py` Git calls with `agentic-kit transfer ...` calls. That file is itself a wrapper/core layer; replacing it with CLI calls risks recursion and unclear control flow.

## Required next safe action

Create a follow-up patch branch for the highest-risk candidates only, starting with PR merge and release tag/push paths. Before patching, inspect the concrete functions and tests.

### RESULT: PASS ###
