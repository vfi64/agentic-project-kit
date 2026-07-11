## Handoff Freshness Guard

WARNING: this successor handoff prompt may be stale.
Refresh `docs/STATUS.md`, `.agentic/handoff_state.yaml`, `docs/handoff/CURRENT_HANDOFF.md`, and the successor prompt before treating this prompt as authoritative.

- latest successor handoff prompt is missing: docs/reports/terminal/post-pr1834-successor-chat-handoff.md

# Übergabeprompt

## 1. Arbeitsumgebung

Local path: `agentic-project-kit`
Remote: `github.com:vfi64/agentic-project-kit`
Default branch: `main`

## 2. Sicherer Stand

Branch: `main`
Commit: `e4a63287`
Subject: P5d: Deprecate implicit legacy profile (#1834)
Semantics: `last_substantive_work_state`
Working tree expected clean: `True`

## 2a. Administrative Evidence State

Administrative Evidence Commits nach dem fachlichen Safe-State sind erlaubt, wenn sie nur Logs, Handoff, Summary oder Evidence aktualisieren. Sie ändern den fachlichen Safe-State nicht.

Current HEAD at generation time: `e4a63287`
HEAD subject: P5d: Deprecate implicit legacy profile (#1834)
Allowed after safe state: `True`
Reason: administrative evidence/log/handoff commit after substantive safe_state

## 3. Release- und Produktstand

Current version: `0.4.6`
Previous version: `0.4.4`
Tag: `v0.4.6`
Zenodo concept DOI: `10.5281/zenodo.20101359`
Zenodo version DOI: `10.5281/zenodo.20467371`
Post-release check: `PASS`

## 4. Pflichtquellen vor jeder Mutation

Lies diese Quellen zuerst. Wenn eine Quelle fehlt, widersprüchlich ist oder nicht gelesen werden kann, melde Drift und mutiere nicht außer zur Drift-Reparatur.

- .agentic/compiled_agent_context.yaml
- .agentic/handoff_state.yaml
- .agentic/operational_handoff_state.yaml
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
- docs/DOCUMENTATION_REGISTRY.yaml
- docs/planning/PROJECT_DIRECTION.yaml
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

- PR #968 refreshed handoff state after README release-history extraction and v0.4.5 DOI closeout.
- PR #897 merged standard summary validator hardening before this administrative handoff refresh.
- PR #894 merged post-merge gate bootstrap visibility documentation before this administrative handoff refresh.
- PR #892 recorded the post-merge handoff refresh status gate visibility inventory so the workflow can move the gate into more visible kit/ns paths.
- PR #888 added optional patch-preflight slice-gate enforcement so planning-document preflight can require deterministic slice readiness and a clean worktree.
- PR #886 fixed workflow evidence hygiene by moving active next-turn/work-order results out of the repo-backed fixed slot until explicit upload/promotion.
- PR #883 added the GUI gatekeeper implementation inventory and recorded that helper-local PASS is not slice PASS without matching repository governance gates.
- PR #881 refreshed bootstrap/handoff state after PR #880; this post-PR881 refresh records the resulting custom-subject administrative merge commit as current main.
- PR #880 accepted bounded administrative merge chains in the handoff freshness guard while preserving blocking behavior for product merges inside such chains.
- PR #877 fixed the handoff freshness self-reference loop by checking freshly rendered prompt text before warning.
- PR #876 recorded v0.4.4 DOI metadata and post-release evidence at docs/reports/terminal/v044-post-release-verify.log.
- PR #875 prepared v0.4.4 release metadata, after which v0.4.4 was tagged and post-release verified with Zenodo version DOI 10.5281/zenodo.20431326.
- PR #874 records the GUI deterministic gatekeeper migration plan in docs/planning/GUI_DETERMINISTIC_GATEKEEPER_PLAN.md as planning-only work.
- PR #873 added the GUI work order upload strip and was verified by docs/reports/terminal/pr873-final-main-closeout.log.
- PR #838 refreshed post-PR837 administrative handoff state and preserved the last substantive safe-state distinction.
- PR #837 recorded the post-PR836 successor handoff prompt and evidence anchor.
- PR #838 refreshed post-PR837 administrative handoff state and preserved the last substantive safe-state distinction.
- PR #837 recorded the post-PR836 successor handoff prompt and evidence anchor.
- PR #836 refreshed post-PR835 next-step state and is the current successor-handoff safe-state anchor.
- PR #835 recorded PR #834 closeout evidence at docs/reports/terminal/pr834-merge-finalize.log and added docs/reports/terminal/post-pr834-successor-handoff.md as the successor anchor.
- PR #834 repaired generator-backed handoff freshness state so the generated successor prompt anchors to the post-PR834 safe state.
- PR #833 recorded the corrected post-PR831 successor handoff at docs/reports/terminal/post-pr831-successor-handoff.md and superseded the rejected PR825-era stale generated prompt.
- PR #831 recorded PR #830 closeout evidence at docs/reports/terminal/pr830-merge-finalize.log and verified main 011b6dc24829be44c7693c468a90694981cd40ce for the successor handoff anchor.
- PR #825 hardened active handoff freshness checks: state-freshness-check now fails active next-step instructions that point to already-recorded closeout evidence or stale release versions.
- PR #824 recorded PR #823 closeout evidence at docs/reports/terminal/pr823-merge-finalize.log and refreshed STATUS, CURRENT_HANDOFF, and persistent handoff state.
- PR #823 hardened merge-if-green head/base pinning: the command validates the target base branch, requires a PR head SHA, passes --match-head-commit to GitHub, and renders checked base/head refs in the command output.
- PR #821 hardened merge-if-green postconditions: after a successful merge, the command verifies the merge commit on main, waits for main CI, and fails the command result unless main CI is green.
- PR #819 hardened next-turn PR status failed-log diagnostics: red CI now exposes failed check names, GitHub Actions run ids, exact gh run view --log-failed commands, bounded log-fetch status, and no-checks classification for empty rollups.
- PR #817 hardened PASS_ALREADY_DONE target-state classification: generic already-exists output is no longer sufficient success evidence; target-specific classes and hard-failure precedence are test-backed.
- PR #815 hardened release-prep atomicity and remote release readiness: release-prep stops before metadata patching on main/branch failures; release-check and release-preflight block release readiness on remote WARN; release-publish blocks inconclusive remote lookups before tagging.
- PR #813 published v0.4.3 and post-release verification found Zenodo version DOI 10.5281/zenodo.20393329; evidence: docs/reports/terminal/20260526-120216_v043-release-verify.log.
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

- 1. `readme-release-history-extraction-follow-up` — Continue only with the next smallest README release-history extraction follow-up if README size or DOI-history drift reappears.
- 2. `inspect-selected-dead-code-slice` — Remove or justify inspect_selected() dead code in one isolated, test-backed slice.
- 3. `doctor-absolute-path-gate-slice` — Add the missing doctor gate for absolute path leakage in one isolated, test-backed slice.
- 4. `cockpit-action-result-enum-slice` — Replace CockpitActionResult string literal result constants with an enum in one isolated, test-backed slice.
- 1. `b11-gatekeeper-core` — Implement B11 Gatekeeper Core before GUI work: machine-readable READY/WAIT/BLOCKED/FAILED state model, next_action, allowed actions, button enablement contract, safe GitHub/PR/CI checks, race-condition handling, automatic log/evidence classification, no-copy transfer path, and hardened handoff-prompt preparation command.
- 5. `tkinter-workbench-gui-slice-1` — Resume the smallest Tkinter workbench GUI slice only after B11 Gatekeeper Core state/action contract is test-backed and current-state/handoff freshness are clean.

## 12. Gesperrte Aufgaben

- Remote/destructive GUI actions
- Large GUI architecture expansion before successor-chat bootstrap
- Broad documentation migration during release/evidence-kernel hardening closeouts
- Release, tag, or DOI mutation
- GUI product work before post-PR880 bootstrap refresh is merged and verified
- Broad GUI implementation before the deterministic gatekeeper read-only inspection slice
- Gatekeeper product work before post-PR883 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS before repository governance gates pass
- Gatekeeper product work before post-PR886 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS without slice-gate evidence
- Gatekeeper product work before post-PR888 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS without patch-preflight slice-gate evidence
- GUI implementation before B11 Gatekeeper Core state/action contract is test-backed

## 13. Erste Arbeitsanweisung

Review PR #1436 and the refreshed successor handoff package for the release command authority planning slice. After merge, start from fresh main and use centralized historical record docs/planning/PROJECT_DIRECTION.yaml#release-command-authority-slice before DOI, legacy-doc, absolute-path, or GUI work.

## 14. Arbeitsmodus für den Nachfolge-Chat

1. Führe zuerst den Bootloader aus.
2. Lies danach alle Pflichtquellen aus Abschnitt 4.
3. Rekonstruiere den aktuellen Stand aus Repo, PR/CI, Logs und Summary, nicht aus Chat-Erinnerung.
4. Prüfe Drift zwischen Regeln, Tests, Summary-Renderer, Status und Handoff.
5. Bei Drift: warnen, keine Produktmutation, Handoff-Prompt oder Drift-Fix anbieten.
6. Arbeite nur in kleinen, testbaren Slices mit ehrlicher Evidence.

