# Successor Chat Handoff After PR714

## 1. Working Environment

Repository: `vfi64/agentic-project-kit`
Default branch: `main`
Remote: `github.com:vfi64/agentic-project-kit`
Release line: `v0.4.1`

Do not start from chat memory. Reconstruct current state from the remote repository, PR metadata, committed evidence, and the mandatory sources below.

## 2. Safe State

Branch: `main`
Commit: `7d092cb`
Subject: `Add workflow guard diagnostics (#714)`
Semantics: `current_main_head`
Working tree expected clean: `true`

PR #714 is the last substantive safe state. It added workflow-guard diagnostics, integrated the guard into patch preflight, restored protected-control-file preservation coverage, removed hard word limits from protected control files, and aligned tests with the no-hard-limit policy.

Local verification evidence reported before the closeout branch:
- Targeted tests: 21 passed
- Full pytest: 929 passed
- Ruff: PASS
- check-docs: PASS
- doctor: PASS
- workflow-guard: PASS
- patch-preflight: PASS
- Evidence: `docs/reports/terminal/pr714-verify-after-test-alignment.log`

## 3. PR715 Closeout State

PR #715 is the administrative post-PR714 closeout branch `post714-state-refresh`.
It must be checked before merge. Do not blind-merge it.

Required checks:
- PR state is open.
- Head SHA matches the latest `post714-state-refresh` head.
- CI/status checks are complete and successful.
- Mergeability is clean.
- No conflicts are reported.
- Changed files are only closeout/governance/evidence files for post-PR714 state repair.

After merge, sync/verify `main` and confirm these files exist on main:
- `docs/STATUS.md`
- `.agentic/handoff_state.yaml`
- `docs/handoff/CURRENT_HANDOFF.md`
- `docs/reports/terminal/v041-successor-chat-handoff-after-pr714.md`
- `docs/reports/terminal/v041-handoff-after-pr714.log`

## 4. Mandatory Sources Before Mutation

Read these first, in order:
1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
9. `.agentic/handoff_state.yaml`
10. relevant source files and tests for the requested slice

If any mandatory source is missing, contradictory, or stale, stop product work and repair the drift first.

## 5. Communication And Evidence Rules

User shorthand is a communication signal, not evidence:
- `d` or `D`: a local block appears done. Verify the previous terminal output or repo evidence before treating it as success.
- `f` or `F`: failure was reported. First inspect the remote or local evidence. Ask for pasted output only when evidence is unavailable, unusable, lost, or the process was killed.
- `w` or `W`: continue under the current governance and evidence rules.
- `paste-output`: manual paste is allowed only when repo-backed or local evidence is unavailable or unusable.

No-copy/evidence rule: normal PASS and normal FAIL handoffs must be log-backed. Manual copy-and-paste is the fallback, not the default.

Remote log lookup rule: when a summary names `docs/reports/terminal/*.log`, direct-fetch that exact path at the expected branch or main before claiming the log is missing.

## 6. Final Summary Contract

Relevant workflow blocks must end with the canonical structured SUMMARY defined by `docs/governance/FINAL_SUMMARY_CONTRACT.md` and rendered through the deterministic renderer route (`./ns summary` or `agentic_project_kit.run_summary_renderer`). Legacy handmade `WORK RESULT:` / `NEXT_CHAT_REPLY:` summaries are drift.

Required consistency principles:
- A final PASS is invalid after an inner required gate failed.
- Successful evidence upload cannot relabel failed work as PASS.
- `REMOTE_EVIDENCE: PASS` requires committed/pushed evidence or equivalent remote-readable evidence.
- `CHAT_REPLY: d` is valid only for an actually successful and evidence-backed result.
- `CHAT_REPLY: f` is for log-backed failure.
- `CHAT_REPLY: paste-output` is for missing or unusable evidence.
- `REMOTE_EVIDENCE` in a final summary must be one of `PASS`, `FAIL`, `PARTIAL`, or `NOT_REQUIRED`.

## 7. Active Rules To Preserve

The following rules were repeatedly lost or weakened during long-chat drift and must be treated as active:
- repository state is the source of truth, not chat memory;
- remote GitHub work with known paths, refs, PRs, or commits is direct-path-first;
- governance YAML changes are structured parse-modify-dump mutations with parse validation;
- protected control files must not lose active rules; hard length-limit trimming is forbidden;
- structured SUMMARY is mandatory for relevant work blocks;
- `d` and `f` must trigger evidence inspection, not blind continuation;
- remote logs must be direct-fetched before asking for pasted terminal output;
- recurring workflow failures must become tests, guards, or repo-backed rules;
- documentation-management work remains paused until summary enforcement is hardened.

## 8. Next Work After PR715 Merge

Do not return directly to documentation-management registry/projection work.

First create a small, test-backed hardening slice:

Title suggestion: `Enforce structured final summaries`

Goal: enforce canonical structured SUMMARY handling across renderer, workflow guard or patch preflight, terminal logs, command reports, handoff/successor prompts, and chat/workflow contracts.

Minimum scope:
- Verify and, if needed, repair `FINAL_SUMMARY_CONTRACT.md`.
- Link `CHAT_COMMUNICATION_CONTRACT.md` and `CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md` clearly to the final summary requirement.
- Reflect the rule in `.agentic/compiled_agent_context.yaml`.
- Extend workflow guard or patch preflight so missing, malformed, legacy, or contradictory summary blocks in relevant evidence files are reported.
- Add regression tests for valid, missing, contradictory, and invalid final-summary states.
- Do not perform a broad documentation migration.
- Do not create a release, tag, or DOI change.
- Do not implement unrelated product logic.

Only after this summary-hardening slice is green and merged should the documentation-management rebuild resume.

## 9. Planned Follow-Up After Summary Hardening

Resume the documentation-management rebuild in small additive slices only. Preferred next targets:
- extend Artifact-GC or policy-registry consumers;
- stabilize machine-readable documentation registry projections.

Broad migration remains forbidden.

## 10. Immediate First Instruction

Check PR #715 remotely. If CI and mergeability are green, merge it, sync/verify main, confirm the closeout files on main, and then begin the structured-summary enforcement slice. If PR715 is red or not mergeable, do not do product work; reconstruct the cause from PR/CI/evidence and repair only that drift.
