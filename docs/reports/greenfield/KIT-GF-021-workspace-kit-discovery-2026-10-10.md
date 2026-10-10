---
artifact_type: evidence
status: active
review_policy: historical_evidence
---

# KIT-GF-021: workspace-owned Kit discovery

Date: 2026-10-10
Kit state: CLOSED in this patch; released-package Cockpit retest pending.
Source: vfi64/agp-Cockpit origin/main `c31eb2dc3dcea2cd9f8b86ae6a9fdc60adad2577`,
`docs/validation/AGENTIC_KIT_GREENFIELD_FINDINGS.json`, family KIT-GF-021.
The external ledger remains unchanged; Cockpit owns VERIFIED_FIXED.

## Finding and repair

An intact repository-local Kit could be reported missing when its console script
was absent from global PATH. Shared discovery now checks the workspace `.venv`
first, followed by an explicitly declared `kit.interpreter`. It preserves the
venv interpreter's invocation path instead of resolving its symlink to a base
Python. Isolated bounded probes inspect distribution metadata, virtualenv prefix,
module origin and CLI entrypoint without importing the package. Missing evidence
is distinct from unknown/error evidence. Global installs and package origins
outside the selected environment are refused, with no implicit installation.

`kit status`, signed `kit update` and external doctor installation diagnostics use
the same model. Execution uses the selected Python module, so the console script
need not exist. A doctor warning about unavailable local discovery does not block
existing external CI runners that intentionally use a different runtime scope.

## Regression and external retest

`tests/test_kit_installation.py` covers local-first ordering, explicitly declared
venvs, absent PATH/script, timeouts, malformed metadata, mismatched interpreters,
system environments and source-outside-environment rejection. The update tests
exercise actual selection through the public route; 81 combined focused tests
passed. Earlier installed-wheel discovery smoke checks also covered an absent
console script and an explicitly declared dedicated environment.

The separate GF-051 fixture detected actual PyPI 1.0.18 in a workspace `.venv`
with global PATH restricted, upgraded that exact environment to the local
candidate and passed target-runtime check/doctor. Generated references existed;
Kit tests and the Kit registry were absent. ACK: `a3c2547eb39e`.
No Cockpit files were edited and no package was published. Cockpit should repeat
its local-installation regression after adopting a released Kit with this fix.

## Limits

The resolver deliberately does not choose arbitrary global installations or
support editable origins outside the environment. Existing single-executable
legacy callers remain compatible; the new maintenance surface uses an argv model
instead of putting a Python module command into one executable-path string.
Installation probes are bounded and read-only. A focused immutable observation
model suffices without an additional DCO layer.

## Final local gates

3460 full-suite tests, Ruff, check-docs and doctor passed. The canonical generated
handoff and bound DPA readiness record use `COMMAND_MANIFEST_ACK a3c2547eb39e`.
Doctor's 76 existing lifecycle findings remain report-only. No release action
was performed; the fix awaits a future release and Cockpit's independent retest.
