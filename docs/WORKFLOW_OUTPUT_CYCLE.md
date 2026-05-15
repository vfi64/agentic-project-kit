# Workflow Output Cycle

## Purpose

Use the workflow CLI or compatibility entrypoint as the normal local entrypoint for bounded workflow-output handoff between a local checkout, the user, and an LLM with GitHub access.

## Current safe default

- `IDLE` with `.agentic/current_work.yaml` state `READY`: no-ops and stays idle.
- `IDLE` with `.agentic/current_work.yaml` state `REQUESTED`: runs the configured declarative workflow.
- `UPLOADED`: performs bounded cleanup of the temporary evidence branch.
- `FAILED`: preserves evidence and never cleans up automatically.
- `RUNNING`: refuses to start a second workflow automatically.

## Standard next-step terminal workflow

For app-based ChatGPT workflows, the normal local command is:

```bash
cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit
agentic-kit workflow request
agentic-kit workflow run
```

The compatibility entrypoint remains available and has equivalent request/run behavior:

```bash
.venv/bin/python tools/next-step.py --request
python3 tools/next-step.py
```

After the command finishes, the user can usually reply in chat with only:

```text
done
```

The short acknowledgement `d` is also valid. The assistant then evaluates the workflow state, evidence pointer, or copied terminal output and proposes the next safe step.

This keeps routine work out of long manual Copy-and-Paste blocks. Use full copied terminal output only when the local workflow did not provide enough bounded evidence for review.

## Single-command state behavior

`tools/next-step.py` branches by `.agentic/workflow_state`:

```text
IDLE + .agentic/current_work.yaml state READY -> no-op -> IDLE
IDLE + .agentic/current_work.yaml state REQUESTED -> run workflow -> reset request to READY -> upload evidence -> UPLOADED
UPLOADED -> cleanup temporary evidence branch -> IDLE
FAILED -> preserve evidence; no automatic cleanup
RUNNING -> refuse duplicate execution
TEST/UPLOAD/CLEANUP -> legacy compatibility cycle
```

This means routine work uses an explicit request followed by the same command for validation and cleanup:

```bash
agentic-kit workflow request
agentic-kit workflow run
```

After `UPLOADED`, run `agentic-kit workflow cleanup` or `python3 tools/next-step.py` once more for cleanup. Then reply in chat with `done` or `d`.

## FAILED handling

`FAILED` is a stop-and-diagnose state. Do not repeatedly run `ns` or `python3 tools/next-step.py`. Also do not repeatedly run `agentic-kit workflow run` hoping that the same workflow will self-heal.

When the workflow state is `FAILED`:

1. Preserve the local terminal output and any files under `tmp/agent-evidence/`.
2. Send the relevant terminal output to the assistant if no temporary evidence branch was uploaded.
3. Inspect the local state with:

```bash
git status --short
git branch --show-current
cat .agentic/workflow_state
ls -lt tmp/agent-evidence 2>/dev/null | head
```

4. Diagnose and fix the root cause, such as a test failure, documentation-coverage failure, missing tool, or dirty git state.
5. Only after the cause is understood, consciously reset the workflow state and generated report:

```bash
git restore .agentic/workflow_state docs/reports/CURRENT_WORKFLOW_OUTPUT.md
```

6. If stale local evidence files would confuse the next run, remove only the local bounded evidence pointers:

```bash
rm -f tmp/agent-evidence/workflow-output-*.md
rm -f tmp/agent-evidence/latest-branch.txt
```

7. Run `agentic-kit workflow run`, `ns`, or `python3 tools/next-step.py` again after the failure cause has been fixed.

The short chat acknowledgement `d` is normally sufficient after `UPLOADED`, because the assistant can inspect the remote evidence branch. It is not sufficient for a local `FAILED` state unless the failure evidence was already uploaded or the assistant has enough copied terminal output.

Never automatically clean up from `FAILED`. The failure evidence is part of the diagnostic trail.

## Environment bootstrap

`tools/next-step.py` is intended to work even when the project virtual environment is not activated in the current shell.

Before reading the workflow state, it performs a bounded environment bootstrap:

```text
missing .venv/bin/python -> create .venv with the current Python interpreter
missing .venv/bin/ruff or .venv/bin/agentic-kit -> run .venv/bin/python -m pip install -e .[dev]
```

The workflow runner then uses the project-local tools:

```text
.venv/bin/python
.venv/bin/ruff
.venv/bin/agentic-kit
```

This does not activate the virtual environment in the parent shell. It only makes the workflow command self-sufficient.

## Optional shell shortcut

A local zsh alias or function can shorten the compatibility entrypoint to `ns`. This is local shell configuration, not repository state. A typical user setup is:

```zsh
alias ns='cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit && python3 tools/next-step.py'
alias nsr='cd /Users/hof/Dropbox/Privat/GitHub/agentic-project-kit && .venv/bin/python tools/next-step.py --request'
```

After adding those aliases to `~/.zshrc`, routine compatibility-entrypoint work becomes:

```zsh
nsr
ns
```

A plain `ns` is intentionally a no-op while `.agentic/current_work.yaml` is `READY`.

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

It does not switch to `main`, so it can validate either `main` or the current PR branch. This is the standard evidence-producing workflow for routine chat-assisted validation.

## Primary workflow CLI

Use these commands for explicit operation:

```text
agentic-kit workflow request
agentic-kit workflow run
agentic-kit workflow status
agentic-kit workflow cleanup
```

The commands operate on `.agentic/workflow_state` and `.agentic/current_work.yaml`.

`agentic-kit workflow request` is the public equivalent of `tools/next-step.py --request`: it sets `.agentic/current_work.yaml` to `state: REQUESTED` while leaving `.agentic/workflow_state` at `IDLE`. It does not run the workflow as a side effect. A repeated request while the workflow is already requested is idempotent.

`agentic-kit workflow status` reports both state layers. Add `--explain` for a read-only interpretation and recommended next step. For example:

```text
workflow_state=IDLE
current_work=present
current_work_state=REQUESTED
```

`agentic-kit workflow status` also reports the current workflow-output pointer when present:

```text
current_report=docs/reports/CURRENT_WORKFLOW_OUTPUT.md
```

`current_report` is a pointer to the latest local workflow-output summary. It is useful for review, but it is not a command and does not change state.

Guided status compass:

- `IDLE` plus `current_work_state=READY`: no active workflow request; do nothing or request a concrete slice.
- `IDLE` plus `current_work_state=REQUESTED`: a workflow request is pending; run `agentic-kit workflow run`.
- `UPLOADED`: evidence was uploaded; inspect it, then run `agentic-kit workflow cleanup`.
- `FAILED`: stop and inspect evidence before cleanup or retry.
- dirty working tree: inspect `git status` before running workflow automation.

- `workflow request`: marks the declarative workflow file as REQUESTED while the main workflow state remains IDLE.
- `workflow run`: runs exactly one bounded state-machine step through the existing local entrypoint.
- `workflow status`: prints the current state, current workflow request state, and bounded evidence pointers.
- `workflow cleanup`: cleans an UPLOADED/CLEANUP evidence branch, otherwise no-ops with a status message.

## Compatibility entrypoint

`tools/next-step.py` remains supported as the compatibility entrypoint while the CLI path stabilizes:

```bash
python3 tools/next-step.py
```

Keep `tools/next-step.py` available for the standard chat-assisted terminal workflow. Do not expand it indefinitely. New user-facing workflow behavior should move toward `agentic-kit workflow ...` commands while preserving this compatibility bridge.

## Legacy state cycle

The original evidence cycle remains supported for compatibility:

- `TEST`: run the local workflow gate and capture complete output under `tmp/agent-evidence/`.
- `UPLOAD`: create a temporary `temp/workflow-evidence-*` branch, commit the bounded evidence file, and push it.
- `CLEANUP`: delete the temporary evidence branch locally and remotely, delete local evidence files, and reset the state to `IDLE`.

## Declarative workflow request cycle

A newer, safer workflow uses a declarative allowlisted request file:

- `.agentic/current_work.yaml`: describes the current local task using known step names and stores the request state.
- `READY`: a safe no-op request state.
- `REQUESTED`: the configured declarative workflow should run on the next workflow step.
- `RUNNING`: guard state written before the local task starts.
- `UPLOADED`: local task finished and the evidence branch was pushed for LLM review.
- `FAILED`: local task failed or timed out; evidence is preserved when possible and no automatic cleanup is performed.

Allowed declarative steps are implemented in `tools/workflow_runner.py`. The runner executes command lists directly and does not use shell snippets.

The main workflow state is stored in `.agentic/workflow_state`. `IDLE` is the safe default and only starts a run when `.agentic/current_work.yaml` has `state: REQUESTED`.

## Starting a legacy cycle intentionally

Set the state to `TEST`, then run the entrypoint:

```bash
printf 'TEST\n' > .agentic/workflow_state
agentic-kit workflow run
```

After the `TEST`, `UPLOAD`, and `CLEANUP` steps complete, the script returns the repository to `IDLE`.

## Starting a declarative workflow intentionally

Set `.agentic/current_work.yaml` to the desired allowlisted task with `state: READY`, request it explicitly, then run:

```bash
agentic-kit workflow request
agentic-kit workflow run
```

After the `IDLE` step succeeds, the state becomes `UPLOADED`. The LLM can inspect the remote temporary evidence branch. A later `agentic-kit workflow cleanup` call cleans up and returns to `IDLE`.

## Rules for agents

- Prefer the standard workflow CLI or compatibility next-step terminal workflow over manual Copy-and-Paste when complete terminal output matters.
- Accept `done` or `d` as the normal user acknowledgement after the workflow command finishes.
- Prefer declarative YAML workflow requests over executable ad-hoc scripts.
- Treat evidence as temporary and bounded.
- Do not keep raw workflow evidence permanently in `main`.
- Cleanup must only delete branches whose names start with `temp/workflow-evidence-`.
- Never automatically clean up from `FAILED`.
- Inspect evidence for secrets before using it as review material.
