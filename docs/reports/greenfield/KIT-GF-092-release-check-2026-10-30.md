---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-092 — optional stable release discovery

## Observed and cause

At main `62ea664c`, kit status observes only the workspace-owned interpreter and
installation; kit update requires an explicit version. An external desktop
controller would otherwise need its own package-index policy. Two CLI regressions
first reproduced the missing release-check and latest options.

## Contract and implementation

The focused kit_release_check module reads only the configured Simple index,
accepts its JSON or HTML representation, parses distribution filenames with
packaging>=22 and compares PEP 440 versions. Post-releases are stable candidates;
pre/dev releases and yanked files are excluded. A version remains available if
at least one of its distribution files is not yanked. There is no PyPI JSON API
fallback or second index. Invalid metadata, no stable release, transport errors,
oversized responses and the 10-second observation deadline yield UNKNOWN.
The deadline bounds DNS and slow responses as well as socket inactivity; a timed
out read-only daemon cannot keep the CLI alive and its late result is discarded.
No retry or cache writes are introduced.

The existing offline status remains unchanged. The optional release_check has
installed, latest_release, index_url, checked_at (UTC), result and
installation_kind. A reason accompanies UNKNOWN; unavailable installation
metadata is null rather than guessed. Direct-url metadata distinguishes editable
installations. The optional observation never changes the base status result.

The focused kit_update_latest adapter resolves once and delegates to the exact
updater. The resolved version is reported outside the signed plan, preserving
signature equality with the exact version route. The generated execution command
always names --version and the original signature. Re-running --latest with
--execute is refused: only that exact command executes the authorized target.
CURRENT is PASS/already_current with no plan, writes or branch requirement.
Editable is PASS/checkout_required with a governed checkout-sync hint, without an
installation plan or index read. AHEAD refuses implicit downgrade. UNKNOWN blocks
planning with reason and next_safe_action. Exact version updates retain their
existing guards; post-release comparisons and the managed CI pin guard agree.

## External machine contract

The external_release_check fixture prepares an owned noneditable runtime copy and
an ephemeral loopback HTTP Simple index in a disposable workspace. It exercises
the installed CLI for offline status, CURRENT, branch-free already-current,
UPDATE_AVAILABLE with a post-release ahead of pre/dev and yanked files, and
UNKNOWN/blocked planning when no stable candidate exists. It never installs from
that fake index. Fixture-specific effect handling permits only the declared
status/latest read routes with the fixed owned interpreter and loopback index;
alternate roots, execute flags and changed index bindings are refused. Ordinary
remote service retests retain owner_remote classification. No consumer workspace
is read or changed, and this evidence does not claim consumer VERIFIED_FIXED.

## Verification

The existing 95 update/installation tests passed before changes. Focused tests
cover JSON/HTML, index failure, deadline, editable metadata,
offline compatibility, CURRENT/UPDATE_AVAILABLE/AHEAD, post/pre/dev/yanked policy,
selector exclusion and guarded exact execution. The signature regression compares
latest and exact plans and executes the proposed exact command after a newer
candidate appears. Installed-wheel machine evidence and final gates are recorded
below and in the companion JSON result. No release publication is part of this finding.

Review-only modularization exception: existing updater and retest orchestration
remain large; new policy is delegated to focused modules. Extracting their full
state machines would exceed this slice. A later safe step is an independently
tested orchestration extraction behind the current CLI contracts. Existing typed
plans and retest steps suffice; another DCO layer would duplicate them.

## Completed local baseline before compatibility correction

- Full unchanged suite, run serially: 4410 passed, 560 warnings.
- Ruff, project check, check-docs, doctor and protected-diff-plan: PASS.
  Doctor retains 76 pre-existing report-only lifecycle findings.
- Fresh noneditable branch installation: version 1.1.8, packaging
  26.3; GF-092 installed-wheel retest: PASS, one executed
  contract, zero failed or unexecuted contracts.
- Code/test candidate commit: `144dfbd19c6982519f3555ebb9ae5740ee16d95e`.
  Source tree: `03d9f11bb905d5ca7e8f2350bc0080682b1e49cd`; test tree: `c37af602ac6af1448f8da571db6d8fe0ae0177a1`.
- Command manifest SHA: `52fa7baf8daf`.
- Machine-readable wheel result:
  [GF-092 result](KIT-GF-092-release-check-2026-10-30.json), SHA-256 `041c5ed613951e02d99e025c45a13434e09c8094a0982f47cc778557339ac706`.
  Its execution-origin path omits the private host prefix; all contract step
  outcomes and the catalog binding are preserved.
- A parallel macOS run was interrupted after a process-start hang. Native
  inspection located its child in close-open-file-descriptors before exec,
  with a Tcl/Tk notifier active. It is not reported as PASS; the complete serial
  run above is the local full-suite evidence. No assertions or gates were skipped.

## Reproduction and artifact completeness

Implementation, tests, catalog source, machine fixture, generated reference and
catalog projections, documentation and bounded final outcomes are repository
artifacts. No checked-in file depends on a temporary helper or virtualenv.
The machine contract is preserved in `.agentic/greenfield_findings.json` and
exported with the installed Kit; it creates its own disposable loopback index.

Recreate the wheel evidence by making a fresh virtualenv, installing this checkout
noneditably with pip, and invoking its installed `agentic-kit greenfield retest
--id KIT-GF-092 --json`. Check distribution metadata for editable=false first.
Run the full suite with `python -m pytest -q --durations=10`, then `ruff check .`,
`agentic-kit check --json`, `agentic-kit check-docs --json` and `agentic-kit doctor`.
Dependency requirements are declared in pyproject.toml; the saved test virtualenv
and orchestration helpers are disposable and are not required for reproduction.

Temporary raw logs and process samples are diagnostics, not unique required
inputs or the only final verification record. This evidence does not claim a
real consumer update, cross-platform certification or release publication.

## Compatibility correction before merge

The final contract review found that the exact updater's new PEP 440 comparison
had broadened the accepted installed-version domain beyond the previous stable
X.Y.Z contract. Two regressions first demonstrated AWAITING_APPROVAL for installed
pre/dev versions where unsupported_installed_version was required. The narrow
installed-version preflight now preserves the old refusal and additionally
accepts the explicitly approved stable post-release form. A positive regression
protects installed post-release support. All 113 targeted tests passed after the
correction; no assertion was weakened. The automatic closeout was stopped before
merge. The complete baseline above is not presented as a full-suite run of this
subsequent correction; final full-suite and wheel evidence must be refreshed
before completion.

Correction input `src/agentic_project_kit/kit_update.py` SHA-256: `be320fe9b184bc4050147fbe4a44b3553fe7979c6befcf829b4fe7ffd0c8b325`.

Correction input `tests/test_kit_update.py` SHA-256: `d294e3d54566016d3af0e1d2baf2d151b2fd0fd235e7114e0c9598fb9fbffcaf`.
