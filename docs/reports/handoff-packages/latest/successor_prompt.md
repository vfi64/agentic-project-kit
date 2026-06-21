## Machine-readable execution contract

The markdown successor prompt is a compact projection. The machine-readable files take precedence.

Read first: `execution_contract.json`, `successor_context.yaml`, `validation_report.json`, and `source_manifest.json`.

## Durable agentic-kit operating model

- scope: `durable-agentic-kit-operating-model`
- agentic-kit wrappers are the authoritative control plane.
- Use the rule system, command reference, documentation registry, project direction authority, gates, evidence logs, report-retention GC, and successor handoff package as active subsystems.
- GC is technical retention, not semantic documentation migration.
- Historical `ns` migration documents are not active rule locations.

Source authorities:
- `.agentic/compiled_agent_context.yaml`
- `.agentic/transfer_safety_rules.yaml`
- `.agentic/transfer/one_command_transfer_protocol.yaml`
- `docs/planning/project_direction.yaml`
- `docs/DOCUMENTATION_REGISTRY.yaml`
- `docs/reference/agentic-kit-commands.json`
- `docs/reference/AGENTIC_KIT_COMMANDS.md`

Critical rule IDs:
- `local-copy-paste-protocol` (critical)
- `strict-start-decision` (critical)
- `bootstrap_acceptance_gate` (critical)
- `wrapper-first-complete-development-cycle` (critical)
- `successor-package-not-prompt-only` (critical)
- `documentation-authority-model` (critical)
- `repo-backed-rules-and-gates` (critical)
- `gc-retention-not-document-migration` (critical)
- `ns-legacy-not-active-control-plane` (critical)
- `generated-handoff-projection-update-policy` (critical)
- `patch-cycle-diagnostic-gate` (critical)
- `copy-paste-output-discipline` (critical)
- `protected-file-preservation` (critical)

## Current continuation state

- branch: `docs/post-pr1547-handoff-refresh`
- head_matches_origin_main: `True`
- worktree_clean: `False`
- current_release_version: `0.4.11`
- open_tasks_source: `docs/planning/project_direction.yaml`
- document_registry_source: `docs/DOCUMENTATION_REGISTRY.yaml`
- Current state is volatile continuation data, not a durable rule source.

## Wrapper-first complete development cycle

Normal feature lifecycle: feature branch -> tests/audits -> `transfer protected-diff-plan` -> `transfer commit` -> `rules acknowledge` -> fresh successor/LLM context -> `transfer pr-create-complete ... --post-merge-complete` -> sync main -> `transfer post-merge-check` on main -> `transfer repo-status` -> docs/program/standard gates -> final successor handoff package.

`transfer post-merge-check` is a main/post-merge lifecycle check, not a feature-branch pre-PR gate. Use `transfer repo-status` for feature-branch cleanliness.

## Handoff package precedence

- prompt_is_projection_only: `True`
- machine_readable_files_take_precedence: `True`
- source_of_truth: `generator_and_machine_readable_successor_package`
- generator_command: `agentic-kit transfer prepare-successor-handoff --render-prompt`
- Markdown handoff files and latest package files are generated projections; update generator/contract/rule sources first, then regenerate projections.
- Forbidden update path: manual direct edits to generated handoff projections as the primary source of new rules.
- Do not use stale copied prompt text or `NEW_CHAT_HANDOFF_PROMPT.md` as sole authority.

## Patch-cycle diagnostic gate

After one failed patch, exactly one direct correction is allowed. After a second failure in the same patch family, stop mutations, run bounded diagnosis, classify product bug versus test-model bug, and record `next_mutation_allowed`.

## Local copy-and-paste protocol

Use exactly one complete Bash block per local action. The block must start by changing into the repository root, write verbose output to `~/Downloads/*.log`, and end by printing `LOG=...` and `RC=...`.

Chat output after local blocks should be only `LOG=...` and `RC=...`; large diagnostics belong in compact JSON summaries or log files.

Forbidden local-command patterns: loose command fragments, manual editor instructions, naked `python`, naked `pytest`, `git add .`, `{ ... } > "$OUT" 2>&1` as the recommended logging pattern, `cat` of whole diagnostic files, and unbounded grep over reports/outbox/generated logs.

# Successor Chat Prompt

Du bist ein neuer LLM-/Coding-Chat für das Repo `vfi64/agentic-project-kit`.

Arbeite nicht aus Chat-Erinnerung. Quelle der Wahrheit ist der aktuelle Remote-Stand von `main`, der lokale Repo-Zustand, repo-/log-backed Evidenz und das maschinenlesbare Successor-Paket.
