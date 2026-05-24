## Handoff Freshness Guard

WARNING: this successor handoff prompt may be stale.
Refresh `docs/STATUS.md`, `.agentic/handoff_state.yaml`, `docs/handoff/CURRENT_HANDOFF.md`, and the successor prompt before treating this prompt as authoritative.

- latest successor handoff prompt is missing: docs/reports/terminal/v041-successor-chat-handoff-after-pr712.md

# Übergabeprompt

## 1. Arbeitsumgebung

Local path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Sicherer Stand

Branch: `main`
Commit: `7d092cb`
Subject: Add workflow guard diagnostics (#714)
Semantics: `current_main_head`
Working tree expected clean: `True`

## 2a. Administrative Evidence State

Administrative Evidence Commits nach dem fachlichen Safe-State sind erlaubt, wenn sie nur Logs, Handoff, Summary oder Evidence aktualisieren. Sie ändern den fachlichen Safe-State nicht.

Current HEAD at generation time: `ce665c3`
HEAD subject: Harden remote route and YAML mutation workflow (#712)
Allowed after safe state: `True`
Reason: post-PR712 state refresh target; future pure administrative refresh merge may point at this prompt without creating a loop

## 3. Release- und Produktstand

Current version: `0.4.1`
Previous version: `0.4.0`
Tag: `v0.4.1`
Zenodo concept DOI: `10.5281/zenodo.20101359`
Zenodo version DOI: `10.5281/zenodo.20357657`
Post-release check: `PASS`

## 4. Pflichtquellen vor jeder Mutation

Lies diese Quellen zuerst. Wenn eine Quelle fehlt, widersprüchlich ist oder nicht gelesen werden kann, melde Drift und mutiere nicht außer zur Drift-Reparatur.

- .agentic/compiled_agent_context.yaml
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/TEST_GATES.md
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- relevant source files and tests for the requested slice

## 5. Kommunikations- und Summary-Regeln

User-Kürzel sind Kommunikationssignale, keine Evidence:

- d/D: local block appears finished; verify evidence before treating it as success
- f/F: failure reported; inspect or upload evidence before asking for pasted output
- w/W: continue within the current governance and evidence rules
- paste-output: manual paste only when repo-backed or local evidence is unavailable or unusable
- stop: no further mutation or terminal instructions

Final-Summary-Vokabular:

- WORK RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND
- EVIDENCE RESULT: PASS|FAIL|PARTIAL|CHAT_ONLY|NOT_REQUIRED
- OVERALL RESULT: PASS|FAIL|PENDING|HARD-FAIL|NO-COMMAND
- REMOTE_EVIDENCE: PASS|FAIL|PARTIAL|NOT_REQUIRED
- NEXT_CHAT_REPLY: p|f|paste-output|continue|stop

## 6. Aktive Regeln aus handoff_state

- `remote-first-no-guess`: Do not guess repository state, command syntax, file locations, release phase, GitHub JSON fields, or available evidence. Inspect the remote repository and authoritative command help or repo files first, then act on the verified result.
- `deterministic-quality-before-speed`: Prefer technically robust, testable, repeatable solutions over fast workarounds.
- `no-copy-terminal-evidence`: Routine PASS handoffs and normal FAIL handoffs must be backed by repo evidence; use d for log-backed PASS and f for log-backed FAIL. Manual terminal paste is only for hard failure, broken logging, blocked or aborted runs, unavailable pushed evidence, or explicit user request.
- `planning-state-freshness`: Current planning files must be curated and mutually consistent; stale released-version claims or obsolete next-step fragments are guard failures.
- `shell-to-python-portability`: Prefer portable Python-backed helpers and argument-vector execution over fragile shell quoting, heredocs, multiline python -c snippets, or nested quote-based code generation.
- `rules-must-be-test-backed`: Workflow rules are not complete when they only exist in chat, prose, or handoff memory. Every durable rule must have a stable repository home, a rule id, documentation, and at least one deterministic test that fails when the rule disappears or is weakened.
- `no-unconditional-pass`: Do not print PASS after a failed required command.
- `curate-chat-end-lessons`: Chat-end lessons must be curated into YAML and generated prompts without redundant, contradictory, or obsolete rules.
- `last-substantive-safe-state`: safe_state records the last substantive work state; administrative handoff refresh PRs are tracked separately to avoid refresh loops.
- `quality-first-no-shortcuts`: Always choose the technically best deterministic solution for recurring workflow problems; do not use shortcut patches that merely get the current block past the gate.
- `patch-artifact-preflight-before-application`: Complex patches must be treated as patch artifacts and checked before application: syntax, YAML structure, generated Python compileability, documentation coverage terms, and final-summary validity.
- `generated-code-syntax-first`: Generated or newly added Python files must pass py_compile before full gates or commit attempts; nested string-generation mistakes are product defects, not acceptable manual errors.
- `coverage-yaml-terms-must-be-strings`: Documentation coverage terms must be strings; terms containing colons must be quoted so YAML cannot reinterpret them as mappings.
- `final-summary-self-validation`: Terminal workflows must validate their mandatory final SUMMARY block before asking the user to reply p.
- `yaml-structured-mutation-only`: YAML governance files must be changed through parse-modify-dump or an equivalent structured mutation path, then parsed again before gates. Text injection into YAML is forbidden for complex values.
- `quote-guard-no-nested-generation`: Avoid nested quote-based code generation and nested shell/Python quote layers; use line-list generation, existing patch tools, file-based patch helpers, or simple printf line generation.
- `canonical-handoff-prompt-command`: Use agentic-kit handoff prompt or python -m agentic_project_kit.cli handoff prompt as the canonical generator. Do not use ./ns handoff prompt unless ./ns explicitly routes that command correctly.
- `handoff-state-must-not-stale`: A chat switch handoff prompt is invalid if .agentic/handoff_state.yaml points to an obsolete version, commit, or next task. Refresh handoff_state first, then regenerate the prompt.
- `status-boundary-changelog-history`: docs/STATUS.md is the compact live dashboard; CHANGELOG.md is the long-term project history. Do not solve status-headroom failures by turning STATUS.md back into a historical log.
- `administrative-evidence-state-boundary`: Separate substantive safe_state from administrative_evidence_state. Pure log, summary, handoff, or evidence commits after safe_state do not invalidate the successor-chat handoff; substantive code, doc, or product changes after safe_state do.
- `successor-handoff-freshness-guard`: Before a successor handoff prompt is treated as authoritative, check docs/STATUS.md, .agentic/handoff_state.yaml, docs/handoff/CURRENT_HANDOFF.md, and the latest successor prompt against current main; stale prompts must warn or trigger closeout refresh.
- `administrative-refresh-loop-guard`: A pure administrative handoff refresh merge must not create an endless successor-prompt refresh loop; the freshness guard may accept an administrative refresh commit when the prompt names the last substantive safe/admin state.
- `github-connector-direct-path-first`: For remote GitHub work with a known repository, ref, path, PR, or commit, use the GitHub connector direct fetch/update/PR APIs first instead of exploratory search or guessed URL variants.
- `control-file-preservation`: Protected control files must preserve active rules and required anchors. Information preservation outranks compactness; hard length-limit trimming is forbidden. Split, reference, or generate large protected files instead of deleting active rules.
- `structured-summary-must-be-enforced`: Every relevant local or remote work block must end with the canonical structured SUMMARY block defined by FINAL_SUMMARY_CONTRACT.md. Missing, malformed, contradictory, or legacy summaries are workflow drift; product or documentation-management work must stop until the summary output is repaired and validated.

## 7. Offene Punkte

- Keine offenen PRs im handoff_state.

## 8. Abgeschlossen seit letzter Übergabe

- PR #692 introduced the first documentation registry schema and guard slice.
- PR #695 added the first read-only registry consumer and operational/artifact classifications.
- PR #696 added the read-only registry JSON report path.
- PR #697 surfaced registry summary data in docs-audit.
- PR #698 surfaced registry summary data in doc-mesh-audit.
- PR #699 surfaced registry summary data in doc-lifecycle-audit.
- PR #700 surfaced registry summary data in handoff check/show.
- PR #701 surfaced registry summary data in release-check and post-release-check.
- PR #702 refreshed status, handoff state, current handoff, successor prompt, and evidence after PR701.
- PR #706 added the warning-based successor handoff prompt freshness guard.
- PR #707 recorded the post-guard successor handoff prompt and closeout evidence.
- PR #708 refreshed handoff state after PR707.
- PR #709 exposed the machine-readable communication artifact policy through docs-registry and its JSON report without changing cleanup behavior.
- PR #710 refreshed handoff state after PR709.
- PR #712 hardened remote access, governance YAML mutation, and protected control-file preservation.
- PR #714 added workflow guard diagnostics, patched preflight integration, protected control-file preservation coverage, and removed hard word limits from protected control files.

## 9. Letzte bekannte Fehler- und Driftmuster

- `guessing-before-inspection`: Before choosing commands, paths, JSON fields, release checks, or DOI sources, inspect the remote repository and command help. Treat memory and chat summaries as hypotheses until verified.
- `stale-planning-documents`: State freshness checks must compare STATUS, CURRENT_HANDOFF, handoff_state.yaml, release metadata, and strategy baselines before GUI or release-automation work starts.
- `standard-error-guards`: Recurring workflow failures must become guards, tests, and documented contracts.
- `interpreter-discovery-before-python`: Terminal/workflow blocks must discover a usable interpreter before set -e-sensitive work and prefer .venv/bin/python, then .venv/bin/python3, then python3, and only then python. Do not combine naked python with set -e.
- `global-cli-or-venv-assumption`: Verify .venv, python3, ruff, pytest, and agentic-kit before using command names; missing global tooling is environment state, not product failure.
- `interactive-terminal-exit`: Chat-pasted terminal blocks must not call exit, logout, kill, or replace the shell with exec; report markers and return to the prompt.
- `nested-triple-quote-code-generator`: Do not generate source files through nested shell/Python quote layers or nested triple-quoted string literals inside another generated Python script.
- `yaml-colon-term-reinterpreted-as-mapping`: Quote colon-containing YAML values and keep coverage-term string guards active so YAML cannot reinterpret prose as mappings.
- `nested-quote-based-code-generation`: Use file-based patch helpers or simple printf line generation; avoid nested quote-based code generation.
- `repeated-yaml-governance-file-corruption`: Patch scripts must parse YAML before and after mutation, use safe_dump or an equivalent structured writer, and run a YAML integrity test before handoff, governance, or dev gates.
- `stale-successor-handoff-prompt-after-main-merge`: Run the successor handoff freshness guard and refresh STATUS, handoff_state, CURRENT_HANDOFF, and the successor prompt before treating handoff prose as authoritative.
- `handoff-moving-head-loop`: Do not chase every final log commit with a new safe_state commit. Store administrative evidence commits separately and allow pure administrative refresh commits to point at the last substantive prompt marker.
- `final-pass-after-inner-fail`: Final summaries must distinguish work result from evidence result. A later successful evidence push must not relabel failed work as PASS.
- `github-remote-route-guessing`: Use GitHub connector direct-path-first calls for known repo paths, refs, PRs, and commits to avoid search-route drift and token waste.
- `lossy-control-file-shortening`: Protected control files must not be shortened by deleting active rules. Use explicit successor migrations, generated projections, or split/reference patterns.
- `structured-summary-drift`: Before accepting a work block as successful, verify that the final output contains exactly the canonical structured SUMMARY fields and that WORK RESULT, EVIDENCE RESULT, OVERALL RESULT, REMOTE_EVIDENCE, terminal_log, command_report, NEXT_CHAT_REPLY, and RESULT marker are mutually consistent.

## 10. Verbotene Muster

- mutating before reading the mandatory successor-chat sources
- treating d as proof of success
- asking for pasted output while usable local or remote evidence exists
- using shell-only snippets as canonical cross-platform execution
- using POSIX tools as correctness dependencies for portable workflows
- printing REMOTE_EVIDENCE: PENDING in a final summary
- adding handwritten legacy summary footers after the summary renderer
- continuing product work after unresolved contract or evidence drift

## 11. Nächste erlaubte Aufgaben

- 1. `verify-pr712-state-refresh` — Verify the post-PR712 handoff freshness guard is quiet.
- 2. `continue-documentation-registry-rebuild` — Add the next small documentation-registry slice, preferably toward machine-readable source/projection planning.

## 12. Gesperrte Aufgaben

- Remote/destructive GUI actions
- Large GUI architecture expansion before successor-chat bootstrap

## 13. Erste Arbeitsanweisung

Verify the post-PR712 successor handoff prompt and freshness guard, then continue the documentation-management rebuild with one small additive registry slice. Do not start a broad migration, release, tag, or destructive GUI action.

## 14. Arbeitsmodus für den Nachfolge-Chat

1. Lies zuerst alle Pflichtquellen aus Abschnitt 4.
2. Rekonstruiere den aktuellen Stand aus Repo, PR/CI, Logs und Summary, nicht aus Chat-Erinnerung.
3. Prüfe Drift zwischen Regeln, Tests, Summary-Renderer, Status und Handoff.
4. Bei Drift: warnen, keine Produktmutation, Handoff-Prompt oder Drift-Fix anbieten.
5. Arbeite nur in kleinen, testbaren Slices mit ehrlicher Evidence.

