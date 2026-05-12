# Workflow Output Cycle

## Purpose

Use `tools/next-step.py` as the single local entrypoint for bounded workflow-output handoff between a local checkout, the user, and an LLM with GitHub access.

## Current safe default

- `IDLE`: do nothing and report that no workflow action was requested.

## Legacy state cycle

The original evidence cycle remains supported for compatibility:

- `TEST`: run the local workflow gate and capture complete output under `tmp/agent-evidence/`.
- `UPLOAD`: create a temporary `temp/workflow-evidence-*` branch, commit the bounded evidence file, and push it.
- `CLEANUP`: delete the temporary evidence branch locally and remotely, delete local evidence files, and reset the state to `IDLE`.

## Declarative workflow request cycle

A newer, safer workflow uses a declarative allowlisted request file:

- `.agentic/current_work.yaml`: describes the current local task using known step names.
- `REQUESTED`: run the declarative workflow request.
- `RUNNING`: guard state written before the local task starts.
- `UPLOADED`: local task finished and the evidence branch was pushed for LLM review.
- `FAILED`: local task failed or timed out; evidence is preserved when possible and no automatic cleanup is performed.

Allowed declarative steps are implemented in `tools/workflow_runner.py`. The runner executes command lists directly and does not use shell snippets.

## Command

```bash
python tools/next-step.py
```

The current state is stored in `.agentic/workflow_state`. `IDLE` is the safe default and never starts a run.

## Starting a legacy cycle intentionally

Set the state to `TEST`, then run the entrypoint:

```bash
printf 'TEST\n' > .agentic/workflow_state
python tools/next-step.py
```

After the `TEST`, `UPLOAD`, and `CLEANUP` steps complete, the script returns the repository to `IDLE`.

## Starting a declarative workflow intentionally

Set `.agentic/current_work.yaml` to the desired allowlisted task, then set:

```bash
printf 'REQUESTED\n' > .agentic/workflow_state
python tools/next-step.py
```

After the `REQUESTED` step succeeds, the state becomes `UPLOADED`. The LLM can inspect the remote temporary evidence branch. A later `python tools/next-step.py` call cleans up and returns to `IDLE`.

## Future CLI direction

The long-term target is to expose this through first-class commands:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow status
agentic-kit workflow cleanup
```

Keep this as a planned follow-up rather than expanding `tools/next-step.py` indefinitely.

## Rules for agents

- Prefer this workflow over manual Copy-and-Paste when complete terminal output matters.
- Prefer declarative YAML workflow requests over executable ad-hoc scripts.
- Treat evidence as temporary and bounded.
- Do not keep raw workflow evidence permanently in `main`.
- Cleanup must only delete branches whose names start with `temp/workflow-evidence-`.
- Never automatically clean up from `FAILED`.
- Inspect evidence for secrets before using it as review material.
