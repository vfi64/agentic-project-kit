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
