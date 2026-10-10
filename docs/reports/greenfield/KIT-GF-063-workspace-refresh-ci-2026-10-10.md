---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-063: workspace refresh CI

Date: 2026-10-10
Kit state: CLOSED in this patch; released-package Cockpit retest pending.
Source: vfi64/agp-Cockpit origin/main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, family KIT-GF-063.
The source ledger is unchanged; only Cockpit sets VERIFIED_FIXED.

## Finding and repair

The Kit-only refresh classifier could not recognize consumer state paths and
the consumer managed template always ran the complete audit suite. A focused
workspace policy module now derives the reserved state tree and exact handoff
projections from the manifest. The existing CI policy module exposes a thin
file/JSON adapter. A focused template renderer keeps the required agentic-gate
job and chooses between check for proven refresh-only PRs and the full suite.

Branch/event restrictions, strict relative paths, symlink refusal, immutable
configuration in a light diff and NUL-delimited endpoint diffs make uncertain
input select FULL_CI. Fetch/diff failures cannot leave a partial light diff.
The Kit's own CI policy is unchanged. The new normalized template hash is
registered under GF-042. CI refresh adopts only a matching Kit-written pair.
Signed Kit update queries the selected target runtime for the replacement,
binds its bytes in the signature and preserves customized layouts except pins.

## Regression and external retest

Focused tests cover manifest path overrides, refresh/product/config diffs,
wrong branches/events, ambiguous/missing paths, symlinks, malformed manifests,
rendered shell execution, failed endpoint reads and target-runtime adoption.
The external installed-wheel fixture repeats the positive/negative policy
checks without Kit tests or the Kit documentation registry, runs the light
check and verifies managed template adoption. Gate counts are recorded after
validation below. No production workspace, public release or tag is changed.

Cockpit should adopt a released Kit with this fix, explicitly integrate the
classifier into its customized multi-job CI, and retest a refresh-only PR plus
one product-file change and a different branch. The custom workflow is protected
from automatic replacement; updating its Kit pin alone cannot opt its jobs into
the light lane. Confirm check remains required in the light lane.

## Design and risks

The allowlist is an explicit operating-layer ownership boundary. Workspaces
must keep product files outside reserved Kit state and must not declare product
documents as generated projections. Unknown layouts remain full. A small pure
policy plus renderer is sufficient; a new workflow state machine or DCO schema
would add complexity without improving this deterministic selection.

Validation results: 136 focused tests and 3506 full-suite tests passed. All 11
external installed-wheel checks passed. Ruff, check-docs and doctor passed
(76 existing report-only lifecycle findings). Registry reconciliation passed;
command reference regeneration changed no files. Manifest ACK: a3c2547eb39e.
