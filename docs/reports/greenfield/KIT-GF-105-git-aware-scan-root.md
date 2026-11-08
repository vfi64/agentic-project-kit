# KIT-GF-105 — Git-aware scan must verify repository root

## Befund
`_git_aware_scan_files(root, scan_root)` trusted `git ls-files` with exit code 0 even when `root` was inside an unrelated parent Git repository. When the parent ignored `inner/`, the file set was empty and the metadata projection scanner incorrectly returned PASS.

## Reproduktion (vor der Korrektur)
Step 247: `test_parent_repo_ignored_child_is_scanned` failed (expected BLOCKED, got PASS); the existing projection test also failed in the Cockpit temporary directory. This is the required red regression evidence.

## Korrektur
Only use `git ls-files` if `git -C root rev-parse --show-prefix` succeeds with an empty prefix; otherwise recursively scan files. Genuine Git repositories retain `.gitignore` filtering.

## Nachweis und Einschränkungen
Step 248: original 51 pytest-core tests passed; Kit work check was BLOCKED solely on five Ruff formatting findings in the new test. Step 249: Kit work check PASS, no blockers; `git diff --check` PASS. Call sites: `transfer_diagnostics.py` lines near 381 and 500; their `root` semantics still need explicit review. No GF-104 slice or Owner stash modified. Full suite and CI/PR not yet verified.
