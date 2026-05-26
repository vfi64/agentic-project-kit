## Handoff Freshness Guard

WARNING: this successor handoff prompt may be stale.
Refresh `docs/STATUS.md`, `.agentic/handoff_state.yaml`, `docs/handoff/CURRENT_HANDOFF.md`, and the successor prompt before treating this prompt as authoritative.

- latest successor handoff prompt docs/reports/terminal/v041-successor-chat-handoff-after-pr735.md does not mention current handoff commit marker(s): c07f8ec, cf75340

# Übergabeprompt

## 1. Arbeitsumgebung

Local path: `agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Sicherer Stand

Branch: `main`
Commit: `c07f8ec`
Subject: Record protected change planner A1 merge verification log
Semantics: `current_main_head`
Working tree expected clean: `True`

## 2a. Administrative Evidence State

Administrative Evidence Commits nach dem fachlichen Safe-State sind erlaubt, wenn sie nur Logs, Handoff, Summary oder Evidence aktualisieren. Sie ändern den fachlichen Safe-State nicht.

Current HEAD at generation time: `cf75340`
HEAD subject: Plan rule registry improvement backlog (#766)
Allowed after safe state: `True`
Reason: v0.4.2 safety release metadata preparation after PR766

## 3. Release- und Produktstand

Current version: `0.4.2`
Previous version: `0.4.1`
Tag: `v0.4.2`
Zenodo concept DOI: `10.5281/zenodo.20101359`
Zenodo version DOI: `PENDING`
Post-release check: `PENDING`

## 4. Pflichtquellen vor jeder Mutation

Lies diese Quellen zuerst. Wenn eine Quelle fehlt, widersprüchlich ist oder nicht gelesen werden kann, melde Drift und mutiere nicht außer zur Drift-Reparatur.

- .agentic/compiled_agent_context.yaml
- .agentic/handoff_state.yaml
- .agentic/rule_mechanism_inventory.yaml
- .agentic/rule_migrations.yaml
- .agentic/rule_preservation.yaml
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/handoff/START_NEW_CHAT_PROMPT.md
- docs/handoff/CLOSEOUT_BEFORE_CHAT_SWITCH_PROMPT.md
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/planning/RULE_REGISTRY_IMPROVEMENT_PLAN.md
- docs/planning/WORKFLOW_REDUCTION_FOCUS.md
- docs/TEST_GATES.md
- relevant source files and tests for the requested slice

## 4a. Bootloader

Beim Chatwechsel zuerst den Bootloader ausführen: `agentic-kit boot prompt` oder `./ns chat-bootloader`.

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

- `remote-first-no-guess`: Do not guess repository state, command syntax, file locations, release phase, GitHub JSON fields, or available evidence. Inspect the remote repository, command help, known paths, PRs, commits, logs, and authoritative repo files before acting.
- `quality-first-no-shortcuts`: Prefer deterministic, test-backed, maintainable fixes over quick patches. No shortcuts, workaround-only fixes, or chat-only promises for recurring workflow defects.
- `patch-artifact-preflight-before-application`: Before applying generated patch artifacts, run patch-artifact preflight diagnostics and fail on unsafe quoting, ambiguous YAML terms, or control-file weakening.
- `generated-code-syntax-first`: Generated shell and Python artifacts must be syntax-checked before execution or commit; generated code cannot be trusted because it looks plausible.
- `coverage-yaml-terms-must-be-strings`: Coverage YAML required terms must stay strings; colon-containing terms must be quoted or written through structured YAML writers.
- `final-summary-self-validation`: Final summaries must be self-validated against preceding output before treating a block as successful.
- `no-copy-terminal-evidence`: Routine PASS and normal FAIL handoffs must be backed by repo evidence; use d for log-backed PASS and f for log-backed FAIL. Manual terminal paste is only for hard failure, broken logging, unavailable evidence, unusable evidence, or explicit user request.
- `remote-log-lookup-first`: Remote evidence must be inspected first for FAIL or uncertain handoffs; direct-fetch docs/reports/terminal logs before asking for paste-output unless logging is broken or unavailable. The phrase remote evidence is intentionally preserved for rule-preservation coverage.
- `rules-must-be-test-backed`: Durable workflow rules need a stable repository home, documentation, and deterministic tests or guards that fail when the rule disappears or is weakened.
- `yaml-structured-mutation-only`: YAML governance files must be changed through parse-modify-dump or equivalent structured mutation, then parsed again before gates.
- `github-connector-direct-path-first`: For remote GitHub work with known paths, refs, or commits, use direct fetch, update, and PR APIs before search.
- `control-file-preservation`: Protected control files must preserve active rules and required anchors. Information preservation outranks compactness; hard length-limit trimming is forbidden.
- `structured-summary-must-be-enforced`: Relevant local or remote work blocks must end with the canonical structured SUMMARY from FINAL_SUMMARY_CONTRACT.md. Missing, malformed, contradictory, or legacy summaries are workflow drift.
- `governed-rule-registry-before-documentation-rebuild`: A governed modular rule registry must become the canonical source of truth before documentation-management rebuild work resumes.

## 7. Offene Punkte

- Keine offenen PRs im handoff_state.

## 8. Abgeschlossen seit letzter Übergabe

- PR #791 merged Protected Change Planner A1 and verified it via docs/reports/terminal/protected-change-planner-a1-merge-verify.log.
- PR #763 refreshed status and handoff after the PR762 direct-coverage closeout.
- PR #764 added explicit rule-registry direct coverage completion reporting for JSON and human CLI reports.
- PR #766 recorded the accepted rule-registry improvement backlog before the v0.4.2 safety release.

## 9. Letzte bekannte Fehler- und Driftmuster

- `guessing-before-inspection`: Before choosing commands, paths, JSON fields, release checks, or DOI sources, inspect the remote repository and command help. Treat memory and chat summaries as hypotheses until verified.
- `interpreter-discovery-before-python`: Discover the active interpreter and project environment before invoking python, python3, pytest, ruff, or agentic-kit; prefer .venv/bin/python when the project venv exists; avoid naked python; when wrapping shell commands, avoid assuming set -e behavior unless explicitly set and logged.
- `global-cli-or-venv-assumption`: Do not assume global CLIs or an existing venv; use project-local discovery and documented bootstrap paths.
- `nested-triple-quote-code-generator`: Avoid nested quote-based code generation, nested shell/Python quote layers, nested triple-quoted string literals, and nested triple quotes in generated patch scripts; prefer line-list generation, existing helper scripts, simple file writes, or structured update APIs.
- `yaml-colon-term-reinterpreted-as-mapping`: Quote colon-containing YAML terms or use structured YAML writers so plain scalars are not reinterpreted as mappings.
- `standard-error-guards`: Recurring workflow errors must become deterministic guards, tests, or documented failure patterns.
- `interactive-terminal-exit`: Chat-pasted terminal blocks must not end by closing the user terminal; avoid top-level exit and exec unless explicitly requested.
- `stale-successor-handoff-prompt-after-main-merge`: Refresh STATUS, handoff_state, CURRENT_HANDOFF, and successor prompt before treating handoff prose as authoritative.
- `repeated-yaml-governance-file-corruption`: Parse YAML before and after mutation and use a structured writer.
- `final-pass-after-inner-fail`: Final summaries must distinguish work result from evidence result; evidence upload must not relabel failed work as PASS.
- `lossy-control-file-shortening`: Do not shorten protected control files by deleting active rules; use successors, generated projections, or split/reference patterns.
- `structured-summary-drift`: Verify canonical SUMMARY fields and consistency across WORK, EVIDENCE, OVERALL, REMOTE_EVIDENCE, terminal_log, command_report, CHAT_REPLY, and RESULT marker.

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

- 1. `continue-documentation-registry-rebuild` — After this closeout is merged and verified, continue the documentation-management rebuild with one small additive registry or projection slice.
- 2. `verify-rule-registry-reporting` — Verify rule-registry completion reporting remains pass/complete after local main sync.

## 12. Gesperrte Aufgaben

- Remote/destructive GUI actions
- Large GUI architecture expansion before successor-chat bootstrap
- Broad documentation migration until post-PR764 closeout is merged and verified
- Release, tag, or DOI mutation

## 13. Erste Arbeitsanweisung

Merge and verify v0.4.2 release metadata, publish the v0.4.2 tag/release, run post-release checks, then prepare a successor-chat handoff.

## 14. Arbeitsmodus für den Nachfolge-Chat

1. Führe zuerst den Bootloader aus.
2. Lies danach alle Pflichtquellen aus Abschnitt 4.
3. Rekonstruiere den aktuellen Stand aus Repo, PR/CI, Logs und Summary, nicht aus Chat-Erinnerung.
4. Prüfe Drift zwischen Regeln, Tests, Summary-Renderer, Status und Handoff.
5. Bei Drift: warnen, keine Produktmutation, Handoff-Prompt oder Drift-Fix anbieten.
6. Arbeite nur in kleinen, testbaren Slices mit ehrlicher Evidence.

