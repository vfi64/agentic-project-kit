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

The registry covers the existing temporary and communication artifact classes currently used by the repository: `/tmp/agentic-project-kit-*.log`, `docs/reports/terminal/*.log`, `docs/reports/terminal/LATEST_TERMINAL_LOG.txt`, `docs/reports/command_runs/*.md`, `.agentic/commands/inbox/*`, and `.agentic/commands/current.*`.


## Implemented hardening status

The current implementation hardens the communication artifact GC in bounded steps:

- `.agentic/commands/current.yaml` and `.agentic/commands/current.sh` are treated as transient runner compatibility files.
- Symlinked transient artifacts are rejected with `FAIL_SYMLINK_ARTIFACT` and are never followed or deleted.
- Repo-backed terminal logs under `docs/reports/terminal/*.log` are protected evidence.
- `docs/reports/terminal/LATEST_TERMINAL_LOG.txt` is a protected pointer and must not be collected.
- Command-run reports under `docs/reports/command_runs/*.md` are protected evidence.
- Command inbox files under `.agentic/commands/inbox/*` are protected pending or consumable commands and are never generic temporary files.
- Local `/tmp/agentic-project-kit-*.log` files are the only TTL-based local tmp-log class currently handled by the GC.
- `./ns artifact-gc --tmp-logs` performs a dry-run for expired local tmp logs and reports `PENDING_EXPIRED_TMP_LOGS` without deleting.
- `./ns artifact-gc --tmp-logs --execute` may delete only expired, non-symlink `/tmp/agentic-project-kit-*.log` files directly under `/tmp`.
- The GC must stay conservative: unknown files, repo evidence, command inbox files, symlinks, and files outside allowlisted zones are not collected.

## Current safe commands

```bash
./ns artifact-gc
./ns artifact-gc --execute
./ns artifact-gc --tmp-logs
./ns artifact-gc --tmp-logs --execute
```

Use dry-run forms first. Mutating forms are bounded to explicitly implemented artifact classes and must be covered by terminal evidence for relevant workflow blocks.
