# Master Implementation Q — CM → LC/ID → P4–P6 → LC3/TH1 → L

Status: active
Status-date: 2026-07-10
Decision status: accepted
Review policy: review_after:release:>=0.4.13
Supersedes: previous direct P4/P5/P6 ordering
Repository: vfi64/agentic-project-kit

This document is the central planning anchor for Master Implementation Q.

## Evidence anchor

K3 closeout documentation was merged by PR #1776.
Merge commit: 7ef6ba8cf3b782c5b521e8ee1ad45b473c6a2bb8

## Binding sequence

One slice equals one branch and one PR.

1. CM1 → CM2 → CM3 → CM4
2. LC1 → LC2 → ID1
3. K3 → P4a → P4b → P5a → P5b → P5d → P5c-PLAN → P6a → P6b
4. LC3 → TH1
5. L0 → L1 → L2 → L3 → L4 → L5

K3 is completed by PR #1776.

## Updated planning consequence for P4, P5, and P6

P4, P5, and P6 are no longer the next immediate workstream after K3.
They now run only after CM1 through CM4, LC1 through LC2, and ID1 are completed or verified done by Turn 0.

New P4 through P6 order:

1. P4a namespace defaults.
2. P4b resolver sweep and closeout evidence.
3. P5a self-hosting manifest.
4. P5b resolver alias evidence and suite guard.
5. P5d legacy profile deprecation.
6. P5c physical migration plan only; execution remains blocked.
7. P6a GUI project selection.
8. P6b operating-layer quickstart and CI template tests.

## Turn-0 generated handoff report hygiene

Before Turn-0 state probes are evaluated, the executor must inspect the worktree.

If and only if the only dirty tracked files are these generated transfer handoff reports, they are restored before continuing:

- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json
- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log

Any other dirty file remains a hard stop.

CM1 must fix this durably: a successful transfer refresh-llm-context-carriers run must not leave tracked generated transfer handoff reports dirty. The fix needs a regression test.

## Delta Q0

The generated handoff report dirty-state bug is handled operationally in Turn 0 and fixed durably in CM1.

## Maintainer-gated stops

- P5c physical migration execution.
- strict lifecycle switch in the kit repository.
- --strict-unknown.
- propose-delete execution.
- first Comm-SCI adoption.
- the 2.0 line.
