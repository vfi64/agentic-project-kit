# KIT-GF-033 work rescue report

Source finding ledger: `vfi64/agp-Cockpit` `origin/main` commit `7f2e421de8f453fb3c32aab54f740eec5aa0885f`.

## Finding

`KIT-GF-033` reports that external workspaces had no lossless Kit route for `main` when local uncommitted changes or local commits block normal startup recovery.

## Implemented Kit change

- Added `agentic-kit work rescue` as a dry-run-default human workflow command.
- The route has no remote effect and uses the existing local `origin/main` ref.
- Execution requires the matching dry-run `--expected-signature` when a rescue is needed.
- Dirty `main` creates a local `rescue/...` branch, commits tracked and untracked non-ignored changes on that branch, verifies the rescue branch contains the original `HEAD`, then realigns `main` to the local base ref.
- `main` with local commits creates a local rescue branch at the original `HEAD`, verifies containment, then realigns `main` to the local base ref.
- Repeated execution after a successful rescue is a no-op when `main` is already clean and aligned.

## Regression evidence

External-workspace regression tests create a temporary non-Kit Git repository with a bare `origin`, a committed `.agentic/config.yaml`, and a local `origin/main`.

Covered cases:

- dirty `main` with a tracked edit and untracked file ends with `main == origin/main`, a clean worktree, and a rescue branch containing both changes;
- `main` one local commit ahead ends with `main == origin/main`, a clean worktree, and a rescue branch pointing to the local commit;
- repeated runs after successful rescue are idempotent no-ops;
- `--json` output is parsed directly as JSON in the tests;
- generated command manifest classifies `agentic-kit work rescue` with `remote_effects: ["none"]`.

Latest targeted evidence in this slice:

```text
.venv/bin/python -m pytest -q tests/test_work_rescue.py tests/test_command_manifest.py tests/test_agentic_kit_command_reference_is_current.py
25 passed, 10 warnings
```

## Scope note

The agp-Cockpit finding ledger was not changed. Verification status remains owned by the external workspace retest.
