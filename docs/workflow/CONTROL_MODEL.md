# Deterministic Workflow Control Model

The workflow control model separates low-level command success from target-state success.
A command is not considered failed merely because a local action was unnecessary.
The decisive question is whether the intended target state has been reached.

## Core rule

Every workflow step must classify its result before follow-up actions are allowed.

Required step order:

1. Precheck
2. Patch or action
3. Verify target state
4. Run dependent tests or gates only after the target state is valid
5. Commit, push, PR, merge, or release only after the preceding state is valid

A failing patch or action must stop the slice immediately.
Dependent tests, gates, commits, pushes, PR creation, merges, tags, and releases must not run after a failed core step.

## Successful target states

These states are successful and may continue to the next step:

- `PASS`
- `DONE`
- `NOOP`
- `ALREADY_ON_MAIN`
- `ALREADY_MERGED`
- `ALREADY_RELEASED`
- `DOI_VERIFIED`
- `SUPERSEDED`

These states mean that the target condition is already satisfied or the requested action is unnecessary.
They must not be reported as generic failures.

## Retryable states

These states stop the current slice without treating the target as permanently failed:

- `PENDING`
- `WAIT`

A retryable state must not trigger dependent actions such as merge, tag, release, or finalization.
The correct outcome is to stop with a clear retry path.

## Failure states

These states stop the slice immediately:

- `FAIL`
- `NEEDS_HUMAN_REVIEW`

A failure state must not be followed by tests, gates, commits, pushes, PR creation, merges, tags, releases, or finalization.

## Standard error classes this model prevents

- Treating already reached target states as failures
- Continuing after a failed patch
- Adding tests although the implementation patch failed
- Running release builds after release metadata checks failed
- Trying to create PRs for branches with no commits over main
- Treating pending checks as permanent failures
- Treating already merged or superseded finalization branches as hard failures
- Confusing tool availability problems with semantic patch failures

## Implementation anchors

- `src/agentic_project_kit/control_state.py` defines machine-readable workflow states.
- `src/agentic_project_kit/slice_runner.py` defines stop-on-fail sequential slice execution.
- `tests/test_control_state.py` verifies target-state classification.
- `tests/test_slice_runner.py` verifies stop-on-fail and retryable-stop behavior.
