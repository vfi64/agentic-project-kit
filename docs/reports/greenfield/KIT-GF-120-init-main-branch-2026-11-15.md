# KIT-GF-120: init starts the repository on main

Date: 2026-11-15

Scope: `agentic-kit init` (`templates.py`, repository creation).

Status: fixed in this change; not released.

## Finding

`init` created the repository with a plain `git init`, so the branch followed
the machine's `init.defaultBranch`. Without it Git uses `master`: the project's
initial commit and, with `--github`, its first push landed on `master`, while
the Kit's workflows assume `main` (`work start --from-ref main`, `sync-main`,
`release run`). Observed in the stub probe of order 0112, whose environment had
no `init.defaultBranch`; journey J6 and the retest environment set `main` and
hid it, as did the owner's machine in the live runs 0107 and 0112.

## Change

After `git init`, a repository without commits is pointed at `main`
(`git symbolic-ref HEAD refs/heads/main`), which works with every Git version.
An existing repository with commits keeps its branch.

## Regression evidence

`tests/test_init_main_branch.py` runs `init` with the Git default branch
`master`, `trunk` and unset; the project is on `main` with no other branch. The
machine contract of the catalog entry sets the run-local default branch to
`master` and checks `main`. Both fail against the previous code.

## Boundaries

No release or consumer `VERIFIED_FIXED` is claimed.
