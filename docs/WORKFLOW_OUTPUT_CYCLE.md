# Workflow Output Cycle

## Purpose

Use `tools/next-step.py` as the single local entrypoint for bounded workflow-output handoff between a local checkout, the user, and an LLM with GitHub access.

## State cycle

- `IDLE`: do nothing and report that no workflow action was requested.
- `TEST`: run the local workflow gate and capture complete output under `tmp/agent-evidence/`.
- `UPLOAD`: create a temporary `temp/workflow-evidence-*` branch, commit the bounded evidence file, and push it.
- `CLEANUP`: delete the temporary evidence branch locally and remotely, delete local evidence files, and reset the state to `IDLE`.

## Command

```bash
python tools/next-step.py
```

The current state is stored in `.agentic/workflow_state`. `IDLE` is the safe default and never starts a test run.

## Starting a new cycle intentionally

Set the state to `TEST`, then run the entrypoint:

```bash
printf 'TEST\n' > .agentic/workflow_state
python tools/next-step.py
```

After the `TEST`, `UPLOAD`, and `CLEANUP` steps complete, the script returns the repository to `IDLE`.

## Rules for agents

- Prefer this workflow over manual Copy-and-Paste when complete terminal output matters.
- Treat evidence as temporary and bounded.
- Do not keep raw workflow evidence permanently in `main`.
- Cleanup must only delete branches whose names start with `temp/workflow-evidence-`.
- Inspect evidence for secrets before using it as review material.
