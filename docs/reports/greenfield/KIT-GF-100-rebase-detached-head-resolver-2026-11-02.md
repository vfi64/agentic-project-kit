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
Full-suite and final gate results are recorded below when run.
This fix is separate from the B activation PR. Main's activation remains False.

## Scope and limitations

No dependencies, CLI options or result schema change. Existing file-write and
staging behavior remains in the CLI; only the cohesive new ownership check is
extracted, avoiding unrelated refactoring of the existing command module.
The active rebase metadata is treated as local Git state, not a security boundary
against a malicious actor who can rewrite the repository and its Git metadata.
