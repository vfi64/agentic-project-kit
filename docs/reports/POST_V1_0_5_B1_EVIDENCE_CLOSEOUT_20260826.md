# Post-v1.0.5 B1 Evidence Closeout

Status: B1_EVALUABLE  
Date: 2026-08-26  
Kit main verified for this report: `7cf492c1b8a705ab1e3f792636a9760718a1d29a`  
Current released package during closeout: `agentic-project-kit==1.0.5`  
Machine-readable companion: `docs/reports/POST_V1_0_5_B1_EVIDENCE_CLOSEOUT_20260826.json`

## Scope

This report consolidates the B1 Brownfield evidence from five real work cycles
in `vfi64/Comm-SCI-Control-private`. It adjudicates the B0 evaluability
threshold and records public-claim boundaries for the generated website and
community post drafts.

It does not claim general Brownfield portability, publish a release, run a sixth
Comm-SCI cycle, or reclassify command safety metadata.

## Method

B0 defined the B1 threshold before the realbetrieb window:

- at least five real B1 work cycles completed or stopped with evidence;
- at least three cycles crossed a merge boundary with measurable post-merge
  refresh outcome.

The cycle records, GitHub PR metadata, GitHub Actions runs, successor package
validation, and current Kit/Comm-SCI repository state were rechecked on
2026-08-26. Cycle 005 received a special evidence check because it changed CI
configuration rather than functional code.

## Cycle Summary

| Cycle | Real task | PRs | Merge boundary | Test evidence | Seam result | Remote CI |
| --- | --- | --- | --- | --- | --- | --- |
| 001 | Modularize App2 bridge helper seams | Comm-SCI #3 | later merged, not counted in the first report denominator | full suite 1483 passed | 72 -> 67 | no checks |
| 002 | Modularize App2 bridge runtime helpers | Comm-SCI #4 | counted | full suite 1488 passed | 67 -> 61 | no checks |
| 003 | Modularize App2 rule-file loading seam | Comm-SCI #5, #6, #7 | counted | full suite 1489 passed | 61 -> 59 | no checks |
| 004 | Modularize App2 window geometry seam | Comm-SCI #8, #9, #10 | counted | full suite 1490 passed | 59 -> 58 | no checks |
| 005 | Enable CI for feature branch PRs | Comm-SCI #11, #12, #13 | counted | remote CI only; no historical local full-suite entry | 58 -> 58 | success |

Cycle 005 changed CI configuration rather than functional code, so it has no
historical local full-suite entry. The three remote `pull_request` runs for
Comm-SCI #11/#12/#13 were revalidated as successful `pytest (3.11)` runs:
`32938530335`, `32938873386`, and `32939086344`.

No post-cycle local full-suite run was added during this closeout. Such a run
would be useful only as post-cycle verification and would not prove that the
same test was run during Cycle 005. The existing evidence is enough to
adjudicate B1 evaluability because Cycle 005's purpose was target-repository CI
configuration and its acceptance condition was real remote CI on PRs into the
feature integration branch.

## Quantitative Results

The seam metric is the Comm-SCI `tools/count_legacy_seams.py`
`legacy_seams_remaining` value for App2 legacy explicit delegations.

```text
legacy_seams_remaining: 72 -> 67 -> 61 -> 59 -> 58 -> 58
```

Full-suite runs stayed green across the cycles that ran them, growing from
1,483 to 1,490 tests as regression coverage was added. Cycle 005 is deliberately
excluded from that historical full-suite sequence because it was a CI
configuration slice.

B0 refresh metric:

```text
real B1 cycles: 5
merge-boundary cycles: 4
pure administrative refresh PRs: 6
administrative_refresh_rate: 6/4 = 1.5
observable_admin_refresh_share: 6/11
```

The refresh-rate result is a friction metric, not a success target. It shows
that the safety boundary worked, but at visible PR-cost.

## Brownfield Kit Defects

| Finding | Trigger | Root cause | Fix | Status | Evidence type |
| --- | --- | --- | --- | --- | --- |
| B1-KIT-002 external command-manifest handling | Cycle 001 | installed package lacked a manifest resource fallback | PR #2158, merge `78b1244a` | fixed in v1.0.5 | `kit_main`, `released_package`, `external_retest` |
| B1-KIT-004/005 external merge preflight | Cycle 002 | external context paths and self-hosting rule state leaked into preflight | PR #2166, merge `6533a98a` | fixed in v1.0.5 | `kit_main`, `released_package`, `external_retest` |
| B1-KIT-006 external post-merge base branch | Cycle 002 | post-merge check assumed `main` | PR #2168, merge `7ac386b9` | fixed in v1.0.5 | `kit_main`, `released_package`, `external_retest` |
| B1-KIT-009 external rule acknowledgement | Cycles 003-005 | rule source validation expected Kit self-hosting sources | PR #2180, merge `cd9543a7` | fixed on main and externally retested from checkout | `kit_main`, `external_retest` |

B1-KIT-009 is not yet `released_package` evidence. It needs a later package
release and an external installed-package retest before public copy can claim
that status.

## Friction And Bypasses

The bypasses are B1 results, not cleanup noise.

- Cycle 002 used raw `gh pr merge` pinned to the verified head after
  `pr-merge-safe` blocked on external context and rule-state assumptions.
- Cycles 003 and 004 used explicit Git/GitHub operations after `transfer
  commit`, `transfer push-current`, and `pr-merge-safe` hit external Rule-Ack or
  no-checks boundaries.
- Cycle 005 merged Comm-SCI #11/#12/#13 through `pr-merge-safe` after real
  remote CI became available, but the local wrapper did not return after the
  successful remote merge and had to be interrupted after remote verification.
- Mixed handoff/status/report updates produced extra administrative
  successor-refresh PRs in cycles 003-005.
- The external Rule-Ack retest on Kit main left an untracked
  `.agentic/rule_ack/` path in the local Comm-SCI checkout because that target
  workspace does not yet ignore it. This is a hygiene/UX follow-up, not a B1
  blocker.

## Adjudication

B1 reaches `B1_EVALUABLE`.

The predeclared B0 threshold is met: five real cycles were completed, and four
of them crossed a merge boundary with measurable post-merge refresh outcomes.
The target repository's own gates remained green for the functional cycles, and
Cycle 005 proved that target-owned CI could be adjusted so feature integration
branch PRs receive real remote checks.

B1 is not a proof of general Brownfield portability. The tested repository is
exactly the project whose growing complexity helped motivate the Kit in the
first place. That makes the test narratively relevant and operationally useful,
but methodically it is still one familiar private repository.

Therefore the correct public boundary is:

```text
stronger evidence than self-hosting, weaker evidence than an independent user adopting the Kit on an unrelated repository
```

## Decision

Update the planning state from `realbetrieb_running` to `B1_EVALUABLE` and
unblock B2 adjudication. Continue B3 only as report-only Stage 1 audit work.
Do not run another Comm-SCI cycle merely to improve the count.
