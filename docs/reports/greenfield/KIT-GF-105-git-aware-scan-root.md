# KIT-GF-105: Git-aware scan must verify the repository root

Date: 2026-11-08

Scope: `_git_aware_scan_files` in `cli_commands/transfer_diagnostics.py`.

Status: fix merged on Kit `main` in PR #2753 (`d6956cd2`); not released.

## Finding

`_git_aware_scan_files(root, scan_root)` trusted `git -C root ls-files` with
exit code 0 even when `root` was not a repository root but lay inside an
unrelated parent Git working tree. When the parent ignored the directory
containing `root`, the file list was empty and the static meta-preference
projection scan returned PASS instead of BLOCKED.

The defect surfaced only in AGP Cockpit runs: for a steered repository the
Cockpit sets the work-order `TMPDIR` below its own checkout
(`.local/agp-cockpit/repos/<name>-<hash>/tmp/<step>`, Git-ignored there), so
pytest temporary projects sat inside an ignored part of a foreign working tree.

## Change

`git ls-files` is used only if `git -C root rev-parse --show-prefix` succeeds
with an empty prefix, i.e. `root` is itself the top of a working tree.
Otherwise the scan falls back to a recursive file walk. Genuine repository
roots keep `.gitignore` filtering.

## Regression evidence

New tests in `tests/test_transfer_diagnostics_git_root.py`:

- `test_parent_repo_ignored_child_is_scanned`: a child directory ignored by a
  parent repository is scanned and the drift is BLOCKED.
- `test_own_repository_still_respects_ignore`: in a real repository root,
  ignored paths stay excluded and the scan is PASS.

Counterprobe (2026-11-08): the test module from `d6956cd2` run against the
source of the PR base `78a38d95` gives `1 failed, 1 passed`
(`test_parent_repo_ignored_child_is_scanned`: PASS instead of BLOCKED).
Against `d6956cd2` it gives `2 passed`.

CI on PR head `95198cb`: `test`, `test-shard (0..2)` and `classify` succeeded,
`pytest-parallel-shadow` skipped.

## Call-site review

Both callers pass the project root as `root`:

- `_scan_static_meta_preference_projection_drift` (line ~381) filters excluded
  directory names on the path relative to the scan root; correct under the fix.
- `_known_bad_pattern_scan` (line ~500) filters `.git`, `.venv`, `tmp` and
  `__pycache__` against all parts of the absolute path. A project located
  below any directory named `tmp` is therefore skipped completely and the scan
  reports no matches. Reproduced locally on 2026-11-08 (same file, 0 matches
  below `/tmp`, 1 match elsewhere). This is a separate defect, not caused or
  fixed by KIT-GF-105; it is tracked as KIT-GF-106.

The absolute-path and ns-legacy audits used the same Git file-list pattern;
their parent-repository false negatives are tracked as KIT-GF-108.

## Boundaries

Kit closure does not establish external consumer `VERIFIED_FIXED`. The finding
now has a catalog retest description, but the installed-runtime harness has no
ignored-parent-repository fixture. No release is claimed.
