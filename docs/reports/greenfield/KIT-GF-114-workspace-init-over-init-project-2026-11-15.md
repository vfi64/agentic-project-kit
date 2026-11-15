# KIT-GF-114: workspace init over an init project

Date: 2026-11-15

Scope: `workspace init` (`cli_commands/workspace.py`, `workspace_recovery.py`,
`g3_remedies.py`).

Status: fixed in this change; not released.

## Finding

`agentic-kit init` writes `.agentic/project.yaml` but no workspace manifest.
`workspace init` on such a project failed with `FOREIGN_AGENTIC` and the human
marker, although the documented way on is the signed recovery
(`workspace init --recover-partial`). Observed live in order 0107; the code
path dates from #1742.

## Change

The G3 remedy table (`g3_remedies.REMEDIES`) maps `FOREIGN_AGENTIC` of
`workspace init` to `agentic-kit workspace init --recover-partial`, under the
condition that the root holds a valid, recoverable generated project contract
and an existing Git HEAD (`generated_project_recoverable`; `init` without a Git
identity leaves no HEAD, KIT-GF-104). The result names that plan as an autonomous
`next_command`; with `--inject-ci` its `next_action` adds
`workspace ci-update --inject-ci --execute` for after the recovery. A foreign
`.agentic/` without such a contract, or a generated project without a commit,
keeps the human marker. Exit code, code
and error text are unchanged.

## Regression evidence

`tests/test_g3_remedy_table.py` (cases `FOREIGN_AGENTIC`, text mode) checks
JSON and text output, that the named plan offers a signature, the foreign
control and the control without a Git HEAD; the module sets a Git identity, as
CI runners have none. Against the previous code it fails with `next_command_kind` human.
The machine contract runs the same with the installed wheel.

## Boundaries

No release or consumer `VERIFIED_FIXED` is claimed.
