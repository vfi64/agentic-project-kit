# Portable Chat Execution Contract

Status-date: 2026-05-24
Status: normative governance contract
Scope: operating-system-independent execution rules for chat-assisted workflows

## Purpose

The kit must work across macOS, Linux, and Windows assumptions. Canonical workflow correctness must not depend on POSIX-only shell utilities, a healthy inherited `PATH`, or long copy-pasted shell scripts.

The observed failure mode was simple and severe: a generated block could not find `git`, `cp`, `tail`, or `sh`. A governance system that cannot preserve evidence when the shell environment is degraded is not robust enough for large-LLM operation.

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
