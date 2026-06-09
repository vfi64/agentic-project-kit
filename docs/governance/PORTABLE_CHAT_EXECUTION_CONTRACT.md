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

`./ns` may expose shortcuts for local convenience, but it must not be the only canonical route. A chat or workflow must use a wrapper only when the wrapper contract is clear for the concrete task from repository documentation, command help, or existing evidence. If the wrapper is ambiguous, unavailable, or narrower than the requested workflow, use the explicit project-local Python entry point such as `./.venv/bin/python -m agentic_project_kit.cli ...` or the documented Python module path instead of guessing a wrapper subcommand.

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

<!-- agentic-kit:command-reference-lifecycle-discipline:start -->
## Non-optional command-reference and lifecycle discipline

This section is normative for successor-chat handoff, transfer-file workflows, and local execution guidance.

### Command Reference is the source of truth

A chat must not reconstruct `agentic-kit` or `agentic-kit transfer` commands from memory, prior examples, or guessed parameter names.

Before writing a transfer file, giving a copy/paste command, or choosing a local execution path, the chat must treat these files as required sources of truth:

- `docs/reference/AGENTIC_KIT_COMMANDS.md`
- `docs/reference/agentic-kit-commands.json`

If a command or option is unclear, the chat must inspect the Command Reference or run the corresponding `--help` locally through an appropriate repo-backed transfer. Guessing command options is a process error.

### Wrapper-first rule

When planning local control, the chat must prefer existing complex `agentic-kit` wrappers over hand-built shell sequences.

Priority order:

1. Existing `agentic-kit` or `agentic-kit transfer` wrapper.
2. Canonical transfer file that invokes the wrapper.
3. Copy/paste shell sequence only when no suitable wrapper exists or the wrapper is proven blocked.

### Canonical PR lifecycle

After a checked patch, do not manually merge as the primary path.

For a new PR, use:

    ./.venv/bin/agentic-kit transfer pr-create-complete --title "<PR title>" --body "<PR body>" --base main --head current --merge-method squash

For an existing PR, use:

    ./.venv/bin/agentic-kit transfer pr-complete <PR_NUMBER> --expected-head-sha current --merge-method squash

If `current` is not accepted or if the branch has to be pinned explicitly, resolve the exact head SHA with `git rev-parse HEAD` and pass that SHA. Do not guess unsupported options.

### Canonical post-merge closeout and remote report

After a successful merge, the required closeout is:

    ./.venv/bin/agentic-kit transfer sync-main
    ./.venv/bin/agentic-kit transfer post-merge-complete --after-pr <PR_NUMBER>
    ./.venv/bin/agentic-kit transfer sync-main
    ./.venv/bin/agentic-kit transfer post-merge-check
    ./.venv/bin/agentic-kit transfer repo-status

`post-merge-complete --after-pr <PR_NUMBER>` is the canonical wrapper that creates post-merge evidence and publishes the transfer report into the remote repository.

`run-and-log` is useful for diagnostics and fallback evidence, but it is not a substitute for `post-merge-complete` after a merge.

### Volatile transfer-output hygiene

Before branch switches, PR completion, or merge-safe operations, known volatile transfer outputs must not be allowed to block the lifecycle.

At minimum, clean these local-only volatile paths when they are dirty and not the target of the current slice:

    git restore -- .agentic/transfer/outbox/last_result.txt
    git restore -- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.json
    git restore -- docs/reports/terminal/transfer_handoff_reports/latest-transfer-handoff-report.log

This cleanup is a workaround for volatile report files. It must not be used to discard substantive source, governance, planning, or handoff changes.
<!-- agentic-kit:command-reference-lifecycle-discipline:end -->

