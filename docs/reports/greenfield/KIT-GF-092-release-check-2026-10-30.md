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
cover JSON/HTML, index failure, response limits/deadline, editable metadata,
offline compatibility, CURRENT/UPDATE_AVAILABLE/AHEAD, post/pre/dev/yanked policy,
selector exclusion and guarded exact execution. The signature regression compares
latest and exact plans and executes the proposed exact command after a newer
candidate appears. Installed-wheel machine evidence and final gates are recorded
in the slice PR. No release publication is part of this finding.

Review-only modularization exception: existing updater and retest orchestration
remain large; new policy is delegated to focused modules. Extracting their full
state machines would exceed this slice. A later safe step is an independently
tested orchestration extraction behind the current CLI contracts. Existing typed
plans and retest steps suffice; another DCO layer would duplicate them.
