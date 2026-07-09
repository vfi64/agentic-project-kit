# Failure-Mode Review Automation Plan

Document class: archive/historical
Status-date: 2026-07-08
Moved-from: docs/archive/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md
Superseded-by: docs/planning/PROJECT_DIRECTION.yaml
Archive note: Open implementation work is carried by Project Direction items; this file is retained as historical plan evidence.

Status: proposed
Decision status: proposed for phased implementation
Owner: release/evidence kernel
Scope: agentic workflow safety, pre-slice review, post-merge closeout

## Purpose

The project must not rely on a chat prompt such as "think adversarially" to find workflow failures. Known failure modes must be represented as repository-backed contracts, checked by commands, covered by tests, and eventually enforced by preflight gates.

This plan defines the implementation contract for automating failure-mode review before product work and closeout checks after merge.

## Goals

- Require a repository-backed failure-mode review before a new product or workflow slice starts.
- Require a repository-backed post-merge closeout path after a merge.
- Make known workflow-kernel risks visible as machine-readable checklist items.
- Keep the system deterministic first: commands produce structured reports, tests verify contracts, and LLMs may only choose from bounded recommendations.
- Start in read-only/WARN mode and only later promote unambiguous failures to BLOCK.

## Non-goals

- Do not build a free autonomous agent.
- Do not encode this as a chat-only rule.
- Do not let an LLM freely invent or silently skip known failure modes.
- Do not combine the initial catalog, read-only command, preflight blocker, and post-merge automation in one PR.
- Do not broadly rewrite protected STATUS, Handoff, governance, or YAML files.

## Target workflow

```text
Pre-slice Kernel Review
-> smallest PR slice
-> PR CI
-> merge-if-green
-> Post-merge Main Verification
-> Evidence Finalize
-> Handoff/Status Freshness
-> Next-slice Recommendation
```

## Phase boundaries

### Phase 1: catalog and read-only next-slice review

Allowed work:

- Add `.agentic/failure_modes.yaml`.
- Add `src/agentic_project_kit/failure_mode_review.py`.
- Add `src/agentic_project_kit/cli_commands/next_slice.py`.
- Register `agentic-kit next-slice review`.
- Record the removed legacy wrapper shortcut as historical context only.
- Add tests for catalog loading, report rendering, CLI exposure, dirty worktree blocking, missing catalog blocking, and stale review artifact rejection.
- Add documentation references in `docs/TEST_GATES.md` and this planning document.

Forbidden in Phase 1:

- Do not change `merge-if-green` behavior.
- Do not change `pr-status` behavior.
- Do not change `patch-preflight` or `protected-change-plan` to block patches.
- Do not create automatic PRs.
- Do not add a post-merge closeout wrapper.
- Do not convert WARN findings into broad hard blockers.

### Phase 2: WARN gate integration

- Add a lightweight gate path that runs `agentic-kit next-slice review` during local preflight.
- Keep non-critical findings as WARN.
- Require the report to be current for the local HEAD when the user explicitly asks to start a new kernel slice.

### Phase 3: kernel preflight enforcement

- Integrate the review with patch/preflight logic for workflow-kernel files only.
- If a patch changes registered kernel surfaces and no fresh review artifact exists, block the patch.
- Keep non-kernel documentation edits outside the hard block unless they modify the failure-mode catalog or closeout contracts.

### Phase 4: post-merge closeout command

- Add `agentic-kit post-merge closeout <pr>` and `removed legacy-wrapper route post-merge-closeout <pr>`.
- Wrap existing primitives rather than reimplementing them: merge commit inspection, main CI verification, evidence finalize-log, evidence inspect with `--require-summary`, state-freshness-check, handoff-check, governance-check, and doctor.
- Produce a structured closeout report.

### Phase 5: promote unambiguous hazards from WARN to BLOCK

- Promote only deterministic cases: dirty worktree, missing catalog, invalid catalog, stale review artifact, missing required known failure-mode ids, missing post-merge main-CI verification for merge closeout.
- Do not promote semantic recommendations to hard blockers.

## Known failure-mode catalog contract

The catalog path is `.agentic/failure_modes.yaml`.

The catalog must contain at least these ids:

```yaml
failure_modes:
  - id: false-pass-already-done
    surface: pass-already-done
    question: "Can generic no-op text hide a hard failure?"
    required_commands:
      - "agentic-kit pass-already-done"
    required_tests:
      - "tests/test_pass_already_done.py"

  - id: red-ci-opaque
    surface: pr-status
    question: "Can red CI be reported without failed check diagnostics?"
    required_commands:
      - "removed legacy-wrapper route pr-status <pr>"
    required_tests:
      - "tests/test_next_turn_pr_status.py"

  - id: unverified-main-after-merge
    surface: merge-if-green
    question: "Can merge success be reported before main CI is verified?"
    required_commands:
      - "removed legacy-wrapper route merge-if-green <pr>"
    required_tests:
      - "tests/test_next_turn_merge_if_green.py"

  - id: head-changed-between-check-and-merge
    surface: merge-if-green
    question: "Can a different commit be merged than the one checked?"
    required_commands:
      - "removed legacy-wrapper route merge-if-green <pr>"
    required_tests:
      - "tests/test_next_turn_merge_if_green.py"

  - id: stale-handoff-successor
    surface: handoff prompt
    question: "Can stale successor handoff content override the current safe state?"
    required_commands:
      - "removed legacy-wrapper route handoff-check"
      - "removed legacy-wrapper route state-freshness-check"
    required_tests:
      - "tests/test_handoff_freshness.py"

  - id: stale-active-handoff-next-step
    surface: handoff state
    question: "Can active next-step text point to already-recorded closeout evidence or stale release state?"
    required_commands:
      - "removed legacy-wrapper route state-freshness-check"
    required_tests:
      - "tests/test_state_freshness.py"
```

## Archived next-slice review command proposal

Status: superseded
Status-date: 2026-07-09
Superseded-by: src/agentic_project_kit/cli_commands/ and current transfer workflow commands

This archived section records an early command proposal only.
It is not a current executable route and must not be used as an operator instruction.
### Required checks

The command must inspect:

- current branch
- dirty worktree state
- current short HEAD
- existence and parseability of `.agentic/failure_modes.yaml`
- required failure-mode ids
- existence of `docs/STATUS.md`
- existence of `.agentic/handoff_state.yaml`
- existence of `docs/handoff/CURRENT_HANDOFF.md`
- optional review artifact freshness when a review artifact path is provided

### Output format

Default output must be YAML-compatible text with this shape:

```yaml
result: PASS | WARN | BLOCK
safe_state:
  branch: "<branch>"
  dirty: true | false
  main_head: "<short-sha-or-unknown>"
  evidence_anchor: "<path-or-null>"
  status_handoff_freshness: checked | missing
risk_review:
  - id: false-pass-already-done
    status: checked | missing | stale
    surface: pass-already-done
    required_tests_present: true | false
recommended_next_slice:
  title: "<string>"
  allowed_files:
    - "<path>"
blocked_reasons:
  - "<string>"
warnings:
  - "<string>"
```

### Exit-code contract

- `PASS`: exit `0`
- `WARN`: exit `0` in Phase 1
- `BLOCK`: exit `2`
- invalid catalog, internal error, or unreadable required file: exit `1` unless explicitly classified as `BLOCK`

### Phase-1 BLOCK rules

The command must return `BLOCK` when:

- the worktree is dirty
- `.agentic/failure_modes.yaml` is missing
- the catalog is invalid or lacks a required failure-mode id
- any required active handoff/status file is missing
- a supplied review artifact has `main_head` different from the current HEAD

## Review artifact contract

Phase 1 may support an optional argument such as:

```bash
agentic-kit next-slice review --review-artifact docs/reports/next_slice_reviews/<timestamp>-<mainsha>.yaml
```

A review artifact must include:

```yaml
generated_at: "<ISO-8601 timestamp>"
command_version: 1
main_head: "<short sha>"
failure_mode_catalog_sha256: "<sha256>"
result: PASS | WARN | BLOCK
reviewed_surfaces:
  - pass-already-done
  - pr-status
  - merge-if-green
  - handoff prompt
allowed_scope:
  - "<path>"
```

A stale artifact must be rejected when `main_head` does not match the current HEAD.

## Test contract

Phase 1 must add or update tests for these behaviors:

- `test_failure_mode_catalog_loads_required_ids`
- `test_next_slice_review_blocks_dirty_worktree`
- `test_next_slice_review_blocks_missing_catalog`
- `test_next_slice_review_reports_known_failure_modes`
- `test_next_slice_review_rejects_stale_review_artifact`
- `test_cli_exposes_next_slice_review_command`
- `test_next_slice_review_output_is_yaml_parseable`

## Documentation integration

- `docs/TEST_GATES.md` must list the canonical `agentic-kit next-slice review` gate once Phase 1 exists; removed wrapper shortcuts are historical only.
- `docs/STATUS.md` may reference only the current next safe slice. It must not contain the full plan.
- `docs/handoff/CURRENT_HANDOFF.md` may reference only the next safe phase and must not duplicate the full plan.
- `docs/DOCUMENTATION_REGISTRY.yaml` must register this planning document if the registry requires planning documents to be enumerated.

## Acceptance for the initial planning PR

The planning PR is complete when:

- this document exists
- the plan is discoverable through the documentation registry or equivalent documentation index
- `docs/TEST_GATES.md` references the future Phase-1 gate as planned, not active
- protected-change-plan passes for the actual diff
- docs/checks pass

## Acceptance for Phase 1 implementation PR

The Phase 1 implementation PR is complete when:

- `agentic-kit next-slice review` exists
- removed legacy wrapper shortcut is not required
- the command emits YAML-compatible structured output
- required ids from `.agentic/failure_modes.yaml` are checked
- dirty worktree blocks with exit `2`
- stale review artifacts block with exit `2`
- missing catalog blocks with exit `2`
- tests listed in the Test contract pass
- full project gates pass
- protected-change-plan passes for the actual diff
