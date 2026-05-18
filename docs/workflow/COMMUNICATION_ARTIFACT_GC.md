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
