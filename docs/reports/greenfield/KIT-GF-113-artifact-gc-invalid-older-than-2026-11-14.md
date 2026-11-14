# KIT-GF-113: artifact-gc with an invalid --older-than value

Date: 2026-11-14

Scope: `artifact-gc` (`cli_commands/artifact_gc.py`).

Status: fixed in this change; not released.

## Finding

`artifact-gc` parsed `--older-than` with `typer.BadParameter`. An unreadable
value therefore ended as a Click usage error: exit 2, a usage text on stderr,
no JSON document even with `--json` and no G3 route, although every other
refusal of the command is a routed `artifact_gc_result`.

## Change

An unreadable cutoff returns `FAIL_INVALID_OLDER_THAN` as an
`artifact_gc_result` with `result_status` FAIL, an `error` naming the value,
no candidates and the human route (rerun with an ISO date or datetime, or omit
the option). The command exits 2 as before and collects nothing. Options, help
texts and the command manifest are unchanged.

## Regression evidence

`test_artifact_gc_invalid_older_than_is_a_routed_result_without_collection`
(`tests/test_g3_command_routes.py`) checks JSON and text mode for two invalid
values and that no collector runs. Against the previous code it fails because
stdout holds no JSON document. The machine contract runs the same refusal and a
valid-date control with the installed wheel.

## Boundaries

No release or consumer `VERIFIED_FIXED` is claimed.
