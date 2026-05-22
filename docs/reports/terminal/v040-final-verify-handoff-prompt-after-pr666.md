# Übergabeprompt

## 1. Arbeitsumgebung

Local path: `/Users/hof/Dropbox/Privat/GitHub/agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Sicherer Stand

Branch: `main`
Commit: `adc65ac`
Subject: Close out GUI MVP three read-only actions (#656)
Semantics: `last_substantive_work_state`
Working tree expected clean: `True`

## 2a. Administrative Evidence State

Administrative Evidence Commits nach dem fachlichen Safe-State sind erlaubt, wenn sie nur Logs, Handoff, Summary oder Evidence aktualisieren. Sie ändern den fachlichen Safe-State nicht.

Current HEAD at generation time: `8198ebe`
HEAD subject: Refresh handoff state after PR665 (#666)
Allowed after safe state: `True`
Reason: post-PR666 handoff_state refresh and administrative evidence commits after GUI MVP closeout

## 3. Release- und Produktstand

Current version: `0.3.37`
Previous version: `0.3.36`
Tag: `v0.3.37`
Zenodo concept DOI: `10.5281/zenodo.20101359`
Zenodo version DOI: `10.5281/zenodo.20329450`
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
- `quote-guard-no-nested-generation`: Avoid nested quote-based code generation; use file-based patch helpers or simple printf line generation.
- `canonical-handoff-prompt-command`: Use agentic-kit handoff prompt or python -m agentic_project_kit.cli handoff prompt as the canonical generator. Do not use ./ns handoff prompt unless ./ns explicitly routes that command correctly.
- `handoff-state-must-not-stale`: A chat switch handoff prompt is invalid if .agentic/handoff_state.yaml points to an obsolete version, commit, or next task. Refresh handoff_state first, then regenerate the prompt.
- `status-boundary-changelog-history`: docs/STATUS.md is the compact live dashboard; CHANGELOG.md is the long-term project history. Do not solve status-headroom failures by turning STATUS.md back into a historical log.
- `administrative-evidence-state-boundary`: Separate substantive safe_state from administrative_evidence_state. Pure log, summary, handoff, or evidence commits after safe_state do not invalidate the successor-chat handoff; substantive code, doc, or product changes after safe_state do.

## 7. Offene Punkte

- Keine offenen PRs im handoff_state.

## 8. Abgeschlossen seit letzter Übergabe

- PR #647 enabled the Doctor button through the bounded read-only GUI contract.
- PR #649 added LLM communication and portable execution contracts.
- PR #650 closed out PR649 communication contracts in STATUS and CURRENT_HANDOFF.
- PR #651 hardened documentation audit headroom and log finalization.
- PR #652 hardened remote log communication verification rules.
- PR #653 hardened GUI visual evidence workflow rules.
- PR #654 added the shared read-only GUI runner abstraction.
- PR #655 enabled check-docs as the third read-only GUI action.
- PR #656 closed out the GUI MVP with cockpit-readiness, doctor, and check-docs visually verified as bounded read-only GUI actions.
- PR #657 modeled administrative evidence state in generated handoff prompts.
- PR #659 repaired STATUS.md current-state drift after PR657 without changing CURRENT_HANDOFF.md or handoff_state.yaml.
- PR #660 refreshed handoff_state.yaml after PR659 while preserving existing rule and failure-pattern anchors.
- PR #661 added CURRENT_HANDOFF_OVERLAY_AFTER_PR660.md without changing CURRENT_HANDOFF.md.
- PR #663 repaired README DOI drift and changed doc_mesh README version extraction to use the explicit current verified release marker, with regression coverage for historical version anchors.
- PR #665 merged the PR661 overlay into CURRENT_HANDOFF.md non-destructively, preserving existing compatibility anchors.
- Historical PRs #562, #564, and #568 were closed without merge as superseded evidence branches.
- STATUS.md remains the compact live dashboard while CHANGELOG.md remains the long-term project history.
- PR #666 refreshed handoff_state.yaml after PR665 and set final verification plus canonical handoff prompt regeneration as the next allowed tasks.

## 9. Letzte bekannte Fehler- und Driftmuster

- `guessing-before-inspection`: Before choosing commands, paths, JSON fields, release checks, or DOI sources, inspect the remote repository and command help. Treat memory and chat summaries as hypotheses until verified.
- `stale-planning-documents`: State freshness checks must compare STATUS, CURRENT_HANDOFF, handoff_state.yaml, release metadata, and strategy baselines before GUI or release-automation work starts.
- `standard-error-guards`: Recurring workflow failures must become guards, tests, and documented contracts.
- `interpreter-discovery-before-python`: Terminal/workflow blocks must discover a usable interpreter first and prefer .venv/bin/python, then .venv/bin/python3, then python3, and only then python. Do not combine naked python with set -e because a missing interpreter can close the interactive terminal before diagnostics are preserved.
- `global-cli-or-venv-assumption`: At chat or workflow start, verify .venv, python3, ruff, pytest, and agentic-kit before using command names. Treat missing global agentic-kit or missing .venv as bootstrap/environment state, not as product failure.
- `interactive-terminal-exit`: Chat-pasted terminal blocks must not call exit, logout, kill, or replace the shell with exec. Report PASS/FAIL with markers and return to the prompt. Exit codes belong inside saved scripts, not interactive paste blocks.
- `repo-log-written-while-committing`: Tee long runs into a temporary log outside docs/reports/terminal, finalize with ./ns terminal-finalize, then stage, commit, and push. Never commit a repo terminal log while the current process is still writing to it.
- `unconditional-pass-after-failure`: Use explicit status handling and require log-backed PASS. Avoid shell-specific status variables such as PIPESTATUS in zsh-pasted blocks unless the shell is explicitly controlled.
- `nested-triple-quote-code-generator`: Do not generate source files through nested shell/Python quote layers or nested triple-quoted string literals inside another generated Python script. Prefer line-list generation, existing patch tools, or checked patch artifacts plus py_compile before application.
- `yaml-colon-term-reinterpreted-as-mapping`: Quote every documentation coverage term containing a colon, and keep the coverage-term string guard in the test suite.
- `final-pass-after-inner-fail`: Final summaries must distinguish work result from evidence result. A later successful evidence push must not relabel failed work as PASS.
- `repeated-yaml-governance-file-corruption`: Patch scripts must parse YAML before and after mutation, use safe_dump or an equivalent structured writer, and run a YAML integrity test before handoff, governance, or dev gates.
- `nested-quote-based-code-generation`: Use file-based patch helpers or simple printf line generation; avoid nested quote-based code generation.
- `stale-handoff-state-after-main-merge`: After merge verification, inspect and refresh .agentic/handoff_state.yaml before generating a successor-chat prompt.
- `wrong-handoff-command-route`: Do not assume ./ns handoff prompt works; verify command routing or call the canonical agentic-kit CLI directly.
- `invalid-gh-pr-json-field`: Inspect gh pr view --json field names before using them; use mergedAt rather than a non-existent merged field.
- `handoff-moving-head-loop`: Do not chase every final log commit with a new safe_state commit. Store administrative evidence commits separately.
- `readme-historical-version-anchor-vs-current-extractor`: README version extraction must use the explicit Current verified release marker and retain regression coverage for historical Version anchors.

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

- 1. `final-main-verify-after-pr665` — Verify main after PR665 and run final readiness gates.
- 2. `regenerate-canonical-handoff-prompt` — Regenerate the canonical handoff prompt after final verification.
- 3. `v040-release-readiness-check` — Check v0.4.0 readiness only after final main verification and canonical handoff prompt regeneration.

## 12. Gesperrte Aufgaben

- Release work
- Remote/destructive GUI actions
- Large GUI architecture expansion before successor-chat bootstrap

## 13. Erste Arbeitsanweisung

Verify main at or after PR #666, run final readiness gates, regenerate the canonical handoff prompt, and only then assess v0.4.0 release readiness.

## 14. Arbeitsmodus für den Nachfolge-Chat

1. Lies zuerst alle Pflichtquellen aus Abschnitt 4.
2. Rekonstruiere den aktuellen Stand aus Repo, PR/CI, Logs und Summary, nicht aus Chat-Erinnerung.
3. Prüfe Drift zwischen Regeln, Tests, Summary-Renderer, Status und Handoff.
4. Bei Drift: warnen, keine Produktmutation, Handoff-Prompt oder Drift-Fix anbieten.
5. Arbeite nur in kleinen, testbaren Slices mit ehrlicher Evidence.

