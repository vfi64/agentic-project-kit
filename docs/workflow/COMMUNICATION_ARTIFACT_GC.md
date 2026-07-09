Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Communication Artifact Garbage Collector

## Purpose

Communication, handoff, terminal, and command-run artifacts must not accumulate without classification. They also must not be removed by ad-hoc shell deletion. The project therefore uses a central artifact registry in `.agentic/communication_artifacts.yaml` and a deterministic garbage-collector workflow.

## Quality rule

The goal is deterministic technical quality, not quick cleanup. A cleanup that risks deleting pending commands, evidence, handoff state, terminal logs, or pointers is a product defect.

## Required behavior

- classify artifacts before deletion;
- default to dry-run for cleanup candidates;
- keep repo-backed evidence unless a specific retention rule says otherwise;
- never delete `.agentic/commands/inbox/*` as generic temporary files;
- never delete `docs/reports/terminal/LATEST_TERMINAL_LOG.txt`; repair it if needed;
- delete only allowlisted local temporary files or proven-stale transient runner state;
- write a cleanup report before any mutating cleanup;
- use PASS, FAIL, or PENDING result markers.

## Current compatibility targets

The registry covers the existing temporary and communication artifact classes currently used by the repository: `/tmp/agentic-project-kit-*.log`, `docs/reports/terminal/*.log`, generated successor-handoff Markdown snapshots under `docs/reports/terminal/`, `docs/reports/terminal/LATEST_TERMINAL_LOG.txt`, `docs/reports/command_runs/*.md`, `.agentic/commands/inbox/*`, and `.agentic/commands/current.*`.


## Implemented hardening status

The current implementation hardens the communication artifact GC in bounded steps:

- `.agentic/commands/current.yaml` and `.agentic/commands/current.sh` are treated as transient runner compatibility files.
- Symlinked transient artifacts are rejected with `FAIL_SYMLINK_ARTIFACT` and are never followed or deleted.
- Repo-backed terminal logs under `docs/reports/terminal/*.log` are protected evidence.
- Generated successor-handoff Markdown snapshots under `docs/reports/terminal/` may be collected only by the report-retention route after TTL, newest-file, keep-name, and active-reference checks.
- `docs/reports/terminal/LATEST_TERMINAL_LOG.txt` is a protected pointer and must not be collected.
- Command-run reports under `docs/reports/command_runs/*.md` are protected evidence.
- Command inbox files under `.agentic/commands/inbox/*` are protected pending or consumable commands and are never generic temporary files.
- Local `/tmp/agentic-project-kit-*.log` files remain the OS-level tmp-log class handled by the GC.
- Repository-local `tmp/` cleanup is local-only: `agentic-kit artifact-gc --local-tmp-contents`
  may collect old untracked files and empty directories under repo `tmp/`, but it never
  performs remote cleanup, report retention, or git push.
- `agentic-kit artifact-gc --tmp-logs` performs a dry-run for expired local tmp logs and reports `PENDING_EXPIRED_TMP_LOGS` without deleting.
- `agentic-kit artifact-gc --tmp-logs --execute` may delete only expired, non-symlink `/tmp/agentic-project-kit-*.log` files directly under `/tmp`.
- The GC must stay conservative: unknown files, repo evidence, command inbox files, symlinks, and files outside allowlisted zones are not collected.

## Current safe commands

```bash
agentic-kit artifact-gc
agentic-kit artifact-gc --execute
agentic-kit artifact-gc --tmp-logs
agentic-kit artifact-gc --tmp-logs --execute
agentic-kit artifact-gc --local-tmp-contents
agentic-kit artifact-gc --local-tmp-contents --execute
agentic-kit artifact-gc --transfer-runs
agentic-kit artifact-gc --report-retention
```

Use dry-run forms first. Mutating forms are bounded to explicitly implemented artifact classes and must be covered by terminal evidence for relevant workflow blocks.

## Local run garbage collector preflight

Every local `agentic-kit transfer normalize-session` run invokes the deterministic local
garbage collector preflight before productive transfer follow-up work.

The local command-stack identity is managed by an OS-independent Python state
file, not by shell-specific environment variables. A local command stack begins
with `agentic-kit transfer command-stack-begin` and ends with
`agentic-kit transfer command-stack-end`. `normalize-session` reads that repo-local
state and passes the command-stack id to the local garbage collector.

Subsequent `normalize-session` calls in the same local command stack report
`skipped: true` with `skip_reason: already_ran_for_command_stack`. This keeps the
standard `normalize-session -> rules acknowledge -> normalize-session`
Pflichtstart deterministic without producing repeated cleanup work. If no active
command-stack state exists, `normalize-session` creates an implicit stack state
inside the kit, still without relying on OS-specific shell features.

The preflight may automatically delete only allowlisted local runtime artefacts:
- files below `tmp/`,
- allowlisted suffixes such as `.log`, `.tmp`, `.out`, `.err`, `.py`, `.md`, `.diff`, `.json`, `.sh`, `.txt`,
- empty old directories below `tmp/`,
- files and directories older than the configured retention window,
- files that are not tracked by Git.

The preflight must not delete:
- tracked files,
- protected/governance/handoff/status/planning/YAML files,
- active transfer files,
- failed workflow evidence,
- `tmp/agent-evidence/` workflow evidence,
- `tmp/local-gc-last.json`,
- `tmp/local-gc-last-run-id.txt`,
- `tmp/local-command-stack-state.json`.

Transfer-file lifecycle cleanup remains the responsibility of
`agentic-kit transfer normalize-files`. Workflow evidence cleanup remains the
responsibility of `agentic-kit workflow cleanup`.

## 24-hour retention policy for local and transfer-run logs

Status: ACTIVE AUTHORITY.

`agentic-kit artifact-gc` is dry-run by default. Destructive cleanup requires
explicit `--execute`.

Retention policy:

- `artifact-gc --tmp-logs --local-tmp` may collect local `tmp/*slice*.log`,
  `tmp/*handoff*.log`, `tmp/*release*.log`, and `tmp/*gc*.log` files older than
  24 hours while keeping the newest slice logs and protecting current GC,
  command-stack, and next-turn fixed-slot files.
- `artifact-gc --local-tmp-contents` may collect old untracked files of any
  file type and old empty directories under repository-local `tmp/`. It skips
  tracked files, symlinks, reserved local state files, and `tmp/agent-evidence/`.
  It is local-only and must not be used for remote report retention.
- `artifact-gc --transfer-runs` may collect
  `docs/reports/transfer_runs` files older than 24 hours except these fixed
  latest files:
  - `latest-transfer-report.log`
  - `latest-transfer-report.json`
  - `latest-remote-next-report.log`
  - `latest-remote-next-report.json`
- `artifact-gc --report-retention` may collect expired `.log` and `.json`
  report-retention files under governed report surfaces when they are not
  referenced by active non-report documents. It may also collect generated
  successor-handoff Markdown snapshots under `docs/reports/terminal/` that match
  the explicit post-PR/versioned handoff filename patterns. It must not collect
  generic Markdown reports such as command-run reports, audits, plans, or
  semantic closeout notes.
- GC must not delete current handoff files, latest handoff package manifests, or
  files referenced by the latest handoff/source manifest.
- GC must not delete protected governance/status/handoff files.
- GC must not treat broad documentation cleanup as log retention. Review,
  planning, roadmap, strategy, and workflow cleanup require separate
  protected-diff planning.
