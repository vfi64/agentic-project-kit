# Patch Failure Diagnosis Policy

This repository treats repeated patch misses as a process failure, not as a reason
to keep guessing.

## Rule

After two failed patch or test-correction attempts against the same file, test
function, command registration, or error pattern, the next step must be a
diagnosis step before any further patching.

The diagnosis evidence must include the actual current state relevant to the
failure, such as:

- current branch and worktree status,
- relevant file content or parsed function body,
- relevant diff,
- relevant test failure or command output,
- an explicit diagnosis result marker such as
  `RESULT=PATCH_FAILURE_DIAGNOSIS_DONE` or
  `RESULT=<slice>_DIAGNOSE_<topic>_DONE`.

After the diagnosis step, the next patch must be a minimal patch based on the
observed current state.

## Enforcement

`agentic-kit audit-patch-failure-discipline` scans repo-backed command reports.
When called with `--include-tmp`, it also scans local `tmp/` logs. The audit
fails if a log group contains two or more patch-failure signals after the most
recent diagnosis signal.

This does not prove that a diagnosis was semantically perfect, but it prevents
silent green closeout when repeated patch failures leave no diagnosis evidence.
