---
artifact_type: evidence
status: active
review_policy: historical_evidence
---
# KIT-GF-093 — release check of an editable install uses the running version

## Observed and cause

At main `2ad5357b` (release 1.1.9), `kit status --check-release --json` in a Kit
checkout with an editable installation reported `installed: "1.1.4"`,
`installation_kind: "editable"` and `UPDATE_AVAILABLE` for 1.1.9, although the
checkout runs `__version__ = "1.1.9"` and `agentic-kit --version` reports 1.1.9.
An external desktop controller observed the same shape on a second machine after
a pull (metadata 1.1.8, running 1.1.9).

Cause: `kit_release_check.release_installation` probes the owned interpreter with
`importlib.metadata.distribution("agentic-project-kit").version`. An editable
installation keeps the distribution metadata of its last `pip install -e` while
the checkout's code runs, so every pull without a reinstall produces a stale
version. The comparison then reports an update the checkout already has, or hides
one when the metadata is newer than the code.

## Contract and implementation

For `installation_kind: editable` the probe imports the package in the owned
interpreter (still `-I`) and reports its `__version__` as `installed`; the
metadata version appears beside it as `metadata_version`. `check_release`
compares the running version and adds `metadata_version` to `release_check` only
when it differs. When the editable package cannot be imported, the result is
`UNKNOWN` with reason `running_version_unavailable`; the probe never falls back to
the metadata version. Wheel installations are unchanged: their metadata and
running package agree, the probe output keeps its previous shape and no
`metadata_version` is added.

`kit update --latest` already answers an editable installation with a governed
checkout hint before reading the index; it never used the installed version, so
its behaviour is unchanged.

## External machine contract

The new `external_release_check_stale_editable` fixture is the GF-092 loopback
index fixture with an editable owned runtime: its `direct_url.json` marks the
copy as editable and its distribution `METADATA` names `0.0.1` while the package
runs the installed Kit version; the index offers exactly that running version.
The contract expects `release_check.result: CURRENT`, `installed` equal to the
running Kit version, `metadata_version: "0.0.1"` and, for `kit update --latest`,
PASS with `checkout_required`. Before the fix the same fixture reports installed
0.0.1 and `UPDATE_AVAILABLE`. Effect handling is shared with GF-092: only the
declared status/latest read routes on the loopback index are permitted. No
consumer workspace is read or changed, and this evidence does not claim consumer
VERIFIED_FIXED.

## Verification

Regression tests in `tests/test_kit_release_check.py` run the real probe script
against synthetic distributions on `PYTHONPATH`: stale older metadata (CURRENT,
`metadata_version` 1.1.4), newer metadata (no false AHEAD), a wheel (unchanged
shape) and an unimportable editable package (`UNKNOWN`, no index read). Four of
the five fail on main `2ad5357b`; the wheel case passes before and after. The
machine contract passes from the checkout and from a freshly installed
noneditable wheel of this branch (see the JSON next to this report).
