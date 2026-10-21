---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-070 (c1b): machine contracts for release preparation, CI templates and the CI runtime plan

Date: 2026-10-21
Plan: `external-retest-machine-contracts`, step c1, second part (owner order 2026-10-21).
Kit state: KIT-GF-070 stays PARTIAL. Consumer VERIFIED_FIXED remains independent.

## Contracts added

- KIT-GF-026: an unmodified older Kit-managed template and its injected workflow are planned for
  refresh and then written with the running Kit's pin, push only on main, concurrency and the
  browser cache.
- KIT-GF-036: a one-category summary is rejected by release-prep before any write (exit 2, clean
  worktree); a summary covering three quality categories passes.
- KIT-GF-037: a project-specific version anchor is in the release-prep plan and is written.
- KIT-GF-042: identically customized template and workflow block dry run and execute with both
  blockers named; both files stay unchanged.
- KIT-GF-060: release-prep moves exactly the summarized Unreleased entry into the new section,
  once; an unrelated entry stays under Unreleased; the earlier section is unchanged.
- KIT-GF-063: `ci runtime-plan` is light only for a refresh branch with refresh paths; a work
  branch, an unknown base and a product change are full; nothing is mutated.

The runner offers `{kit_version}` (the running Kit's version) besides `{kit_python}`, so a
contract can name the pinned template line without hard-coding a release. The release fixtures use
versions at or above the changelog-quality threshold and an explicit `--date` where the section
heading is compared.

## Reclassified

KIT-GF-064 is now `kit_release`: the repaired code is the Kit's own self-hosted release
preparation, which an external fixture cannot reach (external workspaces take the KIT-GF-060
path). The Kit's releases 1.1.3 and 1.1.4 left Unreleased empty and earlier sections unchanged.

## Result and remaining work

`greenfield retest --all`: PASS 37, FAIL 0, NO_MACHINE_CONTRACT 6, NOT_RUN_LOCALLY 40.
The family contracts KIT-GF-036, 037 and 060 also pass with the released 1.1.4 wheel.

Still without a contract: KIT-GF-014 and 015 (the catalog route does not exercise the repaired
code; the route must be corrected first), 021 and 067 (need a Kit installed as a wheel inside a
workspace interpreter), 032 and 045 (`release ready` needs a complete successor package and a
release-quality history in the fixture). `test_only_the_named_local_retests_lack_a_contract`
pins this set.
