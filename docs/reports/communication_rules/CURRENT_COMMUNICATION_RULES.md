# Current communication rules refresh

Status: generated
Generated at: 2026-05-29T19:49:50+00:00
Next reply trigger: `d2`

## Assistant instruction

On user reply d2, read this generated file before continuing and refresh the active dialog rules from the repo-backed source snapshots.

## Source files

- `docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md`
- `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
- `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
- `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
- `.agentic/compiled_agent_context.yaml`
- `.agentic/handoff_state.yaml`

## Source snapshots

### `docs/workflow/NO_COPY_TERMINAL_EVIDENCE.md`

```text
# No-Copy Terminal Evidence Policy

Status: active
Decision status: accepted

## Purpose

Routine collaboration must not require terminal copy-and-paste. A user response of d is meaningful only when the terminal action produced repo-backed evidence that can be inspected later.

## Binding rules

- Relevant terminal actions must write durable evidence under docs/reports/terminal or docs/reports/command_runs.
- PASS must not be printed after a failed required command.
- After log-backed PASS, the user may answer d without pasting terminal output.
- Normal FAIL handoff must use f and repo-backed evidence, typically docs/reports/command_runs/LATEST_COMMAND_RUN.txt plus the referenced terminal log. Manual terminal output is required only when FAIL evidence is unavailable, logging is broken, the process aborted, the terminal was lost, kill -9 occurred, pushed evidence is unavailable, or the user explicitly asks for pasted output.
- Future handoff YAML and generated handoff prompts must include this policy and must not accumulate obsolete workaround rules.

## `d`/`f` command-result handoff

For repo-backed agent commands, `docs/reports/command_runs/LATEST_COMMAND_RUN.txt` is the canonical first read after `d` or `f`. The referenced command report records the outcome, exit code, branch, script hash, and terminal-log path. A normal FAIL must still leave remote evidence; otherwise the workflow is broken and must be repaired.


## Fixed remote-next dialog path

For dialog-oriented local work, the preferred target path is `agentic-kit remote-next`. The command synchronizes `main` and executes the next typed work order through the repo-backed typed work-order runner. Chat assistants should prefer queuing a typed work order for this path over pasting long local terminal blocks. The GUI must use the same command path instead of introducing a separate execution model.

`remote-next` reports `expected_closeout_path=` lines when a typed work order creates repo-backed evidence. Those paths are the canonical dirty-state closeout set for the next evidence PR and are intended for future GUI display.

## Full-output transfer requirement

Every local task initiated by the assistant must capture the complete terminal transcript in a repo-backed transfer or evidence file that the assistant can inspect without asking the user to paste output. The captured record must include stdout, stderr, exit code, argv, start time, end time, current branch, HEAD, dirty-state evidence, and the generated terminal-log or command-report path.

Manual paste is an exception, not the normal workflow. It is allowed only when the transfer/evidence file cannot be produced or retrieved, for example after kill -9, terminal loss, machine crash, network failure before push, Python startup failure, filesystem failure, or an explicitly reported broken logging path.

## Remote Python task requirement

Local execution requests must be delivered as repo-backed Python programs, typed work orders, or `agentic-kit` commands. They must run through the repository virtual environment and must not depend on global Python or shell state. For this repository the canonical local runtime is `.venv/bin/python` and `.venv/bin/agentic-kit` with Python 3.13.

Long ad-hoc shell blocks, fragile multi-line `python -c` strings, and raw decoration lines as terminal input are not valid default execution paths. They are recovery-only tools when the repo-backed Python or typed-work-order path is unavailable.
```

### `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`

```text
# Chat Communication Contract

Status-date: 2026-05-22
Status: normative governance contract
Scope: LLM-to-user, user-to-LLM, LLM-to-terminal, and terminal-to-LLM communication for agentic-project-kit work

## Purpose

This contract removes ambiguity from chat-assisted development. Communication shortcuts, terminal blocks, failure handling, and follow-up behavior must be interpreted from repository evidence, not from memory or good intentions.

Large LLMs must have less freedom, not more prose. The durable pattern is: read the required sources, verify current state, run deterministic checks, produce honest evidence, then continue.

## Required startup behavior for successor chats

A successor chat must not start with a terminal block, mutation, merge, release, or GUI feature patch. It must first read the mandatory source list from `.agentic/compiled_agent_context.yaml` and then the human governance documents named there.

Minimum first-read set:

1. `.agentic/compiled_agent_context.yaml`
2. `docs/governance/FINAL_SUMMARY_CONTRACT.md`
3. `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`
4. `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`
5. `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`
6. `docs/TEST_GATES.md`
7. `docs/STATUS.md`
8. `docs/handoff/CURRENT_HANDOFF.md`
9. relevant source and test files for the requested slice

If any of these sources are missing, contradictory, stale, or unreachable, the chat must report drift and avoid mutation until the drift is resolved or a handoff prompt is produced.

## User acknowledgements

Short user replies are control signals, not evidence.

- `d` or `D`: the previous local block appears finished from the user's perspective. The assistant must still inspect terminal output, remote log, command report, PR state, branch, dirty state, and summary before treating it as success.
- `f` or `F`: the previous block failed or the user reports failure. The assistant must first look for local or remote evidence paths and propose log upload/recovery before asking for pasted output.
- `w` or `W`: continue, but only within the current governance and evidence rules.
- `paste-output`: manual output is needed because repo-backed or local evidence is unavailable, broken, or insufficient.
- `stop`: no further mutation or terminal instructions.

A suggested next chat reply for a failed workflow should normally be `f`, not `d`, when remote evidence exists but the work failed. Remote evidence can prove failure; it does not convert failure into success.

## LLM-to-user rules

The assistant must:

- state the current source of truth and evidence basis for any next action,
- separate product progress from workflow/evidence progress,
- report when a failure is caused by tooling, shell environment, summary rendering, CI, docs, tests, or product code,
- avoid asking for full pasted output when a local or remote log path exists,
- prefer a minimal evidence-recovery step over a large new patch after failure,
- never treat a user's `d` as proof that the work passed,
- never hide that a block was only partially executed,
- explicitly say when remote evidence is unavailable.

## LLM-to-terminal rules

Canonical workflow execution must not depend on long ad-hoc shell blocks. When terminal execution is unavoidable, the block must be bounded, copy-safe, and evidence-aware.

Forbidden as canonical control mechanisms:

- heredocs,
- risky multi-line `python -c` strings,
- raw decoration lines that execute as shell commands,
- implicit POSIX tools as correctness dependencies,
- status variables mutated inside `{ ... } | tee "$LOG"` pipeline/subshell constructs,
- handwritten legacy summary footers after `./ns summary`,
- `REMOTE_EVIDENCE: PENDING` in final summaries,
- continuing to PR creation, merge, release, or tagging after a blocking gate failure.

Allowed routes:

- repository-owned Python runners,
- `agentic-kit` CLI commands backed by Python core logic,
- `./ns` as a thin convenience adapter when the local shell is healthy,
- generated command reports and terminal logs stored under the documented evidence paths.

## Terminal-to-LLM rules

Every non-trivial terminal or remote command workflow must end in evidence that the assistant can inspect:

- a rendered final summary printed in the terminal output,
- the same rendered final summary captured in the terminal log or command report,
- a terminal log path or command report path,
- branch and dirty-state evidence when mutation occurred,
- PR/CI/merge state when remote mutation occurred,
- explicit downgrade when evidence is partial, chat-only, or failed.

A chat-only structured summary is not enough for terminal-directed work. The terminal block must render the structured summary itself, normally through `./ns summary`, so the evidence remains inspectable after chat handoff.

A terminal log upload is evidence transport. It does not change the result of failed work.

If a terminal summary names a concrete remote log path, verify that exact path directly before using search results. Search lag is not evidence that a pushed log is missing.

## Failure communication

On failure, the next assistant response must choose the least lossy recovery path:

1. inspect remote evidence if available,
2. inspect local log path if the user pasted it,
3. propose a minimal log-upload or status-recovery step,
4. ask for pasted output only when evidence cannot be retrieved or uploaded.

A blocking gate failure must stop later mutation sections. The final result must identify the first blocking failure and the actual state reached.

## PASS communication

A final PASS claim requires all of the following:

- required work passed,
- required gates passed or were honestly marked not run/not required,
- evidence exists and matches the claim,
- remote evidence is PASS when the workflow requires no-copy continuation,
- no earlier required inner FAIL was overwritten,
- the final summary is rendered through the canonical renderer route,
- terminal-directed work printed the structured summary in the terminal output and captured it in the terminal log.

## Optimization requirement

For every future rule or workflow step, prefer the option that reduces LLM discretion, reduces duplicated wording, improves portability, and makes drift machine-detectable. If a rule cannot yet be machine-checked, it must name the review-only exception and the evidence a reviewer must inspect.

Manual GUI verification must not hide the final result behind an interactive terminal read prompt. Use a two-phase record: GUI launch first, then a non-interactive PASS or FAIL evidence record with a generated summary invocation.

## Mandatory no-copy transfer rules

For assistant-initiated local work, complete terminal output must be captured in a repo-backed transfer or evidence file. The record must contain stdout, stderr, exit code, argv, start time, end time, current branch, HEAD, dirty-state evidence, and a concrete log or command-report path. A normal FAIL must still produce inspectable evidence; the assistant must not ask for pasted output when the transfer file exists or can be pushed.

Local tasks must normally be provided as repo-backed Python programs, typed work orders, or `agentic-kit` commands and must run through the repository virtual environment. Global Python, global shell state, long ad-hoc shell blocks, risky multi-line `python -c`, and raw visual separator lines as terminal commands are forbidden as default control paths.

Manual copy-and-paste of terminal output is allowed only after a hard local failure that prevents evidence creation or transfer, including kill -9, process startup failure, terminal loss, machine crash, filesystem failure, network failure before push, or explicitly broken logging.
```

### `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`

```text
# Portable Chat Execution Contract

Status-date: 2026-05-24
Status: normative governance contract
Scope: operating-system-independent execution rules for chat-assisted workflows

## Purpose

The kit must work across macOS, Linux, and Windows assumptions. Canonical workflow correctness must not depend on POSIX-only shell utilities, a healthy inherited `PATH`, or long copy-pasted shell scripts.

The observed failure mode was simple and severe: a generated block could not find required tools. A governance system that cannot preserve evidence when the command environment is degraded is not robust enough for large-LLM operation.

## Canonical rule

Durable workflow behavior belongs in Python modules, tests, and CLI commands. Shell commands are adapters only (`shell commands are adapters only`).

Canonical implementation must prefer:

- `pathlib.Path` for paths,
- `shutil` for file operations and tool discovery,
- `platform` for platform inspection,
- `subprocess.run([...], shell=False)` when external commands are unavoidable,
- explicit return objects or structured text reports,
- direct log writing through Python file APIs,
- one summary renderer and one validation vocabulary.

Canonical implementation must not require:

- `cp`, `tail`, `grep`, `sed`, `head`, `tee`, `find`, or `sh`,
- hard-coded Unix paths such as `/usr/bin/git`, `/bin/cp`, or `/tmp` as normative rules,
- shell pipelines for correctness,
- shell-specific quoting behavior,
- shell activation of a virtual environment as the only path to execution.

## Bootstrap principle

The portable bootstrap path is a Python entry point, not a shell recovery script.

Required direction:

- `agentic-kit bootstrap-check` verifies Python, repo root, package importability, required governance files, summary renderer importability, and optional Git availability through portable Python APIs.
- `agentic-kit comm-rules-check` verifies communication, summary, bootstrap, and drift contracts.
- `agentic-kit handoff-prompt --reason drift` emits a successor-chat prompt when drift is detected.

`./ns` may expose shortcuts for local convenience, but it must not be the only canonical route.

## Local repository freshness rule

Local repository work must start from a verified fresh base. The workflow must fetch the remote, compare the intended local base with its upstream, and stop or synchronize before any mutation. A local branch that is behind `origin/main`, a dirty worktree, or untracked command artifacts are preflight findings, not details to ignore.

For local `main`-based work, the safe precondition is: `git fetch origin`, clean or preserved local changes, `git switch main`, local HEAD equal to `origin/main`, then feature branch creation. Mutation before that precondition is forbidden.

## Remote connector route rule

When a GitHub connector is available, remote repository inspection must start with the direct connector route: `get_repo` for repository identity, `fetch_file` for known file paths, `fetch_commit` for known commits, `get_pr_info` for known pull requests, `fetch_commit_workflow_runs` for CI evidence, and `compare_commits` for branch comparisons.

Search is for unknown paths or symbols. Raw URLs and local fallbacks come after connector access is unavailable or insufficient.

## Governance YAML mutation rule

Governance YAML mutation must use parse-modify-dump. Tools and command scripts must load YAML through a parser, mutate typed data, write it through a structured emitter, parse the result again, and then run YAML integrity tests.

Manual indentation patches, regex insertion into YAML lists, unparsed string concatenation, and late quote repair after a failed test are forbidden. A YAML parse error in CI is a workflow defect, not a harmless iteration.

## External command rule

When Python code must call an external command, it must use an argument list and `shell=False`. The code must capture stdout, stderr, return code, and command identity in a reportable structure. It must handle command-not-found as a normal diagnostic result, not as an unhandled crash.

## Evidence rule

Evidence generation must be possible without POSIX file-copy utilities. Python code must be able to create log directories, write logs, copy or move report files, and name local and remote evidence paths using portable path handling.

## Chat block rule

A chat-generated terminal block is allowed only as a bounded fallback or adapter. It must not be the authoritative expression of a reusable workflow. If a shell block is used because the portable runner is missing or broken, the summary must say so and must not claim the portable workflow is healthy.

## OS independence rule

Documentation and tests must not define macOS-only, Linux-only, or Windows-only paths as canonical. OS-specific examples may appear only when labeled as examples or local recovery snippets, not as normative kit behavior.

## Optimization requirement

Whenever a workflow is converted from shell to Python, the implementation must remove assumptions instead of merely translating shell commands. Prefer file parsing, imports, and deterministic checks over external process execution whenever possible.
```

### `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`

```text
# Chat Bootstrap and Drift Contract

Status-date: 2026-05-24
Status: normative governance contract
Scope: mandatory startup sequence, drift classes, drift response, and successor-chat handoff behavior

## Purpose

This contract makes chat handoffs reproducible. A new chat must be able to continue without trusting previous-chat memory. It must fetch the current rules, detect contradictions, and stop before mutation when drift is present.

## Mandatory startup sequence

A successor chat must perform this sequence before proposing any mutation block:

1. Identify the repository and remote.
2. Read `.agentic/compiled_agent_context.yaml`.
3. Read every mandatory source named by the compiled context.
4. Read `docs/governance/FINAL_SUMMARY_CONTRACT.md`.
5. Read `docs/governance/CHAT_COMMUNICATION_CONTRACT.md`.
6. Read `docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md`.
7. Read `docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md`.
8. Read `docs/TEST_GATES.md`, `docs/STATUS.md`, and `docs/handoff/CURRENT_HANDOFF.md`.
9. Inspect relevant source files and tests for the requested slice.
10. State any drift or uncertainty before acting.

A chat may summarize these sources compactly, but it must not replace the source-reading step with memory.

## Remote repository connector route

For remote-only work on GitHub repositories, use the GitHub connector direct-path-first workflow before falling back to search, guessed URLs, or local shell commands.

Required first route:

1. call `get_repo` for the exact `repository_full_name`;
2. call `fetch_file` for known paths instead of searching for them;
3. call `fetch_commit`, `get_pr_info`, `fetch_commit_workflow_runs`, or `compare_commits` for known commits, pull requests, runs, or branch comparisons;
4. use repository search only when the path or symbol is genuinely unknown;
5. fall back to raw URLs or local commands only after connector access is unavailable or insufficient.

This route is a token- and drift-control rule. Repeatedly trying raw URLs, branch guesses, or unrelated searches while a known connector path exists is drift.

## Drift classes

The system must treat the following as drift:

- compiled context names sources that are missing,
- human governance documents and compiled context disagree,
- final summary vocabulary differs between docs, renderer, and tests,
- `REMOTE_EVIDENCE` accepts forbidden final values such as `PENDING`, `NONE`, or `CHAT_ONLY`,
- `NO-COMMAND` is declared in docs but unsupported by the renderer or tests,
- status or handoff documents point to stale next steps,
- communication rules are absent from coverage or handoff,
- portable execution rules are absent from coverage or tests,
- a workflow claims no-copy completion without remote-readable evidence,
- a workflow asks for pasted output although usable local or remote evidence exists,
- shell-only snippets are presented as canonical cross-platform execution,
- local work starts while `main` is behind `origin/main`, the worktree is dirty, or the branch does not match the intended base,
- remote repository inspection ignores the GitHub connector direct-path-first workflow,
- governance YAML is mutated without a parse-modify-dump workflow and post-mutation parse validation.

## Drift response

On drift detection, the assistant or tool must:

1. warn that drift exists,
2. identify the source files involved,
3. avoid mutation-oriented work unless the mutation is the drift fix itself,
4. offer a comprehensive handoff prompt when chat length, ambiguity, or contradictory state makes continuation unsafe,
5. prefer a small deterministic fix slice over broad product work.

Drift must not be hidden behind a final PASS. If drift was found and not fixed, the final summary must report it honestly.

## Governance YAML mutation rule

Governance YAML includes `.agentic/handoff_state.yaml`, `.agentic/compiled_agent_context.yaml`, `.agentic/no_copy_terminal_policy.yaml`, `docs/DOCUMENTATION_COVERAGE.yaml`, and `docs/DOCUMENTATION_REGISTRY.yaml`.

The only allowed mutation workflow for these files is parse-modify-dump:

1. parse the original YAML with `yaml.safe_load`;
2. mutate typed Python data structures;
3. write with `yaml.safe_dump` or an equivalent structured emitter;
4. parse the written file again;
5. run the relevant YAML integrity, coverage, and governance tests before claiming success.

Free-text insertion, regex insertion, manual indentation patches, and unparsed string concatenation are forbidden for governance YAML. Quoting a colon after the fact is not enough; the workflow must prevent malformed YAML from being created.

## Handoff prompt requirements

A drift handoff prompt must include:

- repository path and remote identity,
- current branch and commit if available,
- mandatory first-read source list,
- current summary contract vocabulary,
- communication rules including `d`, `f`, `w`, `paste-output`, and `stop`,
- portable execution rule,
- known drift findings,
- forbidden patterns,
- last safe state,
- next safe step,
- instruction not to mutate before reading the mandatory sources.

## Local repository freshness precondition

Before any local mutation, the operator must verify the local repository against the intended remote base. For work based on `main`, the local branch must be `main`, `origin/main` must be fetched, the local HEAD must match `origin/main`, and the worktree must be clean except for explicitly preserved local diagnostics.

If the local repository is behind, the workflow must update it before mutation. If local changes exist, they must be stashed, committed to an evidence branch, or explicitly stopped for review. Continuing product or governance mutation from a stale or contaminated local tree is drift.

## Machine-readable companion

`.agentic/compiled_agent_context.yaml` is the compact machine-readable companion for this contract. It must list the mandatory bootstrap sources and the drift reaction rules. Human documents remain authoritative, but the compiled context is the fastest startup map for LLMs.

## Deterministic check direction

`agentic-kit comm-rules-check` must become the deterministic check for this contract. It should fail closed when required anchors are missing or contradictory. Until that command exists, reviewers must inspect this document, the compiled context, the final summary contract, and renderer tests together.

## Optimization requirement

Do not solve drift by adding more overlapping prose to every document. Prefer one canonical document per concept, compact cross-references elsewhere, compiled machine-readable anchors, and tests that catch known regressions.

## Administrative Evidence State für Handoff-Prompts

Ein Handoff-Prompt unterscheidet zwischen `safe_state` und `administrative_evidence_state`. `safe_state` beschreibt den letzten fachlich/substanziellen Arbeitsstand. Reine Log-, Summary-, Handoff- oder Evidence-Commits nach diesem Stand dürfen als `administrative_evidence_state` geführt werden und machen den fachlichen Safe-State nicht automatisch stale.

Ein Nachfolge-Chat muss prüfen, ob spätere Commits nur administrative Evidence betreffen. Fachliche Änderungen nach dem Safe-State sind Drift und müssen vor Produktarbeit geklärt werden.

Dieses Modell verhindert die Endlosschleife, bei der ein finaler Log-Commit den gerade erzeugten Handoff-Prompt sofort wieder formal veralten lässt.
```

### `.agentic/compiled_agent_context.yaml`

```text
schema_version: 1
updated:
  date: '2026-05-24'
  reason: remote connector route, YAML mutation workflow, and control file preservation hardening
purpose: Fast, redundant-free, machine-readable companion to the human governance docs.
source_policy:
  remote_first_no_guess: true
  human_docs_remain_authoritative: true
  compiled_yaml_must_match_docs: true
  new_rules_need_docs_yaml_tests: true
  local_repo_freshness_before_local_work: true
  github_connector_direct_path_first: true
  yaml_governance_mutation_requires_parse_modify_dump: true
  control_file_preservation_required: true
priority_order:
- .agentic/compiled_agent_context.yaml
- .agentic/control_file_preservation.yaml
- .agentic/handoff_state.yaml
- .agentic/no_copy_terminal_policy.yaml
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md
- docs/DOCUMENTATION_REGISTRY.yaml
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- docs/TEST_GATES.md
- docs/DOCUMENTATION_COVERAGE.yaml
mandatory_successor_chat_sources:
- .agentic/compiled_agent_context.yaml
- docs/governance/FINAL_SUMMARY_CONTRACT.md
- docs/governance/CHAT_COMMUNICATION_CONTRACT.md
- docs/governance/PORTABLE_CHAT_EXECUTION_CONTRACT.md
- docs/governance/CHAT_BOOTSTRAP_AND_DRIFT_CONTRACT.md
- docs/TEST_GATES.md
- docs/STATUS.md
- docs/handoff/CURRENT_HANDOFF.md
- .agentic/handoff_state.yaml
- AGENTS.md
- CHANGELOG.md
- README.md
- CITATION.cff
- docs/releases/VERIFIED_RELEASES.md
- relevant source files and tests for the requested slice
stable_test_anchors:
- "direct-fetch that path before relying on search results"
- "do not use interactive read prompts or shell-backslash summary invocations"
- "GitHub connector direct-path-first workflow"
- "parse-modify-dump is the only allowed governance YAML mutation workflow"
- "Information preservation outranks compactness"
hard_rules:
- id: remote-first-no-guess
  rule: Inspect remote repo files, authoritative docs, and command help before acting.
- id: no-long-manual-command-blocks
  rule: Queue repo-backed commands or use portable Python core commands instead of returning long local shell blocks.
- id: final-summary-contract
  summary: Preserve the framed SUMMARY contract in every final block.
  rule: Use the mandatory SUMMARY block and never relabel inner failures as PASS.
- id: chat-communication-contract
  rule: Interpret d/f/w/paste-output/stop as communication signals only; verify outcomes from evidence before continuing.
- id: portable-chat-execution-contract
  rule: Canonical workflow correctness must be Python-core-first and operating-system independent; shell is an adapter only.
- id: chat-bootstrap-and-drift-contract
  rule: Successor chats must read mandatory sources first, detect drift, warn, and avoid mutation except for drift fixes.
- id: successor-handoff-freshness-guard
  rule: Before presenting a successor handoff prompt as authoritative, run the freshness guard against STATUS, handoff_state, CURRENT_HANDOFF, and the latest successor prompt.
- id: documentation-registry-first-slice
  summary: Classify documentation and artifacts through an additive, reversible registry before broad migration.
  rule: Documentation registry changes must keep the first slice structural, test-backed, and non-destructive; broad migration, deletion, or taxonomy-driven rewrites require later explicit slices.
- id: patch-artifact-preflight
  rule: Generated patch artifacts must pass syntax, YAML, coverage-term, and final-summary checks before use.
- id: rules-must-be-test-backed
  rule: Durable rules require human docs, compiled YAML, and deterministic tests or a documented review-only exception.
- id: remote-log-direct-path-first
  rule: If a concrete docs/reports/terminal log path is known, direct-fetch that path before relying on search results or declaring evidence missing.
- id: github-connector-direct-path-first
  rule: For remote repo work, first use the installed GitHub connector with repository_full_name and fetch_file/fetch_commit/get_pr_info/fetch_commit_workflow_runs/compare_commits before trying raw URLs, search, or local shell fallbacks.
- id: yaml-governance-parse-modify-dump-only
  rule: parse-modify-dump is the only allowed governance YAML mutation workflow; never patch YAML with free-text injection, regex insertion, or unparsed string concatenation.
- id: control-file-preservation
  summary: Preserve critical control-file information; compactness must not delete active rules.
  rule: Critical control files must be additive or use explicit migration records with successor anchors, rationale, and deterministic tests. Hard length-limit trimming is forbidden; if files grow too large, split, reference, or generate them.
- id: gui-visual-two-phase-evidence
  rule: GUI visual checks must separate manual window launch from non-interactive PASS/FAIL evidence recording; do not use interactive read prompts or shell-backslash summary invocations.
- id: local-main-freshness-before-local-work
  rule: Before local repository mutation, fetch the remote, verify the intended local base equals its remote upstream, preserve or stop on dirty state, and only then create the feature branch.
final_summary_contract:
  work_values:
  - PASS
  - FAIL
  - PENDING
  - HARD-FAIL
  - NO-COMMAND
  evidence_values:
  - PASS
  - FAIL
  - PARTIAL
  - CHAT_ONLY
  - NOT_REQUIRED
  overall_values:
  - PASS
  - FAIL
  - PENDING
  - HARD-FAIL
  - NO-COMMAND
  remote_evidence_values:
  - PASS
  - FAIL
  - PARTIAL
  - NOT_REQUIRED
  forbidden_remote_evidence_values:
  - PENDING
  - NONE
  - CHAT_ONLY
communication_rules:
  d: local block appears finished; inspect evidence before treating as success
  f: failure reported; inspect or upload evidence before asking for pasted output
  w: continue within current governance and evidence rules
  paste-output: manual paste only when repo-backed or local evidence is unavailable or unusable
  stop: no further mutation or terminal instructions
portable_execution_rules:
  canonical_core: Python modules and CLI commands
  shell_role: adapter only
  python_apis:
  - pathlib.Path
  - shutil
  - platform
  - subprocess.run with shell=False
  forbidden_canonical_dependencies:
  - cp
  - tail
  - grep
  - sed
  - head
  - tee
  - find
  - sh
  - hard-coded Unix tool paths
  - shell pipelines for correctness
drift_detection:
  fail_closed: true
  on_drift:
  - warn
  - identify affected sources
  - avoid mutation unless fixing drift
  - offer comprehensive handoff prompt when continuation is unsafe
  drift_classes:
  - contract-vs-renderer value drift
  - contract-vs-test drift
  - missing mandatory bootstrap source
  - stale status or handoff state
  - stale successor handoff prompt after newer main merge
  - forbidden final summary value
  - no-copy claim without remote-readable evidence
  - shell-only canonical workflow example
  - local work starts from stale or dirty repository state
  - remote work ignores the GitHub connector direct-path-first workflow
  - governance YAML is mutated without parse-modify-dump validation
  - protected control file loses an active rule without an explicit successor migration
normal_operator_path:
- use GitHub connector direct-path-first workflow for remote repo inspection
- verify local repository freshness before local mutation
- read mandatory successor chat sources
- inspect current remote state
- run handoff prompt freshness guard before presenting a successor prompt
- run or inspect deterministic checks
- mutate governance YAML only through parse-modify-dump helpers and validate parseability afterward
- preserve protected control-file anchors or record explicit successor migrations
- use portable Python core where available
- render final summary through canonical renderer
quality_goal: Prefer deterministic, portable, test-backed solutions over prompt-only conventions.
workflow_friction_rules:
- id: no-remote-command-deadlock
  priority: high
  rule: Remote command first is preferred, but NO-COMMAND must trigger queuing a complete command pair or exactly one minimal fallback command. Do not loop on ask-agent-to-queue-command.
- id: final-summary-no-executable-placeholders
  summary: Executable terminal blocks must print only concrete final SUMMARY outcomes; never placeholder alternatives like PASS|FAIL or p|paste-output.
```

### `.agentic/handoff_state.yaml`

```text
schema_version: 1
updated:
  date: '2026-05-29'
  reason: Refresh handoff state to last substantive work commit
  source: agentic-kit handoff refresh
repo:
  name: agentic-project-kit
  local_path: agentic-project-kit
  remote: github.com:vfi64/agentic-project-kit
  default_branch: main
safe_state:
  branch: main
  commit: e1cac6c
  commit_subject: Integrate GUI gatekeeper into Tkinter shell (#911)
  semantics: current_main_head
  working_tree_expected_clean: true
  administrative_refresh_prs:
  - 656
  - 657
  - 659
  - 660
  - 661
  - 663
  - 665
  - 666
  - 671
  - 672
  - 680
  - 681
  - 688
  - 689
  - 690
  - 691
  - 694
  - 702
  - 705
  - 707
  - 708
  - 710
  - 715
  - 716
  - 718
  - 719
  - 720
  - 721
  - 722
  - 723
  - 724
  - 725
  - 726
  - 727
  - 728
  - 729
  - 730
  - 731
  - 732
  - 733
  - 734
  - 735
  - 736
  - 737
  - 738
  - 739
  - 740
  - 741
  - 742
  - 761
  - 762
  - 763
  - 764
  - 766
  - 831
  - 833
  - 835
  - 836
  - 837
  - 838
  - 878
  - 879
  - 880
  - 881
  - 883
  - 886
  - 888
  - 892
  - 894
  - 897
release:
  current_version: 0.4.4
  previous_version: 0.4.3
  tag: v0.4.4
  github_release_exists: true
  zenodo_concept_doi: 10.5281/zenodo.20101359
  zenodo_version_doi: 10.5281/zenodo.20431326
  post_release_check: PASS
  post_release_evidence: docs/reports/terminal/v044-post-release-verify.log
open_items:
  prs: []
  next_expected_chat_action: Continue after PR892 with post-merge gate visibility
    follow-up work only after the post-merge refresh status gate reports NOOP.
completed_since_previous_handoff:
- 'PR #897 merged standard summary validator hardening before this administrative
  handoff refresh.'
- 'PR #894 merged post-merge gate bootstrap visibility documentation before this administrative
  handoff refresh.'
- 'PR #892 recorded the post-merge handoff refresh status gate visibility inventory
  so the workflow can move the gate into more visible kit/ns paths.'
- 'PR #888 added optional patch-preflight slice-gate enforcement so planning-document
  preflight can require deterministic slice readiness and a clean worktree.'
- 'PR #886 fixed workflow evidence hygiene by moving active next-turn/work-order results
  out of the repo-backed fixed slot until explicit upload/promotion.'
- 'PR #883 added the GUI gatekeeper implementation inventory and recorded that helper-local
  PASS is not slice PASS without matching repository governance gates.'
- 'PR #881 refreshed bootstrap/handoff state after PR #880; this post-PR881 refresh
  records the resulting custom-subject administrative merge commit as current main.'
- 'PR #880 accepted bounded administrative merge chains in the handoff freshness guard
  while preserving blocking behavior for product merges inside such chains.'
- 'PR #877 fixed the handoff freshness self-reference loop by checking freshly rendered
  prompt text before warning.'
- 'PR #876 recorded v0.4.4 DOI metadata and post-release evidence at docs/reports/terminal/v044-post-release-verify.log.'
- 'PR #875 prepared v0.4.4 release metadata, after which v0.4.4 was tagged and post-release
  verified with Zenodo version DOI 10.5281/zenodo.20431326.'
- 'PR #874 records the GUI deterministic gatekeeper migration plan in docs/planning/GUI_DETERMINISTIC_GATEKEEPER_PLAN.md
  as planning-only work.'
- 'PR #873 added the GUI work order upload strip and was verified by docs/reports/terminal/pr873-final-main-closeout.log.'
- 'PR #838 refreshed post-PR837 administrative handoff state and preserved the last
  substantive safe-state distinction.'
- 'PR #837 recorded the post-PR836 successor handoff prompt and evidence anchor.'
- 'PR #838 refreshed post-PR837 administrative handoff state and preserved the last
  substantive safe-state distinction.'
- 'PR #837 recorded the post-PR836 successor handoff prompt and evidence anchor.'
- 'PR #836 refreshed post-PR835 next-step state and is the current successor-handoff
  safe-state anchor.'
- 'PR #835 recorded PR #834 closeout evidence at docs/reports/terminal/pr834-merge-finalize.log
  and added docs/reports/terminal/post-pr834-successor-handoff.md as the successor
  anchor.'
- 'PR #834 repaired generator-backed handoff freshness state so the generated successor
  prompt anchors to the post-PR834 safe state.'
- 'PR #833 recorded the corrected post-PR831 successor handoff at docs/reports/terminal/post-pr831-successor-handoff.md
  and superseded the rejected PR825-era stale generated prompt.'
- 'PR #831 recorded PR #830 closeout evidence at docs/reports/terminal/pr830-merge-finalize.log
  and verified main 011b6dc24829be44c7693c468a90694981cd40ce for the successor handoff
  anchor.'
- 'PR #825 hardened active handoff freshness checks: state-freshness-check now fails
  active next-step instructions that point to already-recorded closeout evidence or
  stale release versions.'
- 'PR #824 recorded PR #823 closeout evidence at docs/reports/terminal/pr823-merge-finalize.log
  and refreshed STATUS, CURRENT_HANDOFF, and persistent handoff state.'
- 'PR #823 hardened merge-if-green head/base pinning: the command validates the target
  base branch, requires a PR head SHA, passes --match-head-commit to GitHub, and renders
  checked base/head refs in the command output.'
- 'PR #821 hardened merge-if-green postconditions: after a successful merge, the command
  verifies the merge commit on main, waits for main CI, and fails the command result
  unless main CI is green.'
- 'PR #819 hardened next-turn PR status failed-log diagnostics: red CI now exposes
  failed check names, GitHub Actions run ids, exact gh run view --log-failed commands,
  bounded log-fetch status, and no-checks classification for empty rollups.'
- 'PR #817 hardened PASS_ALREADY_DONE target-state classification: generic already-exists
  output is no longer sufficient success evidence; target-specific classes and hard-failure
  precedence are test-backed.'
- 'PR #815 hardened release-prep atomicity and remote release readiness: release-prep
  stops before metadata patching on main/branch failures; release-check and release-preflight
  block release readiness on remote WARN; release-publish blocks inconclusive remote
  lookups before tagging.'
- 'PR #813 published v0.4.3 and post-release verification found Zenodo version DOI
  10.5281/zenodo.20393329; evidence: docs/reports/terminal/20260526-120216_v043-release-verify.log.'
- 'PR #791 merged Protected Change Planner A1 and verified it via docs/reports/terminal/protected-change-planner-a1-merge-verify.log.'
- 'PR #763 refreshed status and handoff after the PR762 direct-coverage closeout.'
- 'PR #764 added explicit rule-registry direct coverage completion reporting for JSON
  and human CLI reports.'
- 'PR #766 recorded the accepted rule-registry improvement backlog before the v0.4.2
  safety release.'
current_capabilities:
  ns_actions:
  - agent-next
  - agent-run
  - command-inbox-check
  - state-freshness-check
  - terminal-remote-preflight
  - terminal-finalize
  - handoff-show
  - handoff-check
  - governance-check
  - rule-registry check
  - rule-registry report
  - patch-preflight
  - dev
  artifact_dirs:
    terminal_logs: docs/reports/terminal
    command_runs: docs/reports/command_runs
  rule_preservation:
    registry: .agentic/rule_preservation.yaml
    guard: src/agentic_project_kit/rule_preservation.py
    workflow_guard_pattern: rule-preservation-drift
    status: baseline-active
  documentation_registry:
    registry: docs/DOCUMENTATION_REGISTRY.yaml
    contract: docs/governance/DOCUMENTATION_REGISTRY_CONTRACT.md
    cli_summary: agentic-kit docs-registry
    cli_report: agentic-kit docs-registry --report PATH
    artifact_policy_source: .agentic/communication_artifacts.yaml
    broad_migration_allowed: false
  governed_rule_registry:
    mechanism_inventory: .agentic/rule_mechanism_inventory.yaml
    migration_map: .agentic/rule_migrations.yaml
    test_coverage: .agentic/rule_test_coverage.yaml
    direct_test_plan: .agentic/rule_direct_test_plan.yaml
    validator: src/agentic_project_kit/rule_registry_validator.py
    cli: agentic-kit rule-registry check
    report_cli: agentic-kit rule-registry report
    report_completion_field: summary.direct_coverage_complete
    workflow_guard_pattern: rule-registry-drift
    patch_preflight: true
    status: completion-reporting-closed
    mechanisms:
    - summary-renderer
    - execution-mode-switch
    - rule-preservation-guard
    - workflow-guard
    - patch-preflight
    - chat-communication-rules
    - chat-bootstrap-drift-rules
    - portable-execution-rules
    - evidence-guard
    - typed-work-order-runner
    - release-state-validation
    - post-release-archive-check
    required_fields:
    - category
    - priority
    - enforcement_phase
    - owner
    - conflict_domains
    - surfaces
    - tests
    compatibility_checks:
    - category/enforcement_phase matrix
    - ambiguous category/priority/enforcement_phase rejection
    completeness_checks:
    - known_legacy_rule_ids index
    - migration entry for every known legacy rule
    - every migration entry indexed
    - migrated/archived/rejected disposition statuses
    coverage_checks:
    - test coverage classification for every active mechanism
    - direct-test path validation
    - empty direct-test follow-up plan after PR762
    reporting_checks:
    - explicit JSON direct_coverage_complete field after PR764
    - explicit human completion_status line after PR764
  workflow_hardening:
    remote_route_rule: GitHub connector direct-path-first for known paths, refs, PRs,
      and commits.
    yaml_mutation_rule: Use structured YAML mutation and parse validation.
    control_file_preservation: .agentic/control_file_preservation.yaml protects active
      rules from lossy shortening.
  gui_mvp:
    status: closed_out_on_main
    verified_read_only_actions:
    - cockpit-readiness
    - doctor
    - check-docs
    disabled_actions:
    - agent-run
    - remote_mutation
    - destructive_actions
policies:
  no_copy_terminal_policy: .agentic/no_copy_terminal_policy.yaml
  control_file_preservation: .agentic/control_file_preservation.yaml
rules:
- id: remote-first-no-guess
  status: active
  text: Do not guess repository state, command syntax, file locations, release phase,
    GitHub JSON fields, or available evidence. Inspect the remote repository, command
    help, known paths, PRs, commits, logs, and authoritative repo files before acting.
- id: quality-first-no-shortcuts
  status: active
  text: Prefer deterministic, test-backed, maintainable fixes over quick patches.
    No shortcuts, workaround-only fixes, or chat-only promises for recurring workflow
    defects.
- id: patch-artifact-preflight-before-application
  status: active
  text: Before applying generated patch artifacts, run patch-artifact preflight diagnostics
    and fail on unsafe quoting, ambiguous YAML terms, or control-file weakening.
- id: generated-code-syntax-first
  status: active
  text: Generated shell and Python artifacts must be syntax-checked before execution
    or commit; generated code cannot be trusted because it looks plausible.
- id: coverage-yaml-terms-must-be-strings
  status: active
  text: Coverage YAML required terms must stay strings; colon-containing terms must
    be quoted or written through structured YAML writers.
- id: final-summary-self-validation
  status: active
  text: Final summaries must be self-validated against preceding output before treating
    a block as successful.
- id: no-copy-terminal-evidence
  status: active
  text: Routine PASS and normal FAIL handoffs must be backed by repo evidence; use
    d for log-backed PASS and f for log-backed FAIL. Manual terminal paste is only
    for hard failure, broken logging, unavailable evidence, unusable evidence, or
    explicit user request.
- id: remote-log-lookup-first
  status: active
  text: Remote evidence must be inspected first for FAIL or uncertain handoffs; direct-fetch
    docs/reports/terminal logs before asking for paste-output unless logging is broken
    or unavailable. The phrase remote evidence is intentionally preserved for rule-preservation
    coverage.
- id: rules-must-be-test-backed
  status: active
  text: Durable workflow rules need a stable repository home, documentation, and deterministic
    tests or guards that fail when the rule disappears or is weakened.
- id: yaml-structured-mutation-only
  status: active
  text: YAML governance files must be changed through parse-modify-dump or equivalent
    structured mutation, then parsed again before gates.
- id: github-connector-direct-path-first
  status: active
  text: For remote GitHub work with known paths, refs, or commits, use direct fetch,
    update, and PR APIs before search.
- id: control-file-preservation
  status: active
  text: Protected control files must preserve active rules and required anchors. Information
    preservation outranks compactness; hard length-limit trimming is forbidden.
- id: structured-summary-must-be-enforced
  status: active
  text: Relevant local or remote work blocks must end with the canonical structured
    SUMMARY from FINAL_SUMMARY_CONTRACT.md. Missing, malformed, contradictory, or
    legacy summaries are workflow drift.
- id: governed-rule-registry-before-documentation-rebuild
  status: active
  text: A governed modular rule registry must become the canonical source of truth
    before documentation-management rebuild work resumes.
recent_failure_patterns:
- id: guessing-before-inspection
  prevention: Before choosing commands, paths, JSON fields, release checks, or DOI
    sources, inspect the remote repository and command help. Treat memory and chat
    summaries as hypotheses until verified.
- id: interpreter-discovery-before-python
  prevention: Discover the active interpreter and project environment before invoking
    python, python3, pytest, ruff, or agentic-kit; prefer .venv/bin/python when the
    project venv exists; avoid naked python; when wrapping shell commands, avoid assuming
    set -e behavior unless explicitly set and logged.
- id: global-cli-or-venv-assumption
  prevention: Do not assume global CLIs or an existing venv; use project-local discovery
    and documented bootstrap paths.
- id: nested-triple-quote-code-generator
  prevention: Avoid nested quote-based code generation, nested shell/Python quote
    layers, nested triple-quoted string literals, and nested triple quotes in generated
    patch scripts; prefer line-list generation, existing helper scripts, simple file
    writes, or structured update APIs.
- id: yaml-colon-term-reinterpreted-as-mapping
  prevention: Quote colon-containing YAML terms or use structured YAML writers so
    plain scalars are not reinterpreted as mappings.
- id: standard-error-guards
  prevention: Recurring workflow errors must become deterministic guards, tests, or
    documented failure patterns.
- id: interactive-terminal-exit
  prevention: Chat-pasted terminal blocks must not end by closing the user terminal;
    avoid top-level exit and exec unless explicitly requested.
- id: stale-successor-handoff-prompt-after-main-merge
  prevention: Refresh STATUS, handoff_state, CURRENT_HANDOFF, and successor prompt
    before treating handoff prose as authoritative.
- id: repeated-yaml-governance-file-corruption
  prevention: Parse YAML before and after mutation and use a structured writer.
- id: final-pass-after-inner-fail
  prevention: Final summaries must distinguish work result from evidence result; evidence
    upload must not relabel failed work as PASS.
- id: lossy-control-file-shortening
  prevention: Do not shorten protected control files by deleting active rules; use
    successors, generated projections, or split/reference patterns.
- id: structured-summary-drift
  prevention: Verify canonical SUMMARY fields and consistency across WORK, EVIDENCE,
    OVERALL, REMOTE_EVIDENCE, terminal_log, command_report, CHAT_REPLY, and RESULT
    marker.
next_allowed_tasks:
- id: tkinter-workbench-gui-slice-1
  title: Continue with the smallest Tkinter workbench GUI slice from docs/planning/TKINTER_WORKBENCH_GUI_PLAN.md
    after PR834 closeout evidence is inspected.
  priority: 1
- id: failure-mode-review-automation-slice-1
  title: Continue with the smallest failure-mode review automation slice from docs/planning/FAILURE_MODE_REVIEW_AUTOMATION_PLAN.md
    after PR834 closeout evidence is inspected.
  priority: 2
- id: release-evidence-kernel-hardening-follow-up
  title: Use only a small release/evidence-kernel hardening follow-up if freshness
    or evidence drift reappears.
  priority: 3
blocked_until_closeout:
- Remote/destructive GUI actions
- Large GUI architecture expansion before successor-chat bootstrap
- Broad documentation migration during release/evidence-kernel hardening closeouts
- Release, tag, or DOI mutation
- GUI product work before post-PR880 bootstrap refresh is merged and verified
- Broad GUI implementation before the deterministic gatekeeper read-only inspection
  slice
- Gatekeeper product work before post-PR883 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS before repository governance gates pass
- Gatekeeper product work before post-PR886 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS without slice-gate evidence
- Gatekeeper product work before post-PR888 handoff refresh is merged and verified
- Treating helper-local PASS as slice PASS without patch-preflight slice-gate evidence
first_instruction: Start the next chat from the fresh post-PR911 successor handoff
  prompt and obey agentic-kit handoff post-merge-refresh-status before product work.
handoff_maintenance:
  principle: curated-not-accumulated
  update_required_at_chat_end: true
  no_redundant_rules: true
  no_contradictory_rules: true
  remove_obsolete_rules_when_system_changes: true
  latest_successor_prompt: docs/reports/terminal/v044-successor-chat-handoff-after-pr911.md
# preservation-anchor: use d for log-backed PASS and f for log-backed FAIL
# preservation-anchor: nested shell/Python quote layers
```
