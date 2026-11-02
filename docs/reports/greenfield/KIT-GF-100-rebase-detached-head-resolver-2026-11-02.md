# KIT-GF-100: owned detached-HEAD rebase conflict resolution

Status: CLOSED/unreleased. No merge or release is authorized by this report.

## Reproduction and fix

The file resolver previously rejected a normal conflicted Git rebase because
`git branch --show-current` is empty while HEAD is detached. The new real-Git
regression failed before the fix: one failed, seven passed; the valid resolution
returned BLOCKED instead of PASS. The failing assertion was the expected exit
code, not fixture setup.

The CLI now delegates detached-rebase ownership checks to
`conflict_rebase_branch.py`. Git resolves metadata paths, including linked
worktrees. Exactly one active rebase backend is accepted. The local branch ref
must be valid and still point to the original commit. Original and target IDs
must identify commits, and the target must be an ancestor of the current HEAD.
Existing expected-branch, main/master and conflicted-target guards still apply.
No automatic rebase continuation or metadata repair is performed.

## Evidence

`tests/test_conflict_resolver_rebase.py`: 13 passed after the fix. The valid CLI
case resolves and stages the file and completes the actual rebase. Invalid
states preserve both file bytes and the unmerged index: absent/ambiguous rebase,
missing or invalid target, absent or unsafe branch, protected branch, mismatched
expected branch, moved owner ref, missing original commit, unrelated target.
A linked-worktree case tests the importable ownership checker directly.

The initial focused run including existing transfer CLI regressions passed:
127 tests, 31 warnings. The machine contract first rejects a wrong expected
branch and proves unchanged conflict bytes, then resolves the valid conflict
and verifies staged content and an empty unmerged-path set.

Fresh noneditable wheel: KIT-GF-100 PASS, including all 22 machine steps.
Ruff, check, check-docs and doctor passed. The initial full-suite run encountered
the unchanged audit test's source-versus-HEAD guard while product edits were
uncommitted. A committed-source rerun is required; the guard is not weakened.
Final full suite: 4536 passed, 560 warnings in 1212.37s (0:20:12).
The run used the local virtualenv CLI on PATH and native macOS isolation
outside the outer agent sandbox. An earlier run stopped when a CLI test
could not find the Kit executable; all six affected CLI tests subsequently
passed with the correct PATH. No product changes or test exclusions were
used to resolve either environment limitation.
This fix is separate from the B activation PR. Main's activation remains False.

## Scope and limitations

No dependencies, CLI options or result schema change. Existing file-write and
staging behavior remains in the CLI; only the cohesive new ownership check is
extracted, avoiding unrelated refactoring of the existing command module.
The active rebase metadata is treated as local Git state, not a security boundary
against a malicious actor who can rewrite the repository and its Git metadata.

## Preserved historical evidence

The original reproduction and exact direct-Git B rebase continuation remain
available in the [immutable pre-fix report](https://github.com/vfi64/agentic-project-kit/blob/29f792bc362e7dd130e735e0793833ca5ea2dfc4/docs/reports/greenfield/KIT-GF-100-rebase-detached-head-resolver-2026-11-02.md). Its OPEN finding
and negative-only contract describe the historical state, superseded by
this fix and its positive/negative contract. B is not modified here.
