# KIT-GF-115: recovery with injection flags

Date: 2026-11-15

Scope: `workspace init --recover-partial` (`cli_commands/workspace.py`).

Status: fixed in this change; not released.

## Finding

`workspace init --recover-partial --inject-ci` (or `--inject-pre-commit`)
blocked with "Recovery does not inject CI or pre-commit files." and the human
marker. Two Kit commands resolve it: the same recovery without the flag, then
`workspace ci-update --inject-ci --execute`. Observed live in order 0107; the
refusal dates from #2652.

## Change

The result carries `code` `RECOVERY_NO_INJECTION`, names
`agentic-kit workspace init --recover-partial` (remedy table) as autonomous
`next_command` and `workspace ci-update --inject-ci --execute` in
`next_action`. Nothing is written and the exit code stays 2.

## Regression evidence

`tests/test_g3_remedy_table.py` (case `RECOVERY_NO_INJECTION`) checks both
flags. Against the previous code it fails with `next_command_kind` human. The
machine contract runs it with the installed wheel and checks that no workspace
manifest or workflow was written.

## Boundaries

Pre-commit has no Kit injection route after a recovery; the `next_action`
names only the CI route. No release or consumer `VERIFIED_FIXED` is claimed.
