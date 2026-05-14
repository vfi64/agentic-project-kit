# Agent Instructions

This repository uses explicit project-state and architecture governance. Do not rely on chat history or memory as the source of truth.

## Required Reading Order

Before making non-trivial changes, read these files in order:

1. `docs/architecture/ARCHITECTURE_CONTRACT.md`
2. `docs/DOCUMENTATION_COVERAGE.yaml`
3. `docs/STATUS.md`
4. `docs/TEST_GATES.md`
5. `docs/handoff/CURRENT_HANDOFF.md`
6. relevant source and test files

## Architecture Contract Rule

`docs/architecture/ARCHITECTURE_CONTRACT.md` is a required project gate document.

You must check it before changes that affect any of the following:

- project purpose or product boundary;
- CLI command behavior;
- generated project structure;
- profiles or policy packs;
- `doctor`, `check-docs`, `check-todo`, release checks, or other gates;
- repository state files or handoff conventions;
- agent instructions, PR templates, evidence staging, or review workflow;
- automation boundaries, GitHub integration, or future multiuser assumptions.

If a change conflicts with the architecture contract, do not silently implement it. Instead:

1. state the conflict;
2. propose either a smaller implementation or an architecture-contract update;
3. make the contract update explicit and reviewable.

## Modular Implementation Rule

New non-trivial program functionality must be implemented modularly: core logic belongs in a focused, importable module; CLI files are thin adapters; tests target the core module and the CLI boundary separately.

Existing monoliths must not be allowed to grow. When a touched file already mixes unrelated responsibilities, the preferred direction is incremental modularization: extract cohesive logic into a named module, keep the public command stable, and add regression tests before or with the extraction.

This rule applies especially to new audit, repair, workflow, release, validation, doctor, and generated-project logic. Review-only exceptions are allowed only when extraction would be larger than the requested slice; the exception must name the monolith risk and the next safe modularization step.

## Documentation Coverage Rule

`docs/DOCUMENTATION_COVERAGE.yaml` is the source of truth for required documentation coverage across README, gate docs, state docs, agent instructions, release/citation docs, safety notes, and architecture concepts.

Before adding or changing any public command, generated file, workflow, gate, profile, policy pack, release process, safety rule, evidence convention, or architecture concept:

1. check whether the change is already covered by the documentation coverage matrix;
2. update the matrix when a new public concept must remain visible;
3. update the affected documentation in the same change;
4. run `agentic-kit check-docs` so missing coverage is detected.

Do not add implementation-only features that are invisible to new users, maintainers, or coding agents.

## Rule Hardening Rule

Every new or changed governance rule must be hardened in the same change by one of these mechanisms:

- deterministic unit or integration test;
- documentation coverage requirement in `docs/DOCUMENTATION_COVERAGE.yaml`;
- `doctor`, `check-docs`, `release-check`, or `check-todo` gate;
- generator fixture test when generated projects are affected;
- explicit review-only exception when deterministic enforcement is not currently possible.

Do not add a normative project rule as prose only. If a rule is intentionally review-only, state why it cannot currently be machine-checked and what evidence reviewers should inspect.

## Deterministic Cell Orchestration Decision Rule

For complex, rule-bound AI-generated outputs, check whether Deterministic Cell Orchestration (DCO) would reduce drift or improve validation, repair, rendering, or auditability.

DCO means that an output is split into explicit, typed cells. Each cell can be validated independently, failed cells can be repaired selectively, and the final user-facing artifact is rendered deterministically from validated cells.

Use DCO when it provides a clear advantage for at least one of these cases:

- complex output contracts with required sections or repeated structures;
- outputs that need selective repair instead of full regeneration;
- audit, handoff, review, release, or report artifacts that benefit from machine-readable intermediate structure;
- outputs where deterministic rendering is safer than model-generated formatting;
- workflows where failed subparts should be localized to a specific cell.

Do not use DCO when a simple document, CLI command, gate, or Markdown update is clearer and easier to maintain. DCO must reduce complexity at the workflow level; it must not add schema, validator, repair, or renderer layers merely for architectural symmetry.

When DCO is used, prefer a minimal architecture:

- stable cell IDs;
- explicit cell types;
- required fields;
- deterministic validation rules;
- bounded repair policy, if repair is allowed;
- deterministic renderer expectations;
- tests for schema, validation, repair behavior, and rendering where practical.

DCO validates structure, required fields, dependencies, allowed values, and known rule violations. It must not be presented as proof of semantic correctness unless the semantic property has been converted into a deterministic rule.

This decision rule is currently review-only. It cannot be fully machine-checked because the decision to use DCO depends on architectural judgment. Reviewers should inspect whether the chosen output shape reduces drift and improves validation, repair, rendering, or auditability without making simple workflows harder to maintain.

See `docs/ideas/DETERMINISTIC_CELL_ORCHESTRATION.md` for the curated idea note and lifecycle guidance. The idea note is not a binding implementation requirement.

## Governed Workflow Design Principles

For non-trivial workflow, repair, release, validation, or agent-facing features, prefer explicit governed design over implicit agent behavior.

Use explicit state models when a process is persistent, resumable, multi-step, side-effecting, or failure-prone. State models should name the allowed states, allowed transitions, no-op states, stop states, and cleanup paths. Avoid adding states that do not change behavior or improve diagnostics.

Use contract-first CLI design for public commands. Before implementation, define inputs, outputs, exit codes, state changes, error cases, idempotency expectations, and documentation requirements. CLI adapters should remain thin; core behavior belongs in importable modules with tests.

Prefer idempotent operations where practical. Re-running a request, status, cleanup, validation, or report command should either produce the same safe result or fail with a clear diagnostic. Repeated execution must not silently corrupt state or erase evidence.

Use stop-state principles for failures. Failure states such as `FAILED` must preserve evidence and require diagnosis before cleanup or continuation. Do not automatically skip, overwrite, or repair failure evidence merely to keep a workflow moving.

Separate model output from runtime action. An LLM or coding agent may propose plans, commands, patches, or repairs, but deterministic project logic should validate executable actions before they change repository state, release state, workflow state, or generated artifacts.

Prefer typed intermediate artifacts when they improve reliability. Machine-readable JSON or YAML reports, repair plans, workflow states, or validation results should feed deterministic renderers or summaries when that reduces parsing fragility. Do not replace clear Markdown with typed artifacts unless tests, repair, rendering, or auditability benefit.

Use bounded repair instead of open-ended regeneration. Repairs should target named failure classes, keep diffs small, avoid inventing semantic content, record the repair reason, and stop after a bounded number of attempts.

Use capability matrices when permissions or command availability become conditional. A capability matrix is preferred over scattered conditionals when commands depend on role, state, profile, workflow phase, or maintainer-only authority.

Use Architecture Decision Records (ADRs) for durable architecture choices with real alternatives and long-term consequences. Do not create ADRs for routine implementation details.

These governed workflow principles are currently review-only unless a specific feature turns them into deterministic tests, schema checks, doctor checks, documentation coverage, or CLI contracts. Reviewers should inspect whether a design reduces drift, improves restartability, preserves evidence, and keeps simple workflows simple.

See `docs/ideas/GOVERNED_WORKFLOW_PATTERNS.md` for preserved workflow-pattern notes and `docs/ideas/LAYERED_CLI_USABILITY.md` for the non-binding usability-layer model that keeps the CLI Golden Path small while allowing advanced automation.

## Remote Work Authorization

For `agentic-project-kit`, an assistant or coding agent may work without additional confirmation on remote feature or documentation branches when the task fits the current request and architecture contract.

Allowed without additional confirmation:

- create new feature or documentation branches;
- edit files on those branches;
- repair follow-up failures from tests, `ruff`, `agentic-kit check-docs`, `agentic-kit doctor`, documentation coverage, or fixture drift;
- keep tests, documentation, status, handoff, `AGENTS.md`, PR templates, architecture files, and coverage files consistent;
- create or update pull requests;
- add small correction commits to the same work branch;
- fix obvious fixture, documentation, or drift problems.

Not allowed without explicit maintainer approval:

- write directly to `main`;
- merge pull requests;
- create or push release tags;
- create release or publication artifacts;
- raise project versions for release preparation;
- change repository visibility, access rights, or private configuration;
- make irreversible history changes;
- change architecture direction when multiple plausible options exist.

Remote branch commits are allowed under this rule, but publication, release, and merge decisions remain maintainer-owned.

## Evidence Requirements

Keep evidence requirements explicit and bounded. Do not commit broad logs, credentials, private runtime state, or unreviewed generated evidence.

do not weaken tests, documentation gates, architecture checks, release checks, or coverage checks to make a task pass. If a rule is wrong, propose a reviewable rule change instead.

## Responsibility Split

Use this responsibility model from the architecture contract:

```text
LLM / coding agent      -> propose, explain, draft, inspect, and prepare changes
agentic-kit doctor      -> check contracts, drift, evidence, gates, and repository health
human / maintainer      -> decide, approve, reject, merge, and own architectural judgment
```

## Required Local Gate

Before claiming completion, run or request evidence for:

```bash
git status --short
git branch --show-current
python -m pytest -q
ruff check .
agentic-kit check-docs
agentic-kit doctor
```

If a command was not run, say so explicitly and explain why.

## Standard next-step terminal workflow

For app-based ChatGPT workflows, use the compatibility entrypoint as the normal local command unless a more explicit workflow command is needed:

```bash
cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
python tools/next-step.py
```

A plain next-step command is a no-op while `.agentic/current_work.yaml` is `READY`. Request the configured workflow explicitly first:

```bash
.venv/bin/python tools/next-step.py --request
```

After the command finishes, the expected chat reply is usually only:

```text
done
```

The short acknowledgement `d` is also valid. The assistant must then inspect the available workflow state or copied output and propose the next safe step.

This next-step workflow is the preferred normal path instead of long manual Copy-and-Paste terminal blocks. Long terminal-output blocks are still allowed when a local command did not write enough bounded evidence for review.

The explicit CLI variant remains supported for targeted operation:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow status
agentic-kit workflow cleanup
```

See `docs/WORKFLOW_OUTPUT_CYCLE.md` for state-machine details, evidence pointers, and cleanup rules.

## Chat-assisted terminal workflow

When work is coordinated through a chat-based LLM without Codex CLI, Claude CLI, or another local agent runtime, prefer the standard next-step terminal workflow above. Use longer copy-pasteable terminal blocks only when a bounded local workflow command is not sufficient.

Recommended command-block shape:

```bash
printf "\n========== START: short-run-name ==========\n"
# commands follow here
```

Rules:

- Put the visual separator as the first command in longer terminal blocks so the start of the current run is visible in scrollback.
- Use descriptive separator labels, for example `START: local-gate`, `START: create-feature-branch`, or `START: release-check`.
- Do not paste raw decorative separator lines such as `----------`, `++++++++++`, or `##########` as standalone shell commands.
- For local validation runs, prefer `./tools/screen_control_gate.sh` so the output is mirrored to `Screen-Control_Output.txt`.
- `Screen-Control_Output.txt` is local evidence for human/LLM review and must not be committed.

## Shell command safety for chat-assisted work

When working through a chat-only LLM workflow without a local coding-agent runtime, prefer copy-pasteable terminal blocks that are robust in zsh.

Rules:

- Start longer terminal blocks with a visible separator command as the first command.
- Do not use raw decorative separator lines as standalone shell commands.
- Avoid heredocs in chat-delivered terminal blocks unless they are strictly necessary.
- Prefer checked-in helper scripts, python3 -c commands, or small patch files over multiline heredocs.
- If the terminal shows heredoc> or quote>, stop the unfinished input with Ctrl-C and run `git status --short` and `git branch --show-current` before continuing.
- Use `./tools/screen_control_gate.sh` to capture local evidence in `Screen-Control_Output.txt` when local validation output should be shared.

## Diagnose-/Output-Transfer-Regel

Wenn der arbeitende LLM/Agent keinen direkten Zugriff auf die lokale Kommandozeile, lokale Dateien oder die lokale Repo-Kopie hat, müssen relevante Diagnose-, Test-, Inspektions- und Gate-Ausgaben automatisch in Dateien geschrieben werden.

Diese Dateien sollen am Ende eines Arbeitsblocks oder Slices in einen geeigneten versionierten oder remote zugänglichen Pfad übernommen und gepusht werden, sofern sie für die weitere Auswertung nützlich sind.

Ziel:
- keine manuelle Copy-&-Paste-Abhängigkeit,
- reproduzierbare Auswertung,
- bessere Anschlussfähigkeit in neuen Chats,
- auditierbare Entwicklungsschritte.

Bevorzugte Pfade:
- docs/reports/
- artifacts/
- Logs/SharedManualTestRuns/
- ein projektspezifischer Diagnose-/Report-Pfad

Nicht geeignet:
- ignorierte tmp-Dateien als alleinige Informationsquelle,
- nur Terminalausgabe ohne gespeicherte Datei,
- Screenshots als primäre Diagnosequelle.

Weiterhin gilt:
- Terminalblöcke müssen quoting-sicher bleiben.
- Keine heredocs.
- Keine riskanten mehrzeiligen python -c-Kommandos.
- Längere Blöcke beginnen mit printf-Titelzeile.

## Terminal-Rückmelde-Regel

Jeder vorgeschlagene Terminalblock muss am Ende klar markieren, welche Rückmeldung erwartet wird.

Wenn keine Terminalausgabe benötigt wird:

- Rückmeldung danach: Nur `done` reicht; die Kurzform `d` ist ebenfalls zulässig.

Wenn Terminalausgabe benötigt wird:

- Rückmeldung danach: Terminalausgabe notwendig.
- Die relevante Ausgabe soll exakt zwischen folgenden Markern kopiert werden:

```text
################### Begin Copy Terminal #####################
... Terminalausgabe ...
################### End Copy Terminal #####################
```

Die Markierung verhindert, dass Shell-Kommandos, Prompts, Diagnoseausgaben und Chattext vermischt werden.

## Current Workflow Output

When the working LLM/agent cannot directly access the local shell or local repository state, longer terminal, diagnostic, inspection, or gate outputs should be written to:

`docs/reports/CURRENT_WORKFLOW_OUTPUT.md`

This file is a volatile handoff bridge for the current working slice. It may be overwritten in later slices and is not a historical archive.

Use it to speed up app-based ChatGPT workflows and reduce manual copy-and-paste.

Only create additional permanent report files when the result has long-term audit, release, or decision value.

## Diagnosebericht-Hygiene

Diagnose-, Inspektions- und Gate-Ausgaben sollen bei fehlendem direktem Shell-Zugriff des Agents in Dateien geschrieben werden.

Es sollen aber nicht alle Zwischenberichte dauerhaft versioniert werden.

Bevorzugt wird:

- ein finaler, zusammenfassender Slice-Report pro Arbeitsabschnitt,
- plus gezielte Gate-, Release- oder Audit-Berichte, wenn sie langfristigen Evidenzwert haben.

Temporäre Rohberichte sollen gelöscht oder uncommitted bleiben, sobald sie ihren Zweck erfüllt haben.

## Workflow output handoff

When complete local terminal evidence is needed, prefer `python tools/next-step.py` over manual Copy-and-Paste. The script cycles through `TEST`, `UPLOAD`, and `CLEANUP`; see `docs/WORKFLOW_OUTPUT_CYCLE.md`. Evidence branches are temporary and must be cleaned up.
