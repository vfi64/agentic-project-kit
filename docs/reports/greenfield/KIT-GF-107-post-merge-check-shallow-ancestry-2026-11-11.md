# KIT-GF-107: Unknown successor ancestry in a shallow clone

Date: 2026-11-11

Scope: self-hosting successor-package freshness and `transfer post-merge-check`.

Status: fixed on the review branch; not merged or released.

## Finding

In a depth-one clone, the package's `generated_head` can be absent from local
history. Git returns an error for the ancestry query; the old boolean helper
treated that as a proven non-ancestor and requested a successor refresh.
The same package in a full clone was accepted as a refresh-only descendant.

## Change

The ancestry helper now distinguishes ancestor, proven non-ancestor and
unknown. Unknown includes Git errors and a failed changed-path diff. Package
freshness records `ancestry_unknown` plus generated/current HEAD notes and a
local-history diagnostic hint. `post-merge-check` returns `BLOCKED` with a
diagnosis action and no refresh state. It does not fetch history. The summary
does not label unknown ancestry as fresh or stale.

## Regression evidence

`test_post_merge_check_shallow_ancestry_blocks_without_refresh` creates a
real repository with explicit Git identity, a refresh-only package commit,
and depth-one and full clones. Before the fix the shallow clone returned FAIL
and requested `NEEDS_SUCCESSOR_PACKAGE_REFRESH`. After the fix it is BLOCKED
with `ancestry_unknown`; the full clone remains PASS. A divergent commit whose
`generated_head` exists locally still requests refresh. The test also checks
that the settle and lifecycle refresh selectors have no action for BLOCKED.

Full Kit suite on committed branch head `e1ec2b9f`: 4577 passed, 570
deprecation warnings in 1150.65 seconds. The first full-suite attempt exposed
the catalog meta-test's requirement for machine contracts on all local retests;
the four explicitly justified fixture exceptions were added before this green
rerun.

## Other ancestry call sites

A source inventory found `merge-base --is-ancestor` in
`transfer_repo_actions.py` (one separate remote-SHA check), `dpa_final_closeout.py`,
`conflict_rebase_branch.py`, `release_run_resume.py`,
`status_current_state_audit.py`, `kit_return.py` and `work_rescue.py`.
`ci_light_skip.py` uses `merge-base` without `--is-ancestor`. These paths were
not changed; their handling of absent commits needs a separate review if a
shallow-clone failure is observed there.

## Boundaries

The native test establishes the local state transition only. The retest
harness cannot construct a shallow self-hosting clone. No release or external
consumer `VERIFIED_FIXED` is claimed.
