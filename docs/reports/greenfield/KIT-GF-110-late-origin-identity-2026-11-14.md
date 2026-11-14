# KIT-GF-110: Origin added after workspace init

Date: 2026-11-14

Scope: `check_projection` in `external_handoff_projection.py` and the post-merge-check step of `work start` (`cli_commands/human_workflows.py`).

Status: fixed on Kit `main` in PR #2786 (`25a27560`); not released.

## Finding

When `origin` was added after `workspace init`, the committed successor package
still carried the fallback repository identity (project or folder name). The
next `work start` ended BLOCKED: `transfer post-merge-check` reported
`projection_inputs_changed` with `execution_contract` and `repository_name`
and asked for a successor-package refresh. The path "git init, set up the Kit,
create the GitHub repository later" therefore stopped at its first work cycle.
Offline journeys did not see it, because a local origin yields no GitHub
identity (G4 live-run probe, 2026-11-13).

## Change

`check_projection` classifies a projection that differs only because origin
was bound later (the stored projection equals the projection computed without
origin) as `projection_identity_bound_after_init`. `work start` continues in
that case and names the binding; `work finish` regenerates the package in the
same work cycle. Any other changed input still blocks.

## Regression evidence

`tests/test_f1_identity_bound_after_init.py` covers the classification, the
block when another input changed as well, the current state after a refresh
and the `work start` decision. The machine contract adds a GitHub origin to a
committed workspace (redirected to the local bare origin with
`url.<origin>.insteadOf`) and requires `work start` to pass and name the
binding. With the code before PR #2786 the same `work start` ends BLOCKED at
post-merge-check.

## Boundaries

The contract uses a redirected GitHub URL, not a real GitHub repository.
Consumer `VERIFIED_FIXED` and the release are separate.
