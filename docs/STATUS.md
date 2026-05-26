## Post-PR809 Current-State Override

Current verified main HEAD: `ee87fa57ed9372c758e68770478b5783878b506d` (`ee87fa5`).

PR #809 `Document finalize-log closeout and harden protected changes` is merged. It adds the finalize-log summary-contract addendum, hardens `protected_change_planner.py` against broad protected-file rewrites, extends direct tests, and registers the protected-change planner as a `patch-preflight` protected surface.

Authoritative recovery evidence: `docs/reports/terminal/pr809-merge-finalize-summary-recovery.log`. The earlier `docs/reports/terminal/pr809-merge-finalize-summary.log` is ambiguous and superseded by this recovery log.

Immediate next safe step: refresh handoff/status state after PR809, then continue only through guarded diffs, `protected-change-plan`, targeted gates, PR, merge, and `agentic-kit evidence finalize-log` evidence.


<!-- v042-safety-release-prep -->
# Project Status

Status-date: 2026-05-25
Project: agentic-project-kit
Primary branch: main
Current work branch: main
Current version: 0.4.2

## Purpose

agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Durable project memory belongs in versioned repository files, deterministic gates, evidence logs, and explicit handoff state rather than chat transcripts.

The repository is the source of truth; chat memory is not a source of truth. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current-State Boundary

`docs/STATUS.md` is the live current-state dashboard. It must stay concise and must not accumulate release history, old planning fragments, or chat transcripts. Long-term history belongs in `CHANGELOG.md`, verified release/DOI history, architecture/governance contracts, or terminal evidence logs.

This document is a concise pointer, not a duplicate rule book. Machine guard: `agentic-kit docs-audit` enforces the current-state headroom boundary and fails if `docs/STATUS.md` exceeds the configured word limit. This is a hard drift signal.

## Current State

Prepared release: 0.4.2.
Prepared release tag: v0.4.2.
Zenodo concept DOI: `10.5281/zenodo.20101359`.
Previous verified Zenodo version DOI: `10.5281/zenodo.20357657`.
v0.4.2 GitHub Release publication and post-release Zenodo verification are pending; previous v0.4.1 verification remains the current verified DOI anchor until post-release closeout. The guarded command remains `agentic-kit post-release-check --version 0.4.2` after GitHub Release publication and archive processing.

v0.4.2 safety-release target:
- Main is refreshed after PR #766 at `cf75340` (`Plan rule registry improvement backlog (#766)`).
- PRs #718-#764 established and closed out the governed rule-registry direct-coverage baseline: mechanism inventory, migration map, validator, CLI command, workflow-guard integration, patch-preflight integration, deterministic metadata/conflict/completeness checks, direct test coverage for all active mechanisms, an empty direct-test follow-up plan, and explicit machine-readable plus human-readable completion reporting.
- The governed rule registry currently covers twelve active mechanisms: summary-renderer, execution-mode-switch, rule-preservation-guard, workflow-guard, patch-preflight, chat-communication-rules, chat-bootstrap-drift-rules, portable-execution-rules, evidence-guard, typed-work-order-runner, release-state-validation, and post-release-archive-check.
- Rule registry drift is checked through `agentic-kit rule-registry check`, workflow-guard, and patch-preflight.
- Rule registry completion is now explicitly reportable through `agentic-kit rule-registry report` and `agentic-kit rule-registry report --json`; the JSON summary includes `direct_coverage_complete`.
- Evidence is preserved in committed terminal logs including `docs/reports/terminal/pr737-rule-registry-release-evidence.log`, `docs/reports/terminal/pr739-rule-registry-source-evidence-validation.log`, `docs/reports/terminal/pr740-rule-registry-surfaces-tests-inventory.log`, `docs/reports/terminal/pr741-rule-registry-surfaces-tests-inventory-recovery.log`, `docs/reports/terminal/pr742-rule-registry-surfaces-tests-validation.log`, `docs/reports/terminal/pr761-chat-communication-direct-coverage.log`, `docs/reports/terminal/pr762-chat-bootstrap-drift-direct-coverage.log`, and `docs/reports/terminal/pr764-rule-registry-completion-reporting.log`.
- Next immediate task: merge and verify v0.4.2 release metadata, publish the v0.4.2 tag/release, then run post-release verification before opening the successor-chat handoff.

Documentation registry baseline:
- `docs/DOCUMENTATION_REGISTRY.yaml` is the additive machine-readable registry.
- `docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md` is the human contract.
- `docs/DOCUMENTATION_COVERAGE.yaml` and documentation coverage remain active gate inputs.
- `agentic-kit docs-registry` shows the read-only summary.
- `agentic-kit docs-registry --report PATH` writes the JSON report.
- The registry is visible in `check-docs`, `docs-audit`, `doc-mesh-audit`, `doc-lifecycle-audit`, `handoff check`, `handoff show`, `release-check`, and `post-release-check`.
- `.agentic/communication_artifacts.yaml` is consumed as read-only artifact-policy input.
- The registry guard is structural only and does not prove semantic documentation quality.

Workflow hardening baseline:
- GitHub connector direct-path-first is the required remote route for known repository paths, refs, PRs, and commits.
- Governance YAML mutation must use parse-modify-dump or an equivalent structured mutation path, then parse again.
- `.agentic/control_file_preservation.yaml` protects active rules from lossy shortening.
- Information preservation outranks compactness for protected control files. Hard length-limit trimming is forbidden; large protected files must be split, referenced, or generated instead of losing active rules.
- Rule registry artifacts are governed inputs: `.agentic/rule_mechanism_inventory.yaml`, `.agentic/rule_migrations.yaml`, `.agentic/rule_test_coverage.yaml`, and `.agentic/rule_direct_test_plan.yaml`.
- `agentic-kit rule-registry check`, workflow-guard, and patch-preflight are the current hard enforcement path for the governed rule registry.
- remote inspection evidence contract and remote evidence present: standard PASS/FAIL work must preserve logs under `docs/reports/terminal` before asking for paste-output.
- no-copy/evidence remains active: `d` and `f` are acknowledgements only; inspect evidence before continuing.
- long chat-generated shell or Python patch blocks are disfavored; shell is a runner, not a patch language.

GUI MVP baseline:
- `cockpit-readiness`, `doctor`, and `check-docs` visually pass as bounded read-only GUI actions.
- Action Registry is the single source of allowed GUI actions.
- `agent-run` and non-read-only actions remain disabled in the GUI MVP.
- Headless GUI action execution tests cover the bounded read-only action executor.
- v0.3.30 GUI Readiness Hardening Plan and v0.3.30 GUI Readiness Hardening Closeout remain historical anchors; v0.3.30 was not the Tkinter GUI release, and Tkinter remains explicitly deferred.
- Tkinter cockpit remains an anchor term for pre-GUI boundary checks.
- Tkinter is explicitly deferred until these contracts pass gates.
- Communication artifact GC hardening is now part of the pre-GUI baseline.

## A1 State Refresh Addendum

Remote main is refreshed after Protected Change Planner A1.

- Current verified main HEAD: `c07f8ece568501771849bd922aefd1f8ed169ff6`.
- PR #791 `Expose protected change planner through ns` is merged.
- `./ns protected-change-plan --diff-file <file>` is available as a read-only route.
- A1 verification evidence: `docs/reports/terminal/protected-change-planner-a1-merge-verify.log`.
- The A1 verification log contains an expected negative planner smoke that prints `### RESULT: FAIL ###`; this is not an unresolved gate failure, but it exposes the next standard-error hardening target: expected negative smokes must not look like final workflow failures.

Next safe slice: harden final-summary and expected-negative-smoke reporting so each workflow has exactly one canonical final SUMMARY and expected blocking tests are clearly scoped.

## Current Goal

Prepare and publish the v0.4.2 safety release after the governed rule-registry baseline and accepted improvement backlog. Documentation-management rebuild work resumes only after release and successor-chat handoff closeout.

## Active Workflow Rules

- Read mandatory successor-chat sources before mutation.
- Use repo state as source of truth; do not reconstruct current state from chat memory.
- Treat repeated workflow errors as product defects to be fixed with guards, tests, or repo-backed rules.
- Keep `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, `.agentic/handoff_state.yaml`, and `CHANGELOG.md` in their correct roles.
- Use project-local interpreter/tooling first.
- Preserve relevant PASS and FAIL terminal output remotely under `docs/reports/terminal/*.log` whenever technically possible.
- Relevant terminal blocks must render the structured Final summary contract in terminal output before log upload; example evidence field: terminal_log=docs/reports/terminal/<name>.log.
- `d`, `f`, `w`, and `p` are communication signals, not evidence.
- Remote-first no-guess: do not guess repository state; inspect known remote paths, PRs, commits, logs, and command help first.
- Remote command first is a delivery preference, not a permission bypass or a reason to skip evidence.
- Remote-log evidence is mandatory for standard-error hardening slices.
- FAIL without terminal kill uses NEXT_CHAT_REPLY: f and must first inspect the repo-backed log before requesting paste-output.
- Remote inspection evidence contract: logs and command reports that matter for later reasoning must be committed, pushed, and registered for later GC.
- no-remote-command-deadlock applies: remote command output must not depend on manual paste when remote or local evidence exists.
- Ruff must run only on Python sources or Python files; shell files use shell checks, not Ruff.
- Generated terminal blocks must avoid heredocs, risky multiline `python -c` snippets, and quote-prone constructs.
- Recent CHANGELOG release entries from v0.3.36 onward are guarded structurally.
- Typed Work Orders Pre-GUI Execution Path remains the preferred pre-GUI execution path, with the minimal typed Work Order Runner as the pre-GUI bridge without chat-generated patch scripts; thin Tkinter cockpit must consume these typed contracts.
- Documentation registry changes must remain additive, modular, reversible, and test-backed.
- Remote repo inspection should use the GitHub connector direct-path-first workflow when path, commit, PR, or branch is known.
- Governance YAML must be changed through parse-modify-dump and validated after mutation.
- Protected control files must preserve active rules unless an explicit successor migration is recorded and tested.
- Structured SUMMARY drift is blocking drift: missing, malformed, contradictory, or legacy summaries must be fixed before product or documentation-management work continues.
- GUI readiness hardening, not a Tkinter implementation, remains the pre-GUI boundary before any bounded Tkinter MVP work.
- GUI expansion is intentionally paused until the current hardening slice is green.

## Documentation and Communication Contracts

Mandatory successor-chat source order is defined by `.agentic/compiled_agent_context.yaml` and checked by `agentic-kit docs-audit`:
1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`

Mandatory Final Summary Contract: relevant workflow blocks must end with the framed SUMMARY contract containing WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, CHAT_REPLY, and the final result marker. No executable placeholder summaries and final-summary-no-executable-placeholders remain active.

No-copy/evidence contract: `d` means a log-backed block appears finished; evidence must still be inspected. `f` means failure was reported; first inspect remote or local evidence and request pasted output only when evidence is unavailable or unusable.

Pattern Advisor baseline: Pattern Advisor is an advisory-only read-only catalog; `patterns list` and `patterns show` are guarded anchor commands. policy-pack doctor checks and policy packs remain guarded status terms.

Planning-state freshness compatibility: Current released version: 0.3.29 and Current released version: 0.3.32 remain retained legacy anchors only for deterministic historical tests; Verified Zenodo version DOI: `10.5281/zenodo.20314341`; the current version is 0.4.1.

v0.3.36 current-state cleanup started as a documentation-only line; the current active line is the governed rule-registry direct-coverage baseline.

Recent closeout anchors retained for handoff/status sync: PR #650 merged; PR #651 merged; PR #652 merged.

## Live Status Commands

Use project-local commands first: `./ns state`, `./ns check-docs`, `./ns doctor`, `./ns docs-audit`, `./ns handoff-check`, `./ns governance-check`, `./ns rule-registry check`, `agentic-kit check-docs`, `agentic-kit doctor`, `agentic-kit rule-registry check`, `agentic-kit rule-registry report`, and `agentic-kit handoff prompt` when installed through the active project environment.

The documentation registry can be inspected through `agentic-kit docs-registry` and exported with `agentic-kit docs-registry --report PATH`.

## Gate Status

Required gate set for current-state, handoff, or governance-summary changes:
- `./ns state-freshness-check`
- `./ns handoff-check`
- `./ns governance-check`
- `./ns rule-registry check`
- `./ns patch-preflight`
- `./ns docs-audit`
- `./ns dev`
- `agentic-kit check-docs`

## Next Safe Step

Merge and verify v0.4.2 release metadata, then publish the v0.4.2 tag/release and run post-release checks. After release closeout, start a new chat with a detailed handoff before resuming documentation-management work.
