> STATUS boundary: This document uses concise pointers, not duplicate rule books. Machine guard: `agentic-kit docs-audit` enforces the current-state headroom boundary.

## Current State

Current version: 0.4.12
Current verified release: 0.4.12.
Current release tag: v0.4.12.
Zenodo concept DOI: `10.5281/zenodo.20101359`.
Verified Zenodo version DOI: `10.5281/zenodo.21135030`.
Current verified main: `de11f556` (`LC3: Remediate mutation lock coverage (#1843)`).
Latest substantive work: PR #1843 (`LC3: Remediate mutation lock coverage (#1843)`).
Post-merge handoff status: PASS/NOOP after PR #1843 administrative refresh.
Next safe step: continue from fresh main with the next planned governed slice.

## Historical State Snapshots

### Release Command Authority Planning Slice Refresh

Historical planning-slice branch: `codex/release-command-authority-plan`.
Historical planning-slice commit: `1becc4a7` (`Plan release command authority slice`).
Historical planning PR: #1436 (`[codex] Plan release command authority slice`).

This slice recorded `docs/planning/PROJECT_DIRECTION.yaml#release-command-authority-slice` as the first implementation step after v0.4.9. It is historical and must not be treated as the current next step.


## Post-PR1245 Administrative Handoff Refresh State

Current main/admin HEAD: `e97af592` (`Refresh handoff state after PR1244 (#1245)`).
Last substantive work marker: `7f5a331` / PR #1244 (`Enforce operational handoff document freshness`).

This is an administrative handoff/evidence refresh after PR #1244. It does not replace the substantive safe-state intent. It exists so operational handoff freshness no longer points at stale PR1011-era prompts.

Next safe substantive slice: implement the professional operational documentation projection system from a machine-readable state source, with generated blocks, preservation of curated documentation, rule-registry coverage, and drift gates.

## Post-PR1243 Operational Handoff Freshness State

Current verified main HEAD is `88e01f46f4928174ea241039e0a863f28570130a` (`88e01f46`).
Last substantive work state is `4bf3da29` (`Render transfer payload commands as compact summaries (#1242)`).
Administrative refresh PR #1243 is merged.

Recent completed transfer hardening:
- PR #1238: transfer continue self-healing.
- PR #1240: RepoActionResult terminal output now renders compact START/END SUMMARY by default.
- PR #1242: selected transfer payload commands now render compact START/END SUMMARY by default while preserving `--json`.

Operational handoff freshness now includes working-state documentation, not only release state:
`docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, successor/bootstrap prompts, and the active roadmap must mention the current safe/admin commit markers before a handoff is treated as authoritative.

Next safe step: continue with the remaining transfer-safety line only after this freshness slice is merged and post-merge-check reports NOOP. Do not treat older PR1054/PR880 roadmap anchors as current state.


## Post-PR897 Handoff Refresh State

Current verified main HEAD is `a766ce92bbd4fc6cebfbb3ce3762bfa56e79c60c` (`a766ce9`).
Commit subject: `Harden standard summary log classification (#897)`.

PR #897 is merged. This is an administrative post-merge handoff/status refresh before chat handoff.

The post-merge handoff refresh status gate is the canonical decision point after merges: `agentic-kit handoff post-merge-refresh-status`.

Next safe step after this refresh is merged and verified: start the successor chat from the fresh prompt and continue only if the machine-readable refresh status is `result=NOOP`.

## Post-PR894 Handoff Refresh State

Current verified main HEAD is `87407ac463b46638f340fc757ec452c46e803096` (`87407ac`).
Commit subject: `Merge pull request #894 from vfi64/docs/post-merge-gate-bootstrap-visibility`.

PR #894 is merged. This is an administrative post-merge handoff/status refresh before chat handoff.

The post-merge handoff refresh status gate is the canonical decision point after merges: `agentic-kit handoff post-merge-refresh-status`.

Next safe step after this refresh is merged and verified: start the successor chat from the fresh prompt and continue only if the machine-readable refresh status is `result=NOOP`.

## Post-PR892 Handoff Refresh State

Current verified main HEAD: `64f5c4d49e4012e42170b47e6bcf48bf383e8a94` (`64f5c4d`).
Commit subject: `Merge pull request #892 from vfi64/feature/post-merge-gate-visibility-inventory`.

PR #892 is merged. It recorded a read-only inventory of where the post-merge handoff refresh status gate is visible.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: move the post-merge refresh status gate into a more visible kit/ns workflow path without broad product-code changes.

## Post-PR888 Patch Preflight Slice-Gate State

Current verified main HEAD: `508f3dfa2be50d4f369f31e270cc930c24873015` (`508f3df`).
Commit subject: `Merge pull request #888 from vfi64/feature/patch-preflight-slice-gate-clean`.

PR #888 is merged. It adds the optional `agentic-kit patch-preflight --require-slice-gate planning-doc` path so patch preflight can require deterministic slice-gate evidence and a clean worktree before accepting planning-document preflight readiness.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: continue with the smallest gatekeeper-hardening slice, using the slice gate and patch preflight before PR creation or merge claims.

## Post-PR886 Workflow Evidence Hygiene State

Current verified main HEAD: `d77d5804d7eead98ff65b52e38c6d73bc640051c` (`d77d580`).
Commit subject: `Merge pull request #886 from vfi64/codex/fix-workflow-evidence-hygiene`.

PR #886 is merged. It fixed workflow evidence hygiene by writing active next-turn/work-order results first to a local temporary path, making the repo-backed fixed slot an explicit upload/promotion artifact, validating `repo_root` on upload, allowing artifact GC to remove untracked fixed-slot artifacts, and accepting canonical `SUMMARY COMM-...` evidence logs in patch preflight.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: continue with the smallest gatekeeper-hardening slice, using `agentic-kit slice gate --kind planning-doc` before PR creation or merge claims.

## Post-PR883 GUI Gatekeeper Inventory State

Current verified main HEAD: `1ec13cb5283d9b796b667526791eaa94a04073ff` (`1ec13cb`).
Commit subject: `Merge pull request #883 from vfi64/feature/gui-gatekeeper-inventory-helper`.

PR #883 is merged. It added the GUI gatekeeper implementation inventory as a read-only planning/inventory slice, registered the new planning document, recorded the generator and evidence logs, and captured the recurring failure mode that a helper-local PASS is not a slice PASS until the required repository governance gates also pass.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: implement the smallest temporary Python slice-gate command for planning/documentation slices so helper-local PASS can no longer be confused with slice PASS before PR creation, upload, or merge.

## Post-PR881 Bootstrap Refresh State

Current verified main HEAD: `1bb1c0d4b1f0d937314f245217cda9266ed0d106` (`1bb1c0d`).
Commit subject: `Refresh bootstrap handoff after PR880`.

PR #881 merged the post-PR880 bootstrap/handoff refresh. Its merge commit used a custom subject, so this administrative refresh records the actual post-PR881 main HEAD before any GUI product work.

Current verified release remains v0.4.4.
Verified Zenodo version DOI remains `10.5281/zenodo.20431326`.

Next safe step after this refresh is merged and verified: start the GUI deterministic gatekeeper migration only as the smallest reversible read-only inspection/inventory slice.

## Post-PR880 Bootstrap Refresh State

Current verified main HEAD: `f853ccf770e5f692ca2815912b252e453259fc69` (`f853ccf`).
Commit subject: `Merge pull request #880 from vfi64/fix/handoff-freshness-admin-merge-chain`.

PR #880 is merged. It hardens the handoff freshness guard so direct administrative merge commits and bounded first-parent administrative merge chains are accepted while product merges inside such chains remain blocking.

Current verified release: v0.4.4.
Verified Zenodo version DOI: `10.5281/zenodo.20431326`.

Bootstrap status: administrative refresh required before GUI product work, because prompt/status/handoff files still contained older PR #838, PR #877, PR #873, or PR #834 anchors.

Next safe step after this refresh is merged and verified: start the GUI deterministic gatekeeper migration only as the smallest reversible read-only inspection/inventory slice. Do not start broad GUI product work.

## Post-PR873 GUI Gatekeeper Planning State

Current verified main HEAD: `5b30fe30ed9b813255fb9a89d85a6f7bf1ab70ab` (`5b30fe3`).
Commit subject: `Record PR873 final main closeout evidence`.

PR #873 baseline: `Add GUI work order upload strip (#873)`, commit `23532a0`. Final closeout evidence: `docs/reports/terminal/pr873-final-main-closeout.log`.

Planning document: `docs/planning/PROJECT_DIRECTION.yaml`.

PR #874 is planning/state-refresh only. It records the GUI deterministic gatekeeper migration plan and refreshes state pointers. It must not include product-code changes.

Required sequence:
1. Finish planning-only PR #874.
2. Prepare and publish safety release v0.4.4.
3. Generate fresh successor-chat handoff.
4. Start the gatekeeper migration PR series in small reversible PRs.

Next safe step: finish this planning/state-refresh PR; do not start gatekeeper implementation or further GUI feature work before v0.4.4 is released and post-release verified.

## Post-PR838 Administrative Handoff Refresh State

Current administrative main HEAD: `777d957474318fdf797ca23625e52046c3fb7df0` (`777d957`), after PR #838 refreshed post-PR837 administrative handoff state.

PR #837 `Record post-PR836 successor handoff` is merged at `71ba85b5322e26c52680b0dbfe38d81957bb1160` (`71ba85b`). PR #838 `Refresh post-PR837 administrative handoff state` is merged at `777d957474318fdf797ca23625e52046c3fb7df0` (`777d957`).

The substantive safe-state remains `c0ac933a29b71c6660ae7e436386414f08ff9e7b` (`c0ac933`) under `safe_state.semantics: last_substantive_work_state`; later handoff-only refreshes belong in `administrative_evidence_state`.

Immediate next safe step: finish this post-PR838 handoff/status freshness refresh, then continue only with the smallest planned GUI or failure-mode automation slice.


## Post-PR834 Successor-Handoff Freshness Closeout State

Current verified main HEAD: `fd1e631312723166982fb1e0d9ecb76397e97559` (`fd1e631`).

Generated handoff safe-state anchor: `fd1e631312723166982fb1e0d9ecb76397e97559` (`fd1e631`), after PR #834 repaired generator-backed handoff freshness.

PR #834 `Repair post-PR831 handoff freshness state` is merged. PR #835 added `docs/reports/terminal/post-pr836-successor-handoff.md` and `docs/reports/terminal/post-pr836-successor-handoff.log` as the successor/evidence anchors.

v0.4.4 is published and post-release verified. Verified Zenodo version DOI: `10.5281/zenodo.20431326`. Release verification evidence: `docs/reports/terminal/v045-doi-metadata-limit-fix.log`.

Immediate next safe step: continue with the smallest planned GUI or failure-mode automation slice; stop first if handoff freshness, evidence, or status drift reappears.


## Post-PR809 Current-State Override

Current verified main HEAD: `ee87fa57ed9372c758e68770478b5783878b506d` (`ee87fa5`).

PR #809 `Document finalize-log closeout and harden protected changes` is merged. It adds the finalize-log summary-contract addendum, hardens `protected_change_planner.py` against broad protected-file rewrites, extends direct tests, and registers the protected-change planner as a `patch-preflight` protected surface.

Authoritative recovery evidence: `docs/reports/terminal/pr809-merge-finalize-summary-recovery.log`. The earlier `docs/reports/terminal/pr809-merge-finalize-summary.log` is ambiguous and superseded by this recovery log.

Immediate next safe step: refresh handoff/status state after PR809, then continue only through guarded diffs, `protected-change-plan`, targeted gates, PR, merge, and `agentic-kit evidence finalize-log` evidence.


<!-- v042-safety-release-prep -->
# Project Status

Status-date: 2026-05-27
Project: agentic-project-kit
Primary branch: main
Current work branch: codex/refresh-post-pr835-next-step-state
Snapshot package version: 0.4.10

## Purpose

agentic-project-kit is a repository-backed governance and workflow kit for long-running AI-assisted software projects. Durable project memory belongs in versioned repository files, deterministic gates, evidence logs, and explicit handoff state rather than chat transcripts.

The repository is the source of truth; chat memory is not a source of truth. Chat-only rules are not durable unless they are documented, test-backed, and enforced through repo tooling or gates.

## Current-State Boundary

`docs/STATUS.md` is the live current-state dashboard. It must stay concise and must not accumulate release history, old planning fragments, or chat transcripts. Long-term history belongs in `CHANGELOG.md`, verified release/DOI history, architecture/governance contracts, or terminal evidence logs.

This document is a concise pointer, not a duplicate rule book. Machine guard: `agentic-kit docs-audit` enforces the current-state headroom boundary and fails if `docs/STATUS.md` exceeds the configured word limit. This is a hard drift signal.

## Historical Current State Snapshot

Current verified release: 0.4.10.
Current release tag: v0.4.10.
Zenodo concept DOI: `10.5281/zenodo.20101359`.
Verified Zenodo version DOI: `10.5281/zenodo.20767675`.
Post-release verification command: `agentic-kit post-release-check --version 0.4.8`.
Current verified main after handoff freshness repair: `e07ccd4` (`Refresh handoff state after PR1386 (#1387)`).
Generated handoff safe-state anchor: `e07ccd4`.
v0.4.8 GitHub Release publication and post-release Zenodo verification are complete. Verified Zenodo version DOI: `10.5281/zenodo.20727067`.

v0.4.3 safety-release and successor-handoff target:
- Main contains PR #1387 at `e07ccd4` (`Refresh handoff state after PR1386 (#1387)`).
- PR #1387 refreshed handoff state after the v0.4.8 release PR #1386.
- Generated handoff safe-state now anchors to PR #1387 via `docs/reports/terminal/post-pr1386-successor-chat-handoff.md`.
- PR #833 recorded the corrected post-PR831 successor handoff at `docs/reports/terminal/post-pr831-successor-handoff.md`.
- PR #831 recorded PR #830 closeout evidence at `docs/reports/terminal/pr830-merge-finalize.log`.
- PR #825 hardened active handoff freshness checks so already-recorded closeout evidence and stale release-version instructions are blocking drift.
- PR #824 recorded PR #823 closeout evidence at `docs/reports/terminal/pr823-merge-finalize.log`.
- PR #823 hardened `merge-if-green` so the merge command validates the target base branch, requires a PR head SHA, passes `--match-head-commit <sha>` to GitHub, and renders checked base/head refs.
- PR #821 hardened `merge-if-green` so post-merge main-CI verification is required before the command reports clean success.
- PR #819 hardened PR status failed-log diagnostics so red CI carries check names, Actions run ids, exact failed-log commands, bounded log-fetch status, and `no-checks` classification.
- PR #817 hardened PASS_ALREADY_DONE target-state classification so generic already-exists output is not sufficient success evidence.
- PR #815 hardened release-prep atomicity and remote release readiness so inconclusive remote checks no longer permit a release PASS.
- PR #812 includes the PR811 closeout evidence log, successor-handoff YAML freshness baseline, protected-change planner YAML anchor hardening, handoff-state preservation, and the explicit opt-in Tk window-smoke guard.
- PRs #718-#764 established and closed out the governed rule-registry direct-coverage baseline: mechanism inventory, migration map, validator, CLI command, workflow-guard integration, patch-preflight integration, deterministic metadata/conflict/completeness checks, direct test coverage for all active mechanisms, an empty direct-test follow-up plan, and explicit machine-readable plus human-readable completion reporting.
- The governed rule registry currently covers twelve active mechanisms: summary-renderer, execution-mode-switch, rule-preservation-guard, workflow-guard, patch-preflight, chat-communication-rules, chat-bootstrap-drift-rules, portable-execution-rules, evidence-guard, typed-work-order-runner, release-state-validation, and post-release-archive-check.
- Rule registry drift is checked through `agentic-kit rule-registry check`, workflow-guard, and patch-preflight.
- Rule registry completion is now explicitly reportable through `agentic-kit rule-registry report` and `agentic-kit rule-registry report --json`; the JSON summary includes `direct_coverage_complete`.
- Evidence is preserved in committed terminal logs including `docs/reports/terminal/pr737-rule-registry-release-evidence.log`, `docs/reports/terminal/pr739-rule-registry-source-evidence-validation.log`, `docs/reports/terminal/pr740-rule-registry-surfaces-tests-inventory.log`, `docs/reports/terminal/pr741-rule-registry-surfaces-tests-inventory-recovery.log`, `docs/reports/terminal/pr742-rule-registry-surfaces-tests-validation.log`, `docs/reports/terminal/pr761-chat-communication-direct-coverage.log`, `docs/reports/terminal/pr762-chat-bootstrap-drift-direct-coverage.log`, and `docs/reports/terminal/pr764-rule-registry-completion-reporting.log`.
- Next immediate task: continue with the smallest planned GUI or failure-mode automation slice; stop first if handoff freshness, evidence, or status drift reappears.

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
- `agentic-kit transfer protected-diff-plan --diff-file <file>` is available as a read-only route.
- A1 verification evidence: `docs/reports/terminal/protected-change-planner-a1-merge-verify.log`.
- The A1 verification log contains an expected negative planner smoke that prints `### RESULT: FAIL ###`; this is not an unresolved gate failure, but it exposes the next standard-error hardening target: expected negative smokes must not look like final workflow failures.

Next safe slice: harden final-summary and expected-negative-smoke reporting so each workflow has exactly one canonical final SUMMARY and expected blocking tests are clearly scoped.

## Current Goal

Continue with the smallest planned GUI or failure-mode automation slice; stop first if handoff freshness, evidence, or status drift reappears.

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


The documentation registry can be inspected through `agentic-kit docs-registry` and exported with `agentic-kit docs-registry --report PATH`.

## Gate Status

Required gate set for current-state, handoff, or governance-summary changes:
- `agentic-kit state-freshness-check`
- `agentic-kit handoff-check`
- `agentic-kit rule-registry check`
- `agentic-kit patch-preflight`
- `./.venv/bin/agentic-kit docs-audit`
- `agentic-kit check-docs`

## Next Safe Step

Continue with the next smallest Release-/Evidence-Kernel follow-up. Documentation-management rebuild work remains deferred.

## Operational documentation projection state after PR #1249

Current operational documentation projection state is `dfb7c2ba` (`Introduce operational handoff projection source (#1249)`). PR #1249 introduced `.agentic/operational_handoff_state.yaml` as the first machine-readable operational handoff state source and projects the current operational bootstrap block from that source. Continue next with Slice 2: generated-block markers and targeted block updates while preserving curated documentation.

## Operational documentation refresh state

Recent admin-refresh history is compacted here to preserve documentation headroom. PR #1250, #1253, #1255, #1257, #1260, #1262, and #1264 moved operational handoff refresh toward generated, protected-plan-checked, non-accumulative updates. Current policy: use operational handoff refresh, preserve historical protected-state entries, update only current refresh metadata and successor pointers, run protected diff plan before commit, and continue from fresh main after merge.## Operational documentation refresh state after PR #1303

Current administrative handoff refresh state is `794ceff0` (`Fix operational handoff refresh newlines (#1303)`). Continue next only after this post-PR1303 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1307

Current administrative handoff refresh state is `e88a5591` (`Harden successor package freshness gates (#1307)`). Continue next only after this post-PR1307 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1311

Current administrative handoff refresh state is `afc21ade` (`Project bootstrap gate into successor package (#1311)`). Continue next only after this post-PR1311 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1317

Current administrative handoff refresh state is `23c913f9` (`Refresh successor package after PR1316 (#1317)`). Continue next only after this post-PR1317 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1324

Current administrative handoff refresh state is `75d7a3d3` (`Refresh successor package during admin handoff refresh (#1324)`). Continue next only after this post-PR1324 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1330

Current administrative handoff refresh state is `a7a0b6a2` (`Audit ns to agentic-kit migration before GUI (#1330)`). Continue next only after this post-PR1330 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1334

Current administrative handoff refresh state is `c6ab40da` (`Classify ns migration docs before GUI (#1334)`). Continue next only after this post-PR1334 refresh is committed and merged; the next substantive slice must be created from fresh main.

- Diagnostic command coverage: `agentic-kit doctor`.## Operational documentation refresh state after PR #1338

Current administrative handoff refresh state is `979825da` (`Remove ns dev go up shortcuts (#1338)`). Continue next only after this post-PR1338 refresh is committed and merged; the next substantive slice must be created from fresh main.
- Portability closeout: in progress; all tracked shell scripts removed in Slice 6, pending final gates and PR merge.
- Portability closeout: legacy `ns` and `ns-menu` entrypoints removed; no tracked shell scripts remain, pending final gates and PR merge.
## Operational documentation refresh state after PR #1730

Current administrative handoff refresh state is `ae066495` (`Refresh handoff state after PR1730 (#1731)`). The next substantive slice must be created from fresh main.
## Operational documentation refresh state after PR #1843

Current administrative handoff refresh state is `de11f556` (`LC3: Remediate mutation lock coverage (#1843)`). Continue next only after this post-PR1843 refresh is committed and merged; the next substantive slice must be created from fresh main.
