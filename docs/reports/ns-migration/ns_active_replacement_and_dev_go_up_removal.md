# Active ./ns replacement and dev/go/up removal

This controlled documentation slice replaces the 11 active `./ns` command families in active documentation surfaces and removes `./ns dev`, `./ns go`, and `./ns up` from active documentation/planning surfaces.

Scope guard:
- Historical terminal logs and evidence archives are intentionally not rewritten.
- The `./ns` executable itself is not removed in this documentation slice.
- Product-code deprecation/removal, if needed, requires a separate tested code slice.

Replacement families:
- `./ns repo-status` -> `./.venv/bin/agentic-kit transfer repo-status`
- `./ns post-merge-check` -> `./.venv/bin/agentic-kit transfer post-merge-check`
- `./ns protected-diff-plan` -> `./.venv/bin/agentic-kit transfer protected-diff-plan`
- `./ns pr-create-complete` -> `./.venv/bin/agentic-kit transfer pr-create-complete`
- `./ns pr-complete` -> `./.venv/bin/agentic-kit transfer pr-complete`
- `./ns post-merge-complete` -> `./.venv/bin/agentic-kit transfer post-merge-complete`
- `./ns sync-main` -> `./.venv/bin/agentic-kit transfer sync-main`
- `./ns command-reference-check` -> `./.venv/bin/agentic-kit transfer command-reference-check`
- `./ns command-reference-refresh` -> `./.venv/bin/agentic-kit transfer command-reference-refresh`
- `./ns rules acknowledge` -> `./.venv/bin/agentic-kit rules acknowledge`
- `./ns docs-audit` -> `./.venv/bin/agentic-kit docs-audit`
