# Post-v1.0.8 Command-For Warning Hygiene

Status: implemented local retest pass  
Date: 2026-09-05  
Kit branch: `codex/command-for-warning-hygiene`  
Machine-readable companion:
`docs/reports/POST_V1_0_8_COMMAND_FOR_WARNING_HYGIENE_20260905.json`

## Scope

This report records the B1-KIT-010 repair for command selector output hygiene in
manifest-less non-workspaces.

The historical Greenfield evidence showed that `agentic-kit command-for --json`
could emit `LegacyProfileDeprecationWarning` before the JSON payload when invoked
from a manifest-less external directory. That made the command authority helper
less reliable exactly where it is needed most: before an agent proposes or runs a
workflow command.

This is a narrow output-boundary repair. It does not remove the implicit legacy
profile warning for real legacy workspace loading.

## Reproduction

The defect was reproduced from an empty temporary directory with a `--root`
pointing at the same empty directory.

Observed before the repair:

- `agentic-kit command-for --root /tmp/... --task work --json` exited 0;
- stderr/stdout included `LegacyProfileDeprecationWarning`;
- the JSON payload followed the warning and was therefore not a clean standalone
  machine-readable response.

The same behavior was reproduced for raw command selection:

- `agentic-kit command-for --root /tmp/... --raw "git push origin main" --json`.

## Root Cause

`command-for` calls `load_manifest(root)` so it can prefer a repository-local
command manifest when one exists and fall back to the packaged manifest when it
does not.

`load_manifest()` resolved the reference path through `load_workspace(root)`
without suppressing the legacy-profile warning. In a manifest-less
non-workspace, that warning is appropriate for actual legacy workspace use, but
not for read-only command manifest discovery.

## Repair

The repair keeps the existing mechanisms:

- `load_manifest()` now accepts `suppress_legacy_profile_warning` and passes it
  through to `load_workspace()`;
- `command-for` uses that option because command selection is a read-only command
  authority/manifest lookup flow;
- existing package-manifest fallback behavior is unchanged;
- direct `load_workspace()` calls still warn for manifest-less legacy workspace
  use unless the caller explicitly suppresses the warning.

No new command, fallback subsystem, or alternate command taxonomy was added.

## Retest

Focused validation:

- `python -m pytest -q tests/test_command_selector.py tests/test_workspace_foundation.py`
  -> 51 passed.
- `python -m pytest -q` -> 3026 passed, 481 warnings.
- `ruff check .` -> PASS.
- `agentic-kit check-docs` -> PASS after refreshing the docs-registry scope
  decision projection for the new report count.
- `agentic-kit direction validate --root .` -> PASS, 0 findings.
- `agentic-kit audit-command-manifest --json` -> PASS, 0 findings.
- `agentic-kit workflow-guard check` -> PASS.
- `agentic-kit doctor` -> Overall PASS, with 76 document-lifecycle
  report-only findings.

Manual CLI retest:

- `agentic-kit command-for --root /tmp/... --task work --json`
  -> PASS, clean JSON output and no legacy-profile warning.

The focused regression also keeps the direct workspace contract intact:
manifest-less `load_workspace(tmp_path)` still emits `LegacyProfileDeprecationWarning`.

## Greenfield Finding Impact

| Finding | Impact |
| --- | --- |
| B1-KIT-010 / `command_for_manifestless_warning` | Locally fixed and retested for `command-for --json` output hygiene in manifest-less non-workspaces. |
| KIT-GF-010 | Not closed by this slice. The broader rule-acknowledgement self-invalidation lifecycle remains governed by its own evidence and release-package retest path. |

## Boundary

This report does not claim released PyPI behavior. The fix is validated against
the current checkout only. Released-package confirmation must wait until a later
published version contains this change.
