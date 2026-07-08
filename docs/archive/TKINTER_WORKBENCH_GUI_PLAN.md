# Tkinter Workbench GUI Plan

Document class: historical archive
Status-date: 2026-07-08
Archived-from: docs/planning/TKINTER_WORKBENCH_GUI_PLAN.md
Superseded-by: docs/planning/PROJECT_DIRECTION.yaml
Note: implemented differently (progressive-disclosure cockpit).

Status: proposed
Decision status: proposed as the highest-priority implementation track after current closeout evidence is recorded
Owner: workflow/gui kernel
Scope: full Tkinter workbench, button catalog, dispatch integration, no-copy evidence, and staged functionality enablement

## Purpose

The project needs a complete local Tkinter workbench that makes the existing repository-backed workflow rules visible, hard to skip, and easier to execute correctly. The GUI must be planned as the full target interface from the beginning, with all intended buttons visible in a structured layout. Functionality behind the buttons is enabled later in small verified slices.

This plan is not a reduced MVP. The first GUI slice renders the full planned workbench structure. Buttons without finished backends are visible, disabled, and marked as planned.

## Priority

This is the top implementation priority once the current evidence closeout is clean. The goal is to reduce drift by routing recurring human/LLM interaction through visible buttons, typed work orders, strict dispatch validation, remote evidence capture, and deterministic gates.

## Architecture boundaries

- Use the existing `agent-next`, command-inbox, typed-work-order, action-registry, evidence, handoff, and PR workflow primitives.
- Do not introduce a parallel queue with independent state.
- Do not write directly to `main`; use branch, PR, CI, merge, main-sync, finalize evidence, and closeout evidence.
- Use Python core implementation. Shell is allowed only as a thin wrapper or emergency fallback and must not become the canonical mutation path.
- Use temporary files through Python `tempfile` or an equivalent `/tmp`-scoped runtime path for generated command fragments and transient reports.
- Never rely on copy-and-paste as the primary evidence transport. Remote-readable files under `docs/reports/terminal/` or command-run reports must be the normal evidence path.
- Preserve `current + archive`: current state files are pointers; durable dispatch records live in immutable archive files keyed by dispatch id.
- Keep every button backed by a rule reference, safety class, implementation state, and test expectation before enabling execution.

## Target workbench layout

Recommended Tkinter structure:

- Top status bar: branch, dirty state, workflow state, latest evidence pointer, current dispatch id, current PR, and warning/block status.
- Left navigation: category list and filter by safety class.
- Center panel: complete button grid grouped by category.
- Right detail panel: selected button metadata, governing rules, preconditions, allowed files, expected outputs, and latest diagnostic result.
- Bottom evidence panel: latest terminal log, command-run report, PR URL, CI summary, and next human action.
- Footer: mode indicator, `d/f/w` interpretation, and explicit instruction when paste-output is still required.

## Button states

Every button must expose one of these states:

- `implemented`: backend available and covered by tests.
- `planned`: visible but disabled; metadata and rule references exist.
- `blocked`: disabled because preconditions or gates fail.
- `needs_review`: available only after a read-only review report passes.
- `deprecated`: visible only in diagnostics or compatibility mode.

Button state must come from structured metadata, not from handwritten UI conditionals.

## Full button catalog

### Session

| Button | task_type | Initial state |
|---|---|---|
| Generate handoff prompt | `handoff-prompt-generate` | planned |
| Create successor handoff | `successor-handoff-create` | planned |
| Refresh status | `status-refresh` | planned |
| Update handoff state | `handoff-state-update` | planned |
| Show current bootstrap | `bootstrap-show` | planned |
| Run handoff check | `handoff-check` | read-only candidate |

### Git workflow

| Button | task_type | Initial state |
|---|---|---|
| Prepare commit | `commit-prepare` | planned |
| Push branch | `push-branch` | planned |
| Pull / sync main | `pull-sync` | planned |
| Create PR | `pr-create` | planned |
| PR status | `pr-status` | planned |
| Merge PR if green | `pr-merge-if-green` | planned |
| PR closeout | `pr-closeout` | planned |
| Branch status | `branch-status-check` | planned |

### Quality gates

| Button | task_type | Initial state |
|---|---|---|
| Doctor | `gate-doctor` | read-only candidate |
| Check docs | `gate-check-docs` | read-only candidate |
| Docs audit | `gate-docs-audit` | planned |
| Governance check | `gate-governance-check` | planned |
| State freshness | `gate-state-freshness` | planned |
| Evidence guard | `gate-evidence` | planned |
| Portability check | `gate-portability` | planned |
| Rule registry check | `gate-rule-registry` | planned |

### Rule work

| Button | task_type | Initial state |
|---|---|---|
| Register new rule | `rule-register-new` | planned |
| Verify rule | `rule-verify` | planned |
| Rule registry report | `rule-registry-report` | planned |
| Document migration | `rule-migration-document` | planned |
| Check rule conflict | `rule-conflict-check` | planned |

### Documentation

| Button | task_type | Initial state |
|---|---|---|
| Update STATUS.md | `docs-status-update` | planned |
| Add CHANGELOG entry | `docs-changelog-entry` | planned |
| DOI closeout | `docs-doi-closeout` | planned |
| Update verified releases | `docs-verified-releases` | planned |
| Update CITATION.cff | `docs-citation-update` | planned |
| Documentation system audit | `docs-system-audit` | planned |

### Release

| Button | task_type | Initial state |
|---|---|---|
| Prepare release | `release-prepare` | planned |
| Publish release | `release-publish` | planned |
| Post-release verify | `release-post-verify` | planned |
| DOI wait/check | `release-doi-wait` | planned |
| Release plan | `release-plan` | planned |
| Release verify | `release-verify` | planned |

### Diagnostics

| Button | task_type | Initial state |
|---|---|---|
| Agent-next queue health | `diagnose-queue-health` | planned |
| Inbox check | `diagnose-inbox-check` | planned |
| Stale-state detect | `diagnose-stale-state` | planned |
| Evidence-state contract | `diagnose-evidence-state` | planned |
| Compile context | `diagnose-compiled-context` | planned |
| Failure-mode review | `diagnose-failure-mode-review` | planned |

## Dispatch integration

The GUI dispatch layer must be a thin adapter over the existing repository workflow. It must not create a competing state machine.

Target files:

- `.agentic/dispatch/current.yaml`: pointer to the active dispatch record.
- `.agentic/dispatch/archive/<dispatch_id>.yaml`: immutable dispatch record.
- Existing `.agentic/commands/inbox/` command pair or typed-work-order path: execution substrate.
- Existing `docs/reports/terminal/` and `docs/reports/command_runs/`: evidence substrate.

Dispatch records must contain `schema_version`, `dispatch_id`, `task_type`, `button_id`, `safety_class`, `implementation_state`, `governing_rules`, `preconditions`, `allowed_files`, `expected_outputs`, `evidence_requirements`, `created_at`, `created_by`, and `archive_path`.

## Evidence and response loop

The GUI must display and prefer remote-readable evidence. Local-only temporary evidence is not enough for normal completion.

Required normal loop:

1. User selects a visible button.
2. GUI renders metadata and preconditions.
3. GUI runs read-only preflight.
4. GUI creates a dispatch archive record and updates the current pointer.
5. Existing queue/typed-work-order mechanism performs the work or reports why it is blocked.
6. Evidence is finalized with the existing summary renderer.
7. Evidence is committed and pushed through PR workflow when the slice requires durable evidence.
8. GUI shows the next human action from a structured report.

## Implementation slices

### Slice 0: planning and status alignment

- Add this plan and register it.
- Keep existing closeout evidence rules active.
- Do not implement GUI behavior in this planning PR.
- Update current-state pointers only in a dedicated guarded state-refresh slice if required by gates.

### Slice 1: metadata and full GUI skeleton

- Add a Python button catalog with every button listed in this plan.
- Add metadata fields for category, label, task_type, safety class, implementation state, governing rules, preconditions, expected outputs, and planned tests.
- Render the full Tkinter layout with all categories and all buttons.
- Implement selection/detail rendering.
- Keep non-implemented buttons disabled.
- Add headless tests that inspect widget metadata without launching an interactive window.

### Slice 2: dispatch model and archive pointer

- Add typed models for dispatch records.
- Add validators for `current + archive` invariants.
- Write dispatch records through Python core only.
- Add tests for duplicate dispatch ids, stale current pointer, missing archive, invalid rule reference, invalid safety class, and dirty worktree blocking.

### Slice 3: read-only buttons

Enable only low-risk read-only buttons: Doctor, Check docs, Handoff check, State freshness, Governance check, and Failure-mode review once the Phase-1 failure-mode command exists.

### Slice 4: no-copy evidence viewer

- Add evidence pointer display.
- Add structured summary parsing in the GUI.
- Add hard UI warnings when `REMOTE_EVIDENCE` is missing or local-only.
- Add tests that prevent a PASS UI state when evidence inspect would fail.

### Slice 5: bounded PR workflow buttons

- Enable commit-prepare, PR-create, PR-status, and PR-closeout only behind preflight gates.
- Keep merge, release, tag, and destructive actions blocked unless explicit bounded-action workflows exist.
- Require `protected-change-plan` for protected files.

### Slice 6: merge and post-merge closeout buttons

- Enable merge-if-green only after head/base pinning and main-CI verification are available through stable commands.
- Enable post-merge closeout only through the evidence finalize path.
- Display failed-run diagnostics in the GUI when CI is red.

### Slice 7: documentation and rule-work buttons

- Enable documentation and rule buttons one group at a time.
- Each group must have deterministic tests for allowed files, required gates, and stale-state failure behavior.

### Slice 8: release buttons

- Enable release buttons last.
- Require release-readiness, remote tag/release absence checks, DOI safety, and explicit maintainer confirmation for publish/tag actions.

## Test contract

Implementation PRs must add or update tests for complete button catalog rendering, disabled planned buttons, Python-core dispatch creation, absence of a direct main-write path, non-canonical shell mutation paths, temporary-file handling, remote-evidence requirements, protected-file preflight, and state/handoff freshness before mutation buttons become active.

## Planned evidence gate

Until Slice 1 exists, this plan is not executable evidence. The first implementation PR must run at least:

```bash
python -m pytest -q tests/test_tkinter_workbench_gui.py tests/test_cockpit.py tests/test_repo_ns_entrypoint.py
ruff check .
agentic-kit check-docs
agentic-kit docs-audit
agentic-kit doctor
```

If Tk support is unavailable in the default environment, headless metadata tests still remain mandatory and real-window smoke tests must stay opt-in.

## Acceptance for this planning PR

- The plan exists in `docs/planning/`.
- The documentation registry includes the plan.
- The plan states that the full GUI structure is planned from the beginning, not a reduced GUI.
- The plan states that functionality is enabled gradually behind tests and gates.
- The plan forbids a parallel queue and direct writes to `main`.
- The plan records Python-core, temporary-file, and remote-evidence expectations.

## First implementation step after this plan

Implement Slice 1 only: a complete Tkinter workbench skeleton with all buttons present, all non-implemented buttons disabled, structured metadata loaded from a Python catalog, and headless tests proving that the full planned interface is visible and non-executable where appropriate.
