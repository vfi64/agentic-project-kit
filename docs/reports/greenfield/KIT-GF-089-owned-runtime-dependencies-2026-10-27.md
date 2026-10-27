---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-089 — owned-runtime retests without dependencies under an installed wheel

## Observed
After adopting the released Kit 1.1.6, a consumer workspace ran
`agentic-kit greenfield retest --all --json`: PASS 41, FAIL 4, NOT_RUN_LOCALLY 40,
NO_MACHINE_CONTRACT 0. The four failures were KIT-GF-021, 032, 045 and 067, the
contracts that run the Kit from an owned interpreter. Each failed with
`ModuleNotFoundError: No module named 'typer'`. A clean virtual environment with
`agentic-project-kit==1.1.6` from PyPI reproduced the identical counts.

## Cause
`prepare_owned_runtime` copies the running Kit package and its distribution
metadata into a fresh interpreter and shares the invoking environment's
dependencies through a `.pth` file. It deliberately left out the directory that
holds the running Kit, so the owned copy and not the original is imported. From a
source checkout that directory is `src/` and holds only the Kit. From an installed
wheel it is `site-packages`, which also holds typer, click and every other
dependency, so the owned runtime started without them.

The Kit's own tests did not show this: `tests/test_greenfield_retest.py` runs the
contracts from a wheel extracted into its own directory and put on `PYTHONPATH`,
while the dependencies stay in the test environment. That layout matches a source
checkout, not an installed wheel.

## Repair
The Kit's directory is no longer dropped. It is replaced by a view of symbolic
links (`owned-runtime-dependencies` beside the owned runtime) to every entry
except the Kit's own package, its `.dist-info`/`.egg-info` metadata, `.pth` files
and `__pycache__`. The owned runtime therefore imports its dependencies and still
imports the Kit only from its own copy. From a source checkout the view is empty,
which is the previous behaviour. No consumer files, no network and no pip are
involved.

## Regression and machine contract
- `tests/test_greenfield_retest_owned_runtime_wheel.py`: the view keeps every
  dependency and drops the Kit, its metadata, `.pth` files and missing or empty
  paths; and an owned runtime prepared from a wheel layout (Kit and dependencies in
  one directory, `python -S`) imports typer and the Kit from its own copy. The
  second test fails against the previous code.
- Machine contract KIT-GF-089 (`git_repository` fixture): a nested
  `agentic-kit greenfield retest --id KIT-GF-021 --json` must report PASS. It
  proves the repair when the retest runs from an installed wheel.

## Verification (2026-10-27)
| Check | Result |
| --- | --- |
| Released 1.1.6 from PyPI, clean venv, `greenfield retest --id` KIT-GF-021/032/045/067 | FAIL (typer missing) |
| This branch installed non-editable (`pip install .`) in a clean venv, same four ids | PASS |
| Same installation, `greenfield retest --id KIT-GF-089 --json` | PASS |
| `tests/test_greenfield_retest_owned_runtime_wheel.py` | 2 passed; wheel-layout test fails on the previous code |

## Release target
Unreleased, category Fixed. A consumer may record the four families as verified
only after re-running them under the released wheel that contains this repair.
No consumer-identifying material is included.

## Closeout follow-up

The work branch was integrated with current main through the Kit's local merge
lifecycle, retaining its original commit and main as parents; no history rewrite
or force push was used. CHANGELOG and coverage retain both additions. Registry
and scope resolutions came from the existing generator on an isolated public-tree
copy, preserving all main registry entries and adding this report.

The two owned-runtime regressions and six recovery-smoke tests passed in the
independent environment, including both previously reported smoke failures.
Review also found that unversioned `agentic_project_kit.egg-info` was not excluded
by the version-prefixed metadata predicate. The expanded fixture failed before
the one-line correction; the filter now excludes that own metadata as intended.
Dependencies remain unchanged. Final wheel, full-suite and CI results are
recorded in the PR closeout; no release is performed here.
