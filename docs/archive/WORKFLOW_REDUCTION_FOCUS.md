# Workflow Reduction Focus

Document class: historical archive
Status-date: 2026-07-08
Archived-from: docs/planning/WORKFLOW_REDUCTION_FOCUS.md
Superseded-by: docs/archive/PRE_GUI_HARDENING_TASKS.md and docs/planning/PROJECT_DIRECTION.yaml

Status: superseded
Superseded by: `docs/archive/PRE_GUI_HARDENING_TASKS.md` for pre-GUI hardening work and `docs/planning/PROJECT_DIRECTION.yaml` for durable strategy/roadmap authority.
Lifecycle note: This document is closed as an active direction source; current pre-GUI hardening work is governed by `docs/archive/PRE_GUI_HARDENING_TASKS.md`, and durable strategy/roadmap authority is governed by `docs/planning/PROJECT_DIRECTION.yaml`.

This file is retained as historical planning context only. Do not use the current-slice markers or roadmap items below as active work instructions; add new pre-GUI hardening content to `docs/archive/PRE_GUI_HARDENING_TASKS.md`.

## Current First Slice After v0.4.9

Current planning-slice marker: `1becc4a7` / PR #1436 (`[codex] Plan release command authority slice`).

Before DOI closeout hardening, broad legacy-doc cleanup, planning consolidation, absolute-path cleanup, or GUI work, execute `docs/planning/PROJECT_DIRECTION.yaml#release-command-authority-slice`.

That slice establishes the supported release metadata preparation route and makes the remaining release publish core portable or fail-closed after the `./ns` removal.

## First priority: Remote transfer state-machine hardening before ns replacement

Before the remaining `ns` replacement work continues, complete the transfer state-machine MVP from `docs/planning/PROJECT_DIRECTION.yaml` (`workflow-kernel-and-transfer-hardening` transfer-state MVP).

Required before further `ns` replacement slices:

1. Validate exactly-one active transfer command.
2. Validate inbox/outbox command-id correlation.
3. Detect stale `last_result` instead of accepting it as current state.
4. Detect duplicate or obsolete active transfer files.
5. Block mutable execution on local-vs-remote head drift.
6. Classify remote outages as `REMOTE_UNREACHABLE`, not success.
7. Keep all outputs machine-readable with explicit `STATE` and `NEXT`.

This is a workflow safety gate, not a broad rewrite. The goal is to make repo-backed communication deterministic before additional command-surface migration.

## Post-PR1245 Administrative Handoff Refresh State

Current main/admin HEAD: `e97af592` (`Refresh handoff state after PR1244 (#1245)`).
Last substantive work marker: `7f5a331` / PR #1244 (`Enforce operational handoff document freshness`).

This is an administrative handoff/evidence refresh after PR #1244. It does not replace the substantive safe-state intent. It exists so operational handoff freshness no longer points at stale PR1011-era prompts.

Next safe substantive slice: implement the professional operational documentation projection system from a machine-readable state source, with generated blocks, preservation of curated documentation, rule-registry coverage, and drift gates.

Status: active
Decision status: accepted
Review policy: Review after operational handoff freshness changes, after transfer-output summary hardening (#1240/#1242), before adding deterministic transfer outbox implementation, before expanding GUI scope or Pattern Advisor scope, and whenever handoff/bootstrap/status projections drift behind main.
Project: agentic-project-kit

## Purpose

This document records the near-term product focus for `agentic-project-kit` after the v0.4.1 documentation-registry baseline.

The next maturity step is not to add more advisory intelligence. The next maturity step is to reduce manual orchestration while preserving safety, evidence, and deterministic governance.

## Strategic Focus

The kit should increasingly answer these questions from repository state instead of chat memory:

- What is the current state?
- What is the next safe action?
- What is forbidden?
- What is stale?
- What evidence exists?
- Which documents are live state, governance, release history, generated artifacts, temporary artifacts, or evidence?

The goal is to move from a powerful expert tool toward a robust working instrument.

## Machine-Readable Source Direction

Operational truth should move into machine-readable sources. Human-readable Markdown should explain, summarize, or project that state instead of becoming the unverified source of state.

The governing rule is: every operational statement must be traceable to a machine-readable source of truth or to a machine-checkable anchor. This includes state, governance, next actions, evidence, release state, handoff state, registry entries, work orders, artifact retention, automation behavior, dialogue/transfer rules, and local-to-LLM transfer result context.

This does not mean that every document should be forced into YAML or JSON. README files, websites, handbooks, tutorials, architecture rationale, and explanatory notes may remain primarily human-readable. The stricter requirement applies to operative content that affects project state or executable behavior.

Target shape:

- machine-readable sources: `.agentic/handoff_state.yaml`, docs/DOCUMENTATION_REGISTRY.yaml, `.agentic/work_orders/*.yaml`, `.agentic/communication_artifacts.yaml`, future `.agentic/dialogue_rules.yaml`, release metadata, evidence manifests, gate reports, generated state summaries, and generated transfer outbox context projections;
- human-facing projections: `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, successor handoff prompts, README excerpts, handbook text, website text, GUI dashboards, and LLM-generated explanations.

LLM assistance should use the structured sources to translate project state into clear human prose on request. The LLM may explain and review; it should not be the only place where operational truth exists.

## Rule Registry Improvement Direction

The governed rule registry is the current proof point for this direction: rules have moved from chat-only memory into machine-readable inventory, migration, coverage, direct-test-plan, validation, and report artifacts.

Remaining rule-registry weaknesses must be reduced as incremental planning work, not as a second broad rebuild. The accepted backlog is `docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md`.

The improvement direction is:

1. keep the current rule-registry baseline usable while documentation-management work resumes;
2. harden the schema through typed or schema-backed validation;
3. generate human projections instead of duplicating registry state manually;
4. replace high-value `required_terms` checks with stronger behavioral or structural assertions;
5. add query and impact-analysis commands when documentation management, transfer outbox context generation, or GUI readiness needs them;
6. evaluate external policy tooling only after the internal domain model is stable.

This keeps the rule registry professional without letting perfectionism block the next documentation-registry and projection slices.

## Current Operational Roadmap State After PR1243

Current verified main HEAD is `88e01f46f4928174ea241039e0a863f28570130a` (`88e01f46`).
Last substantive work state is `4bf3da29` (`Render transfer payload commands as compact summaries (#1242)`).

Completed since the older PR1054 roadmap anchor:
- transfer continue self-healing (#1238);
- compact RepoActionResult summaries (#1240);
- compact selected transfer payload summaries (#1242);
- administrative handoff refresh after PR1242 (#1243).

The current roadmap rule is not release-only: operational handoff freshness includes the live state docs and prompts used by successor chats. Those projections must be updated or blocked through the existing handoff-freshness mechanism before handoff output is treated as authoritative.

## Priority Order

1. Close the current PR1054/B11 slice without further local product work: verify the PR state/CI, merge only when clean, sync main, run post-merge handoff checks, and preserve evidence.
2. Add the transfer-wrapper branch-safety hardening slice immediately after PR1054: `transfer push-current` must push the actual current branch or fail closed; mutating transfer wrappers must record and validate current branch, requested branch, target branch, upstream branch, and repo head before executing.
3. Add the fail-closed precondition-chain hardening slice immediately after the wrapper branch-safety slice: a failed branch switch, wrong branch, dirty blocker, failed `run-and-log`, or failed transfer report publication must block every following workflow step until explicitly resolved.
4. Clean the active rule semantics before final hardening: remove `w` from active dialogue rules, make `d/f/g` the only preferred signals, classify or obsolete legacy communication anchors, and update tests/compiled context through the rule-management workflow.
5. Complete a documentation-registry coverage audit before final hardening: identify active docs not yet registered or classified, register them in small reversible slices, and record any intentional exclusions with a machine-checkable rationale.
6. Finish any remaining B11 transfer-report contract semantics follow-up: preserve local report command semantics, make `publish-last-report` the only tracked handoff upload source, keep `show-last-report` local-only, and run the targeted transfer tests before PR creation.
7. Add the deterministic transfer outbox context projection to the rule-refresh handshake roadmap: every `.agentic/transfer/outbox/last_result.txt` write should embed a freshly extracted machine-readable header from canonical sources.
8. Introduce `.agentic/dialogue_rules.yaml` only as a tested rule-management slice, not as an unregistered parallel rule table.
9. Ensure every new documentation artifact is registered or classified through the documentation-management system, and every new durable rule is registered through the rule-management system with validation and preservation anchors where appropriate.
10. Finish the documentation-management foundation through small, additive, reversible, test-backed registry slices.
11. Use the registry to make status, handoff, evidence, artifacts, transfer outbox state, and retention/GC behavior visible and machine-checkable.
12. Build the GUI as a control surface over already-hardened read-only or bounded actions.
13. Defer Pattern Advisor expansion until the document, rule, evidence, and transfer substrates are stable.

## Work Model Direction

Future work should prefer small machine-readable work orders over long chat-orchestrated execution. A work order should state:

- slice name,
- goal,
- allowed files,
- required tests or checks,
- forbidden actions,
- closeout requirements.

Chat should describe intent. Repo-owned tools should execute typed operations. Markdown should increasingly be a curated projection of machine-readable state, not the primary state source.

## Handoff and Status Direction

Handoff prompts should be generated from state files, Git state, PR state, registry data, transfer outbox context, and gate evidence wherever possible. Manual free prose should be a curated supplement, not the source of truth.

`docs/STATUS.md` should remain a compact dashboard. Long history belongs in `CHANGELOG.md`, release records, evidence logs, or dedicated planning documents such as this file.

## Documentation Registry Completion Roadmap

The documentation registry is currently an experimental first-slice governance baseline. The contract states that the first slice intentionally registers only a small set of canonical documents and evidence logs and that broad classification must happen later in small reversible slices.

Before final hardening, the project needs a documentation-registry completion line:

1. Add or run a deterministic inventory that lists active repository documentation and classifies each file as registered, intentionally excluded, temporary, generated, historical, or pending classification.
2. Compare the inventory against `docs/DOCUMENTATION_REGISTRY.yaml` and fail closed for new active documents that bypass classification.
3. Register missing active planning, governance, architecture, workflow, handoff, release, and user-facing documents in small additive slices.
4. Record intentional exclusions with rationale instead of silently ignoring them.
5. Keep evidence logs bounded: do not register every transient log individually unless it is durable evidence; prefer class-level retention and GC policy for generated/temporary reports.
6. Add tests or `check-docs` assertions that prevent new documentation islands.
7. Update roadmap/status/handoff projections only after the registry state is machine-checkable.

## B11 Transfer And Rule-Refresh Roadmap

The current transfer line has these remaining work items from the successor-handoff prompt and subsequent planning decisions:

1. Inspect and repair the existing branch `feature/b11-transfer-report-contract-semantics` without blindly overwriting dirty local work.
2. Fix `run-and-log` and `run-sequence-and-log` so their terminal short output reports local report writing only: `TRANSFER_REPORT_WRITTEN=done`, `LOCAL_REPORT=docs/reports/transfer_runs/...`, and `CHAT_REPLY=d | NEXT=Run transfer publish-last-report`.
3. Preserve the JSON report's underlying command semantics: `final_signal`, `returncode`, and the original `next_action` must not be replaced by the publish step.
4. Keep `publish-last-report` as the only source of tracked handoff upload semantics: `TRANSFER_UPLOAD=done`, `REMOTE_REPORT=docs/reports/terminal/transfer_handoff_reports/...`, and `CHAT_REPLY=g` for successful published reports.
5. `publish-last-report` must publish failed reports as evidence without emitting `CHAT_REPLY=g`; failed published reports must emit a failure reply and a next action to inspect the published handoff report.
6. Keep `show-last-report` local-only; it must not imply a tracked handoff or remote upload.
7. Keep gitignored local reports under `docs/reports/transfer_runs/` and tracked handoff reports under `docs/reports/terminal/transfer_handoff_reports/`.
8. Move future local-to-LLM exchange toward exactly one canonical outbox file, `.agentic/transfer/outbox/last_result.txt`, generated as JSON with a deterministic context header extracted from canonical sources at each write.
9. Move future LLM-to-local exchange toward exactly one canonical inbox file, `.agentic/transfer/inbox/next_command.py.txt`, overwritten rather than accumulated.
10. Implement a local Python outbox-header builder that reads and hashes canonical sources, extracts dialogue/transfer priorities, embeds repo state, and fails closed on missing or contradictory sources.
11. Introduce `.agentic/dialogue_rules.yaml` only after schema, parser, tests, compiled-context integration, rule-mechanism inventory integration, and protected-change planning are ready.
12. Register or classify every new planning/governance/status/evidence document in the documentation-management system; do not create untracked documentation islands.
13. Register every new durable dialogue, transfer, or workflow rule in the rule-management system; do not rely on chat-only or document-only instructions when the rule affects executable behavior.
14. After green targeted tests, commit, push, create a PR only if there is a real diff against `origin/main`, wait for CI, merge only when clean, sync main, and run the post-merge handoff refresh status.
15. If post-merge status is `REFRESH_REQUIRED`, create and merge the administrative handoff-refresh PR through existing safe wrappers before continuing product work.

## Transfer Communication Safety Roadmap

This roadmap item is the immediate prerequisite for branch-safety, fail-closed precondition-chain, and GUI action hardening. The transfer channel must treat LLM-to-local transfer files as untrusted work orders, not as intrinsically safe execution artifacts.

Staged implementation:

1. Add machine-readable transfer and Python-patch safety rules to the rule-management system before relying on generated transfer-file prose. These rules must include known recurring failure classes: wrong branch execution, stale local branch after fetch, rule acknowledgement head mismatch, dirty worktree, accumulated untracked transfer or report files, failed report publication being misread as a go signal, diagnostic status success masking an earlier blocker, heredoc-style shell mutation, unescaped shell substitution, raw newlines inside generated Python string literals, quote and escape drift, fragile multiline inline Python commands, long shell mutation blocks, line-ending drift, Python transfer files with text suffixes not validated as Python source, partial patch application, fragile text-anchor patching, accidental compatibility-key removal, destructive use of moving references, implicit main push or upstream mutation, and Python files being syntactically broken before the CLI can still import.
2. Generate the local-to-LLM result file with a deterministic machine-readable rule-refresh header freshly extracted from canonical repo sources on every write. The header must include source hashes, transfer priorities, canonical inbox/outbox paths, patch-safety rules, branch/head/upstream/dirty state, and the last blocking workflow state where available.
3. Add canonical transfer execution preflight before running the LLM-to-local transfer file: verify expected branch, clean worktree, local HEAD equals upstream HEAD, rule acknowledgement matches HEAD, the canonical transfer file exists, and transfer-file content compiles as Python.
4. Add post-patch guards: every changed Python file must pass Python syntax validation before any CLI import or broader tests; failures must stop with FINAL_SIGNAL=f, preserve evidence, and must not emit go semantics.
5. Only after those guards are test-backed, harden push-current, safe stash handling, fail-closed precondition chains, and GUI button enablement on top of the guarded transfer substrate.

Acceptance tests:

- A stale local branch behind its upstream blocks canonical transfer execution before the transfer file is run.
- A rule acknowledgement for a different repo head blocks canonical transfer execution.
- A Python transfer file with invalid Python syntax is rejected before execution.
- A transfer file that generates invalid Python source fails at the post-patch syntax gate before any CLI import is attempted.
- Generated local-to-LLM result state includes the machine-readable safety header from repo rule sources and contains the known failure-class identifiers.
- Diagnostic status success after a prior workflow blocker is classified as diagnostic only and does not clear the blocker.
- Failed local transfer reports may be published as evidence, but never as a go reply.

## Transfer Wrapper Branch-Safety Roadmap

The current workflow exposed a direct wrapper branch-safety bug: `transfer push-current` can report success for a push that targets `main` even when the intended feature branch contains the pending work. This is a hard workflow safety defect, not a usability issue.

This hardening line is the first follow-up after PR1054 closeout and before broader fail-closed precondition-chain work.

Required rules:

1. `transfer push-current` must derive the branch to push from the actual current branch at execution time, not from stale rule-ack metadata, default branch state, cached transfer state, or an implicit `main` fallback.
2. If actual current branch, requested branch, upstream branch, and pushed ref differ, the command must fail closed with `chat_reply=f`, report the exact mismatch, and perform no push.
3. `push-current` must not silently set `main` upstream or push `main` when the local current branch is a feature branch.
4. Mutating wrappers must include precondition fields in their JSON result: `current_branch`, `target_branch`, `pushed_branch` where applicable, `expected_branch` where supplied, `repo_head`, `upstream_ref`, `dirty_state`, `workflow_state`, and `blocking_reason`.
5. A wrapper result status must distinguish command execution success from workflow safety; `git push` returning zero is not sufficient for workflow `PASS` when the pushed ref is wrong.
6. `rules acknowledge` metadata must not cause later wrappers to select `main` when the worktree has moved to a feature branch.
7. Commit, push, PR, merge, run-and-log, publish-last-report, and branch-switch wrapper paths should accept an explicit `--expected-branch` or equivalent typed work-order branch contract.
8. The GUI must not expose branch-mutating buttons unless current branch, expected branch, dirty state, and workflow state are consistent.

Acceptance tests:

- On a feature branch, `transfer push-current` pushes that feature branch and never pushes `main`.
- On `main`, `transfer push-current` refuses product-work pushes unless an explicit safe administrative context allows it.
- If current branch and requested/expected branch differ, no push is attempted and the result is `BLOCKED`/`chat_reply=f`.
- If upstream tracking points to a different ref than the current branch, `push-current` fails closed and reports the mismatch.
- Wrapper JSON includes branch and workflow-safety fields sufficient for LLM/GUI consumers to reject stale or wrong-branch continuations.

## Fail-Closed Precondition Chain Roadmap

The current workflow still permits a dangerous interpretation error: a later diagnostic command can return `PASS` after an earlier precondition command returned `FAIL`. That must never be interpreted as authorization to continue.

This hardening line must be inserted immediately after the transfer-wrapper branch-safety slice and before further rule/outbox/gui hardening.

Required rules:

1. A failed precondition is sticky for the current workflow chain until explicitly resolved.
2. `branch-switch` failure blocks all later product actions; `repo-status PASS` after `branch-switch FAIL` is diagnostic only and must not clear the block.
3. Wrong branch, dirty protected state, untracked files that would be overwritten by checkout, missing transfer inbox file, and failed report publication are workflow blockers.
4. `run-and-log` and `publish-last-report` must support or consume expected branch/clean-state metadata and must fail closed when the current repo state does not match the requested work context.
5. `publish-last-report` must not emit `CHAT_REPLY=g` for reports with `returncode != 0`, `final_signal=f`, wrong-branch failures, missing-file failures, branch-switch failures, or unresolved precondition blockers.
6. `repo-status` must distinguish command execution success from workflow safety. A successful status command is not a workflow PASS.
7. Transfer reports must preserve precondition-chain state so the LLM cannot treat a later signal as clearing an earlier blocker.
8. The normal LLM-to-local transfer path must use the canonical inbox file `.agentic/transfer/inbox/next_command.py.txt` so branch switches are not blocked by accumulated untracked throwaway transfer files.

Acceptance tests:

- `branch-switch FAIL` followed by `repo-status PASS` still yields workflow `BLOCKED`.
- wrong-branch `run-and-log` yields `chat_reply=f` and does not create a go-state report.
- `publish-last-report` for a failed report yields `chat_reply=f`, not `g`.
- untracked transfer inbox files that block checkout are detected as a precondition-chain blocker.
- the generated outbox/report state includes both command status and workflow state.

## Rule Semantics Cleanup Roadmap

The current rule system still has transition drift around dialogue signals and planned transfer rules. Before hardening generated outbox context or GUI gates, this must be cleaned in a rule-management slice:

1. Remove `w` from active dialogue rules, compiled context, generated prompts, and tests; historical logs may remain unchanged as evidence.
2. Make `d/f/g` the only active dialogue signal set.
3. Add `.agentic/dialogue_rules.yaml` only with schema, validation, tests, and registry integration.
4. Add rule-mechanism inventory and test-coverage entries for transfer outbox context projection and canonical transfer files.
5. Add preservation anchors when the new dialogue/transfer rule files become protected control state.
6. Add drift tests proving that governance docs, compiled context, dialogue rules, and generated outbox projections do not disagree.

## Sequencing Decision

This focus must be recorded before completing the documentation-management phase so that the remaining registry slices and the later GUI are shaped by it.

Implementation must not continue product work from a dirty or wrong branch. The practical sequence is:

1. close PR1054/B11 with PR/CI/merge evidence and no further local product work;
2. implement the transfer-wrapper branch-safety hardening slice;
3. implement the fail-closed precondition-chain hardening slice;
4. clean active dialogue/transfer rules in a protected rule-management slice;
5. audit and complete documentation-registry coverage for active docs in small reversible slices;
6. finish any remaining B11 transfer-report contract semantics follow-up;
7. add any new documentation artifacts to the documentation-management system and any new durable rules to the rule-management system;
8. continue the handoff/status freshness guard and documentation-registry work;
9. complete the documentation-management foundation enough for artifact and evidence visibility;
10. implement transfer outbox context generation and dialogue rules in small tested slices;
11. then make the GUI expose this reduced-orchestration model;
12. only after that, resume Pattern Advisor expansion.

## External Review Input Handling

External model reviews, advisory audits, or user-provided comparative assessments may be used as prioritization input, but they are not evidence by themselves.

When an external review identifies a repeated workflow risk, the kit should classify it into one of these outcomes:

- already covered by an executable guard or deterministic check;
- covered by a plan but still missing executable enforcement;
- useful only as advisory context;
- rejected because it conflicts with repository evidence.

The preferred response to useful external review input is not to copy ratings or qualitative praise into status documents. The preferred response is to connect the input to a concrete backlog item, guard candidate, GUI-safe action, test, or workflow-kernel capability.

For the current GUI and workflow-kernel line, the useful review signal is: prioritize enforcement and automation over additional chat-only instructions. The GUI should expose existing hardened command paths and make safe state, evidence, PR status, protected-change planning, transfer outbox state, and next-step decisions easier to execute without manual terminal orchestration.

The rule-refresh handshake is the stability core for this direction. `docs/planning/RULE_REFRESH_HANDSHAKE_PLAN.md` governs the staged work to make local-to-LLM and LLM-to-local rule freshness machine-checkable, fail-closed, and visible to the later GUI.

## Non-Goals For The Current Line

- no broad documentation migration in one PR,
- no release or tag work,
- no destructive GUI or remote-GUI actions,
- no expansion of Pattern Advisor before the registry and GUI foundations are ready,
- no new chat-only rules without a repository home and, where appropriate, deterministic checks,
- no new documentation artifacts that bypass documentation-management classification,
- no new durable rule sources that bypass rule-management registration and validation.

## Review Rule

When a future slice adds complexity, reviewers should ask whether it reduces manual orchestration or only adds another surface area. Prefer the smallest change that makes state, evidence, next action, or drift more explicit.

## Pre-GUI Wrapper And Workflow Hardening Roadmap

Status: active
Decision status: accepted

This roadmap records the remaining wrapper, transfer, evidence, output-discipline, and GUI-prerequisite hardening work. GUI expansion must wait until these workflows are available as bounded, tested wrapper commands.

### Remaining Non-Narrensicher Areas

| Restaufgabe | Einschätzung |
|---|---|
| Guarded GUI dispatch für `successor-handoff-prompt` | noch offen |
| Transfer-Message-State-Modell erweitern/validieren | noch offen |
| technische Vermeidung von Inline-, Quote- und Heredoc-Fallen | weiterhin wichtig |
| weitere Reduktion manueller Einzelschritte | offen, aber deutlich weniger kritisch |
| Outbox-Dirty-Handling bei allen Transferkommandos | Hauptfälle erledigt, Rest beobachten |
| Evidence-Abschluss ergonomisch machen | Hauptpfad erledigt via `transfer evidence-finalize-current-transfer`; Evidence-PR-Automation bleibt offen |
| Evidence-Abschluss | funktional und ergonomischer; direkte Main-Push-Vermeidung/Evidence-PR-Pfad bleibt weiter zu härten |
| Copy/Paste-Patches | weiterhin Schwachstelle |

### Missing Or Desired Wrapper Commands

| Fehlendes Kommando | Warum nötig | Ersetzt bisher |
|---|---|---|
| `transfer branch-save-commit BRANCH SHA` | lokalen Commit sicher auf Branch retten | `git branch evidence/... 512c771` |
| `transfer reset-current-to-upstream` | lokalen Branch kontrolliert auf Upstream zurücksetzen | `git reset --hard origin/main` |
| `transfer concise-report` | lange JSON-/Help-Ausgaben auf Kurzsummary reduzieren | manuelle Python-Auswertung von Reports |
| `transfer pr-existing-for-branch` | vorhandenen PR zu Branch finden | erledigt als read-only Diagnosewrapper; kein PR-Erstellen, kein Push, kein Merge |

### Completed Pre-GUI Wrapper Commands

| Erledigtes Kommando | Stand |
|---|---|
| `transfer restore-known-volatile` | erledigt und getestet |
| `transfer sync-main` | erledigt, getestet und mit kurzer Standardausgabe versehen |
| `transfer divergence-status` | erledigt und getestet |
| `transfer command-reference-refresh` | erledigt und getestet |
| `transfer command-reference-check` | erledigt und getestet |
| `transfer evidence-inspect-latest` | erledigt und getestet; kann korrekt FAIL melden, wenn das aktuell gefundene Evidence-Log alt/ambig/rot ist |
| `transfer evidence-finalize-current-transfer` | erledigt und getestet als ergonomische Hülle um `evidence finalize-log` |
| `transfer remote-work-start` concise default output | erledigt und regressionsgetestet |
| `transfer pr-create-complete` | erledigt, getestet und real erfolgreich genutzt; beseitigt den manuellen PR-Nummern- und HEAD-SHA-Kopierschritt |
| `transfer pr-existing-for-branch` | erledigt und getestet als read-only Branch-zu-PR-Diagnosehelper; optional für GUI-Diagnostik |
| `transfer protected-diff-plan` | erledigt, getestet und real genutzt; ersetzt `git diff --output=/tmp/...` plus `./ns protected-change-plan` |
| `transfer conflict-status` | erledigt, getestet und real genutzt; diagnostiziert Merge-/Rebase-Konflikte ohne Auflösung |
| `transfer work-order-patch` | erledigt, getestet und real genutzt; wendet JSON/YAML-Textpatches mit Branch-, Pfad- und Exact-Match-Guards an |
| `transfer rebase-on-upstream` | erledigt, getestet und real genutzt; führt Rebase mit Branch-Guard und `conflict-status`-Integration aus |
| `transfer conflict-resolve-file` | erledigt, getestet und real genutzt; ersetzt genau ein unmerged File aus expliziter Quelle und staged es kontrolliert |
| `transfer delete-merged-work-branch` | erledigt, getestet und real genutzt; löscht gemergte Work-Branches lokal/remote mit PR-Merge-State-Prüfung |
| `transfer evidence-pr-complete` | erledigt und getestet; finalisiert Transfer-Evidence auf Evidence-Branch, prüft sie, pusht und schließt den Evidence-PR-Lifecycle über guarded Wrapper ab |

### Pre-GUI Work Order

#### 1. Wrapper-Lücken schließen

Priority order:

1. Command-/Rule-Registry-Audit for the completed wrapper set
2. Output-discipline residual audit
3. GUI button mapping and gating over stable wrappers
4. `transfer pr-existing-for-branch` — done as optional read-only diagnostic wrapper

Completed in the hardening passes so far: `transfer restore-known-volatile`, `transfer sync-main`, `transfer divergence-status`, `transfer command-reference-refresh`, `transfer command-reference-check`, `transfer evidence-inspect-latest`, `transfer evidence-finalize-current-transfer`, `transfer pr-create-complete`, `transfer protected-diff-plan`, `transfer conflict-status`, `transfer work-order-patch`, `transfer rebase-on-upstream`, `transfer conflict-resolve-file`, `transfer delete-merged-work-branch`, `transfer pr-existing-for-branch`, and `transfer evidence-pr-complete`.

The manual sequence `pr-create -> read PR number -> FULL_SHA=$(git rev-parse HEAD) -> pr-complete <PR>` is no longer the preferred path. Use `transfer pr-create-complete` for normal PR lifecycle completion.

Reason: these steps are still repeatedly replaced by raw shell, raw git, direct Python invocation, or long copy/paste snippets.

#### 2. Transferdatei statt Inline-Patch

This is higher priority than GUI automation.

Target:

- the assistant should not emit long Heredoc or inline Python mutation blocks as the normal path;
- instead, the assistant should create or request a typed work order with fields such as `kind: patch_file`, `paths`, `expected_branch`, `tests`, `protected_change_plan_required`, and `commit_policy`;
- the local runner executes the work order;
- user-visible output is limited to `PASS`, `FAIL`, and the report path.

This reduces quote, terminal, heredoc, escape, copy/paste, and message-stream failure modes.

Next priority: first GUI display/gating phase, while keeping `transfer pr-existing-for-branch` optional as a future read-only diagnostic helper and tracking `./ns` replacement as a separate OS-independence line.


### Pre-GUI Wrapper/Gating Closeout

The originally blocking pre-GUI wrapper list is now closed for the first GUI display/gating phase:

| Item | Status |
|---|---|
|Output-discipline rest audit | done |
|GUI button mapping/gating metadata | done |
|Command-/Rule-Registry audit | done |
|`transfer pr-existing-for-branch` | optional diagnostic wrapper; not required before the first GUI phase |

The GUI may now proceed only as a display and gating layer over existing bounded wrappers. It must not introduce raw Git, raw GitHub, raw shell, or unrestricted remote mutation actions.

`transfer pr-existing-for-branch` is implemented as an optional read-only branch-to-PR lookup helper for later diagnostics. It remains outside the normal PR lifecycle path, which should use `transfer pr-create-complete`.

### Pre-GUI Wrapper Registry Audit

Status: active

Audit finding after the completed wrapper hardening pass:

| Area | Finding |
|---|---|
| Command reference JSON/Markdown | PASS: completed wrappers are present in `docs/reference/agentic-kit-commands.json` and `docs/reference/AGENTIC_KIT_COMMANDS.md`. |
| Wrapper tests | PASS: completed wrappers have direct regression coverage in transfer-focused tests. |
| Roadmap | PASS: completed wrappers are recorded in this roadmap. |
| Governance references | TODO: verify that governance docs point to wrapper-based workflows rather than manual git/GitHub/evidence choreography. |
| Rule mechanism inventory | TODO: verify that the command-reference registry and transfer-wrapper layer are represented as rule/mechanism sources where applicable. |
| GUI catalog and dispatch plan | TODO: map GUI actions only to stable wrappers and keep mutating GUI actions disabled unless branch, dirty-state, rule-ack, PR/evidence, and failure-mode guards are available. |

Completed wrapper set to audit before GUI expansion:

- `transfer remote-work-start`
- `transfer sync-main`
- `transfer pr-create-complete`
- `transfer protected-diff-plan`
- `transfer work-order-patch`
- `transfer rebase-on-upstream`
- `transfer conflict-status`
- `transfer conflict-resolve-file`
- `transfer delete-merged-work-branch`
- `transfer evidence-inspect-latest`
- `transfer evidence-finalize-current-transfer`
- `transfer evidence-pr-complete`
- `transfer command-reference-refresh`
- `transfer command-reference-check`

Next audit action: inspect and, if needed, minimally update governance docs, `.agentic/rule_mechanism_inventory.yaml`, and GUI planning/catalog references so the GUI expansion starts from the completed wrapper set rather than raw shell, raw git, raw GitHub, or manual evidence commands.

### Pre-GUI Output Discipline Audit

Audit finding after the wrapper registry pass:

| Output group | Finding |
| --- | --- |
| GUI-ready concise transfer defaults | `transfer sync-main`, `transfer remote-work-start`, `transfer pr-complete`, `transfer pr-create-complete`, `transfer protected-diff-plan`, `transfer conflict-status`, `transfer work-order-patch`, `transfer rebase-on-upstream`, `transfer conflict-resolve-file`, `transfer delete-merged-work-branch`, and `transfer evidence-pr-complete` use bounded summaries or command-specific short reports by default and keep JSON behind `--json` where appropriate. |
| Evidence/transfer publication special cases | `transfer run-and-log`, `transfer run-sequence-and-log`, and `transfer publish-last-report` intentionally keep their compact transfer-report semantics. They must not be converted blindly because `CHAT_REPLY=d` and `CHAT_REPLY=g` have different evidence/publication meanings. |
| Machine-state and broad diagnostic commands | `transfer state`, `transfer run-local`, `transfer closeout`, broad `status`/`inspect`/`apply` style paths, and legacy diagnostic helpers are not default GUI mutation targets. They may remain JSON-first or verbose until a GUI-specific read-only or parameterized contract is added. |
| Older JSON-plus-final-signal commands | `restore-known-volatile`, `divergence-status`, `command-reference-refresh`, `command-reference-check`, `evidence-inspect-latest`, `evidence-finalize-current-transfer`, `prepare-successor-handoff`, and related administrative helpers still emit full JSON by default in some modes. This is acceptable before GUI as long as GUI button mapping does not expose them as broad write actions without a bounded adapter. |

Pre-GUI decision: no broad output rewrite before GUI. The GUI must initially map only to the bounded concise wrapper set, keep broad JSON-first commands disabled or read-only, and add command-specific adapters only when a button needs them.

`transfer pr-existing-for-branch` is now available as an optional read-only diagnostic helper. Normal PR lifecycle completion remains covered by `transfer pr-create-complete`.

#### 3. Evidence ergonomisch machen

`evidence finalize-log` works. The regular transfer path is now shortened by `transfer evidence-finalize-current-transfer`.

Completed:

- `transfer evidence-finalize-current-transfer --slice ... --pr ...`;
- default selection of `docs/reports/transfer_runs/latest-transfer-report.log`;
- automatic remote log path generation;
- strict wrapper around `evidence finalize-log`.

Completed additionally:

- `transfer evidence-pr-complete` provides the bounded PR-based evidence closeout path;
- direct `main` evidence commits are no longer the preferred regular workflow.

Still needed:

- audit that all evidence-facing docs, GUI plans, and rule/governance references point to the wrapper path rather than the old manual choreography.

#### 3b. Post-release DOI-Metadaten-Closeout kapseln

Completed: `agentic-kit post-release-doi-closeout --version <version>` now provides a guarded dry-run for verified post-release DOI metadata closeout. `--write` updates release DOI metadata only after `post-release-check` verifies the GitHub Release, Zenodo concept DOI, and Zenodo version DOI.

This is a top-level release-governance command, not a transfer wrapper. It reduces the former manual README/CHANGELOG/CITATION/verified-release-archive editing sequence after release publication.

#### 3c. Post-release DOI-Closeout weiter härten

Next planned safety slice: `Harden post-release DOI closeout consistency`.

Scope for that slice:

1. Add an internal expected-path guard to `agentic-kit post-release-doi-closeout`.
   The command must fail closed if the write path would touch anything outside the intended release metadata files:
   `README.md`, `CHANGELOG.md`, `CITATION.cff`, `docs/STATUS.md`, `docs/handoff/CURRENT_HANDOFF.md`, and `docs/releases/VERIFIED_RELEASES.md`.

2. Add an idempotency regression test.
   After a successful `--write`, a second dry run for the same version must report no further changed paths.

3. Add current-release DOI consistency validation.
   The command should validate that the same `(version, concept DOI, version DOI)` tuple is represented consistently across the release metadata files it manages. Historical DOI notes may remain, but they must not be mistaken for current release state.

4. Add a historical-anchor regression test.
   Fixtures should include older v0.4.4/v0.4.5 DOI lines and assert that closeout for a newer version does not rewrite historical release notes.

Explicitly out of scope for this slice:

- GitHub Release asset checksum comparison against Zenodo files.
- Converting the verified release archive to a generated YAML/JSON-backed projection.
- A general CLI-command-to-rule-registry gate for all future commands.

Rationale: this patch targets the real failure modes seen while implementing `post-release-doi-closeout`: over-broad Markdown replacement, duplicate/malformed DOI archive entries, missing idempotency proof, and consistency checks that currently rely too much on follow-up docs-audit/protected-diff inspection.

#### 4. Command-Reference in Regelverwaltung prüfen

The command reference registry now has a governance contract and a staleness test. The next admin slice should verify or add:

- `docs/governance/COMMAND_REFERENCE_REGISTRY_CONTRACT.md` in the documentation/governance inventory;
- the command reference registry as a rule or mechanism in `.agentic/rule_mechanism_inventory.yaml` or the current successor registry;
- CI coverage proving that command-reference drift is checked whenever CLI commands change.

#### 5. PR-Lifecycle weiter reduzieren

Completed: `transfer pr-create-complete` now creates or reuses a PR, resolves the current HEAD SHA, and runs the complete PR lifecycle without manual PR-number copying.

Completed: `transfer pr-existing-for-branch` is available for read-only branch-to-PR diagnostics, but normal user-facing PR completion should still go through `transfer pr-create-complete`.

#### 5. Output-Disziplin erzwingen

Desired behavior:

- concise output is now the default for `transfer sync-main` and `transfer remote-work-start`;
- full detail payloads remain available through `--json`;
- long reports belong in files, not chat;
- chat output should be limited to status, PR number, HEAD, failed step, report path, and next action.

Still needed: apply the same output discipline to remaining transfer-facing commands that still emit large JSON or embedded stdout by default.

#### 6. Erst danach GUI

The GUI should expose stable wrappers, not raw git, raw GitHub, or unbounded shell blocks.

| GUI-Aktion | Benötigter stabiler Wrapper |
|---|---|
| Neuer Arbeitsbranch | `transfer remote-work-start` |
| Main synchronisieren | `transfer sync-main` |
| PR erstellen und abschließen | `transfer pr-create-complete` |
| PR nur abschließen | `transfer pr-complete` |
| Evidence abschließen | `transfer evidence-finalize-current-transfer` |
| Handoff erzeugen | `transfer prepare-successor-handoff --render-prompt` |
| Command-Reference aktualisieren | `transfer command-reference-refresh` |
| Volatile Dateien bereinigen | `transfer restore-known-volatile` |
| Status anzeigen | `transfer normalize-session --repair-known-volatile` |
| Fehlerdiagnose | `transfer pr-status`, `transfer pr-existing-for-branch`, `transfer divergence-status`, `transfer evidence-inspect-latest` |

Acceptance condition before GUI expansion: every GUI button that mutates repository state must map to a bounded wrapper with branch, dirty-state, rule-ack, evidence, and failure-mode guards.


### OS-Independence Line: Replace `./ns` Core Dependencies With `agentic-kit`

Goal: make the project workflow operating-system independent by ensuring that `./ns` remains only a human convenience adapter or explicit legacy compatibility route, not a core dependency of `agentic-kit` Python code, normal tests, governance gates, or GUI execution.

Guiding decision:

- `./ns` may remain as a local shortcut for humans.
- `agentic-kit` product code must not call `./ns` as its normal implementation path.
- normal product, wrapper, workflow, and GUI tests should call `agentic-kit` commands or Python core APIs directly.
- only an explicit legacy compatibility test may call `./ns`.
- documentation must not present `./ns` as the canonical cross-platform route.

Questions to answer in the audit slice:

1. How many `./ns` command references remain?
B. Which references are in product code, tests, docs, governance, scripts, and `.agentic` control files?
3. Are any `./ns` routes currently called from `agentic-kit` commands?
4. Which test cases still rely on `./ns` as the main workflow guarantee?
5. Which references are historical/legacy and which are normative?
6. Which replacements are small, medium, or risky?

Initial audit command uses a small future wrapper or bounded grep-style audit, not a heredoc. The first implementation slice should replace this manual audit with an `agentic-kit` command so the output is portable and testable.

Classification:

| Category | Treatment |
|---|---|
| `src/...` product code calls `./ns` | replace with Python core API or `agentic-kit` command |
| tests use `./ns` for product/workflow guarantees | replace with `agentic-kit` or direct Python core tests |
| explicit legacy `./ns` compatibility tests | may remain, narrowly scoped |
| docs say `./ns` is required/canonical | update to `agentic-kit`; mark `./ns` as legacy/convenience |
| docs mention `./ns` historically | keep only if clearly marked historical or local shortcut |
| `./ns` adapter file itself | may remain as an adapter, but must not be the only route |

Implementation slices:

1. Audit and guard plan: count all `./ns` references, classify them, and record allowed exceptions.
2. Protected-change-plan Python route: provide a canonical `agentic-kit transfer protected-change-plan --diff-file ...` or equivalent Python-core-backed route for explicit diff-file validation.
3. Detach `transfer protected-diff-plan` from `./ns`: call the protected-change planner core or the new `agentic-kit` route directly.
4. Tests and docs migration: replace normative `./ns` calls in tests, bootloader text, governance, and handoff docs with `agentic-kit` routes; retain at most one legacy adapter test.
5. Regression guard: add a test that blocks `./ns` subprocess calls in `src/`, with only explicit legacy-test exceptions.

Estimated effort:

| Area | Effort |
|---|---|
|Audit all `./ns` occurrences | small |
| Add explicit protected-change-plan `agentic-kit` route | small to medium |
|Detach product code from `./ns` | small |
| Update tests | medium |
|Update docs/governance/handoff references | medium |
|Add CI guard against new `./ns` product-code use | small to medium |

This is a separate OS-independence line and should not be treated as a blocker for the next GUI display/gating slice unless the GUI would otherwise call `./ns` directly.

## Operational documentation projection state after PR #1249

Current operational documentation projection state is `dfb7c2ba` (`Introduce operational handoff projection source (#1249)`). PR #1249 introduced `.agentic/operational_handoff_state.yaml` as the first machine-readable operational handoff state source and projects the current operational bootstrap block from that source. Continue next with Slice 2: generated-block markers and targeted block updates while preserving curated documentation.

## Operational documentation refresh state

Recent admin-refresh history is compacted here to preserve documentation headroom. PR #1250, #1253, #1255, #1257, #1260, #1262, #1264, and #1266 moved operational handoff refresh toward generated, protected-plan-checked, non-accumulative updates. Current policy: use operational handoff refresh, preserve historical protected-state entries, update only current refresh metadata and successor pointers, run protected diff plan before commit, and continue from fresh main after merge.## Operational documentation refresh state after PR #1303

Current administrative handoff refresh state is `794ceff0` (`Fix operational handoff refresh newlines (#1303)`). Continue next only after this post-PR1303 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1307

Current administrative handoff refresh state is `e88a5591` (`Harden successor package freshness gates (#1307)`). Continue next only after this post-PR1307 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1311

Current administrative handoff refresh state is `afc21ade` (`Project bootstrap gate into successor package (#1311)`). Continue next only after this post-PR1311 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1317

Current administrative handoff refresh state is `23c913f9` (`Refresh successor package after PR1316 (#1317)`). Continue next only after this post-PR1317 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1324

Current administrative handoff refresh state is `75d7a3d3` (`Refresh successor package during admin handoff refresh (#1324)`). Continue next only after this post-PR1324 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1330

Current administrative handoff refresh state is `a7a0b6a2` (`Audit ns to agentic-kit migration before GUI (#1330)`). Continue next only after this post-PR1330 refresh is committed and merged; the next substantive slice must be created from fresh main.

## NS-to-agentic-kit migration before GUI

Status: required before GUI implementation.

Audit anchor:
- `docs/reports/ns-migration/ns_to_agentic_kit_audit.md`
- `docs/reports/ns-migration/ns_to_agentic_kit_inventory.json`
- `docs/reports/ns-migration/ns_to_agentic_kit_replacement_table.md`

Policy:
- Do not start GUI implementation until `./ns` usage is either replaced by `agentic-kit` commands or explicitly retained only as a thin compatibility/deprecation shim.
- Do not remove `./ns` blindly. First map each remaining workflow to a tested `agentic-kit` command or to a documented deprecation decision.
- Protected/governance/status/handoff/YAML/generated-reference/planning files remain protected; update them minimally and with `protected-diff-plan`.

Migration slices:
1. Classify all `./ns` references from the audit as one of: active workflow, historical note, compatibility shim, or obsolete planning note.
2. Build a replacement table: `./ns` workflow -> existing `agentic-kit` command -> missing wrapper/test if any.
3. Patch docs to prefer `agentic-kit` commands for active workflows; keep legacy notes explicitly labeled as legacy.
4. Add or extend tests for every newly introduced `agentic-kit` replacement wrapper.
5. Only after slices 1-4 pass, start GUI Phase 1 as a display/gating layer over bounded `agentic-kit` wrappers.

Acceptance gates:
- `agentic-kit transfer command-reference-check` PASS.
- `agentic-kit transfer repo-status` PASS.
- `agentic-kit docs-audit` PASS.
- `agentic-kit transfer protected-diff-plan` PASS for every migration slice.
- No active workflow instruction points users primarily to `./ns` when a tested `agentic-kit` command exists.## Operational documentation refresh state after PR #1334

Current administrative handoff refresh state is `c6ab40da` (`Classify ns migration docs before GUI (#1334)`). Continue next only after this post-PR1334 refresh is committed and merged; the next substantive slice must be created from fresh main.## Operational documentation refresh state after PR #1338

Current administrative handoff refresh state is `979825da` (`Remove ns dev go up shortcuts (#1338)`). Continue next only after this post-PR1338 refresh is committed and merged; the next substantive slice must be created from fresh main.
## Planning-document authority closeout before v0.4.10

Status: ACTIVE AUTHORITY.

Slice 16 and Slice 17 changed the repository from a collection of individual
safety tools into a gate-backed workflow:

- `standard-gates-audit-suite` is the standard aggregation point for the new
  audit layer.
- `doctor` and `gui-readiness-gate` must expose the standard audit layer.
- `command-taxonomy-check` keeps the growing CLI classifiable for humans,
  successor chats, and the future GUI gatekeeper.
- `patch-scope-preflight` is the diagnostic preflight for patch size,
  protected-path exposure, and review risk. It is intentionally diagnostic at
  this stage so feature branches do not self-block while still surfacing risk.

Planning documents are now interpreted through this authority order:

1. Current status and handoff files define the current state.
2. This file and release-command-authority planning define active workflow
   direction.
3. Dedicated GUI planning files define GUI design only after the readiness
   gates pass.
4. Older review, migration, and historical planning documents remain preserved
   evidence. They do not override current gates, command taxonomy, release
   authority, or handoff status.

Before v0.4.10, avoid broad planning-document rewrites. Prefer minimal
additive authority notes, then verify with:

- `agentic-kit audit-planning-docs-consolidation`
- `agentic-kit audit-doc-currency`
- `agentic-kit docs-audit`
- `agentic-kit standard-gates-audit-suite`
## Operational documentation refresh state after PR #1496

Current administrative handoff refresh state is `4d323e52` (`Add Markdown report retention policy (#1496)`). Continue next only after this post-PR1496 refresh is committed and merged; the next substantive slice must be created from fresh main.
