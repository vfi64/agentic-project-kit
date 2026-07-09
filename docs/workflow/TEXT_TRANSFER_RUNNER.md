Status: active
Status-date: 2026-07-09
Superseded-by: n/a

# Text Transfer Runner

Status: Active MVP

## Purpose

The text transfer runner is the preferred local execution bridge for ChatGPT-to-repo work when the ChatGPT GitHub connector can write text artifacts but executable remote payloads are unsafe or unreliable.

The runner keeps responsibility split clearly:

- ChatGPT writes data artifacts only: YAML transfer orders and `.txt` payloads.
- Local execution happens only through `agentic-kit transfer inspect` and `agentic-kit transfer apply`.
- The runner validates paths, payload hashes, and report locations before applying changes.
- The runner writes repo-backed evidence under `docs/reports/command_runs/`.

This prevents the assistant from falling back to ad-hoc terminal snippets as the normal path.

## Commands

```bash
agentic-kit transfer status
agentic-kit transfer inspect
agentic-kit transfer apply
```

## Input layout

```text
.agentic/transfer/inbox/current.yaml
.agentic/transfer/payloads/*.txt
```

## MVP action

```yaml
actions:
  - type: write_text_file
    target_path: src/agentic_project_kit/example.py
    payload_path: .agentic/transfer/payloads/example.py.txt
    sha256: <payload sha256>
```

The MVP supports `write_text_file` only.

## Safety boundaries

The runner must reject:

- absolute paths,
- parent traversal,
- `.git`,
- `.venv`,
- `venv`,
- `__pycache__`,
- report paths outside `docs/reports/command_runs/`,
- payload hash mismatches.

## Evidence contract

Every `apply` writes:

```text
docs/reports/command_runs/<transfer-id>.md
docs/reports/command_runs/LATEST_COMMAND_RUN.txt
```

The user may answer with `d` or `f` after local execution. The assistant must read the repo-backed evidence before claiming success or planning recovery.

## GUI contract

The GUI must treat the runner as the normal execution path for local file-writing work:

1. Show the transfer state.
2. Require inspect before apply.
3. Derive buttons from deterministic state/capabilities.
4. Show the last evidence report.
5. Warn visibly that free terminal shortcuts are not the normal path.

The GUI is not the safety anchor. The safety anchors remain `agentic-kit`, path validation, hash validation, tests, Git, PR CI, protected-change planning, and repo-backed evidence.

## Secure remote connector Branch/PR/Merge path

When the ChatGPT GitHub connector is available, it may be used to create or update UTF-8 text files in the repository, but the safe repository mutation path is still governed by `agentic-kit` wrappers. Raw `git`/`gh` commands are not the normal operator interface for this path.

Required route for connector-backed repository updates:

1. Create and push a feature branch with `agentic-kit transfer branch-create <branch> --push`.
2. Switch to that branch with `agentic-kit transfer branch-switch <branch> --pull`.
3. Use the GitHub connector only for direct-path file create/update operations on that feature branch.
4. Pull the feature branch locally with `agentic-kit transfer pull-current`.
5. Run the relevant local gates before PR creation.
6. Create the pull request with `agentic-kit transfer pr-create --head <branch> --base main`.
7. Inspect the PR with `agentic-kit transfer pr-status <pr> --expected-head-sha <full_sha>`.
8. Wait for CI with `agentic-kit transfer pr-wait-ci <pr> --expected-head-sha <full_sha>`.
9. Merge only with `agentic-kit transfer pr-merge-safe <pr> --expected-head-sha <full_sha>`.
10. After merge, run the post-merge handoff freshness check and refresh handoff state if required.

Safety requirements:

- The connector must not write directly to `main` for product work.
- The connector must not replace protected governance, YAML, status, or handoff files wholesale.
- The PR head SHA must be treated as a pinned merge precondition.
- Merge readiness is not inferred from visual inspection, small diffs, or “green-looking” UI state.
- A dirty worktree blocks the route until the dirty paths are reviewed, committed intentionally, or cleaned.
- If connector access is unavailable or insufficient, the fallback must be named explicitly in the evidence log.
