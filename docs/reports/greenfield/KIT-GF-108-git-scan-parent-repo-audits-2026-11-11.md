# KIT-GF-108: Audits inside an ignored child of a parent repository

Date: 2026-11-11

Scope: absolute-path portability and ns-legacy reference audits.

Status: fixed on the review branch; not merged or released.

## Finding

Both audits accepted `git ls-files` from an unrelated parent Git repository.
When that parent ignored the child project, Git returned an empty file list and
both audits falsely reported PASS with zero references.

## Change

Both audits and the earlier GF-105 call site now share one Git-worktree-root
check. Only an actual root uses Git's tracked/untracked file list; a child of
another repository falls back to the existing recursive walk. An actual root
still honors its ignore rules.

## Regression evidence

The new ignored-parent tests in `test_absolute_path_portability_audit.py` and
`test_ns_legacy_reference_audit.py` both failed before the fix (PASS with zero
references instead of BLOCK) and pass after it. Existing own-root tests keep
the ignored-subdirectory control.

`exclude-standard` source inventory found these three Kit scan call sites and
`scripts/command_flow_audit.py`. The script checks untracked analyzed inputs,
not candidate files for either content audit; it is outside this fix.

## Boundaries

The retest harness has no ignored-parent-repository fixture. Native tests do
not establish external consumer `VERIFIED_FIXED` or a release.
