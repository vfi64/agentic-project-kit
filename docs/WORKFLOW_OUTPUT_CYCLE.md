# Workflow Output Cycle

## Purpose

Use `tools/next-step.py` as the single local entrypoint for bounded workflow-output handoff between a local checkout, the user, and an LLM with GitHub access.

## State cycle

- `TEST`: run the local workflow gate and capture complete output under `tmp/agent-evidence/`.
- `UPLOAD`: create a temporary `temp/workflow-evidence-*` branch, commit the bounded evidence file, and push it.
- `CLEANUP`: delete the temporary evidence branch locally and remotely, delete local evidence files, and reset the state to `TEST`.

## Command

```bash
python tools/next-step.py
```

Run the same command repeatedly. The current state is stored in `.agentic/workflow_state`.

## Rules for agents

- Prefer this workflow over manual Copy-and-Paste when complete terminal output matters.
- Treat evidence as temporary and bounded.
- Do not keep raw workflow evidence permanently in `main`.
- Cleanup must only delete branches whose names start with `temp/workflow-evidence-`.
- Inspect evidence for secrets before using it as review material.
