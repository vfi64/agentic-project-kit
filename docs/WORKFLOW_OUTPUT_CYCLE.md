# Workflow Output Cycle

## Purpose

Use the workflow CLI or compatibility entrypoint as the normal local entrypoint for bounded workflow-output handoff between a local checkout, the user, and an LLM with GitHub access.

## Current safe default

- `IDLE`: do not start work automatically.
- When `.agentic/current_work.yaml` exists, `python tools/next-step.py` reports the current workflow request file and the exact command needed to start it.

## Standard next-step terminal workflow

For app-based ChatGPT workflows, the normal local command is:

```bash
cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
python tools/next-step.py
```

After the command finishes, the user can usually reply in chat with only:

```text
done
```

The short acknowledgement `d` is also valid. The assistant then evaluates the workflow state, evidence pointer, or copied terminal output and proposes the next safe step.

This keeps routine work out of long manual Copy-and-Paste blocks. Use full copied terminal output only when the local workflow did not provide enough bounded evidence for review.

## Default current-branch local gate workflow

`.agentic/current_work.yaml` defines a deterministic default current-branch local gate workflow named `default-current-branch-local-gate`.

The default local gate runs only allowlisted steps on the currently checked-out branch:

```text
git_fetch
git_pull_ff_only
pytest
ruff_check
check_docs
doctor
```

It does not switch to `main`, so it can validate either `main` or the current PR branch. This is the standard evidence-producing workflow for routine chat-assisted validation. To run it from `IDLE`, use:

```bash
agentic-kit workflow request && python tools/next-step.py
```

After the command finishes, reply in chat with `done` or `d`. The assistant can then inspect the workflow state and the current report pointer.

## Primary workflow CLI

Use these commands for explicit operation:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow status
agentic-kit workflow cleanup
```

The commands operate on `.agentic/workflow_state` and `.agentic/current_work.yaml`.

`agentic-kit workflow status` also reports the current workflow-output pointer when present:

```text
docs/reports/CURRENT_WORKFLOW_OUTPUT.md
```

- `workflow request`: marks an IDLE or FAILED declarative workflow as REQUESTED.
- `workflow run`: runs exactly one bounded state-machine step through the existing local entrypoint.
- `workflow status`: prints the current state and bounded evidence pointers.
- `workflow cleanup`: cleans an UPLOADED/CLEANUP evidence branch, otherwise no-ops with a status message.

## Compatibility entrypoint

`tools/next-step.py` remains supported as the compatibility entrypoint while the CLI path stabilizes:

```bash
python tools/next-step.py
```

Keep `tools/next-step.py` available for the standard chat-assisted terminal workflow. Do not expand it indefinitely. New user-facing workflow behavior should move toward `agentic-kit workflow ...` commands while preserving this compatibility bridge.

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

The current state is stored in `.agentic/workflow_state`. `IDLE` is the safe default and never starts a run.

## Starting a legacy cycle intentionally

Set the state to `TEST`, then run the entrypoint:

```bash
printf 'TEST\n' > .agentic/workflow_state
agentic-kit workflow run
```

After the `TEST`, `UPLOAD`, and `CLEANUP` steps complete, the script returns the repository to `IDLE`.

## Starting a declarative workflow intentionally

Set `.agentic/current_work.yaml` to the desired allowlisted task, then run:

```bash
agentic-kit workflow request
agentic-kit workflow run
```

After the `REQUESTED` step succeeds, the state becomes `UPLOADED`. The LLM can inspect the remote temporary evidence branch. A later `agentic-kit workflow cleanup` call cleans up and returns to `IDLE`.

## Rules for agents

- Prefer the standard next-step terminal workflow over manual Copy-and-Paste when complete terminal output matters.
- Accept `done` or `d` as the normal user acknowledgement after `python tools/next-step.py` finishes.
- Prefer declarative YAML workflow requests over executable ad-hoc scripts.
- Treat evidence as temporary and bounded.
- Do not keep raw workflow evidence permanently in `main`.
- Cleanup must only delete branches whose names start with `temp/workflow-evidence-`.
- Never automatically clean up from `FAILED`.
- Inspect evidence for secrets before using it as review material.
